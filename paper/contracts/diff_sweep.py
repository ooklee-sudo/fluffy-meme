import numpy as np
from contracts import Mkt
from diff_bertrand import curves, summarize, deviation_gain, share
rng = np.random.default_rng(5); H=None
rows = []; gaps = []
for d in range(40):
    a = rng.uniform(.05, .5); b = np.exp(rng.uniform(np.log(.15), np.log(3))); Hh = np.exp(rng.uniform(np.log(50), np.log(300)))
    v = Hh*np.exp(rng.uniform(np.log(.003), np.log(.02))); k = v*np.exp(rng.uniform(np.log(.2), np.log(2)))
    m = Mkt(a, b, Hh, v, k, J=3000); fb = m.first_best()
    if fb['surplus'] < 1: continue
    cvs = {kk: curves(m, kk) for kk in "AB"}
    for n in [2, 5]:
        for sf in [.03, .1, .3]:
            sig = sf*fb['surplus']              # differentiation scaled to first-best surplus
            res = {kk: summarize(m, kk, n, sig, cvs[kk]) for kk in "AB"}
            step = Hh/500
            devA = deviation_gain(m, res["A"], cvs, "A", "B", n, sig); devB = deviation_gain(m, res["B"], cvs, "B", "A", n, sig)
            TWfb = sig*np.log(1 + n*np.exp(fb['surplus']/sig))
            rows.append(dict(n=n, sf=sf, A_unstable=devA[0] > devA[1]*(1+1e-6)+1e-9, B_stable=devB[0] <= devB[1]*(1+1e-6)+1e-9,
                             wA=res["A"]['TW']/TWfb, wB=res["B"]['TW']/TWfb, NA=res["A"]['N']/max(fb['N'],1), NB=res["B"]['N']/max(fb['N'],1), vendA=res["A"]['vend_total'], vendB=res["B"]['vend_total'], FA=res["A"]['F'], FB=res["B"]['F'],
                             gapok=max(res['A']['gap'], res['B']['gap']) <= 2*step))
out = []; P = out.append
P(f"Sweep: {len(rows)} (parameter draw x n x differentiation) cells; sigma = {{0.03,0.1,0.3}} x first-best surplus; n in {{2,5}}")
P(f"Fixed-point accuracy within two price-grid steps in {100*np.mean([r['gapok'] for r in rows]):.0f}% of cells")
P(f"Per-attempt equilibrium NOT deviation-proof (a vendor gains by switching to a success fee): {100*np.mean([r['A_unstable'] for r in rows]):.0f}% of cells")
P(f"Success-fee equilibrium deviation-proof against a switch to per-attempt: {100*np.mean([r['B_stable'] for r in rows]):.0f}% of cells")
for n in [2, 5]:
    for sf in [.03, .1, .3]:
        R = [r for r in rows if r['n'] == n and r['sf'] == sf]
        P(f"  n={n} sigma={sf:4.2f}S: welfare/FB per-attempt {np.median([r['wA'] for r in R]):.2f}, success fee {np.median([r['wB'] for r in R]):.2f}; budget/FB-depth A {np.median([r['NA'] for r in R]):.2f}, B {np.median([r['NB'] for r in R]):.2f}; vendor profit B>=A in {100*np.mean([r['vendB']>=r['vendA'] for r in R]):.0f}%; firm saving A>B in {100*np.mean([r['FA']>r['FB'] for r in R]):.0f}%  (cells {len(R)})")
open("results_diff_sweep.txt", "w").write("\n".join(out)); print("\n".join(out))
