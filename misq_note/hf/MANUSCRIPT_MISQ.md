# When Does Executive Speech Move Markets? Platform-Mediated Announcements, Binding Constraints, and the Limits of General Theory

[Author names and affiliations — to be added]

*Manuscript prepared for submission to MIS Quarterly. Bracketed items are placeholders to be completed or verified before submission. All analyses are documented in the project repository with the pre-registration files cited in Appendix A.*

---

## Abstract

Heads of state now announce policy directly on social platforms, and market participants watch those feeds in real time. Whether such speech moves markets through a general channel, such as attention, repetition, or credibility, or only under particular conditions is not settled. We study this question using 4,838 original posts from the U.S. president's own platform (March–October 2026), hourly and five-minute futures data, and the 2026 closure of the Strait of Hormuz as a natural setting in which a physical constraint was binding. Post arrivals are overdispersed and bursty but conditionally Poisson, as expected of a Poisson–Gamma process with a time-varying rate. Posts that two independent model coders, working blind to market data, classified as de-escalation were followed by a 1.29% fall in WTI within two hours during the closure, together with movements in the dollar, the yuan, and Treasury futures; escalation posts showed no response, and neither did posts on monetary policy or non-tariff China matters. The result survives a momentum control and exclusion of the two largest events. We then tested three pre-registered general mechanisms (binding constraint, salience, habituation) out of sample. None is confirmed. An interpretive analysis of 136 posts, triangulated against 20 market-wire cases, generates propositions that are likewise not supported in held-out tests. We argue that platform-mediated executive speech is best understood as a conditional, announcement-carrying channel rather than a general attention shock, and we show how pre-registered mixed-methods design can make such a conclusion credible.

**Keywords:** social media, executive communication, event study, pre-registration, large language models as coders, financial markets, mixed methods

---

## 1. Introduction

On the evening of 7 April 2026, a post on the president's platform announced a conditional two-week ceasefire with Iran, contingent on the reopening of the Strait of Hormuz. Oil, which had risen from roughly $67 to $114.6 per barrel since the first U.S. trading day of the war, fell by double digits in the next session. Seven weeks earlier, and many times since, similar posts had threatened strikes, announced pauses, or restated demands, and the market had often barely moved. The episode illustrates a puzzle that has become central to research on platform-mediated information: the same channel, and often the same author, produces messages that are sometimes consequential and sometimes ignored.

Information systems research has long treated social platforms as sources of market-relevant information (Bollen et al. 2011; Tetlock 2007 for the news-media precursor). Two literatures give partial answers to the puzzle. The first treats market reactions to communication as a function of attention and salience: posts matter more when they are noticed, and less when repeated (Sims 2003; Barber and Odean 2008). The second, from central-bank communication, distinguishes words from actions and asks when statements move prices at all (Gürkaynak et al. 2005). Neither has been tested systematically for the posts of a head of state, and neither tells us whether the effect is a property of the speaker, the topic, the text, or the state of the world at the time.

This paper makes three contributions. The first is descriptive: we characterize how such posts arrive. The arrivals follow a Poisson–Gamma structure, with strong overdispersion in daily counts that disappears once the weekly rate is allowed to vary. This matters because event-study designs often assume that posting times are exogenous, and the burstiness we document is a warning against that assumption. The second is empirical: during the physical closure of Hormuz, de-escalation posts, and only those, were followed by large, fast price changes in oil and in assets linked to it, while posts on Federal Reserve policy and non-tariff China matters were followed by none. The third concerns inference. We pre-registered three general mechanisms and tested them out of sample, and none was confirmed. We report that outcome as a finding, because it constrains the theories that can reasonably be built on this setting, and we document the design that makes the negative results interpretable.

We do not claim that posts cause price changes in general, that tariff or monetary-policy posts move markets, or that any of our three mechanisms operates. The evidence supports a narrower statement: when a physical constraint is binding and a post announces a decision that relaxes it, prices of the constrained commodity respond within hours.

The remainder of the paper proceeds as follows. Section 2 develops the conceptual background and the hypotheses. Section 3 describes the setting, data, and design. Section 4 reports results. Section 5 discusses contributions, implications, and limitations. Section 6 concludes.

## 2. Theoretical Background

### 2.1 Platform-mediated executive communication

When the author of a message is also the decision-maker, the message is not about a policy; in many cases it is the policy's first public form. This distinguishes executive announcements from commentary, forecasts, or sentiment, which are the objects of most social-media-and-markets research. In the language of speech-act theory, an announcement that a strike is postponed is closer to a declarative act, one that changes the state of the world by being uttered by someone with the authority to do so, than to an assertion about the world (Austin 1962; Searle 1969). A threat is a directive or commissive act whose force depends on whether the speaker can and will carry it out. Habermas's (1984) distinction among validity claims (truth, sincerity, and normative rightness) suggests that audiences evaluate each message on dimensions that differ in how quickly they can be checked.

A platform adds two features. It lowers the cost of producing messages, which in turn raises their number, and it removes intermediaries that would otherwise filter, summarize, or confirm. Both features bear on how markets should respond. If announcements are cheap and frequent, the information content of any single message falls; if the platform is also the first and sometimes only channel for real decisions, markets cannot ignore it.

### 2.2 Three general mechanisms

We derived three candidate mechanisms from this background and pre-registered each before testing it.

*Binding constraint (H1).* A post moves a market more when it changes expectations about a binding physical or legal constraint on the market in question. In our setting the constraint is Hormuz transit for oil and the tariff schedule for equities and the dollar. The mechanism predicts a larger reaction during the closure than before it, and no reaction when no constraint binds.

*Salience (H2).* The reaction rises with the recent intensity of posting on the topic, because more posts raise attention to the topic and therefore the weight markets place on its news (Sims 2003).

*Habituation (H3).* The reaction falls with the number of recent similar posts, because markets learn that repeated messages carry less new information. This mechanism is the mirror image of H2 and is observationally distinct from it.

### 2.3 An interpretive question

Alongside these deductive hypotheses we asked an inductive question: what distinguishes the posts that markets did react to from those they did not? We used speech-act and validity-claim concepts only as sensitizing devices and followed the principles for critical interpretive research in information systems that concern contextualization, reflexivity, and the consideration of multiple interpretations (Myers and Klein 2011). The study makes no emancipatory claim and takes no position on the content of the communications themselves.

## 3. Research Design

### 3.1 Setting

The war that began on Saturday 28 February 2026 provides an unusual combination: a topic (Iran and Hormuz) on which the president posted frequently, a physical constraint (the strait was effectively closed from early March), and a commodity market in which the constraint was priced continuously. The first U.S. trading day was 2 March. WTI rose from about $67 to $114.6 by 7 April and was near $96 by the end of the sample. We use the same posts, assets, and design to test the mechanisms in periods and topics where the constraint was absent, which provides the contrast on which hypothesis H1 depends.

### 3.2 Data

*Posts.* We use the CNN-maintained archive of the president's posts. Between 1 March and 13 October 2026 there are 4,838 original posts after removing pure re-posts for the arrival analysis; 373 mention Iran, and 108 mention Iran with a threat term (rule S1, defined in the pre-registration). The archive extends to 2022, which we use for out-of-time tests.

*Markets.* We use hourly bars for WTI and Brent futures, E-mini S&P 500 futures, ten-year Treasury futures, the dollar index, USD/CNH, USD/KRW, gold, and several equities, covering October 2024 to October 2026; five-minute bars cover the final 60 days. Daily WTI and S&P 500 series cover earlier years.

### 3.3 Classifying posts

Each post was classified by two independent model instances, which received only the post text, for direction (escalation, de-escalation, mixed, other) and for type (action versus rhetoric). The primary analyses use the label on which both instances agree; this rule was fixed before returns were examined. Cohen's (1960) kappa for direction was 0.84 for oil and 0.86 for tariff posts, 0.92 for monetary policy and 0.87 for China, and 0.75 in the extension sample. In the out-of-time sample, agreement was 0.62 for oil and 0.96 for tariffs. Human validation of a 150-post subsample by two independent coders is under way [update before submission].

Our first run used keyword classes rather than coded labels and was misleading: the "threat" class contained the principal de-escalation posts, so oil appeared to fall after threats. Blind coding of all 191 keyword-selected posts corrected this, and the correction is documented as a dated amendment to the pre-registration.

### 3.4 Event-study design

The reaction to a post is the log change from the open of the hourly bar containing the post to the close of the next bar. The null distribution consists of the same two-hour change in all other bars of the period that contain no keyword-selected post within two hours. We drop posts within three hours of another post on the same topic, and we assess significance by permutation (5,000 draws; MacKinlay 1997 for the event-study logic). For hypothesis tests the reaction is signed so that positive values are in the direction the post implies: oil rising after escalation and falling after de-escalation; equity futures falling after tariff escalation and rising after tariff relief. Secondary outcomes are adjusted for multiple testing using Holm's (1979) procedure.

### 3.5 Pre-registration

Each analysis had a written plan, committed to the project repository before estimation. Plans state what the authors had already seen, define primary and secondary outcomes, specify decision rules, and are amended only through dated, disclosed entries. Appendix A lists every plan and its outcome. This practice follows the case for pre-registration in observational work with many analytic choices (Nosek et al. 2018) and is especially useful here because the sample, though large in posts, contains few events of each kind.

### 3.6 Interpretive analysis

To address the inductive question we assembled 136 posts (all 106 oil signal posts and 30 randomly drawn tariff posts), shuffled them, removed all labels and market information, and gave them to two independent analysts for open coding. Their codebooks were reconciled and fixed before reactions were linked. We then selected 20 cases by a pre-specified rule (the eight largest directional reactions, the six largest moves opposite to the post's direction, and six de-escalation posts with near-zero reaction) and collected contemporaneous market-wire coverage of each without revealing our reaction values to the researchers. Themes were developed with the stepwise abstraction of Gioia et al. (2013), and trustworthiness was approached through negative-case analysis, independent coding, and an audit trail (Lincoln and Guba 1985). Because the analysts were model instances, the interpretive findings are treated as hypothesis-generating and were subjected to held-out tests (Section 4.5).

## 4. Results

### 4.1 How the posts arrive

For the 108 S1 posts, daily counts have mean 0.48 and variance 0.74; the dispersion index is 350 on 226 degrees of freedom (p < 0.001), and a negative binomial with size 0.79 fits far better than a Poisson (likelihood-ratio p = 3 × 10⁻⁶). Inter-arrival times are bursty: the mean is 51 hours, the median is 21 hours, and the coefficient of variation is 1.94 (exponential: 1). A signal day is followed on average by 0.83 signals the next day, against 0.31 after a quiet day. Yet once week fixed effects are included, the Pearson dispersion of daily counts falls to 0.89, which is consistent with a Poisson process whose rate varies by week. The data resemble a Cox process in which bursts (11–14 March, 11–22 April) arise from changes in intensity rather than from clustering within a week (Figure 1; Cameron and Trivedi 2013). Weekly signal counts do not predict weekly market outcomes.

![Figure 1](figs/fig1_arrivals.png)

*Figure 1. Iran-related posts with threat terms (n = 108). Panel A: observed daily counts against Poisson and negative binomial fits. Panel B: weekly counts.*

### 4.2 The response to de-escalation posts

During the war, WTI fell by 1.29% over the two hours after a de-escalation post (n = 33; p < 0.001; 73% of posts followed by a decline; null standard deviation 1.15%). Brent fell by 1.21%, USD/KRW by 0.14% (a stronger won), and the S&P 500 rose by 0.23% (p = 0.006; n = 14 events with equity hours). Escalation posts (n = 28) were followed by no detectable change: WTI −0.02% (p = 0.92). Mixed posts (n = 10) also showed nothing. Reactions were larger for posts published outside U.S. equity hours (−2.25%, n = 16) than inside them (−0.39%, n = 17).

Two events carry much of the mean. The post of 23 March (WTI −9.8%) and the post of 7 April (−12.0%) account for most of it; without them the mean is −0.67% (p = 0.002) and the median −0.30%. We therefore report both throughout. The result is similar under the second coder (−1.37%) and for posts on which both coders agree (−1.45%, n = 30).

Other assets move in the expected directions. After de-escalation posts during the war, Treasury futures rose 0.10% (Holm-adjusted p = 0.004), the dollar index fell 0.11% (p = 0.014), and USD/CNH fell 0.04% (p = 0.02); gold did not respond significantly. Five-minute data, available for only the last 60 days, contain too few events to be informative (nine oil posts).

![Figure 2](figs/fig2_event_time.png)

*Figure 2. WTI path around war-period posts (de-escalation n = 33; escalation n = 27 with complete windows). Panel A: mean ± one standard error. Panel B: median.*

*Is the response simply momentum?* Figure 2 shows that oil had moved in the direction of the post during the five to six hours before it (+1.38% before escalation posts, t = 1.57; −0.55% before de-escalation posts, t = −0.95). A pre-registered control tests whether this accounts for the response. In ordinary hours there is no momentum (slope of the two-hour forward change on the prior six-hour change: −0.027, SE 0.019). After adjusting each post's reaction for its own prior move, the abnormal directional reaction to de-escalation posts is 1.32% (95% CI 0.44 to 2.37; one-sided p = 0.0005), against a raw 1.29%; excluding the two largest events it is 0.69% (p = 0.004). The control rules out momentum; it cannot rule out that the post and the price move respond to the same news at the same moment, a limitation we return to in Section 5.4.

*Pre-war and other topics.* Before the war, de-escalation posts about Iran show the same sign at roughly a quarter of the size (WTI −0.62% among posts on which both coders agree, n = 8, p = 0.008; the estimates are not significant for either coder alone, −0.30% and −0.28%, with n = 7 and 9). For posts about Russia, Venezuela, and other oil-related geopolitics, the asymmetry reverses: escalation raises oil (+0.46%, p = 0.013) and de-escalation does nothing. The response is therefore specific to the setting, which fits H1 but not any rule that would apply to posts as such.

*Identification.* De-escalation posts are a strong two-hour instrument for oil (first-stage p < 0.001) but a weak daily one (F = 2.8). We therefore cannot identify the effect of oil prices on Korean airlines or equities from them; the reduced forms are null.

### 4.3 Tests of the three mechanisms

**Binding constraint (H1).** Oil de-escalation posts during the war moved WTI by a directional 1.40% (n = 31), against 0.01% before the war (n = 24); the difference of 1.39 percentage points has a permutation p = 0.014 (Holm-adjusted over four primary tests, 0.056). The other three primary comparisons do not support the prediction: oil escalation (difference 0.05, p = 0.86), tariff escalation (the response was larger after the April 2025 tariff announcements, which is the opposite of the predicted sign, p = 0.09), and tariff relief (too few pre-period posts to test: three). H1 is therefore supported in the one cell with enough data and not elsewhere.

**Salience (H2).** In a pre-registered test on hold-out topics (monetary policy, non-tariff China; 55 and 48 signal posts), the coefficient of the log number of posts in the preceding week on standardized directional impact is +0.045 (SE 0.31; one-sided p = 0.44). The hold-out topics show essentially no hourly reaction to posts at all. Salience through posting intensity is rejected.

**Habituation (H3).** In-sample, an additional post on the same topic in the previous 24 hours is associated with a standardized impact lower by 0.24 (p = 0.036; exploratory, not corrected for multiplicity). The pre-registered out-of-time test on 14 February 2022–13 October 2024 (234 coded posts, 49 signal posts) gives −0.09 (SE 0.29; one-sided p = 0.38), and the minimum detectable effect at 80% power is 0.82, more than three times the in-sample estimate. Leave-one-year-out estimates are unstable. The mechanism is neither confirmed nor refuted; detecting an effect of 0.24 would require roughly 480 to 560 signal posts.

### 4.4 What the interpretive analysis suggests

The two analysts' independently built codebooks mapped onto each other with theme-level agreement on all six of one analyst's themes (some merged), and post-level agreement on shared concepts ranged from kappa 0.37 (claims of agreement) to 0.96 (amplification). Five themes were retained.

First, posts alternate between pressure and pause: conditional threats with stated triggers and deadlines, followed by postponements attributed to mediators or progress in talks. Second, a distinction runs through the corpus between concrete acts (dated, quantified, procedurally specified) and atmospheric statements (boasts, rebuttals of critics, sweeping claims). Third, announcements are contested by counterparties, with partial retracement: after the 23 March postponement the Iranian state denied that talks were taking place and oil rebounded the next session. Fourth, and most important for our argument, many of the largest reactions occur when the post is itself the first public announcement of the decision. Of the eight largest reactions, at least four (the 7 April ceasefire, the 23 March postponement, the 11 June approval, the 5 May pause) fit that description. Fifth, every one of the 20 triangulated cases has other reported drivers, and seven were not mentioned in market coverage. We read these findings as indicating that the channel is hard to separate from the decisions it carries.

### 4.5 Held-out tests of the interpretive propositions

The interpretive themes yielded four propositions, frozen before testing. Q1 held that re-posts and links, which carry no new decision, are followed by no reaction whereas original announcements are. Using a pseudo-out-of-sample set (the 2022–2024 posts and the monetary-policy and China topics, 134 posts with returns), the original-minus-amplification difference was −0.13 standard deviations (95% CI −0.57 to +0.31; one-sided p = 0.76; minimum detectable effect 0.75), so Q1 is not supported. Q4 held that posts made after market hours are better measured at the next open; the reopening reaction was 0.10 points smaller than the immediate one (n = 61; p = 0.63; exploratory because the cases motivating it were in the sample). Q2 (counterparty denial) and Q3 (concurrent news) require news-coded data that do not yet exist, and we have registered a prospective collection protocol instead.

## 5. Discussion

### 5.1 What the evidence supports

The evidence supports a conditional and narrow claim. Executive speech on a platform moves prices when it announces a decision that changes the state of a binding constraint, and it did so in the 2026 setting for de-escalation only. The same data reject a general salience channel, fail to confirm habituation, and show that an inductive account of which posts were consequential does not generalize to held-out data. A reader who expected posts to function as a general shock to attention will find little support here.

### 5.2 Contributions to theory

The paper's main theoretical claim is a boundary condition. Research on social media and markets often asks whether platform content "moves" prices and treats variation across messages as noise or sentiment. Our evidence suggests that variation across messages is partly variation across states of the world and across whether a message is itself an act. This implies that the unit of analysis for platform-mediated executive speech should be the announcement of a decision in a state where a constraint binds, rather than the post.

Second, we contribute to the literature on the arrival of platform content. A Poisson–Gamma structure, with within-week Poisson behavior and a weekly rate that moves, implies that the timing of posts is informative about the environment and is therefore not an exogenous source of variation. Event studies of executive posts that treat timing as random will overstate their identification.

Third, we offer a methodological contribution to IS research that uses large language models as coders: pre-registered plans, independent instances working blind to outcomes, agreed-label primary analysis, and explicit power reporting, together with a worked example of how the approach caught a misclassification (the "threat" class) that would have produced a misleading headline result. The same design allowed us to report three failures of general theory without ambiguity about what was tested.

### 5.3 Implications for practice

For market participants and analysts, the results suggest that a signal-detection rule on executive posts should discriminate between decision-carrying announcements and commentary, and that the state of the relevant constraint should condition how much weight the signal receives. For platform operators and regulators, the results highlight that the platform's role as the first channel for decisions concentrates informational advantage in the hours before secondary coverage; we make no claim about any trading behavior.

### 5.4 Limitations and future research

Several limitations qualify the findings. First, the coders, in both the classification and the interpretive analysis, are model instances. Their agreement with each other is high for most concepts but is not validation against human judgment; a human-coded subsample is under way and results should be incorporated before publication. Second, posting is endogenous: posts respond to developments, and all 20 triangulated cases show other reported drivers. Our momentum control addresses a specific channel and not simultaneous news. Third, the sample contains a single war and a single administration, and many cells contain few events; two events carry about half of the war-period mean. Fourth, hourly bars mix other news into the two-hour window, and escalation posts are followed by a rise in oil four to seven hours later in both mean and median paths, which falls outside our pre-registered window and deserves its own test. Fifth, access limits (several news sites could not be retrieved automatically) and approximate quotations constrain the triangulation. Sixth, we tested three theories and failed to confirm any; we cannot exclude that a different formulation would succeed.

Future work should collect posts prospectively under the protocol we registered for counterparty denial and concurrent news, aim for the sample size needed to test habituation, and extend the design to other binding-constraint settings (sanctions, shipping disruptions, trade embargoes) in which the boundary condition can be tested directly.

## 6. Conclusion

A single post on a platform can coincide with a large move in a market. Our evidence says that this happens under conditions, namely a binding constraint and a message that announces a decision to relax it, and not as a general property of executive speech on social platforms. We hope the design (pre-registered, blind to outcomes, and explicit about what failed) makes that conclusion a useful baseline for work that seeks more general mechanisms.

---

## Declarations [to be completed]

*Use of generative AI.* Large language models were used as classification instruments in the study and in drafting and analysis support. The journal's disclosure requirements should be checked and the declaration completed accordingly [required].

*Data and code availability.* Code, pre-registration files, coder outputs, and analysis results are in the project repository; the post archive and market data come from public sources [add repository DOI].

## References

[All references must be checked against the originals, including volume, page, and year, before submission.]

Austin, J. L. 1962. *How to Do Things with Words*. Oxford: Clarendon Press.

Barber, B. M., and Odean, T. 2008. "All That Glitters: The Effect of Attention and News on the Buying Behavior of Individual and Institutional Investors," *Review of Financial Studies* (21:2), pp. 785–818.

Bollen, J., Mao, H., and Zeng, X. 2011. "Twitter Mood Predicts the Stock Market," *Journal of Computational Science* (2:1), pp. 1–8.

Cameron, A. C., and Trivedi, P. K. 2013. *Regression Analysis of Count Data* (2nd ed.). Cambridge: Cambridge University Press.

Cohen, J. 1960. "A Coefficient of Agreement for Nominal Scales," *Educational and Psychological Measurement* (20:1), pp. 37–46.

Gioia, D. A., Corley, K. G., and Hamilton, A. L. 2013. "Seeking Qualitative Rigor in Inductive Research: Notes on the Gioia Methodology," *Organizational Research Methods* (16:1), pp. 15–31.

Gürkaynak, R. S., Sack, B., and Swanson, E. 2005. "Do Actions Speak Louder Than Words? The Response of Asset Prices to Monetary Policy Actions and Statements," *International Journal of Central Banking* (1:1), pp. 55–93.

Habermas, J. 1984. *The Theory of Communicative Action, Volume 1: Reason and the Rationalization of Society*. Boston: Beacon Press.

Holm, S. 1979. "A Simple Sequentially Rejective Multiple Test Procedure," *Scandinavian Journal of Statistics* (6:2), pp. 65–70.

Lincoln, Y. S., and Guba, E. G. 1985. *Naturalistic Inquiry*. Beverly Hills, CA: Sage.

MacKinlay, A. C. 1997. "Event Studies in Economics and Finance," *Journal of Economic Literature* (35:1), pp. 13–39.

Myers, M. D., and Klein, H. K. 2011. "A Set of Principles for Conducting Critical Research in Information Systems," *MIS Quarterly* (35:1), pp. 17–36.

Nosek, B. A., Ebersole, C. R., DeHaven, A. C., and Mellor, D. T. 2018. "The Preregistration Revolution," *Proceedings of the National Academy of Sciences* (115:11), pp. 2600–2606.

Searle, J. R. 1969. *Speech Acts: An Essay in the Philosophy of Language*. Cambridge: Cambridge University Press.

Sims, C. A. 2003. "Implications of Rational Inattention," *Journal of Monetary Economics* (50:3), pp. 665–690.

Tetlock, P. C. 2007. "Giving Content to Investor Sentiment: The Role of Media in the Stock Market," *Journal of Finance* (62:3), pp. 1139–1168.

## Appendix A. Pre-registration ledger

| Block | Plan | Outcome |
|---|---|---|
| Arrivals | poisson_posts/ANALYSIS_PLAN.md | Overdispersed; Poisson with time-varying rate |
| Weekly market tests | ANALYSIS_PLAN_MARKETS.md | Null |
| Intraday core | hf/ANALYSIS_PLAN.md (Amendment 1) | De-escalation response; none for escalation |
| Instrumental variables | ANALYSIS_PLAN_IV.md | Weak first stage (F = 2.8) |
| Extension and replication | ANALYSIS_PLAN_EXT.md | Coder-robust; partial pre-war replication; reversal for other oil posts |
| Binding constraint (H1) | THEORY_AND_PAPER_PLAN.md | Partly supported |
| Salience (H2) | THEORY_V2_SALIENCE.md | Rejected |
| Habituation (H3) | THEORY_V3_HABITUATION.md | Underpowered |
| Interpretive analysis | ANALYSIS_PLAN_QUAL.md (Amendments 1–2) | Five themes; four propositions |
| Held-out tests of propositions | ANALYSIS_PLAN_QUAL_TESTS.md | Q1, Q4 not supported; Q2, Q3 deferred |
| Pre-trend control | ANALYSIS_PLAN_PRETREND.md | Response survives |

## Appendix B. Coding protocol

[Summary of the direction and type definitions, the blind-coding instructions, the agreed-label rule, the reconciliation procedure for interpretive codebooks, and a reference to the repository files.]

## Appendix C. Human validation

[To be completed when the 150-post human-coded subsample is returned: kappa between model-agreed labels and human-agreed labels, and the primary result re-estimated on human labels.]
