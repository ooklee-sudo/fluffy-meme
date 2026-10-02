# Open data used by the simulation (accessed 2026-10-02)

| File | Content | Source |
|---|---|---|
| gemini_lifecycles.csv | release and shutdown dates of Gemini-API models | https://ai.google.dev/gemini-api/docs/deprecations |
| gemini_prices.csv | USD per 1M tokens by tier and generation | https://ai.google.dev/gemini-api/docs/pricing (2.0 prices: third-party aggregators) |
| openai_deprecations.csv | announcement date, shutdown date, model (96 selected rows: one row per model, the replacement column dropped, endpoint and batch-duplicate variants thinned) | https://developers.openai.com/api/docs/deprecations |
| labor_bls.csv | median software-developer pay, May 2025 | https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm |

The tables were extracted with an automated page reader. Before submission, re-check every row against the live page (or an archived copy) and cite the access date.
Not available as open data: migration effort in person-weeks, outage cost per day, and token volume of a given enterprise. Those enter the simulation as assumptions and are varied in the sensitivity analysis.
Google does not publish announcement dates in the table, so notice periods come from OpenAI only.
