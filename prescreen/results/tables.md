## Table 2 (main): five models of the pre-registered studies, truth = EB

| Model | Implied ρ [95% CI] | Best headline discarded by filter | Loss: test all | Loss: twin filter | Loss: twin prior | Traffic saved by prior [95% CI] |
|---|---|---|---|---|---|---|
| Claude Haiku 5.5 | 0.13 [0.07, 0.20] | 41.0% | 4.1% | 8.8% | 4.0% | 1.3% [-1.2, 3.6] |
| Gemini 3.7 Flash | 0.18 [0.12, 0.25] | 41.0% | 4.0% | 8.8% | 4.0% | 0.9% [-2.2, 3.6] |
| Llama 4 Maverick | 0.14 [0.08, 0.20] | 44.8% | 4.0% | 9.9% | 4.0% | 0.4% [-2.4, 2.7] |
| GPT-5.6 luna | 0.13 [0.07, 0.19] | 42.8% | 4.0% | 9.1% | 4.0% | 0.5% [-2.4, 2.5] |
| Grok 4.3 | 0.20 [0.14, 0.26] | 39.8% | 4.0% | 8.3% | 3.9% | 2.8% [0.0, 5.4] |
| Ensemble (five models) | 0.20 [0.14, 0.27] | 40.0% | 4.0% | 8.8% | 4.0% | 1.6% [-1.1, 4.6] |

## Supplement: newer models, truth = EB

| Model | Implied ρ [95% CI] | Best headline discarded by filter | Loss: test all | Loss: twin filter | Loss: twin prior | Traffic saved by prior [95% CI] |
|---|---|---|---|---|---|---|
| GPT-6 luna | 0.17 [0.11, 0.23] | 42.0% | 4.0% | 9.1% | 4.0% | 2.0% [-0.4, 4.2] |
| DeepSeek V4.1 Flash | 0.23 [0.17, 0.28] | 38.4% | 4.0% | 8.1% | 3.9% | 3.0% [-0.3, 5.8] |
| Ensemble (four current models) | 0.21 [0.15, 0.27] | 39.8% | 4.0% | 8.7% | 4.0% | 1.6% [-1.6, 4.6] |

## Robustness: definition of the true CTR (ensemble of the five original models)

| Truth | Implied ρ [95% CI] | Discarded | Loss: test all | Loss: filter | Filter minus test all [95% CI] | Prior minus test all [95% CI] | Traffic saved by prior [95% CI] |
|---|---|---|---|---|---|---|---|
| Empirical Bayes, all impressions (main) | 0.20 [0.14, 0.27] | 40.0% | 4.0% | 8.8% | +4.8 [3.7, 5.8] | -0.05 [-0.14, +0.03] | 1.6% [-1.1, 4.6] |
| Raw CTR, all impressions | 0.20 [0.14, 0.26] | 40.4% | 3.3% | 10.0% | +6.7 [5.4, 8.0] | +0.02 [-0.06, +0.10] | -1.1% [-4.9, 1.9] |
| Split sample: truth from half B, calibration on half A | 0.15 [0.08, 0.21] | 44.2% | 4.3% | 9.2% | +4.9 [3.8, 6.0] | +0.01 [-0.09, +0.11] | -0.5% [-4.9, 3.1] |

Losses are expected CTR shortfalls relative to the best headline at 16,000 impressions per test. Intervals: bootstrap over tests (1,000 resamples). Differences are in percentage points.
