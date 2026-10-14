# Pre-registration: high-frequency (tick/5-minute) test of the post–price timing (committed before any high-frequency data are analysed, 2026-10-14)

Motivation: simulated peer review (reviewer 2, M1) and our own bar decomposition show that hourly bars cannot separate the post from a pre-post drift (mean directional return in the hour before the post bar +0.36%, in the hour after +0.34%). The Yahoo five-minute series covers only the last 60 days (nine oil posts). We therefore obtain tick-level quotes for a WTI crude CFD (Dukascopy `LIGHTCMDUSD`, UTC time stamps) for the whole war period and measure returns around the exact post time.

Already seen: hourly results for all 61 war-period posts (RESULTS.md, RESULTS_REVISION.md). Not seen: any tick-level price around any post.

## Data and construction
- Ticks: bid/ask for 2026-03-01 00:00 UTC to 2026-10-13 23:59 UTC; mid = (bid+ask)/2; price at time s = mid of the last tick at or before s.
- Posts: the 61 war-period signal posts used in RESULTS_REVISION.md (33 DEESC, 28 ESC; ESC with incomplete prior-300-bar history are retained here since no history is needed). Exact post time = `created_at` (UTC).
- Directional return over (s, s+Δ] = sgn × 100·ln(P(s+Δ)/P(s)), sgn = +1 ESC, −1 DEESC. Post window Δ ∈ {5, 15, 30, 60, 120} minutes from t; pre window Δ ∈ {5, 15, 30, 60, 120} minutes ending at t.
- A post enters a window only if a tick exists within 10 minutes before each window endpoint (market open); otherwise the post is excluded from that window and counted (closed-market posts, e.g., weekends, are reported separately and descriptively as gap-at-reopen).
- Validation of the source: (a) correlation of hourly returns from the tick series with the hourly CL=F series over the war period; (b) the two-hour-from-bar-open directional mean for DEESC recomputed on tick data (should be close to 1.29%).

## Hypotheses (decision rules fixed now)
- **H5a (post-window response):** mean directional 30-minute return after the post > 0 for DEESC; one-sided Wilcoxon signed-rank, α = .05.
- **H5b (post exceeds pre-drift) — primary:** paired difference (post 30-minute return minus pre 30-minute return) > 0 for DEESC; one-sided Wilcoxon, α = .05. **The paper may claim that the post adds to a pre-post drift only if both H5a and H5b are supported.**
- **H5c (placebo):** observed mean DEESC-signed 30-minute return after the post exceeds the 95th percentile of 10,000 draws in which each event's time is replaced by a random time from the same UTC clock hour within ±3 days (excluding ±2 hours around any coded post) and the same weekday/weekend status.
- **H5d (speed):** report the cumulative directional return profile at 5, 15, 30, 60, 120 minutes after and the pre-drift profile; no test beyond the above.
- Secondary, same tests for ESC (expected null); week-block bootstrap CI for means; sign test.
- Heterogeneity (descriptive): reaction by first-source class from `results_wire.json` and by regular versus other hours.
- Standardization (secondary): divide by the standard deviation of 30-minute returns in the same UTC clock hour over the previous 20 days.

## Reporting
All results, including nulls and exclusions, go to RESULTS_5MIN.md. Code: `fetch_duka.sh`, `build_ticks.py`, `analysis_5min.py`; output `results_5min.json`. If the tick source fails validation (hourly-return correlation with CL=F below 0.9), the analysis is reported as invalid and not interpreted.

## Amendments
(none)
