"""EXPLORATORY 2 (post hoc; chosen after seeing the event-study and the exploratory-seasonality results; not in ANALYSIS_PLAN.md).
Splits the post period into an early window (April-May, one to two months after the war began on 28 Feb 2026) and a late window (June-August),
and allows tier-specific and distance-specific seasonality AND linear trends, so the post coefficients are deviations from each group's own
seasonal pattern and long-run trend. The same model is run on the placebo (fake shock 2025-04; early = Apr-May 2025, late = Jun-Aug 2025).
Usage: python analysis_oil_exploratory2.py WORKDIR"""
import sys, json, warnings
src = open(__file__.replace("analysis_oil_exploratory2.py", "analysis_oil.py")).read()
exec(src.split("res = {}\ndef main_models")[0])
res = {}
def run(P, first_post_t, label):
    cal = ((P.t.astype("int32") + P_M0) % 12); names = []
    for c in range(12):
        if c == 1: continue
        P[f"Lm{c}"] = (P.Low * (cal == c)).astype("float32"); P[f"Dm{c}"] = (P.logDist * (cal == c)).astype("float32"); names += [f"Lm{c}", f"Dm{c}"]
    P["Ltr"] = (P.Low * P.yr).astype("float32"); P["Mtr"] = (P.Mid * P.yr).astype("float32"); P["Dtr"] = (P.logDist * P.yr).astype("float32"); names += ["Ltr", "Mtr", "Dtr"]
    early = ((P.t >= first_post_t) & (P.t <= first_post_t + 1)).astype("int8"); late = (P.t >= first_post_t + 2).astype("int8")
    for nm, w in (("Early", early), ("Late", late)):
        P[f"Low{nm}"] = (P.Low * w).astype("int8"); P[f"Mid{nm}"] = (P.Mid * w).astype("int8"); P[f"Dist{nm}"] = (P.logDist * w).astype("float32")
    m = pf.fepois("y ~ LowEarly + MidEarly + DistEarly + LowLate + MidLate + DistLate + " + " + ".join(names) + " | key + cym", data=P, vcov={"CRV1": "key"})
    mc = m.vcov({"CRV1": "city_id"})
    for k in ("LowEarly", "MidEarly", "DistEarly", "LowLate", "MidLate", "DistLate"):
        res[f"{label}: {k}"] = tid(m, k); res[f"{label}: city-clustered {k}"] = tid(mc, k)
    json.dump(res, open("results_oil_exploratory2.json", "w"), indent=1); log(label, "done")
P_M0 = mi(2023, 1); P0, Li = build(P_M0, mi(2026, 8), mi(2024, 3), mi(2025, 2)); Pm = setpost(P0, P_M0, mi(2026, 4)); run(Pm, mi(2026, 4) - P_M0, "main")
del P0, Pm
P_M0 = mi(2022, 1); Pp0, Lp = build(P_M0, mi(2025, 8), mi(2023, 3), mi(2024, 2)); Pp = setpost(Pp0, P_M0, mi(2025, 4)); run(Pp, mi(2025, 4) - P_M0, "placebo")
for k, v in res.items(): print(k, {a: round(b, 4) for a, b in v.items()})
