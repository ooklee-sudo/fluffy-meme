# detectability: can an exposure-based design see assimilation?

Calculator, derivation (`DERIVATION.md`) and simulation checks for the detectability bound of "Acquired, Not Yet Assimilated?".
Given an adoption share A, an effect beta per assimilating employer, the reliability R of the exposure measure and the standard error of the
exposure coefficient, it returns the implied coefficient gamma* = A beta sigma_s sqrt(R), the minimum detectable effect (2.8 SE), whether complete
assimilation is detectable, the adoption share needed, and (with a logistic adoption path) the earliest detection year.

    python -m detectability --A 0.3618 --beta -0.5 --se 0.0178 --k 5.33 --slope 0.75     # one design
    python audit.py examples/own_estimates.csv results/own_estimates_audit.csv            # many estimates (CSV columns in audit.py)
    python -m pytest -q tests                                                              # 24 tests, incl. Tables 5-6 of the manuscript
    python simulate.py 3000 results/simulation_results.json                                # Monte Carlo checks (about 1.5 minutes)

```python
from detectability import detectability, required_adoption, earliest_year, classify
detectability(A=0.3618, beta=-0.5, se=0.0178, k=5.33)         # sigma_s = 1/k;   or sigma_s=...
```

## Simulation results (3,000 replications per scenario, J = 96 occupations, 6 cells each)
Scenarios: sigma_s in {0.10, 0.19}, R in {1, 0.7, 0.5}, (A, beta) in {(0.096, -0.19), (0.362, -0.5), (0.70, -0.5)}, plus an employer-level (binomial) variant.
* **gamma\* formula.** Mean estimate / gamma\* = 0.99 (range 0.97 to 1.01) in scenarios with |gamma\*| > 0.01; the binomial variant gives 1.00. For |gamma\*| below 0.01 the ratio is dominated by Monte Carlo noise.
* **Standard error.** Empirical SD / analytic SE = 1.03 on average (0.99 to 1.15; the largest values occur with large effects and skewed exposure).
* **Power at the MDE.** When |gamma\*| equals 2.8 SE the rejection rate is 0.73 to 0.80 (mean 0.77), below the nominal 0.80 because the clustered SE is itself estimated with error and exposure is skewed. Statements that gamma\* is *below* the MDE are therefore conservative by about 3 to 7 percentage points of power.
* **Size.** Under the null the nominal 5 percent cluster-robust t test rejects 7.0 percent of the time with 96 clusters: use randomization inference or a wild bootstrap, as the manuscript does for its p-values.

## Application to the manuscript's data (`results/application_sigma_s.json`, `results/own_estimates_audit.csv`)
With k = 5.33 the largest implied 2024 coefficient is -0.034 against an MDE of 0.050. If the exposure scores are read as actual shares of work (mean 0.032, SD 0.039, maximum 0.239), gamma\* is about five times smaller and
no adoption share up to 100 percent reaches the MDE for any beta in the manuscript's range. The conclusion that these designs cannot detect complete assimilation is therefore robust to the scale assumption.

## Status and limits
Derivation and simulation validate the bound under the stated assumptions (see `DERIVATION.md`); they do not show that real labor markets satisfy them.
An audit of published exposure studies (their standard errors, acquisition rates and effect sizes) is not done: `audit.py` and the CSV template are ready, but
the inputs have to be taken from the papers themselves. No published study is included in `examples/`.

## Audit of published studies
`PUBLISHED_AUDIT.md`, `examples/published_estimates.csv`, `audit_published.py` and `results/published_audit.csv` apply the bound to six published exposure and adoption studies, with the source (table, figure or text, page) of every number. The audit is small and non-systematic.
