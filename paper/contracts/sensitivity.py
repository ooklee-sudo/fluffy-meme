"""Sensitivity of the main conclusions over calibrated ranges of (H, v, k) and three heterogeneity profiles. Exact enumeration of budget steps (no price grids)."""
import numpy as np, itertools
from scipy.special import betaln
def stats(a, b, H, v, k, J=2000):
    n = np.arange(J+1); S = np.exp(betaln(a, b+n) - betaln(a, b)); E = np.concatenate([[0], np.cumsum(S)])[:J+1]; Pn = 1 - S
    q = a/(a+b+np.arange(J))
    W = H*Pn - (k+v)*E
    fb = int(np.argmax(W[:J])) if (q[0]*H > k+v) else 0
    res = dict(NFB=fb, SFB=W[fb] if fb else 0.0)
    if fb == 0: return res
    nmax = min(int(a*H/v)+2, J-1)
    best = {"A": (-1, 0, 0), "B": (-1, 0, 0)}                          # (profit, n, firm saving)
    for m in range(1, nmax+1):
        if q[m-1]*H <= v: break
        wcap = q[m-1]*H - v
        if wcap >= k:
            pr = (wcap - k)*E[m]
            if pr > best["A"][0]: best["A"] = (pr, m, W[m] - pr)
        phi = H - v/q[m-1]
        if phi >= 0:
            pr = phi*Pn[m] - k*E[m]
            if pr > best["B"][0]: best["B"] = (pr, m, W[m] - pr)
    Gmin = v*(Pn[fb]/q[fb-1] - E[fb])
    res.update(A=best["A"], B=best["B"], WA=W[best["A"][1]] if best["A"][1] else 0, WB=W[best["B"][1]] if best["B"][1] else 0, rent_share=Gmin/W[fb], W=W)
    return res
profiles = {"RepairBench-like (0.12,0.39)": (.12, .39), "SWE-Verified-like (0.25,0.34)": (.25, .34), "HumanEvalFix-Llama-like (0.50,0.58)": (.50, .58)}
regimes = {
 "Function-level, automated verification": dict(H=[15, 30, 50, 100, 200, 400], v=[.01, .03, .1, .3, .5], k=[.0003, .001, .003, .01, .03, .1]),
 "Function-level, manual triage per attempt": dict(H=[15, 30, 50, 100, 200, 400], v=[3, 5, 8, 15], k=[.0003, .001, .003, .01, .03, .1]),
 "Repository-level agentic": dict(H=[50, 100, 200, 400, 800], v=[.1, .5, 2, 5], k=[.6, .64, .84, 1.5, 3.]),
}
out = []; P = out.append
for rname, rg in regimes.items():
    P(f"\n=== {rname}:  H in {rg['H']}, v in {rg['v']}, k in {rg['k']}")
    P("profile | grid pts | AI worth using (N^FB>=1) | among those: welfare success fee > per-attempt | vendor profit B>=A | firm saving B>A | median W/FB: A, B | median N^FB, n_hat(B) | n_hat(B)<N^FB | rent share of W(N^FB): median [min-max]")
    for pname, (a, b) in profiles.items():
        rows = []; tot = 0
        for H, v, k in itertools.product(rg['H'], rg['v'], rg['k']):
            tot += 1; r = stats(a, b, H, v, k)
            if r['NFB'] >= 1 and r['A'][1] > 0 and r['B'][1] > 0: rows.append(r)
        if not rows: P(f"{pname} | {tot} | 0%"); continue
        n = len(rows)
        wa = np.array([r['WA']/r['SFB'] for r in rows]); wb = np.array([r['WB']/r['SFB'] for r in rows])
        P(f"{pname:36s} | {tot:3d} | {100*n/tot:3.0f}% | {100*np.mean(wb > wa + 1e-9):3.0f}% | {100*np.mean([r['B'][0] >= r['A'][0] - 1e-9 for r in rows]):3.0f}% | {100*np.mean([r['B'][2] > r['A'][2] for r in rows]):3.0f}% | {np.median(wa):.2f}, {np.median(wb):.2f} | {np.median([r['NFB'] for r in rows]):.0f}, {np.median([r['B'][1] for r in rows]):.0f} | {100*np.mean([r['B'][1] < r['NFB'] for r in rows]):3.0f}% | {100*np.median([r['rent_share'] for r in rows]):.0f}% [{100*min(r['rent_share'] for r in rows):.0f}-{100*max(r['rent_share'] for r in rows):.0f}%]")
open("results_sensitivity.txt", "w").write("\n".join(out)); print("\n".join(out))
