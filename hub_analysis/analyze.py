"""Migration of adapter authors after successive base-model generations (Hugging Face Hub snapshot)."""
import datetime as dt
import json
import math
import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
cache = json.load(open(os.path.join(HERE, "hub_cache.json")))
FAM = json.load(open(os.path.join(HERE, "families.json")))["FAM"]
P = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
CUTOFF = dt.datetime(2026, 9, 29, tzinfo=dt.timezone.utc)

rows, events = [], []
for fam, gens in FAM.items():
    G = []
    for repos in gens:
        rs = [b for b in repos if cache.get(b, {}).get("created")]
        if not rs:
            G.append(None)
            continue
        T = min(P(cache[b]["created"]) for b in rs)
        ads = [(a, P(c), dl, lk, i) for b in rs for a, c, dl, lk, i in cache[b]["adapters"]]
        G.append((T, ads))
    for k in range(len(G) - 1):
        if not G[k] or not G[k + 1]:
            continue
        (T0, a0), (T1, a1) = G[k], G[k + 1]
        later = [x for j in range(k + 1, len(G)) if G[j] for x in G[j][1]]
        interval = (T1 - T0).days
        if interval <= 0 or not a0:
            continue
        eid = f"{fam}:{k}->{k+1}"
        old = {}
        for a, c, dl, lk, i in a0:
            if T1 - dt.timedelta(days=365) <= c < T1:
                d = old.setdefault(a, {"n": 0, "maxdl": 0, "likes": 0})
                d["n"] += 1
                d["maxdl"] = max(d["maxdl"], dl)
                d["likes"] += lk
        if not old:
            continue
        for W in (90, 180, 365):
            if T1 + dt.timedelta(days=W) > CUTOFF:
                pass
        new_by_author = {}
        for a, c, dl, lk, i in a1:
            new_by_author.setdefault(a, []).append(c)
        later_by_author = {}
        for a, c, dl, lk, i in later:
            later_by_author.setdefault(a, []).append(c)
        for a, d in old.items():
            r = {"event": eid, "family": fam, "interval": interval, "author": a, "n_old": d["n"], "maxdl": d["maxdl"], "likes": d["likes"]}
            for W in (90, 180, 365):
                lim = T1 + dt.timedelta(days=W)
                r[f"m{W}"] = int(any(T1 <= c <= lim for c in new_by_author.get(a, [])))
                r[f"any{W}"] = int(any(T1 <= c <= lim for c in later_by_author.get(a, [])))
            rows.append(r)
        events.append((eid, fam, interval, len(old)))

df = pd.DataFrame(rows)
print(f"author-events: {len(df):,} | events: {df.event.nunique()} | families: {df.family.nunique()} | authors: {df.author.nunique():,}")
df["persist"] = ((df.n_old >= 3) | (df.maxdl >= 50)).astype(int)
df["multi"] = (df.n_old >= 3).astype(int)
print("\nPopulation sizes: all=%d, >=3 adapters=%d, persistent (>=3 adapters or >=50 downloads)=%d" % (len(df), df.multi.sum(), df.persist.sum()))

print("\nMigration to the next generation, by population and window:")
for name, sel in (("all", df), ("multi (>=3 adapters)", df[df.multi == 1]), ("persistent", df[df.persist == 1])):
    print(f"  {name:<24} n={len(sel):>6}  " + "  ".join(f"{W}d: {sel[f'm{W}'].mean():.3f} (any later {sel[f'any{W}'].mean():.3f})" for W in (90, 180, 365)))

# event table for the persistent population
ev = (df[df.persist == 1].groupby("event").agg(family=("family", "first"), interval=("interval", "first"), n=("author", "count"), m180=("m180", "mean"), m365=("m365", "mean")).reset_index())
ev = ev[ev.n >= 20].sort_values(["family", "interval"])
print("\nEvents with >=20 persistent authors:")
print(ev.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
if len(ev) >= 5:
    for col in ("m180", "m365"):
        rho, p = spearmanr(ev.interval, ev[col])
        print(f"  Spearman(interval of old generation, {col}): n={len(ev)} rho={rho:.2f} p={p:.2f}")

# author-level logit with event fixed effects: does migration rise with investment / value?
def logit(sub, y, cols, label):
    X = pd.get_dummies(sub.event, drop_first=True, dtype=float)
    for c in cols:
        X[c] = sub[c]
    X = sm.add_constant(X)
    m = sm.Logit(sub[y], X).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": pd.factorize(sub.author)[0]})
    out = [f"{c}: OR={math.exp(m.params[c]):.2f} (p={m.pvalues[c]:.3f})" for c in cols]
    print(f"  {label:<40} n={len(sub):>6} " + " | ".join(out))

df["ln_n"] = np.log1p(df.n_old)
df["ln_dl"] = np.log1p(df.maxdl)
df["ln_likes"] = np.log1p(df.likes)
print("\nAuthor-level logit, event fixed effects, SE clustered by author (odds ratios per one-unit log increase):")
for y in ("m180", "m365"):
    logit(df, y, ["ln_n", "ln_dl"], f"all authors, {y}")
    logit(df[df.multi == 1], y, ["ln_n", "ln_dl"], f">=3 adapters, {y}")

# cadence at author level with family FE, SE clustered by event
df["ln_int"] = np.log(df.interval)
print("\nCadence test (author-level logit, family fixed effects, SE clustered by event):")
for y in ("m180", "m365"):
    for name, sub in (("all", df), ("persistent", df[df.persist == 1])):
        X = pd.get_dummies(sub.family, drop_first=True, dtype=float)
        X["ln_n"] = sub.ln_n
        X["ln_int"] = sub.ln_int
        X = sm.add_constant(X)
        m = sm.Logit(sub[y], X).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": pd.factorize(sub.event)[0]})
        print(f"  {name:<11} {y}: ln(interval) OR={math.exp(m.params['ln_int']):.2f}, p={m.pvalues['ln_int']:.3f}  (events={sub.event.nunique()}, n={len(sub)})")
df.to_csv(os.path.join(HERE, "author_events.csv"), index=False)
