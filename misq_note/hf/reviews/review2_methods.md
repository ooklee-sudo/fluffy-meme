# MIS Quarterly review, Reviewer 2 (empirical methods and financial econometrics)

Manuscript: "When Does Executive Speech Move Markets? Platform-Mediated Announcements, Binding Constraints, and the Limits of General Theory" (MANUSCRIPT_MISQ.md).

Materials audited: the manuscript, figs/, the plan files (ANALYSIS_PLAN*.md, THEORY_*.md), RESULTS*.md, results*.json, post_reactions_oil_coded.csv, raw2y/CL_1h.csv, analysis_hf2.py and analysis_pretrend.py.
Numbers labelled "my recomputation" were produced read-only from those CSV files. They are not in the authors' result files.

---

## 1. Summary

The paper studies 4,838 posts from a head of state's platform, March to October 2026. It documents Poisson-Gamma arrivals. Its main empirical result is that WTI fell 1.29% over a two-hour window after 33 posts coded as "de-escalation" during the Strait of Hormuz closure, while "escalation" posts, Fed posts and China posts showed no reaction.
It then reports that three theory-derived mechanisms (binding constraint, salience, habituation) were "not confirmed" in pre-registered out-of-sample tests, and that four propositions from an interpretive analysis were not supported in held-out data.
The authors conclude that platform speech is "a conditional, announcement-carrying channel" and that pre-registered, LLM-coded, mixed-methods design makes this conclusion credible.
My assessment is that the headline effect is a post-hoc, single-regime, 33-event result whose identification rests on a research design that cannot separate the post from the news that prompts it. The "pre-registration" is a set of undated, self-hosted files, several of which are explicitly written after the authors saw the relevant data.
The confirmatory tests that were genuinely out-of-sample are mostly too underpowered or too far from the original setting to bear on the theories. The manuscript nevertheless treats them as informative rejections, and the headline as a protected finding.

---

## 2. Major concerns

### M1. The posting time is endogenous, and the design cannot distinguish "post moves oil" from "post and oil respond to the same news"

**What the paper says.** The paper acknowledges endogeneity (Sec. 4.2 and 5.4: "it cannot rule out that the post and the price move respond to the same news at the same moment"). It then draws causal-sounding conclusions anyway: "when a physical constraint is binding and a post announces a decision that relaxes it, prices of the constrained commodity respond within hours" (Sec. 1).

**Why this matters.** A de-escalation post is typically a response to a diplomatic development (talks, an Iranian offer, a mediator request). The authors' own qualitative work says so:
- RESULTS_QUAL.md: "all 20 triangulated cases have other reported drivers".
- qual/triangulation.md: case C07, a top-8 reaction, is attributed in the wires to the Iranian foreign minister's Hormuz announcement, not the post.
- C04 and C06, also top-8, are classed "B" (another event is the main cause). C03 is "A/B". So only four of the top eight reactions (C01, C02, C05, C08) are classed "A".

The asymmetry (de-escalation moves oil, escalation does not) is offered as evidence that markets treat the posts as news. It is equally what one expects if the price responds to real diplomatic or supply news, which is informative for oil when Hormuz is shut and largely priced when it is escalating.
The momentum control (RESULTS_PRETREND.md) tests a narrow thing. It regresses the forward 2-hour return on the prior 6-hour return in ordinary hours (slope -0.027, SE 0.019) and then subtracts a near-zero adjustment. By construction this changes the estimate by 0.03 pp (1.29 to 1.32) and cannot be informative about common-news confounding.
The manuscript says "The control rules out momentum". That claim is correct but is not the identification problem.

**The window is also contaminated by pre-post price movement.** The reaction is measured "from the open of the hourly bar containing the post to the close of the next bar" (Sec. 3.4). The plan (ANALYSIS_PLAN.md) calls this "conservative". For simultaneous news it is the opposite.
By my recomputation (post_reactions_oil_coded.csv with raw2y/CL_1h.csv, 33 war-period de-escalation posts), the post falls on average 40% of the way through its hourly bar, so about 40% of the first bar predates the post. The 2-hour reaction decomposes as:

| Bar | All 33 (mean) | Excluding the two extremes (mean) |
|---|---|---|
| bar k-1, the hour before the post bar | -0.36% | -0.32% |
| bar k, the post bar | -0.96% | -0.50% |
| bar k+1, the hour after the post bar | -0.34% | -0.17% |

The strictly pre-post hour (k-1) therefore carries a move the same size and sign as the strictly post-post hour (k+1).

**Remedies with existing data.**
1. Report the bar-by-bar decomposition above, with the lead bars k-1 and k-2 as pre-registered placebos, and re-estimate the headline using only bar k+1 (the first full hour after the post). Report the share of the effect that survives.
2. Do a timing placebo that preserves the news-flow structure: draw fake post times from the same hour-of-day within +/-3 days of each real post (excluding +/-2 h of any coded post) and compare. The current null uses all non-post war hours (n of about 3,160), which are systematically quiet, news-free hours. A permutation draw from them tests "post hour versus quiet hour", not "post versus other news".
3. Use the 59 keyword-matched Iran posts coded OTHER, which are already in post_reactions_oil_coded.csv, as a placebo-post class. RESULTS_PAPER.md shows OTHER-post absolute moves of 0.71% versus 1.00% for signal posts, so the contrast is already available. Test directly whether OTHER posts that coincide with de-escalation news (for example, those within 6 h of an independently timed wire item) show the same fall.
4. Use the wire items already collected in qual/triangulation_*.json. For each of the 33 events, code whether an independently timed, non-post item (Iranian statement, shipping report, official briefing) preceded the post by under 2 h. Estimate the effect in the "no-prior-news" stratum. If the effect persists there, the identification is much stronger.
5. The 5-minute subsample (the last 60 days, 9 oil posts) is too small. State this as the key identification gap rather than offering it as robustness.

### M2. The headline result is exploratory and post hoc, and the "pre-registration" does not protect it

**What the paper says.**
- The abstract uses the word "pre-registered" for the three mechanisms. The Sec. 1 contribution list calls the paper's design the thing "that makes the negative results interpretable".
- Sec. 3.5: "Each analysis had a written plan, committed to the project repository before estimation."
- Appendix A lists each plan and its outcome.

**What the "already seen" disclosures in the plans actually show.**
- ANALYSIS_PLAN.md, Amendment 1 (written after the first-run results): "The keyword class N contained the main de-escalation posts ... the first-run result that oil fell and stocks rose after 'threat' posts reflects that." The classification scheme that produces the headline was designed after seeing which posts moved oil. The amendment names the three extreme events (7 April, 23 March, 11 June) as the motivating examples. It states: "This is exploratory because it was designed after seeing the first results." The Abstract and Sec. 1 do not carry that label.
- Seen data (the author-disclosed text): ANALYSIS_PLAN.md says "no intraday return has been examined" when written. The F/C/oil/tariff windows, the 3-hour cluster rule, the +/-2 h null exclusion and the start date of the war regime were chosen before the first run. The classes were redefined after it. The headline is therefore a post-hoc relabeling that flips a significant opposite-sign finding (oil falls after "threats") into the reported one (oil falls after de-escalation).
- ANALYSIS_PLAN_EXT.md opens with "In the 2026 war sample ... the asymmetry ... was found ... This plan tests whether it replicates". The coder-robustness test (H_R3) re-labels the same events. The replication samples A and B are fresh. Sample A (pre-war Iran) is n = 7 to 9 and significant only in the "agreed" subset. Sample B reverses.
- THEORY_AND_PAPER_PLAN.md, hypothesis P1 (the paper's H1): "Predicted and already observed (exploratory): de-escalation lowers WTI by 1.3% in the war vs 0.3% before". The hypothesis is built from the result it then tests, on the same 31 war events (the O DEESC high cell, 1.40%, n = 31). H1 is not an out-of-sample test of anything for the oil cell.
- THEORY_V2_SALIENCE.md: "The new model is a revision after seeing those in-sample results". THEORY_V3_HABITUATION.md is built from an exploratory p = 0.036 that RESULTS_HOLDOUT.md labels "not corrected for multiple tests".
- ANALYSIS_PLAN_PRETREND.md is motivated by Figure 2 ("Motivation: Figure 2 ... shows that WTI moved in the direction of the post before the post") and by the raw reactions. Its primary hypothesis is that the raw effect will survive. The manuscript calls this "A pre-registered control".
- ANALYSIS_PLAN_QUAL.md: "the researchers (including the AI assistant) already know the quantitative results for these posts". The 20 triangulated cases were selected by reaction size (8 largest, 6 largest opposite, 6 flat), which is selection on the outcome by design.
- ANALYSIS_PLAN_QUAL_TESTS.md concedes that Q4 "includes the cases that generated the hypothesis" and that the Q1 holdout data were "already used in other tests".

**There is no external time-stamp.** All plan, code and result files carry modification times between 03:26 and 06:29 on a single day, 2026-10-14. The data end on 13 October. The pre-trend plan, the pre-trend script and the pre-trend results all have mtime 06:27. I cannot verify any ordering from the repository files. The manuscript says "committed" but gives no commit hashes or registry (OSF, AsPredicted, a registered-report track).

**Consequences.**
1. The one positive result in the paper is unprotected by pre-registration and is the one most exposed to forking paths. The negative results are protected, but, as M7 argues, they are mostly uninformative.
2. The paper's methodological claim ("we show how pre-registered mixed-methods design can make such a conclusion credible") is therefore inverted. Pre-registration constrains what was done after the plan, and nearly every positive element was determined before or without a plan.
3. The manuscript's Appendix A is a ledger of selected analyses. It omits the many unregistered analyses (analysis_robust.py, the other-asset runs, the 5-minute run, the exploratory habituation coefficient).

**Remedies.**
- Relabel the oil result everywhere (abstract, Sec. 1, Sec. 3.5, Sec. 5.2) as exploratory and discovery-sample, and demote "pre-registered" to describe only what was written before estimation, with a column in Appendix A for "data already seen" and "frozen before or after returns".
- Provide external time evidence (git commit hashes and dates for each plan file versus its first results file, or a third-party time-stamp). If none exists, say so plainly.
- Make the 14 October 2026 onward prospective sample the confirmatory test of the headline. The authors have already registered a prospective protocol for Q2/Q3. Extend it to the headline effect, with a fixed N and the analysis (windows, class definitions, exclusion rule) frozen in a dated, externally hosted file.
- Add a full forking-path table (see M3).

### M3. Researcher degrees of freedom, multiple testing, and the Holm family definition

**Specification space.** The headline cell is one of many the authors could have reported. The manuscript's own result files show:
- 9 assets x 3 classes = 27 cells in results_hf2.json (21 cells with a p-value in the recomputation file).
- results_ext.json contains roughly 183 entries with a p-value (my count of dictionary entries carrying `p` or `p_two`). That count includes coders 1, 2 and "agree", samples W/A/B, and WTI/Brent/equity assets.
- Three coder definitions (coder 1, coder 2, agreed), three pre-trend windows (2, 6, 12 h), with and without the two extreme events, and war versus pre-war regimes.
- Keyword set, 3-hour cluster rule, +/-2 h null exclusion and the war start date are all researcher-chosen.

**The Holm family is too narrow.** analysis_robust.py line 25: "Holm within each (tp,cls,rg) across the four assets". The Holm-adjusted p of 0.004 (Treasury), 0.014 (dollar) and 0.02 (yuan) in Sec. 4.2 corrects only over four assets within a single class and regime. It does not correct over classes, regimes, topics, coders, windows or plans.
The S&P 500 result (p = 0.006, n = 14) is reported uncorrected in the same paragraph where other assets are Holm-adjusted. Bonferroni over the 27 cells of the main run gives 0.006 x 27 = 0.16.

**H1 fails the authors' own Holm rule, but is treated as supported.** RESULTS_PAPER.md: "p = 0.014 (Holm-adjusted over the four primary tests: 0.056)". Sec. 4.3 then says "H1 is therefore supported in the one cell with enough data and not elsewhere". Sec. 5.1 says "The evidence supports a conditional and narrow claim". Sec. 5.2 calls "a boundary condition" "the paper's main theoretical claim". By the pre-registered rule that boundary-condition claim is not confirmed. Appendix A's "Partly supported" is closer to the truth than the text.

**Remedies.**
- Build a single forking-path table: every class definition, window, coder, sample and asset tried, with the number of cells. Report the adjusted p for the headline over the full family (Holm or Westfall-Young step-down using the permutation draws the authors already have).
- Report a specification curve for the headline cell: all coder choices x all windows (2, 3, 4 h) x with/without extremes x cluster filter (none, 3 h, 6 h) x null definitions.
- Report the one-sided versus two-sided choice consistently. The pre-trend test is one-sided (p = 0.0005); the headline permutation is two-sided.

### M4. Two events dominate, the p-values overstate the evidence, and the heavy-tailed null breaks the permutation scale

**Facts verified.** WTI means: -1.29% (n = 33), median -0.31% (results_hf2.json), -0.67% without 23 March (-9.8%) and 7 April (-12.0%). My recomputation:
- The two events account for 21.8 of the 42.6 summed percentage points, i.e. 51%. Sec. 4.2 says "most of it"; Sec. 5.4 says "about half".
- The sign test is 24 negative of 33, binomial p = 0.014. The Wilcoxon signed-rank is p = 0.010. The 10% trimmed mean is -0.81% and the 20% trimmed mean is -0.73%.
- The headline "p < 0.001" is a mean-based permutation p against a null with excess kurtosis of 13.1 (my recomputation on 3,164 non-post war bars).
- The 33 events fall on 26 distinct days in 16 distinct ISO weeks. The week means range from -4.1% to +0.9%. Four of 16 weeks (13, 15, 16, 24) carry the large negative values.

**The outside-U.S.-hours finding is not independent.** Sec. 4.2: "Reactions were larger for posts published outside U.S. equity hours (-2.25%, n = 16) than inside them (-0.39%, n = 17)". Both extreme events (7 April 22:32Z; 23 March 11:23Z) are outside U.S. equity hours. Removing them gives about -1.0% (outside) versus -0.39% (inside), by my arithmetic from the reported means. The "thin market" explanation is therefore an artefact of the same two events.

**Comparison with a null that ignores time-of-day volatility.** The plan (ANALYSIS_PLAN.md) said bars would be classified "by whether they are within regular U.S. equity hours". analysis_hf2.py does not do this for oil: the null is every non-post war bar.
Hourly standard deviations in the null range from 0.54% (02-03 UTC) to 1.64% (20 UTC) (my recomputation), so a pooled sd of 1.15% is wrong for specific posting hours.
An hour-matched permutation (my recomputation) leaves the mean-based p essentially unchanged. A standardized mean of -1.33 sd, t = -2.3, is far more modest than the pooled p suggests. The qualitative result is not an artefact of hour-of-day, but the strength is.

**Pre-war versus war scale (state dependence is partly a volatility effect).** This directly bears on H1. The unconditional 2-hour WTI sd is 0.60% before the war and 1.22% during it (my recomputation, raw2y/CL_1h.csv; ratio 2.04).
- The war effect, 1.40/1.22 = 1.15 sd.
- The pre-war Iran de-escalation effect (agreed, n = 8), -0.62/0.60 = 1.04 sd.

In volatility units the "state dependence" shrinks to nearly nothing, so a "quarter of the size" comparison in raw percent is mostly the volatility regime. Unlike the hold-out and out-of-time analyses, the headline H1 contrast is not standardized.
The H1 contrast (1.40 versus 0.01) also pools very different pre-war cells: Iran posts (n = 8, effect 0.62) with Russia/Venezuela/OPEC posts, for which the sign is reversed (Sample B: escalation raises oil). The "pre-war" cell of n = 24 thus mixes topics, which dilutes the pre-war de-escalation effect.

**Remedies.**
- Report medians, trimmed means, signed-rank and sign tests next to the mean for every directional cell. State the signed-rank p (about 0.010) as the main inferential number.
- Cluster or block by week (or by calendar day) in the permutation (block permutation, 16 weeks), and report a leave-one-week-out (jackknife) range.
- Standardize reactions by the hour-of-day-specific, trailing realized volatility (the same method used in the hold-out analysis, 300 prior bars) and redo the H1 contrast in standardized units, and separately for Iran-only pre-war posts.
- Present the effect with and without the two events as co-primary, not as "robustness".

### M5. Null construction and the permutation test

**Issues.**
1. The null is drawn from bars "that contain no keyword-selected post within two hours" (Sec. 3.4). Excluding bars near any coded post makes the comparator systematically quieter than the event hours. Mean realized vol over the prior 24 hours is 0.61 at events versus 0.54 in null bars (my recomputation). The null conditions on "no Iran-related news from the president", not on "no news".
2. The null is an unconditional bootstrap distribution of bar returns, not randomization inference over timing. Event hours cluster in time (bursts of 11-14 March and 11-22 April; Sec. 4.1), and war-period regimes within the war differ widely in volatility. A pooled null does not preserve either feature.
3. Adjacent null windows overlap by one hour (two-hour returns on hourly bars), so the null is serially dependent. The draws without replacement assume exchangeability that does not hold.
4. The 3-hour cluster filter is applied to coded signal posts of every class and uses the previous post of any class, including dropped ones (analysis_hf2.py: `keep.append(ep-last>=3*3600); last=ep`). A de-escalation announcement that follows a threat within 3 hours (the pattern the qualitative analysis calls "pressure then pause") is dropped. So the rule conditions on the label sequence. The effect of this filter on the cell composition is not reported, and no sensitivity is shown (no filter, 6-hour filter).
5. The sample of events comes from a keyword filter, Iran plus a threat term or one of: deal, ceasefire, cease-fire, agreement, peace, negotiat, talks, memorandum, reopen, "open". The filter has unknown recall for de-escalation posts that avoid those words (for example "we will hold off"), and the term "open" matches many non-geopolitical strings. The population is "Iran posts containing selected words", not "de-escalation posts".

**Remedies.**
- Add stratified nulls: hour-of-day, day-of-week and war-month blocks, and a null that excludes only the +/-2 h around events of the class being tested.
- Run a block-permutation/placebo-timing test (shift the 33 event timestamps by random offsets within the same week, preserving hour-of-day), 10,000 draws.
- Provide the filter's sensitivity (none, 6 h, 12 h) and the number of posts it removes by class.
- Estimate keyword recall on a random human- or model-labelled sample of all 373 Iran posts, to show how many de-escalation posts the keyword filter misses.

### M6. Coder-agreed labels, correlated coders, and possible look-ahead in the coders

**Selection on agreement.**
- Sec. 3.3: "The primary analyses use the label on which both instances agree; this rule was fixed before returns were examined." The files do not support this for the headline.
- The 33-post headline (-1.29%) is coder 1's labelling (post_reactions_oil_coded.csv, from posts_coded.json; Amendment 1). Coder 2 appears only in ANALYSIS_PLAN_EXT.md (03:34). The agreed-label rule is first written in THEORY_AND_PAPER_PLAN.md (mtime 04:31), after RESULTS.md (03:26).
- The reported numbers use three different n for the same concept, which a reader cannot reconcile: n = 33 (coder 1; 1.29%), n = 30 (agreed; -1.45%; RESULTS_EXT.md), n = 31 (agreed under a different sample and cluster filter; 1.40%; RESULTS_PAPER.md).
- Agreement is more likely for explicit, formal announcements (for example, the 7 April ceasefire). Those are also the posts most likely to carry market-relevant information. Conditioning on agreement is therefore conditioning on a text property correlated with treatment intensity.
- The pattern in the pre-war Iran cell is the standard signature: significant only for agreed posts (-0.62%, n = 8, p = 0.008), not for either coder alone (-0.30%, p = 0.16, n = 7; -0.28%, p = 0.13, n = 9). With n = 7 to 9 this is not a replication.
- Kappa is reported on the four-class direction variable (0.84, 0.86, 0.92, 0.87), which is dominated by the OTHER class. The kappa that matters is the ESC versus DEESC discrimination among signal posts. The out-of-time oil kappa is 0.62 (results_oot.json), and the extension sample is 0.75.

**The coders are not independent.** "Two independent model instances" of the same model family share training data, priors and failure modes. Their agreement measures reproducibility, not validity. Human validation is "under way" (Sec. 3.3, Appendix C is a stub). For a journal where LLM coding is a stated contribution (Sec. 5.2), validity against humans is a precondition, not a revision item.

**Look-ahead and label-design leakage.**
- "Blind to market data" does not mean blind to outcomes. Models with training data that overlaps the March to October 2026 period may know the oil path after the 7 April ceasefire or the 23 March postponement. The authors do not report the coders' training cutoff, or any test of leakage.
- The class definitions (DEESC = "hold-off, ceasefire, deal, talks, reopening") were written after the authors saw that the first-run "threat" class contained the large oil falls. The coders were blind, but the coding scheme was not.

**Remedies.**
- Report the confusion matrix (ESC/DEESC/MIXED/OTHER, coder 1 by coder 2) and the signed-effect for every cell of it, including disagreement posts: coder-1-only DEESC, coder-2-only DEESC, and both. If the effect is concentrated in agreed posts, say so.
- Report the headline on the union and the intersection of labels, and by confidence level (the `conf` column in post_reactions_oil_coded.csv is already available).
- Re-code the 33 plus 28 war posts with entity names, dates and place names redacted (a "text-only, time-blind" version), and with a second model family with a documented earlier cutoff. Compare the labels.
- Report the human validation before submission, or drop the claim that the coding pipeline is a contribution.

### M7. The negative tests are weakly informative and are reported as rejections

**Salience (H2).**
- The hold-out topics have essentially no first-order reaction (RESULTS_HOLDOUT.md: "essentially no hourly market reaction"; mean directional impact -0.01 to +0.02 percent). A moderator (posting intensity) cannot be detected where the main effect is zero.
- The coefficient is +0.045 with SE 0.31. The 95% CI is roughly +/-0.6 sd. The manuscript says "Salience through posting intensity is rejected" (Sec. 4.3) and "The same data reject a general salience channel" (Sec. 5.1). An equivalence test is not reported.
- In the Fed topic, all 55 signal posts are one direction, so direction cannot vary within the topic. The directional mapping (easing means Treasury futures up) is imposed.
- Posting intensity is an endogenous proxy of attention.

**Habituation (H3).** The paper correctly says "neither confirmed nor refuted" (MDE 0.82, more than three times the in-sample 0.24). But the out-of-time sample is not the same experiment as the hourly in-sample one. It uses daily returns, 2022 to 2024 (before the presidency), a private-citizen speaker, and a different standardization (20-day sd). Daily returns contain all of that day's news. This is a test of a different object.

**H1.** See M3 and M4: not confirmed by the plan's own Holm rule, in-sample, on a regime dummy.

**Interpretive propositions (Sec. 4.5).**
- Q1 compares "original versus amplification" using a pseudo-out-of-sample set that mixes daily out-of-time and hourly Fed/China data, 134 posts in total. These are standardized differently and have no first-order reactions (ORIG mean +0.03 sd), so there is nothing to differ.
- RESULTS_QUAL_TESTS.md says as much: "ORIG 평균 자체가 0과 거의 같다" (the ORIG mean itself is almost zero), "so there was nothing to distinguish from reposts".
- The minimum detectable effect, 0.75 sd, is larger than most effects in the paper. The manuscript's "Q1 is not supported" fits the rule but does not say the test could not have found anything.
- Q2 and Q3 are untested.

**What the pattern says.** The paper's conclusion ("none of the general theories holds") rests on one positive in-sample cell and a series of underpowered or off-target nulls. A null from a test with an MDE larger than the hypothesized effect says nothing about the theory. The cumulative sequence (v1, v2, v3, each built from the previous failure) is itself a forking path that the pre-registration ledger does not make credible.

**Remedies.**
- For every negative test, report the 90% CI, the equivalence margin and the smallest effect size of interest (TOST), not the point estimate and one-sided p.
- Change "rejected" to "not detected, MDE = X" throughout, in the abstract and Sec. 4.3, 5.1, 5.4.
- Where there is no first-order effect (Fed, China), do not test moderators. Test them in the topics where a main effect exists, as a pre-specified exploratory analysis.

### M8. "The asymmetry" and "escalation posts showed no response" are not tested

**Issue.** The paper's central contrast is that de-escalation posts move oil and escalation posts do not. This is a difference between a significant and a non-significant result. No test of the difference is reported for the war sample alone.
- ESC (n = 28): -0.02%, p = 0.92. The minimum detectable effect on that cell is about 0.61 pp (my calculation: 2.8 x 1.15 / sqrt(28)). That is roughly the de-escalation effect excluding the two extreme events (0.67%), so the escalation cell cannot rule out an effect of the same size.
- My recomputation of the directional difference (de-escalation minus escalation) gives about 1.31 pp. A one-sided Mann-Whitney test gives p of about 0.049. This is marginal.
- The one pooled test of asymmetry (RESULTS_EXT.md, pooled across contexts: difference -0.85 pp, p = 0.007) is pooled across samples where the sign reverses (Sample B), so it does not support the war-period claim.
- Sec. 5.4 says escalation posts "are followed by a rise in oil four to seven hours later in both mean and median paths, which falls outside our pre-registered window". The fixed 2-hour window therefore can favour a response with a fast adjustment (de-escalation as news) over one with a slow adjustment. The choice of window was not justified by any theory, and there is no multi-horizon analysis.

**Remedies.**
- Test the difference (de-escalation minus escalation, directional) with a permutation test and report the MDE for each cell.
- Report cumulative abnormal returns at 1, 2, 4, 6 and 12 hours for both classes with the same block-permutation CI. State the primary window's rationale.
- Replace "only those" (Sec. 1, contribution 2) and "escalation posts showed no response" (abstract) by a statement of what the data can exclude.

### M9. Dependence and cross-asset "corroboration"

- The dollar, yuan, Treasury and won responses (Sec. 4.2) are measured on the same 33 events and share the same common oil/geopolitical factor. They are not independent confirmations. They are the same event repeated in correlated assets, so consider them one test with multiple outcomes.
- The Holm correction across four assets with one family is therefore misleading as a measure of independent evidence.
- The S&P 500 effect is based on 14 events with equity hours and is uncorrected.
- The IV analysis is a failure (F = 2.8) and is reported as such; this is good practice. But Sec. 4.2 calls the posts "a strong two-hour instrument for oil (first-stage p < 0.001)". The exclusion restriction is violated by design (the posts carry war-risk information, as ANALYSIS_PLAN_IV.md concedes: "the estimate is an upper bound"). The label "instrument" should be dropped.

**Remedy.** Report a single multivariate test (for example, a joint test across assets using the permutation distribution of the sum or the maximum t) for the cross-asset claim, and cluster by day.

### M10. The arrivals section is not connected to the tests, and describes a class the authors say is mislabelled

- Sec. 4.1 describes the 108 "S1" posts, defined as Iran plus a threat term. Sec. 3.3 says this very class "contained the principal de-escalation posts". The arrival process of a mislabelled class is not an arrival process of threats.
- "Conditionally Poisson" rests on a Pearson dispersion of 0.89 with 32 weekly fixed effects on 227 daily observations. That test has little power against clustering inside a week. The ACF in results_poisson.json shows lag-1 and lag-2 autocorrelation of 0.39 and 0.23, and the authors report that a signal day is followed by 0.83 signals the next day versus 0.31 after a quiet day. This is within-week dependence. Weekly fixed effects can absorb it, but they cannot separate a changing rate from a self-exciting process, so "arise from changes in intensity rather than from clustering within a week" is not identified. A Hawkes alternative is the natural comparator.
- The paper's implication that "timing of posts is informative about the environment and is therefore not an exogenous source of variation" (Sec. 5.2) is asserted, not tested. A test would be a Granger-type regression of post intensity on lagged oil returns and news flow.

**Remedies.** Fit a Hawkes versus a time-varying-rate Poisson and report a likelihood or information-criterion comparison on the same 108 posts. Use the refined (blind-coded) DEESC and ESC classes for arrivals. Regress daily DEESC/ESC post counts on lagged oil, S&P and volatility changes to show how timing is endogenous.

### M11. Interpretive analysis: sampling, unit and strength of claims

- The 20 cases were selected by outcome size (8 largest, 6 opposite, 6 flat), and the coders were AI models. The analysis says "Because the analysts were model instances, the interpretive findings are treated as hypothesis-generating". That is appropriate, but then Sec. 5.2 builds its main theoretical claim ("the unit of analysis ... should be the announcement of a decision in a state where a constraint binds") partly from this analysis.
- "At least four" of the eight largest reactions fit the "first public announcement" description (Sec. 4.4). That is the A class in triangulation.md. The other four are B or A/B, i.e. attributed to other events.
- triangulation.md states its own limits: "CNBC, CNN, Axios etc. could not be opened (403/429); quotations are approximate; ... limited source independence (Bloomberg via Rigzone)". It also notes that the wire sources report daily closes while the study uses hourly bars (C13: daily WTI +0.73% versus the hourly -1.4%). Daily and hourly attributions do not measure the same quantity.
- C12 is a re-post of the C02 content (14:29Z), yet it is among the 20 cases and the quantitative sample. The authors' cluster filter and the "original posts after removing pure re-posts" statement (Sec. 3.2) did not exclude it. How many of the 33 and 28 are near-duplicate or repeat statements is not reported.

**Remedy.** Move the interpretive material to a clearly labelled exploratory section with fewer claims, state the A/B/C classification rule and report a second coder's classification. Report how many quantitative events are duplicates of an earlier same-day statement and re-estimate without them.

---

## 3. Minor concerns

1. **Sample inconsistencies across files.** The null size for WTI is 3,084 in RESULTS.md, 3,160 in results_hf2.json, 3,164 in my reproduction and 3,244 in the pre-trend run. State which null is used where.
2. **Figure 2 caption.** It reports "escalation n = 27 with complete windows" while RESULTS_PRETREND.md reports 28 escalation posts with complete bars. The earlier PAPER_DRAFT.md caption says "coders' agreed labels" for n = 33, but the agreed-label de-escalation n is 30 (RESULTS_EXT.md). State the label set used in each figure and table.
3. **Directional sign convention.** Directional sign is imposed ex ante (oil up after escalation, down after de-escalation). For the Fed topic, easing posts are assumed to move Treasury futures up. If the assumed sign is wrong for an asset, the test is biased toward zero. Report unsigned results too.
4. **Standardization is inconsistent.** Hourly e_std uses the previous 300 hourly bars, daily uses the previous 20 trading days. Q1 pools the two. The hold-out numbers are in standard-deviation units, the headline is not.
5. **The 5-minute analysis (nine oil posts) is not informative**, and the text says so. Remove it from "robustness" or present only as a feasibility note.
6. **The title and abstract promise more than the evidence.** "Limits of general theory" implies tested general theories. The theories are post-hoc and partly built on the same data (M2).
7. **Terminology.** "Natural setting" (abstract) and "natural experiment" language should be avoided. The regime is not exogenous.
8. **Poisson-Gamma versus Cox process wording.** Sec. 4.1 says "Poisson process with a time-varying rate" and "resembles a Cox process". A Poisson-Gamma mixture (negative binomial) is a specific Cox process. Be consistent and cite the actual model fitted.
9. **"73% of posts followed by a decline"** (24 of 33) is a meaningful statistic but needs its test (binomial p = 0.014).
10. **Reference verification.** The manuscript admits that references have not been checked. Check Bollen et al. 2011 (the journal field and relevance), Sims 2003, Barber and Odean 2008 against the claims made for them. The Gürkaynak et al. attribution is fine.
11. **Declarations.** The generative-AI statement is a placeholder. LLM coding, drafting, analysis and triangulation (agents collected the wire reports) were all performed by models. A full description of which steps were model-executed and what human oversight existed is required.
12. **Ethics/political sensitivity.** The paper studies a sitting head of state's speech and potential trading advantages. Sec. 5.3 says "we make no claim about any trading behavior" but then speaks of "informational advantage in the hours before secondary coverage". The latter is a claim. Remove it or support it.
13. **The war start date for the "binding constraint"** is 2 March (first trading day) in some analyses and 1 March in others (RESULTS_PAPER.md). Use one definition.
14. **The pre-war cell definition.** The H1 "pre" period starts 15 October 2024 and includes the period of the 2025 conflict, before the 2026 war. Check whether any Hormuz-related risk was priced then.
15. **Language and dates.** The qualitative result files are in Korean. If the repository is offered as a replication package, provide English versions.

---

## 4. Text-versus-result-file inconsistencies I verified

| # | Manuscript statement | File and number | Verdict |
|---|---|---|---|
| 1 | Sec. 4.2: the two events "account for most of it" | RESULTS.md, with the means: 33 x 1.29 = 42.6 summed points; the two events sum to 21.8, i.e. 51% | "Most" is overstated. Sec. 5.4's "about half" is correct. The two statements conflict. |
| 2 | Sec. 3.3: agreed-label rule "fixed before returns were examined"; "the primary analyses use the label on which both instances agree" | RESULTS.md headline n = 33 is coder 1's labelling (post_reactions_oil_coded.csv). Agreed-label rule first appears in THEORY_AND_PAPER_PLAN.md (mtime 04:31) after RESULTS.md (03:26). Agreed n = 30 (-1.45%) in RESULTS_EXT.md; n = 31 (1.40%) in results_paper.json | Not true for the headline. Three different n's for one concept. |
| 3 | Sec. 4.3: "H1 is therefore supported in the one cell with enough data" and Sec. 5.1 "evidence supports" | results_paper.json: p = 0.014, and RESULTS_PAPER.md: Holm-adjusted 0.056 | Fails the authors' own correction. Appendix A says "Partly supported". The text is stronger than the table. |
| 4 | Sec. 4.2: "Treasury futures rose 0.10% (Holm-adjusted p = 0.004), the dollar index fell 0.11% (p = 0.014), USD/CNH fell 0.04% (p = 0.02)" | RESULTS_HOLDOUT.md: Holm over the four assets within (topic, class, regime) | Numbers agree. The Holm family is much narrower than the set of tests, and S&P p = 0.006 in the same paragraph is uncorrected. |
| 5 | Sec. 4.1 describes 108 "threat" posts | Sec. 3.3 and ANALYSIS_PLAN.md Amendment 1: the S1/N class contains the main de-escalation posts | The arrivals section describes a class the authors say is not what it is called. |
| 6 | Sec. 4.2: "p < 0.001" for the 33 WTI events | results_hf2.json p_two = 0.0 (5,000 draws); my recomputation: sign test 24/33, p = 0.014; Wilcoxon p = 0.010; hour-matched standardized mean t = -2.3 | The mean-based permutation p is correct as computed but is the most favorable test given the null's excess kurtosis of about 13. |
| 7 | Sec. 4.2: "the abnormal directional reaction ... is 1.32% ... against a raw 1.29%" and "A pre-registered control" | results_pretrend.json: 1.3158 vs 1.2892; the plan file (mtime 06:27) shares its minute with the script and the results | The numbers agree. The control adjusts by 0.03 pp by construction. Pre-registration status is unverifiable and the motivation comes from Figure 2. |
| 8 | Sec. 4.3: H3 "MDE ... 0.82, more than three times the in-sample estimate" | results_oot.json: mde80 = 0.8157; in-sample 0.24 (RESULTS_HOLDOUT.md) | Agrees (ratio 3.4). |
| 9 | Sec. 4.2: pre-war posts "WTI -0.62% ... (n = 8, p = 0.008)" and coders alone "-0.30% and -0.28%, with n = 7 and 9" | RESULTS_EXT.md: -0.62 (p = 0.008), -0.30 (p = 0.16), -0.28 (p = 0.13) | Agrees. The text omits that the single-coder p-values are 0.16 and 0.13. |
| 10 | Sec. 4.2: Figure 2 "escalation n = 27" | RESULTS_PRETREND.md: 28 escalation, 33 de-escalation "with complete hourly bars" | Minor mismatch (27 versus 28). |
| 11 | Sec. 4.4: "seven were not mentioned in market coverage" | qual/triangulation.md "post covered in reports" column: six entries read "none" (C04, C09, C10, C11, C16, C19) and two read "indirect / almost none" (C06, C07) | Roughly consistent (six to eight). The counting rule is not stated. |
| 12 | Sec. 4.4: "at least four" of the eight largest fit the first-announcement pattern | qual/triangulation.md top-8: A for C01, C02, C05, C08 (four); B for C04, C06, C07; A/B for C03 | Correct, but the other half of the top-8 are attributed to other events, which the text does not say. |
| 13 | Abstract: "survives ... exclusion of the two largest events" | results_pretrend.json: excl. extremes 0.69% (CI 0.18, 1.22), p = 0.0041. Median -0.31 | The mean survives. The median is 0.31%, about a quarter of one null sd, and the effect halves. |
| 14 | Sec. 3.4 / ANALYSIS_PLAN.md: null bars "classified by whether they are within regular U.S. equity hours" | analysis_hf2.py: oil null is every non-post bar since 2 March (no hour-of-day classification) | The plan's specification was not implemented for oil. |
| 15 | WTI null size | RESULTS.md 3,084; results_hf2.json 3,160; pre-trend 3,244 | Three sizes for the same sample (different exclusions). Not explained. |

---

## 5. Recommendation: major revision (borderline reject in the current form)

**Rationale.**
- The central empirical object is a discovery-sample result from one war regime with 33 events, two of which supply half the mean. It was defined after the authors saw returns, and it is positioned as a protected, pre-registered finding. It is not.
- Identification of "post to price" is not achieved. The authors' own qualitative evidence and the pre- and post-bar decomposition above point to a large role for simultaneous news. The momentum control does not address that.
- The theory contribution is negative, and the negative tests are largely underpowered or off-target. "Rejected" and "limits of general theory" overstate what the data can say.
- The measurement contribution (LLM coders) lacks the human validation that would make it one. The reported agreement is partly selection, and the headline does not use the agreed labels the manuscript says are primary.
- The writing is candid about many limitations, which I credit. The authors disclose failures, publish power calculations and report the minimum detectable effects. These are real strengths and make a revision feasible.

**What would change my view (all feasible on existing data, plus the prospective sample).**
1. Re-label the paper honestly as exploratory for the headline effect and confirmatory only where that is true (M2).
2. The bar-level decomposition, timing placebo and OTHER-post placebo, and the independent-news stratification (M1).
3. Block-robust inference by week, signed-rank and trimmed means, hour-of-day and volatility standardization, and the H1 contrast in standardized units for Iran-only pre-war posts (M4, M5).
4. A direct test of the asymmetry with MDEs and multi-horizon CARs (M8).
5. A full specification curve and a forking-path table with a family-wide adjusted p (M3).
6. Confusion matrices, results on coder-disagreement posts, a redacted-text recoding and human validation (M6).
7. Equivalence tests for every null and removal of "rejected" (M7).
8. A frozen, externally time-stamped prospective test of the headline on posts after 14 October 2026.

If the headline holds under items 2 to 4 and 8, the paper becomes a defensible empirical note about one event class in one regime. As an MISQ paper it would still need a clearer theoretical contribution than "general theories were not confirmed".
