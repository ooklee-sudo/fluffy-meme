"""EXPLORATORY (post hoc, not in ANALYSIS_PLAN.md): allow tier-specific and distance-specific seasonality.
Because the pre-registered placebo (fake shock 2025-04) reproduced the Low-price coefficient, we re-estimate the main and placebo models
with Low x calendar-month and logDist x calendar-month interactions, so LowPost and DistPost are identified from deviations of the post months
from each tier's own seasonal pattern. Usage: python analysis_oil_exploratory.py WORKDIR   (re-uses build() from analysis_oil by exec of its function section)"""
import sys, json, warnings
src = open(__file__.replace("analysis_oil_exploratory.py", "analysis_oil.py")).read()
head = src.split("res = {}\ndef main_models")[0]          # imports, loaders, build(), tid(), setpost()
exec(head)
res = {}
def seasonal_cols(P):
    cal = ((P.t.astype("int32") + P_M0) % 12)
    names = []
    for c in range(12):
        if c == 1: continue                                      # February (index 1) is the reference month
        P[f"Lm{c}"] = (P.Low * (cal == c)).astype("float32"); P[f"Dm{c}"] = (P.logDist * (cal == c)).astype("float32"); names += [f"Lm{c}", f"Dm{c}"]
    return names
def run(P, label):
    names = seasonal_cols(P)
    m = pf.fepois("y ~ LowPost + MidPost + DistPost + " + " + ".join(names) + " | key + cym", data=P, vcov={"CRV1": "key"})
    for k in ("LowPost", "MidPost", "DistPost"): res[f"{label}: {k}"] = tid(m, k)
    mc = m.vcov({"CRV1": "city_id"})
    for k in ("LowPost", "DistPost"): res[f"{label}: city-clustered {k}"] = tid(mc, k)
    json.dump(res, open("results_oil_exploratory.json", "w"), indent=1); log(label, "done")
P_M0 = mi(2023, 1); P0, Li = build(P_M0, mi(2026, 8), mi(2024, 3), mi(2025, 2)); Pm = setpost(P0, P_M0, mi(2026, 4)); run(Pm, "main (exploratory seasonality)")
del P0, Pm
P_M0 = mi(2022, 1); Pp0, Lp = build(P_M0, mi(2025, 8), mi(2023, 3), mi(2024, 2)); Pp = setpost(Pp0, P_M0, mi(2025, 4)); run(Pp, "placebo (exploratory seasonality)")
for k, v in res.items(): print(k, {a: round(b, 4) for a, b in v.items()})
