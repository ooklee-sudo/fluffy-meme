# Draft: Section 5. What Synthetic Pre-Screening Is Worth

*Drop-in replacement for the current Section 5 (validation protocol). Numbers come from `sim_results.json` and `analytic.json`. Run: 500 Upworthy confirmatory tests, 4 models × 3 draws, no-persona prompt from C2, November 2026, API cost 2.37 USD.*

## 5.1 A decision model for pre-screening

A platform has K candidate treatments with true effects θ₁…θ_K and a traffic budget of N impressions. A synthetic agent returns a score s_k for each candidate. Let ρ = corr(s, θ) within a test. The validity map (Table 8) gives ρ an empirical meaning. Direction-valid effects have ρ > 0. Effects whose sign reverses with paradigm familiarity, such as defaults, have ρ < 0. Under a Gaussian approximation, pairwise winner agreement is P = ½ + arcsin(ρ)/π. This maps the excess agreement reported in Study C2 directly into ρ.

We compare three ways to use synthetic evidence:

- **Filter:** test only the m highest-scoring candidates, with N/m impressions each.
- **Prior:** test all K candidates, but combine the observed data with a calibrated prior whose mean is b·s_k.
- **Replace:** pick the top-scoring candidate and run no test.

Filtering trades two forces. More impressions per surviving arm lowers sampling error. But the best arm is discarded with probability 1 − P(best ∈ top m | ρ, K, m). This probability equals 1 − m/K at ρ = 0 and is larger than that when ρ < 0.

**Proposition 1.** (i) When ρ ≤ 0, filtering is weakly dominated by random filtering, and random filtering is dominated by testing all candidates. (ii) When ρ > 0, there is a crossover budget N*(ρ, K, m, τ). Filtering lowers expected regret only when N < N*. N* increases in ρ and in the spread τ of true effects. (iii) A prior calibrated out-of-sample never increases expected regret relative to testing all candidates. Its gain shrinks as N grows.

Simulating the stylized model with the Upworthy parameters (base CTR 1.5%, logit SD of headline effects τ = 0.30, K = 5, m = 2) gives the following crossover budgets:

| ρ | ≤ 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.7 |
|---|---|---|---|---|---|---|
| N* (impressions per test) | never | ≈ 540 | ≈ 1,200 | ≈ 2,100 | ≈ 3,600 | ≈ 9,800 |

Typical Upworthy tests used about 20,000 impressions. At the ρ values implied by our field results, filtering would pay only for tests one to two orders of magnitude smaller than those the platform actually ran.

## 5.2 Field evaluation on Upworthy

**Design.** We use 500 randomly drawn headline tests from the confirmatory archive. Each test has three to eight distinct headlines, and each headline has at least 1,000 impressions. Images are pooled within headline. "True" CTRs are empirical-Bayes estimates on the logit scale. The between-headline SD is 0.30, the sampling SD is 0.20, and the mean shrinkage weight is 0.73. Each model scores all headlines of a test in one call, three times, with the order shuffled. For each budget N from 2,000 to 64,000 impressions, we simulate 400 binomial experiments per test and policy. The prior's slope and variance are cross-fitted across two folds of tests. A random-half policy (C) serves as a placebo for the gain from simply testing fewer arms.

**Table 9. Value of synthetic pre-screening on 500 Upworthy tests (budget 16,000 impressions)**

| Model | Pairwise agreement | Implied ρ | Best headline discarded (twin keeps top half) | CTR loss, test all | CTR loss, twin filter | CTR loss, twin prior | Traffic saved by prior |
|---|---|---|---|---|---|---|---|
| Claude Haiku 5.5 | 0.542 | 0.13 | 41% | 4.06% | 8.81% | 4.02% | 1% |
| DeepSeek V4.1 Flash | 0.572 | 0.23 | 38% | 4.04% | 8.08% | 3.95% | 3% |
| Gemini 3.7 Flash | 0.559 | 0.18 | 41% | 4.07% | 8.81% | 3.99% | 2% |
| GPT-6 luna | 0.555 | 0.17 | 42% | 4.05% | 9.05% | 4.02% | 1% |
| Ensemble (mean z) | 0.566 | 0.21 | 40% | 4.02% | 8.68% | 3.97% | 2% |

*CTR loss is the expected shortfall of the chosen headline's CTR relative to the best headline. A random top-half filter discards the best headline in 50% of tests and has a CTR loss of 11.4% (ensemble row).*

**Results.** Three findings stand out (Figure X).

1. **The signal is real but weak.** Every model discards the best headline less often than chance (38–42% vs. 50%). Every model filter has lower CTR loss than the random filter at every budget. The implied ρ ranges from 0.13 to 0.23. This is at or below the value implied by C2 (0.29). Averaging across models helps only marginally.
2. **Hard filtering never pays at observed budgets.** Even at 2,000 impressions per test, the smallest budget we simulate, testing all headlines beats the twin filter for every model. At 16,000 impressions, filtering doubles the expected CTR loss (8.7% vs. 4.0%). Additional traffic cannot recover a winner that was screened out, so the filter's loss levels off near 7.7%. The loss from testing all headlines keeps falling, to 1.4% at 64,000 impressions.
3. **Soft use is safe but nearly worthless.** The calibrated prior never hurts, but it saves only 1–3% of traffic for the same expected loss. Relying on the twin alone yields a 16.7% loss, which is worse than every policy that uses human traffic.

## 5.3 Decision rules

Combining 5.1–5.2 with the validity map gives rules that state how much each choice is worth:

1. **Estimate ρ for the exact model version and effect type before use.** A short battery of past A/B tests with known outcomes is enough. ρ varies across model versions (Study S) and changes N*.
2. **If ρ ≤ 0.1, or the effect type is not direction-valid (defaults), do not filter.** Filtering is dominated (Proposition 1(i)).
3. **Filter only if the per-test budget is below N*(ρ).** With Upworthy-like effect spreads, that means fewer than about 1,000 impressions at ρ ≈ 0.3. In practice, this situation arises for long-tail or low-traffic surfaces, not for the main experimentation pipeline.
4. **Otherwise use synthetic scores only as a calibrated prior, and budget for a traffic saving of a few percent at most.** Never use them as a replacement for testing.
5. **Document ρ, N*, and the realized discard rate** alongside the model identifier, so that synthetic pre-screening decisions can be audited.

## 5.4 Notes for the limitations section

- The archive dates from 2013–2015 and is public, so models may have memorized some winners. Memorization would inflate ρ, which makes our negative conclusion conservative.
- The "true" CTRs are shrinkage estimates; a split-sample truth (binomial thinning) should be added as a robustness check. The cross-fitted prior avoids using the evaluation data for calibration.
- The test sample (500 random tests with K = 3–8) differs from the 999-test confirmatory package in C2. Results should be re-run on the C2 package, with its registered persona and no-persona arms, before submission.
