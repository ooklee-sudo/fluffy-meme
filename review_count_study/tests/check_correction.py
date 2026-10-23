"""Monte Carlo check of correction.dsl_poisson: bias and 95% CI coverage relative to the oracle
(all rows human-coded) estimate. Run: python tests/check_correction.py [reps]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tempfile

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

import correction, llm_coding, load_data, models

reps = int(sys.argv[1]) if len(sys.argv) > 1 else 100
rhs = ["stars", "np.log(author_reviews)", "specificity", "argument_balance", "emotional_intensity", "narrative"]
df = load_data.make_demo(6000, 11)
tmp = Path(tempfile.mkdtemp())
llm = models.prepare(llm_coding.code_reviews(df, llm_coding.MockCoder(True), tmp / "a.jsonl", log_every=10**9))
tru = models.prepare(llm_coding.code_reviews(df, llm_coding.MockCoder(False), tmp / "b.jsonl", log_every=10**9))
orc = smf.glm("count ~ " + " + ".join(rhs), data=tru, family=sm.families.Poisson(),
              offset=np.log(tru.exposure)).fit().params.drop("Intercept")  # estimand: human-coded regression on this finite population
naive = smf.glm("count ~ " + " + ".join(rhs), data=llm, family=sm.families.Poisson(),
                offset=np.log(llm.exposure)).fit().params.drop("Intercept")
est, cover = [], []
for r in range(reps):
    idx = np.random.default_rng(r).choice(llm.index, 400, replace=False)
    d = correction.dsl_poisson(llm, tru.loc[idx], rhs)
    est.append(d["coef"])
    cover.append((np.log(d["ci_low"]) <= orc) & (orc <= np.log(d["ci_high"])))
est = pd.DataFrame(est)
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 20)
print(pd.DataFrame({"oracle": orc, "naive_LLM_bias": naive - orc, "DSL_mean_bias": est.mean() - orc,
                    "DSL_sd": est.std(), "DSL_cover95": pd.DataFrame(cover).mean()}).round(3))
