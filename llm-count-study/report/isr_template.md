::: {custom-style="Title"}
Counting Customers with Language Models: Heterogeneity Compression in Synthetic Purchase Data
:::

::: {custom-style="Author"}
Manuscript prepared for submission to *Information Systems Research* (author information omitted for review)
:::

**Abstract**

Large language models (LLMs) are increasingly used to create synthetic customers for pre-testing marketing decisions, but evaluations have concentrated on ratings, choices, and stated willingness to pay. We study an output that customer analytics depends on more directly: the number of purchases a customer makes in a period. Building on the Poisson–gamma account of purchase counts, we show analytically that overdispersion measures unobserved customer heterogeneity, derive how much of it a persona-conditioned simulator can carry, and show how a hybrid design avoids double counting. We evaluate four elicitation designs across three LLMs in two public transaction settings (mean counts of about 0.5 and 4.8) and in a randomized email experiment. Direct and day-by-day designs collapse toward a single value in both settings. Describing a distribution recovers part of the dispersion but under-produces zero counts where zeros are common. Personas built from real household demographics change nothing, because those demographics explain about 1% of the heterogeneity in counts. The hybrid matches dispersion only when the model's mean is accurate. Promotion effects have the right sign in most settings, yet their size varies by an order of magnitude with model and prompt, and the absolute lift in purchase probability is overstated four- to 26-fold. We offer a diagnostic protocol for practitioners who consider synthetic customers for decision support.

**Keywords:** synthetic customers, large language models, purchase counts, overdispersion, customer heterogeneity, decision support, digital twins

# 1. Introduction

Firms routinely test promotions, prices, and messages before committing money to them. Large language models (LLMs) promise a cheaper way to do so: prompt a model with a customer description, ask what that customer would do, and repeat for thousands of customers. Early studies found that such synthetic respondents produce plausible willingness-to-pay estimates and conjoint results (Brand et al. 2023), reproduce the qualitative pattern of classic behavioral experiments (Horton 2023), and, with suitable elicitation, mimic human purchase-intent ratings (Maier et al. 2025). Vendors now market "digital twins" of consumer panels on this basis.

What counts as validation in these studies is almost always a rating, a choice, or a price. Customer analytics, however, runs on counts. The number of purchases or visits per customer and period feeds customer lifetime value, repeat-purchase forecasts, and budget allocation, and marketing science has long modeled these counts as a Poisson process whose rate differs across customers (Ehrenberg 1959, Schmittlein et al. 1987, Fader et al. 2005). Because of this structure, the spread of a count distribution carries information about something firms care about, namely how much customers differ. A simulator that gets the average right but flattens the spread will mislead any decision that depends on heavy buyers, on the share of customers who do not buy at all, or on the uncertainty around a forecast.

There is good reason to worry about flattening. Studies of silicon samples repeatedly report variance collapse: simulated answers cluster on the modal response and are narrower than human ones (Li et al. 2025, Tigre and Souto 2026), and instruction-tuned models appear unable to sample from distributions they can otherwise describe (Jang et al. 2026). For count data this problem has a precise statistical form. If customers differ in their purchase rates, counts are overdispersed relative to a Poisson process; a simulator that compresses heterogeneity therefore shows up first as underdispersion and as a distorted share of zeros. Yet we found no study that evaluates LLM-generated purchase counts against Poisson or negative binomial benchmarks.

We ask four questions. Does the per-period purchase-count distribution of synthetic customers match the real one in mean, dispersion, zero share, and tail (RQ1)? Does variance collapse appear in count data as underdispersion (RQ2)? Do the elicitation and sampling design change fidelity (RQ3)? And does the promotion effect estimated with synthetic customers agree with a randomized experiment in direction and size (RQ4)? To answer them we compare four elicitation designs, run with three LLMs and two prompt variants, against two public transaction data sets whose mean counts differ by a factor of ten, and we test the same models against a randomized email experiment.

The study makes four contributions. First, we give a short analytical account of how much heterogeneity a persona-conditioned simulator can carry, and of how an externally injected heterogeneity term must be calibrated to avoid double counting (Propositions 1 and 2). Second, we provide evidence across designs, models, and settings that direct and day-by-day designs collapse, that describing a distribution only partly repairs the problem, and that a hybrid design reproduces dispersion only when the model supplies an accurate mean. Third, in the experimental setting we show that relative and absolute effects can tell different stories when the simulated base rate is wrong, and that the absolute lift in purchase probability is overstated by a large factor in every configuration we tested. Fourth, we translate these findings into a diagnostic protocol for practitioners.

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

We used GPT-4o-mini, Llama-3.3-70B-Instruct, and Claude Haiku 5.5, all through the OpenRouter interface. In the low-mean setting GPT-4o-mini and Llama were run at temperatures 0.3, 0.7, and 1.0 and the results pooled (600 customers per cell); in the high-mean and email settings the temperature was fixed at 0.7 (200 and 300 customers). Claude Haiku 5.5 does not accept a temperature setting, so it contributes one run per prompt variant; its hidden reasoning was switched off so that short answers are not truncated. For each cell we report the mean, the variance-to-mean ratio, the zero share, and $\alpha$, with 95% bootstrap intervals over customers. An asterisk marks an interval that excludes the reference value.

## 4.4 Email experiment

For each of 300 customers sampled from the real data we asked, in separate independent calls, for the probability (0 to 100 percent) that the customer would visit the website, and that it would make a purchase, in the next two weeks, under each of three conditions: no email, a men's email, and a women's email. We report the risk ratio and the absolute lift (the probability with the email minus the probability without it), the latter with paired bootstrap intervals over customers. Yes/no answers and Bernoulli draws from the elicited probabilities were also collected and are discussed where relevant. Because each call sees only one condition, the design mimics random assignment but does not equal it.

# 5. Results

## 5.1 Overview

Table 2 summarizes the first two settings by design. Appendix B gives all cells. The main pattern is that variance collapse is severe in designs A and B in both settings, that design C moves toward the real dispersion but loses zeros, and that design D matches dispersion in about half of the cells.

{{TABLE_SUMMARY}}

*Table 2. Range of results across the six model-and-prompt cells of each design. Reference rows are the real values. For design A in the low-mean setting the variance-to-mean ratio of 1.00 comes from a cell in which practically every simulated customer answered "0" and is uninformative.*

![Figure 1. Variance-to-mean ratio of simulated purchase counts with 95% intervals. The dashed line is the real value; the dotted line is the largest value that design C can reach with its count bins. Filled markers: plain prompt; hollow markers: anchored prompt.](fig1_dispersion.png){width=6.4in}

## 5.2 Low-mean setting

No direct or daily design reproduces the real dispersion. In all 18 cells of designs A, B, and C the upper bound of the variance-to-mean interval is below the reference of 2.49 (Table B1, Figure 1a). Direct answers are the most compressed, with ratios of at most 0.57 (excluding the degenerate all-zero cell). Under the anchored prompt Llama answered "0" and GPT-4o-mini answered "1" for practically every customer; in both cases the answer carries no persona information. Daily simulation overstates the mean without the anchor (GPT-4o-mini: 13.6 purchases in 28 days) and stays close to Poisson or below it. Describing a distribution reaches ratios of 0.96 to 1.59, comparable to or above daily simulation, but remains below its own ceiling of 2.10 in every cell, and its zero share is too low (0.32 to 0.68, against 0.74).

The hybrid matches the reference ratio in three of six cells (both Claude Haiku cells and GPT-4o-mini plain). This agreement is partly by construction, because the gamma multiplier injects the dispersion. What the model contributes is the mean, and the means differ: Llama's anchored mean is twice the reference (1.00 against 0.49).

## 5.3 High-mean setting

A higher mean does not relieve the collapse of direct answers (Table B2, Figure 1b). Ratios for design A lie between 0.00 and 0.27 against a reference of 7.85; GPT-4o-mini and Llama answered "8" for practically every customer without the anchor, and GPT-4o-mini answered "5" for everyone with it. Daily simulation again overstates the mean (7.1 to 16.6 trips against 4.84) and has almost no dispersion. In 17 of the 18 cells of designs A, B, and C the variance-to-mean interval lies entirely below the reference.

Describing a distribution behaves better here. With the anchor, the intervals of all three models contain the ceiling of 6.61, and $\alpha$ (0.80 to 0.96) approaches the attainable 1.18; the plain variants stay below it. Its weak point is the zero share: 0.01 to 0.12 against the real 0.19. The hybrid again matches the reference dispersion in four of six cells, but its mean is unstable (2.94 for Haiku with the anchor, 5.80 for GPT-4o-mini without it).

## 5.4 Is collapse specific to low means?

If direct answers were underdispersed only because small expected counts are rounded to 0, 1, or 2, the problem should shrink at a mean near 5. It does not. Variance-to-mean ratios of direct answers are at most 0.57 at a mean of 0.5 and at most 0.27 at a mean of 4.8, and in both settings models often return a single value for every customer. Collapse of direct answers is therefore not a rounding artifact of low means.

## 5.5 Richer personas from real household demographics

The personas used so far were deliberately simple. To test whether richer personas change the picture, we drew 200 household-windows at random from the 801 Complete Journey households with demographic records and described each household by its real age group, household type and size, number of children, marital status, income, and home ownership. This design also lets us compare each simulated count with that household's real count in the same window. The reference is now the real distribution of these households, who shop more often than the full panel: mean 7.83, variance-to-mean ratio 6.52, zero share 0.03, and $\alpha = 0.71$. The ceiling of design C for this reference is 5.01.

How much can demographics explain? Out of sample (households held out), a Poisson regression of the household's count on all demographic fields reaches a Spearman correlation of only 0.04 with the real count, and the squared coefficient of variation of its predicted means is $c^2 = 0.006$, about 1% of $\alpha$. In terms of Proposition 1, the unexplained share $R$ is almost equal to $\alpha$: the persona describes almost none of the heterogeneity. A deterministic simulator that predicted these means perfectly would have $\alpha^* = c^2 - 1/\mu = -0.12$, against a real $\alpha$ of 0.71.

The simulations behave as Proposition 1 predicts (Table 3, Table B3). Direct answers are collapsed again (variance-to-mean ratio 0.00 to 0.39, zero share 0.00) with $\alpha$ between -0.16 and -0.08. GPT-4o-mini answered "8" for every household when told the base rate (the number in the anchor text) and for practically every household without it, which gives $\alpha = -1/\mu = -0.125$, exactly the value of Proposition 1 with $c^2 = 0$. Daily simulation again overstates the mean (8.2 to 17.3 against 7.83). Describing a distribution reaches ratios of 3.70 to 5.05, and the intervals contain its ceiling of 5.01 in five of six cells; its zero share (0.03 to 0.09) is close to the small real share of 0.03. The hybrid matches the reference ratio in all six cells (5.21 to 7.26), but its mean is too low in five of six cells (4.73 to 6.42 against 7.83) and its zero share too high (0.07 to 0.12).

{{TABLE_DEMO_SUMMARY}}

*Table 3. Persona experiment with real household demographics: range of results across the six model-and-prompt cells of each design (200 households per cell). The last column is the range of the Spearman correlation between the simulated count and the household's real count in the same window.*

Individual-level validity is essentially nil. The Spearman correlation between the simulated count and the household's real count lies between -0.11 and +0.10, and every interval except one includes zero; the exception is GPT-4o-mini without the anchor in the direct design, whose answers are nearly constant (-0.04, interval -0.09 to -0.03). The model's own $\lambda$ in design D correlates between -0.09 and +0.11 with the real count. Because the demographics themselves predict the real count with a Spearman correlation of only 0.04, this result does not show that the models ignore information; it shows that these personas contain almost no information for any simulator to use. It is the empirical counterpart of Proposition 1: richer observable personas cannot supply the heterogeneity that counts contain.

## 5.6 Randomized email experiment

Table 4 reports the elicited-probability design (the most stable of the three formats we tried), and Figure 2 shows the absolute lift for the men's email. The real effect is a risk ratio of 1.72 for visits and 2.19 for purchases for the men's email, with absolute lifts of 7.7 and 0.7 percentage points.

{{TABLE_HILL}}

*Table 4. Probability-elicitation design (mean elicited probability over 300 simulated customers, three independent calls per customer). Lift = probability with the email minus probability without it; gap = lift of the men's email minus lift of the women's email; intervals are 95% paired bootstrap intervals over customers (real values: normal approximation). RR = risk ratio. \* the simulated and the real intervals do not overlap (for RR: the simulated interval excludes the real risk ratio).*

![Figure 2. Absolute lift in the probability of a visit and of a purchase after a men's email (elicited-probability design). Bars are 95% intervals; the dashed line and band are the real lift and its 95% interval. Note the logarithmic axis in panel b.](fig2_lift.png){width=6.4in}

Four patterns emerge. First, the direction is mostly reproduced: the risk ratio exceeds one in all 12 probability-elicitation cells, but it is essentially one for GPT-4o-mini with the anchor for visits (1.01 and 1.06; the model answered about 10% regardless of the email), and Llama with the anchor gave a risk ratio below one (0.63) in the yes/no format for visits. Second, the size is unstable. For visits, Llama and Haiku without the anchor give lifts of +0.071 and +0.078, close to the real +0.077, but GPT-4o-mini gives +0.199 and Haiku with the anchor +0.159. Third, the absolute lift in purchase probability is overstated in every setting, by about 4 to 26 times (for example +0.180 for GPT-4o-mini without the anchor, against a real +0.0068). Providing the base rate lowers the no-email purchase probability toward the real 0.57% for Llama and Haiku but leaves the email-arm probability high, so the risk ratio explodes (16 to 45) while the absolute lift stays large. The relation $RR = 1 + d/p_0$ explains both patterns: Llama without the anchor has a lift of +0.071 close to the real value, but a base rate of 0.30 instead of 0.106, and therefore a risk ratio of only 1.24 against the real 1.72. Fourth, the models do not reliably separate the men's from the women's email. In reality the men's email has the larger lift (+0.077 against +0.045 for visits, a gap of +0.031 with interval +0.024 to +0.038). In 10 of the 12 probability-elicitation cells the interval of the simulated gap includes zero; in the other two (GPT-4o-mini with the anchor) the women's email is rated higher, the opposite of the real result.

Direct yes/no answers are not usable for rare events. Without an email GPT-4o-mini answered "No" for every customer, and with an email about half answered "Yes", so the risk ratio is undefined; the same happened with Llama and Haiku for purchases in several cells. In absolute terms the yes/no purchase lifts range from +0.14 to +0.55, 21 to 81 times the real lift.

## 5.7 Summary of hypotheses

| Hypothesis | Evidence |
|---|---|
| H1. Designs A and B collapse. | Supported. 35 of 36 cells of designs A, B, and C across the two main settings lie below the reference variance-to-mean ratio, and the zero share of designs A and B is below the real value in 23 of 24 cells (the exception: Llama with the anchor answered "0" for practically every customer). The same holds with real household demographics (ratios 0.00 to 0.39, $\alpha$ near $-1/\mu$). |
| H2. Design C approaches but does not exceed its ceiling and under-produces zeros. | Supported. In the low-mean setting all six cells stay below the ceiling of 2.10; in the high-mean settings the anchored cells (and, with demographic personas, five of six cells) reach the ceiling. Zero shares are too low where the real zero share is large (0.74 and 0.19) but not where it is small (0.03). |
| H3. Design D reproduces dispersion; fidelity depends on the model's mean. | Supported. It matches dispersion in 7 of 12 cells, but its accuracy follows the model's mean, which the anchor sometimes worsens. |
| H4a. Direction is reproduced. | Mostly supported (see Section 5.6 for exceptions). |
| H4b. Absolute lift is overstated with an overstated base rate. | Supported for purchases: lifts are 4 to 26 times the real value. |
| H4c. Similar treatments are not distinguished. | Supported. The simulated gap between emails is indistinguishable from zero in 10 of 12 cells and has the wrong sign in two. |
| Exploratory: collapse is specific to low means. | Not supported. Direct answers collapse at means of 0.5, 4.8, and 7.8. |
| Exploratory: richer personas repair collapse. | Not supported. With real demographics the simulated counts have a rank correlation with real counts of -0.11 to +0.10; the demographics themselves explain about 1% of the heterogeneity. |

*Table 5. Hypotheses and evidence.*

# 6. Discussion

## 6.1 Theoretical contributions

Our results support a simple reading of synthetic purchase data: persona-conditioned LLM simulators compress customer heterogeneity, and the compression has a specific, measurable form. Proposition 1 shows why direct answers cannot be overdispersed in general (they lose Poisson noise and the share of heterogeneity that the persona does not describe), and the data are consistent with it: variance-to-mean ratios of direct answers sit between 0.00 and 0.57 in both settings, whatever the mean. Proposition 2 clarifies what an external heterogeneity term can and cannot do: it restores dispersion, but only the within-persona part, and its accuracy then rests on the model's mean. This reframes the usual advice to "add noise" to synthetic respondents. The amount of noise is not a free parameter; it is determined by how much heterogeneity the persona already carries.

Two further results extend what is known about LLM-based simulation. First, describing a distribution (Jang et al. 2026, Zhang et al. 2025a) helps more at a high mean than at a low mean, and in the settings where zeros are common it under-produces them. The zero share is the part of a count distribution that decides how many customers a campaign is not reaching, and this is where description fails. Second, evaluating a promotion simulator on relative effects alone is hazardous. The relation $RR = 1 + d/p_0$ shows that errors in the simulated base rate and errors in the simulated lift are confounded in the risk ratio, and our data contain cases in which the two readings of the same output disagree.

## 6.2 Implications for practice

For managers who consider synthetic customers for decision support, the evidence suggests a short diagnostic protocol.

1. *Compare shapes, not only means.* Before using synthetic counts, compute the variance-to-mean ratio, $\alpha$, and the zero share against a historical customer file, and check them with an interval, as we do here. A ratio near or below one signals collapse.
2. *Do not use direct integer answers.* In our data they returned a single value for practically every customer in several cells.
3. *If the model is used, use it for the mean only,* and inject the remaining heterogeneity externally, calibrated according to Proposition 2 on a historical or pilot sample. Verify that the model's mean is accurate; the hybrid inherits its errors.
4. *Treat a stated base rate as a prompt choice that must be tested.* It corrected the mean in some designs, collapsed all answers to one value in others, and changed the size of the simulated promotion effect by an order of magnitude.
5. *Validate on absolute effects and base rates.* Report the simulated base rate and the absolute lift next to the risk ratio, and compare both with a past randomized test before any revenue calculation.

## 6.3 Limitations and future research

The evidence is preliminary. We used one random seed, 200 to 600 simulated customers per cell, one prompt wording per design, and three small models, so our intervals capture sampling of customers but not variation across prompts, personas, or seeds. Larger and more recent models may collapse less, and the persistence of overstated purchase lifts there is an open question. The low-mean reference is a calibrated parametric distribution rather than the raw data, and the Complete Journey households are loyalty-card shoppers with relatively high purchase frequency. Richer personas built from real household demographics did not change the picture, but the demographics in these data explain almost none of the heterogeneity ($c^2/\alpha = 0.01$), so that test marks the limit of observable personas rather than a limit of particular models; settings in which observable attributes, such as purchase histories, are more predictive of purchase frequency would be a stronger test of Proposition 1. In the Complete Journey data campaigns were targeted rather than randomized, so only the email experiment supports a causal comparison. Design C truncates its top bin, which lowers the dispersion it can reach; we quantified this ceiling but did not remove it. Public data may also be part of the models' training data. Future work should evaluate the hybrid design with a calibrated mean, test prompts that elicit several candidate answers with probabilities, and use a randomized promotion data set with purchase counts, for example from a partner firm, so that the count-distribution and treatment-effect questions can be studied on the same customers.

# 7. Conclusion

Synthetic customers built from language models do not yet reproduce the shape of real purchase-count distributions or the size of real promotion effects. Direct and day-by-day designs collapse toward a single value whether the mean is 0.5 or 4.8; describing a distribution repairs part of the damage but loses zeros; and a hybrid that takes only the mean from the model matches the dispersion when that mean is accurate. In a randomized email test the models usually get the sign of the effect right, but the absolute lift in purchase probability is overstated by a large factor and similar treatments are not told apart. Practitioners who use synthetic customers should check dispersion and zero share against their own data, rely on the model for means only, and validate absolute effects before they act on them.

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

*Table B2. High-mean setting, 200 customers per cell. Reference row: empirical Complete Journey distribution. \* the 95% bootstrap interval excludes the reference value.*

{{TABLE_DEMO}}

*Table B3. Persona experiment with real household demographics, 200 households per cell. Reference row: real distribution of the 801 households (10,413 household-windows). \* the 95% bootstrap interval excludes the reference value.*

# Appendix C. Reproducibility {-}

All code, the pilot grid runner, the demographic-ceiling script, the analysis scripts, and the tables and figures used here are in the project repository (`ooklee-sudo/fluffy-meme`, folder `llm-count-study`). Raw model responses are saved with each run. Household-level Complete Journey data are not redistributed; the code reads them from the public package files.
