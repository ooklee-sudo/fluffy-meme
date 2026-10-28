# Pilot: Web Data Commons JobPosting data as a firm-level source for H3

`parse_wdc.py` turns a class-specific JobPosting N-Quads part (https://data.dws.informatik.uni-mannheim.de/structureddata/<crawl>/quads/classspecific/JobPosting/part_N.gz)
into one row per posting (title, hiring organization, date, description, country). `pilot_stats.py` computes the diagnostics in `pilot_part13_stats.json`
(one of 14 parts of the 2024-12 crawl, 70,051 postings). `crawl_panel_stats.json` compares the per-domain statistics of the 2022-12, 2023-12 and 2024-12 crawls.

Keyword rules in `pilot_stats.py` for visual roles, generative-AI mentions and complement-type roles are crude, multilingual only in part, and untested for recall.

## Full panel run (2022-12, 2023-12, 2024-12 crawls)
Pipeline: `build_panel.py CRAWL PART OUT` for every part (aggregates per hiring organization and extracts visual-role / complement-role candidates)
-> `llm_classify.py` (`visual_title`, `complement_title` on unique titles; `ai_level` on visual postings with a generative-AI keyword hit plus a random non-hit sample)
-> `panel_analysis.py` (see its docstring). Results: `results/panel_result.json`; title labels in `results/`.
Posting descriptions are not stored in the repository.

Findings (see `results/panel_result.json`): visual-role postings 30.7k / 28.1k / 24.5k (2022 / 2023 / 2024); postings mentioning generative-AI tools 11 / 176 / 721;
postings requiring them as a skill or core duty 0 / 24 / 50. Among employers with visual postings in 2022 (n = 3,388), the use x complements interaction on the change in visual-posting share is -1.86 pp (p = 0.064),
but the 2022-2023 placebo gives -2.43 pp (p = 0.009), so the design does not identify the mechanism. Among employers using generative AI (non-visual postings), complements do not raise AI mentions in visual postings (logit -0.20, p = 0.52).
Acquirer = generative-AI keyword in postings other than visual roles; complements = legal/compliance/privacy/AI-governance or creative/design-leadership posting titles; both are crude.
