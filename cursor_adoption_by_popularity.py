"""Does AI-tool adoption (Cursor config files) vary with repository popularity, a crude stakes proxy?

Data: matching.csv from the He et al. (MSR 2026) replication package (Zenodo 10.5281/zenodo.18368662).
Treated = repos that adopted Cursor in the matching month; controls = candidate pool sample for the same month.
The ratio treated:control within a bin is proportional to the adoption rate IF controls are a uniform sample of the
pool; the package does not document the sampling, so this is only a relative-intensity picture.

Usage: python3 -I cursor_adoption_by_popularity.py <path to CursorStudy/data>
"""
import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import chi2

m = pd.read_csv(f"{sys.argv[1]}/matching.csv", usecols=["group", "age_days", "n_stars", "total_events"])
m["y"] = (m.group == "treatment").astype(int)
m["ls"] = np.log10(m.n_stars + 1)
labels = ["0-2 stars", "3-9", "10-30", "31-99", "100-315", "316-999", "1000-3162", "3163+"]
m["bin"] = pd.cut(m.ls, bins=[-0.01, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 6.0], labels=labels)
t = m.groupby("bin", observed=True).agg(n=("y", "size"), treated=("y", "sum"))
t["control"] = t.n - t.treated
base = m.y.sum() / (1 - m.y).sum()
t["rel"] = (t.treated / t.control) / base
t["lo"] = [0 if k == 0 else chi2.ppf(0.025, 2 * k) / 2 for k in t.treated] / t.control / base
t["hi"] = [chi2.ppf(0.975, 2 * (k + 1)) / 2 for k in t.treated] / t.control / base
print("relative adoption intensity by stars (1.0 = overall treated:control ratio)")
print(t[["n", "treated", "control", "rel", "lo", "hi"]].round(2).to_string())

X = sm.add_constant(pd.DataFrame({"ls": m.ls, "ls2": m.ls ** 2, "lage": np.log10(m.age_days + 1),
                                  "lev": np.log10(m.total_events + 1)}))
r = sm.Logit(m.y, X).fit(disp=0)
print("\nlogit: treated ~ log10 stars + (log10 stars)^2 + log10 age + log10 events")
print(r.summary2().tables[1][["Coef.", "Std.Err.", "P>|z|"]].round(4).to_string())
print("quadratic coefficient", "negative (hump)" if r.params["ls2"] < 0 else "positive (U shape, no interior peak)")
