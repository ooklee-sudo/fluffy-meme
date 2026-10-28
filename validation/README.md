# Validation of LLM visual-content scores against a human-coded sample

`human_validation.py` compares the LLM scores (`reproduction/results/task_scores_*.jsonl`) with the 199-task sample coded in an earlier session.
**Only one coder in that sample is human (coder A).** The sheet labelled coder B was filled by an AI rater (three model raters, median, then adjudication) in that session, so A vs B is human vs AI, not two humans.
Coder A's scores are reconstructed from the coder-B sheet and the list of A-B disagreements (A = B elsewhere); the reconstruction reproduces the session's reported distribution (81 / 64 / 54) and kappa (0.301; weighted 0.494).
The coding guide matches the narrow rubric of Appendix A of the manuscript. The sample is not low-prevalence (41 percent of coder A's scores are zero).

Results: `results/human_validation_results.json`; per-task scores: `results/human_sample_scores.csv`.
The original draft's kappas (0.18 between coders; 0.11 and 0.04 for the narrow score; 0.31 to 0.41 for the broad rubric) are not reproduced by these data and could not be traced to a source file.

## Correction (session recovery, Oct 2026)

The original draft's κ values (0.18 between coders, 0.04 coder B vs LLM) are **invalid**: that "coder B" file
(`original_session/`, from branch `claude/cool-hamilton-bi4mzt`) held AI automation-difficulty scores (78/81/41), not human visual-creation codes.
Only coder A is human (the first author; no second human coder exists). Coder A vs the original LLM scores reproduces exactly with `original_session/agreement_creation.py`
(design-weighted exact agreement 0.73, weighted κ 0.11, linear κ 0.16, binary κ 0.15, sensitivity 0.12, specificity 0.98).

Design-weighted agreement of coder A with the current scores (key weights; n = 199):

| scorer | exact (unw / wtd) | weighted κ | linear κ | binary κ | sens | spec | PPV |
|---|---|---|---|---|---|---|---|
| original LLM | .56 / .73 | .11 | .16 | .15 | .12 | .98 | .75 |
| Haiku 5.5 | .55 / .75 | .18 | .23 | .21 | .17 | .99 | .82 |
| Luna 5.6 | .56 / .75 | .20 | .29 | .27 | .22 | .99 | .87 |

No human-human reliability exists. Run from `original_session/` data layout (`data/` folder) as in the script header.

## Two-coder result

Second human coder (undergraduate physics student, the author's relative; given only the written rubric, file `data/second_coder_filled.xlsx`) filled the blank sheet. `two_coder_agreement.py` (run from the `original_session/` layout) gives, design-weighted, n=199:
human-human exact 0.77 (unweighted 0.59), weighted κ 0.42, linear κ 0.49, binary κ 0.55.
Second coder vs original LLM: κ 0.13; vs Haiku: 0.11 (linear 0.16, PPV 0.54); vs Luna: 0.16.
Per-row scores: `results/two_coder_scores.csv`.
