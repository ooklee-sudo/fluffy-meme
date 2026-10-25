::: {custom-style="Title"}
Do Influencers Pay? Limited Attention, Engagement Elasticity, and Simulation-Based Pre-Tests for Seeding Decisions
:::

**Abstract**

Marketers pre-test influencer campaigns in agent-based simulators before choosing between a few influencers and many ordinary users. This research shows that the recommendation of such a pre-test depends on three modeling choices that are separate from agent realism: the metric used to compare plans, the mechanism that schedules agent actions, and the assumed relation between an account's audience size and follower attention, summarized as an engagement elasticity. In an event-driven simulator, concentrated seeding dominates at every hour and quantile under constant attention, and the apparent scale-versus-speed trade-off in the time to half of a plan's own adopters is an artifact of normalization. Alternative schedulers roughly double the absolute differences between plans. The ranking reverses near an elasticity of 0.3 for discounted reach and downside risk and between 0.4 and 0.5 for expected reach. Estimated on 209,890 Weibo posts, the elasticity is 0.66 (95% CI [0.63, 0.68]), above both thresholds, although known data biases push the estimate upward. Simulators that assume constant attention thus build in an advantage for influencer seeding, so simulation-based seeding analysis should make its attention model explicit and estimable.

*Keywords:* influencer marketing; seeding; limited attention; agent-based simulation; stochastic dominance; engagement elasticity; social media

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```
# Introduction

How to allocate a seeding budget is one of the most basic decisions in digital marketing: place the message with a few prominent accounts, or spread the same budget across many ordinary users (Hinz et al. 2011; Leung et al. 2022). Field experiments on this choice are expensive, can disturb the communities under study, and are hard to repeat, so marketing managers and agencies narrow their options with model-based pre-tests before committing budget. Agent-based simulation has long served this purpose (Bonabeau 2002; Rand and Rust 2011), and generative AI has renewed its appeal: agents driven by large language models (LLMs) can be given personas and can react to natural-language content, so that a simulated platform populated by such agents promises a synthetic audience on which campaigns can be tried before launch (Argyle et al. 2023; Horton 2023; Park et al. 2023; Zhang et al. 2024).

Most of the discussion of such simulators in marketing, from the guidelines for rigor in agent-based marketing models (Rand and Rust 2011) to the current work on LLM agents, asks whether the simulated agents behave realistically. That question is necessary but not sufficient. A pre-test is useful only if it ranks the options correctly, and the ranking depends on modeling choices that are logically separate from behavioral fidelity: how the simulator summarizes outcomes, how it decides when simulated users act, and what it assumes about the platform environment in which they act. This paper examines three such choices and shows that each can change what a manager is told.

The first is the decision metric. Simulation studies of seeding often report the final number of adopters together with a speed measure such as the time to reach half of the eventual adopters. Such a measure is normalized by the cascade's own size, so a plan that produces a small cascade can appear fast simply because it finishes early. The marketing literature distinguishes the value of accelerating adoption from the value of expanding it (Libai, Muller, and Peres 2013), but managers with a short attention window do not care when a campaign reaches half of its own total; they care how many people it has reached by a given time. Decision theory supplies criteria that respect this distinction: discounted value for time preference, certainty equivalents and downside risk measures for risk preference, and stochastic dominance for robustness to both (Hadar and Russell 1969; Markowitz 1952; Rockafellar and Uryasev 2000).

The second is the timing mechanism. Many LLM-agent simulators advance in rounds and query agents on a schedule, while some add hourly activation profiles (Yang et al. 2024). Empirical activity is circadian, bursty, and responsive to triggers (Barabási 2005; Crane and Sornette 2008; Malmgren et al. 2008), and concurrent work has begun to gate LLM agents with self-exciting point processes (Miao et al. 2026; Zhang et al. 2026a, 2026b). These studies evaluate whether simulated timing looks realistic. None asks whether the timing assumption changes a managerial decision.

The third is the attention model. Theories of limited attention hold that attention, not information, is the scarce resource in information-rich environments (Simon 1971), and that on social platforms the attention a user devotes to any one source falls as the number of sources competing for it rises (Hodas and Lerman 2014; Weng et al. 2012). Followers of large accounts tend to follow many other accounts, have weaker ties to the author, and encounter its posts among more competing content, so the attention an account commands per follower should decline with its audience size. Studies of influencer campaigns are consistent with this view (Wies, Bleier, and Edeling 2023), yet simulators typically assume that every follower is equally likely to see a post. We formalize the relation as an engagement elasticity β and argue that it, more than the behavioral richness of the agents, is the parameter on which the seeding decision turns.

We study these choices with an event-driven simulator in which each agent's action times are drawn from an inhomogeneous Poisson process whose intensity combines a persona-specific circadian baseline with decaying stimuli from content exposure and feedback. The agents are rule-based throughout; the simulator contains no language model, and the Discussion section describes which results carry over to LLM-agent simulators. We ask four questions. RQ1: Under decision-theoretic criteria, is there a trade-off between concentrated and distributed seeding at all? RQ2: Does the timing mechanism change the ranking or the size of the differences? RQ3: How do realistic seed pricing and hybrid portfolios change the comparison? RQ4: How does the answer depend on the engagement elasticity, and where do real campaigns lie?

The paper makes three contributions. First, to research on agent-based modeling in marketing, it shows that choices outside the agent model can reverse or distort a recommendation, and it derives three principles for pre-tests: report reach at fixed horizons and dominance relations rather than scale-normalized timing; test sensitivity to the scheduling mechanism; and make the attention model explicit and estimable. In our base configuration a scale-normalized speed metric manufactured a trade-off where none existed, and alternative schedulers roughly doubled the absolute differences between plans. Second, to research on seeding and influencer marketing, it identifies the engagement elasticity as a boundary condition on the long-standing debate between influentials and ordinary users (Bakshy et al. 2011; Goldenberg et al. 2009; Hinz et al. 2011; Watts and Dodds 2007). The ranking reverses at moderate elasticities, with thresholds that differ by criterion and enclose a band in which the manager's time and risk preferences decide, and a first-generation exposure argument approximately predicts where the threshold on final reach lies. Third, it converts a qualitative debate into an estimable quantity and estimates it: on six influencer campaigns on Weibo, the elasticity was about 0.66, above the thresholds. Because the simulation results come from a synthetic population and the estimate is associational and subject to the upward biases discussed in the section on estimating the engagement elasticity, we present the conclusions as theory-grounded hypotheses for field testing rather than as prescriptions.

The next section reviews the background. The Framework section sets out the exposure model, the decision criteria, and our conjectures. The Simulator section describes the simulator, Experiments and Results reports the experiments, the following section estimates the elasticity on platform data, and the Discussion and Conclusion sections cover implications and limitations.

# Background

## Seeding: Influentials, Ordinary Users, and the Value of Acceleration

Influence maximization asks for the seed set that maximizes expected spread (Kempe, Kleinberg, and Tardos 2003). The influentials hypothesis holds that a few highly connected individuals drive diffusion, whereas Watts and Dodds (2007) argued that large cascades are driven at least as often by many easily influenced ordinary users. Empirical evidence is mixed. Goldenberg et al. (2009) and Hinz et al. (2011) found that seeding well-connected hubs speeds and widens adoption, whereas Bakshy et al. (2011) found that targeting ordinary users can be more cost-effective once costs are considered. Field experiments have separated influence from susceptibility (Aral and Walker 2012) and shown that network-based seeding raises adoption when adoption requires several exposures (Beaman et al. 2021). Economists have studied the same question as a targeting problem (Ballester, Calvó-Armengol, and Zenou 2006, Galeotti and Goyal 2009, Banerjee et al. 2013). Related work has used simulation and network analytics to support social media decisions, for example by identifying opinion leaders and message disseminators (Bao and Chang 2014; Li and Du 2011), modeling diffusion with consumer and brand agents (Schramm et al. 2010), and modeling the co-diffusion of competing memes (He et al. 2024).

Two features of this literature matter here. First, it mostly evaluates expected final adoption, or adoption speed measured relative to a campaign's own scale; Libai, Muller, and Peres (2013) show that the value of a seeding program depends on whether it accelerates adoption that would otherwise occur later or expands the set of adopters, but decision criteria that combine time and risk preferences have rarely been applied to the comparison. Second, the debate has not identified a single market parameter that determines which side is right in a given setting. We argue that limited attention supplies one.

## Simulation-Based Pre-Tests

Agent-based modeling studies outcomes that emerge from the interaction of heterogeneous actors (Bonabeau 2002; Gilbert 2008), and simulation is an established method for developing theory about such systems (Davis, Eisenhardt, and Bingham 2007). In marketing, the credibility of agent-based models rests on careful specification and validation (Rand and Rust 2011). Generative AI has changed what such models can contain: LLM-based agents replace hand-coded rules with a generative model conditioned on a persona and observations (Park et al. 2023), language models can reproduce response distributions of human subpopulations (Argyle et al. 2023) and behave like simulated economic agents (Horton 2023, Brand, Israeli, and Ngwe 2023), and social-network simulators have been built on these ideas (Gao et al. 2023; Piao et al. 2025; Törnberg et al. 2023; Zhang et al. 2024). The evaluation of these models has focused on behavioral fidelity. From a decision-analytic perspective, however, the relevant quality of a pre-test is the quality of the decision it supports, and that depends on every component that lies between the simulated population and the recommendation. We focus on three such components and ask whether each changes the recommendation, holding the agent model fixed. Our agents are rule-based, but the three components we study are present in any agent-based pre-test, including those built on LLM agents.

## Timing of Action

A temporal point process describes events through a conditional intensity λ(t). Human communication is non-stationary, with strong daily cycles, and bursty, with heavy-tailed inter-event times (Barabási 2005); Malmgren et al. (2008) showed that a cascading non-homogeneous Poisson mechanism with circadian modulation accounts for much of that heavy tail. In a Hawkes process each event raises the intensity of future events (Hawkes 1971), and self-exciting models describe the popularity of online content (Crane and Sornette 2008; Zhao et al. 2015). Non-homogeneous Poisson processes can be simulated exactly by thinning (Lewis and Shedler 1979; Ogata 1981).

Simulators differ in how they decide when agents act. Early systems advance in synchronous rounds. OASIS (Yang et al. 2024) activates each agent according to a 24-dimensional hourly activity vector, and the time-aware influencer simulator of Zhang et al. (2024) selects active agents from user timelines and content lifecycles; both reproduce daily rhythms but do not let an agent's current situation change when it acts. Concurrent work places a point process in front of the LLM: Miao et al. (2026) fit per-user Hawkes processes to email logs, POSIM (Zhang et al. 2026b) drives an opinion simulator with a circadian-modulated Hawkes engine, and Zhang et al. (2026a) gate LLM agents with a data-calibrated self-excitation channel and show that a gate-only ablation reproduces the timing of the LLM-coupled simulator. These studies judge timing by its realism; we ask whether it changes a decision.

# Framework

## Exposure and the Engagement Elasticity

If the probability that a follower of account a sees and responds to its post is proportional to f~a~^-β^, where f~a~ is the account's number of followers, then the expected number of responses grows as f~a~^1-β^. We call β the *engagement elasticity*. With β = 0, every follower is equally likely to see a post, which is the usual simulator assumption; with β > 0, an influencer's nominal reach overstates its effective reach. In our simulator a follower sees an author's post with probability

$$
p_{\text{view}}(a) = 0.5 \cdot (\max(f_a, 10)/10)^{-\beta} \qquad (1)
$$

where the floor of 10 followers normalizes the probability for small accounts.

Consider an equal-link budget: a plan that seeds n accounts with about f followers each, f ≥ 10, uses nf = B follower links. Under Equation 1 its first-generation exposures are n f  p~view~ = 0.5· 10^β^ B f^-β^.

**Proposition 1 (first-generation exposures).** *Under an equal-link budget and exposure rule in Equation 1, the number of first-generation exposures is constant in seed size f when β = 0 and strictly decreasing in f when β > 0. For plans with seed sizes f~C~ > f~D~ ≥ 10, the ratio of first-generation exposures of the distributed to the concentrated plan equals (f~C~/f~D~)^β^, which is equal to one at β = 0 and strictly increasing in β.*

The proposition follows directly from the expression above; it is stylized, because it treats seeds as having a common audience size and ignores feed competition, comment visibility, and later generations of spread. It shows how the first-order effect of attention scales: with distributed seeds at the exposure floor and concentrated seeds of about f~C~ followers, the first-generation ratio shifts in favor of distribution by about (f~C~/10)^β^. Concentration may enjoy other advantages, for example because the audiences of large accounts are themselves well connected. Let R~0~ denote the ratio of final reach under concentration and distribution when β = 0. If β acts mainly through first-generation exposure and leaves this downstream advantage roughly intact, final reach reverses where the two effects offset each other:

$$
\beta^{*} \approx \ln R_0 / \ln(f_C/10) \qquad (2)
$$

Early adopters are dominated by first-generation exposures, whereas final reach also reflects downstream amplification, so criteria that weight early adoption should reverse first. Equation 2 also implies that thresholds fall as the ratio between influencer and ordinary audiences rises, a point we return to in the Discussion section. We treat Equation 2 as a heuristic that organizes the simulation results, not as a derived result.

## Decision Criteria

Let N(t) be the cumulative number of adopters t hours after the campaign is injected, where an agent adopts when it first comments on or retweets campaign content, and let N = N(48) be the final count. A seeding plan induces a distribution of the path N(·) over replications. We compare plans with four criteria, each tied to a property of the manager's preferences.

*Time preference.* If the value of an adopter decays with the time it takes to reach them at rate δ per hour, the value of a campaign is the discounted reach

$$
V(\delta) = \int_0^{48} \exp(-\delta t)\, dN(t) \qquad (3)
$$

which equals final reach at δ = 0 and rewards early adoption as δ grows; ln 2/δ is the half-life of attention. A trade-off between scale and speed exists only if the ranking of two plans on E[V(δ)] changes at some critical δ^\*^.

*Risk preference.* For a decision maker with constant absolute risk aversion ρ, the certainty equivalent of a plan is CE(ρ) = -(1/ρ)ln E[exp(-ρ N)], computed from the empirical distribution. A risk–return trade-off exists only if the ranking on CE changes at some critical ρ^\*^. Because the standard deviation penalizes favorable as well as unfavorable outcomes, we also report the conditional value at risk CVaR~0.2~, the mean of the worst 20% of replications (Rockafellar and Uryasev 2000).

*Robustness.* Plan A first-order stochastically dominates plan B if every quantile of N under A is at least as large as under B, in which case every decision maker who prefers more adopters prefers A, whatever their risk attitude (Hadar and Russell 1969). The analogous pathwise statement for time preference is that E[N(t)] under A exceeds E[N(t)] under B at every t, which implies E[V~A~(δ)] > E[V~B~(δ)] for every δ.

*Why scale-normalized speed misleads.* A common speed metric is t~50~, the time at which a run reaches half of its own final count. Because t~50~ is invariant to the scale of N(·), a plan can have a smaller t~50~ and yet have fewer adopters than its competitor at every point in time. Such a plan is faster in shape but slower in reach, and a manager who acts on t~50~ may choose it in exactly the situations, short attention windows, where it is worse. We report t~50~ only to connect with prior practice and to test Conjecture 1.

*Cost.* To examine RQ3 we price a seed with f followers at C(f) = c~0~ + f^γ^, where c~0~ is a fixed per-account cost of contracting and management and γ ≤ 1 captures declining prices per follower for larger accounts. The budget equals the cost of the three largest accounts. The equal-link comparison common in the literature corresponds to c~0~ = 0 and γ = 1. We also evaluate hybrid portfolios that seed the k largest accounts (k = 0, 1, 2, 3) and spend the remaining budget on randomly chosen ordinary accounts.

## Conjectures

The preceding arguments lead to three conjectures that we examine in the Experiments and Results section.

*Conjecture 1 (metric).* When the speed of a plan is measured relative to its own final scale, a pre-test can show a speed advantage for a plan that is behind in cumulative reach at every horizon, and therefore manufacture a trade-off that does not exist under any monotone preference over adopters, time, and risk.

*Conjecture 2 (timing).* Schedulers that omit stimulus-driven reactivity change the magnitude of simulated differences between seeding plans, and hence any decision that turns on a threshold, even when they preserve the ranking.

*Conjecture 3 (attention).* The ranking of concentrated and distributed seeding depends on β. When β is low, concentration is preferred under every monotone preference; when β is high, distribution is; in between lies a band in which the choice depends on the manager's time and risk preferences. Criteria that weight early adoption reverse at lower β than expected final reach.

# The Simulator

The simulator is designed so that action times are generated by agent state rather than by the simulation clock, and so that its outputs can be evaluated against decision criteria. Parameters not determined by the design are assumptions of this instantiation and are listed in Web Appendix A.

## Platform Environment

The environment maintains a directed follower graph, a store of items (posts, comments, and retweets), and a feed of the 40 most recent items shown to each agent. The follower graph is generated by preferential attachment on in-degree (Barabási and Albert 1999); each new agent follows three existing agents, giving a 2,000-agent network whose three largest accounts have about 1,000 followers between them. When agent a publishes content, each follower sees it with probability given by Equation 1, with β ≥ 0 the engagement elasticity. With β = 0 every follower is equally likely to see a post, which is our base configuration. Comments are shown with an additional visibility factor of 0.4. Authors receive a notification when their content is commented on or retweeted. When an agent comments or retweets, it chooses among feed items with probability proportional to its interest in the item's topic and an exponential recency weight with a two-hour time constant.

## Persona Agents

Each agent is assigned one of five personas (Table 1) that set its baseline rate, its sensitivity to stimuli, its chronotype, and its action propensities. Baseline rates are multiplied by a mean-one log-normal factor (σ = 0.4), and chronotypes are perturbed by a normal term (σ = 1.5 h). Each agent has an interest vector over five topics drawn from a symmetric Dirichlet distribution with concentration 0.4.

**Table 1. Five Personas Differ in Activity Rates, Peak Hours, and Action Propensities**

| Persona | Share | Base rate λ^0^ (1/h) | Gain g | Peak hour | P(post / comment / retweet / like) |
|---|---|---|---|---|---|
| Early adopter | 15% | 0.45 | 1.3 | 22 | .30 / .20 / .25 / .25 |
| Cynic | 15% | 0.30 | 0.8 | 23 | .20 / .45 / .05 / .30 |
| Trend follower | 25% | 0.40 | 1.2 | 21 | .15 / .15 / .40 / .30 |
| Lurker | 30% | 0.12 | 0.6 | 21 | .05 / .10 / .10 / .75 |
| News junkie | 15% | 0.70 | 1.0 | 20 | .40 / .20 / .20 / .20 |

*Notes:* When an agent selects an action that requires a feed item and none is eligible, it posts instead.

## Intensity Model and Scheduler

Let c~i~(t) be a mean-one daily activity profile for agent i with an evening peak at its chronotype, a smaller midday peak, and a night trough. The conditional intensity is

$$
\lambda_i(t) = \lambda_i^0 c_i(t) + S_i(t) \qquad (4)
$$

$$
S_i(t) = \min(S_{\max}, A_i(t)) \qquad (5)
$$

where A~i~(t) = Σ~j~ κ g~i~ I~ij~ r~ij~ exp(−(t − t~j~)/τ) is the sum of decayed stimuli, t~j~ is the time of the jth stimulus (an exposure or a notification), I~ij~ ∈ [0, 5] is the urge rating returned by the urge function described under The Urge Function, r~ij~ ∈ {0.25, 0.50, 0.75} encodes topical relevance, g~i~ is the persona gain, κ = 0.16, τ = 1 h, and S~max~ = 3. Notifications enter with relevance 0.50. The cap keeps the additive intensity finite under this exposure rule; without it the process becomes supercritical in the evening. Next event times are drawn by thinning against the dominating rate λ~i~^0^ · max c~i~ + S~i~(t), which is valid until the next stimulus because S~i~ decays; when a new stimulus arrives the pending event is redrawn, which is exact because the Poisson process is memoryless.

## The Urge Function

The urge function maps an agent's situation (time of day, emotional state, the number of relevant items seen in the last hour, the relevance of the latest item, and notification status) to a rating in [0, 5] by a fixed rule given in Web Appendix A. The rating scales how strongly a stimulus raises the agent's intensity; it does not determine when the agent acts, which is set entirely by Equations 4 and 5. Using a transparent rule rather than a learned or generative model makes the experiments reproducible at negligible cost and isolates the effects of metrics, timing, and attention from the behavior of the agents. Because the rating enters the model only through I~ij~ in Equation 5, the architecture would in principle allow a different rating mechanism to be substituted, but we have not implemented or tested an alternative, and all results in this paper are conditional on the rule-based function.

## Alternative Schedulers

To examine RQ2 we hold every other component fixed and replace the scheduler with three alternatives that represent common practice: (a) circadian-only activation, an inhomogeneous Poisson process with intensity λ~i~^0^ c~i~(t) in which stimuli update feeds but do not change timing, similar in spirit to hourly activation vectors; (b) a homogeneous Poisson process at rate λ~i~^0^; and (c) fixed-period polling with period 1/λ~i~^0^ and random phase. Because stimuli generate a large share of activity under the proposed scheduler, the alternatives would otherwise produce far fewer events. We therefore multiply their baseline rates by 2.00, the ratio of total events under the proposed and circadian-only schedulers in pilot runs without a campaign, so that all schedulers produce similar background activity.

# Experiments and Results

## Setup

All experiments used a 2,000-agent network, an 18-hour warm-up, a campaign of one post per seed injected at 18:00 on topic 0 unless stated otherwise, and a 48-hour observation window. Concentrated seeding used the three accounts with the most followers. Distributed seeding drew accounts at random from outside the top 5% by follower count until their total cost reached the budget; under equal-link pricing this required about 620 accounts. Accounts without followers are priced at one follower-equivalent, so that the budget buys a finite number of ordinary accounts. Replications were paired: within a replication both plans used the same network, personas, and random seed. We report means, paired differences with 95% percentile bootstrap intervals (4,000 resamples), and the share of replications in which concentrated seeding produced more adopters. The base and scheduler comparisons used 30 replications per cell, the elasticity sweep 15 (30 for β from 0.35 to 0.45 and at 0.60, where the intervals overlap zero), and the remaining experiments 20. Code and per-run results are provided as an anonymized supplementary archive. Generative AI (Claude, Anthropic) was used to write and run the simulation and analysis code and to draft and edit the manuscript text; the authors specified the model and take responsibility for the code, the results, and the text.

## Is There a Scale-Versus-Speed Trade-Off? (RQ1)

Table 2 reports the base configuration (β = 0, equal-link pricing, 30 paired replications). Concentrated seeding produced about three times as many adopters as distributed seeding (152 vs. 50; paired difference 102, 95% CI [90, 115]; concentrated ahead in all 30 replications). Distributed seeding reached half of its own adopters 0.69 hours sooner (95% CI [0.50, 0.87]) and had a much smaller standard deviation (8 vs. 34). On the usual reading this is a trade-off: concentration for scale, distribution for speed and predictability.

**Table 2. Concentrated Seeding Leads at Every Hour but Reaches Half of Its Adopters Later**

| | Concentrated (3 seeds) | Distributed (~622 seeds) |
|---|---|---|
| Mean cumulative adopters at 1 h | 37 | 17 |
| at 2 h | 66 | 28 |
| at 3 h | 91 | 36 |
| at 6 h | 135 | 47 |
| at 12 h | 149 | 49 |
| at 48 h (final) | 152 | 50 |
| SD of final adopters | 34 | 8 |
| Minimum of final adopters | 96 | 32 |
| CVaR~0.2~ (mean of worst 20%) | 112 | 39 |
| Mean t~50~ (h) | 2.39 | 1.70 |

*Notes:* Means over 30 paired replications (β = 0, equal-link budget, 18:00 injection); the number of distributed seeds is the mean over replications.

The decision criteria defined under Decision Criteria tell a different story. Concentrated seeding led in mean cumulative adopters at every hour, so its expected discounted reach was higher for every discount rate we evaluated (δ from 0 to 2 per hour, an attention half-life as short as 21 minutes; paired differences from 101.5 at δ = 0 to 10.6 [9.0, 12.2] at δ = 2), and no critical δ^\*^ exists. Its empirical distribution of final adopters lay above that of distributed seeding at every quantile, so it first-order stochastically dominated, which implies a higher certainty equivalent for every degree of risk aversion; no critical ρ^\*^ exists either. Its worst outcomes were also better: CVaR~0.2~ was 112 against 39, and its minimum 96 against 32. Distributed seeding was more predictable in the sense of a smaller variance, but not in the sense that matters to a risk-averse manager, because its variability was low around a low level, whereas the variability of concentrated seeding came almost entirely from favorable outcomes. In no replication was distributed seeding ahead after one hour or after two hours.

The answer to RQ1 is therefore negative for this configuration, and Conjecture 1 is supported: under any monotone preference over adopters, time, and risk, concentrated seeding is the better plan, and the apparent trade-off is produced by the scale-normalized speed metric. In this configuration the concentrated plan was also ahead from the first hour (37 vs. 17), so its advantage is not confined to downstream spread; the elasticity experiments below show how the early advantage disappears as attention declines with audience size.

![Figure 1. Concentrated Seeding Leads Throughout Under Constant Attention, but Its Early Lead Disappears When Attention Declines With Audience Size. Notes: Mean cumulative adopters after injection (equal-link budget, 15 paired replications). Panel (a): β = 0. Panel (b): β = 0.3.](figures/Figure_1.png){width=6.3in}

## Does the Timing Mechanism Matter? (RQ2)

Table 3 repeats the base comparison under the four schedulers. The direction of every result was unchanged: concentrated seeding produced more adopters, reached a later t~50~, and dominated on CVaR~0.2~ under all four. The magnitudes were not. Under polling, HPP, and circadian-only activation, the absolute scale advantage of concentration was 199 to 248 adopters, 1.9 to 2.4 times the 102 obtained under the event-driven scheduler, and the t~50~ gap was 1.0 to 1.5 hours rather than 0.7 hours. In relative terms the difference was smaller: concentrated seeding produced 3.6 to 4.1 times as many adopters as distributed seeding under the alternatives, against 3.0 times under the event-driven scheduler. Part of the absolute difference therefore reflects the larger cascades that the alternative schedulers produced in response to the campaign (276 to 328 adopters for concentrated seeding, against 152), even though volume matching equalized background activity in the absence of a campaign. Circadian-only activation, which reproduces daily rhythms but not reactivity, did not close the gap; the difference lies in the stimulus channel, not the daily profile.

**Table 3. Alternative Schedulers Roughly Double the Absolute Gap Between Plans**

| Scheduler | Adopters (C / D) | Ratio C/D | Δ adopters (SE) [95% CI] | Δ t~50~, h (SE) [95% CI] | CVaR~0.2~ (C / D) |
|---|---|---|---|---|---|
| Event-driven IPP (proposed) | 152 / 50 | 3.03 | 102 (6.3) [90, 115] | 0.69 (0.10) [0.50, 0.88] | 112 / 39 |
| Circadian-only IPP | 328 / 80 | 4.10 | 248 (18.4) [212, 287] | 0.97 (0.11) [0.76, 1.19] | 205 / 67 |
| Homogeneous Poisson | 276 / 77 | 3.57 | 199 (14.2) [172, 228] | 1.46 (0.15) [1.16, 1.77] | 184 / 65 |
| Fixed-period polling | 277 / 71 | 3.88 | 205 (14.7) [177, 235] | 1.25 (0.16) [0.95, 1.56] | 178 / 61 |

*Notes:* Standard errors (SE) and 95% percentile bootstrap intervals (4,000 resamples) of paired differences over 30 replications; adopters are means. Alternative schedulers were volume-matched to the proposed scheduler in the absence of a campaign (see Alternative Schedulers). C = concentrated; D = distributed; IPP = inhomogeneous Poisson process.

The pattern was the same when the campaign was injected at 03:00 or 09:00 (Table 4). Under the event-driven scheduler a night-time injection roughly halved the reach of both plans, because few agents were active to respond, whereas under circadian-only activation the night-time effect appeared mainly as a long delay, with the t~50~ of concentrated seeding stretching to more than seven hours.

**Table 4. Night-Time Injection Roughly Halves the Reach of Both Plans Under Event-Driven Scheduling**

| Injection | Scheduler | Adopters (C / D) | Δ adopters (SE) [95% CI] | t~50~, h (C / D) |
|---|---|---|---|---|
| 03:00 | Event-driven IPP | 80 / 28 | 52 (5.0) [43, 62] | 2.32 / 2.05 |
| 03:00 | Circadian-only | 256 / 59 | 197 (22.5) [154, 242] | 7.38 / 4.60 |
| 09:00 | Event-driven IPP | 111 / 47 | 65 (9.2) [48, 84] | 2.49 / 2.17 |
| 09:00 | Circadian-only | 338 / 83 | 255 (19.3) [219, 296] | 3.71 / 2.30 |
| 18:00 | Event-driven IPP | 159 / 50 | 108 (8.8) [92, 127] | 2.50 / 1.71 |
| 18:00 | Circadian-only | 342 / 81 | 260 (25.0) [214, 310] | 2.60 / 1.54 |

*Notes:* Twenty paired replications per cell; SE and 95% bootstrap intervals of the paired difference in adopters. C = concentrated; D = distributed.

The answer to RQ2 is that, in this configuration, the timing mechanism did not change the ranking but roughly doubled the absolute differences between plans and enlarged the relative difference by about a fifth to a third, consistent with Conjecture 2. Where a decision turns on a threshold, for example whether the scale advantage exceeds the cost of contracting influencers, or where the trade-off band reported in the elasticity experiments lies, differences of this size are decision-relevant.

## Seed Pricing and Hybrid Portfolios (RQ3)

Table 5 reports hybrid portfolios under three pricing rules. Under equal-link pricing, each additional influencer raised expected reach, CVaR~0.2~, and discounted reach at δ = 1 per hour, and the pure concentrated plan (k = 3) was best on every criterion. Under concave pricing (γ = 0.7) or a fixed per-account fee (c~0~ = 10 follower-equivalents), the same budget bought only 90 to 134 ordinary accounts, and distributed seeding reached 9 to 16 adopters, 6 to 10 percent of the reach of concentrated seeding. Pricing therefore strengthens the case for concentration when β = 0: the equal-link comparison is generous to distributed seeding, because it ignores the per-account costs of working with hundreds of small accounts.

**Table 5. Each Additional Influencer Raises Reach, and Pricing Frictions Weaken Distributed Seeding**

| Pricing C(f) | k | Seeds | Mean adopters (SD) | CVaR~0.2~ | V(δ = 1/h) | t~50~ (h) |
|---|---|---|---|---|---|---|
| f (equal links) | 0 | 629 | 50 (9) | 38 | 15 | 1.71 |
| | 1 | 378 | 84 (27) | 60 | 23 | 1.85 |
| | 2 | 180 | 133 (40) | 85 | 30 | 2.33 |
| | 3 | 3 | 159 (38) | 114 | 35 | 2.50 |
| f^0.7^ (concave) | 0 | 134 | 16 (5) | 10 | 5 | 1.76 |
| | 1 | 84 | 78 (44) | 34 | 16 | 2.33 |
| | 2 | 41 | 116 (36) | 70 | 25 | 2.33 |
| | 3 | 3 | 159 (38) | 114 | 35 | 2.50 |
| 10 + f (fixed fee) | 0 | 90 | 9 (5) | 4 | 3 | 1.65 |
| | 1 | 55 | 77 (43) | 38 | 17 | 2.19 |
| | 2 | 27 | 126 (55) | 76 | 27 | 2.31 |
| | 3 | 3 | 159 (38) | 114 | 35 | 2.50 |

*Notes:* Twenty paired replications per row (β = 0); k is the number of largest accounts seeded, and the remaining budget buys randomly chosen ordinary accounts. Under equal-link pricing C(f) = f; under concave pricing C(f) = f^0.7^; under the fixed fee C(f) = 10 + f. Accounts without followers are priced as one follower. V(δ = 1/h) is discounted reach.

## Engagement Elasticity and the Reversal of the Ranking (RQ4)

The preceding experiments assume constant attention. Tables 6 and 7 and Figure 2 relax this assumption by varying β in Equation 1, which applies to all accounts in the network. The ranking reversed, and it did so at different values of β for different criteria. On discounted reach at δ = 1 per hour, the advantage of concentration shrank from 18.2 at β = 0 to 3.2 [0.1, 6.5] at β = 0.2, was indistinguishable from zero at 0.25 and 0.30, and distributed seeding was clearly better from β = 0.35 (−5.0 [−6.8, −3.2]). On CVaR~0.2~ the plans were close at 0.30 (57 vs. 54) and distributed seeding was better from 0.35 (48 vs. 59). The two plans were tied in adopters after one hour at β = 0.25, and distributed seeding led from 0.30. On expected final reach, concentrated seeding kept a clear advantage up to β = 0.30 (18 [4, 33]); the difference was indistinguishable from zero from 0.35 to 0.45 (9, −5, and −7), and distributed seeding was clearly better from 0.50 (−19 [−33, −1]) and at 0.60 (−33 [−41, −24]). At β = 0.5, distributed seeding produced more adopters (74 vs. 55) and had better worst-case outcomes (CVaR~0.2~ of 59 vs. 33).

**Table 6. Concentrated Seeding Loses Its Advantage in Final Adopters as the Engagement Elasticity Rises**

| β | Replications | Adopters (C / D) | Δ adopters (SE) [95% CI] | P(C > D) |
|---|---|---|---|---|
| 0.00 | 15 | 157 / 53 | 104 (8.8) [86, 121] | 1.00 |
| 0.05 | 15 | 139 / 47 | 92 (9.9) [73, 112] | 1.00 |
| 0.10 | 15 | 117 / 59 | 58 (8.1) [41, 74] | .93 |
| 0.15 | 15 | 128 / 61 | 68 (11.5) [46, 92] | 1.00 |
| 0.20 | 15 | 106 / 63 | 43 (8.1) [28, 59] | .93 |
| 0.25 | 15 | 110 / 65 | 46 (10.4) [27, 68] | .87 |
| 0.30 | 15 | 84 / 66 | 18 (7.6) [3, 33] | .67 |
| 0.35 | 30 | 79 / 70 | 9 (6.3) [−2, 22] | .47 |
| 0.40 | 30 | 68 / 73 | −5 (5.5) [−15, 7] | .27 |
| 0.45 | 30 | 66 / 73 | −7 (5.3) [−17, 3] | .27 |
| 0.50 | 15 | 55 / 74 | −19 (8.3) [−33, −1] | .13 |
| 0.60 | 30 | 47 / 80 | −33 (4.3) [−41, −24] | .07 |
| 0.66 | 15 | 69 / 82 | −13 (12.2) [−36, 12] | .27 |

*Notes:* Paired replications as shown; SE and 95% percentile bootstrap intervals of paired differences. P(C > D) is the share of replications in which concentrated seeding produced more adopters. The β = 0 row uses the first 15 replications of the base configuration. The value at β = 0.66, the SAGraph point estimate, is imprecise for final adopters and less negative than at 0.60 because of the heavy right tail of concentrated outcomes with 15 replications. C = concentrated; D = distributed.

**Table 7. Discounted Reach and Downside Risk Favor Distributed Seeding at Lower Elasticities Than Final Adopters Do**

| β | Δ V(δ = 1/hour) (SE) [95% CI] | CVaR~0.2~ (C / D) | Adopters at 1 h (C / D) |
|---|---|---|---|
| 0.00 | 18.2 (1.9) [14.4, 21.9] | 108 / 42 | 37 / 18 |
| 0.05 | 17.1 (1.9) [13.3, 20.6] | 95 / 38 | 34 / 16 |
| 0.10 | 11.5 (1.3) [8.7, 14.2] | 83 / 45 | 31 / 20 |
| 0.15 | 7.8 (2.2) [3.7, 12.5] | 76 / 48 | 26 / 21 |
| 0.20 | 3.2 (1.6) [0.0, 6.4] | 74 / 49 | 24 / 20 |
| 0.25 | 1.3 (1.1) [−0.9, 3.5] | 64 / 55 | 22 / 22 |
| 0.30 | −1.8 (1.6) [−5.0, 1.3] | 57 / 54 | 20 / 23 |
| 0.35 | −5.0 (0.9) [−6.7, −3.2] | 48 / 59 | 16 / 24 |
| 0.40 | −6.2 (0.9) [−7.9, −4.4] | 41 / 59 | 14 / 22 |
| 0.45 | −8.8 (1.0) [−10.6, −6.9] | 35 / 61 | 13 / 24 |
| 0.50 | −11.6 (1.2) [−13.9, −9.2] | 33 / 59 | 11 / 25 |
| 0.60 | −13.2 (0.9) [−14.9, −11.5] | 27 / 60 | 9 / 25 |
| 0.66 | −14.2 (0.8) [−15.8, −12.7] | 28 / 71 | 9 / 26 |

*Notes:* Same replications as Table 6. ΔV is the paired difference (concentrated minus distributed) in discounted reach at δ = 1 per hour; SE and 95% bootstrap intervals. CVaR~0.2~ is the mean of the worst 20% of replications. C = concentrated; D = distributed.


![Figure 2. The Advantage of Concentrated Seeding Disappears at Moderate Engagement Elasticities. Notes: Paired difference (concentrated minus distributed) in final adopters and in discounted reach at δ = 1 per hour, by engagement elasticity. Bars are 95% bootstrap intervals.](figures/Figure_2.png){width=5.2in}

Two thresholds therefore bound a band, roughly 0.3 < β < 0.5 in this configuration, in which a genuine trade-off exists: concentration offers more adopters in expectation, with a long right tail, while distribution reaches more people early and protects against poor outcomes. Inside this band, and only inside it, the choice depends on the manager's attention half-life and risk aversion, and the critical δ^\*^ and ρ^\*^ defined under Decision Criteria are well defined. Below the band (roughly β ≤ 0.2) concentration is better on every criterion, and above it (from about 0.5) distribution is, whatever the manager's preferences. The thresholds are not sharp, because the intervals overlap zero around them. Conjecture 3 is supported.

The first-generation argument under Exposure and the Engagement Elasticity accounts for the location of these thresholds approximately. With three concentrated seeds sharing about 1,000 followers, f~C~ ≈ 335, so distributed seeding gains a first-generation advantage of about 33.5^β^. Because the two plans were not tied after one hour at β = 0 (the ratio of distributed to concentrated adopters at one hour was 0.47), the factor should govern the change in this ratio rather than its level. It predicts that the ratio rises by a factor of 2.9 at β = 0.3 and 5.8 at β = 0.5; the observed rises were 2.5 (1.16 / 0.47) and 4.8 (2.24 / 0.47), that is, about 80 to 85 percent of the predicted shift. With R~0~ = 152/50 ≈ 3.03 from the base configuration, Equation 2 predicts that final reach reverses near β^\*^ ≈ ln 3.03 / ln 33.5 ≈ 0.32; the point estimate of the difference changes sign between 0.35 and 0.40, so the heuristic is close but slightly low. Because early adoption depends on first-generation exposures alone, whereas final reach also reflects the downstream advantage R~0~, discounted reach and downside risk reverse earlier than final reach, as Conjecture 3 states. The approximation is heuristic, since it treats seeds as having the mean audience size and ignores the effect of β on downstream spread, but it shows that the thresholds follow from the attention mechanism rather than from incidental features of the simulation.

# Estimating the Engagement Elasticity on Platform Data

The elasticity experiments locate the decision on the engagement elasticity β, so the practical question is where real campaigns lie. We answer it with SAGraph (Zhang et al. 2025), a public dataset released under a CC-BY 4.0 license that covers influencer campaigns for six products on Weibo. For each product it contains anonymized profiles with follower counts and, for each posting account, the comments and reposts that its posts received. The public release contains neither post identifiers nor timestamps, so we define a post as a unique pair of author and post text, and we cannot calibrate timing. Posting accounts range from no followers to about 240 million, so the data cover the small accounts that make up distributed seeding as well as large influencers. Web Appendix B validates the estimator on synthetic data with known parameters, and the estimation code is included in the supplementary archive.

*Estimator.* If the expected number of interactions on a post by author a is proportional to f~a~^1-β^, then interactions per follower scale as f~a~^-β^, which matches the role of β in Equation 1. We estimate

$$
E[y_p \mid f_a, \text{product}] = \exp(\alpha_{\text{product}} + \theta \ln f_a), \quad \hat\beta = 1 - \hat\theta \qquad (6)
$$

where y~p~ is the number of comments and reposts on post p, by Poisson pseudo-maximum likelihood (PPML) with product fixed effects and standard errors clustered by author. PPML is consistent under heteroskedasticity (Santos Silva and Tenreyro 2006), whereas ordinary least squares on ln(1 + y~p~) is biased when counts are small; on synthetic data with a true β of 0.35 it returned 0.83, against 0.35 [0.26, 0.43] for PPML (Web Appendix B). SAGraph, however, contains only posts that received at least one interaction, so we also estimate Equation 6 as a zero-truncated Poisson (ZTP) model, which conditions on y~p~ ≥ 1. The main sample excludes accounts with fewer than 10 followers, consistent with the floor in Equation 1. Equation 6 is a descriptive scaling relation, not a causal effect of audience size; we discuss its interpretation below.

*Results.* Table 8 reports the estimates. Pooled over the six products, β̂ = 0.66 (95% CI [0.63, 0.68]). Every product-level estimate lies between 0.52 and 0.75, every product-level interval excludes 0.3, and five of the six exclude 0.5 (the exception is ruby_face_cream, 0.52 [0.46, 0.58]). The estimates were similar under the ZTP model (0.63), when only comments were counted (0.74), and when accounts with fewer than 10 followers were included with f set to 10 (0.72). Estimated by audience size, the elasticity was 0.74 [0.62, 0.86] for accounts with 10^3^ to 10^5^ followers and 0.57 [0.49, 0.65] for accounts with at least 10^5^ followers. Product-level estimates for the largest accounts are imprecise because few such accounts post in some campaigns; for ruby_face_cream, with 135 large accounts, the interval is [0.08, 0.65]. Some accounts appear in several campaigns; merging likely matches across products (identical description and following count and the same order of magnitude of followers) into common clusters left the pooled interval essentially unchanged ([0.63, 0.68]).

**Table 8. Engagement Elasticity Estimates on SAGraph Are Well Above Zero in Every Campaign**

| Sample | Posts | Authors | β̂ PPML (SE) [95% CI] | β̂ ZTP (SE) [95% CI] |
|---|---|---|---|---|
| abc_reading | 61,692 | 8,332 | 0.70 (0.033) [0.63, 0.76] | 0.66 (0.039) [0.58, 0.74] |
| electric_toothbrush | 5,804 | 2,353 | 0.65 (0.021) [0.61, 0.69] | 0.64 (0.022) [0.60, 0.69] |
| intelligent_floor_scrubber | 49,975 | 6,965 | 0.60 (0.033) [0.54, 0.67] | 0.54 (0.039) [0.47, 0.62] |
| ruby_face_cream | 9,924 | 4,451 | 0.52 (0.032) [0.46, 0.58] | 0.47 (0.043) [0.38, 0.55] |
| spark_thinking | 65,576 | 8,561 | 0.75 (0.024) [0.70, 0.80] | 0.73 (0.027) [0.67, 0.78] |
| supor_boosted_showerhead | 16,919 | 7,617 | 0.60 (0.033) [0.53, 0.66] | 0.57 (0.037) [0.50, 0.64] |
| Pooled, all accounts (f ≥ 10) | 209,890 | 38,279 | 0.66 (0.012) [0.63, 0.68] | 0.63 (0.014) [0.60, 0.65] |
| Pooled, 10^3^ ≤ f < 10^5^ | 72,960 | 11,760 | 0.74 (0.060) [0.62, 0.86] | 0.67 (0.074) [0.52, 0.82] |
| Pooled, f ≥ 10^5^ | 86,588 | 4,939 | 0.57 (0.042) [0.49, 0.65] | 0.57 (0.042) [0.49, 0.65] |

*Notes:* A post is a unique pair of author and post text; y~p~ counts comments and reposts; standard errors (SE) are clustered by author within campaign. Pooled rows include campaign fixed effects. PPML = Poisson pseudo-maximum likelihood; ZTP = zero-truncated Poisson. The z statistics for β = 0 exceed 15 in every row listed (exact p-values are below .001). Merging accounts that appear in several campaigns into common clusters changes the pooled interval by less than .01.


The pooled estimate and all product-level estimates exceed the thresholds from the elasticity experiments at which the ranking reversed on discounted reach and downside risk (about 0.3), and the pooled estimate exceeds the range in which expected final reach reverses (0.4 to 0.5). The estimate for the largest accounts (0.57 [0.49, 0.65]) and the interval for ruby_face_cream overlap that range. Within the simulated configuration, the observed campaigns therefore fall in the region where distributed seeding is better on discounted reach and downside risk and not worse on final reach, and the constant-attention assumption of the base configuration is not supported by these data. For the smallest accounts (10 to 10^3^ followers), interactions per post barely vary with audience size (β̂ = 1.02), but we do not interpret this estimate, because such accounts enter the data only when one of their posts received an interaction, which inflates their measured engagement.

*Interpretation and scope.* Three features of the data bias β̂ upward. First, accounts enter SAGraph only if their posts received interactions; the ZTP model corrects for truncation at the post level but not for this selection of accounts, which inflates the measured engagement of small accounts. Second, the largest number of comments recorded on a single post ranges from 579 to 963 across products, which is low for accounts with millions of followers and suggests that comments were collected up to a limit per post; this understates the response to large accounts. Third, purchased or inactive followers inflate the follower counts of large accounts. The true elasticity may therefore be lower than our estimates, although the bias would have to be large to bring it to 0.3, the level at which discounted reach and downside risk reverse: about 0.36, more than half of the pooled estimate. A bias of 0.16 would suffice to bring it to 0.5, where final reach clearly favors distribution, so the conclusion for final reach is less secure than the conclusion for discounted reach and downside risk. In addition, β̂ measures engagement, which combines seeing a post with choosing to respond, whereas Equation 1 concerns exposure alone; and because large and small accounts differ in content, audience composition, and campaign role, β̂ describes how engagement scales across accounts rather than how it would change if a given account gained followers. For the seeding decision the cross-sectional relation is the relevant one, because a manager chooses among existing accounts, but the estimate should not be read as a causal effect of audience size.

# Discussion

## Implications for Simulation Research in Marketing

The study shows that the recommendation produced by a simulation-based pre-test can depend on components outside the agent model. In our setting, a scale-normalized speed metric created a trade-off that did not exist, a scheduler without stimulus-driven reactivity doubled the absolute differences between plans, and an attention assumption that most simulators make implicitly determined which plan won. This suggests that evaluating such models by the behavioral realism of their agents is not enough; a pre-test should also be checked for whether its recommendations are robust to plausible alternatives for each component that lies between the simulated population and the decision.

The study supports three principles. First, report reach at fixed horizons, discounted reach at a stated attention half-life, downside risk, and dominance relations, and treat scale-normalized timing statistics and variances as descriptive only. Second, report results under at least one alternative scheduling mechanism, because magnitudes that drive threshold decisions are sensitive to it. Third, make the attention model explicit, expose its parameter to the user, and estimate it from platform data, because the constant-attention default builds in a strong advantage for concentrated seeding.

These principles bear on the growing class of simulators built on LLM agents (Gao et al. 2023; Park et al. 2023; Yang et al. 2024; Zhang et al. 2024), although our simulator contains no language model. The scope of the carry-over differs by result. The metric result is a property of t~50~ and of the decision criteria and holds for any simulator that produces adoption paths. The attention result concerns the exposure rule of the platform environment, which in LLM-agent simulators is typically specified outside the language model, so a constant-visibility rule should be expected to favor concentrated seeding there as well, although how strongly would depend on how LLM agents respond to the content they are shown. The timing result depends on the rule-based urge function and on rule-based action choices, and whether it holds when a language model drives agent behavior is an open empirical question.

## Implications for Research on Seeding

The engagement elasticity offers a boundary condition for the debate between influentials and ordinary users. Studies that found an advantage for hubs (Goldenberg et al. 2009; Hinz et al. 2011) and studies that favored ordinary users (Bakshy et al. 2011; Watts and Dodds 2007) need not conflict if they were conducted in settings with different elasticities. Our results also refine the distinction between acceleration and expansion (Libai, Muller, and Peres 2013): when attention declines with audience size, distributed seeding accelerates adoption at lower elasticities than those at which it expands it, which produces a band in which time preference decides.

Equation 2) suggests a further hypothesis. Thresholds fall as the ratio between influencer and ordinary audiences rises. In our network that ratio was about 34; on platforms where influencers have 10^4^ times as many followers as ordinary users, the same downstream advantage would imply a threshold for final reach of about 0.12. If the downstream advantage of concentration does not grow as fast as the audience ratio, the thresholds in our small network overstate those in real networks, and our conclusion that observed elasticities favor distributed seeding would be strengthened. Testing this requires simulations on networks with realistic audience distributions, which we leave to future work.

## Managerial Implications

A report that one plan is faster because it reaches half of its adopters sooner should prompt the question: faster at reaching how many people? In our base configuration, the plan that looked fast was behind at every hour. A manager who can estimate β for the platform and product category can locate the decision: below roughly 0.25, choose influencers; above roughly 0.5, choose many ordinary users; in between, choose according to the attention window and tolerance for a weak campaign, and consider hybrid portfolios. In the Weibo campaigns we examined, the estimated elasticity lies above the upper threshold, although for the largest accounts and for one product its interval reaches the upper threshold. The exact thresholds belong to this synthetic configuration and should be re-derived with a calibrated simulator before they are applied to a specific campaign, but the structure of the decision, two thresholds and a band, is likely to be more general. Costs matter as well: comparisons at equal follower links ignore the per-account cost of recruiting, briefing, and monitoring hundreds of small accounts, and when such costs or concave pricing were included at β = 0, distributed seeding lost most of its reach. The case for grassroots seeding thus rests on a high engagement elasticity, not on the number of accounts it can reach, and a manager should weigh the two together.

## Limitations and Future Research

The study has several limitations. First, the simulation results come from a synthetic 2,000-agent network with manually set parameters, and the thresholds in the elasticity experiments should be read as properties of this configuration. The audience sizes of the simulated influencers are several orders of magnitude smaller than those of real influencers; the discussion of seeding research argues that this likely makes our thresholds conservative, but the argument rests on a heuristic. Second, the behavioral parameters, including the circadian profile, the persona rates, and the cap on stimulus intensity, have not been calibrated to trace data, because the public campaign data lack timestamps. Third, all agents are rule-based, and the simulator contains no language model. The metric and attention results do not depend on this choice, but the magnitudes in the scheduler, pricing, and elasticity experiments do, and whether they hold in simulators where a language model chooses actions, targets, and content should be tested directly; concurrent evidence suggests that, for timing, the gating mechanism matters more than the behavioral model behind it (Zhang et al. 2026a). Fourth, adoption follows a simple contagion rule in which one exposure can trigger adoption; Beaman et al. (2021) show that seeding recommendations change when adoption requires several exposures, and a threshold rule is a natural extension. Fifth, the elasticity applies to all accounts in the network, not only to seeds, and some cells use 15 replications, which leaves estimates at the largest elasticities imprecise (the non-monotone final-reach difference at β = 0.66 is an example).

The elasticity estimate has limits of its own. It comes from one platform, one country, and six product categories, and the two education products produced higher estimates (0.70 and 0.75) than the household and cosmetic products (0.52 to 0.65). It is a descriptive scaling relation, the known biases in the data push it upward, it measures engagement rather than exposure, and it is identified mainly from accounts with more than 10^3^ followers. Future work should estimate β with impression data that separate exposure from response, with complete interaction counts, with samples that include posts and accounts that received no interactions, and, ideally, with exogenous variation in exposure, and should compare the simulated relation between seed audience and cascade size with observed campaigns.

# Conclusion

Simulation-based pre-tests of seeding plans can mislead through the metric used to compare plans, through the mechanism that sets when simulated users act, and through the assumption about how attention scales with audience size. In our synthetic setting, the familiar trade-off between influencer scale and grassroots speed disappeared once speed was measured as reach over time rather than as time to half of a plan's own total; the timing mechanism roughly doubled the absolute differences between plans; and a moderate engagement elasticity (about 0.3 to 0.5, depending on the criterion) reversed the ranking, at thresholds that a simple limited-attention argument approximately predicts. On six influencer campaigns on Weibo, the estimated elasticity was about 0.66, above the points at which the ranking reversed, although the main biases in the data push the estimate upward. Decision support for seeding should therefore report decision-theoretic criteria, test sensitivity to the timing mechanism, and, above all, make explicit and estimate how attention scales with audience size on the platform at hand.
```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```
# References

Aral, Sinan and Dylan Walker (2012), “Identifying Influential and Susceptible Members of Social Networks,” *Science*, 337 (6092), 337–41.

Argyle, Lisa P., Ethan C. Busby, Nancy Fulda, Joshua R. Gubler, Christopher Rytting, and David Wingate (2023), “Out of One, Many: Using Language Models to Simulate Human Samples,” *Political Analysis*, 31 (3), 337–51.

Bakshy, Eytan, Jake M. Hofman, Winter A. Mason, and Duncan J. Watts (2011), “Everyone's an Influencer: Quantifying Influence on Twitter,” in Proceedings of the Fourth ACM International Conference on Web Search and Data Mining, 65–74.

Ballester, Coralio, Antoni Calvó-Armengol, and Yves Zenou (2006), “Who's Who in Networks. Wanted: The Key Player,” *Econometrica*, 74 (5), 1403–17.

Banerjee, Abhijit, Arun G. Chandrasekhar, Esther Duflo, and Matthew O. Jackson (2013), “The Diffusion of Microfinance,” *Science*, 341 (6144), 1236498.

Bao, Tong and Tung-lung Steven Chang (2014), “Finding Disseminators via Electronic Word of Mouth Message for Effective Marketing Communications,” *Decision Support Systems*, 67, 21–29.

Barabási, Albert-László (2005), “The Origin of Bursts and Heavy Tails in Human Dynamics,” *Nature*, 435 (7039), 207–11.

Barabási, Albert-László and Réka Albert (1999), “Emergence of Scaling in Random Networks,” *Science*, 286 (5439), 509–12.

Beaman, Lori, Ariel BenYishay, Jeremy Magruder, and Ahmed Mushfiq Mobarak (2021), “Can Network Theory-Based Targeting Increase Technology Adoption?,” *American Economic Review*, 111 (6), 1918–43.

Bonabeau, Eric (2002), “Agent-Based Modeling: Methods and Techniques for Simulating Human Systems,” *Proceedings of the National Academy of Sciences*, 99 (Supplement 3), 7280–87.

Brand, James, Ayelet Israeli, and Donald Ngwe (2023), “Using GPT for Market Research,” Harvard Business School Marketing Unit Working Paper No. 23-062, https://doi.org/10.2139/ssrn.4395751.

Crane, Riley and Didier Sornette (2008), “Robust Dynamic Classes Revealed by Measuring the Response Function of a Social System,” *Proceedings of the National Academy of Sciences*, 105 (41), 15649–53.

Davis, Jason P., Kathleen M. Eisenhardt, and Christopher B. Bingham (2007), “Developing Theory Through Simulation Methods,” *Academy of Management Review*, 32 (2), 480–99.

Galeotti, Andrea and Sanjeev Goyal (2009), “Influencing the Influencers: A Theory of Strategic Diffusion,” *The RAND Journal of Economics*, 40 (3), 509–32.

Gao, Chen, Xiaochong Lan, Zhihong Lu, Jinzhu Mao, Jinghua Piao, Huandong Wang, Depeng Jin, and Yong Li (2023), “S³: Social-Network Simulation System with Large Language Model-Empowered Agents,” arXiv preprint, https://doi.org/10.48550/arXiv.2307.14984.

Gilbert, Nigel (2008), *Agent-Based Models*. Sage.

Goldenberg, Jacob, Sangman Han, Donald R. Lehmann, and Jae Weon Hong (2009), “The Role of Hubs in the Adoption Process,” *Journal of Marketing*, 73 (2), 1–13.

Hadar, Josef and William R. Russell (1969), “Rules for Ordering Uncertain Prospects,” *American Economic Review*, 59 (1), 25–34.

Hawkes, Alan G. (1971), “Spectra of Some Self-Exciting and Mutually Exciting Point Processes,” *Biometrika*, 58 (1), 83–90.

He, Saike, Weiguang Zhang, Jun Luo, Peijie Zhang, Kang Zhao, and Daniel Dajun Zeng (2024), “Modeling the Co-Diffusion of Competing Memes in Online Social Networks,” *Decision Support Systems*, 187, 114324.

Hinz, Oliver, Bernd Skiera, Christian Barrot, and Jan U. Becker (2011), “Seeding Strategies for Viral Marketing: An Empirical Comparison,” *Journal of Marketing*, 75 (6), 55–71.

Hodas, Nathan O. and Kristina Lerman (2014), “The Simple Rules of Social Contagion,” *Scientific Reports*, 4, 4343.

Horton, John J. (2023), “Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus?,” NBER Working Paper No. 31122, https://doi.org/10.3386/w31122.

Kempe, David, Jon Kleinberg, and Éva Tardos (2003), “Maximizing the Spread of Influence Through a Social Network,” in Proceedings of the Ninth ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 137–46.

Leung, Fine F., Flora F. Gu, Yiwei Li, Jonathan Z. Zhang, and Robert W. Palmatier (2022), “Influencer Marketing Effectiveness,” *Journal of Marketing*, 86 (6), 93–115.

Lewis, Peter A. W. and Gerald S. Shedler (1979), “Simulation of Nonhomogeneous Poisson Processes by Thinning,” *Naval Research Logistics Quarterly*, 26 (3), 403–13.

Li, Feng and Timon C. Du (2011), “Who Is Talking? An Ontology-Based Opinion Leader Identification Framework for Word-of-Mouth Marketing in Online Social Blogs,” *Decision Support Systems*, 51 (1), 190–97.

Libai, Barak, Eitan Muller, and Renana Peres (2013), “Decomposing the Value of Word-of-Mouth Seeding Programs: Acceleration versus Expansion,” *Journal of Marketing Research*, 50 (2), 161–76.

Malmgren, R. Dean, Daniel B. Stouffer, Adilson E. Motter, and Luís A. N. Amaral (2008), “A Poissonian Explanation for Heavy Tails in E-Mail Communication,” *Proceedings of the National Academy of Sciences*, 105 (47), 18153–58.

Markowitz, Harry (1952), “Portfolio Selection,” *The Journal of Finance*, 7 (1), 77–91.

Miao, Siqi, Ziyang Chen, Yuhong Luo, Hans Hao-Hsun Hsu, Mufei Li, Kaiqing Zhang, and Pan Li (2026), “Can LLM Agents Simulate Dynamic Networks? A Case Study on Email Networks with Phishing Synthesis,” arXiv preprint, https://doi.org/10.48550/arXiv.2605.12507.

Ogata, Yosihiko (1981), “On Lewis' Simulation Method for Point Processes,” *IEEE Transactions on Information Theory*, 27 (1), 23–31.

Park, Joon Sung, Joseph C. O'Brien, Carrie J. Cai, Meredith Ringel Morris, Percy Liang, and Michael S. Bernstein (2023), “Generative Agents: Interactive Simulacra of Human Behavior,” in Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology.

Piao, Jinghua, Yuwei Yan, Jun Zhang, Nian Li, Junbo Yan, Xiaochong Lan, Zhihong Lu, Zhiheng Zheng, Jing Yi Wang, Di Zhou, Chen Gao, Fengli Xu, Fang Zhang, Ke Rong, Jun Su, and Yong Li (2025), “AgentSociety: Large-Scale Simulation of LLM-Driven Generative Agents Advances Understanding of Human Behaviors and Society,” arXiv preprint, https://doi.org/10.48550/arXiv.2502.08691.

Rand, William and Roland T. Rust (2011), “Agent-Based Modeling in Marketing: Guidelines for Rigor,” *International Journal of Research in Marketing*, 28 (3), 181–93.

Rockafellar, R. Tyrrell and Stanislav Uryasev (2000), “Optimization of Conditional Value-at-Risk,” *The Journal of Risk*, 2 (3), 21–41.

Santos Silva, João M. C. and Silvana Tenreyro (2006), “The Log of Gravity,” *Review of Economics and Statistics*, 88 (4), 641–58.

Schramm, Mary E., Kevin J. Trainor, Murali Shanker, and Michael Y. Hu (2010), “An Agent-Based Diffusion Model with Consumer and Brand Agents,” *Decision Support Systems*, 50 (1), 234–42.

Simon, Herbert A. (1971), “Designing Organizations for an Information-Rich World,” in *Computers, Communications, and the Public Interest*, Martin Greenberger, ed. Johns Hopkins Press, 37–72.

Törnberg, Petter, Diliara Valeeva, Justus Uitermark, and Christopher Bail (2023), “Simulating Social Media Using Large Language Models to Evaluate Alternative News Feed Algorithms,” arXiv preprint, https://doi.org/10.48550/arXiv.2310.05984.

Watts, Duncan J. and Peter Sheridan Dodds (2007), “Influentials, Networks, and Public Opinion Formation,” *Journal of Consumer Research*, 34 (4), 441–58.

Weng, Lilian, Alessandro Flammini, Alessandro Vespignani, and Filippo Menczer (2012), “Competition Among Memes in a World with Limited Attention,” *Scientific Reports*, 2, 335.

Wies, Simone, Alexander Bleier, and Alexander Edeling (2023), “Finding Goldilocks Influencers: How Follower Count Drives Social Media Engagement,” *Journal of Marketing*, 87 (3), 383–405.

Yang, Ziyi, Zaibin Zhang, Zirui Zheng, Yuxian Jiang, Ziyue Gan, Zhiyu Wang, Zijian Ling, Jinsong Chen, Martz Ma, Bowen Dong, Prateek Gupta, Shuyue Hu, Zhenfei Yin, Guohao Li, Xu Jia, Lijun Wang, Bernard Ghanem, Huchuan Lu, Chaochao Lu, Wanli Ouyang, Yu Qiao, Philip Torr, and Jing Shao (2024), “OASIS: Open Agent Social Interaction Simulations with One Million Agents,” arXiv preprint, https://doi.org/10.48550/arXiv.2411.11581.

Zhang, Anping, Yang Tan, Yuanbo Tang, Huaze Tang, Qiuhua Ye, Marta C. Gonzalez, and Yang Li (2026a), “Toward Temporal Realism in City-Scale Crisis Response Simulation Using LLM Agents,” arXiv preprint, https://doi.org/10.48550/arXiv.2606.19904.

Zhang, Xiaoqing, Xiuying Chen, Yuhan Liu, Jianzhou Wang, Zhenxing Hu, and Rui Yan (2024), “A Large-Scale Time-Aware Agents Simulation for Influencer Selection in Digital Advertising Campaigns,” arXiv preprint, https://doi.org/10.48550/arXiv.2411.01143.

Zhang, Xiaoqing, Yuhan Liu, Jianzhou Wang, Zhenxing Hu, Xiuying Chen, and Rui Yan (2025), “SAGraph: A Large-Scale Social Graph Dataset with Comprehensive Context for Influencer Selection in Marketing,” in Proceedings of the 48th International ACM SIGIR Conference on Research and Development in Information Retrieval, 3733–42, https://doi.org/10.1145/3726302.3730334.

Zhang, Yongmao, Kai Qiao, Zhengyan Wang, Ningning Liang, Dekui Ma, Wenyao Sun, Jian Chen, and Bin Yan (2026b), “POSIM: A Multi-Agent Simulation Framework for Social Media Public Opinion Evolution and Governance,” arXiv preprint, https://doi.org/10.48550/arXiv.2603.23884.

Zhao, Qingyuan, Murat A. Erdogdu, Hera Y. He, Anand Rajaraman, and Jure Leskovec (2015), “SEISMIC: A Self-Exciting Point Process Model for Predicting Tweet Popularity,” in Proceedings of the 21st ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 1513–22.
