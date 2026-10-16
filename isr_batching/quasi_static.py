"""Quasi-static batched-serving model: exact delay/toll, first-best, flat price,
G-level schedules (Sections 3, 4.1-4.4; numbers for Sections 6.2, 6.3, 6.5, 6.7, Table B5).

Units: time = isolated service time, value/price/delay cost = cost of waiting one isolated service time.
Single engine with batch cap M and speed rho(n) = (1+b)/(1+b*min(n,M)), b = beta/alpha.
Random routing over c engines is equivalent (percent losses are invariant), so one engine suffices;
dedicated servers = b = 0 with M = number of servers.

Demand scale ("unpriced demand = r x capacity"): Lambda_k = r * mubar * shape_k.  norm='mean' (default, Sec. 6;
reproduces the dedicated-server numbers 14.7% / 4.6% / 44.1% of the manuscript) uses shape_k = profile_k/mean(profile),
so the peak phase has Lambda = r * peak/mean * mubar (= 3.0 mubar for r = 1.4).  norm='max' (Table B5: "peak unpriced
demand 1.4 times capacity") uses shape_k = profile_k/max(profile).
"""
import argparse, json
import numpy as np
from scipy.optimize import brentq, minimize_scalar


class Engine:
    def __init__(self, M, b):
        self.M, self.b = int(M), float(b)
        n = np.arange(0, self.M + 2)
        rho = (1 + self.b) / (1 + self.b * np.minimum(np.maximum(n, 1), self.M))
        self.mu = np.minimum(n, self.M) * rho            # mu[0] = 0
        self.mubar = self.M * (1 + self.b) / (1 + self.b * self.M)
        self.logcum = np.concatenate([[0.0], np.cumsum(np.log(self.mu[1:self.M + 1]))])  # sum_{i<=n} log mu(i)
        n0 = np.arange(0, self.M + 1)
        self.r1 = (n0 + 1) / self.mu[n0 + 1]             # r_{n+1}, n = 0..M
        self.fw = np.maximum(n0 + 1 - self.M, 0) / self.mu[n0 + 1]   # (n+1-M)+/mu(n+1)

    def stats(self, lam):
        """Exact stationary quantities at arrival rate lam < mubar."""
        M, mb = self.M, self.mubar
        x = lam / mb
        n = np.arange(0, M + 1)
        lw = n * np.log(lam) - self.logcum
        lw -= lw.max()
        w = np.exp(lw)
        wM = w[-1]
        S0, S1, S2 = x / (1 - x), x / (1 - x) ** 2, x * (1 + x) / (1 - x) ** 3
        Z = w.sum() + wM * S0

        def E(expl, a0, a1, a2):                         # E f(N); tail f(M+j)=a0+a1 j+a2 j^2, j>=1
            return ((w * expl).sum() + wM * (a0 * S0 + a1 * S1 + a2 * S2)) / Z
        EN = E(n, M, 1, 0)
        ENf = E(n * (n - 1.0), M * (M - 1), 2 * M - 1, 1)             # E N(N-1)
        Er = E(self.r1, (M + 1) / mb, 1 / mb, 0)                      # = d
        Efw = E(self.fw, 1 / mb, 1 / mb, 0)                           # = waiting delay
        ENr = E(n * self.r1, (M * (M + 1)) / mb, (2 * M + 1) / mb, 1 / mb)
        ENfw = E(n * self.fw, M / mb, (M + 1) / mb, 1 / mb)
        d = EN / lam
        t = (ENf - EN ** 2) / lam                                     # (Var N - E N)/lam
        tW = ENfw - EN * Efw
        return dict(d=d, t=t, tW=tW, tS=t - tW, w=Efw, s=d - Efw, d_check=Er, t_check=ENr - EN * d)

    def d(self, lam): return self.stats(lam)['d'] if lam > 0 else 1.0
    def t(self, lam): return self.stats(lam)['t'] if lam > 0 else 0.0

    def tprime(self, lam):
        h = max(1e-6, 1e-5 * lam)
        h = min(h, 0.4 * (self.mubar - lam))
        lo = max(lam - h, 1e-12)
        return (self.t(lam + h) - self.t(lo)) / (lam + h - lo)


class Phase:
    def __init__(self, eng, V, Lam, pi):
        self.e, self.V, self.Lam, self.pi = eng, V, Lam, pi
        self.hi = min(Lam, eng.mubar) * (1 - 1e-10)

    def P(self, lam): return self.V * (1 - lam / self.Lam)

    def rate(self, p):
        if p >= self.V - 1: return 0.0
        f = lambda l: self.P(l) - self.e.d(l) - p
        return brentq(f, 1e-14, self.hi, xtol=1e-13, rtol=1e-12)

    def welfare_at_rate(self, lam):
        if lam <= 0: return 0.0
        return self.V * (lam - lam ** 2 / (2 * self.Lam)) - lam * self.e.d(lam)

    def W(self, p): return self.welfare_at_rate(self.rate(p))

    def first_best(self):
        g = lambda l: self.P(l) - self.e.d(l) - self.e.t(l)
        lam = brentq(g, 1e-14, self.hi, xtol=1e-13, rtol=1e-12)
        return lam, self.e.t(lam)

    def kappa(self, p):
        lam = self.rate(p)
        h = 1e-6 * max(lam, 1e-3)
        dp = (self.e.d(lam + h) - self.e.d(max(lam - h, 1e-12))) / (lam + h - max(lam - h, 1e-12))
        return 1.0 / (self.V / self.Lam + dp)


def make_phases(profile, M, b, V, ratio, c0=0.0, pi=None, norm='mean'):
    eng = Engine(M, b)
    prof = np.asarray(profile, float)
    shape = prof / (prof.mean() if norm == 'mean' else prof.max())
    K = len(prof)
    pi = np.full(K, 1.0 / K) if pi is None else np.asarray(pi, float)
    return eng, [Phase(eng, V - c0, ratio * eng.mubar * shape[k], pi[k]) for k in range(K)]


def cosine_profile(K=24, peak=2.15, trough=0.24):
    """Stylized daily cycle with the same peak/trough/mean as Azure 2024 (Table B5 profile)."""
    mean, amp = (peak + trough) / 2, (peak - trough) / 2
    return mean + amp * np.cos(2 * np.pi * (np.arange(K) - 17) / K)


def load_hourly_profile(path, ts_col='TIMESTAMP'):
    """Hour-of-day rate profile from a trace CSV (Azure format: TIMESTAMP, ContextTokens, GeneratedTokens)."""
    import pandas as pd
    df = pd.read_csv(path, usecols=[ts_col])
    ts = pd.to_datetime(df[ts_col])
    counts = ts.dt.floor('h').value_counts().sort_index()
    byhour = counts.groupby(counts.index.hour).mean()
    return byhour.reindex(range(24)).to_numpy()


# ---------------------------------------------------------------- schedules
def price_grid(V, n=600):
    # denser near low prices where tolls live
    return np.concatenate([np.linspace(0, 0.1 * V, n // 2, endpoint=False), np.linspace(0.1 * V, V - 1, n - n // 2)])


def welfare_matrix(phases, grid):
    return np.array([[ph.W(p) for p in grid] for ph in phases])         # K x P


def dp_levels(Wm, pi, order, G):
    """Best G-level schedule; groups contiguous in `order` (Prop. 8(ii)). Returns (welfare, groups, grid idx)."""
    K, P = Wm.shape
    Wo, po = Wm[order] * pi[order][:, None], pi[order]
    cum = np.vstack([np.zeros(P), np.cumsum(Wo, axis=0)])
    cost, arg = np.zeros((K + 1, K + 1)), np.zeros((K + 1, K + 1), int)
    for i in range(K):
        for j in range(i + 1, K + 1):
            s = cum[j] - cum[i]
            arg[i, j] = int(np.argmax(s)); cost[i, j] = s[arg[i, j]]
    best = np.full((G + 1, K + 1), -np.inf); back = np.zeros((G + 1, K + 1), int)
    best[0, 0] = 0
    for g in range(1, G + 1):
        for j in range(g, K + 1):
            for i in range(g - 1, j):
                v = best[g - 1, i] + cost[i, j]
                if v > best[g, j]: best[g, j], back[g, j] = v, i
    groups, j = [], K
    for g in range(G, 0, -1):
        i = back[g, j]; groups.append((i, j, arg[i, j])); j = i
    groups = groups[::-1]
    return best[G, K], [(list(order[i:j]), a) for i, j, a in groups]


def analyse(profile, M, b, V=20.0, ratio=1.4, c0=0.0, pi=None, Gs=(2, 3, 4, 6), ngrid=600, verbose=False, norm='mean'):
    eng, ph = make_phases(profile, M, b, V, ratio, c0, pi, norm)
    K = len(ph); pis = np.array([p.pi for p in ph])
    fb = [p.first_best() for p in ph]
    lam_s, p_s = np.array([f[0] for f in fb]), np.array([f[1] for f in fb])
    stats = [eng.stats(l) for l in lam_s]
    Wfb = sum(pis[k] * ph[k].welfare_at_rate(lam_s[k]) for k in range(K))
    # flat price
    res = minimize_scalar(lambda p: -sum(pis[k] * ph[k].W(p) for k in range(K)),
                          bounds=(p_s.min(), p_s.max()), method='bounded', options=dict(xatol=1e-10))
    p_flat = res.x; Wflat = -res.fun
    Wnone = sum(pis[k] * ph[k].W(0.0) for k in range(K))
    out = dict(M=M, b=b, V=V, ratio=ratio, c0=c0, mubar=eng.mubar,
               loss_flat=1 - Wflat / Wfb, loss_noprice=1 - Wnone / Wfb, p_flat=p_flat + c0,
               toll_lowest=float(p_s.min()), toll_peak=float(p_s.max()),
               toll_lower_quartile=float(np.quantile(p_s, 0.25)),
               slow_share_lowQ=float(np.mean([s['tS'] / s['t'] if s['t'] > 1e-12 else np.nan
                                              for s, p in zip(stats, p_s) if p <= np.quantile(p_s, 0.25) + 1e-12])),
               slow_share_peak=float(stats[int(np.argmax(p_s))]['tS'] / max(stats[int(np.argmax(p_s))]['t'], 1e-12)),
               tolls=(p_s + c0).tolist(), toll_W=[s['tW'] for s in stats], toll_S=[s['tS'] for s in stats],
               max_consistency_err=max(abs(s['d'] - s['d_check']) + abs(s['t'] - s['t_check']) for s in stats))
    # G-level (exact) via DP on price grid
    grid = price_grid(V - c0, ngrid)
    Wm = welfare_matrix(ph, grid)
    order = list(np.argsort(p_s))
    # quadratic prediction (Prop. 8)
    omega = np.array([ph[k].kappa(p_s[k]) * (1 + ph[k].kappa(p_s[k]) * eng.tprime(lam_s[k])) for k in range(K)])
    wq = pis * omega
    def qloss(G):
        x = p_s[order]; w = wq[order]
        K_ = len(x); cs = np.concatenate([[0], np.cumsum(w)]); c1 = np.concatenate([[0], np.cumsum(w * x)])
        c2 = np.concatenate([[0], np.cumsum(w * x * x)])
        ss = lambda i, j: (c2[j] - c2[i]) - (c1[j] - c1[i]) ** 2 / (cs[j] - cs[i])
        best = np.full((G + 1, K_ + 1), np.inf); best[0, 0] = 0
        for g in range(1, G + 1):
            for j in range(g, K_ + 1):
                best[g, j] = min(best[g - 1, i] + ss(i, j) for i in range(g - 1, j))
        return 0.5 * best[G, K_]
    q1 = qloss(1)
    q = wq / wq.sum(); mu_x = (q * p_s).sum(); sig = np.sqrt((q * (p_s - mu_x) ** 2).sum())
    mad = (q * np.abs(p_s - mu_x)).sum()
    out['bound_cor9a'] = float((mad / sig) ** 2) if sig > 0 else np.nan
    Wflat_grid = max(sum(pis[k] * Wm[k, j] for k in range(K)) for j in range(len(grid)))
    loss_flat_abs = Wfb - Wflat
    out['levels'] = {}
    for G in Gs:
        Wg, groups = dp_levels(Wm, pis, order, G)
        Wg = max(Wg, Wflat)  # grid cannot do worse than the continuous flat optimum
        rec = (Wg - Wflat) / loss_flat_abs if loss_flat_abs > 0 else np.nan
        out['levels'][G] = dict(recovery_exact=float(rec), recovery_quad=float(1 - qloss(G) / q1) if q1 > 0 else np.nan,
                                loss=float(1 - Wg / Wfb),
                                prices=[float(grid[a] + c0) for _, a in groups],
                                groups=[[int(h) for h in sorted(g)] for g, _ in groups])
    return out


def implied_c0_for_ratio(profile, M, b, V, ratio, target=2.0, **kw):
    """c0/V at which the best two-level schedule's price ratio (incl. c0) equals `target` (Sec. 6.7)."""
    def f(c0frac):
        o = analyse(profile, M, b, V, ratio, c0=c0frac * V, Gs=(2,), **kw)
        p = o['levels'][2]['prices']; return max(p) / min(p) - target
    try:
        return brentq(f, 0.0, 0.6, xtol=1e-3)
    except ValueError:
        return float('nan')


def constrained_ratio_loss(profile, M, b, V, ratio, c0, r=2.0, ngrid=300, norm='mean'):
    """Best two-level schedule with peak = r * off-peak price (incl. c0) and DeepSeek-style fixed peak length."""
    eng, ph = make_phases(profile, M, b, V, ratio, c0, norm=norm)
    K = len(ph); pis = np.array([p.pi for p in ph])
    Wfb = sum(pis[k] * ph[k].welfare_at_rate(ph[k].first_best()[0]) for k in range(K))
    grid = np.linspace(0, V - c0 - 1, ngrid)
    Wm = welfare_matrix(ph, grid)
    order = np.argsort([p.Lam for p in ph])
    best = -np.inf
    for hpk in range(1, K):                       # number of peak hours
        peak = order[-hpk:]; off = order[:-hpk]
        for j, plo in enumerate(grid):            # off-peak tax (excl. c0): p_lo = grid
            phi = r * (plo + c0) - c0
            if phi > grid[-1]: break
            jh = int(np.searchsorted(grid, phi))
            v = pis[off] @ Wm[off, j] + pis[peak] @ Wm[peak, min(jh, len(grid) - 1)]
            best = max(best, v)
    return 1 - best / Wfb


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--M', type=int, required=True, help='batch cap (or #servers if b=0)')
    ap.add_argument('--b', type=float, default=0.0, help='beta/alpha (0 = dedicated servers)')
    ap.add_argument('--V', type=float, default=20.0); ap.add_argument('--ratio', type=float, default=1.4)
    ap.add_argument('--c0', type=float, default=0.0, help='serving cost per request (absolute, same units as V)')
    ap.add_argument('--profile', default='cosine', help="'cosine' or path to Azure trace CSV")
    ap.add_argument('--norm', default='mean', choices=['mean', 'max'])
    ap.add_argument('--json', default=None)
    a = ap.parse_args()
    prof = cosine_profile() if a.profile == 'cosine' else load_hourly_profile(a.profile)
    o = analyse(prof, a.M, a.b, a.V, a.ratio, a.c0, norm=a.norm)
    print(f"mubar={o['mubar']:.2f}  flat loss={o['loss_flat']:.3%}  no-price loss={o['loss_noprice']:.3%}")
    print(f"tolls: lowest={o['toll_lowest']:.3f} lowerQ={o['toll_lower_quartile']:.3f} peak={o['toll_peak']:.3f}; "
          f"slowdown share lowerQ={o['slow_share_lowQ']:.0%} peak={o['slow_share_peak']:.0%}")
    print(f"Cor.9(a) bound={o['bound_cor9a']:.2f}  (consistency err {o['max_consistency_err']:.1e})")
    for G, v in o['levels'].items():
        print(f"G={G}: recovery exact={v['recovery_exact']:.2f} quad={v['recovery_quad']:.2f} "
              f"loss={v['loss']:.3%} prices={np.round(v['prices'], 2)}")
    if a.json: json.dump(o, open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
