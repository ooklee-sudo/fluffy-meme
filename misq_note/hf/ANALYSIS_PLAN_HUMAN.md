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
(none)
