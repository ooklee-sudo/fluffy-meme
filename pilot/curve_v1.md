# LLM-drafted-like share by publication week (strata: applicant group) — run on the user's computer

Baseline (pre-ChatGPT) weeks, scored out-of-fold: 210408, 211007, 220113, 220331, 220609, 221006 (11,905 docs); later weeks: 230406 … 261008 (17,881 docs). Machine documents 4,954 (draft+expand). Vocabulary 6,000.
Calibration (true share -> alpha-hat): 0.00->0.018, 0.02->0.036, 0.05->0.061, 0.10->0.104, 0.15->0.143, 0.20->0.185, 0.30->0.262, 0.40->0.345, 0.50->0.425, 0.70->0.586, 1.00->0.839

Data: `curve_v1_data.csv`; figure: `figures/prevalence_curve.png` (script `plot_curve.py`).

Summary: the six pre-ChatGPT baseline weeks are flat (alpha-hat 0.014–0.024, calibrated share ≤0.7%). Publications of 2023 are still flat (0.019, 0.017). The rise starts with 2024 publications (0.024, 0.025), continues in 2025 (0.028, 0.035) and reaches 0.052 / 0.046 / 0.061 in 2026 (calibrated share 4.0% / 3.1% / 5.0%). US applicants rise faster than non-US (Oct 2026: 0.075 vs 0.051); small firms (<10 applications that week) are about twice as high as large firms (0.072 vs 0.035). By CPC section the pooled post-minus-baseline difference is largest in G (+0.021), A and B (+0.016), C (+0.013), H (+0.010), E (+0.009), F (+0.008).
