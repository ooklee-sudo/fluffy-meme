# Verification effort under LLM coding tools: model note (draft)

Status: working draft. Derivations are by hand and checked numerically in `model_check.py`.
Novelty against prior literature has NOT been verified.

## Setup
- Code of size `s`, tool quality `q`. Introduced defects `N ~ Poisson(lam(q) s)`, `lam' < 0`.
- Developer verification effort `e` finds each defect independently with prob `1 - S(e)`.
- Poisson thinning: residual defects `R ~ Poisson(lam s S(e))`. This is the micro-foundation for the count model.
- Costs: verification `C(e)`, loss `l` per residual defect. Developer bears `(1-phi) l`, users bear `phi l`.

## Baseline: `S(e) = exp(-theta e)`, `C(e) = c e`
Developer problem: `min_e  c e + (1-phi) l lam s exp(-theta e)`.

- Interior optimum (needs `(1-phi) l lam s theta > c`): `e* = (1/theta) ln[(1-phi) l lam s theta / c]`.
- `E[R] = c / ((1-phi) l theta)`.

### Propositions
1. **Offsetting.** `E[R]` does not depend on `lam`. Better tools lower verification effort one for one and leave residual defects unchanged. Savings: `(c/theta) ln(lam0/lam1)`.
2. **Externality wedge.** Private `E[R]` is `1/(1-phi)` times the social optimum (`phi = 0`), independent of `lam`.
3. **Value of quality is log-concave.** Willingness to pay for a quality gain is the verification saving, so the vendor's incentive tracks cost savings, not defect reduction.
4. **Liability allocation.** `E[R]` responds only to the share of loss borne by whoever chooses `e`. Vendor liability lowers `E[R]` only if the contract is tied to verification effort.

## Robustness (numerical, `model_check.py`)
Elasticity `d ln E[R] / d ln lam` (0 = full offset, 1 = none), phi = 0.3:

| specification | elasticity |
|---|---|
| baseline | 0.000 |
| convex cost `c e^1.5` | 0.12 - 0.17 |
| convex cost `c e^2` | 0.26 - 0.35 |
| heavy-tail detection `S=(1+theta e/k)^-k`, k=2 | 0.333 |
| heavy-tail detection, k=1 | 0.500 |
| convex 1.5 + heavy-tail k=2 | 0.46 - 0.49 |

Observation (not proven): with linear cost and heavy-tail detection the elasticity looks like `1/(1+k)`.
So offsetting is **partial** outside the baseline; the headline claim should be "substantial offsetting", not "full".

## Open items
- Prove the `1/(1+k)` pattern and characterise the general elasticity.
- Corner case: no verification when `(1-phi) l lam s theta < c`; `E[R] = lam s`, so quality then matters fully.
- Information asymmetry: developer does not know `lam`; gamma-Poisson prior (overdispersion = heterogeneity of `lam`); vendor quality signal; adverse selection.
- Vendor stage: price, quality cost `k(q)`, liability regimes, competition.
- Empirical: calibrate `lam(q)` by model and `theta` from test curves; test whether residual defect density is flat in tool quality.
- Literature check: Peltzman-type offsetting, optimal software release timing, AI tool liability. Verify novelty before positioning.
