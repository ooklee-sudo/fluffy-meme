# Simulated MISQ review, round 3 (three independent readers of MANUSCRIPT_MISQ_v3.md, 2026-10-14)

Verdicts: Reviewer 1 (IS theory and fit) reject in current form; Reviewer 2 (econometrics) major revision, borderline reject; Associate Editor desk reject as a MISQ research article, suggest a MISQ Research Note or a methods-oriented venue.

## Agreed by all three
1. Model-versus-human comparison is not like for like: the humans used codebook v2, written after the investigators saw the model's errors, and the model was never re-run with v2 definitions. Model name, version, prompt and temperature are not reported. The central lesson ("model labels mislead") is confounded with prompt quality.
2. The "reversal" is over-stated: model-ESC (+0.17, p = .26) and human-ESC (+0.48, p = .0065) are not tested against each other; confidence intervals overlap; samples differ (28/24 vs 16 events); ESC versus DEESC does not differ (p = .20). The title, abstract and 5.2 claim more.
3. The escalation labels depend on the investigator's adjudication. Checked in human_labels_191.csv: of 41 final ESC labels, 27 (66%) were adjudicated by the PI; of 46 final DEESC, 5 (11%). In the Table 3 sample, 7 of 16 escalation events were agreed before adjudication.
4. The 36% escalation precision is a round-2 figure on 61 model-selected posts (10 of 28). Checked: pooled over all 191 posts it is 31 of 63 = 49% (round 3: 21 of 35 = 60%); de-escalation precision pooled 35 of 57 = 61%. The abstract and 5.2 present 36% as general.
5. Primary sample redefined three times; the "confirmatory/pre-registered" language (Table 5, 3.5, abstract) overstates; plans are repository files committed on 13–14 October 2026. One-sided tests throughout; no day-clustered inference; Table 3 variants are not independent.
6. Theory has no weight; Section 2, Table 4 and Appendices D/E dilute the paper. Appendix D (Musk, GDELT, LLM releases) is peripheral and partly unverified.
7. IS relevance is not explicit; the LLM-annotation validity literature is not cited.
8. The key result lacks a main-text figure; Figure 2 caption (n = 27) conflicts with 4.2 (n = 28); terminology (P/H/HI labels), Table 1 cells, repository file names in the text, blind-review issues, placeholders.

## Additional points
- Placebo sample (26/14) differs from the headline (29/16); the placebo is not matched on prior volatility or drift; "drop 23 March and 7 April" removes three events, not two.
- Coders remembered the course of the war: outcome contamination of the human labels is possible; coders are from the author's department.
- 5-minute contrast: the pre-window is [−5,0] while drift occurs in minutes −30 to −5; the window was chosen after results.
- Selection: 48% of signal escalation posts have no window (weekend/closed market), against 22% of de-escalation.
- CFD timestamp alignment, roll and same-second ticks are not discussed.

## Consolidated plan
1. Re-label all 191 posts with blind model instances under codebook v2 (several instances); report κ and precision by class; re-estimate the event study with model-v2 labels; test model-v2 versus human labels on the same events (paired).
2. Report escalation results with and without adjudicated items; ask for an independent blind third coder on the adjudicated items if possible.
3. Reporting fixes: pooled precision; remove "pre-registered/confirmatory"; two-sided and day-clustered tests; three events dropped; same-sample placebo; caption and label consistency; name the model and prompt.
4. Soften the title and abstract; add a main-text figure of the human-label event-time path with placebo band; cite the LLM-annotation literature; strip repository file names; blind version; AI declaration.
5. Venue: MISQ research article unlikely; consider MISQ Research Note or a methods-oriented venue.
