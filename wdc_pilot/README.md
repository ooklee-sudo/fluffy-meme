# Pilot: Web Data Commons JobPosting data as a firm-level source for H3

`parse_wdc.py` turns a class-specific JobPosting N-Quads part (https://data.dws.informatik.uni-mannheim.de/structureddata/<crawl>/quads/classspecific/JobPosting/part_N.gz)
into one row per posting (title, hiring organization, date, description, country). `pilot_stats.py` computes the diagnostics in `pilot_part13_stats.json`
(one of 14 parts of the 2024-12 crawl, 70,051 postings). `crawl_panel_stats.json` compares the per-domain statistics of the 2022-12, 2023-12 and 2024-12 crawls.

Keyword rules in `pilot_stats.py` for visual roles, generative-AI mentions and complement-type roles are crude, multilingual only in part, and untested for recall.
