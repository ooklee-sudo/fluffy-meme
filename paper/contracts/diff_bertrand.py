"""Differentiated Bertrand (logit) competition among n vendors for a population of firms.
Firm i's utility from vendor j's contract = (cost saving vs human-only at the firm's optimal attempt cap) + sigma*eps_ij ; outside option (human only) has saving 0.
sigma = degree of differentiation (sigma->0: homogeneous Bertrand; large sigma: strong vendor market power). Vendors choose the price of a given contract form (per-attempt fee w or success fee f)."""
import numpy as np
from contracts import Mkt
GRID = 500
def curves(m, kind):
    ps = np.linspace(m.k if kind == "A" else 0.0, m.H, GRID)
    F = np.zeros(GRID); Pi = np.zeros(GRID); N = np.zeros(GRID, int); Wm = np.zeros(GRID)
    for i, p in enumerate(ps):
        r = m.per_attempt(p) if kind == "A" else m.success_fee(p)
        F[i] = m.H - r['firm']; Pi[i] = r['vend']; N[i] = r['N']; Wm[i] = r['welfare']
    return ps, F, Pi, N, Wm
def share(F_own, F_riv, n, sig):          # logit with outside option (human-only, saving 0)
    a = F_own/sig; b = F_riv/sig; mx = max(a, b, 0.0)
    num = np.exp(a - mx); den = np.exp(-mx) + num + (n-1)*np.exp(b - mx)
    return num/den
def share_vec(F_own, F_riv, n, sig):
    a = F_own/sig; b = F_riv/sig; mx = np.maximum(np.maximum(a, b), 0.0)
    num = np.exp(a - mx); den = np.exp(-mx) + num + (n-1)*np.exp(b - mx); return num/den
def best_response(cv, F_riv, n, sig):
    ps, F, Pi, N, Wm = cv
    prof = share_vec(F, F_riv, n, sig)*Pi; i = int(np.argmax(prof)); return i, prof[i]
def sym_eq(cv, n, sig):
    ps, F, Pi, N, Wm = cv; best = None
    for j in range(len(ps)):            # candidate rival price index
        i, _ = best_response(cv, F[j], n, sig); gap = abs(ps[i] - ps[j])
        if best is None or gap < best[0]: best = (gap, j, i)
    gap, j, i = best; return j if gap < 1e-9 else i, gap     # take the best-response index when fixed point not exact
def summarize(m, kind, n, sig, cv):
    ps, F, Pi, N, Wm = cv; j, gap = sym_eq(cv, n, sig)
    # symmetric outcome at price index j
    s = share(F[j], F[j], n, sig); cs = sig*np.log(1 + n*np.exp(F[j]/sig)); prof_total = n*s*Pi[j]
    return dict(p=ps[j], N=N[j], cover=n*s, F=F[j], Pi=Pi[j], vend_total=prof_total, TW=cs + prof_total, gap=gap, idx=j)
def deviation_gain(m, eq, cvs, kind_from, kind_to, n, sig):
    """Profit of a vendor deviating to the other form against rivals' equilibrium contract."""
    cvA = cvs[kind_from]; Fr = cvA[1][eq['idx']]
    cvB = cvs[kind_to]; i, prof = best_response(cvB, Fr, n, sig)
    s_eq = share(cvA[1][eq['idx']], Fr, n, sig)*cvA[2][eq['idx']]
    return prof, s_eq
if __name__ == "__main__":
    out = []; P = out.append
    m = Mkt(.12, .39, 100., 1., .2); cvs = {k: curves(m, k) for k in "AB"}; fb = m.first_best()
    P(f"RepairBench-like (a=.12,b=.39), H=100 v=1 k=0.2; first-best N={fb['N']} S^FB={fb['surplus']:.1f}")
    for sig in [1., 3., 10., 30.]:
        TWfb_n = lambda n: sig*np.log(1 + n*np.exp(fb['surplus']/sig))
        P(f"\n sigma = {sig}")
        P("  n | form |  price   N  coverage  firm saving  vendor profit(per firm)  total vendor profit | welfare/FB | deviation to other form profitable?")
        for n in [1, 2, 3, 5, 10]:
            res = {}
            for kind in "AB":
                res[kind] = summarize(m, kind, n, sig, cvs[kind])
            for kind in "AB":
                r = res[kind]; other = "B" if kind == "A" else "A"
                dev, base = deviation_gain(m, r, cvs, kind, other, n, sig)
                P(f"  {n:2d} |  {kind}   | {r['p']:7.2f} {r['N']:3d}  {r['cover']:6.2f}   {r['F']:8.2f}    {r['Pi']:8.2f}              {r['vend_total']:8.3f}       | {r['TW']/TWfb_n(n):6.3f}    | {'yes' if dev > base*(1+1e-6) + 1e-9 else 'no '} (dev {dev:.3f} vs eq {base:.3f})")
    open("results_diff_bertrand.txt", "w").write("\n".join(out)); print("\n".join(out))
