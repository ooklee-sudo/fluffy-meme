# Plan: validating gold-standard-free (latent-class) error estimates against human labels (Hormuz posts)

Written 2026-10-15, before the keyword and zero-shot classifiers below are run on these posts and before any latent-class model
is estimated on them. Already known: all human labels (coders A, B, third coder; v3 and investigator-adjudicated finals), all
LLM labels (model 1 and the four codebook-v2 runs) and their agreement with the human labels; the study-3 latent-class results.

## Purpose
The study-3 paper estimates classifier error rates without a gold standard (Hui-Walter latent-class model). Here the same
estimator is applied to the 191 war-period posts, where human labels exist, to check whether the latent-class estimates of
sensitivity, specificity and prevalence agree with the estimates obtained by treating the human labels as the truth.

## Units, populations, outcomes
- Units: the 191 war-period posts. Populations (playing the role of the DiD cells): four blocks of equal size by post time
  (48, 48, 47, 48 posts; the escalation and de-escalation prevalences differ across the phases of the war).
- Outcomes (binary): escalation content = label in {ESC, MIXED}; de-escalation content = label in {DEESC, MIXED}.
  The same mapping is applied to every classifier and to the human labels.

## Classifiers
- M1: model 1 (claude-sonnet-5-5, two-run first stage, first run; no codebook).
- K: keyword rules fixed in latent/classify_hormuz.py before the first run (escalation and de-escalation lists).
- Z: the zero-shot classifier of study 3 (MoritzLaurer/deberta-v3-xsmall-zeroshot-v1.1-all-33, revision
  262ae02f29173eec1c250f90804dc7edc677dcff), entailment probability >= 0.5, texts truncated to 256 tokens, with hypotheses
  "The post threatens, warns of, or announces military action or pressure against Iran." and
  "The post announces a pause, ceasefire, deal, talks, or easing of the conflict with Iran."
- Primary set: {M1, K, Z} (different error mechanisms, as in study 3).
- Secondary set, to show the effect of correlated classifiers: {M1, v2 opus, v2 haiku} (three LLMs of one family).

## Reference (human) labels
Primary: v3 final labels. Secondary: investigator-adjudicated final labels; coder-consensus posts only (coders A and B agree).

## Estimation and comparison
- Latent-class model with block-specific prevalence and block-invariant Se, Sp (latent.py from study 3); bootstrap of posts
  (1,000 resamples) for 95% intervals.
- Human-based values: Se, Sp of each classifier and block prevalences computed against the reference labels, with bootstrap
  intervals from the same resamples.
- Over-identification tests as in study 3 (classifier M1 varying by block; M1-Z dependence).

## Decision rules (fixed now)
- The method is judged consistent with the human labels for an outcome if, in the primary set, (a) the human-based Se and Sp of
  M1 lie inside the latent-class 95% intervals, and (b) the latent-class block prevalences differ from the human block
  prevalences by at most 0.05 on average (mean absolute difference).
- All point differences are reported whatever the decision, because with 191 posts the intervals are wide.
- The secondary (all-LLM) set is expected to overstate accuracy if LLM errors are correlated; this is reported as a
  demonstration, not as a test of the method.

## Not allowed after outputs are seen
Changing classifiers, keyword lists, hypotheses, thresholds, blocks, outcome mapping or decision rules.
