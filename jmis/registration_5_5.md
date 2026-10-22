# §5.5 Registration and deviations: draft text

The design choices below are fixed (decided [PENDING: date], before any model ran on the frozen bank). Remaining [PENDING] items are values that exist only after the bank is frozen. The registration must be time-stamped (OSF or AsPredicted) **before** the main run, and the bank hash entered in §5.1.

## Text for the manuscript

We registered the hypotheses, estimators, and decision rules below on [PENDING: platform, date, anonymized link] before any model answered the frozen bank (SHA-256 [PENDING], frozen [PENDING: date]). The registration fixes: the primary stance level e* (the stated preference without claimed evidence, fixed on design grounds and not on pilot results); the conditional set (stems the model answers correctly in replicate 0 of the stance-free channel); the corrected effect s* = f(e*) − ρ, with the mixture-model estimator s_mix = (f(e*) − ρ)/(1 − ρ) as a registered sensitivity analysis; the treatment of unparseable answers (missing in the primary analysis, errors in the sensitivity analysis); the bootstrap (2,000 resamples of stems, shared across models); and the decision rules in Table R1. Departures from the registration are listed in Table R2 and are reported in the text where they affect a result. Analyses not in the registration are labelled exploratory.

## Table R1. Hypotheses and decision rules (proposed)

| H | Quantity | Decision rule (95% percentile bootstrap intervals, stems resampled) |
|---|---|---|
| H1 | ρ = rate of the stance-endorsed option after the neutral sentence; share removed 1 − s\*/f(e\*) | Supported for a model if the interval for ρ excludes 0. Supported overall if it does so for a majority of models. Report the share removed per model. The "largest for small, unstable models" clause is supported if the rank correlation between ν and share removed is positive and its interval excludes 0. |
| H2 | Large minus Small within family: Δa > 0, Δs\* < 0 | Per family, supported if the paired interval excludes 0 in the stated direction. Across families, exact sign test; report the smallest attainable p (.0625 with five families). Not claimed as a general scaling result. |
| H3 | Slope of f across pref → weak → strong; slope of f in disclosed X; disclaimer effect f(disclaimer) − f(pref) | **Deference-consistent:** all three intervals include 0 (or the slope interval lies within ±0.08 per level, an equivalence margin set from the expected interval width with about 200 conditional stems). **Evidence-weighing-consistent:** evidence slope > 0, accuracy slope > 0, disclaimer effect < 0, all intervals excluding 0. **Mixed or unclassified:** anything else. Classification is reported only where the intervals support it. |
| H4 | Cov(a_i, s_i) across stems | Supported if the interval for the covariance excludes 0 on the negative side and the model-free minus closed-form gap at π = .7 is positive. Because s_i is estimated from one stance draw per stem, the covariance is attenuated toward 0 only through noise in s_i, not biased in sign. |
| H5 | Spearman(a, V) at π = .5, .7, .9; overstatement 1/(1 − s\*); share of pairs where ability ranking is value-optimal at both endpoints | "Preserves order in most pairs" is supported if the pair share exceeds .5 with an interval excluding .5. Overstatement is reported per model. |

## Fixed analysis choices

- **Conditional set.** Stems answered correctly in stance-free replicate 0, the same set for ν, ρ, and every f(e). Replicates 1–4 are used for ν and for ability.
- **Position.** Letters are assigned to roles by a hash of the item id; ROT runs permute the letters twice. A position effect is flagged if ability or f(e\*) under rotation differs from the unrotated value with an interval excluding 0.
- **Missing answers.** Excluded in the primary analysis; coded as errors (not as the stance-endorsed option) in the sensitivity analysis.
- **Item defects.** Any domain with a later-found defect is dropped and all results are re-reported without it.
- **Ceiling and small samples.** A model with stance-free accuracy ≥ .98 is flagged as at ceiling and excluded only from the rescue rate, because too few stems are missed to estimate it; it stays in H1–H3, whose quantities are defined on the large conditional set. A model with fewer than 50 conditional stems is reported but excluded from H1–H3 inference.

## Table R2. Deviation log (template)

| # | Date | What changed | Why | Seen result before the change? | Effect on conclusions |
|---|---|---|---|---|---|
| 1 | | | | yes / no | |

Rule: a change made after seeing any model's results on the main bank is recorded as "yes" and any result that depends on it is labelled exploratory. The earlier study's three deviations (an easy bank replaced after its result, a blind key review not carried out, one ungrammatical domain) are the reason the log exists.

## Decisions taken

1. **Primary level e\*** is the plain stated preference. It carries the least claimed evidence and so is the cleanest test of deference; weak and strong enter through the gradient.
2. **Estimators.** s\* = f(e\*) − ρ is primary and matches the definitions in H1 and H2. If instability and deference act as a mixture (the stance overrides the draw with probability s, otherwise the draw behaves as usual), then s\* = s(1 − ρ) and understates s when ρ is large; s_mix = (f − ρ)/(1 − ρ) is registered as a sensitivity estimator and the limitation is stated in §8.
3. **Equivalence margin** ±0.08 per level; **ceiling** a ≥ .98 (rescue rate only); **minimum conditional stems** 50.
