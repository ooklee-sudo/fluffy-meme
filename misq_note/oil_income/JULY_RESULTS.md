# Census MRTS, July 2026 only (exploratory; `analysis_july.py`, `results_july.json`)
Requested by the author after the March–July results were seen, so this is exploratory, not pre-registered. Same rolling-origin method (36 months before March of Y, forecast July of Y, D = actual − forecast in logs; placebo = July of 2012–2019 and 2025; n = 10 incl. 2026; July 2026 is a preliminary figure).

- **Restaurants:** food services 722 +0.019 (p = 0.4); restaurants 7225 +0.023 (p = 0.4); limited-service +0.014 (p = 0.7); full-service (derived) +0.033 (p = 0.3); ratio limited/full −0.019 (low-tail p = 0.2). No decline in any.
- **Discretionary vs essential:** ratio R = +0.081 (highest of ten; low-tail p = 1.00); DISC +0.053 (every category above forecast: furniture +0.023, electronics +0.063, clothing +0.032, sporting/hobby +0.084, misc. +0.081); ESS −0.028 (p = 0.2): grocery −0.009 (p = 0.5), health and personal care −0.065 (lowest of ten, low-tail p = 0.10).
- **Others:** motor vehicles +0.033, building materials +0.065, department stores +0.040, general merchandise +0.017, nonstore +0.019, gasoline stations +0.179 (price effect).
- Checks for R: no trend +0.056; 24-month training +0.044.

**Reading.** July alone gives the same picture as March–July: no decline in restaurants or in discretionary retail relative to the pre-war trend; the only category below its trend is health and personal care. Nominal sales; one month; ten reference years.
