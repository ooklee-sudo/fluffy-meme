# Revision materials: "When Do Better AI Coding Tools Ship Fewer Defects?"

Revision of ISRE-2026-4635 (desk-rejected at ISR), retargeted to **Management Science (IS department)**.

| File | What it is |
|---|---|
| `manuscript/manuscript.docx` | Full revised manuscript in MS submission format (blinded, double-spaced, Times 12 pt, native Word equations) with electronic companion. Yellow `[[…]]` = values you still need to fill in. |
| `manuscript/manuscript.md` | Source of the manuscript (Markdown + LaTeX math). Edit here, then rebuild. |
| `manuscript/build.py` | Rebuilds the .docx: `python3 manuscript/build.py` (needs pandoc and python-docx). |
| `proposition_cv.tex` | The new propositions (CV result and verification-adjusted quality) with proofs, in LaTeX. |
| `sim_cv_elasticity.py` | Numerical checks of the new results (Section EC.3); writes `results/cv_elasticity_checks.json` and `results/eps_vs_effort.png`. |
| `sim_power.py` | Power simulation for the proposed experiment; writes `results/power.json`. |
| `experiment_protocol.md` | Preregistrable design for the verification experiment (N ≈ 240). |
| `manuscript_edits.md` | Edit list against the ISR version, with the reasoning for each change. |

## Still to do before submission

1. Compute the nonparametric survivor-CV estimates and the Hill estimate of k (Table 2, Section 6.3) from the calibration data.
2. Estimate η across models (Section 6.4), ideally with more than eight models.
3. Fill Table EC.4 with per-model bootstrap intervals and mean detectability.
4. Optionally run the experiment and add Section 6.7.
5. Verify every newly added reference against the original source.
