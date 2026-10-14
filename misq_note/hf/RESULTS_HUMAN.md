# Human validation of the model labels (plan: ANALYSIS_PLAN_HUMAN.md; code: eval_human.py, analysis_human_detail.py; output: results_human_eval.json, results_human_detail.json)

Two human coders independently coded the same 150 posts from text only (sample W war-period 67, A pre-war Iran 23, B other oil-geopolitics 60). Humans marked 21% (A) and 34% (B) of items as unclear (confidence 2); no notes were written.

## Agreement (Cohen's kappa; simple agreement in brackets)
| Pair | 4 classes | 3 classes (ESC / DEESC / not-signal) | 2 classes (signal / not) |
|---|---|---|---|
| Human A – Human B | 0.51 (0.65) | 0.52 (0.71) | 0.49 (0.75) |
| Model 1 – Model 2 | 0.74 (0.83) | 0.74 (0.83) | 0.68 (0.84) |
| Human consensus (n = 97) – Model 1 | 0.43 (0.62) | 0.48 (0.69) | 0.46 (0.73) |
| Human consensus (n = 97) – Model 2 | 0.56 (0.70) | 0.59 (0.74) | 0.55 (0.77) |
| Human A – Model 1 / Human B – Model 1 | 0.32 / 0.31 | 0.34 / 0.34 | 0.27 / 0.34 |
| Human A – Model 2 / Human B – Model 2 | 0.42 / 0.43 | 0.45 / 0.46 | 0.37 / 0.44 |
Under the criteria fixed in advance (≥ 0.60 validated; 0.40–0.60 moderate; < 0.40 weak): Model 1 against the human consensus is **moderate** (0.43; 0.48 in three classes) and Model 2 is **moderate** (0.56; 0.59), against a human–human ceiling of 0.51. The two models agree with each other (0.74) much more than with either human, which is the signature of shared model bias, not of validity. In sample W alone, Model 1–consensus kappa is 0.38 (n = 33, weak).

## Class-level quality against the human consensus (n = 97)
Model 1: DEESC precision 0.52 (13 of 25), recall 0.77 (13 of 17); ESC precision 0.68 (13 of 19), recall 0.52 (13 of 25). Model 2: DEESC precision 0.54 (15 of 28), recall 0.88; ESC precision 0.73 (19 of 26), recall 0.76. In sample W: Model 1 DEESC precision 0.57 (n = 7), ESC 0.82 (n = 11); Model 2 DEESC 0.67 (n = 6), ESC 0.77 (n = 17).
The dominant error is model DEESC where the humans say OTHER (9 of 25 for Model 1; 11 of 28 for Model 2), followed by model OTHER where humans say MIXED (7) or ESC (6). 14% of the disagreements involve posts with no text beyond a link or re-post; 38% involve MIXED.

## Relevance for the war-period headline (descriptive; H4)
Eighteen of the 61 posts in the tick-level analysis are in the human sample. Among the 12 of them that Model 1 labelled de-escalation, the human consensus is DEESC for 3 (W08, W17, W19), ESC for 2 (W22, W26), OTHER for 1 (W40, a link), and absent (humans disagree) for 6. The 30-minute directional returns are +0.61% (mean, n = 3, humans agree), +0.36% (n = 3, humans disagree), +0.68% (n = 6, no consensus): three observations per cell, so no inference is possible.

## Implications
1. The model labels are not validated. A reader must treat every result as conditional on a labelling whose precision for the key class (de-escalation) is about one half against human judgment, with the humans themselves agreeing only at kappa 0.51.
2. If the false positives had no response, the response of truly de-escalating posts would be roughly twice as large (1/precision ≈ 1.8–1.9); if instead the response comes from a small subset of clear announcements (the 23 March and 7 April posts), it would not be affected. The data here cannot distinguish the two.
3. The most defensible remedy is a human-labelled primary sample for the war period (all 61 signal posts and a random sample of the rest), with the model labels used only for scale. This requires further human coding.
