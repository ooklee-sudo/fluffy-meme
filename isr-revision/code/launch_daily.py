"""Daily-resolution re-analysis of release timing around upstream model launches (RQ3).

Why: with a weekly release probability of about 0.42 in treated blocks, a weekly indicator
saturates, and a same-day SDK release is indistinguishable from one six days later.
This script measures timing in days and benchmarks it against placebo launch dates.

Inputs (in --data): releases.csv, launches.csv, exposure.csv (schemas in make_synthetic.py)

Outputs (in --out):
  launch_daily_results.csv     statistics, placebo p-values
  launch_pairs.csv             one row per repository x launch (treated and control)
  fig4_launch_daily.png/.pdf   cumulative release probability gap vs. placebo band

Design
  Day 0 is the announcement date (UTC). For each launch, treated repositories are exposed
  to its type; controls are repositories not exposed to that type (optionally also not
  exposed to another launch within the window: --clean). A repository enters a launch
  only if it released at least once in the 90 days before day 0 (it is active).
  Statistics, averaged over launches with equal weight:
    gap_k     P(treated releases within days 0..k) - P(control releases within days 0..k)
    rmst_gap  difference in restricted mean days to first release, truncated at --horizon
  Inference: randomization inference that replaces every launch date with a placebo date
  drawn from days at least --buffer days away from any real launch, keeping the launch's
  type, so treated and control sets and baseline release rates are re-formed at the
  placebo date. Two-sided p = share of placebo statistics at least as far from the placebo
  mean as the observed statistic (the placebo mean absorbs any baseline difference in
  release rates between exposed and unexposed repositories).
  Content vs timing (treated pairs): days to first release vs. days to first release whose
  notes mention the model (keyword match), and the share of first mentions that occur in the
  very first release after the launch.
"""
import argparse
import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="data")
ap.add_argument("--out", default="output")
ap.add_argument("--horizon", type=int, default=28)
ap.add_argument("--buffer", type=int, default=14)
ap.add_argument("--R", type=int, default=999)
ap.add_argument("--clean", action="store_true")
ap.add_argument("--hotfix", choices=["all", "regular"], default="all")
ap.add_argument("--seed", type=int, default=20261013)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
rng = np.random.default_rng(a.seed)
KS = [0, 1, 3, 7, 14, 28]

R = pd.read_csv(os.path.join(a.data, "releases.csv"))
L = pd.read_csv(os.path.join(a.data, "launches.csv"))
X = pd.read_csv(os.path.join(a.data, "exposure.csv")).set_index("repo")
if a.hotfix == "regular":
    R = R[R.is_hotfix == 0]
R["day"] = pd.to_datetime(R.published_at, utc=True).dt.tz_localize(None).dt.normalize()
L["day"] = pd.to_datetime(L.date).dt.normalize()
origin = min(R.day.min(), L.day.min())
R["d"] = (R.day - origin).dt.days
L["d"] = (L.day - origin).dt.days
repos = sorted(set(X.index) & set(R.repo))
rel = {r: np.sort(R.loc[R.repo == r, "d"].unique()) for r in repos}
first_d = {r: v[0] for r, v in rel.items()}
last_d = {r: v[-1] for r, v in rel.items()}
H = a.horizon


def days_to_next(r, d0):
    v = rel[r]
    i = np.searchsorted(v, d0)
    return v[i] - d0 if i < len(v) else np.inf


def active(r, d0):
    v = rel[r]
    i = np.searchsorted(v, d0)
    return i > 0 and d0 - v[i - 1] <= 90 and last_d[r] >= d0 + H


def groups(ltype, d0, own_id=None):
    tr, co = [], []
    for r in repos:
        if not active(r, d0):
            continue
        if X.loc[r, ltype] == 1:
            tr.append(r)
        else:
            if a.clean:
                other = L[(L.launch_id != own_id) & (abs(L.d - d0) <= H)]
                if any(X.loc[r, t] == 1 for t in other.type):
                    continue
            co.append(r)
    return tr, co


def launch_stats(ltype, d0, own_id=None):
    tr, co = groups(ltype, d0, own_id)
    if not tr or not co:
        return None
    t = np.array([days_to_next(r, d0) for r in tr])
    c = np.array([days_to_next(r, d0) for r in co])
    out = {f"gap_{k}": (t <= k).mean() - (c <= k).mean() for k in KS}
    out["rmst_gap"] = np.minimum(t, H).mean() - np.minimum(c, H).mean()
    out["curve"] = np.array([(t <= k).mean() - (c <= k).mean() for k in range(H + 1)])
    return out, tr, co, t, c


def aggregate(stats):
    keys = [k for k in stats[0] if k != "curve"]
    agg = {k: float(np.mean([s[k] for s in stats])) for k in keys}
    agg["curve"] = np.mean([s["curve"] for s in stats], axis=0)
    return agg


# ------------------------------------------------------------- observed
obs, pairs = [], []
for _, l in L.iterrows():
    res = launch_stats(l.type, l.d, l.launch_id)
    if res is None:
        continue
    s, tr, co, t, c = res
    obs.append(s)
    pat = re.compile(str(l.keywords), re.I) if isinstance(l.keywords, str) and l.keywords.strip() else None
    for r, dt in zip(tr + co, list(t) + list(c)):
        row = dict(launch_id=l.launch_id, type=l.type, repo=r, treated=int(r in tr),
                   days_to_release=dt)
        if r in tr and pat is not None:
            sub = R[(R.repo == r) & (R.d >= l.d) & (R.d <= l.d + 56)].sort_values("d")
            hit = sub[sub.body.fillna("").str.contains(pat)]
            row["days_to_mention"] = (hit.d.iloc[0] - l.d) if len(hit) else np.inf
            row["mention_in_first_release"] = int(len(sub) > 0 and len(hit) > 0 and hit.index[0] == sub.index[0])
        pairs.append(row)
O = aggregate(obs)
pairs = pd.DataFrame(pairs)

# ------------------------------------------------------------- placebo dates
lo, hi = int(max(min(first_d.values()) + 90, L.d.min() - 365)), int(min(max(last_d.values()) - H, L.d.max() + 365))
cand = np.arange(lo, hi)
mask = np.ones(len(cand), bool)
for d in L.d:
    mask &= np.abs(cand - d) > a.buffer
cand = cand[mask]
placebo = []
for b in range(a.R):
    st = []
    for _, l in L.iterrows():
        res = launch_stats(l.type, int(rng.choice(cand)))
        if res is not None:
            st.append(res[0])
    if st:
        placebo.append(aggregate(st))

rows = []
for k in [f"gap_{k}" for k in KS] + ["rmst_gap"]:
    dist = np.array([p[k] for p in placebo])
    rows.append(dict(statistic=k, observed=O[k], placebo_mean=dist.mean(),
                     placebo_2_5=np.quantile(dist, .025), placebo_97_5=np.quantile(dist, .975),
                     p_two_sided=(np.sum(np.abs(dist - dist.mean()) >= abs(O[k] - dist.mean())) + 1) / (len(dist) + 1)))
res = pd.DataFrame(rows)

tp = pairs[pairs.treated == 1]
content = {
    "treated_pairs": len(tp),
    "median_days_first_release": float(np.median(np.minimum(tp.days_to_release, 999))),
    "share_with_mention_56d": float(np.isfinite(tp.days_to_mention).mean()) if "days_to_mention" in tp else np.nan,
    "median_days_first_mention_given_mention": float(np.median(tp.days_to_mention[np.isfinite(tp.days_to_mention)]))
        if "days_to_mention" in tp and np.isfinite(tp.days_to_mention).any() else np.nan,
    "share_first_mention_in_first_release": float(tp.loc[np.isfinite(tp.days_to_mention), "mention_in_first_release"].mean())
        if "days_to_mention" in tp and np.isfinite(tp.days_to_mention).any() else np.nan,
}
res = pd.concat([res, pd.DataFrame([dict(statistic=k, observed=v) for k, v in content.items()])])
res.to_csv(f"{a.out}/launch_daily_results.csv", index=False)
pairs.to_csv(f"{a.out}/launch_pairs.csv", index=False)

# ------------------------------------------------------------- figure
curves = np.array([p["curve"] for p in placebo])
plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 150})
fig, ax = plt.subplots(figsize=(5.6, 2.8))
k = np.arange(H + 1)
ax.fill_between(k, np.quantile(curves, .025, axis=0), np.quantile(curves, .975, axis=0),
                color="0.88", label="95% placebo band")
ax.plot(k, curves.mean(axis=0), color="0.55", lw=1, ls="--", label="Placebo mean")
ax.plot(k, O["curve"], color="black", lw=1.6, label="Observed launches")
ax.axhline(0, color="0.3", lw=0.6)
ax.set_xlabel("Days since launch (day 0 = announcement)")
ax.set_ylabel("Treated minus control:\nshare released by day k")
ax.legend(frameon=False, fontsize=7)
fig.tight_layout()
fig.savefig(f"{a.out}/fig4_launch_daily.png"); fig.savefig(f"{a.out}/fig4_launch_daily.pdf")
print(res.to_string(index=False))
