"""Trace-driven capacity sizing for batched serving (Section 5.4 / Table 1, Table B4).

Each engine holds at most M requests in its batch; every request in service progresses at speed
rho(n) = (1+b)/(1+b*n) (b = beta/alpha) in units of 'isolated service time per unit time'.
A request with work w (isolated service times) finishes when the engine's virtual clock advanced by w.
Excess requests wait FCFS per engine.  Routing: 'random' or 'jsq' (join-the-shortest-queue, "balanced").
Delays are in units of the mean isolated service time of the workload.
"""
import argparse, heapq, collections
import numpy as np


def simulate(arr, work, c, M, b, routing='random', seed=0):
    """arr: sorted arrival times; work: isolated service times. Returns (wait, sojourn) arrays."""
    rng = np.random.default_rng(seed)
    n_req = len(arr)
    rho = lambda n: (1 + b) / (1 + b * n)
    v = np.zeros(c); tl = np.zeros(c); nb = np.zeros(c, int)                # virtual clock, last update, batch size
    fin = [[] for _ in range(c)]                                              # heaps of (finish_virtual, req)
    q = [collections.deque() for _ in range(c)]
    ver = np.zeros(c, int); ev = []                                           # global completion events
    start = np.full(n_req, np.nan); done = np.full(n_req, np.nan)

    def advance(e, t):
        if nb[e] > 0: v[e] += (t - tl[e]) * rho(nb[e])
        tl[e] = t

    def schedule(e):
        ver[e] += 1
        if nb[e] > 0:
            heapq.heappush(ev, (tl[e] + (fin[e][0][0] - v[e]) / rho(nb[e]), e, ver[e]))

    def admit(e, i, t):
        heapq.heappush(fin[e], (v[e] + work[i], i)); nb[e] += 1; start[i] = t

    def complete_until(t_lim):
        while ev and ev[0][0] <= t_lim:
            t, e, vv = heapq.heappop(ev)
            if vv != ver[e]: continue
            advance(e, t)
            _, i = heapq.heappop(fin[e]); nb[e] -= 1; done[i] = t
            while q[e] and nb[e] < M: admit(e, q[e].popleft(), t)
            schedule(e)

    for i in range(n_req):
        t = arr[i]; complete_until(t)
        if routing == 'random': e = int(rng.integers(c))
        else: e = int(np.argmin(nb + np.fromiter((len(x) for x in q), int, c)))
        advance(e, t)
        if nb[e] < M: admit(e, i, t)
        else: q[e].append(i)
        schedule(e)
    complete_until(np.inf)
    return start - arr, done - arr


def size_capacity(arr, work, M, b, target, routing='random', c_max=512, seed=0):
    """Smallest #engines whose tail probability meets `target = (metric, thresh, prob)`.
    metric 'wait' -> P(wait > thresh) <= prob; 'sojourn' -> P(sojourn > thresh) <= prob."""
    metric, thresh, prob = target
    lo, hi = 1, 1
    ok = lambda c: np.mean((lambda w, s: (w if metric == 'wait' else s))(*simulate(arr, work, c, M, b, routing, seed)) > thresh) <= prob
    while hi < c_max and not ok(hi): lo, hi = hi, hi * 2
    if not ok(hi): return None
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if ok(mid): hi = mid
        else: lo = mid
    return hi


def size_dedicated(arr, work, target, c_max=2048, seed=0):
    """Dedicated servers = ONE pooled FCFS queue with c servers (M/M/c): engine with batch cap M = c, rho = 1.
    Smallest c meeting the target."""
    metric, thresh, prob = target
    def ok(c):
        w, s = simulate(arr, work, 1, c, 0.0, 'random', seed)
        return np.mean((w if metric == 'wait' else s) > thresh) <= prob
    lo, hi = 1, 1
    while hi < c_max and not ok(hi): lo, hi = hi, hi * 2
    if not ok(hi): return None
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if ok(mid): hi = mid
        else: lo = mid
    return hi


# ----- arrival models (all operate in SECONDS; returns (arrival_times, work_ms)) ---------------
def model_replay(arr, work, rng): return arr, work


def model_poisson(arr, work, rng):
    n = len(arr); T = arr[-1] - arr[0]
    return np.sort(arr[0] + rng.uniform(0, T, n)), work


def model_bootstrap(arr, work, rng, block=200):
    """Block bootstrap: resample blocks of consecutive interarrivals (with their work)."""
    ia = np.diff(arr, prepend=arr[0]); n = len(arr); nb = int(np.ceil(n / block))
    starts = rng.integers(0, n - block, nb)
    idx = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
    return np.cumsum(ia[idx]), work[idx]


def _counts(arr, w):
    edges = np.arange(arr[0], arr[-1] + w, w)
    return np.histogram(arr, bins=edges)[0].astype(float)


def model_rate_chain(arr, work, rng, window=30.0, states=5):
    """Five-state Markov chain on the 30-second arrival rate (quantile states), Poisson within a window."""
    c = _counts(arr, window) / window
    qs = np.quantile(c, np.linspace(0, 1, states + 1)[1:-1])
    st = np.searchsorted(qs, c, side='right')
    rate = np.array([c[st == k].mean() if np.any(st == k) else c.mean() for k in range(states)])
    P = np.full((states, states), 1e-9)
    for a, b in zip(st[:-1], st[1:]): P[a, b] += 1
    P /= P.sum(1, keepdims=True)
    nwin = len(c); k = rng.integers(states); times = []
    for i in range(nwin):
        m = rng.poisson(rate[k] * window)
        times.append(arr[0] + i * window + np.sort(rng.uniform(0, window, m)))
        k = rng.choice(states, p=P[k])
    t = np.concatenate(times)
    return t, rng.choice(work, len(t))


def fit_mmpp2(arr, windows=(1, 5, 15, 30, 60, 120, 300)):
    """Fit a 2-state MMPP to the index of dispersion for counts (IDC) at several window lengths (least squares, log scale)."""
    from scipy.optimize import minimize
    lam = len(arr) / (arr[-1] - arr[0])
    ws = [w for w in windows if w < (arr[-1] - arr[0]) / 8]
    emp = []
    for w in ws:
        c = _counts(arr, w); emp.append(c.var() / c.mean())
    emp = np.array(emp)

    def idc(theta, t):
        l1, l2, r12, r21 = np.exp(theta)
        r = r12 + r21; p1, p2 = r21 / r, r12 / r; lb = p1 * l1 + p2 * l2
        return 1 + 2 * (l1 - l2) ** 2 * p1 * p2 / (r * lb) * (1 - (1 - np.exp(-r * t)) / (r * t))

    lo = np.log([0.02 * lam, 0.02 * lam, 1e-4, 1e-4]); hi = np.log([30 * lam, 30 * lam, 5.0, 5.0])   # keep parameters finite
    best = None
    for l1m, l2m, r0 in [(3, .3, .05), (2, .5, .5), (5, .1, .01), (1.5, .7, 2)]:
        x0 = np.clip(np.log([lam * l1m, lam * l2m, r0, r0]), lo, hi)
        def loss(x):
            x = np.clip(x, lo, hi)
            l1, l2, r12, r21 = np.exp(x); r = r12 + r21; lb = (r21 * l1 + r12 * l2) / r
            return ((np.log(np.array([idc(x, t) for t in ws])) - np.log(emp)) ** 2).sum() + 50 * np.log(lb / lam) ** 2
        res = minimize(loss, x0, method='Nelder-Mead', options=dict(maxiter=4000, xatol=1e-6, fatol=1e-10))
        if best is None or res.fun < best.fun: best = res
    return np.exp(np.clip(best.x, lo, hi)), best.fun


def model_mmpp2(arr, work, rng, params=None):
    l1, l2, r12, r21 = params; T = arr[-1] - arr[0]
    t, state, out = 0.0, int(rng.random() < r12 / (r12 + r21)), []
    while t < T:
        rates = (l1, l2)[state]; dwell = rng.exponential(1.0 / (r12, r21)[state])
        d = min(dwell, T - t); m = rng.poisson(rates * d)
        out.append(arr[0] + t + np.sort(rng.uniform(0, d, m))); t += dwell; state ^= 1
    a = np.concatenate(out)
    return a, rng.choice(work, len(a))


def load_trace(path, ts_col='TIMESTAMP', prompt_col='ContextTokens', gen_col='GeneratedTokens', max_rows=None):
    import pandas as pd
    df = pd.read_csv(path, nrows=max_rows)
    t = pd.to_datetime(df[ts_col]); arr = (t - t.iloc[0]).dt.total_seconds().to_numpy()
    order = np.argsort(arr, kind='stable')
    return arr[order], df[prompt_col].to_numpy()[order], df[gen_col].to_numpy()[order]


def main():
    ap = argparse.ArgumentParser(description='Table 1: capacity required to meet a delay target under several arrival models.')
    ap.add_argument('--trace', required=True)
    ap.add_argument('--decode-ms', type=float, required=True, help='alpha: decode step time at batch 1 (ms per generated token)')
    ap.add_argument('--beta-ms', type=float, default=0.0, help='beta (0 = dedicated servers)')
    ap.add_argument('--prefill-ms', type=float, required=True, help='ms per prompt token')
    ap.add_argument('--dedicated', action='store_true', help='pooled M/M/c dedicated servers (beta=0); capacity = #servers')
    ap.add_argument('--M', type=int, default=64, help='batch cap per engine (batched mode)')
    ap.add_argument('--metric', choices=['wait', 'sojourn'], default='wait')
    ap.add_argument('--thresh', type=float, default=1.0, help='in mean isolated service times')
    ap.add_argument('--prob', type=float, default=0.05)
    ap.add_argument('--routing', default='random', choices=['random', 'jsq'])
    ap.add_argument('--reps', type=int, default=5); ap.add_argument('--block', type=int, default=200)
    ap.add_argument('--models', default='replay,bootstrap,poisson,ratechain,mmpp')
    ap.add_argument('--max-rows', type=int, default=None); ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args()
    b = 0.0 if a.dedicated else a.beta_ms / a.decode_ms
    if a.dedicated: a.beta_ms = 0.0
    arr, P, G = load_trace(a.trace, max_rows=a.max_rows)
    iso_ms = G * (a.decode_ms + a.beta_ms) + P * a.prefill_ms          # isolated service time of each request
    mean_s = iso_ms.mean() / 1000.0
    lam = len(arr) / (arr[-1] - arr[0])
    print(f'n={len(arr)}  span={arr[-1]-arr[0]:.0f}s  mean isolated service={mean_s:.3f}s  '
          f'offered load={lam*mean_s:.1f} servers  SCV(interarrival)={np.var(np.diff(arr))/np.mean(np.diff(arr))**2:.1f}')
    work_n = iso_ms / iso_ms.mean()                                      # work in isolated service times
    rng = np.random.default_rng(a.seed)
    tgt = (a.metric, a.thresh, a.prob)
    mm = None
    if 'mmpp' in a.models:
        mm, f = fit_mmpp2(arr); print('MMPP2 (l1,l2,r12,r21)=', np.round(mm, 4), ' fit loss', round(f, 4))
    gens = dict(replay=lambda: model_replay(arr, iso_ms, rng), bootstrap=lambda: model_bootstrap(arr, iso_ms, rng, a.block),
                poisson=lambda: model_poisson(arr, iso_ms, rng), ratechain=lambda: model_rate_chain(arr, iso_ms, rng),
                mmpp=lambda: model_mmpp2(arr, iso_ms, rng, mm))
    res = {}
    for name in a.models.split(','):
        reps = 1 if name == 'replay' else a.reps; vals = []
        for r in range(reps):
            t, w_ms = gens[name]()
            tt, ww = t / mean_s, w_ms / iso_ms.mean()
            vals.append(size_dedicated(tt, ww, tgt, seed=r) if a.dedicated else size_capacity(tt, ww, a.M, b, tgt, a.routing, seed=r))
        v = [x for x in vals if x]
        res[name] = (int(np.median(v)) if v else None, vals)
        print(f'{name:10s} capacity ({"servers" if a.dedicated else "engines"}) = {res[name][0]}   reps={vals}')
    if res.get('bootstrap', (None,))[0] and res.get('poisson', (None,))[0]:
        print(f"Poisson understates the bootstrap requirement by {1 - res['poisson'][0]/res['bootstrap'][0]:.1%}")


if __name__ == '__main__':
    main()
