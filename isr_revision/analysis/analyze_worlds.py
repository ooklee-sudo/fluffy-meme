"""World-level and election-level analysis (replaces the marginal permutation tests).

usage: python analysis/analyze_worlds.py DATA_DIR
Needs worlds.csv and elections.csv (see README.md for columns).
"""
import sys, warnings
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

warnings.filterwarnings("ignore")
D = sys.argv[1]
W = pd.read_csv(f"{D}/worlds.csv"); E = pd.read_csv(f"{D}/elections.csv")
W["nocand_share"] = W.n_nocand / W.n_elections
W["contested_share"] = W.n_contested / W.n_elections
RHS = "C(authority)*C(rent) + C(authority):C(population) + C(rent):C(population) + C(rule) + C(population)"

# outcome -> (family, confirmatory hypothesis term)
SPEC = {
    "nocand_share":    ("binom", "C(rent)"),
    "contested_share": ("binom", "C(rent)"),
    "gini":            ("ols",   "C(authority)"),
    "reelect":         ("ols",   "C(rule)"),
    "transfers":       ("pois",  "C(authority)"),
}

def fit(y, fam):
    if fam == "ols":
        return smf.ols(f"{y} ~ {RHS}", W).fit(cov_type="HC3")
    if fam == "binom":                       # quasi-binomial on counts of elections
        yy = np.c_[W[y] * W.n_elections, W.n_elections * (1 - W[y])]
        X = smf.ols(f"{y} ~ {RHS}", W).fit().model.exog
        names = smf.ols(f"{y} ~ {RHS}", W).fit().model.exog_names
        m = sm.GLM(yy, pd.DataFrame(X, columns=names), family=sm.families.Binomial())
        return m.fit(scale="X2", cov_type="HC1")
    return smf.glm(f"{y} ~ {RHS}", W, family=sm.families.Poisson()).fit(scale="X2", cov_type="HC1")

rows = []
for y, (fam, term) in SPEC.items():
    r = fit(y, fam)
    wt = r.wald_test_terms(scalar=True).summary_frame()
    for t in wt.index:
        if t == "Intercept": continue
        rows.append(dict(outcome=y, term=t, p=float(wt.loc[t, "P>chi2"]),
                         confirmatory=t.startswith(term) and ":" not in t))
T = pd.DataFrame(rows)
# Holm within the pre-specified family, BH across everything else
c = T.confirmatory
T.loc[c, "p_adj"] = multipletests(T.loc[c, "p"], method="holm")[1]
T.loc[~c, "p_adj"] = multipletests(T.loc[~c, "p"], method="fdr_bh")[1]
print("== World-level Wald tests (robust SE; p_adj: Holm for confirmatory, BH otherwise) ==")
print(T.round(4).to_string(index=False))

# interaction of interest, bootstrap by resampling worlds within cells
def did(df):
    m = df.groupby(["authority", "rent"]).gini.mean()
    return (m["binding", 2] - m["advisory", 2]) - (m["binding", 0] - m["advisory", 0])
rng = np.random.default_rng(1)
cells = ["authority", "rent", "population", "rule"]
bs = [did(W.groupby(cells).sample(frac=1, replace=True, random_state=int(rng.integers(1e9))))
      for _ in range(1000)]
print(f"\nGini authority x rent difference-in-differences: {did(W):+.4f}  "
      f"95% bootstrap CI [{np.percentile(bs,2.5):+.4f}, {np.percentile(bs,97.5):+.4f}]")

# --- election level: who stands (GEE, clustered on world), who wins given candidates
E["claude"] = (E.family == "claude").astype(int)
E = E.merge(W[["world_id", "rent", "population"]], on="world_id")
g = smf.gee("stood ~ claude + C(rent) + held_before + energy_rank_before", "world_id", E,
            family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
print("\n== Candidacy (GEE logit, cluster = world) ==")
print(g.summary().tables[1])

from statsmodels.discrete.conditional_models import ConditionalLogit
S = E[E.stood == 1].copy()
S["grp"] = S.world_id * 1000 + S.election_id
keep = S.groupby("grp").filter(lambda x: len(x) > 1 and 0 < x.won.sum() < len(x))
def cl(df, col):
    return ConditionalLogit(df.won, df[[col, "held_before"]], groups=df.grp).fit(disp=0).params[col]
b = cl(keep, "claude")
by_world = {w: d for w, d in keep.groupby("world_id")}
worlds_ids = np.array(list(by_world)); boot = []
for _ in range(200):
    pick = rng.choice(worlds_ids, len(worlds_ids))
    bd = pd.concat([by_world[w].assign(grp=by_world[w].grp + k * 10**7) for k, w in enumerate(pick)])
    try: boot.append(cl(bd, "claude"))
    except Exception: pass
print(f"\n== Winning | standing (conditional logit within election, world-cluster bootstrap) ==\n"
      f"claude coef {b:+.3f}  95% CI [{np.percentile(boot,2.5):+.3f}, {np.percentile(boot,97.5):+.3f}]  "
      f"(n elections {keep.grp.nunique()})")
