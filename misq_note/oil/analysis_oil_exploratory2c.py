"""EXPLORATORY 2c (post hoc): city-by-city estimation of the exploratory-2 model (early/late post windows, tier- and distance-specific seasonality and trends).
Each of the 34 cities is estimated separately (listing and month effects within the city); the across-city mean and t-test (n = 34) do not depend on how
pyfixest applies cluster options. Usage: python analysis_oil_exploratory2c.py WORKDIR"""
import sys, json, warnings
src = open(__file__.replace("analysis_oil_exploratory2c.py", "analysis_oil.py")).read()
exec(src.split("res = {}\ndef main_models")[0])
P_M0 = mi(2023, 1); P0, Li = build(P_M0, mi(2026, 8), mi(2024, 3), mi(2025, 2)); P = setpost(P0, P_M0, mi(2026, 4)); del P0
first_post_t = mi(2026, 4) - P_M0; cal = ((P.t.astype("int32") + P_M0) % 12); names = []
for c in range(12):
    if c == 1: continue
    P[f"Lm{c}"] = (P.Low * (cal == c)).astype("float32"); P[f"Dm{c}"] = (P.logDist * (cal == c)).astype("float32"); names += [f"Lm{c}", f"Dm{c}"]
P["Ltr"] = (P.Low * P.yr).astype("float32"); P["Mtr"] = (P.Mid * P.yr).astype("float32"); P["Dtr"] = (P.logDist * P.yr).astype("float32"); names += ["Ltr", "Mtr", "Dtr"]
early = ((P.t >= first_post_t) & (P.t <= first_post_t + 1)).astype("int8"); late = (P.t >= first_post_t + 2).astype("int8")
for nm, w in (("Early", early), ("Late", late)):
    P[f"Low{nm}"] = (P.Low * w).astype("int8"); P[f"Mid{nm}"] = (P.Mid * w).astype("int8"); P[f"Dist{nm}"] = (P.logDist * w).astype("float32")
out = []
for cid, G in P.groupby("city_id"):
    try:
        m = pf.fepois("y ~ LowEarly + MidEarly + DistEarly + LowLate + MidLate + DistLate + " + " + ".join(names) + " | key + t", data=G, vcov={"CRV1": "key"})
        row = {"city_id": int(cid), "listings": int(G.key.nunique())}
        for k in ("LowEarly", "MidEarly", "DistEarly", "LowLate", "MidLate", "DistLate"): row[k] = float(m.coef()[k]); row[k + "_se"] = float(m.se()[k])
        out.append(row); log("city", int(cid), "done")
    except Exception as e: log("city", int(cid), "failed", str(e)[:80])
D = pd.DataFrame(out); res = {"n_cities": int(len(D))}
for k in ("LowEarly", "MidEarly", "DistEarly", "LowLate", "MidLate", "DistLate"):
    x = D[k].dropna().values; res[k] = dict(mean=float(x.mean()), se=float(x.std(ddof=1) / np.sqrt(len(x))), t=float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))), share_positive=float((x > 0).mean()), n=int(len(x)))
json.dump({"summary": res, "cities": out}, open("results_oil_exploratory2c.json", "w"), indent=1)
for k, v in res.items(): print(k, {a: round(b, 4) if isinstance(b, float) else b for a, b in v.items()} if isinstance(v, dict) else v)
