# Anthropic Economic Index: can it give tag-level AI usage? (checked 2026-10-30)

Source: Hugging Face `Anthropic/EconomicIndex`, CC-BY-4.0. Newest release `release_2026_06_26` covers Apr-May 2026 only.

- Categories: `overall`, `onet` (work tasks), `request` (topic hierarchy), `soc_occupation`. Geography: global, country, US subregion.
- `1p_api` excludes Claude Code. Claude Code usage is not in the data.
- Coding share: "Software Development" is 11.5% of claude.ai and 18.0% of 1P API conversations (level-2 request topic).
- Language/technology granularity is essentially absent. Only a few request-topic leaves name a technology: React (0.13%), SQL queries (0.11%), CSS styling (0.27%), JavaScript (0.01%), Git workflow (level 1, 0.19%). No Python, Java, C++, pandas, etc.

Conclusion: usable as an aggregate adoption trend (coding share over time across releases), not as a tag-level exposure or control variable.
