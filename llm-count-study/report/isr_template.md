::: {custom-style="Title"}
Synthetic Customers as Decision-Support Artifacts: Design Constraints, Calibration, and Accountability in Generative-AI Marketing Analytics
:::

::: {custom-style="Author"}
Manuscript prepared for submission to *Information Systems Research* (author information omitted for review)
:::

**Abstract**

Organizations are placing generative-AI "digital twins" of customers inside their marketing analytics systems, yet little is known about how such systems should be designed, validated, and governed. We treat the synthetic-customer simulator as an IT artifact for decision support and develop design constraints and a calibration mechanism for it. Two propositions state system design constraints. A persona-conditioned model that returns deterministic answers can carry only the customer heterogeneity that its persona describes (Proposition 1), and heterogeneity supplied from outside the model must be calibrated against it to avoid double counting (Proposition 2). These constraints explain why a familiar statistical result becomes a managerial problem: when behavior is generated instead of estimated, the spread of simulated behavior is no longer disciplined by the firm's data, it cannot be detected from inside the system, and it can be checked only against the real data that the system was meant to economize. We evaluate four elicitation designs in eight language models against public transaction data (mean counts of about 0.5, 4.8, and 7.8) and a randomized email experiment, using purchase counts and promotion lifts as supporting evidence. Direct and day-by-day designs collapse toward near-constant answers and lose the concentration of purchases among heavy buyers; a design that takes only the level from the model and calibrates the spread externally restores concentration; but calibrating the level adds little beyond what the historical mean alone provides, so the model supplies little that the firm's data do not. Purchase lifts have the right sign but are overstated in 15 of 16 configurations (median about ninefold), enough to reverse a go/no-go decision. We derive five design principles, an acceptance-test protocol, and accountability arrangements for validating and governing synthetic data in analytics systems.

**Keywords:** IT artifact, decision support systems, generative AI, synthetic customers, organizational accountability

# 1. Introduction

Organizations are beginning to place generative-AI "digital twins" of customers inside their marketing analytics systems. The idea is simple: prompt a language model with a customer description, ask what that customer would do, and repeat for thousands of customers, so that promotions, prices, and messages can be tested before money is committed. Early studies found that such synthetic respondents produce plausible willingness-to-pay estimates (Brand et al. 2023), reproduce classic behavioral experiments (Horton 2023), and mimic purchase-intent ratings (Maier et al. 2025), and vendors now market twins of consumer panels on this basis. These studies evaluate the model's answers. What an organization adopts, however, is a system: personas drawn from its customer data, an elicitation procedure, a step that turns answers into numbers, and a decision process that uses them. Whether that system can be trusted for a decision depends on how it is designed, how it is validated, and who is accountable for it. These are questions for information systems research.

We treat the synthetic-customer simulator as an IT artifact, a system that organizations design, deploy, and use to support decisions (Orlikowski and Iacono 2001). Such an artifact should be evaluated against the decisions it serves, and its value lies in the fit between what the system delivers and what the task demands (Goodhue and Thompson 1995). For promotion planning the task demands a plausible share of non-buyers, a plausible weight of heavy buyers, and a plausible absolute size of an effect. The elicitation design, meaning how the model is asked, how its answers become numbers, and where the variation among customers comes from, is therefore the artifact's central design variable.

The question sits at the interface of information systems and marketing. Marketing analytics has become a systems problem: data are collected, transformed, and fed into models and dashboards that shape budgets and campaigns (Wedel and Kannan 2016), and the design, validation, and governance of those systems fall to information systems functions as much as to marketing. Generative AI adds a new component to this pipeline, the synthetic customer. A twin is only as useful as the properties it preserves, and fluent output invites reliance beyond what a system warrants (Lee and See 2004).

To make the question tractable we examine one property on which analytics systems depend, the heterogeneity of customers, as it appears in purchase counts. Marketing science has long modeled counts as a Poisson process with customer-specific rates, so that overdispersion measures how much customers differ (Ehrenberg 1959, Schmittlein et al. 1987, Fader et al. 2005). Heterogeneity is a demanding test for three reasons: it is invisible in the averages that users inspect, it drives decisions about heavy buyers, non-buyers, and uncertainty, and studies of silicon samples find it compressed (Li et al. 2025, Tigre and Souto 2026, Jang et al. 2026). Purchase counts, concentration, and promotion lifts are thus the supporting evidence in this paper, not its subject.

The statistics are familiar; the setting is not. In classical customer-base models heterogeneity is estimated from the firm's own data, so its magnitude is disciplined by that data. In a synthetic-customer system it is generated by a pretrained model, and nothing in the generation process ties it to the firm's customers. This changes who can know whether the artifact is right, and what the firm must do about it.

We ask four questions. What design constraints govern how much customer heterogeneity a persona-conditioned generative system can carry, and what calibration mechanism restores the rest (RQ1)? Do the elicitation designs open to an organization differ in whether they preserve decision-relevant properties of customer behavior, across models and settings (RQ2)? How can a firm validate such a system, and does calibrating it with its own data suffice (RQ3)? And what do the errors mean for a decision, as judged against a randomized promotion experiment (RQ4)? We compare four elicitation designs in eight language models and two prompt variants against public transaction data sets whose mean counts differ by a factor of ten or more, and against a randomized email experiment.

The study makes four contributions. First, we give design constraints for the artifact: a design constraint, a calibration mechanism, and a result that links the constraint to customer concentration (Propositions 1 to 3; RQ1), and we explain why this is a managerial problem and not merely a statistical one: when behavior is generated rather than estimated, quality is bounded by the firm's data assets, cannot be seen from inside the system, and depends on components that the firm does not control. Second, we show across designs, models, and settings that direct and day-by-day designs collapse, that taking only the level from the model and calibrating the spread externally restores concentration, and that calibrating the level adds little beyond the historical mean (RQ2). Third, we show that the cues a user can see do not reliably reveal the errors that matter, and we derive five design principles and an acceptance-test protocol (RQ3). Fourth, we identify the organizational arrangements that follow, and we show with a randomized email experiment that overstated promotion lifts would reverse a go/no-go decision (RQ4).

The remainder of the paper is organized as follows. Section 2 reviews the literature and states the gap. Section 3 develops the design constraints and hypotheses. Section 4 describes the data, designs, and measures. Section 5 reports results, Section 6 discusses implications and limitations, and Section 7 concludes.

# 2. Related Literature

## 2.1 LLMs as synthetic respondents and customers

LLMs are increasingly proposed as inexpensive stand-ins for consumer panels. Early work suggested that GPT-based respondents can produce plausible willingness-to-pay estimates and conjoint results (Brand et al. 2023), that simulated agents reproduce the qualitative pattern of classic behavioral experiments (Horton 2023), and that LLM-driven agents can be placed in simulated markets to test discount strategies (Chu et al. 2025). Evidence on preferences is more mixed (Goli and Singh 2023), and LLM-generated data can track the direction of treatment effects while overstating their magnitudes (Hewitt et al. 2024).

## 2.2 Variance collapse and sampling

The narrowness of simulated responses is now well documented. Silicon samples drift toward the modal answer within demographic subgroups (Li et al. 2025), consumer panels built from LLMs show variance compression and sign flips in estimated coefficients (Tigre and Souto 2026), and instruction-tuned models appear unable to draw independent samples from the distribution they can otherwise describe (Jang et al. 2026; see also Gu et al. 2024). Listing several candidate answers with probabilities partly restores diversity (Zhang et al. 2025a), and mapping free-text answers to rating scales improves purchase-intent ratings (Maier et al. 2025). In operations management, LLMs often reproduce the outcome of a hypothesis test while diverging from human data in the full response distribution (Zhang et al. 2025b).

## 2.3 Counts in customer analytics

Nearly all of this evidence concerns bounded, ordinal, or continuous responses. Purchase and visit counts differ in an important way. They are nonnegative integers whose variance is tied to their mean, and in marketing practice they are modeled as a Poisson process whose rate varies across customers, giving a negative binomial distribution in aggregate (Ehrenberg 1959, Schmittlein et al. 1987, Fader et al. 2005). Overdispersion relative to the Poisson is therefore the empirical signature of customer heterogeneity (Cameron and Trivedi 1990), and a simulator that compresses heterogeneity should show up first as underdispersion. These distributions also feed customer lifetime value, repeat-purchase forecasts, and budget allocation.

## 2.4 Synthetic customers as decision-support artifacts

Information systems research has long treated decision-support tools as artifacts whose worth must be shown by evaluation against the decisions they serve (Orlikowski and Iacono 2001). We separate the design of the artifact, here the elicitation procedure, the persona schema, and the calibration step of a simulator, from its evaluation, here the comparison with observed behavior. Task–technology fit supplies the criterion (Goodhue and Thompson 1995). Promotion pre-testing demands four capabilities of a simulated customer base: a plausible average, a plausible spread across customers, a plausible share of non-buyers, and a plausible absolute effect size. Existing evaluations of synthetic respondents mostly check the first and, through ratings, a crude version of the second. We therefore frame our four designs as alternative instantiations of one artifact class and our measures as the fit criteria that this task imposes. The artifact view locates the topic at the interface of information systems and marketing analytics (Wedel and Kannan 2016), and the hybrid design is an instance of arrangements in which a model supplies part of a judgment and a statistical procedure another (Dellermann et al. 2019). The question is not whether language models "understand" customers, but whether a particular system built on them supports a particular decision (Orlikowski and Iacono 2001).

## 2.5 Research gap

The studies closest to ours stop short of this question. Huang and Wang (2026) model aggregate demand as a mixture of persona-level purchase probabilities, but within a single period and without repeat counts. Sashihara et al. (2025) use the distribution of purchases per buyer as a validation metric for a simulated marketplace, without testing it against Poisson or negative binomial benchmarks. Chen (2026) compares LLM user simulators with verified payment outcomes and finds that they overstate purchase propensity among customers who ultimately do not buy, but the outcome there is a binary conversion rather than a count. Calibration frameworks such as SYN-DIGITS (Fan et al. 2026) align simulated responses with human ground truth at the individual and distributional level, yet, to our reading, they do not exploit the Poisson–gamma structure that governs count data. To our knowledge, and within the scope of our search, no prior study evaluates whether LLM-generated per-customer purchase counts reproduce the dispersion, zero proportion, and tail behavior of observed count data, or examines how the way heterogeneity is injected affects that fidelity.

# 3. Design Constraints and Hypotheses

This section develops design constraints for the artifact. We use the Poisson–gamma model as the formal language in which to state what a persona-conditioned generative system can and cannot carry, and we use the propositions that follow as design constraints and as a calibration mechanism for such a system, not as claims about count data. Section 3.7 sets out why we regard them as an information systems contribution.

## 3.1 Purchase counts as a Poisson–gamma mixture

Let customer $i$ have a latent purchase rate $\Lambda_i$ for the period, with mean $\mu = E[\Lambda]$, and let the observed count satisfy $N_i \mid \Lambda_i \sim \text{Poisson}(\Lambda_i)$. Then $E[N] = \mu$ and $\text{Var}(N) = \mu + \text{Var}(\Lambda)$. We define the overdispersion parameter
$$\alpha = \frac{\text{Var}(N) - E[N]}{E[N]^2} = \frac{\text{Var}(\Lambda)}{\mu^2},$$
the squared coefficient of variation of the rate, so that the variance-to-mean ratio equals $1 + \alpha\mu$. When $\Lambda$ follows a gamma distribution, $N$ is negative binomial with dispersion $\alpha$. The quantity $\alpha$ is thus a direct measure of unobserved customer heterogeneity, and it does not depend on the mean, whereas the variance-to-mean ratio does. We report both: the variance-to-mean ratio is easier to read, and $\alpha$ permits comparison across settings with different means.

## 3.2 What a persona-conditioned simulator can carry

A synthetic customer is generated from a persona description $X$. Suppose that, given $X$, the simulator returns a count with conditional mean $m(X)$ and conditional variance $v(X)$, and let $\mu^* = E[m(X)]$.

**Proposition 1.** The simulated counts $N^*$ satisfy $\text{Var}(N^*) = E[v(X)] + \text{Var}(m(X))$. If the simulator is deterministic given the persona, so that $v(X) = 0$, then
$$\alpha^* = c^2 - \frac{1}{\mu^*}, \qquad c^2 = \frac{\text{Var}(m(X))}{\mu^{*2}},$$
and the simulated counts are underdispersed ($\alpha^* < 0$) whenever $\text{Var}(m(X)) < \mu^*$. If in addition $m(X) = E[\Lambda \mid X]$, then $\alpha^* = \alpha - R - 1/\mu$, where $R = E[\text{Var}(\Lambda \mid X)]/\mu^2$ is the share of heterogeneity that the persona does not explain.

*Proof.* The first statement is the law of total variance; the remaining statements follow by substitution (Online Appendix D). $\square$

Proposition 1 identifies two losses: a deterministic simulator drops the Poisson noise (the term $-1/\mu$) and cannot carry heterogeneity that the persona does not describe (the term $R$). Because real customers differ in ways that a short persona cannot capture, $R$ is rarely small, and collapse toward a single answer is the expected outcome.

## 3.3 Injecting heterogeneity without double counting

An obvious repair is to let the model supply only a persona-level mean $\lambda(X)$ and to add the missing heterogeneity from an external random multiplier. Let $\Lambda = \lambda(X)\,G$, where $G$ is independent of $X$, $E[G] = 1$, and $\text{Var}(G) = \alpha_w$.

**Proposition 2.** With $c^2 = \text{Var}(\lambda(X))/E[\lambda(X)]^2$,
$$1 + \alpha = (1 + c^2)(1 + \alpha_w).$$
Consequently, setting $\alpha_w$ equal to the total target $\alpha$ implies an overdispersion of $(1 + c^2)(1 + \alpha) - 1 > \alpha$, an overstatement of $c^2(1 + \alpha)$.

*Proof.* By independence, $E[\Lambda^2] = E[\lambda(X)^2]\,E[G^2]$ (Online Appendix D). $\square$

Proposition 2 gives the calibration rule used in our hybrid design: the external multiplier must carry only the within-persona heterogeneity $\alpha_w = (1 + \alpha)/(1 + c^2) - 1$. It also shows that the hybrid reproduces dispersion by construction, so that its fidelity depends on the one thing the model still supplies, the accuracy of $\lambda(X)$.

## 3.4 Describing a distribution, and a ceiling

A third design asks the model to state probabilities for count bins and samples a count externally. Because the top bin must be closed, this design cannot produce the extreme tail of the real distribution. The variance-to-mean ratio attainable by a perfect description, with each bin's mass spread uniformly within the bin, is 2.10 (with $\alpha$ of 2.33) in the low-mean setting and 6.61 (with $\alpha$ of 1.18) in the high-mean setting, against real values of 2.49 and 7.85, so comparisons for this design are made against the ceiling as well as the real value.

## 3.5 Relative and absolute effects

Let $p_0$ be the probability of an outcome without a promotion and $d$ the absolute lift caused by it. The risk ratio is $RR = 1 + d/p_0$. A simulator that has the lift right but the base rate wrong therefore produces the wrong risk ratio, and a simulator that has the base rate right but overstates the lift produces an inflated one. Because revenue depends on the absolute lift $d$, evaluating a simulator on risk ratios alone can lead to opposite conclusions from evaluating it on lifts.

## 3.6 Hypotheses

Proposition 1 motivates the first hypothesis, Proposition 2 and Section 3.4 the second and third, and Section 3.5 the fourth.

- **H1 (collapse).** Direct answers (design A) and day-by-day simulation (design B) yield variance-to-mean ratios below the real value and fewer zero counts than the real data.
- **H2 (description).** Describing a distribution (design C) raises dispersion toward, but not beyond, the ceiling of its bins, and yields too few zeros.
- **H3 (hybrid).** The hybrid (design D) reproduces dispersion, and its fidelity depends on the accuracy of the model's mean.
- **H4 (effects).** In an experiment, simulated promotion effects (a) have the correct sign, (b) overstate the absolute lift when the simulated base rate is overstated, and (c) fail to distinguish similar treatments.

Five supplementary analyses are not hypotheses and are labeled S1 to S5 in Section 5.11: (S1) the concentration of purchases among heavy buyers (Proposition 3), (S2) calibration of the level, (S3) the robustness of collapse to the mean level, to richer personas, and to model scale, (S4) whether the cues a user can see reveal decision errors, and (S5) a backtest of the acceptance test.

## 3.7 Propositions as design constraints and a calibration mechanism

The propositions can be read as statements about how to build the artifact, not only about count distributions. Proposition 1 is a design constraint: a component that returns a deterministic answer for each persona can transmit only the heterogeneity that the persona describes, so the remainder must come from another component. Proposition 2 is a calibration mechanism. It allocates a variance budget between the model's persona-conditioned rates and an external noise generator so that their combination matches the dispersion in the organization's own data, $1 + \alpha = (1 + c^2)(1 + \alpha_w)$. The mechanism is explicit, because the allocation is computed rather than tuned; auditable, because the target comes from a named historical data set; and modular, because the model can be replaced without changing the calibration step, although the step must then be recomputed. Together the propositions separate the responsibilities of the language model, which supplies the level of a customer's expected behavior, and a statistical layer, which supplies and calibrates the spread.

*Why this is more than a statistical result.* The algebra is elementary, and we do not claim otherwise. The contribution lies in what it establishes about the design space that an organization faces. First, Proposition 1 is an impossibility result for the levers that organizations control: the prompt, the persona, the choice of model, and the decoding settings. Each acts on the deterministic map from persona to answer, and none can lift the bound $\alpha^* = c^2 - 1/\mu$ beyond what the persona information allows, so a team that tunes prompts to "add diversity" is working on the wrong lever, which can be known before any experiment. Second, Proposition 2 turns the remedy into a rule that can be computed, audited, and handed to a governance process, a form that organizations can use. Third, both propositions are independent of which model is used, so they hold when models and providers change. Fourth, they generate predictions that we test in Section 5.

## 3.8 Why a familiar statistic becomes a managerial problem

The model behind the propositions is not new. What is new is the setting in which their implication becomes a problem for organizations, in four ways.

*From estimated to generated heterogeneity.* In the customer-base models of marketing science, heterogeneity is a latent quantity inferred from the firm's own data, so its magnitude is disciplined by that data. In a synthetic-customer system it is generated by a pretrained model, and nothing in the generation process ties it to the firm's customers. By Proposition 1 the tie cannot be restored through the prompt, so the spread must be supplied by a component that is connected to data.

*A bound set by the organization's data assets.* The heterogeneity that a simulator can carry is the share explained by the persona, and the persona contains only what the organization knows about its customers (about 1% in our demographic experiment). This is a complementarity between a generative model and the firm's data assets, familiar from research on IT business value (Melville et al. 2004), with a sharp form: more capable models cannot compensate for uninformative customer data.

*The validation paradox.* Synthetic customers are adopted where real data are scarce or costly, yet the heterogeneity that Proposition 1 shows to be lost is invisible inside the system and can be detected only against real data on the same properties. The evidence that would reveal the error is the evidence that the system was meant to economize. Only partial validation resolves this, in which a small amount of real data calibrates and audits a large amount of synthetic data, and Proposition 2 supplies the calibration step.

*Silent failure and shifting components.* Fluent output with the right sign gives no signal of failure, and a wrong decision becomes visible only after several campaign cycles, if at all. The generating component is also outside the firm's control: in our runs eight models produced very different levels and spreads for the same prompt, and a rented model has to be re-validated whenever it changes, which makes validation a continuing governance task.

A lost spread also affects decisions that depend on concentration, as the following result shows.

**Proposition 3 (concentration).** Let $\Lambda \ge 0$ be a customer rate with mean $\mu$ and squared coefficient of variation $\alpha > 0$. For $0 < q < 1$ let $S_q$ be the share of all expected purchases that comes from the fraction $q$ of customers with the highest rates, $S_q = \max_{P(A) = q} E[\Lambda \mathbf{1}_A]/\mu$, where the maximum is over events $A$ of probability $q$.

(a) For every rate distribution, $q \le S_q \le q + \sqrt{\alpha\, q(1-q)}$.

(b) If $\Lambda$ is gamma distributed with shape $k = 1/\alpha$, then $S_q(\alpha) = 1 - F_{k+1}\!\left(F_k^{-1}(1-q)\right)$, where $F_k$ is the distribution function of a gamma variable with shape $k$ and unit scale.

(c) Among gamma distributions, $S_q(\alpha)$ is strictly increasing in $\alpha$, and $S_q(\alpha) \to q$ as $\alpha \to 0$.

(d) The simulated count $N^*$ of a deterministic persona-conditioned simulator (Proposition 1) has squared coefficient of variation $c^2$. The share of simulated purchases made by the fraction $q$ of customers with the highest counts is therefore at most $q + \sqrt{c^2 q(1-q)}$.

*Proof sketch.* Part (a) follows from the Cauchy–Schwarz inequality applied to $\text{Cov}(\Lambda, \mathbf{1}_A)$, with an independent event of probability $q$ for the lower bound. Part (b) follows from the identity $\lambda f_{k,\theta}(\lambda) = k\theta\, f_{k+1,\theta}(\lambda)$, which makes the size-biased gamma a gamma with shape $k+1$. Part (c) uses the beta–gamma algebra to write a gamma variable with smaller shape as an independent mean-one multiple of one with larger shape. Part (d) applies (a) to the simulated counts. The full proof is in Online Appendix D. $\square$

For the three reference settings with $q = 0.1$, part (b) gives shares of expected purchases of 52% for the top tenth of customers when $\alpha = 3.05$ (low-mean setting), 38% when $\alpha = 1.42$ (high-mean setting), and 29% when $\alpha = 0.71$ (demographic households), against 10% for a population without heterogeneity. The shares of observed counts are somewhat higher in the low-mean setting (65%, 39%, and 30%) because counts are discrete and zeros are common. A simulator that carries only the persona-described heterogeneity of the demographic experiment ($c^2 = 0.006$) can represent a share of at most 12% by part (d), and 11% if its rates were gamma distributed. Decisions that depend on concentration, such as how deeply to target a promotion, how to set loyalty tiers, or how to size a budget ceiling for heavy buyers, are therefore biased in a known direction when the spread is lost. The direction of the bias, and an upper bound on what a given simulator can represent, are known in advance, which is what makes the problem manageable by design.

# 4. Research Design

## 4.1 Settings and reference data

Table 1 summarizes the three reference settings. In the first, the reference is a negative binomial distribution calibrated to the 4-week purchase counts of customers in the public Online Retail II transaction file (Chen 2019) whose first purchase fell in the first three months: mean 0.49, variance-to-mean ratio 2.49, zero share 0.74, and $\alpha = 3.05$. In the second, the reference is the empirical distribution of 4-week basket counts, pooled over 13 windows, for the 2,469 loyalty-card households of the dunnhumby Complete Journey data in 2017 (32,097 household-windows), for which negative binomial was the best-fitting model by AIC in every window. In the third, the benchmark is the randomized email test of Hillstrom (2008), in which 64,000 customers received no email, a men's merchandise email, or a women's merchandise email, and visits and purchases were recorded for the following two weeks.

| Data | Unit | Mean | Zero | Var/mean | Alpha | Treatment |
|---|---|---|---|---|---|---|
| Online Retail II (reference) | customer, 4 weeks | 0.49 | 0.74 | 2.49 | 3.05 | none |
| Complete Journey (empirical) | household, 4 weeks | 4.84 | 0.19 | 7.85 | 1.42 | targeted campaigns, not randomized |
| Complete Journey, households with demographics (empirical) | household, 4 weeks | 7.83 | 0.03 | 6.52 | 0.71 | none |
| Hillstrom email test | customer, 2 weeks | visit 0.106; purchase 0.0057 (no email) | | | | randomized: none, men's, women's |

*Table 1. Reference settings.*

## 4.2 Elicitation designs

Each simulated customer is described by a short persona text (a segment label, age, and country or household size; in the email experiment, the real covariates of a sampled customer). We compare four designs.

*Design A (direct).* The persona is asked how many purchases (or shopping trips) it will make in the next 4 weeks and answers with an integer.

*Design B (daily).* For each of the four weeks, the persona decides for each of 7 days whether it makes a purchase (one model call per week); the daily indicators are summed.

*Design C (describe, then sample).* The persona states probabilities for count bins (0, 1, 2, 3, 4, and 5 or more in the low-mean setting; 0, 1–2, 3–4, 5–7, 8–12, 13–20, and 21 or more in the high-mean setting), and a count is drawn with an external random number generator.

*Design D (hybrid).* The persona states only its expected mean count $\lambda$. The count is Poisson with rate $\lambda G$, where $G$ is an external gamma multiplier whose variance is set according to Proposition 2 from the dispersion of the model's own $\lambda$ values and the reference $\alpha$.

Each design is run in two prompt variants. In the *plain* variant the persona receives no information about the population's purchase behavior. In the *anchored* variant it is told the base rate (about 0.5 purchases per 4 weeks and that most customers make none; or about 5 shopping trips per 4 weeks and that some make none).

## 4.3 Models, runs, and measures

We used eight LLMs through the OpenRouter interface: GPT-4o-mini, Llama-3.3-70B-Instruct, and Claude Haiku 5.5 in the first runs, and Claude Sonnet 5, GPT-5.6-terra, DeepSeek-V4-Pro, Gemini 3.1 Flash-Lite, and Mistral Large 4, added to test whether larger and more recent models behave differently. All eight models were run on three random seeds, that is, on three independent samples of customers (or household-windows) with new model calls. In the low-mean setting GPT-4o-mini and Llama were run at temperatures 0.3, 0.7, and 1.0 in the first seed and at 0.7 in the two further seeds (1,000 customers per cell), and the other six models contribute 600 (three seeds of 200); in the two high-mean settings the temperature was 0.7 (600 per cell); and in the email experiment each seed uses 300 customers (900 per model). Haiku 5.5, Sonnet 5, and GPT-5.6-terra do not accept a temperature setting and contribute one run per prompt variant and seed. Hidden reasoning was switched off where possible so that short answers are not truncated. For each cell we report the mean, the variance-to-mean ratio, the zero share, and $\alpha$, with 95% bootstrap intervals over customers; an asterisk marks an interval that excludes the reference value. Parsing failed for 5% or less of the responses in all cells but two (DeepSeek-V4-Pro, daily simulation, high-mean setting, about 10%), which are computed from the parsed responses only.

## 4.4 Email experiment

For each of 300 customers sampled from the real data (a new sample for each seed) we asked, in separate independent calls, for the probability (0 to 100 percent) that the customer would visit the website, and that it would make a purchase, in the next two weeks, under each of three conditions: no email, a men's email, and a women's email. We report the risk ratio and the absolute lift (the probability with the email minus the probability without it), the latter with paired bootstrap intervals over customers. Yes/no answers and Bernoulli draws from the elicited probabilities were also collected and are discussed where relevant. Because each call sees only one condition, the design mimics random assignment but does not equal it.

# 5. Results

## 5.1 Overview

Figure 1 shows the variance-to-mean ratio of every cell, and Appendix B gives all cells and ranges by design (Tables B1 to B6). The main pattern is that variance collapse is severe in designs A and B in every setting, that design C moves toward the real dispersion but loses zeros where they are common, and that design D matches dispersion in most cells while its mean depends on the model. The loss of dispersion has a direct consequence for the concentration of purchases among heavy buyers (Section 5.7).


![Figure 1. Variance-to-mean ratio of simulated purchase counts with 95% intervals, by design (columns), model (rows), and setting (a: low mean; b: high mean; c: real household demographics). The dashed line is the real value; the dotted line is the largest value that design C can reach with its count bins. Filled markers: plain prompt; hollow markers: anchored prompt.](fig1_dispersion.png){width=5.6in}

## 5.2 Low-mean setting

Direct and daily designs rarely reproduce the real dispersion. In 45 of the 47 cells of designs A, B, and C with a defined ratio, the upper bound of the variance-to-mean interval is below the reference of 2.49 (Online Appendix Table B1, Figure 1a). The exceptions are DeepSeek-V4-Pro without the anchor for direct answers (ratio 14.7, interval 5.6 to 22.3, from a few very large counts alongside many zeros) and Sonnet 5 without the anchor for daily simulation (2.95, interval 2.73 to 3.17). Elsewhere direct answers are the most compressed, with ratios of at most 0.87 in 11 of 16 cells; with the anchor, five cells return "0" for 98% to 100% of customers, which follows the anchor text ("most make none") but carries no persona information. Without the anchor, daily simulation overstates the mean in every model (1.6 to 13.6 purchases in 28 days against 0.49). Describing a distribution reaches ratios of 0.97 to 1.61, below its ceiling of 2.10 in all 16 cells, with a zero share that is too low in every cell (0.32 to 0.71 against 0.74). The hybrid matches the reference ratio in 10 of 16 cells, the mean in 6, the zero share in 10, and $\alpha$ in 13, and all four in 5 (Sonnet 5, DeepSeek-V4-Pro, and GPT-5.6-terra without the anchor, and Mistral Large 4 and GPT-5.6-terra with it). Agreement on dispersion is partly by construction, because the gamma multiplier injects it; what the model contributes is the mean, which is almost twice the reference for Llama with the anchor (0.93 against 0.49).

## 5.3 High-mean setting

A higher mean does not relieve the collapse of direct answers (Online Appendix Table B2, Figure 1b). In 13 of 16 cells the variance-to-mean ratio of design A lies between 0.00 and 0.36, against a reference of 7.85; the three cells with more spread are DeepSeek-V4-Pro (1.10 and 1.57) and Mistral Large 4 without the anchor (2.45). Without the anchor GPT-4o-mini and Llama answered "8" for practically every customer, and with the anchor all eight models returned numbers close to the stated base rate of 5 (means of 3.73 to 5.22). Daily simulation again misses the mean (4.35 to 16.65 trips against 4.84) and has almost no dispersion (ratios of 0.04 to 0.38). In all 48 cells of designs A, B, and C the variance-to-mean interval lies entirely below the reference. Describing a distribution reaches ratios of 3.65 to 6.44, with intervals that contain the ceiling of 6.61 in only 3 of 16 cells, and its zero share is below the real 0.19 in every cell (0.01 to 0.15). The hybrid matches the reference ratio in 12 of 16 cells but the mean in 4, the zero share in 8, and all four statistics in 2 (Haiku 5.5 without the anchor and GPT-4o-mini with it), mostly because the model's mean is wrong, for example 3.63 for Mistral Large 4 with the anchor.

## 5.4 Is collapse specific to low means?

If direct answers were underdispersed only because small expected counts are rounded to 0, 1, or 2, the problem should shrink at higher means. It does not: the variance-to-mean ratio of direct answers is at most 0.87 in 11 of 16 cells at a mean of 0.5, at most 0.36 in 13 of 16 at a mean of 4.8, and at most 0.53 in 14 of 16 at a mean of 7.8, and larger or more recent models do not escape it.

## 5.5 Richer personas from real household demographics

To test whether richer personas change the picture, we drew 200 household-windows at random in each of three seeds from the 801 Complete Journey households with demographic records and described each household by its real age group, household type and size, children, marital status, income, and home ownership. This also lets us compare each simulated count with the household's real count in the same window. The reference is the real distribution of these households (mean 7.83, variance-to-mean ratio 6.52, zero share 0.03, $\alpha = 0.71$; ceiling of design C 5.01).

Out of sample, a Poisson regression of the household's count on all demographic fields reaches a Spearman correlation of only 0.04 with the real count, and the squared coefficient of variation of its predicted means is $c^2 = 0.006$, about 1% of $\alpha$. In terms of Proposition 1 the unexplained share $R$ is almost equal to $\alpha$, and a deterministic simulator that predicted these means perfectly would have $\alpha^* = c^2 - 1/\mu = -0.12$ against a real $\alpha$ of 0.71.

The simulations behave as Proposition 1 predicts (Online Appendix Tables B3 and B6). Direct answers are collapsed again (variance-to-mean ratio 0.00 to 1.73, $\alpha$ between -0.16 and +0.08). GPT-4o-mini answered "8" for every household when told the base rate and for practically every household without it, which gives $\alpha = -1/\mu = -0.125$, exactly the value of Proposition 1 with $c^2 = 0$. Daily simulation again misses the mean (5.9 to 17.2 against 7.83). Describing a distribution reaches ratios of 3.44 to 6.11, with intervals that contain the ceiling of 5.01 in 10 of 16 cells and a zero share that matches the real 0.03 in 8 of 16. The hybrid matches the reference ratio in 10 of 16 cells but the mean in only 3, because the model's $\lambda$ is usually too low (4.28 to 7.17 in the cells that miss, against 7.83). It matches the zero share in none (0.07 to 0.15), because Poisson counts with a gamma multiplier produce more zeros than these households, and so it matches all four statistics in none.


Individual-level validity is essentially nil. Across the 63 cells in which the answers vary, the Spearman correlation between the simulated count and the household's real count lies between -0.11 and +0.08, and the interval excludes zero in only two cells (one negative, for DeepSeek-V4-Pro without the anchor, and one positive, for GPT-5.6-terra with it). The model's own $\lambda$ in design D correlates between -0.06 and +0.05 with the real count, and none of its 16 intervals excludes zero. With 79 intervals, about four exclusions are expected by chance at the 5% level. Design C has positive correlations somewhat more often than the others (11 of 16 cells), but the median is +0.01, and the models were run on the same samples of household-windows, so the cells are not independent evidence. On the first sample the demographic regression itself has a rank correlation of -0.03 (interval -0.17 to +0.10); on the two further samples of 200 household-windows it reaches +0.19 and -0.02, which shows how much a single sample can move these correlations. Because the demographics predict the real count with a rank correlation of only 0.04 across all households, this result does not show that the models ignore information; it shows that these personas contain almost no information for any simulator to use. It is the empirical counterpart of Proposition 1: richer observable personas cannot supply the heterogeneity that counts contain.

## 5.6 Randomized email experiment

Figure 2 shows the absolute lift for the men's email in the elicited-probability design (the most stable of the three formats we tried), and Online Appendix Table B4 gives all lifts, gaps, and risk ratios; models are pooled over three samples of 300 customers each. The real effect of the men's email is a risk ratio of 1.72 for visits and 2.19 for purchases, with absolute lifts of 7.7 and 0.7 percentage points, and the real gap between the men's and the women's email is +0.031 for visits (interval +0.024 to +0.038).

![Figure 2. Absolute lift in the probability of a visit and of a purchase after a men's email (elicited-probability design). Bars are 95% intervals; the dashed line and band are the real lift and its 95% interval. Note the logarithmic axis in panel b.](fig2_lift.png){width=5.6in}

Four patterns emerge. First, the direction is mostly reproduced: the risk ratio, averaged over seeds, exceeds one in all 32 probability-elicitation cells (smallest 1.03), although individual seeds touch one in a few cells, and Llama with the anchor gave a risk ratio below one in the yes/no format for visits (0.60 to 0.69). Second, the size of the visit effect depends on the model and the prompt: 4 of 16 configurations are statistically consistent with the real +0.077 (Llama-3.3-70B, Haiku 5.5, and Mistral Large 4 without the anchor, and GPT-5.6-terra with it), eight are significantly smaller (three less than half as large, for example Sonnet 5 with the anchor, +0.027), and four are more than 1.5 times as large (for example GPT-4o-mini without the anchor, +0.190). The anchor brings GPT-5.6-terra to the real value but moves DeepSeek-V4-Pro from 0.5 to 2.6 times the real lift.

Third, the absolute lift in purchase probability exceeds the real +0.0068 in 15 of 16 configurations, by a median factor of about 9 and by up to 25 (+0.169 for GPT-4o-mini without the anchor). The exception is Sonnet 5 with the anchor (+0.002, 0.4 times the real lift), which attributes almost no effect to the email. Providing the base rate sets the no-email probability close to the stated number (about 0.10 for visits in six models, and 0.004 to 0.010 for purchases in five) without lowering the email-arm probability accordingly, so the risk ratio explodes in some cases (10 to 44 for Llama, Haiku, and Mistral) while the absolute lift stays large. By $RR = 1 + d/p_0$, Llama without the anchor has a visit lift close to the real value (+0.071) but a no-email probability of 0.30 instead of 0.106, and therefore a risk ratio of only 1.24 against 1.72.

Fourth, the models do not tell the two emails apart. The point estimate of the gap is positive in only 9 of 32 cells, and the largest simulated visit gap is +0.015. Seven gap intervals exclude zero: in six the women's email is rated significantly higher, and in one (DeepSeek-V4-Pro with the anchor for visits) the men's email is rated higher, by half the real gap.

Direct yes/no answers are not usable for rare events. In 15 of 32 yes/no cells of the first seed (and 27 of 64 cells of the two further seeds) the model answered "No" for every customer in the no-email condition, so the risk ratio is undefined, and the lifts range from -0.31 to +0.55 for visits and from +0.008 to +0.55 for purchases, up to 80 times the real lift.

## 5.7 Customer concentration

Proposition 3 predicts that a simulator without heterogeneity cannot represent the concentration of purchases among heavy buyers, and that the hybrid design, which supplies the spread externally, can. We measured the share of all simulated purchases made by the top tenth of customers (ranked by count) in every cell. In the reference the top tenth account for 65% of purchases in the low-mean setting, 39% in the high-mean setting, and 30% for the demographic households, against 10% or slightly more in a population without heterogeneity.

The prediction is borne out. In the 91 cells of direct answers and daily simulation in which a meaningful share can be computed, the top-decile share is below the reference and its interval excludes the reference in every one: 0.10 to 0.49 in the low-mean setting (the highest value is the overdispersed DeepSeek-V4-Pro cell), 0.10 to 0.18 in the high-mean setting, and 0.10 to 0.16 for the demographic households, practically the 10% of a homogeneous population. Five low-mean cells in which almost every simulated customer made no purchase are excluded, because the share is 1.00 or undefined only for lack of purchases to distribute. Describing a distribution recovers part of the concentration (0.30 to 0.52 against 0.65 in the low-mean setting and 0.27 to 0.36 against 0.39 in the high-mean setting) and lies within the interval of the reference in 11 of 16 cells for the demographic households. The hybrid design reproduces concentration in 39 of 48 cells (11, 13, and 15 of 16 in the three settings), including cells in which the model's mean is wrong, because the share depends on the dispersion and not on the level. This is the clearest case in which the hybrid design repairs a decision-relevant property that direct elicitation loses entirely.

## 5.8 Does calibrating the level repair the hybrid design?

The hybrid design inherits the model's mean, which was often wrong. An obvious repair is to rescale the model's expected counts so that their average equals the historical mean of the organization's customer file, keeping the external gamma multiplier of Proposition 2. We tested this offline on the stored expected counts of design D in every cell, with a fresh simulation of the counts (so the figures differ slightly from those in Sections 5.2 to 5.5), and added a baseline that uses no information from the model: every customer receives the reference mean, and the same gamma multiplier supplies the entire dispersion. This baseline is the reference distribution itself, up to sampling, and shows what the model adds.

Calibration repairs the mean: it matches the reference in 44 of 48 cells after calibration against 19 of 48 before (13 of 48 in the original simulation of Sections 5.2 to 5.5). It does not make the design match on all four statistics at once. The number of cells that match on mean, variance-to-mean ratio, zero share, and $\alpha$ together is 14 of 48 after calibration and 10 before, and 19 for the baseline with no model information (low-mean setting: 12, 7, and 15 of 16; high-mean setting: 2, 3, and 4; demographic households: 0 in all three). The remaining mismatches are mostly in the zero share and do not come from the model. A Poisson–gamma distribution with the reference mean and dispersion implies a zero share of 0.23 in the high-mean setting (real 0.19) and 0.07 for the demographic households (real 0.03), and the baseline shows the same misses. The squared coefficient of variation of the model's expected counts was small relative to $\alpha$ (0.00 to 0.75 against 3.05 at the low mean, and 0.00 to 0.07 against 0.71 for the demographic households), and with rank correlations to real counts near zero (Section 5.5) it does not identify which customers buy more. In this task the model supplies a level, and a model-free level from the organization's data does as well or better. Whether a model contributes more when personas carry informative histories is untested.

## 5.9 Do the cues a user can see reveal the errors that matter?

A user who inspects a synthetic population sees its mean, the sign of a promotion effect, the width of its intervals, and whether the answers parsed. We asked whether such cues reveal the errors that matter for a decision, defined for the transaction settings as an error in $1 + \alpha$ of more than a factor of 1.65 or an error of more than 0.15 in the top-decile share, and for the email experiment as a lift ratio outside 0.5 to 2. The thresholds were fixed before the analysis, and a cell passes a face-validity check if its mean is within 50% of the reference and fewer than 5% of answers failed to parse (in the email experiment, if both lifts have the right sign). Of the 191 transaction cells, 135 pass, and 60 of those (44%) have a large decision error, against 51 of the 56 cells that fail. The check works as a screen for gross failure, mainly because the hybrid design passes it with no large errors in 45 cells. It does not work for the designs that collapse: of the 48 direct and daily cells that pass, 47 have a large decision error, and in the email experiment all 32 configurations have the right sign while 15 of 16 purchase lifts and 5 of 16 visit lifts are outside the 0.5 to 2 range. The interval is not a reliable cue either. Across all cells the relative width of the interval of the mean correlates negatively with the decision errors (rank correlation -0.32 with the $\alpha$ error and -0.43 with the top-decile error), because collapsed answers have very narrow intervals, but within each design the sign reverses (+0.22 to +0.57), so the width tells a user little. The error of the mean is more informative: within the direct and daily designs it correlates with the decision errors (+0.42 to +0.78), yet nearly all cells that pass the check still carry large errors. With eight models the model-level permutation tests are not significant (p between 0.13 and 0.50).

## 5.10 Backtest of the acceptance test

Section 6.2 proposes that a system be accepted only if it reproduces the organization's own history. We tested this rule on the existing results, without new model calls. In the email experiment one email served as the past randomized test and the other as the new campaign (and the reverse), and the simulator was accepted only if its lift for the past campaign was within a factor of 2 of the measured one. A firm launches when the lift exceeds a break-even value, which we varied from one tenth to ten times the measured lift of the new campaign; a decision is wrong when simulated and measured lifts fall on different sides of it. Trusting the simulator gave wrong decisions at 29% of break-even values across the 64 cases, with a lift off by more than a factor of 2 in 69%, although the sign check passed in all of them. The gate admitted 20 cases, all for visits and none for purchases. Among the 32 visit cases, trusting the simulator gave 14% wrong decisions and a lift off by more than a factor of 2 in 12; among the 20 admitted cases the shares were 9% and 4. Rescaling the new lift by the past ratio lowered wrong decisions to 17% overall, but the lift stayed off by more than a factor of 2 in 59% of cases. Errors for the two campaigns are strongly correlated (Spearman 0.84), so a past test can reveal them, but for purchases they are too large to correct by one factor.

In the transaction settings we gated on the reference mean and zero share and checked the top-decile share implied by the simulated $\alpha$ (Proposition 3(b)). Of 187 cells, 133 passed the face-validity check, and 50% of them had a top-decile share off by more than 0.10. The gate admitted 18 cells (14 hybrid, 4 describe-then-sample, none of direct or daily simulation), of which one was wrong. Because the hybrid design takes its dispersion from the reference, this shows that the gate removes failing designs, not that the hybrid is validated independently.

## 5.11 Summary of hypotheses and supplementary analyses

| Hypothesis | Evidence |
|---|---|
| H1. Designs A and B collapse. | Supported. The variance-to-mean ratio of designs A and B is below the reference in 93 of 95 cells (29 of 31 at the low mean, where the exceptions are a DeepSeek-V4-Pro cell for direct answers and a Sonnet 5 cell for daily simulation; 32 of 32 at the high mean; 32 of 32 for the demographic personas). The zero share of designs A and B is at most 0.02 in the two high-mean settings and below the real value in 26 of 32 low-mean cells. |
| H2. Design C approaches but does not exceed its ceiling and under-produces zeros. | Partly supported. It stays below its ceiling in all 16 low-mean cells, reaches it in 3 of 16 high-mean cells and 10 of 16 cells with demographic personas, and its zero share is too low where the real share is large (0.74, 0.19) but close where it is small (0.03; 8 of 16 cells). |
| H3. Design D reproduces dispersion; fidelity depends on the model's mean. | Partly supported. It matches the reference ratio in 32 of 48 cells, but matches mean, ratio, zero share, and $\alpha$ jointly in only 7 of 48 (5, 2, 0) because the model's mean is often wrong and, for the demographic households, the zero share is too high in every cell. |
| H4a. Direction is reproduced. | Mostly supported: the risk ratio exceeds one in all 32 probability cells (smallest 1.03), though individual seeds touch one in a few. |
| H4b. Absolute lift is overstated. | Supported for purchases: 15 of 16 configurations (median about ninefold). Not for visits: 4 of 16 are consistent with the real value, 8 are too small, and 4 are too large. |
| H4c. Similar treatments are not distinguished. | Supported. The gap between the two emails excludes zero in 7 of 32 cells; in six the sign is opposite to the real one, and in one it is right but half the size. |
| S1. Purchases remain concentrated among heavy buyers (Proposition 3). | Direct and daily designs lose concentration (below the reference in all 91 interpretable cells); describing a distribution recovers part; the hybrid design matches in 39 of 48 cells. |
| S2. Calibrating the model's level repairs the hybrid design. | Partly. The mean matches in 44 of 48 cells after calibration (19 before in the same simulation), but cells matching on all four statistics rise only from 10 to 14 of 48, and a baseline that uses no model information matches in 19. |
| S3. Collapse is robust to the mean level, richer personas, and model scale. | Collapse is not specific to low means (direct answers have ratios of at most 0.87, 0.36, and 0.53 in most cells at means of 0.5, 4.8, and 7.8). Richer personas do not repair it (rank correlations with real counts -0.11 to +0.08; demographics explain about 1% of the heterogeneity). Larger and more recent models do not escape it (ratios of at most 1.00 in 42 of 48 direct cells; the hybrid's mean matched in 13 of 48 cells). |
| S4. Visible cues reveal decision errors. | Partly. A face-validity check separates gross failures, but 47 of the 48 direct and daily cells that pass it have large decision errors, and interval width is not a reliable cue (Section 5.9). |
| S5. An acceptance test based on history screens out bad simulators. | Partly. In the email backtest among visit cases the gate cut wrong launch decisions from 14% to 9% and rejected every purchase case; in the transaction settings it rejected every direct and daily cell (Section 5.10). |

*Table 2. Hypotheses (H) and supplementary analyses (S), with evidence.*

# 6. Discussion

We lead with the contributions to information systems research (Section 6.1) and the design principles and acceptance test that follow from them (Section 6.2), then turn to the decision consequences and the cost of uncritical trust (Section 6.3) and the organizational arrangements that follow (Section 6.4). The marketing results of Section 5 serve as evidence for these contributions. Limitations are in Section 6.5.

## 6.1 Contributions to information systems research

*Design constraints for a class of artifacts that organizations are adopting without them.* Propositions 1 and 2 define a design constraint and a calibration mechanism for persona-conditioned generative systems, and the evidence is consistent with both. Variance-to-mean ratios of direct answers are at most 1.00 in 42 of 48 cells, whatever the mean or the model. When a model returns the same number for every household, the dispersion parameter takes the value $-1/\mu$ that Proposition 1 predicts (about -0.12 in the demographic experiment). And the design that follows Proposition 2 restores the concentration of purchases among heavy buyers in 39 of 48 cells where direct and daily designs lose it entirely (Section 5.7).

*Why the problem is managerial.* The constraint has organizational consequences that a purely statistical reading would miss (Section 3.8). The system's quality is bounded by the firm's data assets and not by the capability of the model: the model contributed little heterogeneity of its own (squared coefficients of variation of its rates of 0.00 to 0.75 against dispersion parameters of 0.71 to 3.05) and nothing that identified which customers buy more (rank correlations with real counts between -0.11 and +0.08). Calibrating the model's level to the historical mean repaired the mean in 44 of 48 cells, but a baseline that gave every customer the historical mean did as well or better on the joint fit (Section 5.8). The value of the generative component therefore has to be shown against the firm's own data, which is the data the system was meant to economize.

*The limits of AI-based decision support and of the "digital twin" idea.* A twin is usually understood as a replica that can stand in for the original in a decision. Our evidence supports a narrower reading. At the level of the individual customer, the demographic personas carried almost no information about real counts, so a customer-level replica is not supported. At the level of the population, the distribution of counts and the size of effects are reproduced only by designs in which the dispersion is supplied from outside the model and the level is checked against data. A claim that a simulated population is a twin is therefore a claim about specific properties, to be tested one by one: the share of zeros, the spread, the concentration among heavy buyers, and the absolute size of an effect.

*Supporting evidence for marketing analytics.* Describing a distribution (Jang et al. 2026, Zhang et al. 2025a) helps more at a high mean than at a low mean and under-produces zeros where they are common, which matters because the zero share decides how many customers a campaign does not reach. And evaluating a promotion simulator on relative effects alone is hazardous, because by $RR = 1 + d/p_0$ errors in the simulated base rate and in the simulated lift are confounded in the risk ratio.

## 6.2 Design principles and an acceptance test

The evidence supports five design principles. They are derived from our experiments and analytical results. The acceptance test was backtested on our own data (Section 5.10), but no principle has been tested as an intervention in an organization, so they remain hypotheses for design.

*Principle 1: Separate the level from the spread.* Take the expected rate of a customer from the model and the dispersion across customers from an external, calibrated source (Proposition 2), which places a statistical calibration layer behind the language model with the variance budget of Section 3.7 as its rule. Designs that let the model produce the spread itself collapsed, while the hybrid design matched the reference dispersion in 32 of 48 cells and restored concentration (Section 5.7).

*Principle 2: Do not let the model produce the final integer or the daily draw.* Direct integer answers and day-by-day simulation returned nearly constant values in almost every cell, and their errors were systematic, not random.

*Principle 3: Calibrate the level, and invest in customer data before model capability.* Because the persona bounds what the model can carry (Section 3.8), the data assets that feed the persona matter more than the choice of model. Rescaling the model's rates to the historical mean repaired the mean in 44 of 48 cells (19 before in the same simulation; Section 5.8), but a baseline that gives every customer the historical mean did as well or better on the joint fit, so calibration should be paired with a test against such a baseline to show what the model adds.

*Principle 4: Treat context and wording as design parameters that must be validated.* A stated base rate changed some outputs by an order of magnitude and in several cells made the model repeat the stated number for every customer.

*Principle 5: Evaluate on absolute effects against a randomized benchmark.* Risk ratios hid errors in the simulated base rate (Section 5.6).

The principles imply an acceptance test that a system should pass before it enters a planning process. The test compares the synthetic output with the organization's own history on the variance-to-mean ratio, $\alpha$, the zero share, and the share of purchases made by the top decile of customers, with intervals; compares the hybrid design with a baseline that uses no model information; checks sensitivity to the prompt context; and compares the simulated base rate and absolute lift, not only the risk ratio, with a past randomized test. These errors cannot be seen by inspecting the output: the sign was right in nearly all cells, and the answers were fluent.

## 6.3 Decision consequences and the cost of uncritical trust

The central managerial risk is not that synthetic customers are useless but that they are trusted without being tested. A stylized example shows the consequence for a decision. A firm launches a promotion if the lift in purchase probability exceeds the ratio of cost to margin. Suppose a promotion costs 1 monetary unit per targeted customer and each purchase earns a margin of 50, so the ratio is 0.02. The real lift from the men's email was 0.0068, so the randomized test says not to launch: a campaign to 100,000 customers has an expected result of $0.0068 \times 50 - 1 = -0.66$ per customer, a loss of about 66,000. The simulated lift exceeded 0.02 in 13 of 16 configurations, and the median simulated lift of 0.063 predicts about $+2.1$ per customer, a profit of about 213,000. The gap of about 280,000 for a single campaign favors launching, and because the error is systematic it does not average out over campaigns. The numbers are ours, not the retailer's, but the example shows how an overstated lift turns directly into a wrong go decision.

Three further risks follow from our evidence. *False precision:* the simulated lifts often came with narrow intervals that excluded the real value, and the width of an interval is not a reliable cue to the size of the decision error (Section 5.9), so statistical precision, which a synthetic population gives cheaply, must not be mistaken for validity. *Erosion of the evidence base:* if synthetic results replace randomized tests because they are faster and cheaper, the organization loses the data that would reveal the error and that its calibration step needs (Section 3.8), and the failure becomes self-concealing. *Propagation:* synthetic customers used as inputs to forecasts or other learned systems carry their compressed spread with them, so concentration is lost (Proposition 3) and the share of non-buyers is distorted, and the result enters downstream decisions as if it were observed data. These risks argue against using the technology as a replacement for evidence rather than as a complement to it, and against purchasing decisions based on demonstrations of fluency and plausible averages.

## 6.4 Organizational accountability: validating and governing synthetic data in analytics systems

The following arrangements follow from our evidence and from the artifact view; we did not test them in an organization.

*Treat validation as an acceptance gate with named owners.* Before synthetic customers enter a planning process, the system should pass the acceptance test of Section 6.2 against the organization's own history. Marketing owns the reference data and the decision requirements, and information systems owns the pipeline, the model versions, and the calibration step. A decision that rests on a vendor's model, an analyst's prompt, and a calibration step maintained by another team has no owner for its errors unless accountability is assigned before use.

*Re-validate when a component changes.* The eight models differed widely in the same design, and the same model reacted differently to different prompt context. A vendor update, a switch of model or provider, or a change of prompt template should trigger the acceptance test again.

*Use synthetic data where its errors do the least harm, and keep it separate from real data.* The designs reproduced the sign of a promotion effect but not its size, so synthetic customers suit screening, ranking, and hypothesis generation better than sizing a campaign, for which a randomized holdout remains the standard. Provenance labels and a rule against pooling synthetic and real records keep their compressed spread out of downstream models.

*Weigh the savings against the cost of a wrong decision, and build the correcting loop.* The runs are cheap (under about eleven US dollars for 25,600 calls with the models we priced); the relevant cost is the decision made on the output. Storing the simulated and realized lift of each past campaign lets the system track its own bias.

## 6.5 Limitations and future research

The evidence is preliminary. Every design has one prompt wording, so our intervals capture the sampling of customers but not variation across prompts. All eight models were run on three seeds. Per-seed variance-to-mean ratios were stable for the direct and daily designs but varied more for the describe and hybrid designs (median ranges 0.9 and 1.2), so counts of cells that match the reference are approximate. The low-mean reference is a calibrated parametric distribution, the Complete Journey households are loyalty-card shoppers, and campaigns there were targeted rather than randomized, so only the email experiment supports a causal comparison. The demographic personas contain almost no information about purchase frequency; personas that carry purchase histories would be a stronger test of Proposition 1 and of whether the model contributes more than a level. Whether still larger or reasoning-enabled models collapse less remains open, and public data may be part of the models' training data. The principles and organizational arrangements have not been tested in an organization, and the backtest of the acceptance test (Section 5.10) uses one pair of campaigns. Future work should use a randomized promotion data set with purchase counts, for example from a partner firm, so that count distributions and treatment effects can be studied on the same customers.

# 7. Conclusion

A synthetic-customer system is an artifact whose quality cannot be read from its output. We showed that a persona-conditioned generative component can transmit only the customer heterogeneity that its persona describes, that the remainder must be supplied and calibrated by a layer connected to the firm's own data, and that this turns a familiar statistical fact into a managerial problem: the spread of simulated behavior is no longer disciplined by the firm's data, it cannot be seen from inside the system, and it can be checked only against the real data that the system was meant to economize. Evidence from eight language models, three transaction settings, and a randomized email experiment is consistent with this account. Direct and day-by-day designs lose the concentration of purchases among heavy buyers; taking the level from the model and the spread from an external calibrated source restores it; calibrating the level repairs the mean, but a baseline that uses the historical mean alone does about as well; and purchase lifts are overstated in 15 of 16 configurations, enough to turn a no-go decision into a go. For organizations the implication is a short list of duties: validate against the firm's own data before use, revalidate when the model, provider, or prompt changes, keep synthetic data apart from real data, keep running randomized tests, and assign accountability before the artifact is used. Future research should study these arrangements in organizations and test whether personas with informative purchase histories give the generative component more to contribute.

# References {-}

{{REFS}}

# Appendix A. Prompt Templates {-}

Persona text, low-mean setting: "You are a customer of an online giftware retailer. Profile: {segment}, age {age}, based in {country}. You made your first purchase 4 weeks ago." Anchored variant adds: "Context: customers of this retailer make on average about 0.5 purchases per 4 weeks, and most make none."

Persona text, high-mean setting: "You are a household with a loyalty card at a supermarket chain and you do part of your grocery shopping there. Profile: {segment}, head of household aged {age}, {household size} person(s)." Anchored variant adds: "Context: households in this loyalty program make on average about 5 shopping trips to the chain per 4 weeks, and some make none."

Questions. Design A: "How many separate purchases will you make in the next 4 weeks? Answer with ONLY an integer." Design B: "Week {w} of the next 4 weeks: for each of its 7 days decide whether you make a purchase that day. Reply with ONLY 7 comma-separated 0/1 values." Design C: "Give the probabilities of making {bins} purchases in the next 4 weeks. Reply with ONLY JSON like {...} summing to 1." Design D: "What is your expected average number of purchases per 4 weeks (can be fractional, e.g. 0.4)? Reply with ONLY a number." Email experiment: persona from the customer's recency, 12-month spend, merchandise bought, area, new or existing status, and channel, followed by one of three sentences describing the email received, and "What is the probability, from 0 to 100 percent, that you will {visit the retailer's website / make a purchase from the retailer} during the next two weeks? Reply with ONLY a number."

# Appendix B. Full Results {-}

{{TABLE_RETAIL}}

*Table B1. Low-mean setting, per cell. Reference row: negative binomial with mean 0.49 and alpha 3.05. \* the 95% bootstrap interval excludes the reference value. Temperatures are pooled for GPT-4o-mini and Llama.*

{{TABLE_GROCERY}}

*Table B2. High-mean setting, 600 customers per cell. Reference row: empirical Complete Journey distribution. \* the 95% bootstrap interval excludes the reference value.*

{{TABLE_DEMO}}

*Table B3. Persona experiment with real household demographics, 600 household-windows per cell. Reference row: real distribution of the 801 households (10,413 household-windows). \* the 95% bootstrap interval excludes the reference value.*

{{TABLE_HILL}}

*Table B4. Email experiment, probability-elicitation design (mean elicited probability over 300 simulated customers per seed, three independent calls per customer, pooled over three seeds, 900 customers per model). Lift = probability with the email minus probability without it; gap = lift of the men's email minus lift of the women's email; intervals are 95% paired bootstrap intervals over customers (real values: normal approximation). RR = risk ratio, the mean of the three per-seed ratios; its asterisk is set only if the interval excludes the real ratio in all three seeds. \* the simulated and the real intervals do not overlap.*

{{TABLE_SUMMARY}}

*Table B5. Low-mean and high-mean settings: range of results across the model-and-prompt cells of each design (sixteen cells in each setting). Reference rows are the real values. For design A in the low-mean setting the variance-to-mean ratio of 1.00 comes from a cell in which practically every simulated customer answered "0" and is uninformative.*

{{TABLE_DEMO_SUMMARY}}

*Table B6. Persona experiment with real household demographics: range of results across the 16 model-and-prompt cells of each design (600 household-windows per cell). The last column is the range of the Spearman correlation between the simulated count and the household's real count in the same window.*

# Appendix C. Reproducibility {-}

All code, the pilot grid runner, the demographic-ceiling script, the analysis scripts, and the tables and figures used here are in an anonymized project repository (the link will be provided after the review process to preserve double-blind review). Raw model responses are saved with each run. Household-level Complete Journey data are not redistributed; the code reads them from the public package files.

# Appendix D. Proofs of Propositions 1 to 3 {-}

**Proposition 1.**  The first statement is the law of total variance. With $v(X) = 0$, $\text{Var}(N^*) = \text{Var}(m(X))$, and substituting into the definition of $\alpha$ gives $\alpha^* = c^2 - 1/\mu^*$. If $m(X) = E[\Lambda \mid X]$, then $\mu^* = \mu$ and $\text{Var}(m(X)) = \text{Var}(\Lambda) - E[\text{Var}(\Lambda \mid X)]$, which yields the last expression. $\square$

**Proposition 2.**  By independence, $E[\Lambda^2] = E[\lambda(X)^2]\,E[G^2] = \mu^2(1 + c^2)(1 + \alpha_w)$, and $\alpha = E[\Lambda^2]/\mu^2 - 1$. $\square$

**Proposition 3.***Proof.* (a) Let $A$ be any event with $P(A) = q$. Then $E[\Lambda \mathbf{1}_A] = \mu q + \text{Cov}(\Lambda, \mathbf{1}_A)$, and the Cauchy–Schwarz inequality gives $\text{Cov}(\Lambda, \mathbf{1}_A) \le \sqrt{\text{Var}(\Lambda)}\sqrt{q(1-q)} = \mu\sqrt{\alpha q(1-q)}$. This bounds $S_q$ from above. For the lower bound take an event that is independent of $\Lambda$ and has probability $q$ (on a sufficiently rich probability space, or by assigning ties fractionally); it yields $E[\Lambda \mathbf{1}_A] = \mu q$.

(b) Let $\Lambda$ have density $f_{k,\theta}$ with $\mu = k\theta$. Since $\lambda f_{k,\theta}(\lambda) = k\theta\, f_{k+1,\theta}(\lambda)$, we have $E[\Lambda \mathbf{1}\{\Lambda > x\}] = \mu\, P(G_{k+1,\theta} > x)$ for a gamma variable $G_{k+1,\theta}$ with shape $k+1$ and scale $\theta$. The maximum in the definition of $S_q$ is attained by the event $\{\Lambda > x_q\}$ with $P(\Lambda > x_q) = q$, because $E[\Lambda \mathbf{1}_A]$ is largest when $A$ collects the largest values of $\Lambda$. Hence $S_q = P(G_{k+1,\theta} > x_q)$ with $x_q = \theta F_k^{-1}(1-q)$, which is the stated expression.

(c) The limit follows from (a), because the upper bound tends to $q$ as $\alpha \to 0$. For monotonicity let $k_1 < k_2$, so that $\alpha_1 > \alpha_2$, and let $Y_j$ be gamma variables with shape $k_j$ and mean one. By the beta–gamma algebra, if $G \sim \text{Gamma}(k_2, 1)$ and $B \sim \text{Beta}(k_1, k_2 - k_1)$ are independent, then $BG \sim \text{Gamma}(k_1, 1)$. Hence $Y_1$ has the distribution of $M Y_2$ with $Y_2 = G/k_2$ and $M = B k_2/k_1$, where $M$ is independent of $Y_2$, non-degenerate, and has $E[M] = 1$. Let $A^* = \{Y_2 > x^*\}$ be the event with probability $q$ that attains $S_q$ for $Y_2$. Then $S_q(\alpha_1) \ge E[M Y_2 \mathbf{1}_{A^*}] = E[M]\,E[Y_2 \mathbf{1}_{A^*}] = S_q(\alpha_2)$. The inequality is strict, because the maximizing event for $M Y_2$ is $\{M Y_2 > y^*\}$, which differs from $A^*$ with positive probability when $M$ is non-degenerate, and the maximizing event is unique up to null sets.

(d) The argument of (a) uses only the mean and the variance of the nonnegative variable and holds for any event of probability $q$, including events defined by ranking customers on their counts (ties are broken arbitrarily). For a deterministic simulator $\text{Var}(N^*) = \text{Var}(m(X))$, so the squared coefficient of variation of $N^*$ is $c^2$.

 $\square$
