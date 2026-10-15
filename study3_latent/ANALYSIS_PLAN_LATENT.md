# Plan: correcting LLM-coded outcomes without gold labels (latent-class identification)

Written 2026-10-15, before any additional classifier is run and before any latent-class estimate is computed.
Already seen: the study-3 content results (results_b_content.json: DiD on LLM-coded defect, negative sentiment and
performance praise, none significant), the agreement of the two existing LLM coders on 399 reviews, and the star-rating
distribution. Not seen: any output of the classifiers listed below, any latent-class estimate.

## Question
Do the null DiD results for the LLM-coded content outcomes (H3) reflect no effect, or an effect attenuated or distorted by
classification error? We answer this without human labels, using several classifiers and the four cells of the DiD design.

## Setup and propositions
Outcome y ∈ {0,1} (defect reported; negative overall sentiment; performance praised). Cells c ∈ {treated, control} × {pre, post},
true prevalence p_c. Classifier k reports ỹ_k with sensitivity Se_k = P(ỹ_k=1 | y=1) and specificity Sp_k = P(ỹ_k=0 | y=0);
Youden index J_k = Se_k + Sp_k − 1.

- P1 (attenuation). If classifier k's errors do not depend on the cell (non-differential), E[ỹ_k | c] = (1 − Sp_k) + J_k p_c, so
  the DiD of ỹ_k equals J_k times the DiD of y, and any linear DiD estimator with product and period effects is scaled by J_k.
  A null on ỹ_k is a null on y only up to the factor 1/J_k.
- P2 (identification without gold labels). If K ≥ 2 classifiers have cell-invariant accuracy and are conditionally independent
  given y, and the prevalence differs across at least two cells, then Se_k, Sp_k and every p_c are identified
  (Hui and Walter 1980). With K = 3 classifiers and four cells the model is over-identified (32 cell-pattern frequencies minus
  4 constraints = 28 free moments against 4 + 6 = 10 parameters), which allows tests of cell invariance and one pairwise
  conditional dependence.
- P3 (differential error). If accuracy varies by cell, the DiD of ỹ_k contains the additional term
  DiD[1 − Sp_k] + DiD[(J_k − J̄_k) p], which can create or hide an effect. The over-identification test of P2 detects it
  when it is large enough.

## Classifiers (fixed now)
1. H: the existing LLM coding of all 17,476 reviews (smaller model; model ID to be recorded from the coding session).
2. S: an off-the-shelf supervised sentiment model from Hugging Face, run locally (negative sentiment only).
3. Z: an open-weights zero-shot classifier (NLI entailment model) from Hugging Face, run locally, with fixed hypothesis
   sentences per outcome, threshold 0.5 on the entailment probability.
   Because it is slow on CPU, Z is run on a random subsample of 1,000 reviews per cell (seed 20261015), fixed before any Z
   output exists; the latent-class likelihood treats Z as missing elsewhere (missing at random by design).
4. L: a transparent keyword rule for defect reports (list fixed in code before it is run).
5. Star rating as an auxiliary test for negative sentiment (rating ≤ 2), used only in a sensitivity analysis because it is not
   a reading of the text.
Classifiers 2–4 have different error mechanisms from H, which makes conditional independence more plausible than for two LLMs
of one family. The existing second LLM coder (A, 399 reviews) is used only to measure dependence between two LLMs.
Exact model names, revisions and thresholds are recorded in the code before the first run.

## Estimation
- Primary: for each outcome, a latent-class model with cell-specific prevalence and cell-invariant Se_k, Sp_k for the
  available classifiers (defect: H, Z, L; negative: H, S, Z; performance praise: H, Z), estimated by maximum likelihood (EM);
  standard errors by product-cluster bootstrap (500 resamples).
- Corrected DiD: (i) the DiD of the estimated cell prevalences; (ii) the study-3 fixed-effects DiD on H divided by Ĵ_H, with a
  bootstrap interval that re-estimates both.
- Over-identification: likelihood-ratio test of the primary model against cell-varying Se, Sp for H (P3), and against one
  pairwise dependence term (H–Z).
- Performance praise has only two classifiers, so its model is just identified under P2 and cannot be tested; it is reported as
  secondary.

## Decision rules
- If the corrected DiD for an outcome has a 95% interval excluding zero, we state that the null on the LLM-coded outcome
  understated the effect; otherwise that the null holds after correction.
- If the over-identification test rejects at 5%, the corrected estimate for that outcome is reported as not credible, and the
  partial-identification bounds (Horowitz and Manski 1995) under a maximum error rate equal to the largest estimated
  1 − Sp or 1 − Se are reported instead.
- A simulation with known parameters, run before the real estimates, must recover Se, Sp and the DiD within 2 standard errors
  in at least 90% of replications; otherwise the estimator is fixed before it is applied.

## Not allowed after seeing classifier outputs
Changing classifiers, hypothesis sentences, thresholds, keyword lists, the cell definition or the primary model.

## Amendment 1 (2026-10-15, before any Z output was inspected)
The base zero-shot model processed 96 reviews in ten minutes on the available CPU, which would make the 4,000-review subsample
take about seven hours. Its 96 outputs were deleted without being inspected. Z is changed to
MoritzLaurer/deberta-v3-xsmall-zeroshot-v1.1-all-33 (revision 262ae02f29173eec1c250f90804dc7edc677dcff), with the same
hypothesis sentences and threshold, texts truncated to 256 tokens, on a random subsample of 300 reviews per cell
(seed 20261015). H, S and L remain on all 17,476 reviews.

## Record of the existing LLM coders (added 2026-10-15; no estimate affected)
- H (all 117 batches H0–H116, 17,476 reviews): claude-haiku-5-5 sub-agents (requested as "haiku") of the Claude Code session
  of 2026-10-13, workflows wf_99ecc0dc-5b4, wf_df3c643a-54d and wf_7a12dcf5-d0e (overlapping batches H4–H5 and H97–H98 were re-runs).
- A (validation, 399 of the 400 planned reviews): claude-sonnet-5-5 sub-agents (requested as "sonnet"), workflow
  wf_99ecc0dc-5b4; identified by the commit times of out/A_*.csv (07:23–07:25 UTC, after the study-3 sample was created at
  07:22:44) and by all 399 review ids belonging to val_ids.json.
- Sampling parameters were the agent's defaults; temperature was not set.
