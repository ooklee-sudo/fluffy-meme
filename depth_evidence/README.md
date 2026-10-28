# Depth-of-use evidence for the Section 3.8 conjecture

`fetch.py` pulls Eurostat `isoc_eb_ai` (AI use by technology, purpose, software source), `analyze.py` tests whether, among AI-using firms,
breadth of use (>=2 / >=3 purposes, >=3 technologies) falls where more users run ready-to-use commercial software (`E_AI_ARDY / E_AI_TANY`, 2024).
Result (`depth_results.json`): no relation across 23 countries (rho = -0.03, p = 0.91 for >=2 purposes; rho = -0.33, p = 0.13 for >=3 technologies).
Across size classes the relation is positive (size confounds). Breadth among users rises over 2023-2025. The claim is therefore not supported by these data.
