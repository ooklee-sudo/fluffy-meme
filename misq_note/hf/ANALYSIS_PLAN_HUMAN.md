# Human validation of the model labels — analysis plan (committed before any analysis beyond eval_human.py, 2026-10-14)

Data: two human coders (A, B) independently coded the same 150 posts (sample W = war-period posts 67, A = pre-war Iran posts 23, B = other oil-geopolitics posts 60) using the codebook in the sheet, from text only. Already seen at the time of writing: only the output of the pre-existing script `eval_human.py` (pairwise kappas: A–B 0.509; A–model1 0.317; B–model1 0.309; A–model2 0.423; B–model2 0.429; model1–model2 0.742; accuracy vs human consensus 0.62 (model1) and 0.70 (model2) on the 97 posts where the humans agree).

## Pre-specified criteria
Validation status of a model labelling: kappa with the human consensus (posts where both humans agree) ≥ 0.60 "validated"; 0.40–0.60 "moderate"; < 0.40 "weak". Human–human kappa is the ceiling reference.

## Analyses (all descriptive; no hypothesis tests)
H1. Kappa and agreement by class definition: four classes; three classes (ESC, DEESC, non-signal = MIXED or OTHER); two signal-vs-not.
H2. Confusion matrices of model1 and model2 against the human consensus (n = 97) and against each human coder; per-class precision and recall for ESC and DEESC; separately for sample W.
H3. Where humans and models disagree: counts of the model-ESC/human-OTHER, model-DEESC/human-OTHER, and model-signal/human-opposite-signal cells; and the proportion of disagreements that involve re-posts/links (text empty after removing URLs) or MIXED.
H4. Headline relevance: among the 61 war-period signal posts used in the tick analysis, those that are in the human sample (identify by id), the human-consensus label versus model1, and the tick-level 30-minute directional return by agreement status (human consensus agrees with model1 / disagrees / no consensus). Reported descriptively; the overlap is expected to be small.
H5. Measurement-error implication: attenuation of the war-period de-escalation response if the model's DEESC precision is the sample precision (precision from H2, sample W). Back-of-envelope only: the true mean response among true-DEESC posts would be mean/precision if the false positives have zero response.

## Reporting
Everything is written to RESULTS_HUMAN.md and results_human_eval.json (existing) plus results_human_detail.json. If model kappa is "weak", the manuscript must say that model labelling is not validated and the headline must be described as conditional on it.

## Amendments
**Amendment 1 (2026-10-14, before the second human-coding round is returned).** Because the first round showed moderate agreement, a second round codes the 61 war-period signal posts used in the tick analysis (33 coded de-escalation, 28 escalation by model 1) with a clarified codebook (v2: demands and ultimatums without an announced pause or progress are ESC; DEESC requires an announced pause, ceasefire, agreement, progress, reopening or relief; both present → MIXED; links and re-posts without a stated stance → OTHER). Eighteen of the 61 were already coded in round 1 (v1 codebook); they are included again and give a test–retest comparison. The coders see only text; items are in a different random order for each coder; no labels, times or prices are shown.
Rule for labels: the human label of a post is the class on which both coders agree; disagreements are adjudicated by the principal investigator from the text only, without market information, and if not resolved the post is excluded from the primary analysis (sensitivity: treated as MIXED).
Pre-specified analyses on the returned sheets (descriptive agreement as above plus):
- H6a: among posts with a human label DEESC, the mean 30-minute directional return after the post (tick data, sign −1 for DEESC) > 0, one-sided Wilcoxon.
- H6b: among human-labelled ESC, the same with sign +1 (reported; no directional prediction beyond the earlier null).
- H6c: for human-labelled DEESC, the paired difference post-30-minute minus pre-30-minute return > 0, one-sided Wilcoxon (analogue of H5b). 
- Comparison: the same statistics with model-1 labels on the same posts, and the number of posts whose sign flips when the human label replaces the model label.
- The headline (human labels) is claimed only if H6a and H6c are both supported at α = .05 with at least 12 human-labelled DEESC posts; otherwise the paper must state that the de-escalation result is not confirmed on human labels.
