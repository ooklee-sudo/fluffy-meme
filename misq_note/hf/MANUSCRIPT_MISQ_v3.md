# Human Validation Reverses the Headline: Presidential Posts and Oil Prices in the 2026 Hormuz Closure

Ook Lee  
Department of Information System, Hanyang University, Seoul, Korea  
ooklee@hanyang.ac.kr (corresponding author)

*Manuscript prepared for submission to MIS Quarterly (version 3). Bracketed items are placeholders to be completed before submission. Analyses carry a status (confirmatory, amended, exploratory) given in Table 5 and Appendix A; the plans are files in the authors' repository, not entries in an independent registry.*

---

## Abstract

Heads of state announce policy on social platforms, and researchers increasingly label such posts with large language models. We ask whether that labelling changes what an event study finds, using 4,838 posts from the U.S. president's platform (March–October 2026) and the closure of the Strait of Hormuz. Posting is overdispersed and follows volatile hours, so posting times are not exogenous. A first analysis with model-coded labels showed oil falling 1.29% (median 0.31%) over two hours after de-escalation posts and no response to escalation posts. Two humans then labelled all 191 war-period keyword posts (agreement κ = 0.51, 0.69, 0.61 across three rounds), and the model agreed with them only at κ = 0.50; only 36% of its escalation labels were escalation. On human labels, WTI tick data show a directional move of +1.05% within 30 minutes after de-escalation posts (n = 29, median 0.47%) and +0.48% after escalation posts (n = 16), both larger than at matched placebo times, so "no response to escalation" was a labelling artifact. The move is preceded by drift in the hour before the post; over 5 to 15 minutes the post-period move is distinguishable from it, over an hour it is not. An information-theoretic account that motivated the study is not supported in its pre-registered tests. The case shows how a model-labelling workflow without human validation can produce a false headline.

**Keywords:** social media, executive communication, event study, large language models as coders, measurement validity, financial markets

---

## 1. Introduction

On the evening of 7 April 2026 a post on the president's platform announced a conditional two-week ceasefire with Iran, contingent on the reopening of the Strait of Hormuz. Oil, which had risen from about $67 to $114.6 per barrel since the first U.S. trading day of the war, fell by 12% within hours. Two weeks earlier, on 23 March, a post announcing a five-day postponement of strikes had been followed by a fall of 9.8%. Between those dates, and many times since, other posts threatened strikes, restated demands, or linked to commentary, and the market often barely moved. Whether and how platform posts relate to prices is therefore an empirical question that depends on which posts are counted as what.

Research on social media and markets has mostly asked whether platform content predicts prices (Bollen et al. 2011; Chen et al. 2014; for the news-media precursor, Tetlock 2007) and, from the firm's side, how dissemination through Twitter affects market liquidity (Blankespoor et al. 2014). The closest work on presidential communication studies tweets and firm values or intraday reactions (Born et al. 2017; Ge et al. 2019). Explanations typically invoke attention (Barber and Odean 2008), rational inattention (Sims 2003), or the distinction between words and actions in central-bank communication (Gürkaynak et al. 2005). Most such studies classify text automatically, and increasingly with large language models, and take the labels as given. Agreement between two runs of a model measures its consistency and says nothing about validity; whether the labels agree with human readers is rarely reported alongside the event-study result.

We use the Hormuz closure to study that gap. The setting is favorable because one physical state (strait open or closed) dominated the news for months, because the president posted frequently about it, and because oil was priced continuously. We make four contributions. First, we document that posting is overdispersed and follows volatile hours, so event studies that treat posting times as random are fragile. Second, we show that a model-labelled analysis gave a one-sided answer (a response to de-escalation, none to escalation) that human labelling reverses: on human labels both classes are followed by a directional move in oil, larger than at matched placebo times, and the model's escalation label was correct for only about one post in three. Third, we report which part of the human-label result is robust (the direction of the post-period move, in every variant we tried) and which is not (its separation from pre-post drift beyond short windows). Fourth, we report a test of an information-theoretic account of why posts matter that motivated the study; its pre-registered propositions are not supported, and we say so. The paper does not identify a causal effect of posts on prices.

Section 2 states the account and its propositions. Section 3 describes the data and design. Section 4 reports results. Section 5 discusses contributions and limits. Exploratory and model-labelled analyses are in the appendices.

## 2. An Information-Theoretic Motivation

When the author of a message is also the decision-maker, the message may be the decision's first public form (Austin 1962; Searle 1969). A platform lowers the cost of producing messages and removes intermediaries that would filter or confirm them, so receivers must infer the channel's reliability (Crawford and Sobel 1982; Kamenica and Gentzkow 2011). Information theory offers a vocabulary for this (Shannon 1948; Cover and Thomas 2006). Let S be a state the market cares about (here, whether Hormuz transit is open), with prior π and entropy H(π). A message that changes the belief to π′ conveys KL(π′ ‖ π) (Kullback and Leibler 1951). Three implications follow in expectation. A message that is unlikely under π, and not a repeat of earlier messages, should produce a larger update (surprisal and redundancy). The update should be larger when H(π) is larger (prior uncertainty). And reliability should scale the update. These are statements about the *size* of a reaction, not its sign.

We treat this as a motivation and test four propositions with pre-registered operationalizations:

P1 (surprisal): |reaction| increases in the novelty of the post relative to the poster's recent posts.
P2 (prior uncertainty): |reaction| increases in the market's prior uncertainty.
P3 (interaction): the effect of novelty is larger when prior uncertainty is higher.
P4 (information transfer): the mutual information between post class and the direction of the subsequent price move is positive when prior uncertainty about the relevant state is high and close to zero otherwise.

Three further propositions (P5, redundancy; P6, state-dependent sign; P7, timing surprisal) are examined in Appendix E. The proxies are crude. Prior uncertainty is relative volatility, not the entropy of beliefs about the strait; novelty is a lexical measure computed on the poster's own recent text, not on the market's information set. We therefore treat failures as failures of these tests, not of the vocabulary, and we do not claim that the account organizes the evidence.

## 3. Data and Design

### 3.1 Setting and data

The war that began on Saturday 28 February 2026 provides a topic on which the president posted frequently, a physical constraint (the strait was effectively closed from early March), and a commodity market in which the constraint was priced continuously. The first U.S. trading day was 2 March. WTI rose from about $67 to $114.6 by 7 April and was near $96 at the end of the sample.

*Posts.* We use the CNN-maintained archive of the president's posts. Between 1 March and 13 October 2026 there are 4,838 original posts after removing pure re-posts; 373 mention Iran, and 108 mention Iran with a threat term. A keyword-selected set of 191 war-period posts is the frame for classification. *Markets.* Hourly bars for WTI and Brent, E-mini S&P 500 and ten-year Treasury futures, the dollar index, USD/CNH, USD/KRW, gold and several equities cover October 2024 to October 2026. For timing we use tick quotes (mid price and bid–ask spread) for a WTI crude CFD from Dukascopy, 2017–2026 (hourly returns correlate 0.999 with the futures series). A price at time t is the mid of the last tick before t, accepted only if that tick is no more than ten minutes old; all windows used in the tick results have a tick no more than two minutes old.

### 3.2 Classifying posts

*Model labels.* Each post was classified by two independent runs of a large language model that received only the post text, for direction (escalation, de-escalation, mixed, other). The two runs are copies of one model; their agreement (κ = 0.74 on the human-validation sample, 0.62–0.96 elsewhere) measures consistency. The headline analysis of the first stage (Section 4.2) uses the first run's labels.

*Human labels.* Two human coders labelled the posts independently from the text alone in three rounds (Section 4.3), and agreement is reported as Cohen's (1960) kappa. Disagreements were adjudicated from the text by the principal investigator, who knew the research question; 23.6% of the final labels are adjudicated. We use the consensus-only subsample as a robustness check (Section 4.4). [Describe the coders here: number, background and expertise, instructions, and whether they saw market data — to be completed by the author.] All knew the war and may remember how its events unfolded.

### 3.3 Outcomes

The hourly outcome is the log change from the open of the bar containing the post to the close of the next bar (two hours), signed so that positive values are in the direction the post implies. The tick outcome is the directional log return from the last tick before the post to 5, 15, 30 or 60 minutes after, and the same window before the post for comparison; the 30-minute window is primary. A post is dropped if another of the 191 posts occurred in the previous three hours (cluster filter), or if the market was not open (no tick within ten minutes) at the post time or 30 minutes later. The magnitude outcome used for the propositions is |z|, the absolute return divided by the volatility of the preceding 300 bars (hourly) or of the preceding 60 daily returns scaled to the window (tick-level samples).

### 3.4 Measures of information

*Novelty* N_c is a conditional compression ratio: the compressed length of the post appended to the account's last 30,000 characters of posts from the preceding seven days, minus the compressed length of that context, divided by the compressed length of the post alone. A TF-IDF measure (one minus the maximum cosine similarity to any post in the previous seven days) is a robustness check. *Prior uncertainty* U is the log ratio of the standard deviation of the previous 24 one-bar returns to that of the previous 300 in the post's primary asset. *Mutual information* is estimated between post class (de-escalation, escalation, none) and the sign of the two-hour return over all war-period bars, with a permutation null. U shares the long-run volatility denominator with |z|, so a positive coefficient is also what volatility persistence predicts; we return to this in Section 4.5.

### 3.5 Status of analyses

Each analysis had a written plan committed to the repository before estimation, and plans state what had already been seen. The repository is not an independent registry, many plans were written after related results were seen, several were amended after a first result, and commit dates cluster on 13–14 October 2026. We follow the argument for pre-registration in observational work with many analytic choices (Nosek et al. 2018), but use the plans as a transparency device and classify every reported result as confirmatory (plan preceded the relevant outcome and was not amended), amended, exploratory or post hoc (Table 5). Holm's (1979) sequential procedure is applied within families defined in the plans (Appendix A); other p-values are unadjusted and reported as such. The human-label headline was not the original plan: a first pass with keyword classes, and then model labels, proved misleading, and the primary sample was redefined three times (33 model-labelled posts; 25 posts after round 2; 29 and 16 posts after round 3), each time after label quality or outcomes were known.

## 4. Results

### 4.1 Posting is overdispersed and follows volatile hours

For the 108 posts that mention Iran with a threat term, daily counts have mean 0.48 and variance 0.74; the Pearson dispersion statistic is 350 on 226 degrees of freedom (p < 0.001), and a negative binomial (Cameron and Trivedi 2013) with size 0.79 fits much better than a Poisson (LR p = 3 × 10⁻⁶). Inter-arrival times are bursty (mean 51 hours, median 21, coefficient of variation 1.94; exponential: 1). The overdispersion is not an artifact of the keyword class: de-escalation posts (57 in the war period) have a dispersion statistic of 367 and escalation posts (60) 430 (all p < 10⁻⁸). Posting is also not independent of market conditions. In an hourly logit over 3,605 war-period bars, the absolute prior six-hour oil return predicts a de-escalation post (coefficient 0.115, p = 0.033) and an escalation post (0.144, p = 0.024); the signed prior return does not (p = 0.32 and 0.18). Posts follow volatile hours, so posting times cannot be treated as random for identification. A homogeneous Poisson process is rejected in every series we examined, including 2017–2021 Twitter and a second account, and daily conflict events remove at most a quarter of the dispersion (Appendix D).

![Figure 1](figs/fig1_arrivals.png)

*Figure 1. Iran-related posts with threat terms (n = 108). A: observed daily counts versus Poisson and negative binomial fits. B: weekly counts.*

### 4.2 First stage: model labels

With the first model run's labels, WTI fell by 1.29% in the two hours after a de-escalation post (n = 33; median 0.31%; 24 of 33 declines; sign test p = 0.007; Wilcoxon p = 0.005; week-block bootstrap 95% CI 0.43 to 2.27, 16 weeks). Two events (23 March, −9.8%; 7 April, −12.0%) account for half of the summed move; without them the mean is 0.67% and the median 0.30%. Brent fell by 1.21% and USD/KRW by 0.14%; after the same posts Treasury futures rose 0.10% (Holm-adjusted p = 0.004), the dollar index fell 0.11% (p = 0.014) and USD/CNH fell 0.04% (p = 0.02). These responses are measured on the same events and share a common oil and geopolitical factor; they are one finding in several assets. Posts labelled escalation by the model (n = 28) showed no response (WTI −0.02%; week-block CI −0.58 to 0.35), and the difference between the two classes was 1.31 points (permutation p = 0.011; rank-based p = 0.051).

![Figure 2](figs/fig2_event_time.png)

*Figure 2. WTI path around war-period posts: de-escalation n = 33; escalation n = 27 with complete windows. A: mean ± 1 SE. B: median.*

At hourly resolution the post cannot be separated from what came before it. The return in the hour before the post bar is already +0.36% in the direction of the post (p = 0.10), and the first full hour after it adds +0.34% (p = 0.18, the revised primary statistic, not supported); the paired difference is −0.02%. Of 20 cases examined against contemporaneous market-wire coverage, all show other reported drivers. We therefore describe the finding as co-movement. Whether the model's asymmetry between classes was real depended on the validity of its labels, which we then tested.

### 4.3 Human validation of the labels

In round 1, two human coders labelled 150 posts (67 from the war period, 23 pre-war Iran posts, 60 other oil-related posts). They agree at κ = 0.51; against the 97 posts on which both humans agree, the two model runs reach κ = 0.43 and 0.56 (moderate by our prior criteria), while agreeing with each other at κ = 0.74. The dominant error is a model de-escalation label where humans see an unrelated post (de-escalation precision about 0.52 and 0.54; recall 0.77 and 0.88). In round 2, the coders labelled all 61 war-period signal posts with a clarified codebook (demands and ultimatums without an announced pause are escalation; de-escalation requires an announced pause, agreement, progress or reopening): humans agree at κ = 0.69, 13 disagreements were adjudicated, and the first model run agrees with the final labels at κ = 0.29. Its de-escalation label is right for 21 of 33 posts (precision 0.64), and its escalation label is right for 10 of 28 (precision 0.36). In round 3, the remaining 130 war-period keyword posts were labelled (humans κ = 0.61 on 129 posts with two labels). Across all 191 posts the final human labels are 79 other, 46 de-escalation, 41 escalation and 25 mixed; the model agrees with them at κ = 0.50, and of 71 posts that the model called other or mixed, 14 (20%) are escalation or de-escalation for humans, so the model also misses signals.

| Round | Posts | Human–human κ | Model run 1 vs humans κ | Model de-escalation / escalation precision |
|---|---|---|---|---|
| 1 | 150 | 0.51 | 0.43 (consensus, 97 posts) | 0.52 / not reported |
| 2 | 61 | 0.69 | 0.29 | 0.64 / 0.36 |
| 3 | 130 | 0.61 | 0.55 | not computed |
| All war-period | 191 | 0.67 (190 with two labels) | 0.50 | — |

*Table 1. Agreement between human coders and between model and humans. Model run 2 reaches 0.56 in round 1.*

The labelling is noisy in a way that the high agreement between model runs conceals. Because the effects we study are small relative to the noise in oil returns, label noise is first-order.

### 4.4 Human-labelled posts and tick-level results

We rebuilt the signal set from the human labels over all 191 posts (cluster filter; market open at the post and 30 minutes later). The reconciliation is in Table 2.

| Step | De-escalation | Escalation |
|---|---|---|
| Posts with a human signal label after the three-hour filter (141 of 191 pass) | 37 | 31 |
| With a tick window at the post time and +30 minutes (primary sample) | 29 | 16 |
| Also with a valid −60 minute price (placebo sample) | 26 | 14 |
| Signal posts dropped for no window | 8 | 15 |

*Table 2. Sample reconciliation (human labels). 83% of the 23 signal posts without a window were made on weekends or with the market closed, against 29% of all signal posts: the result does not extend to weekend announcements.*

For de-escalation posts the directional WTI return is +0.67% at five minutes and +1.05% at 30 minutes (n = 29; median 0.47%; one-sided Wilcoxon p = 0.0002; week-block 95% CI 0.42 to 1.79). For escalation posts it is +0.48% at 30 minutes (n = 16; median 0.40%; p = 0.0065; CI 0.10 to 0.84), against +0.17% (p = 0.26) when the model's escalation label is used. The difference between the two directions is not distinguishable from zero (Mann–Whitney p = 0.20, exploratory). The "no response to escalation" of Section 4.2 therefore applied to the model's escalation label, not to escalation as humans see it. Quote quality does not explain the result: the median bid–ask spread is 0.05 on a price near 89.6, and the median absolute 30-minute move (0.46) is about nine spreads.

*Placebo.* To check that the co-movement is not an artefact of the hours in which posts fall, we drew fake post times in the same clock hour on neighbouring days (same weekday status, at least two hours from any labelled post; 10,000 draws; 26 de-escalation and 14 escalation posts). The mean directional 30-minute return after the post is +0.62% for de-escalation and +0.53% for escalation, against placebo means of +0.05% and 95th percentiles of 0.22% and 0.26% (shares of draws at least as large below 0.0001 and 0.0003).

*Pre-post drift.* The 30 minutes before the post also exceed the placebo for de-escalation (+0.57%; +0.86% over the preceding hour; both below 0.0001) and, on the 30-minute window only, for escalation (+0.29%, p = 0.016); tick counts in the half hour before a de-escalation post are 28% above comparable hours. We describe this as drift larger than in comparable hours whose cause is not identified: the market may be reacting to news that the post then repeats, or the same event may move both. It does not show leakage or any party's conduct. Whether the outside source reported a decision before the post makes no difference to the drift (30 events, p = 0.90; Appendix E).

*Robustness.* Table 3 varies one feature at a time. The direction of the post-period move is positive and one-sided significant in every variant for both classes, including when the events on 23 March and 7 April are dropped (de-escalation mean 0.80%, median 0.48%) and when only posts on which both coders already agreed are used. The median is stable at 0.4 to 0.5%; the mean is pulled by a few events (the three largest de-escalation events, 2.7%, 3.3% and 10.5%, make up 54% of the summed move; leave-one-event-out means range from 0.71 to 1.12). The excess of the 30 minutes after a post over the 30 minutes before is borderline (de-escalation p between 0.026 and 0.063 across cluster rules; escalation 0.044 to 0.097) and depends on the window: over 5 and 15 minutes the post move is not preceded by drift (pre-window means −0.05% and 0.00%; paired excess +0.72 and +0.76 points, p = 0.003 and 0.005), whereas over 60 minutes the earlier drift has caught up (paired −0.15, p = 0.37). The statement we can defend is the short-window one.

| Variant | De-escalation: n, post-30 mean (median), paired post − pre (p) | Escalation: n, post-30 mean (median), paired post − pre (p) |
|---|---|---|
| Baseline (3-hour filter) | 29, 1.05 (0.47), +0.48 (.030) | 16, 0.48 (0.40), +0.26 (.058) |
| No cluster filter | 34, 0.91 (0.46), +0.44 (.026) | 19, 0.46 (0.35), +0.23 (.071) |
| 6-hour filter | 25, 1.08 (0.49), +0.42 (.063) | 14, 0.54 (0.50), +0.27 (.097) |
| Both coders agreed before adjudication | 28, 1.03 (0.47), +0.44 (.045) | 7, 0.71 (0.54), +0.44 (.078) |
| Window 5 minutes | 29, 0.67 (0.21), +0.72 (.003) | 16, 0.46 (0.19), +0.38 (.096) |
| Window 15 minutes | 29, 0.76 (0.60), +0.76 (.005) | 16, 0.57 (0.42), +0.36 (.019) |
| Window 60 minutes | 28, 1.18 (0.42), −0.15 (.365) | 16, 0.48 (0.40), +0.44 (.086) |
| Drop 23 March and 7 April | 26, 0.80 (0.48), +0.49 (.025) | 16, 0.48 (0.40), +0.26 (.058) |

*Table 3. Robustness of the human-label tick-level result (mean directional returns in percent; p from one-sided Wilcoxon tests of post > pre; variants are not independent and p-values are unadjusted).*

Other topics. Before the war, de-escalation posts about Iran show the same sign at about a quarter of the size, significant only for posts on which both coders agree (−0.62%, n = 8, p = 0.008); posts about monetary policy and non-tariff China matters show no hourly reaction, though the sample is too small to call this "no response".

### 4.5 Tests of the information-theoretic propositions

Table 4 reports the pre-registered tests on 271 hourly signal posts across four topics (oil 112, tariffs 74, Fed 47, China 38), with topic fixed effects and standard errors clustered by day; the outcome is |z|. These tests use model labels only to select posts, so they do not depend on the label of direction.

| Proposition | Estimate | One-sided p | Decision |
|---|---|---|---|
| P1 novelty N_c, 2026 sample | +0.77 (SE 0.56) | 0.084 | Not supported; same sign in all four topics |
| P1, 2022–24 daily (n = 49) | +0.26 (SE 0.37) | 0.24 | Same sign |
| P1, 2017–21 oil/Iran tweets (n = 191) | −0.27 (SE 0.74) | 0.64 | Not supported |
| P1, 2017–21 tariff tweets (n = 410) | −0.05 (SE 0.68) | Holm 0.74 | Not supported |
| P2 prior uncertainty U, 2026 | +0.29 (SE 0.20) | 0.072 | Not supported |
| P2, 2017–21 oil/Iran | +0.18 (SE 0.18) | 0.15 | Not supported |
| P2, 2017–21 tariff | +0.40 (SE 0.10) | < 0.001 | Supported; confounded with volatility clustering |
| P3 N_c × U, 2026 | −0.08 (SE 1.52) | 0.52 | Not supported |
| P3, 2017–21 oil/Iran; tariff | −0.37 (1.81); +0.32 (0.97) | 0.58; Holm 0.74 | Not supported |
| P4 mutual information, war | 0.0014 bits (null 0.0004) | 0.041 | Marginal; Holm over HI1–HI4 would give 0.16 |
| P4 mutual information, pre-war | 0.0003 bits (null 0.0002) | 0.28 | Not different from null |

*Table 4. Pre-registered information-theoretic tests (ANALYSIS_PLAN_INFO.md; ANALYSIS_PLAN_TWITTER.md; ANALYSIS_PLAN_TARIFF.md).*

The coefficients of novelty and prior uncertainty have the predicted sign in the 2026 sample and its replication, but none reaches p < 0.05, and the interaction is absent. In the two 2017–2021 samples novelty is negative or zero. With 271 posts the standard error of the novelty coefficient is 0.56 against an estimate of 0.77, so effects below about 1.5 in these units cannot be excluded. The only coefficient that clears its threshold, prior uncertainty in the tariff tweets, is the one that volatility persistence predicts without any account of information (Section 3.4), and it did not appear in the oil samples. The mutual-information result, at about one thousandth of a bit per hour-bar, is one of four tests of the information family in the plan (each fixed at α = .05 with no family adjustment); a Holm adjustment over the four would give 0.16, and the plan's test of a larger value in the war than before the war was not a formal contrast. We do not count it as support. We conclude that these pre-registered tests do not support the propositions.

### 4.6 Status of the reported results

| Result | Status |
|---|---|
| Posting overdispersed; follows volatile hours (4.1) | Confirmatory for dispersion; exploratory for the logit |
| Model-labelled hourly co-movement (4.2) | Amended (headline arose from an amendment); superseded by 4.4 |
| Human validation κ (4.3) | Descriptive; round-2 and round-3 plans written before labels returned |
| Tick-level human-label direction, 5 and 30 minutes (4.4) | Amended (primary sample redefined after round 2) |
| Post − pre excess at 30 minutes (4.4) | Amended; borderline in robustness |
| Placebo and pre-post drift (4.4) | Planned before placebo data were analysed; applied to human labels after the sample was fixed |
| Robustness variants (Table 3) | Planned before computation; unadjusted |
| P1–P3 (4.5) | Confirmatory (pre-registered; not supported) |
| P4 (4.5) | Confirmatory; marginal |
| Cross-asset responses (4.2) | Model-labelled; Holm within assets |
| Appendices D and E | Exploratory or model-labelled |

*Table 5. Status of results in the main text.*

## 5. Discussion

### 5.1 What the evidence supports

The evidence supports four statements. First, platform speech by a head of state arrives as an overdispersed, bursty process that follows volatile market hours, so event-study designs that treat posting times as random overstate their identification. Second, during the closure, oil moves in the direction of posts that humans label de-escalation (about +1.05% over 30 minutes; median 0.47%) and, at about half the size, of posts that humans label escalation (+0.48%); the direction of this move is robust to the choices we varied, it exceeds the move at matched placebo times, and, for de-escalation posts, over 5 and 15 minutes it is not preceded by drift. Third, over longer windows it cannot be separated from drift that precedes the post, so the evidence is of co-movement, not of an effect of the post. Fourth, the labels that gave the first-stage asymmetry were wrong in a way that reversed one of its conclusions: only 36% of the model's escalation labels were escalation in human judgment.

The information-theoretic propositions that we tested in advance do not hold: novelty, the interaction and timing surprisal (Appendix E) do not predict the size of the reaction in any sample, and prior uncertainty does so only where it is confounded with volatility clustering.

### 5.2 Contributions

The paper's main contribution is a worked example, with the full audit trail, of how model labelling can reverse an event-study headline. Agreement between two runs of a model was high (κ 0.62 to 0.96) throughout, but agreement with humans was moderate to weak (0.29 to 0.56), the model's escalation label was mostly wrong, and the first-stage conclusion that escalation posts do not move oil was an artifact. For IS research that uses language models as measurement instruments, the lesson is practical: report validity against human coders by class, not only inter-run consistency, before attaching market outcomes to the labels, and treat the labelling decisions as researcher degrees of freedom. A second contribution is descriptive: a documented case in which posting timing is endogenous, and in which oil moves with posts within minutes without us being able to say that the post is the news. A third is a record of negative results: the pre-registered propositions derived from an information-theoretic account were mostly not supported, and the two instances in which they appeared to be (mutual information; prior uncertainty in tariff tweets) do not survive scrutiny.

The paper does not offer a theory of platform-mediated speech. No platform feature varies in our data, and everything we find would be the same if the same statements had been issued by press release; what the platform changes is the volume of posts and the availability of timestamps, which is what makes the measurement possible.

### 5.3 Limitations

The identification is weak. Posts follow volatile hours, all 20 cases examined in market-wire coverage show other drivers, and the pre-post drift is as large as the post move over windows of 30 minutes and longer; the tick analysis separates them only at 5 to 15 minutes, on 29 and 16 events from one conflict, one sender and one asset (a CFD, not exchange futures). Two events supply a large part of the mean, and 83% of signal posts without a market window were made on weekends or off-hours, so the result does not extend to weekend announcements. The labels are not independent of the investigator: adjudication by the principal investigator is not blind to the hypotheses. The two human coders agree at κ = 0.51 to 0.69, which limits what any human-label result can claim, and the original coder instruments are model runs. The primary sample was redefined after seeing label quality and outcomes, and the pre-registration is a transparency device, not an independent registry. Prior uncertainty and novelty are proxies that are not the market's information set. The 2017–2021 samples and tariff results use model labels that humans accept for only about half of the model-agreed signals (Appendix E), and human labels for the oil sample were not collected. The arrival-process and event-explanation analyses in Appendix D were run after the main results were seen.

### 5.4 Future research

The most informative next steps are replication on other episodes with human-validated labels, exchange-futures data, and a continuous measure of the physical constraint (tanker transits, insurance spreads, term structure) as a measure of prior uncertainty. A comparison between accounts of people who use posts to influence others and matched ordinary accounts is specified (ANALYSIS_PLAN_ACCOUNTS.md) and has not been run because suitable data have not been established.

## 6. Conclusion

In the 2026 Hormuz closure, oil moved with posts that humans labelled de-escalation and escalation, within minutes, by more than at comparable hours, and the model-labelled analysis that suggested a one-sided response was wrong because the model's escalation label was mostly incorrect. The co-movement cannot be separated from earlier drift beyond short windows, and the information-theoretic propositions we pre-registered are not supported. We offer the case as an audited example of why model labels need human validation before they are attached to market outcomes.

---

## Declarations [to be completed]

*Use of generative AI.* Large language models were used as classification instruments in the study and for drafting and analysis support. The journal's disclosure requirements should be checked and the declaration completed accordingly [required].

*Data and code availability.* Code, analysis plans, coder outputs, and results are in the project repository; the post archive and market data come from public sources [add anonymous repository DOI for review].

## References

[On 14 October 2026 the journal articles, the Clauset chapter, the Leetaru and Schrodt paper and Richardson (1960) were checked against Crossref, publisher or library records. The textbooks (Austin, Cameron and Trivedi, Cover and Thomas, Searle) and Holm (1979) were not machine-checked and should be confirmed against the originals before submission.]

Austin, J. L. 1962. *How to Do Things with Words*. Oxford: Clarendon Press.

Barber, B. M., and Odean, T. 2008. "All That Glitters: The Effect of Attention and News on the Buying Behavior of Individual and Institutional Investors," *Review of Financial Studies* (21:2), pp. 785–818.

Blankespoor, E., Miller, G. S., and White, H. D. 2014. "The Role of Dissemination in Market Liquidity: Evidence from Firms' Use of Twitter," *The Accounting Review* (89:1), pp. 79–112, https://doi.org/10.2308/accr-50576.

Bollen, J., Mao, H., and Zeng, X. 2011. "Twitter Mood Predicts the Stock Market," *Journal of Computational Science* (2:1), pp. 1–8.

Born, J. A., Myers, D. H., and Clark, W. J. 2017. "Trump Tweets and the Efficient Market Hypothesis," *Algorithmic Finance* (6:3–4), pp. 103–109, https://doi.org/10.3233/AF-170211.

Cameron, A. C., and Trivedi, P. K. 2013. *Regression Analysis of Count Data* (2nd ed.). Cambridge: Cambridge University Press.

Chen, H., De, P., Hu, Y. J., and Hwang, B.-H. 2014. "Wisdom of Crowds: The Value of Stock Opinions Transmitted Through Social Media," *Review of Financial Studies* (27:5), pp. 1367–1403, https://doi.org/10.1093/rfs/hhu001.

Clauset, A. 2020. "On the Frequency and Severity of Interstate Wars," in *Lewis Fry Richardson: His Intellectual Legacy and Influence in the Social Sciences*, N. P. Gleditsch (ed.), Cham: Springer, pp. 113–127, https://doi.org/10.1007/978-3-030-31589-4_10.

Cohen, J. 1960. "A Coefficient of Agreement for Nominal Scales," *Educational and Psychological Measurement* (20:1), pp. 37–46.

Cover, T. M., and Thomas, J. A. 2006. *Elements of Information Theory* (2nd ed.). Hoboken, NJ: Wiley.

Crawford, V. P., and Sobel, J. 1982. "Strategic Information Transmission," *Econometrica* (50:6), pp. 1431–1451.

Ge, Q., Kurov, A., and Wolfe, M. H. 2019. "Do Investors Care About Presidential Company-Specific Tweets?," *Journal of Financial Research* (42:2), pp. 213–242, https://doi.org/10.1111/jfir.12177.

Gürkaynak, R. S., Sack, B., and Swanson, E. 2005. "Do Actions Speak Louder Than Words? The Response of Asset Prices to Monetary Policy Actions and Statements," *International Journal of Central Banking* (1:1), pp. 55–93.

Holm, S. 1979. "A Simple Sequentially Rejective Multiple Test Procedure," *Scandinavian Journal of Statistics* (6:2), pp. 65–70.

Houweling, H. W., and Kuné, J. B. 1984. "Do Outbreaks of War Follow a Poisson-Process?," *Journal of Conflict Resolution* (28:1), pp. 51–61, https://doi.org/10.1177/0022002784028001003.

Kamenica, E., and Gentzkow, M. 2011. "Bayesian Persuasion," *American Economic Review* (101:6), pp. 2590–2615.

Kullback, S., and Leibler, R. A. 1951. "On Information and Sufficiency," *Annals of Mathematical Statistics* (22:1), pp. 79–86.

Leetaru, K., and Schrodt, P. A. 2013. "GDELT: Global Data on Events, Location and Tone, 1979–2012," paper presented at the International Studies Association Annual Convention, San Francisco, April.

Lewis, E., Mohler, G., Brantingham, P. J., and Bertozzi, A. L. 2012. "Self-Exciting Point Process Models of Civilian Deaths in Iraq," *Security Journal* (25:3), pp. 244–264, https://doi.org/10.1057/sj.2011.21.

Nosek, B. A., Ebersole, C. R., DeHaven, A. C., and Mellor, D. T. 2018. "The Preregistration Revolution," *Proceedings of the National Academy of Sciences* (115:11), pp. 2600–2606.

Richardson, L. F. 1960. *Statistics of Deadly Quarrels*, Q. Wright and C. C. Lienau (eds.), Pittsburgh: Boxwood Press; Chicago: Quadrangle Books.

Searle, J. R. 1969. *Speech Acts: An Essay in the Philosophy of Language*. Cambridge: Cambridge University Press.

Shannon, C. E. 1948. "A Mathematical Theory of Communication," *Bell System Technical Journal* (27:3), pp. 379–423.

Sims, C. A. 2003. "Implications of Rational Inattention," *Journal of Monetary Economics* (50:3), pp. 665–690.

Tetlock, P. C. 2007. "Giving Content to Investor Sentiment: The Role of Media in the Stock Market," *Journal of Finance* (62:3), pp. 1139–1168.

## Appendix A. Analysis plans and outcomes

Plans are files in the authors' repository, dated 13–14 October 2026 in the commit history; the status of each result (confirmatory, amended, exploratory) is in Table 5.

| Block | Plan | Outcome |
|---|---|---|
| Arrivals | poisson_posts/ANALYSIS_PLAN.md | Overdispersed; conditionally Poisson |
| Weekly market tests | ANALYSIS_PLAN_MARKETS.md | Null |
| Intraday core | hf/ANALYSIS_PLAN.md (Amendment 1) | De-escalation co-movement; none for escalation (exploratory after amendment) |
| Instrumental variables | ANALYSIS_PLAN_IV.md | Weak first stage (F = 2.8) |
| Extension | ANALYSIS_PLAN_EXT.md | Coder-robust; partial pre-war replication; reversal for other oil posts |
| Binding constraint | THEORY_AND_PAPER_PLAN.md | Partly supported |
| Salience | THEORY_V2_SALIENCE.md | Rejected |
| Habituation | THEORY_V3_HABITUATION.md | Underpowered |
| Content analysis | ANALYSIS_PLAN_QUAL.md (Amendments 1–2) | Five themes; four propositions |
| Held-out tests of propositions | ANALYSIS_PLAN_QUAL_TESTS.md | Not supported |
| Pre-trend control | ANALYSIS_PLAN_PRETREND.md | Estimate unchanged; control uninformative |
| First source | ANALYSIS_PLAN_WIRE.md | Not supported (p = 0.176) |
| Tick-level timing | ANALYSIS_PLAN_5MIN.md | H5a, H5b supported for de-escalation posts |
| Matched-hour placebo (H5c) and anticipatory drift (H8) | ANALYSIS_PLAN_H5C_H8.md | H5c supported (de-escalation +0.62 vs placebo 95th pct 0.22; escalation +0.53 vs 0.26); H8a: pre-post drift also exceeds placebo for de-escalation (+0.57, +0.86) and partly for escalation; H8c: no difference by first source (p = 0.90); cause not identified |
| Twitter-era oil/Iran sample | twitter/ANALYSIS_PLAN_TWITTER.md (Amendment 1) | HI1–HI3 not supported (Holm p ≥ 0.45); H10 supported for escalation (p = 0.001), not for de-escalation |
| Twitter-era tariff/trade sample | twitter/ANALYSIS_PLAN_TARIFF.md (Amendment 1: P6/H12 state-dependent sign) | HI2 supported (Holm p < 0.001; volatility caveat); HI1, HI3 not supported; H10 supported (small); H12 not supported, opposite sign (β = −0.097) |
| Human validation, H7 (human-labelled sample) | ANALYSIS_PLAN_HUMAN.md (Amendments 1–2) | H7a, H7b supported for de-escalation (p = 0.0002, 0.030); escalation +0.48% (p = 0.007) |
| Human validation (round 2) | ANALYSIS_PLAN_HUMAN.md (Amendment 1) | Round 1 κ 0.43–0.56; round 2 (61 war-period posts, adjudicated) κ 0.29, H6a supported, H6c not supported |
| Revision analyses | ANALYSIS_PLAN_REVISION.md | Revised primary not supported; robust inference supports; posting follows volatility |
| Timing surprisal (P7) | arrivals/ANALYSIS_PLAN_TIMING.md | Not supported (pooled β = +0.04 SD, p = 0.27; n = 685) |
| Arrival models and Musk account | none (descriptive; arrivals/RESULTS_ARRIVALS_MODELS.md) | Poisson rejected; NB ≈ Poisson–lognormal; dynamic NB-INGARCH best in multi-year series |
| Event explanation of dispersion | arrivals/ANALYSIS_PLAN_EVENTS.md (exploratory) | Lagged GDELT conflict events significant in all six pairings but remove 9–25% of NB dispersion (never ≥ 50%); event series not Poisson; Calendar-week effects remove 66% (all Twitter) |
| LLM release arrival | arrivals/ANALYSIS_PLAN_LLM_RELEASES.md (exploratory) | Over-dispersed after trend (LR p = 0.0001); weekend share 4% vs 29% expected; geometric gaps rejected |
| LLM release stock reaction | arrivals/ANALYSIS_PLAN_LLM_STOCK.md (exploratory) | Direction not supported (+0.40 pp, p = 0.55); magnitude larger than random windows (p = 0.008; Holm 0.015); n = 31 |
| Matched-account comparison (HA1–HA2) | arrivals/ANALYSIS_PLAN_ACCOUNTS.md | Registered, not run; data availability not established |
| Information-theoretic hypotheses | ANALYSIS_PLAN_INFO.md | P1–P3 not supported (p = 0.08, 0.07, 0.52); P4 marginal (p = 0.041; Holm over HI1–HI4 would give 0.16) and not counted as support |
| Robustness of the human-label headline | hf/ANALYSIS_PLAN_ROBUST_HEADLINE.md | Direction robust in every variant; post − pre excess borderline and window-dependent (Table 3) |

## Appendix B. Coding protocol

[Summary of direction and type definitions, blind-coding instructions, the primary-label rule, reconciliation of content-analysis codebooks, the model and prompt provenance, and a reference to the repository files.]

## Appendix C. Human validation

Two human coders coded 150 posts independently from text only (war-period 67, pre-war Iran 23, other oil-geopolitics 60). Four-class kappa: human–human 0.51; model 1–model 2 0.74; human consensus (97 posts) with model 1 0.43 and with model 2 0.56 (three-class 0.48 and 0.59). De-escalation precision against the consensus is 0.52 (model 1) and 0.54 (model 2); recall 0.77 and 0.88. Of the 12 posts in the tick-level de-escalation sample that fall in the round-1 human sample, the human consensus is de-escalation for 3, escalation for 2, other for 1, and absent for 6. In round 2 (all 61 war-period signal posts, codebook v2, κ between humans 0.69, 13 disagreements adjudicated), the final human labels are 25 de-escalation, 11 escalation, 12 mixed, and 13 other; the model agrees at κ = 0.29. On the 25 human-labelled de-escalation posts the 30-minute directional return is +1.03% (p = 0.0015) and its excess over the preceding 30 minutes +0.35% (p = 0.082). Details are in RESULTS_HUMAN.md and RESULTS_HUMAN61.md.

## Appendix D. Exploratory analyses of arrival, events and other self-timed events

These analyses were run after the main results were seen. Their definitions were fixed in dated plans before the relevant data were downloaded or parsed (Appendix A), but none is confirmatory.

### D.1 Alternative arrival models and a second account

 Poisson is not the only candidate, and the negative binomial (a Poisson–Gamma mixture) is a particular one. Table D1 compares daily-count models by AIC for the Truth Social series, for the 2017–2021 Twitter series (all original tweets and the two topic subsets of Appendices E.4–E.5), and for Elon Musk's account as a second influential poster (a public third-party extract of 3,218 tweets, 2012–2017, whose completeness and time zone we could not verify). A homogeneous Poisson process is rejected everywhere (ΔAIC 150 to 3,700). The negative binomial and a Poisson–lognormal mixture fit equally well (differences within about 13 AIC units), so the data do not support choosing a gamma over a lognormal mixing distribution. In the multi-year Twitter series a dynamic model, a negative-binomial INGARCH(1,1) in which today's rate depends on yesterday's count and rate, is far better than every static mixture (ΔAIC 57 to 626); the 227-day Truth Social series is too short for this and the static negative binomial suffices. Waiting times follow no power law (Pareto is worst in every series); the best form is Weibull for all of Trump's tweets, gamma for the topic subsets, and lognormal for Truth Social and Musk (CV 1.7 to 2.5). Musk's account shows the same qualitative pattern as the president's. We read this as evidence that human posting is bursty and self-exciting, not as evidence that the pattern is specific to people whose words carry weight: we have no comparison with ordinary accounts. A pre-registered comparison with matched ordinary accounts is specified (ANALYSIS_PLAN_ACCOUNTS.md) but has not been run, because we have not established that data of sufficient quality exist.

| Series | Days | Static NB (ΔAIC) | Poisson–lognormal (ΔAIC) | NB-INGARCH (ΔAIC) | Best waiting-time model |
|---|---|---|---|---|---|
| Trump, Truth Social 2026 | 227 | 0 | 1 | 0 (collapses to NB) | Lognormal |
| Trump, Twitter, all original | 1,448 | 626 | 639 | 0 | Weibull |
| Trump, Twitter, oil/Iran | 1,448 | 57 | 62 | 0 | Gamma |
| Trump, Twitter, tariff/trade | 1,448 | 137 | 129 | 0 | Gamma |
| Musk, Twitter 2012–17 | 1,779 | 238 | 249 | 0 | Lognormal |
| Musk, Twitter 2016–17 | 638 | 59 | 66 | 0 | Lognormal |

*Table D1. Alternative models for the arrival of posts (ΔAIC relative to the best model in each row; Poisson ΔAIC 150 to 3,700 in all rows; descriptive, not pre-registered; RESULTS_ARRIVALS_MODELS.md).*

### D.2 Do external events explain the over-dispersion?

 If a head of state mostly reports external events and those events arrive as a Poisson process, posting would be over-dispersed only because each event spawns several posts. Richardson's classic result is that the onsets of separate interstate wars are roughly Poisson at an annual scale (Richardson 1960; Clauset 2020), although it has been questioned (Houweling and Kuné 1984), and within a war, violent events are usually modelled as self-exciting (Lewis et al. 2012); a single war that has already begun supplies no such onsets at the daily scale of our data. We therefore tested the idea directly, in an exploratory analysis whose definitions were fixed before the event counts were downloaded (ANALYSIS_PLAN_EVENTS.md). We counted GDELT conflict events per day (Iran-involved conflict events, world conflict, riots, and US–China conflict events; Leetaru and Schrodt 2013) and added the previous day's count and the average of the previous 2–7 days, together with total event volume, to a negative binomial model of daily posts. The event terms are statistically significant in all six pairings, but they remove only a small part of the dispersion: 9% (Truth Social, all posts), 11% (tariff tweets), 17–20% (all Twitter posts, with riot or world-conflict events) and about 22–25% (oil/Iran tweets; Truth Social Iran posts); in no pairing do they remove half. Calendar-week fixed effects, in contrast, remove 66% of the dispersion of all Twitter posts, so the over-dispersion mostly reflects a slowly moving rate that daily conflict counts do not capture. The event series are themselves far from Poisson (variance-to-mean ratios of about 550 and 900 for Iran-related conflict events, lag-1 autocorrelations of 0.85 and 0.96). The premise that the posts follow Poisson events fails at the daily scale. These counts reflect media coverage, which the posts also influence, so the tests do not identify causal direction, and block-bootstrap intervals rest on only 100 resamples.

### D.3 A probe beyond politics: other actors who time their own events

A head of state who announces a war and a company that releases a model both choose when the event happens. If the account generalizes, the arrival of such events should not be Poisson, and the market should react more strongly on event days. We probed both in an exploratory analysis registered before the data were parsed (ANALYSIS_PLAN_LLM_RELEASES.md; ANALYSIS_PLAN_LLM_STOCK.md). The source is Wikipedia's list of large language models (fetched on 14 October 2026; 187 rows with at least a month, 126 with a full date, nearly all from 2025–2026); it is crowd-edited and includes models by notability, so the tests are descriptive.

*Arrival.* Monthly release counts rise steeply over 2018–2026, and with a log-trend they remain over-dispersed (Pearson χ²/df 1.7; negative-binomial α = 0.25; likelihood-ratio p = 0.0001); in the shorter 2024–2026 window the evidence is weaker with a quadratic trend (α = 0.10; one-sided p = 0.028). Of 125 releases with a full date since 2023, 4% fell on a weekend, against 29% expected under a homogeneous process (χ² = 62.1, 6 df; Holm p < 10⁻¹⁰). Gaps between releases (119 gaps since 2024; coefficient of variation 1.55) are fitted best by a negative binomial; the memoryless geometric is worse by 22 AIC units. Individual developers release more regularly than a Poisson process (coefficients of variation 0.67 for Anthropic, 0.81 for OpenAI, 1.12 for Google DeepMind), so the clustering appears only after pooling. Release dates follow the business calendar, a clear departure from a Poisson process.

*Market reaction.* For the 31 releases by listed developers (Alphabet 9, Alibaba 8, Meta 4, Microsoft, Xiaomi and Tencent 3 each, Nvidia 1), the mean abnormal return over the release day and the next trading day, from a market model, is +0.40 percentage points (SE 0.68; Wilcoxon p = 0.76). The standardized absolute abnormal return is larger than in random two-day windows of the same firms (1.11 against 0.75; permutation p = 0.008; Holm p = 0.015). In other words, there is a magnitude effect without a direction. It shrinks by about 40% when three events likely to coincide with other news are removed (Gemini 2.0 on 5 February 2025, Qwen2.5 on 26–27 January 2025 and Llama 4 on 5–7 April 2025; the coincidences are our recollection, not checked here). Release times of day are not in the list, so daily windows were used; unlisted developers, about half of the 2025–2026 rows, are excluded by design; and a few firms contribute only 3–4 events each, with opposite signs across firms.

Taken together with the war-period results, the two settings agree on one point, that timing is chosen by the actor and arrival is not Poisson. They do not agree on the market reaction: with the matched-hour placebo (Section 4.4) the posts show a directional move beyond fake times in comparable hours, whereas releases show larger absolute moves without a direction. Because the two statistics differ, and because we have no comparison group of externally caused events, we do not claim that self-caused events are a common class with a common market signature.

## Appendix E. Supplementary analyses (model-labelled or exploratory)

The analyses in this appendix use model labels that humans accept for only about half of the model-agreed signals (Section 4.3; E.5), or were generated from the cases they describe, or were run after the main results were seen. They are not evidence for the information-theoretic account. In particular, the opposite signs of the oil responses in 2026 and 2017–2021 are an unvalidated observation: the 2017–2021 oil sample has model labels only, and the pre-registered test of the proposition that would have made sense of it (P6) was rejected in the opposite direction (E.5).

![Figure 3](figs/fig3_bar_decomposition.png)

*Figure 3. Directional WTI return by hour relative to the bar k containing the post, model-labelled de-escalation posts (mean ± 1 SE); the hour before the post bar already carries +0.36%.*

### E.1 Earlier pre-registered mechanisms

Three mechanisms were pre-registered before the information-theoretic account. *Binding constraint:* oil de-escalation posts moved WTI by a directional 1.40% during the war and 0.01% before it (p = 0.014; Holm-adjusted 0.056); the other three primary comparisons did not support the prediction (oil escalation p = 0.86; tariff escalation, opposite sign, p = 0.09; tariff relief, three pre-period posts). *Salience:* in hold-out topics the coefficient of log posts in the previous seven days is +0.045 (p = 0.44), and those topics show no hourly reaction at all. *Habituation:* −0.24 pooled in-sample (p = 0.036, exploratory); −0.09 (SE 0.29) in the pre-registered 2022–2024 test, whose minimum detectable effect (0.82) is more than three times the in-sample estimate, so the test can neither confirm nor refute it. The action-versus-rhetoric difference (a verifiability premium) was +0.56 points for oil (p = 0.12) and not significant pooled (p = 0.20). Under the information-theoretic account, habituation is the redundancy implication and the binding constraint the prior-uncertainty implication, but the evidence for each is no stronger when stated that way.

### E.2 Content analysis (hypothesis generation)

To generate hypotheses about which posts were consequential, 136 posts were shuffled, stripped of labels and market data, and coded by two model-instance analysts; codebooks were reconciled and fixed before reactions were attached; 20 cases (the eight largest reactions, six moves opposite to the post's direction, and six near-zero de-escalation posts) were compared with contemporaneous market-wire coverage collected without access to our reaction values. Because the analysts are model instances and the study involves no human interpreter, we describe this as LLM-assisted content analysis for hypothesis generation, not as interpretive or critical research.

The two analysts' codebooks mapped onto each other on all six themes of one analyst's list (some merged); post-level agreement on shared concepts ranged from kappa 0.37 (claims of agreement) and 0.42 (boasts) to 0.96 (amplification). Five themes were retained: pressure-then-pause cycles; concrete acts versus atmospheric statements; counterparty denial and partial retracement (after the 23 March postponement, the Iranian state denied that talks had occurred and oil rebounded the next session); posts that are themselves the first announcement of a decision (four of the eight largest reactions); and multi-causality (all 20 triangulated cases show other reported drivers; seven were not mentioned in market coverage). Two propositions derived from these themes were tested on held-out data and not supported: that re-posts and links produce no reaction while originals do (difference −0.13 standard deviations, CI −0.57 to +0.31, minimum detectable effect 0.75; in that sample original posts also showed almost no reaction), and that after-hours posts are better measured at the next open (−0.10 points, p = 0.63). The themes of counterparty denial and the carrying of decisions correspond to the channel-reliability and surprisal implications of the account, but they were generated from the same cases they describe and are not independent support.

### E.3 Timing surprisal (P7), first source and redundancy (P5)

*Timing surprisal (P7).* The account's second information channel is the time at which a post arrives. We computed, for each post, the surprisal of its waiting time under a lognormal predictive model fitted to the poster's own gaps in the preceding 60 days, separately by trading-session bucket (ANALYSIS_PLAN_TIMING.md, registered before the measure was computed). Pooled over the three tick-level samples, a one-SD increase in timing surprisal is associated with 0.04 SD higher |z| (SE 0.065; one-sided p = 0.27; n = 685), with N_c, U, the preceding 30-minute |z|, the prior-hour post count, session and sample controlled. The estimates are +0.08 in the tariff tweets, −0.02 in the oil tweets and −0.01 in the 2026 posts (Holm p ≥ 0.60); a count-based surprisal, winsorizing, a log outcome, dropping bursts and dropping weekends give the same answer. Timing surprisal is nearly uncorrelated with the volatility preceding the post (Spearman 0.05), so the null is not a control artifact. The confidence interval (about −0.09 to +0.17 SD) excludes a medium effect but not a small one. P7 is not supported.

*First source.* Because the account treats the platform as a possible first source of a decision, we classified all 61 war-period signal posts by whether an outside public source had reported the decision earlier (searchers saw only the post's time and text). Thirty-two were POST_FIRST, 14 OTHER_FIRST, 10 SIMULTANEOUS (six of them 6–9 minutes after the post), and five undeterminable; nine of the 14 OTHER_FIRST posts were links to articles or re-posts. The mean directional reaction was +0.73% for POST_FIRST and +0.04% for OTHER_FIRST (difference 0.70; permutation p = 0.176; not supported). "Post first" means that no earlier report was found by keyword-based search; several outlets could not be opened, and the classification should be read as an upper bound on how often the post was first.

The redundancy proposition (P5) was examined as the correlation between novelty and the number of same-topic posts in the previous 24 hours (−0.10, direction as expected, uninformative) and in the held-out re-post test of E.2. For the 30 events that overlap the first-source classification, the mean directional return in the 30 minutes before the post was +0.28% (POST_FIRST, n = 10), +0.66% (OTHER_FIRST, 9), +1.57% (SIMULTANEOUS, 6) and +0.30% (undeterminable, 5); POST_FIRST versus OTHER_FIRST p = 0.90, so the drift does not differ by who reported first.

### E.4 Twitter-era oil and Iran tweets (model labels)

To test the propositions on data not used to form them, we pre-registered (ANALYSIS_PLAN_TWITTER.md, written before any label, price or return was examined) a confirmatory analysis of the same author's original tweets from 20 January 2017 to 8 January 2021 that mention Iran, oil, OPEC, Saudi Arabia, or related energy terms (341 tweets; exact times from the tweet identifiers). Two independent model instances labelled direction (κ = 0.77). After the three-hour cluster filter, 278 tweets remained, and 191 had a tick window (market open 30 minutes before and after); 87, mostly weekend and overnight tweets, did not. The outcome is the 30-minute absolute return divided by a scale derived from the prior 60 daily volatilities, so the test of the three propositions does not depend on any label.

The propositions are not supported. The coefficient of novelty (conditional compression) on the standardized absolute reaction is −0.27 (SE 0.74; one-sided p = 0.64), that of prior uncertainty +0.18 (SE 0.18; p = 0.15), and that of their interaction −0.37 (SE 1.81; p = 0.58); the Holm-adjusted p-values are 1.00, 0.45, and 1.00. A lexical novelty measure registered as a robustness check is positive (+1.14, SE 0.44; p = 0.005), so the two measures of novelty disagree, and because the plan designated the compression measure as the test we do not read the lexical result as confirmation. The standard error of the novelty coefficient is large, so effects smaller than about 1.5 standardized units cannot be excluded.

The directional response differs from 2026 in sign. Among tweets that both model instances label escalation (n = 32), oil rose by 0.51% in the 30 minutes after the tweet (median +0.09%; one-sided Wilcoxon p = 0.001); the preceding 30 minutes show +0.04%, and the excess is +0.50 points (p = 0.010). Among tweets labelled de-escalation (n = 11) the response is +0.18% in the expected direction and not significant (p = 0.22), too few to conclude. With the strait closed in 2026 the pattern differed: de-escalation moved oil, and escalation did so when humans, not the model, labelled it. An information-theoretic account can accommodate this (a message is informative when it changes beliefs about the state to which the market assigns little probability: relief when closure is the prior, threat when peace is), but we had not pre-registered the sign flip, and we offer it as a post hoc reading. P6 turns it into a prediction that is tested on the tariff and trade tweets of the same period, with a plan registered before their returns were examined (ANALYSIS_PLAN_TARIFF.md, Amendment 1); human labels for the oil sample were not collected. Finally, the standardized reaction is larger in the 2026 posts (mean 1.39 against 0.84; exploratory permutation p = 0.002); the comparison is confounded with the war and cannot isolate the platform.

### E.5 Tariff and trade tweets (model labels; state-dependent sign)

The state-dependence reading of Appendix E.4 was formed after the oil results, so it could not be tested on them. For the tariff, trade, and China tweets of 2017–2021 (937 original tweets; 632 after the three-hour filter; 410 with a tick window of the S&P 500 index CFD; labels from two model instances, κ = 0.80, human labels for only 150 tweets) we registered the test before any price or return was examined (ANALYSIS_PLAN_TARIFF.md and its Amendment 1).

*Novelty, uncertainty, and their interaction.* Prior uncertainty is supported: the coefficient of U on the standardized absolute 30-minute reaction is +0.40 (SE 0.10; one-sided p < 0.001; Holm-adjusted 0.0001). Novelty (−0.05, SE 0.68; Holm-adjusted p = 0.74) and the interaction (+0.32, SE 0.97; 0.74) are not. The result for U needs a caveat that restricts its meaning: U is the log ratio of recent to long-run daily volatility and the outcome is scaled by long-run volatility, so the coefficient is what the persistence of volatility predicts without any account of information. It is consistent with our account but does not distinguish it from volatility clustering, and in the oil sample the same coefficient was not significant (p = 0.15).

*Direction.* Among tweets with an agreed label, the S&P 500 rose by 0.085% in the 30 minutes after de-escalation tweets (n = 70; one-sided Wilcoxon p = 0.0007) and fell by 0.046% after escalation tweets (n = 50; p = 0.024); the excess over the preceding 30 minutes is significant for escalation (p = 0.048) and not for de-escalation (p = 0.099). Both responses have the expected sign and are small in index terms.

*Human validation.* Two coders labelled 150 of these tweets (a stratified sample of model-agreed signals, model-disagreed candidates, and model-agreed other tweets; κ between the coders 0.54; 44 disagreements adjudicated from the text). The model labels agree with the final human labels only weakly (κ = 0.39 and 0.34): of the 60 tweets that both models call escalation or de-escalation, humans give the same label to 33 (55%), call 19 other, and reverse the sign of 8; the models almost never miss a signal (1 of 30 model-other tweets is a human signal). On the human labels the directional 30-minute S&P 500 return is −0.10% after de-escalation tweets (n = 20 with a window; one-sided p = 0.49) and +0.058% after escalation tweets (n = 30; p = 0.069; excess over the preceding 30 minutes +0.056, p = 0.026). The response to de-escalation seen with model labels is therefore not reproduced on the human-labelled subset, which is small and not random, and the escalation response is borderline.

*State-dependent sign.* A regime variable R, computed from labels alone as the balance of escalatory and de-escalatory trade tweets in the preceding 30 days, was used to test P6: a message that runs against the regime should move prices more than one that continues it (H12). Among 108 tweets with a defined regime the coefficient is −0.097 (SE 0.032; one-sided p = 0.9987; two-sided p = 0.003). The effect is in the opposite direction: messages that continued the recent regime moved the index more (mean directional returns of +0.119% for aligned and +0.045% for opposed de-escalation; +0.150% and −0.084% for escalation). The test on the human-labelled subset (46 tweets with a window and a regime) gives the same answer (β = −0.041, SE 0.079; one-sided p = 0.70). By the rule we fixed in advance, P6 is not supported and the sign flip in the oil samples remains a post hoc observation that carries no theoretical weight. A reader should therefore not take the opposite signs of the 2026 and 2017–2021 oil responses as evidence for the account. USD/CNH ticks for the China-related subset were not analysed.
