::: {custom-style="Title"}
Counting Customers with Language Models: Heterogeneity Compression in Synthetic Purchase Data
:::

::: {custom-style="Author"}
Manuscript prepared for submission to *Information Systems Research* (author information omitted for review)
:::

**Abstract**

Large language models (LLMs) are increasingly used to create synthetic customers for pre-testing marketing decisions, but evaluations have concentrated on ratings, choices, and stated willingness to pay. We study an output that customer analytics depends on more directly: the number of purchases a customer makes in a period. Building on the Poisson–gamma account of purchase counts, we show analytically that overdispersion measures unobserved customer heterogeneity, derive how much of it a persona-conditioned simulator can carry, and show how a hybrid design avoids double counting. We evaluate four elicitation designs across eight LLMs in public transaction settings (mean counts of about 0.5, 4.8, and 7.8) and in a randomized email experiment. Direct and day-by-day designs collapse toward a single value in nearly every model and setting, and larger, more recent models do not change this. Describing a distribution recovers part of the dispersion but under-produces zero counts where zeros are common. Personas built from real household demographics change nothing, because those demographics explain about 1% of the heterogeneity in counts. The hybrid matches dispersion only when the model's mean is accurate. Promotion effects have the right sign in most settings, yet their size varies by an order of magnitude with model and prompt, and the absolute lift in purchase probability is overstated in 15 of 16 configurations (median about tenfold). We offer a diagnostic protocol for practitioners who consider synthetic customers for decision support.

**Keywords:** synthetic customers, large language models, purchase counts, overdispersion, customer heterogeneity, decision support, digital twins

# 1. Introduction

Firms routinely test promotions, prices, and messages before committing money to them. Large language models (LLMs) promise a cheaper way to do so: prompt a model with a customer description, ask what that customer would do, and repeat for thousands of customers. Early studies found that such synthetic respondents produce plausible willingness-to-pay estimates and conjoint results (Brand et al. 2023), reproduce the qualitative pattern of classic behavioral experiments (Horton 2023), and, with suitable elicitation, mimic human purchase-intent ratings (Maier et al. 2025). Vendors now market "digital twins" of consumer panels on this basis.

What counts as validation in these studies is almost always a rating, a choice, or a price. Customer analytics, however, runs on counts. The number of purchases or visits per customer and period feeds customer lifetime value, repeat-purchase forecasts, and budget allocation, and marketing science has long modeled these counts as a Poisson process whose rate differs across customers (Ehrenberg 1959, Schmittlein et al. 1987, Fader et al. 2005). Because of this structure, the spread of a count distribution carries information about something firms care about, namely how much customers differ. A simulator that gets the average right but flattens the spread will mislead any decision that depends on heavy buyers, on the share of customers who do not buy at all, or on the uncertainty around a forecast.

There is good reason to worry about flattening. Studies of silicon samples repeatedly report variance collapse: simulated answers cluster on the modal response and are narrower than human ones (Li et al. 2025, Tigre and Souto 2026), and instruction-tuned models appear unable to sample from distributions they can otherwise describe (Jang et al. 2026). For count data this problem has a precise statistical form. If customers differ in their purchase rates, counts are overdispersed relative to a Poisson process; a simulator that compresses heterogeneity therefore shows up first as underdispersion and as a distorted share of zeros. Yet we found no study that evaluates LLM-generated purchase counts against Poisson or negative binomial benchmarks.

We ask four questions. Does the per-period purchase-count distribution of synthetic customers match the real one in mean, dispersion, zero share, and tail (RQ1)? Does variance collapse appear in count data as underdispersion (RQ2)? Do the elicitation and sampling design change fidelity (RQ3)? And does the promotion effect estimated with synthetic customers agree with a randomized experiment in direction and size (RQ4)? To answer them we compare four elicitation designs, run with eight LLMs and two prompt variants, against public transaction data sets whose mean counts differ by a factor of ten or more, and we test the same models against a randomized email experiment.

The study makes four contributions. First, we give a short analytical account of how much heterogeneity a persona-conditioned simulator can carry, and of how an externally injected heterogeneity term must be calibrated to avoid double counting (Propositions 1 and 2). Second, we provide evidence across designs, models, and settings that direct and day-by-day designs collapse, that describing a distribution only partly repairs the problem, and that a hybrid design reproduces dispersion only when the model supplies an accurate mean. Third, in the experimental setting we show that relative and absolute effects can tell different stories when the simulated base rate is wrong, and that the absolute lift in purchase probability is overstated in 15 of the 16 configurations we tested. Fourth, we translate these findings into a diagnostic protocol for practitioners.

The remainder of the paper is organized as follows. Section 2 reviews the literature and states the gap. Section 3 develops the framework and hypotheses. Section 4 describes the data, designs, and measures. Section 5 reports results, Section 6 discusses implications and limitations, and Section 7 concludes.

# 2. Related Literature

## 2.1 LLMs as synthetic respondents and customers

LLMs are increasingly proposed as inexpensive stand-ins for consumer panels. Early work suggested that GPT-based respondents can produce plausible willingness-to-pay estimates and conjoint results (Brand et al. 2023), that simulated agents reproduce the qualitative pattern of classic behavioral experiments (Horton 2023), and that LLM-driven agents can be placed in simulated markets to test discount strategies (Chu et al. 2025). Evidence on preferences is more mixed: Goli and Singh (2023) report that GPT models are less patient than humans in intertemporal choices. Related studies find that LLM-generated data can track the direction of experimental treatment effects, although the magnitudes tend to be overstated (Hewitt et al. 2024). Direct elicitation of numerical ratings yields response distributions that are unrealistically narrow, and recent methods address this by mapping free-text answers to rating scales through embedding similarity (Maier et al. 2025).

## 2.2 Variance collapse and sampling

The narrowness of simulated responses is now well documented. Silicon samples drift toward the modal answer within demographic subgroups (Li et al. 2025), consumer panels built from LLMs show variance compression and sign flips in estimated coefficients (Tigre and Souto 2026), and instruction-tuned models appear unable to draw independent samples from the distribution they can otherwise describe (Jang et al. 2026; see also Gu et al. 2024). Prompting a model to list several candidate answers together with their probabilities partly restores diversity (Zhang et al. 2025a). In operations management, LLMs often reproduce the outcome of a hypothesis test while diverging from human data in the full response distribution, with mismatched dispersion playing a central role (Zhang et al. 2025b).

## 2.3 Counts in customer analytics

Nearly all of this evidence concerns bounded, ordinal, or continuous responses such as ratings, choices, and prices. Purchase and visit counts differ in an important way. They are nonnegative integers whose variance is tied to their mean, and in marketing practice they are modeled as a Poisson process whose rate varies across customers, giving a negative binomial distribution in aggregate (Ehrenberg 1959, Schmittlein et al. 1987, Fader et al. 2005). For this reason, overdispersion relative to the Poisson is the empirical signature of customer heterogeneity (Cameron and Trivedi 1990), and a simulator that compresses heterogeneity should show up first as underdispersion. These distributions also feed customer lifetime value, repeat-purchase forecasts, and budget allocation, so errors in their shape propagate directly into downstream decisions.

## 2.4 Research gap

The studies closest to ours stop short of this question. Huang and Wang (2026) model aggregate demand as a mixture of persona-level purchase probabilities, but within a single period and without repeat counts. Sashihara et al. (2025) use the distribution of purchases per buyer as a validation metric for a simulated marketplace, without testing it against Poisson or negative binomial benchmarks. Chen (2026) compares LLM user simulators with verified payment outcomes and finds that they overstate purchase propensity among customers who ultimately do not buy, but the outcome there is a binary conversion rather than a count. Calibration frameworks such as SYN-DIGITS (Fan et al. 2026) align simulated responses with human ground truth at the individual and distributional level, yet, to our reading, they do not exploit the Poisson–gamma structure that governs count data. To our knowledge, and within the scope of our search, no prior study evaluates whether LLM-generated per-customer purchase counts reproduce the dispersion, zero proportion, and tail behavior of observed count data, or examines how the way heterogeneity is injected affects that fidelity.

# 3. Theoretical Framework and Hypotheses

## 3.1 Purchase counts as a Poisson–gamma mixture

Let customer $i$ have a latent purchase rate $\Lambda_i$ for the period, with mean $\mu = E[\Lambda]$, and let the observed count satisfy $N_i \mid \Lambda_i \sim \text{Poisson}(\Lambda_i)$. Then $E[N] = \mu$ and $\text{Var}(N) = \mu + \text{Var}(\Lambda)$. We define the overdispersion parameter
$$\alpha = \frac{\text{Var}(N) - E[N]}{E[N]^2} = \frac{\text{Var}(\Lambda)}{\mu^2},$$
the squared coefficient of variation of the rate, so that the variance-to-mean ratio equals $1 + \alpha\mu$. When $\Lambda$ follows a gamma distribution, $N$ is negative binomial with dispersion $\alpha$. The quantity $\alpha$ is thus a direct measure of unobserved customer heterogeneity, and it does not depend on the mean, whereas the variance-to-mean ratio does. We report both: the variance-to-mean ratio is easier to read, and $\alpha$ permits comparison across settings with different means.

## 3.2 What a persona-conditioned simulator can carry

A synthetic customer is generated from a persona description $X$. Suppose that, given $X$, the simulator returns a count with conditional mean $m(X)$ and conditional variance $v(X)$, and let $\mu^* = E[m(X)]$.

**Proposition 1.** The simulated counts $N^*$ satisfy $\text{Var}(N^*) = E[v(X)] + \text{Var}(m(X))$. If the simulator is deterministic given the persona, so that $v(X) = 0$, then
$$\alpha^* = c^2 - \frac{1}{\mu^*}, \qquad c^2 = \frac{\text{Var}(m(X))}{\mu^{*2}},$$
and the simulated counts are underdispersed ($\alpha^* < 0$) whenever $\text{Var}(m(X)) < \mu^*$. If in addition $m(X) = E[\Lambda \mid X]$, then $\alpha^* = \alpha - R - 1/\mu$, where $R = E[\text{Var}(\Lambda \mid X)]/\mu^2$ is the share of heterogeneity that the persona does not explain.

*Proof.* The first statement is the law of total variance. With $v(X) = 0$, $\text{Var}(N^*) = \text{Var}(m(X))$, and substituting into the definition of $\alpha$ gives $\alpha^* = c^2 - 1/\mu^*$. If $m(X) = E[\Lambda \mid X]$, then $\mu^* = \mu$ and $\text{Var}(m(X)) = \text{Var}(\Lambda) - E[\text{Var}(\Lambda \mid X)]$, which yields the last expression. $\square$

Proposition 1 identifies two losses. A deterministic simulator drops the Poisson noise (the term $-1/\mu$), and it cannot carry any heterogeneity that the persona does not describe (the term $R$). Both losses are present in direct integer answers. Because real customers differ in ways that a short persona cannot capture, $R$ is rarely small, and collapse toward a single answer is the expected outcome rather than an anomaly.

## 3.3 Injecting heterogeneity without double counting

An obvious repair is to let the model supply only a persona-level mean $\lambda(X)$ and to add the missing heterogeneity from an external random multiplier. Let $\Lambda = \lambda(X)\,G$, where $G$ is independent of $X$, $E[G] = 1$, and $\text{Var}(G) = \alpha_w$.

**Proposition 2.** With $c^2 = \text{Var}(\lambda(X))/E[\lambda(X)]^2$,
$$1 + \alpha = (1 + c^2)(1 + \alpha_w).$$
Consequently, setting $\alpha_w$ equal to the total target $\alpha$ implies an overdispersion of $(1 + c^2)(1 + \alpha) - 1 > \alpha$, an overstatement of $c^2(1 + \alpha)$.

*Proof.* By independence, $E[\Lambda^2] = E[\lambda(X)^2]\,E[G^2] = \mu^2(1 + c^2)(1 + \alpha_w)$, and $\alpha = E[\Lambda^2]/\mu^2 - 1$. $\square$

Proposition 2 gives the calibration rule used in our hybrid design: the external multiplier must carry only the within-persona heterogeneity $\alpha_w = (1 + \alpha)/(1 + c^2) - 1$. It also shows that the hybrid reproduces dispersion by construction, so that its fidelity depends on the one thing the model still supplies, the accuracy of $\lambda(X)$.

## 3.4 Describing a distribution, and a ceiling

A third design asks the model to state probabilities for count bins and then samples a count externally. Because the top bin must be closed to be sampled, this design cannot produce the extreme tail of the real distribution. The variance-to-mean ratio attainable by a perfect description is that of the reference distribution after each bin's mass is spread uniformly within the bin. For the bins we use, this ceiling is 2.10 (with $\alpha$ of 2.33) in the low-mean setting and 6.61 (with $\alpha$ of 1.18) in the high-mean setting, against real values of 2.49 and 7.85. Comparisons for this design are therefore made against the ceiling as well as against the real value.

## 3.5 Relative and absolute effects

Let $p_0$ be the probability of an outcome without a promotion and $d$ the absolute lift caused by it. The risk ratio is $RR = 1 + d/p_0$. A simulator that has the lift right but the base rate wrong therefore produces the wrong risk ratio, and a simulator that has the base rate right but overstates the lift produces an inflated one. Because revenue depends on the absolute lift $d$, evaluating a simulator on risk ratios alone can lead to opposite conclusions from evaluating it on lifts.

## 3.6 Hypotheses

Proposition 1 motivates the first hypothesis, Proposition 2 and Section 3.4 the second and third, and Section 3.5 the fourth.

- **H1 (collapse).** Direct answers (design A) and day-by-day simulation (design B) yield variance-to-mean ratios below the real value and fewer zero counts than the real data.
- **H2 (description).** Describing a distribution (design C) raises dispersion toward, but not beyond, the ceiling of its bins, and yields too few zeros.
- **H3 (hybrid).** The hybrid (design D) reproduces dispersion, and its fidelity depends on the accuracy of the model's mean.
- **H4 (effects).** In an experiment, simulated promotion effects (a) have the correct sign, (b) overstate the absolute lift when the simulated base rate is overstated, and (c) fail to distinguish similar treatments.

We also ask, as an exploratory question, whether collapse is specific to settings with low mean counts, as one might expect if the model rounds small expected counts to 0, 1, or 2.

# 4. Research Design

## 4.1 Settings and reference data

Table 1 summarizes the three reference settings. In the first, the reference is a negative binomial distribution calibrated to the 4-week purchase counts of customers in the public Online Retail II transaction file (Chen 2019) whose first purchase fell in the first three months: mean 0.49, variance-to-mean ratio 2.49, zero share 0.74, and $\alpha = 3.05$. Our re-aggregation of the public file gave a similar profile (mean 0.43 to 0.51, zero share 0.66 to 0.72, and $\alpha$ between 2.2 and 4.2 across seven consecutive windows, for a cohort of 1,731 customers), and the Cameron and Trivedi (1990) test rejected the Poisson model in every window. In the second, the reference is the empirical distribution of 4-week basket counts, pooled over 13 windows, for the 2,469 loyalty-card households of the dunnhumby Complete Journey data in 2017 (32,097 household-windows). Negative binomial was the best-fitting model by AIC in every window, and the Poisson model was rejected in all of them. In the third, the benchmark is the randomized email test of Hillstrom (2008), in which 64,000 customers received no email, a men's merchandise email, or a women's merchandise email, and visits and purchases were recorded for the following two weeks.

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

We used eight LLMs through the OpenRouter interface: GPT-4o-mini, Llama-3.3-70B-Instruct, and Claude Haiku 5.5 in the first runs, and Claude Sonnet 5, GPT-5.6-terra, DeepSeek-V4-Pro, Gemini 3.1 Flash-Lite, and Mistral Large 4, which were added to test whether larger and more recent models behave differently. The first three models (GPT-4o-mini, Llama-3.3-70B, and Haiku 5.5) were run on three random seeds, that is, on three independent samples of customers; the five newer models were run on one seed. In the low-mean setting GPT-4o-mini and Llama were run at temperatures 0.3, 0.7, and 1.0 in the first seed and at 0.7 in the two further seeds, giving 1,000 customers per cell; Haiku 5.5 contributes 600 (three seeds of 200), and the other five models 200. In the two high-mean settings the temperature was fixed at 0.7, with 600 customers per cell for the three models run on three seeds and 200 for the others. In the email experiment each seed uses 300 customers (900 for the three models run on three seeds). Three models (Haiku 5.5, Sonnet 5, and GPT-5.6-terra) do not accept a temperature setting and contribute one run per prompt variant and seed. For every model that allows it, hidden reasoning was switched off so that short answers are not truncated. For each cell we report the mean, the variance-to-mean ratio, the zero share, and $\alpha$, with 95% bootstrap intervals over customers. An asterisk marks an interval that excludes the reference value. Parsing failed for 5% or less of the responses in all cells but two: DeepSeek-V4-Pro returned unusable answers for about 10% of the daily-simulation prompts in the high-mean setting, and those cells are computed from the parsed responses only.

## 4.4 Email experiment

For each of 300 customers sampled from the real data (a new sample for each seed) we asked, in separate independent calls, for the probability (0 to 100 percent) that the customer would visit the website, and that it would make a purchase, in the next two weeks, under each of three conditions: no email, a men's email, and a women's email. We report the risk ratio and the absolute lift (the probability with the email minus the probability without it), the latter with paired bootstrap intervals over customers. Yes/no answers and Bernoulli draws from the elicited probabilities were also collected and are discussed where relevant. Because each call sees only one condition, the design mimics random assignment but does not equal it.

# 5. Results

## 5.1 Overview

Table 2 summarizes the low-mean and the high-mean setting by design, and Appendix B gives all cells. The main pattern is that variance collapse is severe in designs A and B in every setting, that design C moves toward the real dispersion but loses zeros where they are common, and that design D matches dispersion in most cells while its mean depends on the model.

| Setting | Design | Mean | Var/mean | Zero | Alpha |
|---|---|---|---|---|---|
| Low mean | Reference | 0.49 | 2.49 | 0.74 | 3.05 |
| Low mean | A Direct | 0.00 to 2.15 | 0.00 to 18.37 | 0.00 to 1.00 | -1.00 to 8.06 |
| Low mean | B Daily | 0.00 to 13.56 | 0.24 to 2.96 | 0.00 to 1.00 | -0.67 to 0.63 |
| Low mean | C Describe | 0.37 to 1.30 | 0.95 to 1.61 | 0.32 to 0.71 | -0.10 to 0.80 |
| Low mean | D Hybrid | 0.28 to 0.93 | 1.46 to 3.38 | 0.63 to 0.80 | 1.67 to 4.06 |
| High mean | Reference | 4.84 | 7.85 | 0.19 | 1.42 |
| High mean | A Direct | 3.73 to 11.82 | 0.00 to 2.38 | 0.00 to 0.02 | -0.20 to 0.16 |
| High mean | B Daily | 4.45 to 16.65 | 0.04 to 0.40 | 0.00 to 0.01 | -0.19 to -0.06 |
| High mean | C Describe | 4.13 to 7.79 | 3.18 to 6.44 | 0.01 to 0.14 | 0.40 to 1.00 |
| High mean | D Hybrid | 3.09 to 7.87 | 5.84 to 13.01 | 0.09 to 0.28 | 0.95 to 2.11 |

*Table 2. Range of results across the model-and-prompt cells of each design (sixteen cells in each setting). Reference rows are the real values. For design A in the low-mean setting the variance-to-mean ratio of 1.00 comes from a cell in which practically every simulated customer answered "0" and is uninformative.*

![Figure 1. Variance-to-mean ratio of simulated purchase counts with 95% intervals, by design (columns), model (rows), and setting (a: low mean; b: high mean; c: real household demographics). The dashed line is the real value; the dotted line is the largest value that design C can reach with its count bins. Filled markers: plain prompt; hollow markers: anchored prompt.](fig1_dispersion.png){width=6.4in}

## 5.2 Low-mean setting

Direct and daily designs rarely reproduce the real dispersion. In 45 of the 47 cells of designs A, B, and C with a defined ratio, the upper bound of the variance-to-mean interval is below the reference of 2.49 (Table B1, Figure 1a). Two cells go the other way. DeepSeek-V4-Pro without the anchor gives direct answers with a ratio of 18.4 (interval 3.0 to 30.6), because a few customers receive very large counts alongside many zeros (mean 2.15, zero share 0.55); and Sonnet 5 without the anchor gives daily simulations with a ratio of 2.96 (2.58 to 3.34). Elsewhere direct answers are the most compressed, with ratios of at most 0.86 in 12 of 16 cells; in three further cells nearly every answer was "0" (Llama, Sonnet 5, and Mistral Large 4 with the anchor), which gives a ratio near one and no information. With the anchor, five cells in all (those three, and Sonnet 5 and GPT-5.6-terra for daily simulation) return "0" for 97% to 100% of customers, which follows the anchor text ("most make none") but carries no persona information. Without the anchor, daily simulation overstates the mean in every model (1.6 to 13.6 purchases in 28 days against 0.49) and stays close to Poisson or below it in most. Describing a distribution reaches ratios of 0.95 to 1.61, below its own ceiling of 2.10 in all 16 cells, and its zero share is too low (0.32 to 0.71, against 0.74) in every cell.

The hybrid matches the reference ratio in 7 of 16 cells, the mean in 8, the zero share in 13, and $\alpha$ in 14; all four in 5 cells (DeepSeek-V4-Pro in both prompt variants, and Gemini 3.1 Flash-Lite, Mistral Large 4, and GPT-5.6-terra with the anchor). Its variance-to-mean ratio misses mainly when the model's mean is low, because the ratio equals $1 + \alpha\mu$ and so inherits the error of the mean even when $\alpha$ is right. Agreement on dispersion is partly by construction, because the gamma multiplier injects it; what the model contributes is the mean, which is almost twice the reference for Llama with the anchor (0.93 against 0.49).

## 5.3 High-mean setting

A higher mean does not relieve the collapse of direct answers (Table B2, Figure 1b). In 15 of 16 cells the variance-to-mean ratio of design A lies between 0.00 and 0.76, against a reference of 7.85. The exception is Mistral Large 4 without the anchor, whose direct answers have real spread (ratio 2.38, interval 1.82 to 3.02, $\alpha = +0.16$) but still carry only a third of the real dispersion. Without the anchor GPT-4o-mini and Llama answered "8" for practically every customer; with the anchor all eight models returned numbers close to the stated base rate of 5 (means of 3.73 to 5.20), so that the answer carries little persona information. Daily simulation again misses the mean (4.45 to 16.65 trips against 4.84) and has almost no dispersion (ratios of 0.04 to 0.40, zero share of at most 0.01). In all 48 cells of designs A, B, and C the variance-to-mean interval lies entirely below the reference.

Describing a distribution reaches ratios of 3.18 to 6.44. Its intervals contain the ceiling of 6.61 in only 4 of 16 cells (4 of the 8 anchored cells), so the impression from the first three models that the anchor lets design C reach the ceiling does not generalize. Its weak point is the zero share: 0.01 to 0.14 against the real 0.19, below the reference in every cell. The hybrid matches the reference ratio in 15 of 16 cells, the mean in 7, the zero share in 8, and all four of mean, ratio, zero share, and $\alpha$ in 5: Haiku 5.5 without the anchor, GPT-4o-mini with it, Sonnet 5 in both variants, and Gemini 3.1 Flash-Lite with it. The remaining cells fail because the model's mean is wrong, for example 3.09 for Mistral Large 4 with the anchor and 7.87 for DeepSeek-V4-Pro without it.

## 5.4 Is collapse specific to low means?

If direct answers were underdispersed only because small expected counts are rounded to 0, 1, or 2, the problem should shrink at higher means. It does not. At a mean of 0.5, 12 of 16 direct-answer cells have variance-to-mean ratios of at most 0.86, three more are cells in which nearly every answer was "0", and one (DeepSeek-V4-Pro without the anchor) is overdispersed; at a mean of 4.8 the ratio is at most 0.76 in 15 of 16 cells, and at a mean of 7.8 it is at most 1.32. In every setting several models return one value for practically every customer. Collapse of direct answers is therefore not a rounding artifact of low means. Nor do larger or more recent models escape it: the ratios of Sonnet 5 and GPT-5.6-terra in the two high-mean settings lie between 0.02 and 0.31 for direct and daily designs.

## 5.5 Richer personas from real household demographics

The personas used so far were deliberately simple. To test whether richer personas change the picture, we drew 200 household-windows at random from the 801 Complete Journey households with demographic records and described each household by its real age group, household type and size, number of children, marital status, income, and home ownership. This design also lets us compare each simulated count with that household's real count in the same window. The reference is now the real distribution of these households, who shop more often than the full panel: mean 7.83, variance-to-mean ratio 6.52, zero share 0.03, and $\alpha = 0.71$. The ceiling of design C for this reference is 5.01.

How much can demographics explain? Out of sample (households held out), a Poisson regression of the household's count on all demographic fields reaches a Spearman correlation of only 0.04 with the real count, and the squared coefficient of variation of its predicted means is $c^2 = 0.006$, about 1% of $\alpha$. In terms of Proposition 1, the unexplained share $R$ is almost equal to $\alpha$: the persona describes almost none of the heterogeneity. A deterministic simulator that predicted these means perfectly would have $\alpha^* = c^2 - 1/\mu = -0.12$, against a real $\alpha$ of 0.71.

The simulations behave as Proposition 1 predicts (Table 3, Table B3). Direct answers are collapsed again (variance-to-mean ratio 0.00 to 1.32, zero share at most 0.01) with $\alpha$ between -0.16 and +0.03. GPT-4o-mini answered "8" for every household when told the base rate (the number in the anchor text) and for practically every household without it, which gives $\alpha = -1/\mu = -0.125$, exactly the value of Proposition 1 with $c^2 = 0$. Daily simulation again misses the mean (6.0 to 17.2 against 7.83) and has ratios of 0.07 to 0.31. Describing a distribution reaches ratios of 2.78 to 6.11, and its intervals contain the ceiling of 5.01 in 9 of 16 cells (6 of the 8 anchored cells); its zero share (0.01 to 0.13) matches the small real share of 0.03 in 11 of 16 cells. The hybrid matches the reference ratio in 13 of 16 cells, but its mean in only 5 of 16: the model's $\lambda$ is usually too low (3.95 to 6.57 in the cells that miss, against 7.83). It also matches the zero share in only 2 of 16 cells (0.06 to 0.14 against 0.03), and all four of mean, ratio, zero share, and $\alpha$ in 2 of 16 cells (DeepSeek-V4-Pro with the anchor and Gemini 3.1 Flash-Lite without it).

| Design | Mean | Var/mean | Zero | Alpha | Rank correlation with real count |
|---|---|---|---|---|---|
| Reference | 7.83 | 6.52 | 0.03 | 0.71 | |
| A Direct | 5.62 to 10.24 | 0.00 to 1.32 | 0.00 to 0.01 | -0.16 to 0.03 | -0.17 to +0.07 |
| B Daily | 6.01 to 17.21 | 0.07 to 0.31 | 0.00 to 0.00 | -0.12 to -0.05 | -0.08 to +0.04 |
| C Describe | 5.56 to 8.79 | 2.78 to 6.11 | 0.01 to 0.13 | 0.32 to 0.79 | -0.01 to +0.16 |
| D Hybrid | 3.95 to 7.53 | 3.97 to 8.58 | 0.06 to 0.14 | 0.71 to 1.11 | -0.10 to +0.06 |

*Table 3. Persona experiment with real household demographics: range of results across the 16 model-and-prompt cells of each design (200 households per cell). The last column is the range of the Spearman correlation between the simulated count and the household's real count in the same window.*

Individual-level validity is essentially nil. Across the 63 cells in which the answers vary, the Spearman correlation between the simulated count and the household's real count lies between -0.17 and +0.16, and the interval excludes zero in only three cells (two positive, one negative). The model's own $\lambda$ in design D correlates between -0.05 and +0.05 with the real count, and none of its 16 intervals excludes zero. With 79 intervals, about four exclusions are expected by chance at the 5% level. Design C is the only design whose correlations are mostly positive (14 of 16 cells, median +0.06), but the models were run on overlapping samples of household-windows, so the cells are not independent evidence. On the first sample the demographic regression itself has a rank correlation of -0.03 (interval -0.17 to +0.10); on the two further samples of 200 household-windows it reaches +0.19 and -0.02, which shows how much a single sample can move these correlations. Because the demographics predict the real count with a rank correlation of only 0.04 across all households, this result does not show that the models ignore information; it shows that these personas contain almost no information for any simulator to use. It is the empirical counterpart of Proposition 1: richer observable personas cannot supply the heterogeneity that counts contain.

## 5.6 Randomized email experiment

Table 4 reports the elicited-probability design (the most stable of the three formats we tried), and Figure 2 shows the absolute lift for the men's email. Models run on three seeds are pooled over the three samples of 300 customers. The real effect is a risk ratio of 1.72 for visits and 2.19 for purchases for the men's email, with absolute lifts of 7.7 and 0.7 percentage points.

| Model | Prompt | Outcome | No email | Lift, men's email [95% CI] | Lift, women's email [95% CI] | Gap men minus women [95% CI] | RR men | RR women |
|---|---|---|---|---|---|---|---|---|
| Real (randomized) | | visit | 0.106 | +0.077 [+0.070, +0.083] | +0.045 [+0.039, +0.052] | +0.031 [+0.024, +0.038] | 1.72 | 1.43 |
| Real (randomized) | | purchase | 0.0057 | +0.0068 [+0.0050, +0.0086] | +0.0031 [+0.0015, +0.0047] | +0.0037 [+0.0017, +0.0056] | 2.19 | 1.54 |
| GPT-4o-mini | plain | visit | 0.260 | +0.190 [+0.175, +0.206]\* | +0.215 [+0.199, +0.229]\* | -0.025 [-0.051, +0.003]\* | 1.73 | 1.83\* |
| GPT-4o-mini | anchored | visit | 0.100 | +0.003 [+0.002, +0.004]\* | +0.004 [+0.002, +0.006]\* | -0.001 [-0.003, +0.001]\* | 1.03\* | 1.04\* |
| Llama-3.3-70B | plain | visit | 0.296 | +0.071 [+0.057, +0.084] | +0.064 [+0.050, +0.079]\* | +0.007 [-0.018, +0.030]\* | 1.24\* | 1.22\* |
| Llama-3.3-70B | anchored | visit | 0.100 | +0.035 [+0.032, +0.039]\* | +0.036 [+0.033, +0.039]\* | -0.000 [-0.006, +0.005]\* | 1.36\* | 1.36 |
| Haiku 5.5 | plain | visit | 0.154 | +0.073 [+0.065, +0.081] | +0.091 [+0.082, +0.099]\* | -0.018 [-0.032, -0.004]\* | 1.47\* | 1.59 |
| Haiku 5.5 | anchored | visit | 0.093 | +0.159 [+0.154, +0.164]\* | +0.163 [+0.158, +0.167]\* | -0.004 [-0.011, +0.003]\* | 2.71\* | 2.75\* |
| Sonnet 5 | plain | visit | 0.223 | +0.137 [+0.120, +0.153]\* | +0.141 [+0.125, +0.157]\* | -0.004 [-0.031, +0.024]\* | 1.61\* | 1.63\* |
| Sonnet 5 | anchored | visit | 0.203 | +0.025 [+0.012, +0.040]\* | +0.025 [+0.011, +0.040]\* | -0.000 [-0.022, +0.020]\* | 1.13\* | 1.13\* |
| GPT-5.6-terra | plain | visit | 0.282 | +0.050 [+0.033, +0.069]\* | +0.052 [+0.035, +0.070] | -0.001 [-0.030, +0.027]\* | 1.18\* | 1.18\* |
| GPT-5.6-terra | anchored | visit | 0.102 | +0.075 [+0.063, +0.087] | +0.083 [+0.070, +0.095]\* | -0.008 [-0.028, +0.013]\* | 1.73 | 1.81\* |
| DeepSeek-V4-Pro | plain | visit | 0.203 | +0.037 [+0.012, +0.058]\* | +0.035 [+0.010, +0.059] | +0.001 [-0.024, +0.026]\* | 1.18\* | 1.17\* |
| DeepSeek-V4-Pro | anchored | visit | 0.069 | +0.196 [+0.178, +0.213]\* | +0.183 [+0.165, +0.200]\* | +0.013 [-0.011, +0.036] | 3.82\* | 3.63\* |
| Gemini 3.1 Flash-Lite | plain | visit | 0.126 | +0.050 [+0.035, +0.067]\* | +0.044 [+0.029, +0.060] | +0.006 [-0.022, +0.033] | 1.39\* | 1.35 |
| Gemini 3.1 Flash-Lite | anchored | visit | 0.100 | +0.062 [+0.053, +0.070]\* | +0.054 [+0.046, +0.063]\* | +0.008 [-0.007, +0.021]\* | 1.62\* | 1.54\* |
| Mistral Large 4 | plain | visit | 0.235 | +0.080 [+0.058, +0.100] | +0.075 [+0.053, +0.095]\* | +0.005 [-0.033, +0.043] | 1.34\* | 1.32\* |
| Mistral Large 4 | anchored | visit | 0.100 | +0.038 [+0.029, +0.049]\* | +0.030 [+0.021, +0.040]\* | +0.008 [-0.008, +0.024]\* | 1.38\* | 1.30\* |
| GPT-4o-mini | plain | purchase | 0.155 | +0.169 [+0.155, +0.184]\* | +0.201 [+0.187, +0.214]\* | -0.032 [-0.056, -0.005]\* | 2.09 | 2.30\* |
| GPT-4o-mini | anchored | purchase | 0.064 | +0.026 [+0.021, +0.030]\* | +0.048 [+0.044, +0.053]\* | -0.023 [-0.029, -0.018]\* | 1.40\* | 1.75\* |
| Llama-3.3-70B | plain | purchase | 0.087 | +0.154 [+0.141, +0.168]\* | +0.167 [+0.153, +0.182]\* | -0.013 [-0.039, +0.011] | 2.78\* | 2.93\* |
| Llama-3.3-70B | anchored | purchase | 0.004 | +0.149 [+0.137, +0.162]\* | +0.161 [+0.148, +0.175]\* | -0.012 [-0.034, +0.011] | 43.83\* | 47.87\* |
| Haiku 5.5 | plain | purchase | 0.096 | +0.047 [+0.041, +0.053]\* | +0.054 [+0.049, +0.060]\* | -0.008 [-0.017, +0.002]\* | 1.49\* | 1.57 |
| Haiku 5.5 | anchored | purchase | 0.008 | +0.110 [+0.104, +0.116]\* | +0.120 [+0.113, +0.126]\* | -0.010 [-0.019, -0.000]\* | 15.80\* | 17.02\* |
| Sonnet 5 | plain | purchase | 0.094 | +0.050 [+0.040, +0.060]\* | +0.054 [+0.045, +0.063]\* | -0.004 [-0.020, +0.012] | 1.53\* | 1.57 |
| Sonnet 5 | anchored | purchase | 0.046 | +0.004 [-0.002, +0.010] | +0.006 [-0.001, +0.013] | -0.002 [-0.011, +0.007] | 1.09\* | 1.14\* |
| GPT-5.6-terra | plain | purchase | 0.073 | +0.115 [+0.103, +0.128]\* | +0.106 [+0.095, +0.117]\* | +0.009 [-0.010, +0.027] | 2.58\* | 2.45\* |
| GPT-5.6-terra | anchored | purchase | 0.008 | +0.017 [+0.013, +0.020]\* | +0.016 [+0.013, +0.019]\* | +0.001 [-0.005, +0.006] | 3.15\* | 3.05\* |
| DeepSeek-V4-Pro | plain | purchase | 0.103 | +0.028 [+0.010, +0.045]\* | +0.025 [+0.009, +0.042]\* | +0.003 [-0.016, +0.020] | 1.27\* | 1.25\* |
| DeepSeek-V4-Pro | anchored | purchase | 0.076 | +0.128 [+0.108, +0.150]\* | +0.105 [+0.088, +0.124]\* | +0.023 [+0.000, +0.047] | 2.68\* | 2.37\* |
| Gemini 3.1 Flash-Lite | plain | purchase | 0.072 | +0.032 [+0.025, +0.039]\* | +0.028 [+0.021, +0.035]\* | +0.004 [-0.008, +0.016] | 1.45\* | 1.39\* |
| Gemini 3.1 Flash-Lite | anchored | purchase | 0.010 | +0.015 [+0.013, +0.018]\* | +0.011 [+0.009, +0.014]\* | +0.004 [-0.001, +0.009] | 2.54\* | 2.16\* |
| Mistral Large 4 | plain | purchase | 0.124 | +0.103 [+0.089, +0.118]\* | +0.099 [+0.083, +0.115]\* | +0.004 [-0.022, +0.030] | 1.83\* | 1.80\* |
| Mistral Large 4 | anchored | purchase | 0.009 | +0.080 [+0.072, +0.088]\* | +0.077 [+0.069, +0.084]\* | +0.003 [-0.010, +0.017] | 10.43\* | 10.03\* |

*Table 4. Probability-elicitation design (mean elicited probability over 300 simulated customers per seed, three independent calls per customer; 900 customers for GPT-4o-mini, Llama-3.3-70B, and Haiku 5.5, which were run on three seeds). Lift = probability with the email minus probability without it; gap = lift of the men's email minus lift of the women's email; intervals are 95% paired bootstrap intervals over customers (real values: normal approximation). RR = risk ratio; for the models run on three seeds it is the mean of the three per-seed ratios, and the asterisk is set only if the interval excludes the real ratio in all three seeds. \* the simulated and the real intervals do not overlap.*

![Figure 2. Absolute lift in the probability of a visit and of a purchase after a men's email (elicited-probability design). Bars are 95% intervals; the dashed line and band are the real lift and its 95% interval. Note the logarithmic axis in panel b.](fig2_lift.png){width=6.4in}

Four patterns emerge. First, the direction is mostly reproduced: the risk ratio exceeds one in all 32 probability-elicitation cells, but its interval includes or touches one in two (GPT-4o-mini with the anchor for visits, 1.01 [1.00, 1.03], where the model answered about 10% regardless of the email, and Sonnet 5 with the anchor for purchases, 1.09 [0.96, 1.25]), and Llama with the anchor gave a risk ratio below one in the yes/no format for visits (0.60 to 0.69 in all three seeds). For the three models run on three seeds, the risk ratio exceeded one in all 24 cells of the two further seeds (smallest lower bound 1.00). Second, the size of the visit effect depends on the model and the prompt. In 4 of 16 configurations the lift for the men's email is statistically consistent with the real +0.077 (Llama-3.3-70B, Haiku 5.5, and Mistral Large 4 without the anchor, and GPT-5.6-terra with it); five are less than half as large (for example Sonnet 5 with the anchor, +0.025), and four are more than 1.5 times as large (for example GPT-4o-mini without the anchor, +0.190). Which prompt works differs by model: the anchor brings GPT-5.6-terra to the real value but moves DeepSeek-V4-Pro from 0.5 to 2.6 times the real lift.

Third, the absolute lift in purchase probability exceeds the real +0.0068 in 15 of the 16 configurations, by a median factor of about 10 and by up to 25 (for example +0.169 for GPT-4o-mini without the anchor). The one exception is Sonnet 5 with the anchor, whose purchase lift (+0.004, interval -0.002 to +0.010) is consistent with the real one; but this model rates the visit lift at only 0.3 times the real value and its no-email purchase probability (0.046) is eight times the real one, so it attributes almost no effect to the email. Providing the base rate sets the no-email probability close to the stated number (about 0.10 for visits in six models, and 0.004 to 0.010 for purchases in five) without lowering the email-arm probability accordingly, so the risk ratio explodes in some cases (10 to 44 for Llama, Haiku, and Mistral) while the absolute lift stays large. The relation $RR = 1 + d/p_0$ explains both patterns: Llama without the anchor has a visit lift of +0.071, close to the real value, but a no-email probability of 0.30 instead of 0.106, and therefore a risk ratio of only 1.24 against the real 1.72.

Fourth, the models do not tell the two emails apart. In reality the men's email has the larger lift (+0.077 against +0.045 for visits, a gap of +0.031 with interval +0.024 to +0.038). Among the 32 probability-elicitation cells, none has a gap interval that excludes zero in the right direction. The point estimate of the gap is positive in only 15 cells, the largest simulated visit gap is +0.013, and in three cells (Haiku 5.5 without the anchor for visits, and GPT-4o-mini in both prompt variants for purchases) the women's email is rated significantly higher.

Direct yes/no answers are not usable for rare events. In 15 of 32 yes/no cells of the first seed (and in 13 of 24 cells of the two further seeds) the model answered "No" for every customer in the no-email condition, so the risk ratio is undefined (for example, GPT-4o-mini answered "No" for every customer without an email and "Yes" for about half with one). The yes/no visit lifts range from -0.31 to +0.55, and the purchase lifts from +0.007 to +0.55, up to 80 times the real lift.

## 5.7 Summary of hypotheses

| Hypothesis | Evidence |
|---|---|
| H1. Designs A and B collapse. | Supported. The variance-to-mean ratio of designs A, B, and C lies below the reference in 45 of 47 cells (low mean; the exceptions are two DeepSeek-V4-Pro and Sonnet 5 cells without the anchor), 48 of 48 (high mean), and 43 of 48 (demographic personas, where design C often reaches the reference). The zero share of designs A and B is at most 0.02 in the two high-mean settings and below the real value in 26 of 32 low-mean cells (in the others, anchored prompts led the model to answer "0" for most customers). |
| H2. Design C approaches but does not exceed its ceiling and under-produces zeros. | Partly supported. Design C stays below its ceiling in all 16 low-mean cells, reaches it in 4 of 16 high-mean cells, and reaches it in 9 of 16 cells with demographic personas. Zero shares are too low where the real share is large (0.74 and 0.19) but close to the real value where it is small (0.03; 11 of 16 cells). |
| H3. Design D reproduces dispersion; fidelity depends on the model's mean. | Supported with a qualification. It matches the reference ratio in 35 of 48 cells (7 of 16, 15 of 16, 13 of 16), but matches mean, ratio, zero share, and $\alpha$ jointly in only 12 of 48 (5, 5, 2) because the model's mean is often wrong. Sonnet 5 reproduces all four in both prompt variants in the high-mean setting. |
| H4a. Direction is reproduced. | Mostly supported: the risk ratio exceeds one in all 32 probability cells, with two intervals touching one (see Section 5.6). |
| H4b. Absolute lift is overstated when the simulated base rate is overstated. | Supported for purchases: the lift exceeds the real value in 15 of 16 configurations (median about tenfold). Not for visits: 4 of 16 are consistent with the real value, 5 are too small, and 4 are too large. |
| H4c. Similar treatments are not distinguished. | Supported. The simulated gap between the two emails excludes zero in only 3 of 32 cells, and in all three the sign is the opposite of the real one. |
| Exploratory: collapse is specific to low means. | Not supported. Direct answers collapse at means of 0.5, 4.8, and 7.8. |
| Exploratory: richer personas repair collapse. | Not supported. With real demographics the simulated counts have a rank correlation with real counts of -0.17 to +0.16 (3 of 63 intervals exclude zero); the demographics themselves explain about 1% of the heterogeneity. |
| Exploratory: larger and more recent models escape collapse. | Not for direct answers (ratios of at most 1.00 in 44 of 48 cells; the four exceptions are DeepSeek-V4-Pro or Mistral Large 4 without the anchor). Partly for the hybrid design, whose accuracy follows the model's mean (best for Sonnet 5 in the high-mean setting). |

*Table 5. Hypotheses and evidence.*

# 6. Discussion

## 6.1 Theoretical contributions

Our results support a simple reading of synthetic purchase data: persona-conditioned LLM simulators compress customer heterogeneity, and the compression has a specific, measurable form. Proposition 1 shows why direct answers cannot be overdispersed in general (they lose Poisson noise and the share of heterogeneity that the persona does not describe), and the data are consistent with it: variance-to-mean ratios of direct answers are at most 1.00 in 44 of 48 cells, whatever the mean or the model, and the demographic-persona experiment reproduces the predicted $\alpha$ of about -0.12. Proposition 2 clarifies what an external heterogeneity term can and cannot do: it restores dispersion, but only the within-persona part, and its accuracy then rests on the model's mean. A further result concerns model scale. Larger and more recent models (Sonnet 5, GPT-5.6-terra, DeepSeek-V4-Pro, Mistral Large 4) do not escape the collapse of direct answers, but the better ones supply a more accurate mean, and the hybrid design then works well (Sonnet 5 in the high-mean setting). This reframes the usual advice to "add noise" to synthetic respondents. The amount of noise is not a free parameter; it is determined by how much heterogeneity the persona already carries.

Two further results extend what is known about LLM-based simulation. First, describing a distribution (Jang et al. 2026, Zhang et al. 2025a) helps more at a high mean than at a low mean, and in the settings where zeros are common it under-produces them. The zero share is the part of a count distribution that decides how many customers a campaign is not reaching, and this is where description fails. Second, evaluating a promotion simulator on relative effects alone is hazardous. The relation $RR = 1 + d/p_0$ shows that errors in the simulated base rate and errors in the simulated lift are confounded in the risk ratio, and our data contain cases in which the two readings of the same output disagree.

## 6.2 Implications for practice

For managers who consider synthetic customers for decision support, the evidence suggests a short diagnostic protocol.

1. *Compare shapes, not only means.* Before using synthetic counts, compute the variance-to-mean ratio, $\alpha$, and the zero share against a historical customer file, and check them with an interval, as we do here. A ratio near or below one signals collapse.
2. *Do not use direct integer answers.* In our data they returned a single value for practically every customer in several cells.
3. *If the model is used, use it for the mean only,* and inject the remaining heterogeneity externally, calibrated according to Proposition 2 on a historical or pilot sample. Verify that the model's mean is accurate; the hybrid inherits its errors, and in our data the mean matched the reference in only 20 of 48 hybrid cells.
4. *Treat a stated base rate as a prompt choice that must be tested.* It corrected the mean in some designs, collapsed all answers to one value in others, and changed the size of the simulated promotion effect by an order of magnitude.
5. *Validate on absolute effects and base rates.* Report the simulated base rate and the absolute lift next to the risk ratio, and compare both with a past randomized test before any revenue calculation.

## 6.3 Limitations and future research

The evidence is preliminary. The five newer models were run on a single random seed, and every design has one prompt wording, so our intervals capture the sampling of customers but not variation across prompts. For the three models that we repeated on three seeds, the qualitative conclusions did not change, and the per-seed variance-to-mean ratios of the direct and daily designs differ by at most 0.11 and 0.20; the ratio of the describe design varies by up to 2.1 and that of the hybrid by up to 4.2 across seeds in the high-mean settings, which is why the counts of cells in which these designs match the reference should be read as approximate. We tested eight models in all four settings, five of them larger or more recent than the first three. Whether still larger or reasoning-enabled models collapse less, and whether the overstated purchase lifts persist there, remains open. The low-mean reference is a calibrated parametric distribution rather than the raw data, and the Complete Journey households are loyalty-card shoppers with relatively high purchase frequency. Richer personas built from real household demographics did not change the picture, but the demographics in these data explain almost none of the heterogeneity ($c^2/\alpha = 0.01$), so that test marks the limit of observable personas rather than a limit of particular models; settings in which observable attributes, such as purchase histories, are more predictive of purchase frequency would be a stronger test of Proposition 1. In the Complete Journey data campaigns were targeted rather than randomized, so only the email experiment supports a causal comparison. Design C truncates its top bin, which lowers the dispersion it can reach; we quantified this ceiling but did not remove it. Public data may also be part of the models' training data. Future work should evaluate the hybrid design with a calibrated mean, test prompts that elicit several candidate answers with probabilities, and use a randomized promotion data set with purchase counts, for example from a partner firm, so that the count-distribution and treatment-effect questions can be studied on the same customers.

# 7. Conclusion

Synthetic customers built from language models do not yet reproduce the shape of real purchase-count distributions or the size of real promotion effects. Direct and day-by-day designs collapse toward a single value whether the mean is 0.5, 4.8, or 7.8, and larger, more recent models do not change this; describing a distribution repairs part of the damage but loses zeros; and a hybrid that takes only the mean from the model matches the dispersion when that mean is accurate. In a randomized email test the models usually get the sign of the effect right, but the absolute lift in purchase probability is overstated in 15 of 16 configurations and similar treatments are not told apart. Practitioners who use synthetic customers should check dispersion and zero share against their own data, rely on the model for means only, and validate absolute effects before they act on them.

# References {-}

Brand J, Israeli A, Ngwe D (2023) Using GPT for market research. Working Paper 23-062, Harvard Business School, Boston.

Cameron AC, Trivedi PK (1990) Regression-based tests for overdispersion in the Poisson model. *J. Econometrics* 46(3):347–364.

Chen D (2019) Online Retail II. Data set, UCI Machine Learning Repository, University of California, Irvine.

Chen L (2026) Simulated customers never walk away: Decision fidelity of LLM user simulators measured against real purchase outcomes. Preprint, submitted June 16, arXiv:2606.20708.

Chu ML, Terhorst L, Reed K, et al. (2025) LLM-based multi-agent system for simulating and analyzing marketing and consumer behavior. Preprint, submitted October 20, arXiv:2510.18155.

dunnhumby (n.d.) The Complete Journey. Data set, accessed through the completejourney_py package.

Ehrenberg ASC (1959) The pattern of consumer purchases. *J. Royal Statist. Soc. Ser. C* 8(1):26–41.

Fader PS, Hardie BGS, Lee KL (2005) "Counting your customers" the easy way: An alternative to the Pareto/NBD model. *Marketing Sci.* 24(2):275–284.

Fan GJ, Huang C, Peng T (2026) SYN-DIGITS: A synthetic control framework for calibrated digital twin simulation. Preprint, submitted April 8, arXiv:2604.07513.

Goli A, Singh A (2023) Can LLMs capture human preferences? Preprint, submitted May 4, arXiv:2305.02531.

Gu J, Pang L, Shen H, Cheng X (2024) Do LLMs play dice? Exploring probability distribution sampling in large language models for behavioral simulation. Preprint, submitted April 13, arXiv:2404.09043.

Hewitt L, Ashokkumar A, Ghezae I, Willer R (2024) Predicting results of social science experiments using large language models. Working paper, Stanford University, Stanford, CA.

Hillstrom K (2008) The MineThatData e-mail analytics and data mining challenge. Blog post, March 20, http://blog.minethatdata.com.

Horton JJ (2023) Large language models as simulated economic agents: What can we learn from Homo silicus? Preprint, submitted January 18, arXiv:2301.07543.

Huang C, Wang K (2026) LLM-powered virtual population for demand simulation and pricing. Preprint, submitted June 15, arXiv:2606.16183.

Jang C, Lee D, Kim J (2026) Instruction-tuned language models cannot sample from distributions they can describe. Preprint, submitted July 28, arXiv:2607.25292.

Li D, Li L, Qiu HS (2025) ChatGPT is not a man but Das Man: Representativeness and structural consistency of silicon samples generated by large language models. Preprint, submitted June 25, arXiv:2507.02919.

Maier BF, Aslak U, Fiaschi L, et al. (2025) LLMs reproduce human purchase intent via semantic similarity elicitation of Likert ratings. Preprint, submitted October 9, arXiv:2510.08338.

Sashihara J, Fujita Y, Nakamura K, et al. (2025) LLM-based multi-agent system for simulating strategic and goal-oriented data marketplaces. Preprint, submitted November 17, arXiv:2511.13233.

Schmittlein DC, Morrison DG, Colombo R (1987) Counting your customers: Who are they and what will they do next? *Management Sci.* 33(1):1–24.

Tigre R, Souto HG (2026) When can you trust your synthetic users? Diagnostics and corrections for LLM consumer panels. Preprint, submitted June 3, arXiv:2609.13148.

Zhang J, Yu S, Chong D, et al. (2025a) Verbalized sampling: How to mitigate mode collapse and unlock LLM diversity. Preprint, submitted October 1, arXiv:2510.01171.

Zhang R, Zhang X, Zhao M (2025b) Predicting effects, missing distributions: Evaluating LLMs as human behavior simulators in operations management. Preprint, submitted September 30, arXiv:2510.03310.

# Appendix A. Prompt Templates {-}

Persona text, low-mean setting: "You are a customer of an online giftware retailer. Profile: {segment}, age {age}, based in {country}. You made your first purchase 4 weeks ago." Anchored variant adds: "Context: customers of this retailer make on average about 0.5 purchases per 4 weeks, and most make none."

Persona text, high-mean setting: "You are a household with a loyalty card at a supermarket chain and you do part of your grocery shopping there. Profile: {segment}, head of household aged {age}, {household size} person(s)." Anchored variant adds: "Context: households in this loyalty program make on average about 5 shopping trips to the chain per 4 weeks, and some make none."

Questions. Design A: "How many separate purchases will you make in the next 4 weeks? Answer with ONLY an integer." Design B: "Week {w} of the next 4 weeks: for each of its 7 days decide whether you make a purchase that day. Reply with ONLY 7 comma-separated 0/1 values." Design C: "Give the probabilities of making {bins} purchases in the next 4 weeks. Reply with ONLY JSON like {...} summing to 1." Design D: "What is your expected average number of purchases per 4 weeks (can be fractional, e.g. 0.4)? Reply with ONLY a number." Email experiment: persona from the customer's recency, 12-month spend, merchandise bought, area, new or existing status, and channel, followed by one of three sentences describing the email received, and "What is the probability, from 0 to 100 percent, that you will {visit the retailer's website / make a purchase from the retailer} during the next two weeks? Reply with ONLY a number."

# Appendix B. Full Results {-}

| Model | Prompt | Design | Mean | Var/mean | Zero | Alpha |
|---|---|---|---|---|---|---|
| Reference | | | 0.49 | 2.49 | 0.74 | 3.05 |
| GPT-4o-mini | plain | A Direct | 1.92\* | 0.25\* | 0.00\* | -0.39\* |
| GPT-4o-mini | plain | B Daily | 13.56\* | 0.24\* | 0.00\* | -0.06\* |
| GPT-4o-mini | plain | C Describe | 1.30\* | 1.21\* | 0.32\* | 0.16\* |
| GPT-4o-mini | plain | D Hybrid | 0.43\* | 2.19 | 0.73 | 2.79 |
| GPT-4o-mini | anchored | A Direct | 1.00\* | 0.00\* | 0.00\* | -1.00\* |
| GPT-4o-mini | anchored | B Daily | 5.07\* | 0.33\* | 0.00\* | -0.13\* |
| GPT-4o-mini | anchored | C Describe | 0.37\* | 1.17\* | 0.71\* | 0.46\* |
| GPT-4o-mini | anchored | D Hybrid | 0.59\* | 2.19\* | 0.70\* | 2.01\* |
| Llama-3.3-70B | plain | A Direct | 0.96\* | 0.56\* | 0.29\* | -0.46\* |
| Llama-3.3-70B | plain | B Daily | 3.13\* | 0.38\* | 0.03\* | -0.20\* |
| Llama-3.3-70B | plain | C Describe | 0.98\* | 1.61\* | 0.47\* | 0.62\* |
| Llama-3.3-70B | plain | D Hybrid | 0.42\* | 2.03\* | 0.75 | 2.43 |
| Llama-3.3-70B | anchored | A Direct | 0.00\* | 1.00\* | 1.00\* | 0.00\* |
| Llama-3.3-70B | anchored | B Daily | 0.59\* | 1.24\* | 0.62\* | 0.41\* |
| Llama-3.3-70B | anchored | C Describe | 0.40\* | 1.08\* | 0.67\* | 0.19\* |
| Llama-3.3-70B | anchored | D Hybrid | 0.93\* | 3.38\* | 0.63\* | 2.57 |
| Haiku 5.5 | plain | A Direct | 1.64\* | 0.19\* | 0.00\* | -0.49\* |
| Haiku 5.5 | plain | B Daily | 5.90\* | 0.89\* | 0.01\* | -0.02\* |
| Haiku 5.5 | plain | C Describe | 0.85\* | 1.60\* | 0.52\* | 0.70\* |
| Haiku 5.5 | plain | D Hybrid | 0.65\* | 2.90 | 0.69\* | 2.95 |
| Haiku 5.5 | anchored | A Direct | 0.74\* | 0.26\* | 0.26\* | -1.00\* |
| Haiku 5.5 | anchored | B Daily | 2.10\* | 1.14\* | 0.27\* | 0.07\* |
| Haiku 5.5 | anchored | C Describe | 0.43 | 1.34\* | 0.69\* | 0.80\* |
| Haiku 5.5 | anchored | D Hybrid | 0.49 | 2.04\* | 0.72 | 2.09\* |
| Sonnet 5 | plain | A Direct | 1.33\* | 0.86\* | 0.30\* | -0.10\* |
| Sonnet 5 | plain | B Daily | 3.12\* | 2.96\* | 0.39\* | 0.63\* |
| Sonnet 5 | plain | C Describe | 0.71\* | 1.49\* | 0.59\* | 0.70\* |
| Sonnet 5 | plain | D Hybrid | 0.36\* | 1.70\* | 0.75 | 1.96 |
| Sonnet 5 | anchored | A Direct | 0.02\* | 0.98\* | 0.98\* | -0.75\* |
| Sonnet 5 | anchored | B Daily | 0.00\* | n/a | 1.00\* | n/a |
| Sonnet 5 | anchored | C Describe | 0.48 | 1.19\* | 0.65\* | 0.40\* |
| Sonnet 5 | anchored | D Hybrid | 0.41 | 2.02\* | 0.76 | 2.45 |
| GPT-5.6-terra | plain | A Direct | 0.67\* | 0.48\* | 0.38\* | -0.77\* |
| GPT-5.6-terra | plain | B Daily | 1.56\* | 1.16\* | 0.32\* | 0.10\* |
| GPT-5.6-terra | plain | C Describe | 0.53 | 1.25\* | 0.62\* | 0.47\* |
| GPT-5.6-terra | plain | D Hybrid | 0.52 | 2.05\* | 0.72 | 2.04 |
| GPT-5.6-terra | anchored | A Direct | 0.26\* | 0.74\* | 0.74 | -0.99\* |
| GPT-5.6-terra | anchored | B Daily | 0.01\* | 0.99\* | 0.98\* | -0.67\* |
| GPT-5.6-terra | anchored | C Describe | 0.47 | 0.97\* | 0.61\* | -0.06\* |
| GPT-5.6-terra | anchored | D Hybrid | 0.64 | 2.40 | 0.71 | 2.19 |
| DeepSeek-V4-Pro | plain | A Direct | 2.15\* | 18.37\* | 0.55\* | 8.06 |
| DeepSeek-V4-Pro | plain | B Daily | 4.80\* | 1.03\* | 0.02\* | 0.01\* |
| DeepSeek-V4-Pro | plain | C Describe | 0.61\* | 1.19\* | 0.58\* | 0.30\* |
| DeepSeek-V4-Pro | plain | D Hybrid | 0.41 | 2.66 | 0.77 | 4.06 |
| DeepSeek-V4-Pro | anchored | A Direct | 0.35\* | 0.83\* | 0.67\* | -0.48\* |
| DeepSeek-V4-Pro | anchored | B Daily | 0.49 | 0.89\* | 0.58\* | -0.23\* |
| DeepSeek-V4-Pro | anchored | C Describe | 0.54 | 0.98\* | 0.58\* | -0.04\* |
| DeepSeek-V4-Pro | anchored | D Hybrid | 0.59 | 2.92 | 0.72 | 3.26 |
| Gemini 3.1 Flash-Lite | plain | A Direct | 1.03\* | 0.62\* | 0.30\* | -0.37\* |
| Gemini 3.1 Flash-Lite | plain | B Daily | 3.50\* | 0.41\* | 0.04\* | -0.17\* |
| Gemini 3.1 Flash-Lite | plain | C Describe | 0.51 | 1.19\* | 0.64\* | 0.38\* |
| Gemini 3.1 Flash-Lite | plain | D Hybrid | 0.33\* | 1.64\* | 0.79 | 1.96 |
| Gemini 3.1 Flash-Lite | anchored | A Direct | 0.27\* | 0.73\* | 0.73 | -0.99\* |
| Gemini 3.1 Flash-Lite | anchored | B Daily | 1.42\* | 1.24\* | 0.38\* | 0.17\* |
| Gemini 3.1 Flash-Lite | anchored | C Describe | 0.53 | 0.95\* | 0.58\* | -0.10\* |
| Gemini 3.1 Flash-Lite | anchored | D Hybrid | 0.61 | 2.56 | 0.72 | 2.54 |
| Mistral Large 4 | plain | A Direct | 1.00\* | 0.68\* | 0.29\* | -0.31\* |
| Mistral Large 4 | plain | B Daily | 5.07\* | 0.97\* | 0.01\* | -0.01\* |
| Mistral Large 4 | plain | C Describe | 1.01\* | 1.31\* | 0.45\* | 0.31\* |
| Mistral Large 4 | plain | D Hybrid | 0.28\* | 1.46\* | 0.80 | 1.67 |
| Mistral Large 4 | anchored | A Direct | 0.03\* | 0.97\* | 0.97\* | -0.84\* |
| Mistral Large 4 | anchored | B Daily | 0.50 | 1.03\* | 0.62\* | 0.05\* |
| Mistral Large 4 | anchored | C Describe | 0.57 | 1.07\* | 0.56\* | 0.12\* |
| Mistral Large 4 | anchored | D Hybrid | 0.46 | 2.67 | 0.77 | 3.67 |

*Table B1. Low-mean setting, per cell. Reference row: negative binomial with mean 0.49 and alpha 3.05. \* the 95% bootstrap interval excludes the reference value. Temperatures are pooled for GPT-4o-mini and Llama.*

| Model | Prompt | Design | Mean | Var/mean | Zero | Alpha |
|---|---|---|---|---|---|---|
| Reference | | | 4.84 | 7.85 | 0.19 | 1.42 |
| GPT-4o-mini | plain | A Direct | 8.00\* | 0.01\* | 0.00\* | -0.12\* |
| GPT-4o-mini | plain | B Daily | 16.45\* | 0.05\* | 0.00\* | -0.06\* |
| GPT-4o-mini | plain | C Describe | 5.68\* | 5.37\* | 0.10\* | 0.77\* |
| GPT-4o-mini | plain | D Hybrid | 6.56\* | 9.02 | 0.18 | 1.22 |
| GPT-4o-mini | anchored | A Direct | 5.00\* | 0.00\* | 0.00\* | -0.20\* |
| GPT-4o-mini | anchored | B Daily | 16.65\* | 0.08\* | 0.00\* | -0.06\* |
| GPT-4o-mini | anchored | C Describe | 5.46\* | 6.44\* | 0.13\* | 1.00\* |
| GPT-4o-mini | anchored | D Hybrid | 5.33 | 8.73 | 0.21 | 1.45 |
| Llama-3.3-70B | plain | A Direct | 8.00\* | 0.00\* | 0.00\* | -0.12\* |
| Llama-3.3-70B | plain | B Daily | 9.86\* | 0.23\* | 0.00\* | -0.08\* |
| Llama-3.3-70B | plain | C Describe | 7.32\* | 4.85\* | 0.03\* | 0.53\* |
| Llama-3.3-70B | plain | D Hybrid | 6.06\* | 9.06 | 0.22 | 1.33 |
| Llama-3.3-70B | anchored | A Direct | 3.73\* | 0.27\* | 0.02\* | -0.20\* |
| Llama-3.3-70B | anchored | B Daily | 7.03\* | 0.19\* | 0.00\* | -0.12\* |
| Llama-3.3-70B | anchored | C Describe | 6.49\* | 5.76\* | 0.05\* | 0.73\* |
| Llama-3.3-70B | anchored | D Hybrid | 4.26\* | 5.90 | 0.14\* | 1.15 |
| Haiku 5.5 | plain | A Direct | 7.71\* | 0.24\* | 0.00\* | -0.10\* |
| Haiku 5.5 | plain | B Daily | 9.93\* | 0.25\* | 0.00\* | -0.08\* |
| Haiku 5.5 | plain | C Describe | 6.16\* | 4.13\* | 0.01\* | 0.51\* |
| Haiku 5.5 | plain | D Hybrid | 4.81 | 7.48 | 0.20 | 1.35 |
| Haiku 5.5 | anchored | A Direct | 4.48\* | 0.11\* | 0.00\* | -0.20\* |
| Haiku 5.5 | anchored | B Daily | 9.47\* | 0.19\* | 0.00\* | -0.09\* |
| Haiku 5.5 | anchored | C Describe | 5.66\* | 5.82\* | 0.12\* | 0.85\* |
| Haiku 5.5 | anchored | D Hybrid | 3.66\* | 5.84\* | 0.26\* | 1.32 |
| Sonnet 5 | plain | A Direct | 8.04\* | 0.28\* | 0.00\* | -0.09\* |
| Sonnet 5 | plain | B Daily | 10.22\* | 0.14\* | 0.00\* | -0.08\* |
| Sonnet 5 | plain | C Describe | 7.21\* | 4.08\* | 0.04\* | 0.43\* |
| Sonnet 5 | plain | D Hybrid | 4.86 | 9.99 | 0.23 | 1.85 |
| Sonnet 5 | anchored | A Direct | 5.00\* | 0.03\* | 0.00\* | -0.19\* |
| Sonnet 5 | anchored | B Daily | 8.19\* | 0.04\* | 0.00\* | -0.12\* |
| Sonnet 5 | anchored | C Describe | 4.88 | 4.41\* | 0.10\* | 0.70\* |
| Sonnet 5 | anchored | D Hybrid | 4.94 | 8.87 | 0.23 | 1.59 |
| GPT-5.6-terra | plain | A Direct | 7.56\* | 0.21\* | 0.00\* | -0.10\* |
| GPT-5.6-terra | plain | B Daily | 8.36\* | 0.08\* | 0.00\* | -0.11\* |
| GPT-5.6-terra | plain | C Describe | 6.67\* | 5.07\* | 0.07\* | 0.61\* |
| GPT-5.6-terra | plain | D Hybrid | 5.13 | 10.65 | 0.25\* | 1.88 |
| GPT-5.6-terra | anchored | A Direct | 4.88 | 0.02\* | 0.00\* | -0.20\* |
| GPT-5.6-terra | anchored | B Daily | 4.45\* | 0.14\* | 0.00\* | -0.19\* |
| GPT-5.6-terra | anchored | C Describe | 5.50\* | 3.70\* | 0.09\* | 0.49\* |
| GPT-5.6-terra | anchored | D Hybrid | 4.67 | 10.85 | 0.28\* | 2.11 |
| DeepSeek-V4-Pro | plain | A Direct | 7.71\* | 0.76\* | 0.00\* | -0.03\* |
| DeepSeek-V4-Pro | plain | B Daily | 9.04\* | 0.18\* | 0.00\* | -0.09\* |
| DeepSeek-V4-Pro | plain | C Describe | 5.58\* | 3.85\* | 0.04\* | 0.51\* |
| DeepSeek-V4-Pro | plain | D Hybrid | 7.87\* | 11.54 | 0.09\* | 1.34 |
| DeepSeek-V4-Pro | anchored | A Direct | 5.20\* | 0.65\* | 0.02\* | -0.07\* |
| DeepSeek-V4-Pro | anchored | B Daily | 6.84\* | 0.40\* | 0.01\* | -0.09\* |
| DeepSeek-V4-Pro | anchored | C Describe | 5.24 | 4.80\* | 0.06\* | 0.72\* |
| DeepSeek-V4-Pro | anchored | D Hybrid | 6.69\* | 7.34 | 0.12\* | 0.95\* |
| Gemini 3.1 Flash-Lite | plain | A Direct | 11.82\* | 0.30\* | 0.00\* | -0.06\* |
| Gemini 3.1 Flash-Lite | plain | B Daily | 8.21\* | 0.04\* | 0.00\* | -0.12\* |
| Gemini 3.1 Flash-Lite | plain | C Describe | 6.24\* | 3.52\* | 0.03\* | 0.40\* |
| Gemini 3.1 Flash-Lite | plain | D Hybrid | 7.57\* | 13.01 | 0.17 | 1.59 |
| Gemini 3.1 Flash-Lite | anchored | A Direct | 5.16\* | 0.08\* | 0.00\* | -0.18\* |
| Gemini 3.1 Flash-Lite | anchored | B Daily | 7.53\* | 0.09\* | 0.00\* | -0.12\* |
| Gemini 3.1 Flash-Lite | anchored | C Describe | 4.13\* | 3.18\* | 0.14\* | 0.53\* |
| Gemini 3.1 Flash-Lite | anchored | D Hybrid | 4.12 | 7.02 | 0.24 | 1.46 |
| Mistral Large 4 | plain | A Direct | 8.59\* | 2.38\* | 0.00\* | 0.16\* |
| Mistral Large 4 | plain | B Daily | 8.33\* | 0.06\* | 0.00\* | -0.11\* |
| Mistral Large 4 | plain | C Describe | 7.79\* | 4.39\* | 0.03\* | 0.43\* |
| Mistral Large 4 | plain | D Hybrid | 3.73\* | 6.22 | 0.25\* | 1.40 |
| Mistral Large 4 | anchored | A Direct | 4.90\* | 0.02\* | 0.00\* | -0.20\* |
| Mistral Large 4 | anchored | B Daily | 8.22\* | 0.05\* | 0.00\* | -0.12\* |
| Mistral Large 4 | anchored | C Describe | 4.82 | 4.11\* | 0.13\* | 0.65\* |
| Mistral Large 4 | anchored | D Hybrid | 3.09\* | 6.06 | 0.27\* | 1.64 |

*Table B2. High-mean setting, 200 customers per cell. Reference row: empirical Complete Journey distribution. \* the 95% bootstrap interval excludes the reference value.*

| Model | Prompt | Design | Mean | Var/mean | Zero | Alpha |
|---|---|---|---|---|---|---|
| Reference | | | 7.83 | 6.52 | 0.03 | 0.71 |
| GPT-4o-mini | plain | A Direct | 7.96\* | 0.02\* | 0.00\* | -0.12\* |
| GPT-4o-mini | plain | B Daily | 16.58\* | 0.07\* | 0.00\* | -0.06\* |
| GPT-4o-mini | plain | C Describe | 6.02\* | 5.78 | 0.09\* | 0.79 |
| GPT-4o-mini | plain | D Hybrid | 6.46\* | 5.68 | 0.08\* | 0.72 |
| GPT-4o-mini | anchored | A Direct | 8.00\* | 0.00\* | 0.00\* | -0.12\* |
| GPT-4o-mini | anchored | B Daily | 17.21\* | 0.13\* | 0.00\* | -0.05\* |
| GPT-4o-mini | anchored | C Describe | 6.56\* | 5.22\* | 0.10\* | 0.64 |
| GPT-4o-mini | anchored | D Hybrid | 7.53 | 6.35 | 0.07\* | 0.71 |
| Llama-3.3-70B | plain | A Direct | 7.98\* | 0.00\* | 0.00\* | -0.12\* |
| Llama-3.3-70B | plain | B Daily | 9.04\* | 0.18\* | 0.00\* | -0.09\* |
| Llama-3.3-70B | plain | C Describe | 6.80\* | 5.01\* | 0.03 | 0.59\* |
| Llama-3.3-70B | plain | D Hybrid | 4.91\* | 4.60\* | 0.12\* | 0.73 |
| Llama-3.3-70B | anchored | A Direct | 6.05\* | 0.03\* | 0.00\* | -0.16\* |
| Llama-3.3-70B | anchored | B Daily | 8.12\* | 0.13\* | 0.00\* | -0.11\* |
| Llama-3.3-70B | anchored | C Describe | 7.54 | 6.04 | 0.05 | 0.67 |
| Llama-3.3-70B | anchored | D Hybrid | 6.15\* | 5.55 | 0.10\* | 0.74 |
| Haiku 5.5 | plain | A Direct | 8.02\* | 0.37\* | 0.00\* | -0.08\* |
| Haiku 5.5 | plain | B Daily | 11.72\* | 0.16\* | 0.00\* | -0.07\* |
| Haiku 5.5 | plain | C Describe | 6.42\* | 4.11\* | 0.03 | 0.48\* |
| Haiku 5.5 | plain | D Hybrid | 5.14\* | 5.07\* | 0.12\* | 0.79 |
| Haiku 5.5 | anchored | A Direct | 7.13\* | 0.11\* | 0.00\* | -0.12\* |
| Haiku 5.5 | anchored | B Daily | 11.06\* | 0.15\* | 0.00\* | -0.08\* |
| Haiku 5.5 | anchored | C Describe | 7.49 | 6.11 | 0.10\* | 0.68 |
| Haiku 5.5 | anchored | D Hybrid | 5.71\* | 5.79 | 0.11\* | 0.84 |
| Sonnet 5 | plain | A Direct | 5.62\* | 0.18\* | 0.00\* | -0.15\* |
| Sonnet 5 | plain | B Daily | 10.51\* | 0.20\* | 0.00\* | -0.08\* |
| Sonnet 5 | plain | C Describe | 6.33\* | 3.87\* | 0.03 | 0.45\* |
| Sonnet 5 | plain | D Hybrid | 4.72\* | 5.43 | 0.12\* | 0.94 |
| Sonnet 5 | anchored | A Direct | 6.78\* | 0.18\* | 0.00\* | -0.12\* |
| Sonnet 5 | anchored | B Daily | 10.27\* | 0.22\* | 0.00\* | -0.08\* |
| Sonnet 5 | anchored | C Describe | 6.89\* | 4.16\* | 0.04 | 0.46\* |
| Sonnet 5 | anchored | D Hybrid | 6.84 | 8.58 | 0.07\* | 1.11\* |
| GPT-5.6-terra | plain | A Direct | 7.90 | 0.16\* | 0.00\* | -0.11\* |
| GPT-5.6-terra | plain | B Daily | 8.46\* | 0.13\* | 0.00\* | -0.10\* |
| GPT-5.6-terra | plain | C Describe | 6.66\* | 3.80\* | 0.03 | 0.42\* |
| GPT-5.6-terra | plain | D Hybrid | 5.14\* | 5.29 | 0.09\* | 0.83 |
| GPT-5.6-terra | anchored | A Direct | 7.67\* | 0.13\* | 0.00\* | -0.11\* |
| GPT-5.6-terra | anchored | B Daily | 6.01\* | 0.31\* | 0.00\* | -0.12\* |
| GPT-5.6-terra | anchored | C Describe | 8.79\* | 4.95\* | 0.04 | 0.45\* |
| GPT-5.6-terra | anchored | D Hybrid | 7.03 | 8.24 | 0.07\* | 1.03 |
| DeepSeek-V4-Pro | plain | A Direct | 7.15\* | 1.07\* | 0.00\* | 0.01\* |
| DeepSeek-V4-Pro | plain | B Daily | 8.68\* | 0.14\* | 0.00\* | -0.10\* |
| DeepSeek-V4-Pro | plain | C Describe | 5.56\* | 2.78\* | 0.01 | 0.32\* |
| DeepSeek-V4-Pro | plain | D Hybrid | 6.37\* | 6.04 | 0.08\* | 0.79 |
| DeepSeek-V4-Pro | anchored | A Direct | 6.51\* | 0.55\* | 0.01\* | -0.07\* |
| DeepSeek-V4-Pro | anchored | B Daily | 7.09\* | 0.21\* | 0.00\* | -0.11\* |
| DeepSeek-V4-Pro | anchored | C Describe | 6.91\* | 4.06\* | 0.03 | 0.44\* |
| DeepSeek-V4-Pro | anchored | D Hybrid | 6.99 | 6.08 | 0.06 | 0.73 |
| Gemini 3.1 Flash-Lite | plain | A Direct | 10.24\* | 0.40\* | 0.00\* | -0.06\* |
| Gemini 3.1 Flash-Lite | plain | B Daily | 8.04\* | 0.07\* | 0.00\* | -0.12\* |
| Gemini 3.1 Flash-Lite | plain | C Describe | 6.25\* | 3.11\* | 0.03 | 0.34\* |
| Gemini 3.1 Flash-Lite | plain | D Hybrid | 7.16 | 7.58 | 0.06 | 0.92 |
| Gemini 3.1 Flash-Lite | anchored | A Direct | 6.91\* | 0.30\* | 0.00\* | -0.10\* |
| Gemini 3.1 Flash-Lite | anchored | B Daily | 7.21\* | 0.12\* | 0.00\* | -0.12\* |
| Gemini 3.1 Flash-Lite | anchored | C Describe | 5.75\* | 5.18 | 0.10\* | 0.73 |
| Gemini 3.1 Flash-Lite | anchored | D Hybrid | 6.57\* | 6.30 | 0.08\* | 0.81 |
| Mistral Large 4 | plain | A Direct | 9.68\* | 1.32\* | 0.00\* | 0.03\* |
| Mistral Large 4 | plain | B Daily | 8.39\* | 0.07\* | 0.00\* | -0.11\* |
| Mistral Large 4 | plain | C Describe | 6.79\* | 4.08\* | 0.03 | 0.45\* |
| Mistral Large 4 | plain | D Hybrid | 3.95\* | 3.97\* | 0.14\* | 0.75 |
| Mistral Large 4 | anchored | A Direct | 7.38\* | 0.25\* | 0.01\* | -0.10\* |
| Mistral Large 4 | anchored | B Daily | 8.84\* | 0.12\* | 0.00\* | -0.10\* |
| Mistral Large 4 | anchored | C Describe | 6.23\* | 5.39 | 0.13\* | 0.70 |
| Mistral Large 4 | anchored | D Hybrid | 5.19\* | 5.67 | 0.14\* | 0.90 |

*Table B3. Persona experiment with real household demographics, 200 households per cell. Reference row: real distribution of the 801 households (10,413 household-windows). \* the 95% bootstrap interval excludes the reference value.*

# Appendix C. Reproducibility {-}

All code, the pilot grid runner, the demographic-ceiling script, the analysis scripts, and the tables and figures used here are in the project repository (`ooklee-sudo/fluffy-meme`, folder `llm-count-study`). Raw model responses are saved with each run. Household-level Complete Journey data are not redistributed; the code reads them from the public package files.
