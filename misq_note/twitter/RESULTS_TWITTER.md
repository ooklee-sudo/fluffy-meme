# Twitter-era (2017–2021) oil/Iran/energy sample: confirmatory test (plan: ANALYSIS_PLAN_TWITTER.md with Amendment 1; code: build_frame.py, analysis_twitter.py; output: results_twitter.json)

Frame 341 tweets; 278 pass the three-hour filter; 191 have valid tick windows (market open at t−30, t, t+30 minutes; 87 are excluded, mostly weekend or overnight tweets; by year 18, 49, 68, 56). Labels are from two independent model instances (κ = 0.77); human labels for this sample have been requested and are not yet available, so every directional result is conditional on model labels. Mean |z| = 0.84 (median 0.49).

## Pre-registered propositions (label-free; OLS with year fixed effects, standard errors clustered by day; one-sided; Holm across HI1–HI3)
| Hypothesis | Coefficient (SE) | One-sided p | Holm-adjusted | Decision |
|---|---|---|---|---|
| HI1: novelty N_c > 0 | −0.27 (0.74) | 0.64 | 1.00 | **Not supported** (wrong sign) |
| HI2: prior uncertainty U > 0 | +0.18 (0.18) | 0.15 | 0.45 | **Not supported** |
| HI3: N_c × U > 0 | −0.37 (1.81) | 0.58 | 1.00 | **Not supported** |
Robustness (not decision-bearing under the plan): TF-IDF novelty N_t is positive, +1.14 (SE 0.44), one-sided p = 0.005. The two novelty measures disagree: the compression-based measure (the primary) shows no relation to |z|; the lexical measure does. We cannot treat the N_t result as confirmation because the plan designated N_c as the test and N_t as a robustness check, and the two were registered together.
Power: the standard error of the N_c coefficient is 0.74 in |z| units, so effects below about 1.5 cannot be excluded.

## H10: directional response (agreed model labels; directional return in %, one-sided Wilcoxon)
| Class | n | mean 30 min | median | p (> 0) | mean pre-30 | post − pre | p (post > pre) |
|---|---|---|---|---|---|---|---|
| ESC (oil up) | 32 | +0.51 | +0.09 | 0.001 | +0.04 | +0.50 | 0.010 |
| DEESC (oil down) | 11 | +0.18 | +0.06 | 0.22 | +0.06 | +0.13 | 0.28 |
Single-model labels (model 1): ESC n = 47, +0.35%, p = 0.003, post − pre +0.36, p = 0.011; DEESC n = 13, +0.11%, p = 0.31.
**Decision:** H10 is supported for escalation tweets (oil rose after tweets the models agree are escalation, and the excess over the preceding 30 minutes is significant) and not for de-escalation tweets (n = 11, too few to conclude). This is the opposite asymmetry to the 2026 closure, where de-escalation moved oil and the (model-labelled) escalation class did not. It matches the pre-war Truth Social samples (RESULTS_EXT.md: escalation +0.46%, p = 0.013 for Russia/Venezuela-type posts). Pre-30-minute drift is near zero here, unlike in the 2026 sample.

## H9: era contrast (exploratory)
Mean |z| of the 191 tweets 0.84 (median 0.49) against 1.39 (median 0.81) for the 95 Truth Social war-period keyword posts with tick windows (two-sided permutation p = 0.002). The standardized reaction is larger in 2026; the comparison is confounded by the war state and cannot isolate the platform.

## Reading
1. The pre-registered information-theoretic propositions about novelty and prior uncertainty are not supported in an independent sample (all three, Holm-adjusted p ≥ 0.45). Together with the Truth Social hold-out result this is the second sample in which they do not clear the threshold.
2. The sign of the directional response depends on the state: in 2017–2020, when Hormuz was open, oil responded to escalation tweets and not to de-escalation tweets; in 2026, with the strait closed, de-escalation moved oil. This is a pattern an information-theoretic account can accommodate (a message is informative when it moves the prior of the state in which the market has little mass), but we did not pre-register a directional prediction of the sign flip, so it is a post hoc reading.
3. Limits: model labels only; 191 events; 87 events (31% of the kept tweets) lack a tick window; the novelty measures disagree; a WTI CFD proxy.
