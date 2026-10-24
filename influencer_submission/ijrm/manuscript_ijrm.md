---
title: "Do Influencers Pay? Limited Attention, Engagement Elasticity, and Simulation-Based Pre-Tests for Seeding Decisions"
---

**Abstract**

Marketers pre-test influencer campaigns in agent-based simulators before choosing between a few influencers and many ordinary users. We show that the recommendation depends on three modeling choices separate from agent realism: the metric used to compare plans, the mechanism that schedules agent actions, and the assumed relation between an account's audience size and follower attention, summarized as an engagement elasticity β. In an event-driven simulator, concentrated seeding dominated at every hour and quantile under constant attention (β = 0); the scale-versus-speed trade-off implied by time to half of a plan's own adopters was an artifact of normalization. Alternative schedulers roughly doubled absolute differences between plans. The ranking reversed near β = 0.1 for discounted reach and downside risk and near 0.2 to 0.3 for expected reach. On 209,890 Weibo posts, β is 0.66 (95% CI 0.63 to 0.68), above both thresholds, although data biases push it upward.

**Keywords:** influencer marketing; seeding; limited attention; agent-based simulation; stochastic dominance; engagement

# 1. Introduction

How to allocate a seeding budget is one of the most basic decisions in digital marketing: place the message with a few prominent accounts, or spread the same budget across many ordinary users (Hinz et al. 2011, Leung et al. 2022). Field experiments on this choice are expensive, can disturb the communities under study, and are hard to repeat, so marketing managers and agencies narrow their options with model-based pre-tests before committing budget. Agent-based simulation has long served this purpose (Bonabeau 2002, Rand and Rust 2011), and generative AI has renewed its appeal: agents driven by large language models (LLMs) can be given personas and can react to natural-language content, so that a simulated platform populated by such agents promises a synthetic audience on which campaigns can be tried before launch (Park et al. 2023, Argyle et al. 2023, Horton 2023, Zhang et al. 2024).

Most of the discussion of such simulators in marketing, from the guidelines for rigor in agent-based marketing models (Rand and Rust 2011) to the current work on LLM agents, asks whether the simulated agents behave realistically. That question is necessary but not sufficient. A pre-test is useful only if it ranks the options correctly, and the ranking depends on modeling choices that are logically separate from behavioral fidelity: how the simulator summarizes outcomes, how it decides when simulated users act, and what it assumes about the platform environment in which they act. This paper examines three such choices and shows that each can change what a manager is told.

The first is the decision metric. Simulation studies of seeding often report the final number of adopters together with a speed measure such as the time to reach half of the eventual adopters. Such a measure is normalized by the cascade's own size, so a plan that produces a small cascade can appear fast simply because it finishes early. The marketing literature distinguishes the value of accelerating adoption from the value of expanding it (Libai et al. 2013), but managers with a short attention window do not care when a campaign reaches half of its own total; they care how many people it has reached by a given time. Decision theory supplies criteria that respect this distinction: discounted value for time preference, certainty equivalents and downside risk measures for risk preference, and stochastic dominance for robustness to both (Markowitz 1952, Hadar and Russell 1969, Rockafellar and Uryasev 2000).

The second is the timing mechanism. Many LLM-agent simulators advance in rounds and query agents on a schedule, while some add hourly activation profiles (Yang et al. 2024). Empirical activity is circadian, bursty, and responsive to triggers (Barabási 2005, Malmgren et al. 2008, Crane and Sornette 2008), and concurrent work has begun to gate LLM agents with self-exciting point processes (Miao et al. 2026, Zhang et al. 2026a, 2026b). These studies evaluate whether simulated timing looks realistic. None asks whether the timing assumption changes a managerial decision.

The third is the attention model. Theories of limited attention hold that attention, not information, is the scarce resource in information-rich environments (Simon 1971), and that on social platforms the attention a user devotes to any one source falls as the number of sources competing for it rises (Weng et al. 2012, Hodas and Lerman 2014). Followers of large accounts tend to follow many other accounts, have weaker ties to the author, and encounter its posts among more competing content, so the attention an account commands per follower should decline with its audience size. Studies of influencer campaigns are consistent with this view (Wies et al. 2023), yet simulators typically assume that every follower is equally likely to see a post. We formalize the relation as an engagement elasticity β and argue that it, more than the behavioral richness of the agents, is the parameter on which the seeding decision turns.

We study these choices with an event-driven simulator in which each agent's action times are drawn from an inhomogeneous Poisson process whose intensity combines a persona-specific circadian baseline with decaying stimuli from content exposure and feedback. The agents are rule-based throughout; the simulator contains no language model, and Section 7 discusses which results carry over to LLM-agent simulators. We ask four questions. RQ1: Under decision-theoretic criteria, is there a trade-off between concentrated and distributed seeding at all? RQ2: Does the timing mechanism change the ranking or the size of the differences? RQ3: How do realistic seed pricing and hybrid portfolios change the comparison? RQ4: How does the answer depend on the engagement elasticity, and where do real campaigns lie?

The paper makes three contributions. First, to research on agent-based modeling in marketing, it shows that choices outside the agent model can reverse or distort a recommendation, and it derives three principles for pre-tests: report reach at fixed horizons and dominance relations rather than scale-normalized timing; test sensitivity to the scheduling mechanism; and make the attention model explicit and estimable. In our base configuration a scale-normalized speed metric manufactured a trade-off where none existed, and alternative schedulers roughly doubled the absolute differences between plans. Second, to research on seeding and influencer marketing, it identifies the engagement elasticity as a boundary condition on the long-standing debate between influentials and ordinary users (Watts and Dodds 2007, Goldenberg et al. 2009, Hinz et al. 2011, Bakshy et al. 2011). The ranking reverses at modest elasticities, with thresholds that differ by criterion and enclose a band in which the manager's time and risk preferences decide, and a first-generation exposure argument predicts where the threshold on final reach lies. Third, it converts a qualitative debate into an estimable quantity and estimates it: on six influencer campaigns on Weibo, the elasticity was about 0.66, well above the thresholds. Because the simulation results come from a synthetic population and the estimate is associational and subject to the upward biases discussed in Section 6, we present the conclusions as theory-grounded hypotheses for field testing rather than as prescriptions.

Section 2 reviews the background. Section 3 sets out the framework: the exposure model, the decision criteria, and our conjectures. Section 4 describes the simulator, Section 5 reports the experiments, Section 6 estimates the elasticity, Section 7 discusses implications and limitations, and Section 8 concludes.

# 2. Background

## 2.1 Seeding: Influentials, Ordinary Users, and the Value of Acceleration

Influence maximization asks for the seed set that maximizes expected spread (Kempe et al. 2003). The influentials hypothesis holds that a few highly connected individuals drive diffusion, whereas Watts and Dodds (2007) argued that large cascades are driven at least as often by many easily influenced ordinary users. Empirical evidence is mixed. Goldenberg et al. (2009) and Hinz et al. (2011) found that seeding well-connected hubs speeds and widens adoption, whereas Bakshy et al. (2011) found that targeting ordinary users can be more cost-effective once costs are considered. Field experiments have separated influence from susceptibility (Aral and Walker 2012) and shown that network-based seeding raises adoption when adoption requires several exposures (Beaman et al. 2021). Economists have studied the same question as a targeting problem (Ballester et al. 2006, Galeotti and Goyal 2009, Banerjee et al. 2013). Related work has used simulation and network analytics to support social media decisions, for example by identifying opinion leaders and message disseminators (Li and Du 2011, Bao and Chang 2014), modeling diffusion with consumer and brand agents (Schramm et al. 2010), and modeling the co-diffusion of competing memes (He et al. 2024).

Two features of this literature matter here. First, it mostly evaluates expected final adoption, or adoption speed measured relative to a campaign's own scale; Libai et al. (2013) show that the value of a seeding program depends on whether it accelerates adoption that would otherwise occur later or expands the set of adopters, but decision criteria that combine time and risk preferences have rarely been applied to the comparison. Second, the debate has not identified a single market parameter that determines which side is right in a given setting. We argue that limited attention supplies one.

## 2.2 Simulation-Based Pre-Tests

Agent-based modeling studies outcomes that emerge from the interaction of heterogeneous actors (Bonabeau 2002, Gilbert 2008), and simulation is an established method for developing theory about such systems (Davis et al. 2007). In marketing, the credibility of agent-based models rests on careful specification and validation (Rand and Rust 2011). Generative AI has changed what such models can contain: LLM-based agents replace hand-coded rules with a generative model conditioned on a persona and observations (Park et al. 2023), language models can reproduce response distributions of human subpopulations (Argyle et al. 2023) and behave like simulated economic agents (Horton 2023, Brand et al. 2023), and social-network simulators have been built on these ideas (Gao et al. 2023, Törnberg et al. 2023, Zhang et al. 2024, Piao et al. 2025). The evaluation of these models has focused on behavioral fidelity. From a decision-analytic perspective, however, the relevant quality of a pre-test is the quality of the decision it supports, and that depends on every component that lies between the simulated population and the recommendation. We focus on three such components and ask whether each changes the recommendation, holding the agent model fixed. Our agents are rule-based, but the three components we study are present in any agent-based pre-test, including those built on LLM agents.

## 2.3 Timing of Action

A temporal point process describes events through a conditional intensity $\lambda(t)$. Human communication is non-stationary, with strong daily cycles, and bursty, with heavy-tailed inter-event times (Barabási 2005); Malmgren et al. (2008) showed that a cascading non-homogeneous Poisson mechanism with circadian modulation accounts for much of that heavy tail. In a Hawkes process each event raises the intensity of future events (Hawkes 1971), and self-exciting models describe the popularity of online content (Crane and Sornette 2008, Zhao et al. 2015). Non-homogeneous Poisson processes can be simulated exactly by thinning (Lewis and Shedler 1979, Ogata 1981).

Simulators differ in how they decide when agents act. Early systems advance in synchronous rounds. OASIS (Yang et al. 2024) activates each agent according to a 24-dimensional hourly activity vector, and the time-aware influencer simulator of Zhang et al. (2024) selects active agents from user timelines and content lifecycles; both reproduce daily rhythms but do not let an agent's current situation change when it acts. Concurrent work places a point process in front of the LLM: Miao et al. (2026) fit per-user Hawkes processes to email logs, POSIM (Zhang et al. 2026b) drives an opinion simulator with a circadian-modulated Hawkes engine, and Zhang et al. (2026a) gate LLM agents with a data-calibrated self-excitation channel and show that a gate-only ablation reproduces the timing of the LLM-coupled simulator. These studies judge timing by its realism; we ask whether it changes a decision.

# 3. Framework

## 3.1 Exposure and the Engagement Elasticity

If the probability that a follower of account $a$ sees and responds to its post is proportional to $f_a^{-\beta}$, where $f_a$ is the account's number of followers, then the expected number of responses grows as $f_a^{1-\beta}$. We call $\beta$ the *engagement elasticity*. With $\beta = 0$, every follower is equally likely to see a post, which is the usual simulator assumption; with $\beta > 0$, an influencer's nominal reach overstates its effective reach. In our simulator a follower sees an author's post with probability

$$p_{\text{view}}(a) = 0.5 \cdot \left(\frac{\max\{f_a, 10\}}{10}\right)^{-\beta}, \tag{1}$$

where the floor of 10 followers normalizes the probability for small accounts.

Consider an equal-link budget: a plan that seeds $n$ accounts with about $f$ followers each, $f \ge 10$, uses $nf = B$ follower links. Under (1) its first-generation exposures are $n f\, p_{\text{view}} = 0.5\cdot 10^{\beta} B f^{-\beta}$.

**Proposition 1 (first-generation exposures).** *Under an equal-link budget and exposure rule (1), the number of first-generation exposures is constant in seed size $f$ when $\beta = 0$ and strictly decreasing in $f$ when $\beta > 0$. For plans with seed sizes $f_C > f_D \ge 10$, the ratio of first-generation exposures of the distributed to the concentrated plan equals $(f_C/f_D)^{\beta}$, which is equal to one at $\beta = 0$ and strictly increasing in $\beta$.*

The proposition follows directly from the expression above; it is stylized, because it treats seeds as having a common audience size and ignores feed competition, comment visibility, and later generations of spread. It shows how the first-order effect of attention scales: with distributed seeds at the exposure floor and concentrated seeds of about $f_C$ followers, the first-generation ratio shifts in favor of distribution by about $(f_C/10)^{\beta}$. Concentration may enjoy other advantages, for example because the audiences of large accounts are themselves well connected. Let $R_0$ denote the ratio of final reach under concentration and distribution when $\beta = 0$. If $\beta$ acts mainly through first-generation exposure and leaves this downstream advantage roughly intact, final reach reverses where the two effects offset each other:

$$\beta^{*} \approx \frac{\ln R_0}{\ln(f_C/10)}. \tag{2}$$

Early adopters are dominated by first-generation exposures, whereas final reach also reflects downstream amplification, so criteria that weight early adoption should reverse first. Equation (2) also implies that thresholds fall as the ratio between influencer and ordinary audiences rises, a point we return to in Section 7. We treat (2) as a heuristic that organizes the simulation results, not as a derived result.

## 3.2 Decision Criteria

Let $N(t)$ be the cumulative number of adopters $t$ hours after the campaign is injected, where an agent adopts when it first comments on or retweets campaign content, and let $N = N(48)$ be the final count. A seeding plan induces a distribution of the path $N(\cdot)$ over replications. We compare plans with four criteria, each tied to a property of the manager's preferences.

*Time preference.* If the value of an adopter decays with the time it takes to reach them at rate $\delta$ per hour, the value of a campaign is the discounted reach

$$V(\delta) = \int_0^{48} \exp(-\delta t)\, dN(t), \tag{3}$$

which equals final reach at $\delta = 0$ and rewards early adoption as $\delta$ grows; $\ln 2/\delta$ is the half-life of attention. A trade-off between scale and speed exists only if the ranking of two plans on $E[V(\delta)]$ changes at some critical $\delta^{*}$.

*Risk preference.* For a decision maker with constant absolute risk aversion $\rho$, the certainty equivalent of a plan is $CE(\rho) = -(1/\rho)\ln E[\exp(-\rho N)]$, computed from the empirical distribution. A risk–return trade-off exists only if the ranking on $CE$ changes at some critical $\rho^{*}$. Because the standard deviation penalizes favorable as well as unfavorable outcomes, we also report the conditional value at risk $CVaR_{0.2}$, the mean of the worst 20% of replications (Rockafellar and Uryasev 2000).

*Robustness.* Plan A first-order stochastically dominates plan B if every quantile of $N$ under A is at least as large as under B, in which case every decision maker who prefers more adopters prefers A, whatever their risk attitude (Hadar and Russell 1969). The analogous pathwise statement for time preference is that $E[N(t)]$ under A exceeds $E[N(t)]$ under B at every $t$, which implies $E[V_A(\delta)] > E[V_B(\delta)]$ for every $\delta$.

*Why scale-normalized speed misleads.* A common speed metric is $t_{50}$, the time at which a run reaches half of its own final count. Because $t_{50}$ is invariant to the scale of $N(\cdot)$, a plan can have a smaller $t_{50}$ and yet have fewer adopters than its competitor at every point in time. Such a plan is faster in shape but slower in reach, and a manager who acts on $t_{50}$ may choose it in exactly the situations, short attention windows, where it is worse. We report $t_{50}$ only to connect with prior practice and to test Conjecture 1.

*Cost.* To examine RQ3 we price a seed with $f$ followers at $C(f) = c_0 + f^{\gamma}$, where $c_0$ is a fixed per-account cost of contracting and management and $\gamma \le 1$ captures declining prices per follower for larger accounts. The budget equals the cost of the three largest accounts. The equal-link comparison common in the literature corresponds to $c_0 = 0$ and $\gamma = 1$. We also evaluate hybrid portfolios that seed the $k$ largest accounts ($k = 0, 1, 2, 3$) and spend the remaining budget on randomly chosen ordinary accounts.

## 3.3 Conjectures

The preceding arguments lead to three conjectures that we examine in Section 5.

*Conjecture 1 (metric).* When the speed of a plan is measured relative to its own final scale, a pre-test can show a speed advantage for a plan that is behind in cumulative reach at every horizon, and therefore manufacture a trade-off that does not exist under any monotone preference over adopters, time, and risk.

*Conjecture 2 (timing).* Schedulers that omit stimulus-driven reactivity change the magnitude of simulated differences between seeding plans, and hence any decision that turns on a threshold, even when they preserve the ranking.

*Conjecture 3 (attention).* The ranking of concentrated and distributed seeding depends on $\beta$. When $\beta$ is low, concentration is preferred under every monotone preference; when $\beta$ is high, distribution is; in between lies a band in which the choice depends on the manager's time and risk preferences. Criteria that weight early adoption reverse at lower $\beta$ than expected final reach.

# 4. The Simulator

The simulator is designed so that action times are generated by agent state rather than by the simulation clock, and so that its outputs can be evaluated against decision criteria. Parameters not determined by the design are assumptions of this instantiation and are listed in Appendix A.

## 4.1 Platform Environment

The environment maintains a directed follower graph, a store of items (posts, comments, and retweets), and a feed of the 40 most recent items shown to each agent. The follower graph is generated by preferential attachment on in-degree (Barabási and Albert 1999); each new agent follows three existing agents, giving a 2,000-agent network whose three largest accounts have about 900 followers between them. When agent $a$ publishes content, each follower sees it with probability given by (1), with $\beta \ge 0$ the engagement elasticity. With $\beta = 0$ every follower is equally likely to see a post, which is our base configuration. Comments are shown with an additional visibility factor of 0.4. Authors receive a notification when their content is commented on or retweeted. When an agent comments or retweets, it chooses among feed items with probability proportional to its interest in the item's topic and an exponential recency weight with a two-hour time constant.

## 4.2 Persona Agents

Each agent is assigned one of five personas (Table 1) that set its baseline rate, its sensitivity to stimuli, its chronotype, and its action propensities. Baseline rates are multiplied by a mean-one log-normal factor ($\sigma = 0.4$), and chronotypes are perturbed by a normal term ($\sigma = 1.5$ h). Each agent has an interest vector over five topics drawn from a symmetric Dirichlet distribution with concentration 0.4.

**Table 1. Persona Parameters**

| Persona | Share | Base rate $\lambda^0$ (1/h) | Gain $g$ | Peak hour | P(post / comment / retweet / like) |
|---|---|---|---|---|---|
| Early adopter | 15% | 0.45 | 1.3 | 22 | .30 / .20 / .25 / .25 |
| Cynic | 15% | 0.30 | 0.8 | 23 | .20 / .45 / .05 / .30 |
| Trend follower | 25% | 0.40 | 1.2 | 21 | .15 / .15 / .40 / .30 |
| Lurker | 30% | 0.12 | 0.6 | 21 | .05 / .10 / .10 / .75 |
| News junkie | 15% | 0.70 | 1.0 | 20 | .40 / .20 / .20 / .20 |

*Note.* When an agent selects an action that requires a feed item and none is eligible, it posts instead.

## 4.3 Intensity Model and Scheduler

Let $c_i(t)$ be a mean-one daily activity profile for agent $i$ with an evening peak at its chronotype, a smaller midday peak, and a night trough. The conditional intensity is

$$\lambda_i(t) = \lambda_i^0\, c_i(t) + S_i(t), \tag{4}$$

$$S_i(t) = \min\Big\{S_{\max},\ \sum_j \kappa\, g_i\, I_{ij}\, r_{ij}\, \exp(-(t - t_j)/\tau)\Big\}, \tag{5}$$

where $t_j$ is the time of the $j$th stimulus (an exposure or a notification), $I_{ij} \in [0, 5]$ is the urge rating returned by the urge function of Section 4.4, $r_{ij} \in \{0.25, 0.50, 0.75\}$ encodes topical relevance, $g_i$ is the persona gain, $\kappa = 0.16$, $\tau = 1$ h, and $S_{\max} = 3$. Notifications enter with relevance 0.50. The cap keeps the additive intensity finite under this exposure rule; without it the process becomes supercritical in the evening. Next event times are drawn by thinning against the dominating rate $\lambda_i^0 \cdot \max c_i + S_i(t)$, which is valid until the next stimulus because $S_i$ decays; when a new stimulus arrives the pending event is redrawn, which is exact because the Poisson process is memoryless.

## 4.4 The Urge Function

The urge function maps an agent's situation (time of day, emotional state, the number of relevant items seen in the last hour, the relevance of the latest item, and notification status) to a rating in $[0, 5]$ by a fixed rule given in Appendix A. The rating scales how strongly a stimulus raises the agent's intensity; it does not determine when the agent acts, which is set entirely by (4) and (5). Using a transparent rule rather than a learned or generative model makes the experiments reproducible at negligible cost and isolates the effects of metrics, timing, and attention from the behavior of the agents. Because the rating enters the model only through $I_{ij}$ in (5), the architecture would in principle allow a different rating mechanism to be substituted, but we have not implemented or tested an alternative, and all results in this paper are conditional on the rule-based function.

## 4.5 Alternative Schedulers

To examine RQ2 we hold every other component fixed and replace the scheduler with three alternatives that represent common practice: (a) circadian-only activation, an inhomogeneous Poisson process with intensity $\lambda_i^0 c_i(t)$ in which stimuli update feeds but do not change timing, similar in spirit to hourly activation vectors; (b) a homogeneous Poisson process at rate $\lambda_i^0$; and (c) fixed-period polling with period $1/\lambda_i^0$ and random phase. Because stimuli generate a large share of activity under the proposed scheduler, the alternatives would otherwise produce far fewer events. We therefore multiply their baseline rates by 1.77, the ratio of total events under the proposed and circadian-only schedulers in pilot runs without a campaign, so that all schedulers produce similar background activity.

# 5. Experiments and Results

## 5.1 Setup

All experiments used a 2,000-agent network, an 18-hour warm-up, a campaign of one post per seed injected at 18:00 on topic 0 unless stated otherwise, and a 48-hour observation window. Concentrated seeding used the three accounts with the most followers. Distributed seeding drew accounts at random from outside the top 5% by follower count until their total cost reached the budget; under equal-link pricing this required about 430 accounts. Replications were paired: within a replication both plans used the same network, personas, and random seed. We report means, paired differences with 95% percentile bootstrap intervals (4,000 resamples), and the share of replications in which concentrated seeding produced more adopters. The base and scheduler comparisons used 30 replications per cell, and the remaining experiments 15 to 20. Code and per-run results are provided as an anonymized supplementary archive.

## 5.2 Is There a Scale-Versus-Speed Trade-Off? (RQ1)

Table 2 reports the base configuration ($\beta = 0$, equal-link pricing). Concentrated seeding produced about twice as many adopters as distributed seeding (299 vs. 144; paired difference 155, 95% CI [115, 201]; concentrated ahead in all 30 replications). Distributed seeding reached half of its own adopters 1.13 hours sooner (95% CI [0.91, 1.36]) and had a much smaller standard deviation. On the usual reading this is a trade-off: concentration for scale, distribution for speed and predictability.

**Table 2. Base Configuration ($\beta = 0$, Equal-Link Budget, 30 Paired Replications)**

| | Concentrated (3 seeds) | Distributed (~428 seeds) |
|---|---|---|
| Mean cumulative adopters at 1 h | 56 | 50 |
| at 2 h | 108 | 84 |
| at 3 h | 156 | 106 |
| at 6 h | 248 | 135 |
| at 12 h | 287 | 141 |
| at 48 h (final) | 299 | 144 |
| SD of final adopters | 121 | 24 |
| Minimum of final adopters | 116 | 95 |
| CVaR$_{0.2}$ (mean of worst 20%) | 155 | 113 |
| Mean $t_{50}$ (h) | 2.72 | 1.59 |

The decision criteria of Section 3.2 tell a different story. Concentrated seeding led in mean cumulative adopters at every hour, so its expected discounted reach was higher for every discount rate we evaluated ($\delta$ from 0 to 2 per hour, an attention half-life as short as 21 minutes), and no critical $\delta^{*}$ exists. Its empirical distribution of final adopters lay above that of distributed seeding at every quantile, so it first-order stochastically dominated, and its certainty equivalent was higher for every degree of risk aversion; no critical $\rho^{*}$ exists either. Its worst outcomes were also better: $CVaR_{0.2}$ was 155 against 113, and its minimum 116 against 95. Distributed seeding was more predictable in the sense of a smaller variance, but not in the sense that matters to a risk-averse manager, because its variability was low around a low level, whereas the variability of concentrated seeding came almost entirely from favorable outcomes. Within individual replications, distributed seeding was ahead after one hour in 40% of runs and after two hours in 23%, so its early lead, where present, was small and brief.

The answer to RQ1 is therefore negative for this configuration, and Conjecture 1 is supported: under any monotone preference over adopters, time, and risk, concentrated seeding is the better plan, and the apparent trade-off is produced by the scale-normalized speed metric. Note also that the two plans were nearly tied after one hour (56 vs. 50). Under constant attention the plans create similar numbers of first-generation exposures, and the advantage of concentration arises downstream.

*[Figure 1 here. Mean Cumulative Adopters After Injection. Notes. (a) Base configuration, 15 paired replications shown for comparability with panel (b). (b) Engagement elasticity $\beta = 0.3$.]*

## 5.3 Does the Timing Mechanism Matter? (RQ2)

Table 3 repeats the base comparison under the four schedulers. The direction of every result was unchanged: concentrated seeding produced more adopters, reached a later $t_{50}$, and dominated on $CVaR_{0.2}$ under all four. The magnitudes were not. Under polling, HPP, and circadian-only activation, the absolute scale advantage of concentration was 286 to 340 adopters, roughly twice the 155 obtained under the event-driven scheduler, and the $t_{50}$ gap was 2.6 to 3.0 hours rather than 1.1 hours. In relative terms the difference was smaller: concentrated seeding produced 2.5 to 2.6 times as many adopters as distributed seeding under the alternatives, against 2.1 times under the event-driven scheduler. Part of the absolute difference therefore reflects the larger cascades that the alternative schedulers produced in response to the campaign (478 to 548 adopters for concentrated seeding, against 299), even though volume matching equalized background activity in the absence of a campaign. Circadian-only activation, which reproduces daily rhythms but not reactivity, did not close the gap; the difference lies in the stimulus channel, not the daily profile.

**Table 3. Concentrated Minus Distributed Seeding Under Alternative Schedulers ($\beta = 0$, 18:00 Injection, 30 Paired Replications)**

| Scheduler | Adopters (C / D) | Ratio C/D | $\Delta$ adopters [95% CI] | $\Delta$ $t_{50}$, h [95% CI] | CVaR$_{0.2}$ (C / D) |
|---|---|---|---|---|---|
| Event-driven IPP (proposed) | 299 / 144 | 2.08 | 155 [115, 201] | 1.13 [0.91, 1.36] | 155 / 113 |
| Circadian-only IPP | 548 / 208 | 2.63 | 340 [263, 425] | 2.56 [1.77, 3.51] | 275 / 168 |
| Homogeneous Poisson | 478 / 192 | 2.49 | 286 [222, 359] | 2.94 [2.12, 4.00] | 268 / 160 |
| Fixed-period polling | 484 / 193 | 2.51 | 292 [232, 357] | 2.96 [2.31, 3.73] | 270 / 155 |

*Notes.* Alternative schedulers were volume-matched to the proposed scheduler in the absence of a campaign (Section 4.5). C, concentrated; D, distributed.

The pattern was the same when the campaign was injected at 03:00 or 09:00 (Table 4). Under the event-driven scheduler a night-time injection roughly halved the reach of both plans, because few agents were active to respond, whereas under circadian-only activation the night-time effect appeared mainly as a long delay, with the $t_{50}$ of concentrated seeding stretching to almost ten hours.

**Table 4. Effect of Injection Time (20 Paired Replications per Cell)**

| Injection | Scheduler | Adopters (C / D) | $\Delta$ adopters [95% CI] | $t_{50}$, h (C / D) |
|---|---|---|---|---|
| 03:00 | Event-driven IPP | 172 / 82 | 90 [39, 152] | 3.66 / 2.52 |
| 03:00 | Circadian-only | 471 / 166 | 305 [206, 424] | 9.77 / 5.15 |
| 09:00 | Event-driven IPP | 261 / 122 | 139 [75, 213] | 3.59 / 2.26 |
| 09:00 | Circadian-only | 581 / 215 | 366 [280, 465] | 5.15 / 2.47 |
| 18:00 | Event-driven IPP | 299 / 144 | 155 [115, 201] | 2.72 / 1.59 |
| 18:00 | Circadian-only | 548 / 208 | 340 [263, 425] | 4.23 / 1.67 |

The answer to RQ2 is that, in this configuration, the timing mechanism did not change the ranking but roughly doubled the absolute differences between plans and enlarged the relative difference by about a fifth to a quarter, consistent with Conjecture 2. Where a decision turns on a threshold, for example whether the scale advantage exceeds the cost of contracting influencers, or where the trade-off band of Section 5.5 lies, differences of this size are decision-relevant.

## 5.4 Seed Pricing and Hybrid Portfolios (RQ3)

Table 5 reports hybrid portfolios under three pricing rules. Under equal-link pricing, each additional influencer raised expected reach, $CVaR_{0.2}$, and discounted reach at $\delta = 1$ per hour, and the pure concentrated plan ($k = 3$) was best or tied on every criterion. Under concave pricing ($\gamma = 0.7$) or a fixed per-account fee ($c_0 = 10$ follower-equivalents), the same budget bought only 88 to 102 ordinary accounts, and distributed seeding reached 30 to 35 adopters, about a tenth of concentrated seeding. Pricing therefore strengthens the case for concentration when $\beta = 0$: the equal-link comparison is generous to distributed seeding, because it ignores the per-account costs of working with hundreds of small accounts.

**Table 5. Hybrid Portfolios: $k$ Largest Accounts Plus Ordinary Accounts Filling the Budget ($\beta = 0$, 20 Paired Replications)**

| Pricing $C(f)$ | $k$ | Seeds | Mean adopters (SD) | CVaR$_{0.2}$ | $V(\delta = 1/\text{h})$ | $t_{50}$ (h) |
|---|---|---|---|---|---|---|
| $f$ (equal links) | 0 | 427 | 137 (22) | 110 | 42 | 1.55 |
| | 1 | 260 | 219 (90) | 126 | 48 | 2.28 |
| | 2 | 118 | 282 (113) | 133 | 52 | 2.76 |
| | 3 | 3 | 303 (128) | 156 | 51 | 2.80 |
| $f^{0.7}$ (concave) | 0 | 102 | 35 (6) | 28 | 10 | 1.66 |
| | 1 | 65 | 174 (132) | 74 | 30 | 2.53 |
| | 2 | 32 | 248 (121) | 119 | 42 | 2.76 |
| | 3 | 3 | 303 (128) | 156 | 51 | 2.80 |
| $10 + f$ (fixed fee) | 0 | 88 | 30 (7) | 21 | 9 | 1.53 |
| | 1 | 55 | 179 (112) | 73 | 30 | 2.75 |
| | 2 | 26 | 252 (122) | 126 | 42 | 2.84 |
| | 3 | 3 | 303 (128) | 156 | 51 | 2.80 |

## 5.5 Engagement Elasticity and the Reversal of the Ranking (RQ4)

Sections 5.2 to 5.4 assume constant attention. Table 6 and Figure 2 relax this assumption by varying $\beta$ in (1), which applies to all accounts in the network. The ranking reversed, and it did so at different values of $\beta$ for different criteria. On discounted reach at $\delta = 1$ per hour and on $CVaR_{0.2}$, concentrated seeding lost its advantage near $\beta = 0.1$, and distributed seeding was clearly better from $\beta = 0.15$. On expected final reach, concentrated seeding kept a nominal advantage up to $\beta = 0.25$, although the interval included zero from $\beta = 0.15$, and distributed seeding was clearly better from $\beta = 0.3$. At $\beta = 0.3$, distributed seeding produced more adopters (175 vs. 123), led at every hour (Figure 1(b)), and had better worst-case outcomes ($CVaR_{0.2}$ of 136 vs. 67).

**Table 6. Concentrated vs. Distributed Seeding as a Function of the Engagement Elasticity $\beta$ (Equal-Link Budget, 15 Paired Replications)**

| $\beta$ | Adopters (C / D) | $\Delta$ adopters [95% CI] | P(C > D) | $\Delta V(\delta = 1/\text{h})$ [95% CI] | CVaR$_{0.2}$ (C / D) | Adopters at 1 h (C / D) |
|---|---|---|---|---|---|---|
| 0 | 289 / 133 | 157 [100, 218] | 1.00 | 7.8 [2.2, 14.1] | 147 / 105 | 51 / 49 |
| 0.05 | 283 / 143 | 140 [84, 198] | 0.87 | 6.6 [−1.6, 15.2] | 130 / 107 | 51 / 49 |
| 0.10 | 261 / 144 | 117 [39, 218] | 0.73 | −2.5 [−7.8, 3.7] | 121 / 118 | 41 / 48 |
| 0.15 | 207 / 159 | 49 [−10, 131] | 0.67 | −15.4 [−21.1, −10.8] | 90 / 129 | 32 / 56 |
| 0.20 | 159 / 156 | 2 [−26, 37] | 0.27 | −19.1 [−23.1, −14.7] | 112 / 132 | 30 / 54 |
| 0.25 | 203 / 170 | 33 [−26, 100] | 0.53 | −22.6 [−26.9, −18.7] | 79 / 137 | 29 / 58 |
| 0.30 | 123 / 175 | −52 [−82, −16] | 0.13 | −29.7 [−33.4, −25.4] | 67 / 136 | 23 / 59 |
| 0.50 | 77 / 193 | −116 [−135, −91] | 0.00 | −42.1 [−45.7, −38.6] | 48 / 147 | 13 / 61 |

*Notes.* The $\beta = 0$ row uses the first 15 replications of the base configuration. The nonmonotonic value at $\beta = 0.25$ reflects the heavy right tail of concentrated outcomes with 15 replications.

*[Figure 2 here. Paired Difference (Concentrated Minus Distributed) in Final Adopters and in Discounted Reach at $\delta = 1$ per Hour, by Engagement Elasticity. Note. Bars are 95% bootstrap intervals.]*

Two thresholds therefore bound a band, roughly $0.1 < \beta < 0.25$ in this configuration, in which a genuine trade-off exists: concentration offers more adopters in expectation, with a long right tail, while distribution reaches more people early and protects against poor outcomes. Inside this band, and only inside it, the choice depends on the manager's attention half-life and risk aversion, and the critical $\delta^{*}$ and $\rho^{*}$ of Section 3.2 are well defined. Below the band concentration dominates and above it distribution dominates, whatever the manager's preferences. Conjecture 3 is supported.

The first-generation argument of Section 3.1 accounts for the location of these thresholds. With three concentrated seeds sharing about 900 followers, $f_C \approx 300$, so distributed seeding gains a first-generation advantage of about $30^{\beta}$. At $\beta = 0$, concentration and distribution were nearly tied after one hour (51 vs. 49), so this factor should govern early adoption: it predicts a ratio of distributed to concentrated adopters at one hour of about 2.7 at $\beta = 0.3$ and about 5.3 at $\beta = 0.5$, against observed ratios of 2.6 (59/23) and 4.7 (61/13). With $R_0 = 289/133 \approx 2.17$ from the $\beta = 0$ row, Equation (2) predicts that final reach reverses near $\beta^{*} \approx \ln 2.17 / \ln 30 \approx 0.23$, which lies inside the observed transition between 0.2 and 0.3. Because early adoption depends on first-generation exposures alone, whereas final reach also reflects the downstream advantage $R_0$, discounted reach and downside risk reverse earlier, as Conjecture 3 states. The approximation is heuristic, since it treats seeds as having the mean audience size and ignores the effect of $\beta$ on downstream spread, but it shows that the thresholds follow from the attention mechanism rather than from incidental features of the simulation.

# 6. Estimating the Engagement Elasticity on Platform Data

Section 5.5 locates the decision on the engagement elasticity $\beta$, so the practical question is where real campaigns lie. We answer it with SAGraph (Zhang et al. 2025), a public dataset released under a CC-BY 4.0 license that covers influencer campaigns for six products on Weibo. For each product it contains anonymized profiles with follower counts and, for each posting account, the comments and reposts that its posts received. The public release contains neither post identifiers nor timestamps, so we define a post as a unique pair of author and post text, and we cannot calibrate timing. Posting accounts range from no followers to about 240 million, so the data cover the small accounts that make up distributed seeding as well as large influencers. Appendix B validates the estimator on synthetic data with known parameters, and the estimation code is included in the supplementary archive.

*Estimator.* If the expected number of interactions on a post by author $a$ is proportional to $f_a^{1-\beta}$, then interactions per follower scale as $f_a^{-\beta}$, which matches the role of $\beta$ in (1). We estimate

$$E[y_p \mid f_a, \text{product}] = \exp(\alpha_{\text{product}} + \theta \ln f_a), \qquad \hat\beta = 1 - \hat\theta, \tag{6}$$

where $y_p$ is the number of comments and reposts on post $p$, by Poisson pseudo-maximum likelihood (PPML) with product fixed effects and standard errors clustered by author. PPML is consistent under heteroskedasticity (Santos Silva and Tenreyro 2006), whereas ordinary least squares on $\ln(1 + y_p)$ is biased when counts are small; on synthetic data with a true $\beta$ of 0.35 it returned 0.94, against 0.28 [0.20, 0.37] for PPML (Appendix B). SAGraph, however, contains only posts that received at least one interaction, so we also estimate (6) as a zero-truncated Poisson (ZTP) model, which conditions on $y_p \ge 1$. The main sample excludes accounts with fewer than 10 followers, consistent with the floor in (1). Equation (6) is a descriptive scaling relation, not a causal effect of audience size; we discuss its interpretation below.

*Results.* Table 7 reports the estimates. Pooled over the six products, $\hat\beta = 0.66$ (95% CI [0.63, 0.68]). Every product-level estimate lies between 0.52 and 0.75, and every product-level interval excludes 0.3. The estimates were similar under the ZTP model (0.63), when only comments were counted (0.74), and when accounts with fewer than 10 followers were included with $f$ set to 10 (0.72). Estimated by audience size, the elasticity was 0.74 [0.62, 0.86] for accounts with $10^3$ to $10^5$ followers and 0.57 [0.49, 0.65] for accounts with at least $10^5$ followers. Product-level estimates for the largest accounts are imprecise because few such accounts post in some campaigns; for ruby_face_cream, with 135 large accounts, the interval is [0.08, 0.65]. Some accounts appear in several campaigns; merging likely matches across products (identical description and following count and the same order of magnitude of followers) into common clusters left the pooled interval essentially unchanged ([0.63, 0.68]).

**Table 7. Engagement Elasticity Estimated on SAGraph (Accounts with at Least 10 Followers; Standard Errors Clustered by Author)**

| Sample | Posts | Authors | $\hat\beta$ PPML [95% CI] | $\hat\beta$ ZTP [95% CI] |
|---|---|---|---|---|
| abc_reading | 61,692 | 8,332 | 0.70 [0.63, 0.76] | 0.66 [0.58, 0.74] |
| electric_toothbrush | 5,804 | 2,353 | 0.65 [0.61, 0.69] | 0.64 [0.60, 0.69] |
| intelligent_floor_scrubber | 49,975 | 6,965 | 0.60 [0.54, 0.67] | 0.54 [0.47, 0.62] |
| ruby_face_cream | 9,924 | 4,451 | 0.52 [0.46, 0.58] | 0.47 [0.38, 0.55] |
| spark_thinking | 65,576 | 8,561 | 0.75 [0.70, 0.80] | 0.73 [0.67, 0.78] |
| supor_boosted_showerhead | 16,919 | 7,617 | 0.60 [0.53, 0.66] | 0.57 [0.50, 0.64] |
| Pooled, all accounts ($f \ge 10$) | 209,890 | 38,279 | 0.66 [0.63, 0.68] | 0.63 [0.60, 0.65] |
| Pooled, $10^3 \le f < 10^5$ | 72,960 | 11,760 | 0.74 [0.62, 0.86] | 0.67 [0.52, 0.82] |
| Pooled, $f \ge 10^5$ | 86,588 | 4,939 | 0.57 [0.49, 0.65] | 0.57 [0.49, 0.65] |

*Notes.* A post is a unique pair of author and post text; $y_p$ counts comments and reposts. Pooled rows include product fixed effects. ZTP, zero-truncated Poisson. Merging accounts that appear in several products into common clusters changes the pooled interval by less than 0.01.

All estimates lie well above the thresholds of Section 5.5, at which the ranking reversed on discounted reach and downside risk (about 0.1) and on expected final reach (0.2 to 0.3). Within the simulated configuration, the observed campaigns therefore fall in the region where distributed seeding dominates, and the constant-attention assumption of the base configuration is not supported by these data. For the smallest accounts (10 to $10^3$ followers), interactions per post barely vary with audience size ($\hat\beta = 1.02$), but we do not interpret this estimate, because such accounts enter the data only when one of their posts received an interaction, which inflates their measured engagement.

*Interpretation and scope.* Three features of the data bias $\hat\beta$ upward. First, accounts enter SAGraph only if their posts received interactions; the ZTP model corrects for truncation at the post level but not for this selection of accounts, which inflates the measured engagement of small accounts. Second, the largest number of comments recorded on a single post ranges from 579 to 963 across products, which is low for accounts with millions of followers and suggests that comments were collected up to a limit per post; this understates the response to large accounts. Third, purchased or inactive followers inflate the follower counts of large accounts. The true elasticity may therefore be lower than our estimates, although the bias would have to be large to bring it below 0.3, which is less than half the pooled estimate and well below the lower bound for the largest accounts. In addition, $\hat\beta$ measures engagement, which combines seeing a post with choosing to respond, whereas (1) concerns exposure alone; and because large and small accounts differ in content, audience composition, and campaign role, $\hat\beta$ describes how engagement scales across accounts rather than how it would change if a given account gained followers. For the seeding decision the cross-sectional relation is the relevant one, because a manager chooses among existing accounts, but the estimate should not be read as a causal effect of audience size.

# 7. Discussion

## 7.1 Implications for Simulation Research in Marketing

The study shows that the recommendation produced by a simulation-based pre-test can depend on components outside the agent model. In our setting, a scale-normalized speed metric created a trade-off that did not exist, a scheduler without stimulus-driven reactivity doubled the absolute differences between plans, and an attention assumption that most simulators make implicitly determined which plan won. This suggests that evaluating such models by the behavioral realism of their agents is not enough; a pre-test should also be checked for whether its recommendations are robust to plausible alternatives for each component that lies between the simulated population and the decision.

The study supports three principles. First, report reach at fixed horizons, discounted reach at a stated attention half-life, downside risk, and dominance relations, and treat scale-normalized timing statistics and variances as descriptive only. Second, report results under at least one alternative scheduling mechanism, because magnitudes that drive threshold decisions are sensitive to it. Third, make the attention model explicit, expose its parameter to the user, and estimate it from platform data, because the constant-attention default builds in a strong advantage for concentrated seeding.

These principles bear on the growing class of simulators built on LLM agents (Park et al. 2023, Gao et al. 2023, Yang et al. 2024, Zhang et al. 2024), although our simulator contains no language model. The scope of the carry-over differs by result. The metric result is a property of $t_{50}$ and of the decision criteria and holds for any simulator that produces adoption paths. The attention result concerns the exposure rule of the platform environment, which in LLM-agent simulators is typically specified outside the language model, so a constant-visibility rule should be expected to favor concentrated seeding there as well, although how strongly would depend on how LLM agents respond to the content they are shown. The timing result depends on the rule-based urge function and on rule-based action choices, and whether it holds when a language model drives agent behavior is an open empirical question.

## 7.2 Implications for Research on Seeding

The engagement elasticity offers a boundary condition for the debate between influentials and ordinary users. Studies that found an advantage for hubs (Goldenberg et al. 2009, Hinz et al. 2011) and studies that favored ordinary users (Watts and Dodds 2007, Bakshy et al. 2011) need not conflict if they were conducted in settings with different elasticities. Our results also refine the distinction between acceleration and expansion (Libai et al. 2013): when attention declines with audience size, distributed seeding accelerates adoption at lower elasticities than those at which it expands it, which produces a band in which time preference decides.

Equation (2) suggests a further hypothesis. Thresholds fall as the ratio between influencer and ordinary audiences rises. In our network that ratio was about 30; on platforms where influencers have $10^4$ times as many followers as ordinary users, the same downstream advantage would imply a threshold for final reach below 0.1. If the downstream advantage of concentration does not grow as fast as the audience ratio, the thresholds in our small network overstate those in real networks, and our conclusion that observed elasticities favor distributed seeding would be strengthened. Testing this requires simulations on networks with realistic audience distributions, which we leave to future work.

## 7.3 Managerial Implications

A report that one plan is faster because it reaches half of its adopters sooner should prompt the question: faster at reaching how many people? In our base configuration, the plan that looked fast was behind at every hour. A manager who can estimate $\beta$ for the platform and product category can locate the decision: below roughly 0.1, choose influencers; above roughly 0.25 to 0.3, choose many ordinary users; in between, choose according to the attention window and tolerance for a weak campaign, and consider hybrid portfolios. In the Weibo campaigns we examined, the estimated elasticity lies well above the upper threshold. The exact thresholds belong to this synthetic configuration and should be re-derived with a calibrated simulator before they are applied to a specific campaign, but the structure of the decision, two thresholds and a band, is likely to be more general. Costs matter as well: comparisons at equal follower links ignore the per-account cost of recruiting, briefing, and monitoring hundreds of small accounts, and when such costs or concave pricing were included at $\beta = 0$, distributed seeding lost most of its reach. The case for grassroots seeding thus rests on a high engagement elasticity, not on the number of accounts it can reach, and a manager should weigh the two together.

## 7.4 Limitations and Future Research

The study has several limitations. First, the simulation results come from a synthetic 2,000-agent network with manually set parameters, and the thresholds in Section 5.5 should be read as properties of this configuration. The audience sizes of the simulated influencers are several orders of magnitude smaller than those of real influencers; Section 7.2 argues that this likely makes our thresholds conservative, but the argument rests on a heuristic. Second, the behavioral parameters, including the circadian profile, the persona rates, and the cap on stimulus intensity, have not been calibrated to trace data, because the public campaign data lack timestamps. Third, all agents are rule-based, and the simulator contains no language model. The metric and attention results do not depend on this choice, but the magnitudes in Sections 5.3 to 5.5 do, and whether they hold in simulators where a language model chooses actions, targets, and content should be tested directly; concurrent evidence suggests that, for timing, the gating mechanism matters more than the behavioral model behind it (Zhang et al. 2026a). Fourth, adoption follows a simple contagion rule in which one exposure can trigger adoption; Beaman et al. (2021) show that seeding recommendations change when adoption requires several exposures, and a threshold rule is a natural extension. Fifth, the elasticity applies to all accounts in the network, not only to seeds, and some cells use 15 replications, which leaves the $\beta = 0.25$ estimate noisy.

The elasticity estimate has limits of its own. It comes from one platform, one country, and six product categories, and the two education products produced higher estimates (0.70 and 0.75) than the household and cosmetic products (0.52 to 0.65). It is a descriptive scaling relation, the known biases in the data push it upward, it measures engagement rather than exposure, and it is identified mainly from accounts with more than $10^3$ followers. Future work should estimate $\beta$ with impression data that separate exposure from response, with complete interaction counts, with samples that include posts and accounts that received no interactions, and, ideally, with exogenous variation in exposure, and should compare the simulated relation between seed audience and cascade size with observed campaigns.

# 8. Conclusion

Simulation-based pre-tests of seeding plans can mislead through the metric used to compare plans, through the mechanism that sets when simulated users act, and through the assumption about how attention scales with audience size. In our synthetic setting, the familiar trade-off between influencer scale and grassroots speed disappeared once speed was measured as reach over time rather than as time to half of a plan's own total; the timing mechanism roughly doubled the absolute differences between plans; and a modest engagement elasticity reversed the ranking, at thresholds that a simple limited-attention argument predicts. On six influencer campaigns on Weibo, the estimated elasticity was about 0.66, well above the point at which the ranking reversed, although the main biases in the data push the estimate upward. Decision support for seeding should therefore report decision-theoretic criteria, test sensitivity to the timing mechanism, and, above all, make explicit and estimate how attention scales with audience size on the platform at hand.

**Data availability.** The empirical analysis uses SAGraph (Zhang et al., 2025), a public dataset released under a CC-BY 4.0 license. The simulation code, per-run result files, and estimation scripts are available as an anonymized archive for review [AUTHOR TO COMPLETE: repository link; the journal requires deposit in a data repository and a link, or a statement of why data cannot be shared].

# Declaration of Generative AI and AI-Assisted Technologies in the Manuscript Preparation Process

[AUTHOR TO CONFIRM AND EDIT BEFORE SUBMISSION. Draft based on how this version was prepared:] During the preparation of this work the author(s) used Claude (Anthropic) to restructure and edit the text for this journal and to draft supporting files. After using this tool, the author(s) reviewed and edited the content as needed and take(s) full responsibility for the content of the published article.

# References

Aral S, Walker D (2012) Identifying influential and susceptible members of social networks. *Science* 337(6092):337–341.

Argyle LP, Busby EC, Fulda N, Gubler JR, Rytting C, Wingate D (2023) Out of one, many: Using language models to simulate human samples. *Political Anal.* 31(3):337–351.

Bakshy E, Hofman JM, Mason WA, Watts DJ (2011) Everyone's an influencer: Quantifying influence on Twitter. *Proc. 4th ACM Internat. Conf. Web Search Data Mining* (ACM, New York), 65–74.

Ballester C, Calvó-Armengol A, Zenou Y (2006) Who's who in networks. Wanted: The key player. *Econometrica* 74(5):1403–1417.

Banerjee A, Chandrasekhar AG, Duflo E, Jackson MO (2013) The diffusion of microfinance. *Science* 341(6144):1236498.

Bao T, Chang TS (2014) Finding disseminators via electronic word of mouth message for effective marketing communications. *Decision Support Systems* 67:21–29.

Barabási AL (2005) The origin of bursts and heavy tails in human dynamics. *Nature* 435(7039):207–211.

Barabási AL, Albert R (1999) Emergence of scaling in random networks. *Science* 286(5439):509–512.

Beaman L, BenYishay A, Magruder J, Mobarak AM (2021) Can network theory-based targeting increase technology adoption? *Amer. Econom. Rev.* 111(6):1918–1943.

Bonabeau E (2002) Agent-based modeling: Methods and techniques for simulating human systems. *Proc. Natl. Acad. Sci. USA* 99(Suppl 3):7280–7287.

Brand J, Israeli A, Ngwe D (2023) Using GPT for market research. Working Paper 23-062, Harvard Business School, Boston.

Crane R, Sornette D (2008) Robust dynamic classes revealed by measuring the response function of a social system. *Proc. Natl. Acad. Sci. USA* 105(41):15649–15653.

Davis JP, Eisenhardt KM, Bingham CB (2007) Developing theory through simulation methods. *Acad. Management Rev.* 32(2):480–499.

Galeotti A, Goyal S (2009) Influencing the influencers: A theory of strategic diffusion. *RAND J. Econom.* 40(3):509–532.

Gao C, Lan X, Lu Z, Mao J, Piao J, Wang H, Jin D, Li Y (2023) S³: Social-network simulation system with large language model-empowered agents. Preprint, arXiv:2307.14984.

Gilbert N (2008) *Agent-Based Models* (Sage, Thousand Oaks, CA).

Goldenberg J, Han S, Lehmann DR, Hong JW (2009) The role of hubs in the adoption process. *J. Marketing* 73(2):1–13.

Hadar J, Russell WR (1969) Rules for ordering uncertain prospects. *Amer. Econom. Rev.* 59(1):25–34.

Hawkes AG (1971) Spectra of some self-exciting and mutually exciting point processes. *Biometrika* 58(1):83–90.

He S, Zhang W, Luo J, Zhang P, Zhao K, Zeng DD (2024) Modeling the co-diffusion of competing memes in online social networks. *Decision Support Systems* 187:114324.

Hinz O, Skiera B, Barrot C, Becker JU (2011) Seeding strategies for viral marketing: An empirical comparison. *J. Marketing* 75(6):55–71.

Hodas NO, Lerman K (2014) The simple rules of social contagion. *Sci. Rep.* 4:4343.

Horton JJ (2023) Large language models as simulated economic agents: What can we learn from homo silicus? NBER Working Paper 31122, National Bureau of Economic Research, Cambridge, MA.

Kempe D, Kleinberg J, Tardos É (2003) Maximizing the spread of influence through a social network. *Proc. 9th ACM SIGKDD Internat. Conf. Knowledge Discovery Data Mining* (ACM, New York), 137–146.

Leung FF, Gu FF, Li Y, Zhang JZ, Palmatier RW (2022) Influencer marketing effectiveness. *J. Marketing* 86(6):93–115.

Lewis PAW, Shedler GS (1979) Simulation of nonhomogeneous Poisson processes by thinning. *Naval Res. Logist. Quart.* 26(3):403–413.

Li F, Du TC (2011) Who is talking? An ontology-based opinion leader identification framework for word-of-mouth marketing in online social blogs. *Decision Support Systems* 51:190–197.

Libai B, Muller E, Peres R (2013) Decomposing the value of word-of-mouth seeding programs: Acceleration versus expansion. *J. Marketing Res.* 50(2):161–176.

Malmgren RD, Stouffer DB, Motter AE, Amaral LAN (2008) A Poissonian explanation for heavy tails in e-mail communication. *Proc. Natl. Acad. Sci. USA* 105(47):18153–18158.

Markowitz H (1952) Portfolio selection. *J. Finance* 7(1):77–91.

Miao S, Chen Z, Luo Y, Hsu HHH, Li M, Zhang K, Li P (2026) Can LLM agents simulate dynamic networks? A case study on email networks with phishing synthesis. Preprint, arXiv:2605.12507.

Ogata Y (1981) On Lewis' simulation method for point processes. *IEEE Trans. Inform. Theory* 27(1):23–31.

Park JS, O'Brien JC, Cai CJ, Morris MR, Liang P, Bernstein MS (2023) Generative agents: Interactive simulacra of human behavior. *Proc. 36th Annual ACM Sympos. User Interface Software Tech.* (ACM, New York).

Piao J, Yan Y, Zhang J, Li N, Yan J, Lan X, Lu Z, et al. (2025) AgentSociety: Large-scale simulation of LLM-driven generative agents advances understanding of human behaviors and society. Preprint, arXiv:2502.08691.

Rand W, Rust RT (2011) Agent-based modeling in marketing: Guidelines for rigor. *Internat. J. Res. Marketing* 28(3):181–193.

Rockafellar RT, Uryasev S (2000) Optimization of conditional value-at-risk. *J. Risk* 2(3):21–41.

Santos Silva JMC, Tenreyro S (2006) The log of gravity. *Rev. Econom. Statist.* 88(4):641–658.

Schramm ME, Trainor KJ, Shanker M, Hu MY (2010) An agent-based diffusion model with consumer and brand agents. *Decision Support Systems* 50:234–242.

Simon HA (1971) Designing organizations for an information-rich world. Greenberger M, ed. *Computers, Communications, and the Public Interest* (Johns Hopkins Press, Baltimore), 37–72.

Törnberg P, Valeeva D, Uitermark J, Bail C (2023) Simulating social media using large language models to evaluate alternative news feed algorithms. Preprint, arXiv:2310.05984.

Watts DJ, Dodds PS (2007) Influentials, networks, and public opinion formation. *J. Consumer Res.* 34(4):441–458.

Weng L, Flammini A, Vespignani A, Menczer F (2012) Competition among memes in a world with limited attention. *Sci. Rep.* 2:335.

Wies S, Bleier A, Edeling A (2023) Finding Goldilocks influencers: How follower count drives social media engagement. *J. Marketing* 87(3):383–405.

Yang Z, et al. (2024) OASIS: Open agent social interaction simulations with one million agents. Preprint, arXiv:2411.11581.

Zhang A, Tan Y, Tang Y, Tang H, Ye Q, Gonzalez MC, Li Y (2026a) Toward temporal realism in city-scale crisis response simulation using LLM agents. Preprint, arXiv:2606.19904.

Zhang X, Chen X, Liu Y, Wang J, Hu Z, Yan R (2024) A large-scale time-aware agents simulation for influencer selection in digital advertising campaigns. Preprint, arXiv:2411.01143.

Zhang X, Liu Y, Wang J, Hu Z, Chen X, Yan R (2025) SAGraph: A large-scale social graph dataset with comprehensive context for influencer selection in marketing. *Proc. 48th Internat. ACM SIGIR Conf. Res. Development Inform. Retrieval* (ACM, New York).

Zhang Y, Qiao K, Wang Z, Liang N, Ma D, Sun W, Chen J, Yan B (2026b) POSIM: A multi-agent simulation framework for social media public opinion evolution and governance. Preprint, arXiv:2603.23884.

Zhao Q, Erdogdu MA, He HY, Rajaraman A, Leskovec J (2015) SEISMIC: A self-exciting point process model for predicting tweet popularity. *Proc. 21st ACM SIGKDD Internat. Conf. Knowledge Discovery Data Mining* (ACM, New York), 1513–1522.
