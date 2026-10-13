"""EXPLORATORY 2b (post hoc): re-estimate the main model of analysis_oil_exploratory2.py with city-clustered standard errors fitted directly
(the vcov() re-computation in exploratory2 returned values identical to the listing-clustered ones and is not used).
Usage: python analysis_oil_exploratory2b.py WORKDIR"""
import sys, json, warnings
src = open(__file__.replace("analysis_oil_exploratory2b.py", "analysis_oil.py")).read()
exec(src.split("res = {}\ndef main_models")[0])
res = {}
P_M0 = mi(2023, 1); P0, Li = build(P_M0, mi(2026, 8), mi(2024, 3), mi(2025, 2)); P = setpost(P0, P_M0, mi(2026, 4)); del P0
first_post_t = mi(2026, 4) - P_M0; cal = ((P.t.astype("int32") + P_M0) % 12); names = []
for c in range(12):
    if c == 1: continue
    P[f"Lm{c}"] = (P.Low * (cal == c)).astype("float32"); P[f"Dm{c}"] = (P.logDist * (cal == c)).astype("float32"); names += [f"Lm{c}", f"Dm{c}"]
P["Ltr"] = (P.Low * P.yr).astype("float32"); P["Mtr"] = (P.Mid * P.yr).astype("float32"); P["Dtr"] = (P.logDist * P.yr).astype("float32"); names += ["Ltr", "Mtr", "Dtr"]
early = ((P.t >= first_post_t) & (P.t <= first_post_t + 1)).astype("int8"); late = (P.t >= first_post_t + 2).astype("int8")
for nm, w in (("Early", early), ("Late", late)):
    P[f"Low{nm}"] = (P.Low * w).astype("int8"); P[f"Mid{nm}"] = (P.Mid * w).astype("int8"); P[f"Dist{nm}"] = (P.logDist * w).astype("float32")
m = pf.fepois("y ~ LowEarly + MidEarly + DistEarly + LowLate + MidLate + DistLate + " + " + ".join(names) + " | key + cym", data=P, vcov={"CRV1": "city_id"})
for k in ("LowEarly", "MidEarly", "DistEarly", "LowLate", "MidLate", "DistLate"): res[f"main city-clustered (direct): {k}"] = tid(m, k)
json.dump(res, open("results_oil_exploratory2b.json", "w"), indent=1); log("done")
for k, v in res.items(): print(k, {a: round(b, 4) for a, b in v.items()})
