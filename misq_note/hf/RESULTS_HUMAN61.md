# Second human-coding round: 61 war-period signal posts (plan: ANALYSIS_PLAN_HUMAN.md, Amendment 1; code: analysis_human61.py; output: results_human61.json)

Codebook v2; two coders, text only, different item orders; all 61 posts coded by both.

## Agreement
- Human A – Human B: κ = 0.69 (agreement 79%), up from 0.51 in round 1 with the v1 codebook (different post set). Consensus on 48 of 61 posts; 13 disagreements (to be adjudicated by the principal investigator from text only; adjudication sheet prepared).
- Human consensus distribution (n = 48): DEESC 25, MIXED 9, OTHER 8, ESC 6.
- Model 1 – Human A: κ = 0.30; Model 1 – Human B: 0.27; Model 1 – consensus: κ = 0.31 (agreement 56%) — weak.
- Model 1 de-escalation labels (33 posts) vs the human consensus: DEESC 21, MIXED 4, OTHER 4, ESC 0, no consensus 4 → precision 21/29 = 0.72 on consensus posts, and no model DEESC post was called escalation by the humans.
- Model 1 escalation labels (28 posts): human consensus DEESC 4, ESC 6, MIXED 5, OTHER 4, no consensus 9 → precision 6/19 = 0.32; the model's escalation class is largely not escalation in human judgment.
- Test–retest on the 18 posts coded in both rounds is not interpretable: Coder A agrees with their own round-1 label on 28% (κ 0.03), coder B on 61% (κ 0.46); the codebook changed between rounds and it is not known that the sheet labelled A or B was filled by the same person.

## Tests on human labels (tick data; directional return in %; plan H6)
| Human-consensus class | n | mean 5 min | mean 30 min | median 30 min | one-sided Wilcoxon post30 > 0 | pre-30 mean | paired post − pre (30 min) | Wilcoxon p |
|---|---|---|---|---|---|---|---|---|
| DEESC (sign −1) | 25 | +0.59 | +1.03 | +0.47 | **0.0015 (H6a supported)** | +0.69 | +0.35 | **0.082 (H6c not supported)** |
| ESC (sign +1) | 6 | +0.78 | +0.74 | +0.64 | 0.016 | +0.36 | +0.39 | 0.16 |
For comparison, model-1 labels on the same 61 posts: DEESC (n = 33) 30-minute mean +0.86 (p = 0.0011), post − pre +0.43 (p = 0.025); ESC (n = 28) +0.07 (p = 0.38).
Sensitivity (a post counts as DEESC if either coder says DEESC, n = 30): 30-minute mean +0.89, p = 0.0015; post − pre +0.35, p = 0.062.
**Decision under the pre-registered rule:** H6a is supported (25 human-labelled de-escalation posts, p = 0.0015), but H6c is not (p = 0.082). The paper may therefore claim a post-window response on human labels but may not claim on human labels that the response exceeds the pre-post drift. With human labels the pre-30-minute drift is larger (+0.69%).
Sign flips relative to model 1: 4 model-ESC posts are human-DEESC; 0 model-DEESC posts are human-ESC; 17 posts the model called signal are MIXED or OTHER for the humans.

## What changes
1. The de-escalation response is not an artefact of model labelling: it is present, and similar in size, on posts that two humans agree are de-escalation.
2. The claim that escalation posts do not move oil depends on the model's escalation label, which is mostly not escalation by human judgment (precision 0.32). Human-labelled escalation posts (n = 6, all with positive 30-minute directional returns, Wilcoxon p = 0.016; exploratory, six observations) moved oil in the escalation direction by +0.74%. The data cannot support "no response to escalation"; they support "no response for posts the model labels escalation".
3. The post-versus-drift claim is weakened on human labels (p = 0.082, n = 25).

## Final human labels after adjudication (all 61 labelled; plan Amendment 1)
The principal investigator adjudicated the 13 disagreements from text only: ESC 5, OTHER 5, MIXED 3, DEESC 0. Final human labels for the 61 posts: DEESC 25, OTHER 13, MIXED 12, ESC 11. Model 1 against the final labels: κ = 0.29 (agreement 51%). Model-DEESC (33): human DEESC 21, ESC 1, MIXED 5, OTHER 6. Model-ESC (28): human ESC 10, DEESC 4, MIXED 7, OTHER 7 (precision 0.36). Sign flips: 1 model-DEESC post is human-ESC; 4 model-ESC posts are human-DEESC; 25 model-signal posts are MIXED or OTHER for the humans.

| Final human class | n | mean 5 min | mean 30 min | median 30 min | one-sided Wilcoxon post30 > 0 | pre-30 mean | paired post − pre | Wilcoxon p |
|---|---|---|---|---|---|---|---|---|
| DEESC (sign −1) | 25 | +0.59 | +1.03 | +0.47 | 0.0015 | +0.69 | +0.35 | 0.082 |
| ESC (sign +1) | 11 | +0.56 | +0.53 | +0.35 | 0.016 | +0.29 | +0.24 | 0.10 |
Decision: unchanged — H6a supported, H6c not supported. Human-labelled escalation (n = 11): 9 of 11 positive (oil rose after the post), range −0.75 to +1.78; exploratory (not a pre-registered hypothesis; one-sided test, no correction).
