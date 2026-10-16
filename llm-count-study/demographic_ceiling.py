"""How well do the Complete Journey demographics themselves predict a household's 4-week basket count?

This is the benchmark for persona-conditioned simulators (Proposition 1): if demographics explain little of the real
variation, no persona-based simulator can correlate strongly with real counts. Out-of-sample, households held out.

  python demographic_ceiling.py          (needs: pip install completejourney_py pyarrow scikit-learn)
"""
import numpy as np, pandas as pd
from scipy import stats
from sklearn.linear_model import PoissonRegressor
from sklearn.model_selection import GroupKFold
import run_pilot as rp

demo, counts = rp.load_journey_households()
feat = ["age", "income", "home_ownership", "marital_status", "household_size", "household_comp", "kids_count"]
X = pd.get_dummies(demo[feat].fillna("missing").astype(str)).astype(float).values
n_h, n_w = counts.shape
Xl = np.repeat(X, n_w, axis=0); y = counts.ravel().astype(float); g = np.repeat(np.arange(n_h), n_w)
pred = np.zeros_like(y)
for tr, te in GroupKFold(5).split(Xl, y, g):
    pred[te] = PoissonRegressor(alpha=1.0, max_iter=500).fit(Xl[tr], y[tr]).predict(Xl[te])
mu = y.mean()
print(f"household-windows {len(y):,}; mean {mu:.2f}, var/mean {y.var(ddof=1)/mu:.2f}, zero {np.mean(y==0):.3f}")
print(f"out-of-sample Spearman(predicted mean from demographics, real count) = {stats.spearmanr(pred, y)[0]:.3f}")
c2 = pred.var() / pred.mean() ** 2
alpha = (y.var(ddof=1) - mu) / mu**2
print(f"alpha (real) = {alpha:.2f}; c^2 = CV^2 of the demographic prediction = {c2:.3f}  "
      f"-> share of real heterogeneity explained by demographics c^2/alpha = {c2/alpha:.2f}")
print(f"Proposition 1: a deterministic simulator that predicted these means perfectly would have alpha* = c^2 - 1/mu = {c2 - 1/mu:.3f} (real {alpha:.2f})")
# ceiling of design C bins for this reference
hist = {int(k): int(v) for k, v in zip(*np.unique(counts.ravel(), return_counts=True))}
sc = rp.get_scenario("grocery", hist); k, w = sc["support"], sc["probs"]
m = (k * w).sum(); tail = w[k >= 21].sum()
vals = np.where(k >= 21, 28.0, k.astype(float)); m2 = (vals * w).sum()
v2 = ((vals - m2) ** 2 * w).sum() + tail * ((35 - 21 + 1) ** 2 - 1) / 12
print(f"design C ceiling for this reference: var/mean {v2/m2:.2f} (real {((k-m)**2*w).sum()/m:.2f})")
