# Pre-registration: independent third-coder adjudication (2026-10-14, before the third coder's labels are seen)

Motivation: simulated review round 4 (reviews/review_round4_synthesis.md) noted that 66% of the final escalation labels (27 of 41) and 11% of the de-escalation labels (5 of 46) were decided by the lead investigator, who knew the hypotheses. Already seen: all results using the investigator-adjudicated final labels.

## Design
A third coder, who does not know the research question, the hypotheses or any market result and has not seen the earlier labels, labels with codebook v2 (the text the two coders used) 45 items on which the two coders had not agreed before adjudication, mixed with 15 randomly chosen items on which they had agreed (controls; classes in proportion), in random order, text only, working alone. The sheet shows no model label, no coder label and no marker of which items are controls.

## Label rules (fixed now)
- New final label ("v3 final"): for the 45 items, the majority of (coder A, coder B, third coder); if all three differ, the label is MIXED if any of the three said MIXED, otherwise OTHER (so that no item is decided by the investigator); for all other items the unchanged coder consensus.
- Sensitivity: "third coder only" labels for the 45 items.

## Analyses (all as in the existing code, with the new labels)
1. Agreement: κ (95% bootstrap CI) of the third coder with coder A and with coder B on the 45 items and on the 15 controls; agreement of the third coder with the investigator's adjudicated label on the 45 items; the number of the 45 items whose final label changes, by class.
2. Headline: the human-label 30-minute directional WTI return by class under v3 final (n, mean, median, two-sided Wilcoxon p, day-clustered bootstrap 95% CI), replacing the investigator-adjudicated final labels; the same under "third coder only".
3. Label sets: agreement of model 1 and of the v2 majority with v3 final (κ, escalation precision and recall), and the Table-3 comparison (class means and the day-clustered bootstrap difference, 10,000 resamples) with v3 final as the human label set.
4. Report the adjudication split under v3 final (items decided by the third coder or by majority including the third coder, by class).

## Interpretation rules
- If the escalation estimate under v3 final remains positive with a day-clustered 95% CI excluding zero, the paper states that the escalation result does not depend on the investigator's adjudication; if not, it states that it does.
- The investigator-adjudicated results remain in the paper as the earlier analysis; no label set is chosen after seeing its results.
- If the third coder's agreement with the controls' consensus labels is below κ 0.40, the sheet is treated as unreliable and the analysis is reported as inconclusive.

## Not allowed after the labels are seen
Changing the item set, the majority rule or the tie rule, or dropping the third coder's labels for any item.
