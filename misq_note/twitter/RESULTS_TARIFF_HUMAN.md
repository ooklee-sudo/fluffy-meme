# Tariff/trade tweets: human validation and human-label tests (plan: ANALYSIS_PLAN_TARIFF.md; code: analysis_tariff_human.py; output: results_tariff_human_final.json, human_labels_tariff_final.csv)

Two human coders labelled 150 tweets (30 model-agreed ESC, 30 model-agreed DEESC, 60 model-disagreed signal candidates, 30 model-agreed OTHER; a stratified, non-random sample of the kept tweets); coders agree at κ = 0.54 (71%); 44 disagreements were adjudicated by the principal investigator from text alone (DEESC 19, ESC 14, OTHER 11). Final human labels: OTHER 74, ESC 38, DEESC 38.

## Model labels against human labels
κ (four classes): model 1 = 0.39 (agreement 59%), model 2 = 0.34 (54%). Of the 60 items both models label ESC or DEESC, the human final label is the same for 33 (55%), OTHER for 19, and the opposite signal for 8 (13%). Of the 30 items both models label OTHER, 1 is a human signal. The models almost never miss a signal; they over-label signals and sometimes reverse the sign.

## Tests on human labels (valid S&P tick windows; directional 30-minute return, %, one-sided Wilcoxon)
| Human label | labelled | with window | mean 30 min | median | p (> 0) | post − pre | p |
|---|---|---|---|---|---|---|---|
| DEESC (S&P up) | 38 | 20 | −0.10 | +0.02 | 0.49 | −0.16 | 0.91 |
| ESC (S&P down) | 38 | 30 | +0.058 | +0.022 | 0.069 | +0.056 | 0.026 |
With model labels the same tests gave +0.085% (n = 70, p = 0.0007) for de-escalation and +0.046% (n = 50, p = 0.024) for escalation. **H10 on human labels: not supported for de-escalation, borderline for escalation (p = 0.069; the excess over the preceding 30 minutes is significant, p = 0.026).** The human-labelled subset is small and not random.

**H12 (state-dependent sign) on human labels:** n = 46 signal tweets with a window and a regime variable (meets the plan's n ≥ 40 for human-label primary status); β = −0.041 (SE 0.079); one-sided p = 0.70; two-sided p = 0.60. Not supported, consistent with the model-label result (β = −0.097).

## Reading
The tariff response seen with model labels does not survive in the human-labelled subset for de-escalation (the de-escalation estimate has the wrong sign, n = 20) and is weak for escalation. The model-labelled support for H10 in the tariff sample should be read as largely an artefact of a labelling that a human accepts for 55% of the model-agreed signals and reverses for 13%. The state-dependent sign proposition is not supported on either labelling.
Limits: a stratified, non-random sample; 20 and 30 events with windows; one adjudicator; windows exclude weekend/overnight tweets.
