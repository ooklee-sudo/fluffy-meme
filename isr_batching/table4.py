"""Table 4 (Section 6.6): posted prices, equilibrium demand and non-exponential service, by trace-driven simulation.

Protocol (every step is a choice of this implementation; the manuscript text does not fix them):
* Unpriced demand = the recorded trace (dedicated) or a superposition of shifted copies of it (batched); see build().  Requests carry an i.i.d. uniform rank u; a request in phase k is admitted when
  u < a_k, which is equivalent to the linear demand P(l) = V (1 - l / Lam) of Section 3 (user with rank u has value V (1 - u)).
* Phases: 30-second windows grouped into K equal-size classes by arrival count.
* Service requirements: Gamma with the trace-mean and squared coefficient of variation SCV (same draws in all runs).
* Delay cost 1 per mean isolated service time.  Welfare = sum of admitted values V (1 - u) minus the sum of sojourn times.
* Equilibrium under a flat price p: a_k = 1 - (p + d_k) / V, with d_k the simulated mean sojourn time of admitted requests that
  arrive in phase k (damped fixed point, common random numbers).
* Best phase-dependent schedule: admission levels (a_k) maximising simulated welfare (coordinate search; each plan is
  implementable by phase prices because a_k can be reached by some p_k).
* Poisson-calibrated flat price: optimal flat price (equilibrium) in a homogeneous system fed by Poisson arrivals at the
  recorded load (the planner takes the recorded demand to be the unpriced demand); it is then applied to the real demand.
* Reported: loss relative to the best phase-dependent schedule, in %: no price / Poisson-calibrated flat price / best flat price.
"""
import argparse, json, time
import numpy as np
from multiprocessing import Pool
from capacity_sim import simulate, load_trace

ALPHA, BETA, PREFILL = 3.64, 0.0321, 0.016          # ms; measured (Section 5.2)
BETA_OVER_ALPHA = BETA / ALPHA


class Sys:
    def __init__(self, arr, phase, work, u, c, M, b, V, K):
        self.arr, self.phase, self.work, self.u, self.c, self.M, self.b, self.V, self.K = arr, phase, work, u, c, M, b, V, K

    def run(self, a):
        """a: admission probability per phase.  Returns welfare and per-phase mean delay of admitted requests."""
        keep = self.u < np.asarray(a)[self.phase]
        if keep.sum() == 0: return 0.0, np.zeros(self.K)
        _, soj = simulate(self.arr[keep], self.work[keep], self.c, self.M, self.b, 'random', 0)
        ph = self.phase[keep]
        d = np.array([soj[ph == k].mean() if np.any(ph == k) else 0.0 for k in range(self.K)])
        W = float((self.V * (1 - self.u[keep])).sum() - soj.sum())
        return W, d

    def equilibrium(self, p, a0, iters=40):
        a = np.clip(np.asarray(a0, float), 0, 1)
        for _ in range(iters):
            W, d = self.run(a)
            tgt = np.clip(1 - (p + d) / self.V, 0, 1)
            if np.max(np.abs(tgt - a)) < 2e-3: break
            a = a + 0.5 * (tgt - a)
        return a, self.run(a)[0]

    def best_flat(self, grid):
        a = np.full(self.K, 0.5); best = (-np.inf, None, None)
        for p in grid:
            a, W = self.equilibrium(p, a)
            if W > best[0]: best = (W, p, a.copy())
        lo, hi = max(best[1] - (grid[1] - grid[0]), 0), best[1] + (grid[1] - grid[0])
        for p in np.linspace(lo, hi, 7):
            a, W = self.equilibrium(p, best[2])
            if W > best[0]: best = (W, p, a.copy())
        return best

    def best_plan(self, a0, step=0.2, rounds=5):
        a = np.clip(np.asarray(a0, float), 0, 1); W = self.run(a)[0]
        for _ in range(rounds):
            for k in range(self.K):
                for s in (+step, -step):
                    while True:
                        b_ = a.copy(); b_[k] = np.clip(b_[k] + s, 0, 1)
                        if b_[k] == a[k]: break
                        Wn = self.run(b_)[0]
                        if Wn > W + 1e-9: a, W = b_, Wn
                        else: break
            step /= 2
        return a, W


def build(trace, kind, scv, ratio, V, K, seed, cfg, window=30.0):
    """Unpriced demand.  Time unit = mean isolated service time of the dedicated benchmark (0.5 ms per prompt token + 30 ms per
    generated token: 6.9 s on the conversation trace, 1.9 s on the code trace).  Dedicated rows use c = `servers` servers (45 / 7, the cluster
    sizes of Table 1), batched rows one engine (M = 1,024).  Unpriced demand is the superposition of m = ratio x capacity /
    recorded load copies of the trace (the first copy as recorded, the others circularly shifted by independent random
    offsets, the fractional part of m by thinning), so that the mean unpriced load is `ratio` x capacity.  Phases: 30-second windows grouped into K equal-size classes by arrival count."""
    arr0, P, G = load_trace(trace)
    mean_s = (0.5 * P + 30.0 * G).mean() / 1000.0
    span = arr0[-1] - arr0[0] + 1e-9
    if kind == 'dedicated': c, M, b, cap = 1, cfg['servers'], 0.0, float(cfg['servers'])
    else: c, M, b = 1, cfg['M'], BETA_OVER_ALPHA; cap = M * (1 + b) / (1 + b * M)
    load_rec = len(arr0) / span * mean_s                                     # recorded load in servers
    m = ratio * cap / load_rec                                              # copies of the trace so that unpriced load = ratio x capacity
    rng = np.random.default_rng(seed)
    parts = []
    for r in range(int(np.floor(m))):
        parts.append(arr0 if r == 0 else (arr0 - arr0[0] + rng.uniform(0, span)) % span)
    frac = m - np.floor(m)
    if frac > 0: parts.append(((arr0 - arr0[0] + rng.uniform(0, span)) % span)[rng.uniform(size=len(arr0)) < frac])
    arr_s = np.sort(np.concatenate(parts)) if len(parts) > 1 else arr0 - arr0[0]
    widx = (arr_s // window).astype(int); nw = widx.max() + 1
    counts = np.bincount(widx, minlength=nw)
    cls = np.empty(nw, int); cls[np.argsort(counts, kind='stable')] = np.arange(nw) * K // nw
    phase = cls[widx]
    arr = arr_s / mean_s
    work = rng.gamma(1.0 / scv, scv, len(arr))                              # mean 1, SCV = scv
    u = rng.uniform(size=len(arr))
    return Sys(arr, phase, work, u, c, M, b, V, K), dict(n=len(arr), load=len(arr) / (span / mean_s), scale=m, cap=cap, mean_s=mean_s)


def poisson_price(sysm, ratio, V, grid, seed):
    """Optimal flat price for a planner who treats the recorded load (unpriced load / ratio) as the demand and arrivals as Poisson."""
    n = int(len(sysm.arr) / ratio); span = sysm.arr[-1] - sysm.arr[0]
    rng = np.random.default_rng(seed + 99)
    arr = np.sort(rng.uniform(0, span, n))
    h = Sys(arr, np.zeros(n, int), sysm.work[:n].copy(), sysm.u[:n].copy(), sysm.c, sysm.M, sysm.b, V, 1)
    _, p, _ = h.best_flat(grid)
    return p


def cell(job):
    trace, kind, scv, a = job
    t0 = time.time()
    sysm, info = build(trace, kind, scv, a['ratio'], a['V'], a['K'], a['seed'], a)
    grid = np.linspace(0, a['pmax'], a['np'])
    Wf, pf, af = sysm.best_flat(grid)
    # best phase-dependent plan, started from the best flat equilibrium and from a quantile ladder
    best = None
    for a0 in (af, np.linspace(0.9, 0.2, a['K'])[::-1] * 0 + np.linspace(0.3, 0.9, a['K'])[::-1]):
        ap_, Wp = sysm.best_plan(a0)
        if best is None or Wp > best[1]: best = (ap_, Wp)
    a_pd, Wpd = best
    Wpd = max(Wpd, Wf)
    _, Wn = sysm.equilibrium(0.0, np.full(a['K'], 0.5))
    pp = poisson_price(sysm, a['ratio'], a['V'], grid, a['seed'])
    _, Wp_ = sysm.equilibrium(pp, af)
    L = lambda W: 100 * (Wpd - W) / Wpd
    return dict(trace=trace, kind=kind, scv=scv, none=L(Wn), poisson=L(Wp_), flat=L(Wf), p_flat=float(pf), p_poisson=float(pp),
                Wpd=Wpd, a_pd=a_pd.tolist(), info=info, seconds=time.time() - t0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--conv', required=True); ap.add_argument('--code', required=True)
    ap.add_argument('--servers-conv', type=int, default=45); ap.add_argument('--servers-code', type=int, default=7)
    ap.add_argument('--M', type=int, default=1024)
    ap.add_argument('--kinds', default='dedicated,batched'); ap.add_argument('--scv', default='0.5,1,4,16')
    ap.add_argument('--V', type=float, default=20.0); ap.add_argument('--ratio', type=float, default=1.4)
    ap.add_argument('--K', type=int, default=5); ap.add_argument('--pmax', type=float, default=18.0); ap.add_argument('--np', type=int, default=19)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--procs', type=int, default=4); ap.add_argument('--json', default=None)
    a = vars(ap.parse_args())
    jobs = []
    for kind in a['kinds'].split(','):
        for name, path, srv in (('conv', a['conv'], a['servers_conv']), ('code', a['code'], a['servers_code'])):
            for scv in map(float, a['scv'].split(',')):
                cfg = dict(a, servers=srv)
                jobs.append((path, kind, scv, cfg))
    with Pool(a['procs']) as pool: res = pool.map(cell, jobs)
    for r in res:
        print(f"{r['kind']:9s} {'conv' if 'conv' in r['trace'] else 'code'}  SCV {r['scv']:>4g}:  {r['none']:5.1f} / {r['poisson']:5.1f} / {r['flat']:5.1f}   "
              f"(p_flat {r['p_flat']:.2f}, p_poisson {r['p_poisson']:.2f}, scale {r['info']['scale']:.2f}, {r['seconds']:.0f}s)", flush=True)
    if a['json']: json.dump(dict(args=a, results=res), open(a['json'], 'w'), indent=1)


if __name__ == '__main__':
    main()
