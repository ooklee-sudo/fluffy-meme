"""Capability contrast (DeepSeek V4 Flash vs Pro in the same world): candidacy and winning given standing.

usage: python analysis/capability.py DATA_DIR/h2
"""
import sys, numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from statsmodels.discrete.conditional_models import ConditionalLogit

E = pd.read_csv(f"{sys.argv[1]}/elections.csv")
E["pro"] = (E.capability == "pro").astype(int)
print("== Candidacy (GEE logit, cluster = world) ==")
g = smf.gee("stood ~ pro + held_before + energy_rank_before", "world_id", E, family=sm.families.Binomial(),
            cov_struct=sm.cov_struct.Exchangeable()).fit()
print(g.summary().tables[1])

S = E[E.stood == 1].copy(); S["grp"] = S.world_id * 1000 + S.election_id
keep = S.groupby("grp").filter(lambda x: len(x) > 1 and 0 < x.won.sum() < len(x))
info = keep.groupby("grp").filter(lambda x: x.pro.nunique() == 2)   # elections where both types stood
fit = lambda d: ConditionalLogit(d.won, d[["pro", "held_before"]], groups=d.grp).fit(disp=0).params["pro"]
b = fit(keep); by = {w: d for w, d in keep.groupby("world_id")}; ids = np.array(list(by)); rng = np.random.default_rng(5); boot = []
for _ in range(300):
    pick = rng.choice(ids, len(ids))
    bd = pd.concat([by[w].assign(grp=by[w].grp + k * 10**7) for k, w in enumerate(pick)])
    try: boot.append(fit(bd))
    except Exception: pass
print(f"\n== Winning | standing (conditional logit, world-cluster bootstrap) ==\n"
      f"pro coef {b:+.3f}  95% CI [{np.percentile(boot,2.5):+.3f}, {np.percentile(boot,97.5):+.3f}]  "
      f"(informative contested elections {info.grp.nunique()}; Pro won {int(info[info.pro==1].won.sum())}, expected under a uniform draw {info.groupby("grp").pro.mean().sum():.1f})")
print("stood/won by capability:\n", S.groupby("capability").agg(stood=("stood", "sum"), won=("won", "sum")))
