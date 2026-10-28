# Validation of LLM visual-content scores against a human-coded sample

`human_validation.py` compares the LLM scores (`reproduction/results/task_scores_*.jsonl`) with the 199-task sample coded in an earlier session.
**Only one coder in that sample is human (coder A).** The sheet labelled coder B was filled by an AI rater (three model raters, median, then adjudication) in that session, so A vs B is human vs AI, not two humans.
Coder A's scores are reconstructed from the coder-B sheet and the list of A-B disagreements (A = B elsewhere); the reconstruction reproduces the session's reported distribution (81 / 64 / 54) and kappa (0.301; weighted 0.494).
The coding guide matches the narrow rubric of Appendix A of the manuscript. The sample is not low-prevalence (41 percent of coder A's scores are zero).

Results: `results/human_validation_results.json`; per-task scores: `results/human_sample_scores.csv`.
The original draft's kappas (0.18 between coders; 0.11 and 0.04 for the narrow score; 0.31 to 0.41 for the broad rubric) are not reproduced by these data and could not be traced to a source file.
