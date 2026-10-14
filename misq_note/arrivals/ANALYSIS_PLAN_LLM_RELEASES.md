# Pre-registration (exploratory): are LLM release times a Poisson process?

Written 2026-10-14 before the release-date table was parsed or any statistic computed (only the structure of the source was inspected: per-year wikitables with a "Release date" column in {{dts}} templates, day or month precision).

## Data
Wikipedia, "List of large language models" (wikitext fetched 2026-10-14; revision id recorded in the data file). Every row with a parsable {{dts|YYYY-MM[-DD]}} date, 2018-06 to 2026-10. Developer carried down over rowspans. Unparsable rows are counted and reported, not guessed. Dates are not edited by hand.
Known limits of the source (stated now): a crowd-edited list with notability-based inclusion; recent years are likelier to be complete; many rows have month precision only; "release" means whatever the editor recorded (announcement, weights, API); several rows are versions of one model family.

## Analyses
A1 (monthly counts, all rows with at least month precision, 2018-06 to 2026-09). Models by NB2/Poisson regression with log-linear time trend: Poisson; NB; Poisson with quadratic trend; NB with quadratic trend. AIC; dispersion alpha of the best trend model. Question: after allowing the rate to change over time, is the process still over-dispersed?
A2 (stationary-ish window). Same models restricted to 2024-01 to 2026-09 with trend; report alpha and the Poisson dispersion test (Pearson chi2/df).
A3 (day precision rows only, 2023-01 to 2026-10). Weekday distribution vs uniform (chi2, 6 df). Day-of-month first-week vs rest not tested. A homogeneous Poisson process implies weekday-uniform dates; business-calendar releases do not.
A4 (day precision rows, 2024-01 to 2026-10). Inter-arrival gaps in days between consecutive releases (all developers pooled; ties = 0 days): compare geometric (discrete memoryless), negative binomial, discrete lognormal by AIC; CV.
A5 (per developer, developers with >= 10 day-precision releases). Gaps and weekday distribution reported descriptively; no test family.
A6 (clustering, exploratory). For releases by developer X, the share followed within 14 days by a release from a different developer vs the share expected under a within-window Poisson rate (permutation of release days within the same quarter, 5,000 permutations).

## Decision rules
- "Consistent with Poisson (given a time-varying rate)": alpha CI includes 0 in A2 and weekday chi2 p >= .05.
- "Not Poisson": alpha > 0 with Poisson-to-NB LR p < .05, or weekday chi2 p < .05; the report says which.
- Multiple-testing: A1/A2 LR tests and A3 weekday test form one family of three (Holm).

## Not done
No dates added from memory; no model-family claims (what counts as a "release") beyond the source's own rows; no comparison with the 2017–2021 Trump arrival results other than describing them side by side.
