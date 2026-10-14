# Pre-registration: timing surprisal as a second information channel (P7)

Written 2026-10-14 BEFORE any timing-surprisal measure is computed. Not yet seen: any gap/timing measure related to a market reaction. Already seen (cannot be hidden): the 30-min |z| outcomes, N_c, U, and the arrival-process fits for all three samples.

## Theory link
A post carries information in what it says (content novelty N_c) and in when it arrives. If the market holds a predictive distribution over the poster's timing, a post at an improbable time has surprisal S = -ln f(gap | past) and should move beliefs more (the market learns that something changed). Content surprisal and timing surprisal are different channels; the paper currently measures only the first.

## Proposition
P7: Holding content novelty, prior uncertainty, pre-post volatility and time-of-day constant, a larger timing surprisal S predicts a larger 30-min absolute standardized return |z|.
Direction: beta_S > 0 (one-sided). A zero or negative estimate is reported as not supporting P7.

## Measure (fixed here)
Original posts only (reposts, links-only excluded exactly as in the existing frames). For post i at time t_i with gap g_i = t_i - t_(i-1) in seconds:
- Predictive model: log g ~ Normal(m_h, s^2), where h = one of 4 session buckets (US overnight 00-07 ET, premarket 07-09:30 ET, regular 09:30-16 ET, evening 16-24 ET) of the PREVIOUS post's time. m_h and s^2 are estimated from the account's gaps in the prior 60 days only (rolling origin; minimum 30 gaps, otherwise the post gets no S and is dropped and counted).
- Timing surprisal S_i = -ln f(g_i | h, past) in nats; standardized within sample for the regressions.
- The lognormal form was chosen because it was the best or near-best inter-arrival model for Truth Social and Musk and within a small margin elsewhere (RESULTS_ARRIVALS_MODELS.md). No other form is a primary alternative.
- Robustness measure S_cnt: Poisson-gamma (NB) surprisal of the number of posts in the 60 minutes up to and including post i, against the NB fitted to the same hour-of-week over the prior 28 days.

## Samples (all already built)
1. Truth Social 2026 war-period signal posts with WTI tick outcomes (the 61/191 signal frame; the larger 5-min sample where tick outcomes exist).
2. Twitter oil/Iran frame (341), WTI outcome as built.
3. Twitter tariff frame (937), S&P outcome as built.
Outcome: |z| = |30-min return after the post| / (sigma_d60 * sqrt(30/1380)), as in all earlier tests. No new market data are needed.

## Models
Primary (one test): pooled OLS over the three samples,
|z| = b0 + beta_S * S + b1 * N_c + b2 * U + b3 * |z_pre| + b4 * log(1 + posts in prior 60 min) + session dummies + sample fixed effects,
with standard errors clustered by calendar day. |z_pre| is the |z| of the 30 minutes before the post.
Secondary (Holm over the 3 samples): the same model fitted within each sample.
Confirmatory test: beta_S in the pooled primary model, alpha = .05 one-sided. Secondary tests are reported with Holm adjustment and are not used to rescue a failed primary test.

## Exploratory (not in any family)
1. S x N_c interaction (are the two channels additive or substitutes?).
2. S_cnt in place of S.
3. Winsorizing S at the 1st and 99th percentiles; log|z| as the outcome.
4. Dropping posts within 5 minutes of the previous post (burst repeats).
5. Dropping posts whose time coincides with scheduled data releases or a known external event in the existing event ledger.

## Known confounds and how they are handled
- Volatility clustering: an unexpected gap often follows a quiet spell and precedes news. |z_pre| and the prior-hour post count are controlled; if beta_S disappears with them, the paper states that timing surprisal does not add information beyond market state.
- Overnight/weekend gaps are long by construction; the session dummies and bucket-conditional means absorb the common part, but residual weekend effects are not modelled. Dropping weekend posts is listed as exploratory robustness.
- Staff-run or scheduled posting makes timing less informative and would bias beta_S toward zero.

## Interpretation rules
- beta_S > 0 and significant: P7 supported as "consistent with timing as an information channel"; no causal wording.
- Otherwise: P7 not supported. The paper states that, like HI1 and HI3, a measurable information-theoretic implication did not hold. It is not re-tested with other timing definitions.
- Counts of dropped posts per sample and the final n are reported.

## Not allowed after outcomes are seen
Changing the predictive distribution, the window (60 days), the bucket definition, the control set, or the sample set.
