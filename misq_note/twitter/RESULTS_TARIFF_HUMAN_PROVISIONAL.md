# Tariff/trade tweets: provisional human validation with one coder (coder B only; plan: ANALYSIS_PLAN_TARIFF.md; outputs: results_tariff_humanB_provisional.json)

Only coder B's sheet (150 items) has been returned; the coder A sheet for the tariff sample and both coder sheets for the oil/Iran tweets (coder A's file arrived blank: all 144 cells empty) are missing. With one coder there is no consensus label, so everything below is provisional and does not replace the pre-registered rule (consensus of two coders, adjudicated).

## Agreement with the model labels (single human, stratified sample: 30 model-agreed ESC, 30 model-agreed DEESC, 60 model-disagreed signal candidates, 30 model-agreed OTHER)
- Human B distribution: OTHER 83, ESC 32, DEESC 32, MIXED 3.
- κ (four classes): human B vs model 1 = 0.32 (agreement 54%); vs model 2 = 0.27 (49%).
- Items both models label the same ESC or DEESC (60): the human gives the same label for 26 (43%): ESC 11 of 30 (14 human OTHER), DEESC 15 of 30 (10 human OTHER).
- Items both models label OTHER (30): human OTHER for all 30.
- Items the models disagree on (60): human OTHER 29, ESC 18, DEESC 13.
The pattern matches the Truth Social sample: the models rarely miss a signal (none of 30 model-OTHER items is a signal for the human), but they over-label signals; the sample over-represents model signals by design, so these shares are not population rates.

## Provisional directional test with the single-human labels (valid S&P tick windows; one-sided Wilcoxon)
| Human B label | n | mean 30 min | median | p (> 0) | post − pre | p |
|---|---|---|---|---|---|---|
| DEESC (S&P up) | 20 | −0.07% | +0.04% | 0.32 | −0.11 | 0.65 |
| ESC (S&P down) | 25 | +0.06% | +0.02% | 0.099 | +0.05 | 0.086 |
With model labels the same tests gave +0.085% (n = 70, p = 0.0007) for de-escalation and +0.046% (n = 50, p = 0.024) for escalation. On the 45 posts both labelled by this human with a window the de-escalation response is not present and the escalation response is borderline.
Reading: the model-labelled support for H10 in the tariff sample is not reproduced on a small, single-coder, non-random human-labelled subset; the subset is underpowered (20 and 25 events) and not representative, so this neither confirms nor refutes it. It does show that the tariff results in the manuscript rest on labels that a human accepts for only about 43% of model-agreed signals.
