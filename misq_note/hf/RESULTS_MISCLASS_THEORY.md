# Results: labels as garbled messages; mixture prediction and corrected estimator (plan: ANALYSIS_PLAN_MISCLASS_THEORY.md; code: analysis_misclass.py; numbers: results_misclass.json)

95 event posts (three-hour filter, valid window) and 96 validation posts (the rest of the 191). Q = P(true human class | label class) estimated on the 96 validation posts with add-0.5 smoothing; human class means from the 95 events.

## T1 Mixture prediction (directional mean 30-minute return, percent; observed in the events versus predicted from Q and the human class means; CI of observed minus predicted by day/post bootstrap, 2,000 resamples)
| Label set | Escalation observed / predicted (CI of difference) | De-escalation observed / predicted (CI of difference) |
|---|---|---|
| Model 1 | 0.17 / 0.20 (−0.33, 0.26) | 0.90 / 0.57 (−0.86, 0.01 in raw units) |
| v2 majority | 0.32 / 0.12 (−0.06, 0.46) | 0.95 / 0.69 (−0.70, −0.00) |
| v2 opus | 0.32 / 0.12 (−0.05, 0.47) | 0.95 / 0.64 (−0.77, −0.02) |
| v2 sonnet | 0.24 / 0.18 (−0.16, 0.28) | 1.04 / 0.67 (−0.87, −0.04) |
| v2 haiku | 0.35 / 0.12 (−0.01, 0.50) | 1.04 / 0.69 (−0.88, −0.02) |
| v2 sonnet repeat | 0.22 / 0.16 (−0.26, 0.35) | 0.99 / 0.64 (−0.93, 0.01) |
Escalation: the mixture representation (assumption A) is not rejected for any label set; observed estimates are as large as or larger than predicted. De-escalation: the observed estimate is larger than the mixture predicts in all sets, and the CI excludes zero for four of six; the models' false de-escalation labels (human mixed or other) carry returns like true de-escalation, so label errors are not independent of the return given the human class (non-classical error): the human classes mixed and other contain de-escalation content.

## T2 Corrected estimator (mu_hat = Q^{-1} m)
Condition numbers of Q 4.3 (model 1) to 37.7 (sonnet). Corrected directional escalation estimates: model 1 −0.22, v2 majority 0.59, opus 0.58, sonnet −3.47, haiku 0.62, sonnet repeat 0.46 (human benchmark 0.48); bootstrap CIs span ±14 or wider. Corrected de-escalation estimates: 1.6 to 3.1 (benchmark 1.05; overshoot). Absolute error of the corrected versus the uncorrected escalation estimate: better in three sets (v2 majority, opus, sonnet repeat), equal in one (haiku), worse in two (model 1, sonnet). By the rule in the plan, the correction does not reliably recover the human estimate with these data (95 events, 96 validation posts); with Q estimated on all 191 posts the corrected de-escalation estimates are 1.5 to 1.9 and the escalation estimates −0.94 to 0.67.

## T3 Decomposition of the escalation-labelled mean (model 1: 0.52 of labelled escalation events are human escalation)
Contributions to the 0.19 directional mean: true escalation +0.25, de-escalation −0.04, mixed +0.05, other −0.07. The attenuation is mostly the dilution (precision about one half) of the true-class mean by classes with near-zero mean, not sign reversal. v2 majority: 0.44 true share; +0.21, −0.05, +0.05, −0.09.

## Exploratory (not in the plan): informativeness of each label partition about the return
R² of the 30-minute return on the four label-class dummies (95 events): investigator-adjudicated human labels 0.161 (adjusted 0.133; leave-one-out 0.090); v3 human labels 0.134 (0.106; 0.068); model 1 0.117 (0.088; 0.039); v2 majority 0.135 (0.106; 0.052); v2 sonnet 0.136; v2 haiku 0.143; sonnet repeat 0.111. Human labels explain somewhat more return variance than model labels, but the differences are small and the independent-adjudication human labels are about as informative as the clearer-codebook model labels.
