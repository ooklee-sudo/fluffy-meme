"""Recompute every job-posting number quoted in Section 5.2 (Table 2a) -> summary.json.

Needs pandas and statsmodels. Cox models: one standardized covariate at a time (10 events),
counting-process entry times, model-based standard errors; '_strat' variants stratify by entry cohort.
"""
import json
import os

import numpy as np
import pandas as pd
from statsmodels.duration.hazard_regression import PHReg

D = os.path.dirname(os.path.abspath(__file__))
u = pd.read_csv(f"{D}/universe.csv")
m = pd.read_csv(f"{D}/ats_map.csv")
p = pd.read_csv(f"{D}/postings.csv.gz")
f = p[p.skipped == 0]
P = {"universe": len(u), "matched_firms": int(m.cik.nunique()), "boards": len(m),
     "ats": m.ats.value_counts().to_dict(), "postings": len(p), "fetched": len(f),
     "usable": int((f.text_len >= 200).sum()),
     "rag_posts": int(p.rag.sum()), "rag_firms": int(p.loc[p.rag, "cik"].nunique()),
     "ft_posts": int(p.ft.sum()), "ft_firms": int(p.loc[p.ft, "cik"].nunique())}

ev = pd.read_csv(f"{D}/events_postings.csv")
ev["exclusion"] = ev.exclusion.fillna("")
rk = ev[ev.status == "at_risk"]
P["ft_first"] = int((ev.status == "ft_first").sum())
P["entered"] = len(rk)
for c in ("R1", "R2", "R3", "R4"):
    P["excl_" + c] = int(rk.exclusion.str.startswith(c).sum())
a = rk[rk.exclusion == ""]
fm = pd.read_csv(f"{D}/firm_month_postings.csv")
P.update(an_firms=len(a), an_events=int(a.event.sum()), an_fm=len(fm),
         cohorts={str(int(k)): int(v) for k, v in a.cohort.value_counts().sort_index().items()},
         event_firms=sorted(a.loc[a.event == 1, "name"]))
P["specs"] = {}
for s in ("narrow", "broad", "none"):
    e = pd.read_csv(f"{D}/events_postings_{s}.csv")
    e["exclusion"] = e.exclusion.fillna("")
    r = e[(e.status == "at_risk") & (e.exclusion == "")]
    P["specs"][s] = {"firms": len(r), "events": int(r.event.sum())}

# Cox models
fm = fm.merge(a[["cik", "cohort"]], on="cik")
fm["S_share"] = fm.S_share.fillna(0)
for c in ("S_share", "ind_sigma", "ind_mu"):
    fm["z_" + c] = (fm[c] - fm[c].mean()) / fm[c].std()
models = {}
for name, cols in [("S", ["z_S_share"]), ("sigma", ["z_ind_sigma"]), ("mu", ["z_ind_mu"]),
                   ("S+sigma", ["z_S_share", "z_ind_sigma"])]:
    for strat in (False, True):
        r = PHReg(fm["stop"], fm[cols], status=fm["event"], entry=fm["start"],
                  strata=fm["cohort"] if strat else None).fit()
        models[name + ("_strat" if strat else "")] = {
            c: {"hr": round(float(np.exp(r.params[i])), 2),
                "lo": round(float(np.exp(r.params[i] - 1.96 * r.bse[i])), 2),
                "hi": round(float(np.exp(r.params[i] + 1.96 * r.bse[i])), 2),
                "p": round(float(r.pvalues[i]), 3)} for i, c in enumerate(cols)}

# Kaplan-Meier share transitioned
d, surv, km = a[["T", "event"]], 1.0, []
for t, g in d.sort_values("T").groupby("T"):
    if g.event.sum():
        surv *= 1 - g.event.sum() / (d["T"] >= t).sum()
        km.append((float(t), surv))
share = lambda mth: 1 - next((s for t, s in reversed(km) if t <= mth), 1.0)  # noqa: E731
models["km"] = {"at6": round(share(6), 3), "at12": round(share(12), 3)}
P["models"] = models
json.dump(P, open(f"{D}/summary.json", "w"), indent=1)
print(json.dumps({k: P[k] for k in ("an_firms", "an_events", "an_fm")}), models["S"], models["sigma"], models["km"])
