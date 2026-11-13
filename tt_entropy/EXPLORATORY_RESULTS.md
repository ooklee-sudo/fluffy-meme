# Exploratory follow-up of H1' (not preregistered), 2026-11-13

Data: `results/phase1_value` (H1' sample, 30 brands) and `results/phase1_confirm` (H1 sample, 30 brands);
`results/phase1` (10 brands, single seed) where noted. Scripts: `mechanism.py`, `decision.py`.

## 1. Where the signal sits: everywhere, with no stable location

Partial Spearman rho with relative gain, given the four traits:

| Signal | H1' sample | H1 sample |
| --- | --- | --- |
| All bonds (H1' predictor) | +0.62 | +0.53 |
| q_proj only / v_proj only | +0.58 / +0.58 | +0.44 / +0.59 |
| Early / middle / late layers | +0.40 / +0.43 / +0.69 | +0.44 / +0.37 / +0.37 |
| Bond 1 / 2 / 3 | +0.63 / +0.60 / +0.60 | +0.47 / +0.50 / +0.57 |

The per-layer pattern does not replicate across samples (Spearman of per-layer rho = -0.12). The signal is
a global property of the gradient, not of particular layers or bonds. In the 10-brand exploratory sample the
relation is absent or reversed in every group.

## 2. The tensor-network (MPO) structure adds little beyond an ordinary SVD

| Partial rho with relative gain | H1' sample | H1 sample | Pooled (n = 60, sample indicator added) |
| --- | --- | --- | --- |
| MPO bond entropy, 4 traits | +0.62 | +0.53 | +0.53 |
| Ordinary SVD entropy, 4 traits | +0.52 | +0.49 | +0.51 |
| MPO, 4 traits + SVD | +0.42 (p = 0.035) | +0.23 (p = 0.27) | +0.19 (p = 0.17) |
| SVD, 4 traits + MPO | -0.17 | +0.06 | +0.10 |

MPO and SVD entropy correlate at 0.95 and 0.88 across brands. Most of the effect is the spread of the
gradient's ordinary singular-value spectrum; any extra contribution of the MPO cut is small and
inconsistent.

## 3. Decision value: entropy does not help choose which tenants to personalize

Rules were built on one sample and scored on the other. Share of total relative gain captured by
personalizing 10 of 30 brands (built on H1, scored on H1' | built on H1', scored on H1):

| Rule | Share | Cost to capture 50% (adapter = 1, probe = 0.25) |
| --- | --- | --- |
| Oracle (true gains) | 44.4% / 45.3% | 12 / 12 |
| Type-token ratio alone (low first) | 43.7% / 44.8% | 12 / 12 |
| Four-trait model | 43.7% / 44.6% | 12 / 12 |
| Four traits + entropy | 43.7% / 44.6% | 19.5 / 19.5 |
| Entropy alone | 41.8% / 43.8% | 20.5 / 19.5 |
| Random | 33.3% | 15 |

Response diversity alone already comes within about one point of the oracle, so there is almost no room
left for entropy, and the probe makes entropy rules cost more. The same holds for best gain as the
outcome. The partial correlation of H1' is real in these data, but it explains variation that does not
change which brands rank near the top.

## What this means

- H1' (preregistered) stands as a statistical finding, but it has no practical decision value here and
  is mostly an ordinary spectral measure, not a tensor-network one.
- Simple traits do the practical work: response diversity picks whom to personalize, response length
  tracks how much capacity they need (H1 samples).
- Caveats: one dataset, one model, 30 brands per sample, and gains spread fairly evenly across brands
  (the oracle beats random by only about 11 points at 10 of 30), which limits what any rule can add.
