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

The `1/(1+k)` pattern is exact (see General elasticity). So offsetting is **partial** outside the baseline;
the headline claim should be "substantial offsetting", not "full".

- Corner case: no verification when `(1-phi) l lam s theta < c`; `E[R] = lam s`, so quality then matters fully.
- Vendor stage: price, quality cost `k(q)`, liability regimes, competition.
- Empirical: calibrate `lam(q)` by model and `theta` from test curves; test whether residual defect density is flat in tool quality.
- Literature check: Peltzman-type offsetting, optimal software release timing, AI tool liability. Verify novelty before positioning.

## General elasticity (derived; checked in `elasticity_check.py`)
Let `h = -S'/S` be the hazard of detection and `m = lam S` the residual density. The FOC `C'(e) = A lam S h` gives
`m = C'(e) / (A h(e))`. Differentiating the FOC in `ln lam`, with `a := C''/C' - h'/h`:

    eps := d ln R / d ln lam = a / (a + h),   second-order condition: a + h > 0.

- Baseline (`C''=0`, `h'=0`): `a = 0`, `eps = 0` (full offsetting).
- Convex cost `c e^g`, exponential detection: `eps = (g-1) / ((g-1) + theta e*)`.
- Linear cost, `S = (1 + theta e / k)^-k` (gamma-mixed exponential detection): `a = h/k`, so
  **`eps = 1/(1+k)` exactly**, independent of `e` and `lam`. Small `k` = detectability is heterogeneous
  (easy defects go first, hard ones linger), so offsetting is weaker.
- Increasing hazard (`h' > 0`, e.g. Weibull `beta > 1`): `a < 0`, `eps < 0`. Better tools can *raise*
  residual defects (over-offsetting). Numerically `eps ~ -0.06 ... -0.12` for beta in {1.5, 2}.
- The sign of `eps` is the sign of `a`: marginal-cost convexity and a falling hazard push toward partial
  offsetting, a rising hazard toward over-offsetting.

## Information asymmetry (simulation-checked; proofs not done)
### Developer learns `lam` while verifying (`asymmetry_check.py`)
`lam ~ Gamma(alpha, beta0)`. Discoveries `D` by effort `e` are `Poisson(lam s (1-S))`, residual is independent
given `lam`, so the posterior is `Gamma(alpha + D, beta0 + s(1-S))` and
`E[R | D] = s S (alpha + D) / (beta0 + s(1-S))`. Rule: stop when this first equals `r* = c/(A theta)`.

Simulation (n = 40,000; alpha=2, beta0=1, A=35, theta=0.8, c=1):
1. Among thresholds {0.25..4} x r*, cost is lowest at 1.0 x r* (6.082 vs 6.131 at 0.75x, 6.203 at 1.5x). Consistent with
   the myopic rule being optimal here; optimality in general is not proven.
2. Unconditional `E[R_tau] = 0.0338` vs `r* = 0.0357` (about 2 standard errors short; not resolved).
3. **Offsetting is incomplete once beliefs matter.** Conditional on true `lam` quartiles, `E[R_tau | lam]` rises
   0.017 -> 0.029 -> 0.038 -> 0.052, while stopping time rises only 4.4 -> 5.4. Shrinkage toward the prior makes
   developers under-verify bad tools and over-verify good ones.
4. Value of learning vs a static effort chosen from the prior mean is small (6.230 -> 6.082, about 2.4% of cost).
   Static-effort cost is `(c/theta)[ln(A lam_hat theta / c) + lam/lam_hat]`.

### Vendor quality signal and adverse selection (analytical sketch, NOT numerically verified)
- With effort set from the pooled mean `lam_bar`, willingness to pay for the pool is `(c/theta) ln(lam0 / lam_bar)`
  (depends on the mean, not `E ln lam`).
- Vendor type `lam` has quality cost `k(lam)`, decreasing in `lam`. Participation: `k(lam) <= p`. Fixed point
  `p = (c/theta) ln(lam0 / E[lam | k(lam) <= p])`. The best (low `lam`) types exit first, `lam_bar` rises, `p` falls:
  Akerlof-type unraveling. Conditions for partial vs full unraveling are open.
- Warranty signal: vendor bearing share `phi_v` pays `phi_v l E[R | lam]`. Under full learning the offsetting makes
  this independent of `lam` (single crossing fails, warranty cannot separate). Under incomplete learning, item 3 shows
  `E[R | lam]` is increasing in `lam`, so single crossing holds, but the slope is flatter than with no learning.
  Separation therefore depends on how fast developers learn: a testable implication.
- The warranty also lowers the developer's own share `(1 - phi - phi_v)` and so raises `R` (Proposition 4): the signal
  has a moral-hazard cost.

## Open items
- Prove optimality of the myopic stopping rule (monotone-case condition) and the exact value of `E[R_tau]`.
- Corner case: no verification when `(1-phi) l lam s theta < c`; `E[R] = lam s`, so quality then matters fully.
- Formalise the lemons fixed point and the warranty separating equilibrium; check the second-order conditions.
- Vendor stage: price, quality cost `k(q)`, liability regimes, competition.
- Empirical: calibrate `lam(q)` by model and `theta` from test curves; estimate the cross-sectional slope of
  residual density on tool quality (the elasticity `eps`) and the shape of the detection hazard.
- Literature check: Peltzman-type offsetting, optimal software release timing, AI tool liability. Verify novelty.

## Literature check (2026-10-24; web-search snippets only, none of these were read in full)
| Area | Source | Overlap with this model |
|---|---|---|
| Optimal release | Okumoto & Goel (1979/1980), many extensions (imperfect repair, testing effort, discount rate) | **Proposition 1 is the classical optimal-release condition re-read**: optimum where failure intensity equals a constant cost ratio, so residual intensity does not depend on `a`. Not new mathematically. |
| Verification economics of AI | Catalini, "Some Simple Economics of AGI" (arXiv 2602.20946) | Verification as the bottleneck; moral-hazard limit where verification effort vanishes under weak liability; verification as a public good. Closest conceptual neighbour. |
| Verification capacity | arXiv 2609.38459; 2609.04681 (agentic SDLC cost economics); 2609.26172 (insuring the fallback) | Verification effort / oversight under automation; cost economics of AI code. Need reading. |
| Security economics | Anderson & Moore; Varian (free-riding, liability) | Liability assignment, moral hazard, lemons for unmeasurable security. Standard background. |
| Peltzman effect | ISACA, blogs; formal use in a cyber-insurance model (arXiv 1804.00998) | Mostly commentary for AI/security; empirical support for risk compensation is contested. |
| Warranty signalling | Grossman (1981), Dulleck-Kerschbamer-Sutter (2011) (cited, not checked) | Warranty/credence-goods framework for the vendor stage. |
| Empirical SE | DORA "verification tax"; AI-assisted code quality studies | Motivation and calibration data, not formal models. |

### What this implies
- Offsetting itself (Prop. 1) is not a new result; the contribution has to be elsewhere.
- Candidate contributions: (i) hazard-rate characterisation of offsetting, `eps = a/(a+h)`, with `1/(1+k)` and over-offsetting;
  (ii) incomplete offsetting from Bayesian shrinkage; (iii) warranty separation depending on learning speed;
  (iv) calibration of `lam`, `theta`, hazard shape from LLM-generated-code data.
- No source found modelling AI code generation as a vendor warranty + developer verification game. Absence not proven.
