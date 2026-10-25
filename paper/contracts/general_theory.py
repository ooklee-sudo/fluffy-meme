"""Distribution-free verification (arbitrary mixing distribution F on p, e.g., finite mixtures, zero-inflated).
Checks: (1) q_n nonincreasing for any F; (2) incentive-rent theorem: for every contract (w>=0,f) inducing depth N,
Pi(w,f) <= R(N) - (w/v) G_min(N), with R(N)=W(N)-G_min(N), G_min(N)=v[P(N)/q_{N-1}-E(N)];
(3) increment formula; (4) the vendor's optimum over the 2-parameter class has w=0 (pure success fee); (5) lump-sum fee => first best."""
import numpy as np
rng = np.random.default_rng(99); out = []; P_ = out.append
JJ = 400
class Gen:
    def __init__(s, ps, ws):
        s.ps, s.ws = np.array(ps), np.array(ws)/np.sum(ws); n = np.arange(JJ+1)
        s.S = (s.ws[:, None]*(1-s.ps[:, None])**n[None, :]).sum(0)          # S(j)=E[(1-p)^j]
        s.q = np.array([ (s.ws*s.ps*(1-s.ps)**j).sum()/s.S[j] if s.S[j] > 1e-300 else 0 for j in range(JJ)])
        s.cum = np.concatenate([[0], np.cumsum(s.S)])
    def E(s, N): return s.cum[N]
    def Pr(s, N): return 1 - s.S[N]
def depth(g, w, f, v, H):               # firm continues at n iff q_n (H-f) > w+v (stop when indifferent)
    idx = np.nonzero(g.q*(H-f) <= w+v)[0]; return int(idx[0]) if len(idx) else JJ-1
viol = dict(q=0, bound=0, incr=0, n=0, wpos=0, lump=0)
best_w0 = 0; tested = 0; n1 = 0; nbad = 0; ubviol = 0; gaps = []
for t in range(200):
    kmix = rng.integers(2, 6); ps = rng.uniform(0, 1, kmix)**rng.uniform(1, 4)
    if rng.random() < .4: ps[0] = 0.0                               # unsolvable atom
    ws = rng.dirichlet(np.ones(kmix)); g = Gen(ps, ws)
    H = np.exp(rng.uniform(np.log(30), np.log(300))); v = H*np.exp(rng.uniform(np.log(.003), np.log(.03))); k = v*np.exp(rng.uniform(np.log(.2), np.log(2)))
    if (np.diff(g.q[:100]) > 1e-12).any(): viol['q'] += 1
    W = lambda N: H*g.Pr(N) - (k+v)*g.E(N)
    Gmin = lambda N: v*(g.Pr(N)/g.q[N-1] - g.E(N)) if N >= 1 and g.q[N-1] > 0 else np.nan
    Rf = lambda N: W(N) - Gmin(N)
    # (2) random contracts
    for _ in range(300):
        w = rng.uniform(0, H*.5); f = rng.uniform(0, H); N = depth(g, w, f, v, H)
        if N < 1 or g.q[N-1] <= 0: continue
        Pi = (w-k)*g.E(N) + f*g.Pr(N)
        viol['n'] += 1
        if Pi > Rf(N) - (w/v)*Gmin(N) + 1e-7*max(1, abs(Pi)): viol['bound'] += 1
    # (3) increment formula
    for N in range(1, 40):
        if g.q[N] <= 1e-12 or g.q[N-1] <= 1e-12: break
        lhs = Rf(N+1) - Rf(N); rhs = g.S[N]*(g.q[N]*H - (k+v)) - v*g.Pr(N)*(1/g.q[N] - 1/g.q[N-1])
        if abs(lhs - rhs) > 1e-7*max(1, abs(rhs)): viol['incr'] += 1
    # (4) vendor optimum over (w,f) grid has w ~ 0
    best = (-1e9, None)
    for w in np.linspace(0, H*.4, 60):
        for f in np.linspace(0, H, 120):
            N = depth(g, w, f, v, H)
            if N < 1: continue
            if v*g.E(N) + (w*g.E(N) + f*g.Pr(N)) + H*(1-g.Pr(N)) > H + 1e-9: continue
            Pi = (w-k)*g.E(N) + f*g.Pr(N)
            if Pi > best[0]: best = (Pi, (w, f, N))
    Rmax = max(Rf(N) for N in range(1, JJ-1) if g.q[N-1] > 1e-12 and not np.isnan(Rf(N))) if (g.q[:JJ-2] > 1e-12).any() else None
    if best[1] is not None and Rmax is not None:
        bad = best[0] > Rmax + 1e-7*max(1, abs(Rmax)); ubviol += bad
        if bad: print('VIOL', best, Rmax, 'qN', g.q[best[1][2]-1], 'ps', np.round(g.ps,3), 'ws', np.round(g.ws,2), 'H,v,k', round(H,1), round(v,2), round(k,2))
        gaps.append((Rmax - best[0])/max(abs(Rmax), 1e-9))
    if best[1] is not None:
        tested += 1; ok = best[1][0] <= H*.4/59 + 1e-9; best_w0 += ok or best[1][2] == 1; n1 += (not ok) and best[1][2] == 1; nbad += (not ok) and best[1][2] > 1                 # w within one grid step of 0
    # (5) lump sum: w=k, F=S^FB -> first best
    Nfb = int(np.nonzero(g.q*H <= k+v)[0][0]) if (g.q*H <= k+v).any() else JJ-1
    N_k = depth(g, k, 0, v, H)
    if N_k != Nfb: viol['lump'] += 1
P_(f"200 random heterogeneity distributions (finite mixtures with 2-5 atoms, 40% with an unsolvable atom p=0)")
P_(f"(1) q_n nonincreasing: violations {viol['q']}")
P_(f"(2) Pi(w,f) <= R(N) - (w/v) G_min(N): {viol['bound']} violations in {viol['n']} contracts")
P_(f"(3) increment formula R(N+1)-R(N) = S(N)[q_N H-(k+v)] - v P(N)(1/q_N - 1/q_(N-1)): violations {viol['incr']}")
P_(f"(4) vendor's grid-optimal contract has per-attempt fee within one grid step of 0, or induces a single attempt (where G_min=0 and the forms tie), in {best_w0} of {tested} distributions; of the exceptions to w=0, {n1} are single-attempt ties and {nbad} are other")
P_(f"(5) w=k implements first-best depth under every distribution: violations {viol['lump']}")
P_(f"(6) grid-optimal profit never exceeds max_N R(N) (violations {ubviol}); relative gap to max_N R(N): median {np.median(gaps)*100:.2f}%, max {np.max(gaps)*100:.2f}% (grid resolution)")
open("results_general_theory.txt", "w").write("\n".join(out)); print("\n".join(out))
