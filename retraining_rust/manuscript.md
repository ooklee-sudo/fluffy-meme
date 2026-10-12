---
title: "When Should a Firm Retrain Its Language Model? A Structural Model of AI Depreciation and Maintenance Timing"
---

**Target outlet:** MIS Quarterly (Research Article). **Status:** working draft; the empirical section is a template to be completed with field data (see bracketed notes).

## Abstract

Firms that deploy large language models (LLMs) face a quiet maintenance problem. As the world moves away from the data a model was trained on, its errors accumulate, yet retraining is costly and its true cost is rarely visible to outsiders or even to the firm's own accounting systems. We treat a deployed LLM as a depreciating information systems asset and model the retraining decision as an optimal replacement problem in the spirit of Rust (1987). Errors arrive as a Poisson process whose intensity rises with cumulative distribution drift; at each period the firm either retains the model or pays a fixed cost to reset it. We show that the retraining cost is identified from the timing of updates, derive the implied replacement policy, and propose a two-step estimator that is feasible with the aggregate weekly data firms typically hold. In Monte Carlo experiments the estimator recovers the structural parameters, with the retraining cost identified to within roughly 12 percent at 250 weekly observations and 7 percent at 500. Counterfactuals show that halving retraining cost (for example, through MLOps automation) brings the optimal retraining threshold forward by about 30 percent, while faster environmental drift pushes firms to tolerate higher error rates before acting. We discuss how the framework can be taken to field data and what it implies for the governance of AI systems.

**Keywords:** large language models, model drift, IT maintenance, dynamic discrete choice, structural estimation, MLOps

## 1. Introduction

A language model begins to age the moment it is deployed. Customers ask about products that did not exist when the training corpus was frozen, regulations change, slang shifts, and the share of requests that the model handles poorly creeps upward. Practitioners call this drift, and most firms deal with it by judgment: someone notices that complaints are rising and a retraining project is eventually approved. The decision matters. Retraining consumes engineering time, compute, and evaluation effort, and a new release brings its own risk of regressions. Waiting, however, is not free either, because every additional week of operation exposes customers to a degraded system.

This trade-off is old. Information systems researchers have long studied software maintenance, technical debt, and the timing of system replacement, and operations researchers have studied equipment replacement for even longer. What is new is that the asset in question deteriorates not because it wears out but because the environment changes around it, and that the cost of renewing it is largely hidden. We know of no study that asks how much firms implicitly pay to refresh an AI system, or whether their refresh timing is consistent with cost minimization.

We address three questions. First, what is the hidden cost of retraining a deployed LLM, and can it be identified from observational data? Second, at what level of accumulated error do firms choose to update, and is that choice consistent with an optimizing manager? Third, how do investments that lower the cost of updating, and competitive pressures that speed up drift, change the optimal maintenance cycle?

To answer them we adapt the dynamic discrete choice framework that Rust (1987) developed for bus engine replacement. The state variable is cumulative drift, which accrues stochastically. Errors arrive according to a Poisson process whose rate increases with drift, and the manager chooses each period between keeping the model and retraining it at a fixed cost. Because the cost is paid only when the firm acts, the timing of its actions reveals it. This is the same logic that allows the original model to recover the cost of an engine overhaul from nothing more than mileage and replacement records.

Our contribution is threefold. Conceptually, we recast LLM drift as the depreciation of an information systems asset and retraining as an investment decision with an identifiable, structurally interpretable cost. Methodologically, we show how the Rust framework can be combined with a count-data error process so that both error counts and update timing contribute to estimation, and we document how much precision is lost if the two stages are treated separately. Practically, we provide a way to put numbers on questions that managers already ask informally, such as what an MLOps automation investment is worth, or how a competitor's release should change one's own update schedule.

The paper is organized as follows. Section 2 positions the study in the literature. Section 3 presents the model and Section 4 the estimation strategy. Section 5 reports Monte Carlo evidence and counterfactuals. Section 6 describes the empirical setting and data. Section 7 discusses implications and limitations.

## 2. Background and Related Literature

**IT maintenance and technical debt.** A substantial literature treats maintenance as the dominant lifetime cost of software and links deferred maintenance to later failure. Sculley et al. (2015) argued that machine learning systems accumulate a distinctive form of technical debt, including entanglement and dependence on shifting data. Our setting shares that concern but isolates one mechanism, the loss of fit between a frozen model and a moving environment.

**Concept drift and temporal degradation of language models.** The machine learning literature documents that predictive performance declines when the data distribution changes (Gama et al. 2014), and recent work shows that language models trained on older text perform worse on newer text (Lazaridou et al. 2021; Luu et al. 2022). This work measures how quickly performance decays. It does not model the manager's decision about when to act, which is where our framework enters.

**Replacement and maintenance optimization.** The classical operations literature on optimal replacement and on the economic design of process-control charts (Duncan 1956) derives threshold policies in which an asset is renewed once a deterioration index crosses a critical value. Rust (1987) turned the replacement problem into an econometric one by adding unobserved payoff shocks, so that observed choices could be used to estimate the cost parameters. Subsequent work on conditional choice probability estimation (Hotz and Miller 1993) and on the properties of dynamic discrete choice estimators (Aguirregabiria and Mira 2010) provides the toolkit we rely on.

**Structural estimation in information systems research.** Structural econometric methods have been used in IS to recover primitives that cannot be observed directly, such as consumer preferences and platform fees. We extend this tradition to a producer-side technology decision, the upkeep of an AI system.

[Before submission: expand this section with the IS economics papers that use dynamic structural models, and verify every citation above against the original source.]

## 3. Model

### 3.1 Setup

Time is discrete and indexed by weeks. A firm operates one deployed LLM. The state $x_t \in \{0,1,\dots,N\}$ measures cumulative drift since the model was last refreshed. Each week the firm chooses $d_t \in \{0,1\}$, where $d_t=0$ means retain the current model and $d_t=1$ means retrain.

**Drift.** If the model is retained, drift advances by $\Delta_t \sim \text{Poisson}(\mu)$, so $x_{t+1}=\min(x_t+\Delta_t,N)$. If the firm retrains, drift is reset and then begins to accumulate again, so $x_{t+1}=\min(\Delta_t,N)$.

**Errors.** In week $t$ the number of errors observed is $n_t \sim \text{Poisson}(\lambda_0+\gamma\tilde x_t)$, where $\tilde x_t = x_t(1-d_t)$ is the post-decision state, $\lambda_0$ is the baseline error rate of a fresh model, and $\gamma>0$ is the marginal increase in the error rate per unit of drift.

**Payoffs.** Each error costs the firm $c$. Retraining costs $RC$. Flow payoffs are

$$u(x,0)=-c(\lambda_0+\gamma x)+\varepsilon_0,\qquad u(x,1)=-RC-c\lambda_0+\varepsilon_1,$$

where $\varepsilon_d$ are payoff shocks known to the manager but unobserved by the econometrician, assumed to be independently distributed Type I extreme value with unit scale.

### 3.2 Optimal policy

With discount factor $\beta$, the value function satisfies

$$V(x)=\ln\Big(\exp\{u(x,0)+\beta\,E[V(x')\mid x,0]\}+\exp\{u(x,1)+\beta\,E[V(x')\mid 0]\}\Big),$$

and the probability of retraining in state $x$ takes the logit form

$$P(d=1\mid x)=\frac{1}{1+\exp\{v_0(x)-v_1(x)\}},$$

where $v_d$ are the choice-specific values. Because drift is monotone and the error rate is increasing in drift, the value of retaining the model falls with $x$ while the value of retraining does not depend on it. The retraining probability is therefore increasing in $x$, and we define the threshold $x^*$ as the smallest state at which this probability exceeds one half.

### 3.3 Properties of the solution

**Proposition 1 (existence and uniqueness).** For $\beta\in[0,1)$ the Bellman operator is a contraction in the sup norm on the finite state space, so $V$ exists, is unique, and is obtained by value iteration from any starting point.

*Proof.* The operator $T V(x)=\ln\sum_{d}\exp\{u(x,d)+\beta E[V(x')\mid x,d]\}$ satisfies Blackwell's sufficient conditions: it is monotone, and $T(V+a)=TV+\beta a$ for any constant $a$. Hence $\|TV-TW\|_\infty\le\beta\|V-W\|_\infty$. $\square$

**Proposition 2 (monotone retraining probability).** $V(x)$ is non-increasing in $x$, and $P(d=1\mid x)$ is non-decreasing in $x$. Consequently the threshold $x^*$ is well defined.

*Proof.* Let $V_0\equiv 0$ and $V_{k+1}=TV_k$. Suppose $V_k$ is non-increasing. The transition kernel under retention is stochastically monotone, since $x+\Delta$ is increasing in $x$ and truncation at $N$ preserves order, so $E[V_k(x')\mid x,0]$ is non-increasing in $x$. Because $u(x,0)=-c(\lambda_0+\gamma x)+\varepsilon_0$ is decreasing in $x$, the retention value $v_0^{k}(x)$ is decreasing, while the retraining value $v_1^{k}$ does not depend on $x$. The logsum of a decreasing function and a constant is non-increasing, so $V_{k+1}$ is non-increasing. The property is preserved in the limit. Finally $v_1-v_0$ is non-decreasing in $x$, so the logit probability is as well. $\square$

**Numerical regularity (not proved).** In every parameterization we examined, $x^*$ is increasing in $RC$ and in $\mu$ and decreasing in $\beta$ (Section 5.3). The first is the intuition of any replacement problem. A closed-form comparative static is not available because $V$ itself depends on $RC$ through the continuation values; we therefore report these as computed regularities.

### 3.4 Identification

Three features of the structure deserve comment. First, $c$ and $RC$ are not separately identified from choices: only $RC/c$ is, with the scale of the shocks normalized to one. Reported retraining costs are therefore measured in units of errors, and a monetary value requires an external estimate of $c$, such as customer-support cost per failed interaction. Second, $\lambda_0$ appears in both payoffs and cancels from the choice problem, so it is identified only from the error process. Third, $\beta$ cannot be identified from choices in this class of models and must be set or varied in sensitivity analysis.

## 4. Estimation

We use a two-step procedure. In the first step, $\mu$ is estimated by the mean drift increment over weeks in which the model was retained, and $(\lambda_0,\gamma)$ by maximum likelihood on the Poisson error process. In the second step, $RC$ is estimated by a nested fixed point (NFXP) algorithm: for each candidate $RC$ the Bellman equation is solved by value iteration, and the choice likelihood is maximized over $RC$ holding first-step estimates fixed (Rust 1987).

A simple two-step design understates uncertainty because it ignores sampling error in the first-step parameters. We therefore also estimate $(\gamma,RC)$ jointly from the choice likelihood, which is less precise but delivers honest standard errors, and we recommend either a joint likelihood over errors and choices or a bootstrap in applied work.

## 5. Numerical Results

All results below come from the accompanying code (`rust_retrain.py`). The data-generating process uses $\gamma=0.5$, $RC=40$, $\lambda_0=5$, $\mu=1$, $\beta=0.95$, $c=1$, and a state space truncated at $N=80$.

### 5.1 Optimal policy

The optimal retraining threshold is $x^*=14$. At that point the expected weekly error rate is 12.0, or 2.4 times the baseline. In a simulated panel of 3,000 weeks, the average retraining cycle is about 14 weeks.

### 5.2 Parameter recovery

Table 1 reports 100 Monte Carlo replications of 3,000 weeks each. The estimator recovers the structural parameters closely.

| Parameter | True | Mean estimate | SD across replications |
|---|---|---|---|
| $\mu$ | 1.0 | 0.998 | 0.018 |
| $\lambda_0$ | 5.0 | 4.998 | 0.068 |
| $\gamma$ | 0.5 | 0.499 | 0.011 |
| $RC$ (two-step) | 40 | 39.92 | 1.03 |
| $\gamma$ (joint, choice data only) | 0.5 | 0.501 | 0.038 |
| $RC$ (joint, choice data only) | 40 | 40.08 | 2.98 |

The two-step standard deviation of $RC$ (1.03) is about a third of the joint one (2.98), which illustrates the point made in Section 4.

Table 2 shows how precision depends on the number of weekly observations, using up to 50 replications per cell.

| Weeks | Mean $\widehat{RC}$ | SD |
|---|---|---|
| 100 | 38.5 | 6.7 |
| 250 | 40.0 | 4.8 |
| 500 | 40.2 | 2.8 |
| 1,000 | 40.1 | 2.1 |

With about five years of weekly data on a single model the cost is recovered to within roughly 12 percent (one standard deviation); pooling several deployments would tighten this.

### 5.3 Counterfactuals

| Retraining cost $RC$ | 10 | 20 | 40 | 80 | 160 |
|---|---|---|---|---|---|
| Optimal threshold $x^*$ | 7 | 10 | 14 | 21 | 32 |

| Drift speed $\mu$ | 0.5 | 1.0 | 1.5 | 2.0 |
|---|---|---|---|---|
| Optimal threshold $x^*$ | 11 | 14 | 17 | 19 |

| Discount factor $\beta$ | 0.90 | 0.95 | 0.99 |
|---|---|---|---|
| Optimal threshold $x^*$ | 16 | 14 | 13 |

Halving the retraining cost from 40 to 20 lowers the threshold from 14 to 10, so a firm that automates its retraining pipeline should update at a lower level of accumulated drift. Faster drift raises the threshold in drift units, but because drift also accumulates faster the calendar time between updates still shortens. We therefore recommend reporting the policy both in drift units and in expected weeks between updates.

These are results from simulated data and demonstrate that the structure is identified and the estimator works. They are not empirical findings.

## 6. Empirical Setting and Data [to be completed]

**Primary sample (target).** Weekly error reports and model-update logs from one or more firms operating customer-facing LLM chatbots, provided in de-identified, aggregated form. This sample is the credible one for structural interpretation, because the update decision is made by an identifiable operator facing the cost trade-off in the model.

**Supporting sample.** Weekly counts of bug and quality issues in the public repositories and discussion forums of open-weight models, with release dates as update events. Release timing for open-source models also reflects research roadmaps and competition, so the estimated cost should be read as a shadow cost of release rather than a pure maintenance cost. Issue counts should enter with an exposure offset (downloads or active users).

**Drift proxy.** Cumulative drift is not directly observed. Candidate measures include weeks since the last update, the distributional distance between current user prompts and the training window, and the share of requests that mention post-cutoff entities. We plan to show that results are robust across proxies.

**Robustness.** Overdispersion in error counts (negative binomial), a non-zero post-retraining state to capture release regressions, multiple actions (full retraining, fine-tuning, prompt revision), and time-varying error intensity.

[Report here: descriptive statistics, first-stage estimates, estimated $RC/c$ with standard errors, model fit (observed versus predicted retraining hazard by drift level), and counterfactuals using estimated parameters.]

## 7. Discussion

**Implications.** The framework turns a managerial rule of thumb into a quantity that can be audited. If the estimated cost of a firm is far above what an engineering budget would suggest, either the firm faces hidden organizational frictions or the drift measure is mis-specified, and both are informative. For managers, the counterfactuals provide a way to value MLOps investments by their effect on the optimal update schedule, and to see that the same investment is worth more where drift is fast.

**Limitations.** First, the model assumes a single decision-maker minimizing expected discounted cost, which may not hold for firms whose releases are driven by marketing or competitive signaling. Second, the state is a proxy, and misspecification of the proxy will flow into the cost estimate. Third, the reset assumption is stylized. Fourth, we treat the error cost as constant, although errors in high-stakes interactions are likely to cost more. Finally, our numerical evidence is based on simulation, and the substantive claims about firms await field data.

**Conclusion.** Maintaining an AI system is an investment decision with a cost that can, in principle, be read from the timing of updates. We provide the model and estimator that make this possible, show that they recover known primitives, and outline the data needed to apply them.

## Appendix A. Algorithm

1. Fix $(\gamma,RC,\lambda_0,\mu,\beta,c)$ and build the $(N+1)\times(N+1)$ retention transition matrix $P$ with $P_{x,x+k}=\Pr(\Delta=k)$ for $x+k<N$ and the residual mass placed on $N$.
2. Iterate $V\leftarrow \ln\big(\exp\{u_0+\beta PV\}+\exp\{u_1+\beta P_{0\cdot}V\}\big)$ (computed with the log-sum-exp trick) until $\|V_{k+1}-V_k\|_\infty<10^{-10}$.
3. Compute $P(d=1\mid x)$ from the converged choice-specific values and evaluate the log-likelihood $\sum_t [d_t\ln p(x_t)+(1-d_t)\ln(1-p(x_t))]$.
4. Maximize over $RC$ (bounded one-dimensional search) in the two-step design, or over $(\gamma,RC)$ in the joint design.

## Appendix B. Testable Predictions for the Empirical Section

Once field data are available, the structure yields predictions that can be checked without relying on the estimated parameters alone:

- **P1.** The retraining hazard is increasing in the drift proxy (Proposition 2).
- **P2.** Among otherwise similar deployments, those with access to automated retraining pipelines update at lower drift levels.
- **P3.** Deployments in faster-moving domains exhibit shorter calendar cycles even when their tolerated error level is higher.
- **P4.** The estimated $RC/c$ is stable when the drift proxy is replaced by an alternative proxy; large changes indicate proxy misspecification rather than a change in cost.

## References

Aguirregabiria, V., and Mira, P. 2010. "Dynamic Discrete Choice Structural Models: A Survey," *Journal of Econometrics* (156:1), pp. 38–67.

Duncan, A. J. 1956. "The Economic Design of $\bar X$ Charts Used to Maintain Current Control of a Process," *Journal of the American Statistical Association* (51:274), pp. 228–242.

Gama, J., Žliobaitė, I., Bifet, A., Pechenizkiy, M., and Bouchachia, A. 2014. "A Survey on Concept Drift Adaptation," *ACM Computing Surveys* (46:4), Article 44.

Hotz, V. J., and Miller, R. A. 1993. "Conditional Choice Probabilities and the Estimation of Dynamic Models," *Review of Economic Studies* (60:3), pp. 497–529.

Lazaridou, A., et al. 2021. "Mind the Gap: Assessing Temporal Generalization in Neural Language Models," *Advances in Neural Information Processing Systems* 34.

Luu, K., et al. 2022. "Time Waits for No One! Analysis and Challenges of Temporal Misalignment," *Proceedings of NAACL 2022*.

Rust, J. 1987. "Optimal Replacement of GMC Bus Engines: An Empirical Model of Harold Zurcher," *Econometrica* (55:5), pp. 999–1033.

Sculley, D., et al. 2015. "Hidden Technical Debt in Machine Learning Systems," *Advances in Neural Information Processing Systems* 28.
