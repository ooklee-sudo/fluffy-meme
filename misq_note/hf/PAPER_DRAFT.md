# Draft v0.2 — working title

**When Do Presidential Posts Move Markets? A Pre-Registered Mixed-Methods Study of Truth Social, Oil, and the 2026 Hormuz Closure**

*Status: first draft built only from results already committed in this repository (file pointers in brackets). Numbers are copied from the result files; nothing here is new analysis. Items marked [TODO] are missing or pending.*

---

## Abstract

Executive communication on social platforms is now a real-time input to financial markets, yet it is unclear whether this reflects a general "attention" channel or something narrower. We study 4,838 original Truth Social posts (1 March–13 October 2026) and two years of hourly futures data (October 2024–October 2026), centred on the 2026 Iran war and the closure of the Strait of Hormuz. We make three contributions. First, a descriptive one: post arrivals are not homogeneous Poisson (dispersion index 350 on 226 df; inter-arrival CV 1.94) but are well described by a Poisson process with a time-varying rate (week-fixed-effects dispersion 0.89), the Poisson–Gamma structure familiar from count data on digital platforms. Second, an empirical one: during the Hormuz closure, posts that blind coders classified as de-escalation were followed by WTI falling 1.29% over the next one to two hours (p < 0.001), together with a stronger dollar index, a weaker USD/CNH and higher Treasury futures (Holm-adjusted p ≤ 0.02); escalation posts show no detectable response within two hours, and posts on Fed policy and non-tariff China matters show none either. Third, a methodological and epistemic one: we pre-registered three successive theories (binding constraint, salience, habituation) and tested them out of sample. The first is only partly supported, the second is rejected, and the third cannot be confirmed or refuted for lack of power (MDE 0.82 versus an in-sample estimate of 0.24). An interpretive layer (136 posts coded blind by two analysts, triangulated against 20 market-wire cases) generates five themes and four propositions; the two testable propositions are not supported. We argue that the defensible claim is a state-dependent, context-bound response rather than a general law, and we report the negative results as findings.

## 1. Introduction

Since 2025 the U.S. president's own platform has been a primary channel for announcing tariffs, strikes and pauses. Market participants read these posts in real time; algorithms plausibly do too. For information-systems research this raises two questions that are usually treated separately: how do posts *arrive* (a question about the generating process of platform content), and how do markets *respond* (a question about platform-mediated information). We study both in one corpus.

The 2026 Iran war gives an unusual setting. From the first U.S. trading day (2 March 2026) crude oil rose from about $67 to $114.6 (7 April) while the Strait of Hormuz was physically blocked; a conditional ceasefire announced in a post late on 7 April was followed by the largest single-hour oil move in the sample. This invites a strong claim ("posts move oil") which our design is built to test and, where necessary, to withdraw.

**What we claim.** (1) Arrivals are overdispersed and bursty but conditionally Poisson. (2) A state-dependent response exists: it is large for de-escalation posts during the physical closure, small or absent before it, absent for escalation posts and absent for topics without a binding physical or legal constraint. (3) None of three general mechanisms is confirmed. (4) A transparent pipeline—independent model-instance coders, pre-registered plans committed before estimation, explicit out-of-sample tests—can produce credible negative results.

**What we do not claim.** We do not claim that posts cause price changes in general, that tariff or Fed posts move markets, or that any of our theories holds. We do not make normative claims about the communications themselves.

## 2. Background and Propositions

**Arrivals.** Count data on digital platforms are typically overdispersed; a Poisson–Gamma (negative binomial) mixture is the standard description, and the CGC/Poisson framework from the earlier research note in this project applies directly. [`poisson_posts/RESULTS.md`]

**Three pre-registered mechanisms.**
- *v1, binding constraint:* a post moves a market more when it changes expectations about a binding physical or legal constraint (here, Hormuz supply or the tariff schedule). [`THEORY_AND_PAPER_PLAN.md`]
- *v2, salience:* the reaction rises with recent posting intensity. [`THEORY_V2_SALIENCE.md`]
- *v3, habituation/credibility learning:* the reaction falls with the number of recent similar posts. [`THEORY_V3_HABITUATION.md`]

**Interpretive lens.** Speech-act theory (assertive, directive, commissive, declarative acts) and the validity claims of communicative action (truthfulness, sincerity, legitimacy) were used as sensitizing concepts only, with the suspicion and contextualisation principles of critical interpretive research for the reflexive parts. The study is not a critical-theory study: it makes no emancipatory claim. [`ANALYSIS_PLAN_QUAL.md`]

## 3. Data and Methods

**Corpus.** Original posts from the CNN Truth Social archive, with pure re-posts excluded in the arrival analysis; 373 of 4,838 mention Iran. Keyword selection produced 108 posts with Iran and a threat term (S1). [`poisson_posts/`]

**Markets.** Hourly Yahoo bars for WTI, Brent, E-mini S&P 500, ZN, DXY, USD/CNH, gold and equities; 5-minute bars for the last 60 days. Reaction = log change from the open of the bar containing the post to the close of the next bar; the null distribution is the same two-hour change in other bars without a keyword-selected post within ±2 h; 3-hour same-topic cluster filter; permutation tests. [`hf/ANALYSIS_PLAN.md`]

**Coding.** Each post is coded by two independent model instances for direction (ESC, DEESC, MIXED, OTHER) and type (ACTION, RHETORIC). The primary label is the one on which both instances agree. Cohen's kappa for direction: 0.84 (oil), 0.86 (tariffs), 0.92 (Fed), 0.87 (China); out-of-time sample 0.62 (oil) and 0.96 (tariffs); extension sample 0.75. Human validation on 150 posts [TODO: sheets distributed, results not yet returned; `eval_human.py`].

**Pre-registration ledger.** Every analysis had a plan file committed before estimation; amendments are dated and disclosed (e.g., Amendment 1 after the keyword class "threat" turned out to contain de-escalation posts). The full ledger is in Appendix A.

**Interpretive layer.** 136 posts (all 106 oil signal posts plus 30 random tariff posts) were coded inductively and blind to market data by two analysts; codebooks were reconciled and frozen before reactions were attached; 20 cases (8 largest reactions, 6 moves opposite to post direction, 6 flat de-escalation posts) were triangulated against market-wire reports collected without access to our reaction values. [`hf/qual/`]

## 4. Results

### 4.1 Arrivals
![Figure 1](figs/fig1_arrivals.png)
*Figure 1. Posts mentioning Iran with a threat term (S1; n = 108; 1 March–13 October 2026). A: observed daily counts versus fitted Poisson and negative binomial (log scale; the Poisson tail is too thin). B: weekly counts; the rate changes across weeks. Script: `make_figures.py`.*

Daily counts: variance 0.74 versus mean 0.48; dispersion index 350 (χ² p = 2e-7); negative binomial fits far better (size ≈ 0.79; LR p = 3e-6). Inter-arrival times: mean 51 h, median 21 h, CV 1.94, KS test against exponential p = 0.0001. With week fixed effects the Pearson dispersion is 0.89, close to Poisson: bursts in rate (11–14 March; 11–22 April), not within-week clustering. Weekly signal counts show no relation to weekly market outcomes (null). [`poisson_posts/RESULTS.md`, `RESULTS_MARKETS.md`]

### 4.2 The state-dependent response
![Figure 2](figs/fig2_event_time.png)
*Figure 2. WTI hourly path around blind-coded war-period posts (coders' agreed labels; de-escalation n = 33, escalation n = 27 with complete hourly windows). A: mean ± 1 SE; B: median. The path is the log change of the bar close relative to the open of the bar containing the post.*

Blind-coded de-escalation posts during the war (n = 33 with WTI bars): WTI −1.29%, Brent −1.21%, USD/KRW −0.14%, S&P 500 +0.23% (n = 14). Two posts (23 March, −9.8%; 7 April, −12.0%) contribute heavily; without them WTI still falls 0.67% (p = 0.002; median −0.30%). Escalation posts (n = 28): WTI −0.02% (p = 0.92). The result is similar under the second coder (−1.37%) and for posts on which both agree (−1.45%, n = 30). [`hf/RESULTS.md`, `RESULTS_EXT.md`]

Other assets (war period, de-escalation): ZN +0.10% (Holm p = 0.004), DXY −0.11% (0.014), USD/CNH −0.04% (0.02); gold not significant. A 5-minute subsample has only 9 oil posts and is uninformative (sign-flip p = 0.13). [`RESULTS_HOLDOUT.md`]

Before the war, Iran de-escalation posts give a smaller response in the same direction (about a quarter in size; significant only among agreed posts, n = 7–9), while for Russia/Venezuela-type posts the asymmetry reverses (escalation raises oil: +0.46%, p = 0.013). The effect is therefore context-bound. [`RESULTS_EXT.md`]

Figure 2 also shows what the pre-registered two-hour window does not: (a) the oil move into the post has the same sign as the move after it—WTI rose 1.38% (t = 1.57) in the five to six hours before escalation posts and fell 0.55% (t = −0.95) before de-escalation posts—so part of the post-window move may reflect the same news that prompted the post (the placebo window of two hours showed no systematic pre-trend); (b) the median path after de-escalation posts is much shallower than the mean (about −0.4 to −0.6% over 2–7 hours), consistent with the influence of the two extreme events; and (c) escalation posts are followed by a rise in WTI at 4–7 hours in both mean and median (exploratory; outside the pre-registered window, not tested).

Identification. De-escalation posts are a strong two-hour oil instrument but a weak daily one (first-stage F = 2.8), so effects on Korean airlines cannot be identified from them; the reduced form is null. [`RESULTS_IV.md`]

### 4.3 Three general theories
- **v1:** oil de-escalation, war versus pre-war: 1.39 pp difference (p = 0.014, Holm 0.056)—supported in the one cell with enough data; oil escalation (p = 0.86) and the tariff test (opposite sign, p = 0.09) are not. [`RESULTS_PAPER.md`]
- **v2:** the coefficient of log posts in the previous 7 days on standardized impact in hold-out topics is +0.045 (one-sided p = 0.44): rejected. Fed and non-tariff China posts show essentially no hourly reaction. [`RESULTS_HOLDOUT.md`]
- **v3:** in-sample the number of same-topic posts in the prior 24 hours reduces impact (−0.24, p = 0.036, exploratory). In the pre-registered out-of-time test (2022-02-14 to 2024-10-13; 49 signal posts) the coefficient is −0.09 (SE 0.29, one-sided p = 0.38); the minimum detectable effect at 80% power is 0.82, more than three times the in-sample estimate. Not confirmed, not refuted. Leave-one-year-out estimates are unstable (+0.81 without 2024). [`RESULTS_OOT.md`]

### 4.4 Interpretive findings
Two analysts' codebooks aligned on all six themes of the first analyst (some merged); post-level agreement on shared concepts ranged from kappa 0.37 (deal claims) and 0.42 (boasting) to 0.96 (amplification). The themes: (T1) pressure-then-pause cycles; (T2) concrete acts versus atmospheric statements; (T3) counterparty denial and partial retracement (C02: Iranian denial, rebound next session; C05; C07 reversal); (T4) the post as the carrier of the decision—4 of the 8 largest reactions are posts that are themselves the first public announcement of a ceasefire, postponement or approval; (T5) multi-causality—all 20 triangulated cases show other reported drivers, and 7 of 20 were not mentioned in market coverage. [`hf/qual/`]

### 4.5 Tests of the interpretive propositions
Pre-registered, pseudo-out-of-sample. **Q1** (re-posts and links produce no reaction while originals do): ORIG − AMP = −0.13 σ (CI −0.57, +0.31; one-sided p = 0.76; MDE 0.75): not supported. **Q4** (after-hours posts read better at reopening): −0.10 pp, p = 0.63 (in-sample, exploratory): not supported. **Q2, Q3** need news-coded data and are deferred to a prospective protocol. [`RESULTS_QUAL_TESTS.md`]

## 5. Discussion

**What the evidence supports.** A narrow but robust finding: when a physical constraint is binding and the post announces a pause, market prices of the constrained commodity and related risk assets move within hours. A second, descriptive finding concerns how platform posts arrive. The qualitative layer provides a coherent account of *which* posts were large (those that announce decisions), but this account did not survive out-of-sample tests.

**Implications for IS research.** (i) The unit of analysis for platform-mediated market information is the *announcement of a decision*, not the post as text—this makes the channel difficult to separate from the decision itself. (ii) Overdispersed, bursty arrivals mean that event-study designs relying on "random" posting times are fragile. (iii) The coding pipeline shows a transferable design: independent model-instance coders, agreed-label primary analysis, pre-registration committed before estimation, and explicit power reporting.

**Why the negative results matter.** Three generations of theory failed or could not be tested; the failure is informative about how much structure the data contain, and about the cost of confirmatory work in this setting (≈ 480–560 signal posts for habituation; years of prospective collection).

**Limitations.** Coders are model instances; human validation is pending. Posting times are endogenous; reactions at hourly horizons mix other news (20 of 20 triangulated cases). Keyword selection precedes coding. The qualitative analysts are also model instances; access limits and approximate quotations constrain the triangulation; reaction values were seen before themes were finalized. Many small subsamples (4–14 per cell). A single administration and a single war.

## 6. Conclusion

Posts by a head of state can coincide with large, fast market moves, but our evidence supports a context-bound, state-dependent response rather than a general mechanism, and we show how a pre-registered, mixed-methods design can make that conclusion credible.

---

## Appendix A. Pre-registration ledger (all committed before the corresponding estimation)

| Block | Plan file | Outcome |
|---|---|---|
| Arrivals | poisson_posts/ANALYSIS_PLAN.md | Not Poisson; conditionally Poisson |
| Weekly markets | ANALYSIS_PLAN_MARKETS.md | Null |
| Intraday core | hf/ANALYSIS_PLAN.md (+Amendment 1) | De-escalation response; escalation none |
| IV | ANALYSIS_PLAN_IV.md | Weak instrument (F = 2.8) |
| Extension | ANALYSIS_PLAN_EXT.md | Coder-robust; partial pre-war replication; Russia/Venezuela reversed |
| Theory v1 | THEORY_AND_PAPER_PLAN.md | Partly supported |
| Theory v2 | THEORY_V2_SALIENCE.md | Rejected |
| Theory v3 | THEORY_V3_HABITUATION.md | Underpowered |
| Qualitative | ANALYSIS_PLAN_QUAL.md (+Amendments 1–2) | Five themes; four propositions |
| Qualitative tests | ANALYSIS_PLAN_QUAL_TESTS.md | Q1, Q4 not supported; Q2, Q3 deferred |

## Appendix B. To do before submission [TODO]

1. Human coding of 150 posts (coder sheets A/B distributed): report kappa(model, human) and re-run the primary result on human-agreed labels.
2. Prospective collection protocol for Q2/Q3 and for a confirmatory habituation test (≥ 480 signal posts).
3. Replace approximate quotations in the triangulation with directly verified wire text where outlets allow.
4. Decide the journal fit: this is currently an empirical research note whose main contributions are descriptive plus negative; a theory-development outlet would require a confirmed mechanism.
5. Language edit; figure 3 (cell means of directional impact by topic and direction) if a third figure is wanted.
