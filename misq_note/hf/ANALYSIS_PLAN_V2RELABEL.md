# Pre-registration: model re-labelling under codebook v2, label-set comparison, and reporting fixes (2026-10-14)

Prompted by simulated review round 3 (reviews/review_round3_synthesis.md). Already seen: human final labels and all results in RESULTS_H7.md, RESULTS_H5C_H8.md, RESULTS_ROBUST_HEADLINE.md; the original model-1 labels and their agreement with humans (κ 0.50; escalation precision 31/63 pooled, 10/28 in round 2). Not seen: any model label produced under codebook v2.

## A. Re-labelling
Instances: four independent model runs (three different model sizes and one repeat), each given only (i) the codebook v2 text exactly as the human coders saw it (hf/human_coding_sheet130_coderA.xlsx, sheet "Codebook") and (ii) the 191 post texts exactly as shown to the human coders, in a different random order per run, with no ids, times, prices, source labels, human labels or earlier model labels. Each run returns one class per item (ESC, DEESC, MIXED, OTHER) and a confidence (1 or 2). Runs write only to a file outside the repository; they are instructed not to read any other file. The model name and version of each run are recorded. The consensus model-v2 label is the majority of the four runs (ties → the label of the largest run; reported).

## B. Agreement and error profile (descriptive)
Cohen's κ (with 95% bootstrap CI) of each run and of the majority against the final human labels on all 191 posts, by round (2: 61 posts; 3: 130 posts); class-level precision and recall; pooled and by round; model-v2 versus the original model-1; κ among the four runs; Gwet's AC1 alongside κ.

## C. Event-study comparison on the same events
Events: the posts passing the three-hour cluster filter (computed on the 191 posts) with a valid tick window (last tick ≤ 10 minutes old at t and t+30 minutes). For each labelling (human final; model-1; model-v2 majority; each run) compute the mean directional 30-minute WTI return by class (sign −1 for DEESC, +1 for ESC). Formal comparison: for human versus model-v2 and human versus model-1, the difference in class means, with a day-clustered bootstrap (10,000 resamples of days) 95% CI over the union of valid-window events; two-sided p. Reported for the escalation and the de-escalation class separately.

## D. Adjudication sensitivity (escalation)
For the human-label headline report: (i) all final labels; (ii) coder-consensus labels only; (iii) adjudicated items only; (iv) adjudicated items set to OTHER. For each: n and the 30-minute mean, median, two-sided Wilcoxon p and day-clustered bootstrap CI.

## E. Reporting fixes
Headline human-label results re-stated with two-sided p-values and day-clustered bootstrap CIs; placebo re-run on the headline sample (29 and 16 events, post-30 only) so that placebo and headline use the same events; the number of events dropped in the "23 March and 7 April" variant is 3.

## Decision rules
If model-v2 agrees with the humans at κ ≥ 0.60 and its escalation precision is ≥ 0.70, the paper states that the first-stage failure was largely a prompt problem; otherwise that it persisted under the clearer codebook. A difference between label sets is called detectable only if the 95% CI excludes zero. No label set is chosen after seeing its results.

## Not allowed after the labels are seen
Changing the codebook text, the run set, the majority rule, or the event set.
