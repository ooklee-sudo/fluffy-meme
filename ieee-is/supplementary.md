---
title: "Supplementary Material — Filter or Prior? What LLM Synthetic Agents Are Worth in Experimentation Pipelines"
author: "Ook Lee, Hanyang University"
---

## S1. Newer models

The main text reports the five models used in the pre-registered studies. Two newer low-cost models were scored on the same 500 Upworthy tests with the same prompt and three draws per test. The true CTR is the empirical-Bayes estimate (main analysis).

| Model | Implied ρ [95% CI] | Best headline discarded by filter | Loss: test all | Loss: twin filter | Loss: twin prior | Traffic saved by prior [95% CI] |
|----------------------|----------------|------------|---------|---------|---------|-----------------|
| GPT-6 luna | 0.17 [0.11, 0.23] | 42.0% | 4.0% | 9.1% | 4.0% | 2.0% [-0.4, 4.2] |
| DeepSeek V4.1 Flash | 0.23 [0.17, 0.28] | 38.4% | 4.0% | 8.1% | 3.9% | 3.0% [-0.3, 5.8] |
| Ensemble (four current models) | 0.21 [0.15, 0.27] | 39.8% | 4.0% | 8.7% | 4.0% | 1.6% [-1.6, 4.6] |



## S2. Robustness to the definition of the true CTR

Ensemble of the five models from the pre-registered studies. *Empirical Bayes* is the main analysis. *Raw CTR* uses each headline's observed CTR on all impressions without shrinkage, which overstates the true spread of effects. *Split sample* divides each headline's impressions at random into two halves (hypergeometric draw). Half B defines the true CTR (empirical-Bayes estimate), and half A calibrates the prior, so the noise in the calibration and in the truth is independent.

| Truth | Implied ρ [95% CI] | Discarded | Loss: test all | Loss: filter | Filter minus test all [95% CI] | Prior minus test all [95% CI] | Traffic saved by prior [95% CI] |
|----------------------|---------------|---------|--------|--------|--------------|--------------|--------------|
| Empirical Bayes (main) | 0.20 [0.14, 0.27] | 40.0% | 4.0% | 8.8% | +4.8 [3.7, 5.8] | -0.05 [-0.14, +0.03] | 1.6% [-1.1, 4.6] |
| Raw CTR | 0.20 [0.14, 0.26] | 40.4% | 3.3% | 10.0% | +6.7 [5.4, 8.0] | +0.02 [-0.06, +0.10] | -1.1% [-4.9, 1.9] |
| Split sample | 0.15 [0.08, 0.21] | 44.2% | 4.3% | 9.2% | +4.9 [3.8, 6.0] | +0.01 [-0.09, +0.11] | -0.5% [-4.9, 3.1] |

Losses are expected CTR shortfalls relative to the best headline at 16,000 impressions per test. Differences are in percentage points. All intervals are 95% bootstrap intervals over tests (1,000 resamples).

## S3. Simulation details

- **Sample:** 500 tests drawn at random (seed 2026) from the Upworthy confirmatory release, each with three to eight distinct headlines and at least 1,000 impressions per headline. Images are pooled within a headline.
- **Twin scores:** each model estimated, for every headline of a test in one call, the probability (0–100) that a typical U.S. social media user would click. Order was shuffled per call, the temperature was 0.7, and reasoning effort was low. Scores were averaged over three draws and standardized within test.
- **Policies:** (A) test all headlines with equal traffic; (B) test only the top half by twin score; (C) test a random half; (D) ship the top twin headline without a test; (E) test all headlines and select by the posterior mean under a normal prior on the logit scale whose mean is b·z, with b and the prior variance estimated on the other half of the tests (two-fold cross-fitting).
- **Budgets:** 2,000 to 64,000 impressions per test, with 400 simulated A/B tests per test, budget, and policy.
- **Implied ρ:** sin(π·(P − ½)), where P is the share of headline pairs ordered correctly by the twin.
- **Code and outputs:** [repository URL].
