"""Robustness checks for the Hub migration analysis (run after analyze.py, which writes author_events.csv).

Linear probability models with event or family fixed effects, cluster-robust errors, leave-one-event-out for the
release-cadence coefficient, and a release-date control.
"""
import datetime as dt
import json
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, "author_events.csv"))
cache = json.load(open(os.path.join(HERE, "hub_cache.json")))
FAM = json.load(open(os.path.join(HERE, "families.json")))["FAM"]
P = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00"))

df["ln_n"] = np.log1p(df.n_old)
df["ln_dl"] = np.log1p(df.maxdl)
df["ln_int"] = np.log(df.interval)

# release date of the new generation, in years since 2023-01-01
tnew = {}
for fam, gens in FAM.items():
    ts = []
    for g in gens:
        cs = [P(cache[b]["created"]) for b in g if cache.get(b, {}).get("created")]
        ts.append(min(cs) if cs else None)
    for k in range(len(ts) - 1):
        if ts[k + 1] is not None:
            tnew[f"{fam}:{k}->{k+1}"] = ts[k + 1]
df["t_new"] = df.event.map(lambda e: (tnew[e] - dt.datetime(2023, 1, 1, tzinfo=dt.timezone.utc)).days / 365.25)

print(f"events: {df.event.nunique()}, author-events: {len(df):,}")
ev = df.groupby("event").agg(interval=("interval", "first"), n=("author", "count"), m180=("m180", "mean")).sort_values("interval")
print("\nEvent-level migration rates (all authors, 180 days):")
print(ev.to_string(float_format=lambda x: f"{x:.3f}"))


def lpm(sub, y, cols, fe, cl):
    X = pd.get_dummies(sub[fe], drop_first=True, dtype=float)
    for c in cols:
        X[c] = sub[c].astype(float)
    X = sm.add_constant(X)
    return sm.OLS(sub[y].astype(float), X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(sub[cl])[0]})


print("\nLinear probability model, event fixed effects, errors clustered by author (percentage points per 1 log-unit):")
for y in ("m180", "m365"):
    for name, sub in (("all authors", df), (">=3 adapters", df[df.n_old >= 3])):
        m = lpm(sub, y, ["ln_n", "ln_dl"], "event", "author")
        print(f"  {name:<13}{y}: ln(1+adapters)={100*m.params['ln_n']:+.2f} (p={m.pvalues['ln_n']:.3f}) | "
              f"ln(1+max downloads)={100*m.params['ln_dl']:+.2f} (p={m.pvalues['ln_dl']:.3f})")


def cadence(sub, y="m180", extra=()):
    m = lpm(sub, y, ["ln_n", "ln_int", *extra], "family", "event")
    return 100 * m.params["ln_int"], m.pvalues["ln_int"]


print("\nRelease cadence (ln of the old generation's lifetime in days): LPM, family fixed effects, errors clustered by event")
for y in ("m180", "m365"):
    b0, p0 = cadence(df, y)
    b1, p1 = cadence(df, y, ["t_new"])
    print(f"  {y}: {b0:+.2f} pp (p={p0:.3f}); with release-date control {b1:+.2f} pp (p={p1:.3f})")
b, p = cadence(df[df.n_old >= 3], "m180", ["t_new"])
print(f"  >=3 adapters, m180, release-date control: {b:+.2f} pp (p={p:.3f})")
loo = []
for e in df.event.unique():
    try:
        b, p = cadence(df[df.event != e])
        loo.append((e, b, p))
    except Exception:
        pass
bs = [r[1] for r in loo]
print(f"  leave-one-event-out (m180): range {min(bs):+.2f} to {max(bs):+.2f} pp, p<0.05 in {sum(r[2] < 0.05 for r in loo)} of {len(loo)}")
for e, b, p in loo:
    if e == "Qwen:1->2":
        print(f"  without Qwen:1->2: {b:+.2f} pp (p={p:.3f})")
b, p = cadence(df[(df.event != "Qwen:1->2") & (df.n_old >= 3)])
print(f"  without Qwen:1->2, >=3 adapters: {b:+.2f} pp (p={p:.3f})")
