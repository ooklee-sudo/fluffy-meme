# Pre-registration: an economic model of labels as garbled messages, and a misclassification-corrected estimator (2026-10-14/15, before computed)

Motivation: simulated review round 4 and the author's aim of a theoretical contribution. Already seen: all label-set comparisons (RESULTS_V2RELABEL.md, RESULTS_V4B.md, RESULTS_THIRD_CODER.md): human and model class means, confusion matrices, Table 3b decomposition. Not seen: any misclassification-corrected estimate.

## Model (informal statement, to be written in the paper)
A message has a true class S in {ESC, DEESC, MIXED, OTHER}; the market's price response is a function of the class, mu_k = E[r | S = k] (r = 30-minute return). The econometrician observes only a label L from a classifier, which is a garbling of S (Blackwell): P(L | S) = confusion matrix. Under conditional independence of the label error and the return given S (assumption A),
E[r | L = c] = sum_k q_ck mu_k, where q_ck = P(S = k | L = c) is the positive predictive value matrix, which depends on the base rates of the classes, not on the sensitivity alone.
Implications: (i) a class mean estimated with labels is a mixture of true-class means with weights given by precision; (ii) over-labelling (high recall, low precision) biases the estimate toward the other classes' means and can reverse its sign if opposite-signed classes are mislabelled into it; under-labelling changes only the sample size; (iii) estimates depend on prevalence, as do kappa; (iv) if label errors depend on the return given S (non-classical error, e.g. a labeller who remembers the outcome), the mixture representation fails.

## Tests (all on the 95 events of RESULTS_V2RELABEL.md: three-hour filter, valid 30-minute window)
T1 Mixture prediction. For each label set (model 1, v2 majority and the four v2 runs), estimate Q = P(S | L) with human final labels as S on the posts NOT in the event set (96 posts; cross-fit), compute the predicted mean raw return by label class from Q and the human-class mean raw returns observed in the event set, and compare with the observed mean raw return by label class in the event set. Report predicted, observed and the difference with day-clustered/post bootstrap 95% CI (2,000 resamples; events resampled by day, validation posts resampled by post). Assumption A is "not rejected" for a label set if the 95% CI of the difference includes zero for ESC and DEESC.
T2 Corrected estimator. For each label set, estimate mu_hat = Q^{-1} m, where m is the vector of mean raw returns by label class in the event set (classes ESC, DEESC, MIXED, OTHER; classes with fewer than 3 events in the event set are given the grand mean and flagged). Compare mu_hat_ESC and mu_hat_DEESC with the human-label class means (+0.48 and −1.05 directional) and with the uncorrected model-label means; report the absolute error of the corrected versus the uncorrected estimate and bootstrap CIs. Also report the same with Q estimated on all 191 posts (in-sample).
T3 Sign-reversal condition. Report for each label set the weighted contribution of each true class to the escalation-labelled mean (the Table 3b decomposition in formula form) and whether the contribution of opposite-signed classes exceeds that of the true class.

## Interpretation rules
- If T1 shows no detectable difference for ESC and DEESC across label sets, the paper states that the attenuation is consistent with misclassification of true classes into the label classes (assumption A not rejected, with low power).
- If T2's corrected estimates are closer to the human benchmark than the uncorrected ones for ESC in most label sets, the paper reports the corrected estimator as recovering the human estimate; if not, it reports that the correction does not help with these data.
- Human final labels (investigator-adjudicated) are the benchmark; results with v3 final labels (third coder) are reported as a robustness check.

## Not allowed after the results are seen
Changing the event set, the validation set, the classes in Q, or the benchmark.
