"""Write small synthetic input files with the schemas the other scripts expect.

Use only to check that the scripts run; replace ./data with the real files.

weekly_panel.csv   repo, week, release, age, regular_release, regular_age, issues, bugs
releases.csv       repo, published_at (UTC ISO), tag, is_hotfix, body
launches.csv       launch_id, date, type, keywords (regular expression, case-insensitive)
exposure.csv       repo, open_weights, openai, anthropic, google   (0/1)
adoption_weekly.csv repo, week, downloads, stars_new
"""
import os
import numpy as np
import pandas as pd

rng = np.random.default_rng(1)
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_synthetic")
os.makedirs(D, exist_ok=True)
repos = [f"repo{i:02d}" for i in range(19)]
start, end = pd.Timestamp("2023-01-02"), pd.Timestamp("2026-09-28")
days = pd.date_range(start, end + pd.Timedelta(days=6), freq="D")
types = ["open_weights", "openai", "anthropic", "google"]

launches = pd.DataFrame({
    "launch_id": [f"L{i:02d}" for i in range(38)],
    "date": np.sort(rng.choice(days[200:-60], 38, replace=False)),
    "type": rng.choice(types, 38, p=[.58, .16, .16, .10]),
})
launches["keywords"] = [f"model{i:02d}|m{i:02d}" for i in range(38)]
launches.to_csv(f"{D}/launches.csv", index=False)

expo = pd.DataFrame({"repo": repos})
for t, k in zip(types, [11, 6, 6, 5]):
    expo[t] = 0
    expo.loc[rng.choice(19, k, replace=False), t] = 1
expo.to_csv(f"{D}/exposure.csv", index=False)

rel_rows, panel_rows, adopt_rows = [], [], []
for r_i, r in enumerate(repos):
    p = rng.uniform(0.06, 0.35)          # daily release probability
    rel_days = days[rng.random(len(days)) < p / 4]
    for d in rel_days:
        txt = "Fixes and improvements."
        for _, L in launches.iterrows():
            if expo.loc[r_i, L.type] and 0 <= (d - L.date).days <= 30 and rng.random() < .3:
                txt += f" Add support for {L.keywords.split('|')[0]}."
        rel_rows.append((r, d + pd.Timedelta(hours=int(rng.integers(0, 24))), f"v{len(rel_rows)}",
                         int(rng.random() < .4), txt))
    weeks = pd.date_range(start, end, freq="W-MON")
    rel_week = pd.Series(1, index=pd.DatetimeIndex(rel_days).to_period("W-SUN").start_time).groupby(level=0).sum()
    age = reg_age = 1
    dl = 1e5 * rng.uniform(.2, 5)
    for w in weeks:
        rel = int(w in rel_week.index)
        reg = int(rel and rng.random() < .6)
        iss = rng.poisson(40); bug = rng.binomial(iss, .35)
        panel_rows.append((r, w.date(), rel, min(age, 52), reg, min(reg_age, 52), iss, bug))
        age = 1 if rel else age + 1
        reg_age = 1 if reg else reg_age + 1
        dl *= np.exp(0.01 + 0.02 * rel + rng.normal(0, .08))
        adopt_rows.append((r, w.date(), int(dl), rng.poisson(60)))

pd.DataFrame(rel_rows, columns=["repo", "published_at", "tag", "is_hotfix", "body"]).to_csv(f"{D}/releases.csv", index=False)
pd.DataFrame(panel_rows, columns=["repo", "week", "release", "age", "regular_release", "regular_age",
                                  "issues", "bugs"]).to_csv(f"{D}/weekly_panel.csv", index=False)
pd.DataFrame(adopt_rows, columns=["repo", "week", "downloads", "stars_new"]).to_csv(f"{D}/adoption_weekly.csv", index=False)
print("synthetic data in", D)
