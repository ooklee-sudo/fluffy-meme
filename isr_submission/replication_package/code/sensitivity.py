"""Sensitivity of the LLM-adoption value to the economic parameters (c_f, LLM cost premium).

Fits the NegBin model once on the seed-42 simulated data, then sweeps a grid over
  c_f  : cost of a residual (field) fault, in units of one human testing-budget unit
  prem : LLM cost per budget unit relative to human (c_LLM / c_human)
and reports, per complexity level, posterior mean V = C*_human - C*_LLM and P(V>0), next to the
true-parameter V. Also finds the break-even c_f (posterior-mean V = 0) for each premium.

Run: python3 sensitivity.py
"""
import numpy as np
import pandas as pd
import pymc as pm
import nhpp_llm_econ as M

CF = [0.5, 1, 2, 3, 5, 8, 12, 20]
PREM = [1.0, 1.3, 1.6, 2.0, 3.0]
CX = [-1.0, 0.0, 1.0]

cx, proj, llm, Y, t = M.simulate()
with M.build(cx, proj, llm, Y, t, True):
    idata = pm.sample(1000, tune=1500, chains=4, cores=4, target_accept=0.9,
                      random_seed=1, progressbar=False)

# H5: do Poisson-based decisions overstate confidence? compare V interval width / P(V>0)
with M.build(cx, proj, llm, Y, t, False):
    idata_p = pm.sample(1000, tune=1500, chains=4, cores=4, target_accept=0.9,
                        random_seed=1, progressbar=False)
print("\n##### H5: Poisson vs NegBin at default economics (c_f=3, premium 1.3)")
for cx0 in CX:
    for name, idt in (("poisson", idata_p), ("negbin", idata)):
        _, Cs, _ = M.economics(idt.posterior, cx0)
        V = Cs[0] - Cs[1]
        lo, hi = np.percentile(V, [5.5, 94.5])
        print(f"cx={cx0:+.0f} {name:8s} V mean {V.mean():6.2f}  89% width {hi - lo:6.2f}  P(V>0)={(V > 0).mean():.2f}")

rows = []
for cx0 in CX:
    for prem in PREM:
        for cf in CF:
            ct = {0: 1.0, 1: prem}
            _, Cs, _ = M.economics(idata.posterior, cx0, cf=cf, ct=ct)
            _, Ct = M.truth(cx0, cf=cf, ct=ct)
            V = Cs[0] - Cs[1]
            rows.append(dict(cx=cx0, prem=prem, cf=cf, V_mean=V.mean(), P_pos=(V > 0).mean(),
                             V_true=Ct[0] - Ct[1]))
df = pd.DataFrame(rows)
df.to_csv("sensitivity_results.csv", index=False)

pd.set_option("display.width", 200)
for cx0 in CX:
    sub = df[df.cx == cx0]
    print(f"\n##### complexity cx={cx0:+.0f}")
    print("Posterior mean V (rows: LLM cost premium, cols: c_f)")
    print(sub.pivot(index="prem", columns="cf", values="V_mean").round(1))
    print("P(V>0)")
    print(sub.pivot(index="prem", columns="cf", values="P_pos").round(2))
    print("True V")
    print(sub.pivot(index="prem", columns="cf", values="V_true").round(1))

print("\n##### Range of c_f where posterior-mean V>0 (fine grid); '-' = never")
fine = np.linspace(0.3, 40, 400)
for cx0 in CX:
    for prem in PREM:
        vals = np.array([(lambda Cs: (Cs[0] - Cs[1]).mean())(
            M.economics(idata.posterior, cx0, cf=cf, ct={0: 1.0, 1: prem})[1]) for cf in fine])
        pos = fine[vals > 0]
        rng = f"[{pos.min():.1f}, {pos.max():.1f}]" if len(pos) else "-"
        tvals = np.array([(lambda Cs: Cs[0] - Cs[1])(
            M.truth(cx0, cf=cf, ct={0: 1.0, 1: prem})[1]) for cf in fine])
        tpos = fine[tvals > 0]
        trng = f"[{tpos.min():.1f}, {tpos.max():.1f}]" if len(tpos) else "-"
        print(f"cx={cx0:+.0f} premium={prem:.1f}: posterior V>0 on c_f in {rng:14s} true V>0 on {trng}")
