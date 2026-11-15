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

## Calibration (regenerated, November 2026)

`calibration/` rebuilds the detectability data from scratch: 26 models x 157 HumanEval+ tasks x 20 samples
(81,640 solutions) sampled through OpenRouter, run in a sandboxed harness, and analysed by
`calibration/scripts/analyze.py` and `analyze_extra.py`. All Section 6 and EC.3-EC.5 numbers come from
`calibration/results/calibration_results.json`. Pipeline:

```
python3 -I calibration/scripts/prep_tasks.py calibration/data/humanevalplus/test.parquet calibration/data/tasks.json
python3 -I calibration/scripts/sample.py calibration/data/tasks.json calibration/data/samples MODEL ...
python3 -I calibration/scripts/harness.py calibration/data/tasks.json calibration/data/results.jsonl.gz calibration/data/samples/*.jsonl
python3 -I calibration/scripts/analyze.py calibration/data/tasks.json calibration/data/results.jsonl.gz calibration/results --core MODEL ...
python3 -I calibration/scripts/analyze_extra.py calibration/data/tasks.json calibration/data/results.jsonl.gz calibration/results/calibration_results.json
python3 -I calibration/scripts/make_figures.py calibration/results/calibration_results.json calibration/results/figures
```

## Still to do before submission

1. Optionally run the experiment (`experiment_protocol.md`) and fill Section 6.7, the one remaining placeholder.
2. Verify every newly added reference against the original source.
3. Note for the authors: Qwen 2.5 7B Instruct is no longer available, so Gemma 3 12B replaces it in the core panel.
