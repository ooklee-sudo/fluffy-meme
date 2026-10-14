# Pre-registration (exploratory-labelled): do external events explain the over-dispersion of posting?

Written 2026-10-14 BEFORE any GDELT event count was downloaded or related to post counts. Status: EXPLORATORY. The question arose after the dispersion results (RESULTS_ARRIVALS_MODELS.md) were seen, so no test below is confirmatory; the plan fixes definitions so that the analysis cannot be steered afterwards.

## Idea under test
If influential people mostly post about external events and those events arrive roughly as a Poisson process, then (i) conditional on the day's recent events, post counts should be much less over-dispersed, and (ii) the dynamic dependence (self-excitation) should shrink. If, instead, over-dispersion stays when events are controlled, posting has its own dynamics (activity cycles, attention, internal agenda) and "the events are Poisson" cannot be the explanation.

## Data
GDELT 1.0 daily event files (storage.googleapis.com/data.gdeltproject.org/events/YYYYMMDD.export.CSV.zip), day = file date (UTC). Only daily counts are kept. Days: 2017-01-20 to 2021-01-08 (Twitter) and 2026-03-01 to 2026-10-13 (Truth Social).
Event series (counts of event rows per day; CAMEO columns as in the GDELT 1.0 codebook):
- E_IRN: EventRootCode in {18, 19, 20} (assault, fight, mass violence) with Actor1CountryCode or Actor2CountryCode = IRN, or ActionGeo_CountryCode = IR.
- E_WORLD_CONF: EventRootCode in {18, 19, 20}, any location.
- E_RIOT: EventBaseCode 145 (violent protest/riot), any location.
- E_USCHN: Actor1CountryCode = USA and Actor2CountryCode = CHN, or the reverse, QuadClass in {3, 4} (conflict).
- N_ALL: all event rows that day (media-volume control).
Threat events (root 13) are not used because they can be caused by the post itself.

## Post series (daily counts of original posts, UTC days; reposts excluded as before)
Twitter: all original; oil/Iran subset (frame_oil_iran); tariff/trade/China subset (frame_tariff).
Truth Social: all original; Iran-related posts (keyword class used in Section 4.1).
Event series assigned to samples: oil/Iran subset and Truth Social (both) use E_IRN; all-original series use E_WORLD_CONF; tariff subset uses E_USCHN; the riot series is used only with all-original series. No other pairing is run.

## Models (statsmodels NegativeBinomial NB2, ML)
- M0 (baseline): weekday dummies. alpha_0.
- M_week: weekday + calendar-week fixed effects (benchmark for how much slowly varying rate can absorb). alpha_week.
- M_ev: weekday + ln(1+E_{t-1}) + ln(1+mean(E_{t-2..t-7})) + ln(N_ALL_{t-1}). alpha_ev. Lags only, so that the post cannot cause the covariate on the same day.
- M_ev0 (sensitivity, contaminated by reverse causation): M_ev plus same-day ln(1+E_t).
Outcomes:
- R = 1 - alpha_ev / alpha_0 (share of NB dispersion removed by events). Bootstrap 95% CI, 2,000 moving-block resamples (block = 14 days).
- LR test of the two event terms (chi2, 2 df). One test per pairing; Holm across pairings.
- INGARCH check: NB-INGARCH(1,1) with the same covariates in the mean; report a+b with and without covariates (Twitter all-original and Truth Social only).
Decision rules (set now):
- "Events account for most of the over-dispersion": R >= 0.5 and LR Holm p < .05.
- "Events account for little": R < 0.2.
- Between: "partly".
- If alpha_ev is no smaller than alpha_0 in all-original series, the pairing is reported as no support.

## Confounds and limits (stated in advance)
1. GDELT counts reflect media coverage, which the poster's own behaviour influences (even with lags: a multi-day story). The N_ALL control only partly removes this.
2. The pairing of event types to post topics is crude; "the right event" for most posts (rallies, praise, domestic politics) is not in these series, so R for the all-original series will understate any true event-driven share.
3. GDELT 1.0 has duplicates and changes in source mix over time; levels are not comparable across years, which is why the models use logs and weekday terms, and why M_week is shown as a benchmark.
4. A reduction in alpha shows co-variation with events, not that events cause posts.
5. No ordinary-account comparison here (see ANALYSIS_PLAN_ACCOUNTS.md).
