# Public-disclosure validation cases, 2026-09-28

U.S.-listed firms whose own primary sources (engineering blogs, press releases, investor material,
papers by staff) state that they deployed RAG and/or fine-tuned their own language models. Collected
by an AI research agent (Claude) on 2026-09-28; a claim was kept only if it appeared on a source page
the agent retrieved. No human coding. This is the validation subsample in Sections 4.2 and 5.2 and
Online Appendix Tables A1–A3 of the manuscript.

| File | Contents |
|---|---|
| `public_cases.csv` | 26 cases: dates, quotations (≤ 40 words), source URLs, notes |
| `public_cases_queries.txt` | the 88 search queries, in the order run |
| `public_cases_vs_edgar.csv` | cases matched to EDGAR by ticker (SEC `company_tickers.json`), with first confirmed EDGAR RAG/FT dates from `../edgar_2026-09-28/edgar_docs.csv` |
| `public_stats.json` | the counts quoted in Section 5.2 |

Web pages change; re-check the URLs before submission.
