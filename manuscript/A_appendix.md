## Appendix A. Proofs

**Notation.** A path is the sequence of errors by type and the completion indicators of the steps. Let $T$ be the first completing step, $S_t = \sum_j w_j N_{j,t}$ the weighted count of errors before step $t$, and $\pi(S) = 1 - e^{-S}$ the probability that the task is derailed at weighted count $S$. For a threshold $c$ on the weighted count, a step $t$ is taken under the firm's rule only if $S_t < c$, and we write $\tau_c = \inf\{t : S_t \ge c\}$. Let $\tau_h$ be the first step in which the agent transfers the task itself (infinite if never). A task is handed to a person by someone if $\min(\tau_c, \tau_h) \le T$ and is completed otherwise.

**Single-type threshold, Equation (A1).** With one error type and no self-transfer the rule of Proposition 1 reads: hand off at the first count $N$ with
$$(1-\theta_w)^N \le \left[1 - \frac{qH - k - c\mu}{qF}\right] e^{\mu\theta_w}. \tag{A1}$$

### Lemma A1 (monotonicity of the policy family)

For a threshold $c$ let $a_c$ be the expected cost of the steps taken (step and error costs), $z_c = E[\pi(S_{T+1})\,\mathbf 1\{T < \min(\tau_c, \tau_h)\}]$ the probability that the task is completed in a derailed state, and $P_c = P(\min(\tau_c, \tau_h) \le T)$ the probability that the task is handed to a person by either party. The expected cost of the policy is
$$a_c + F\,z_c + H\,P_c .$$
Then $a_c$ and $z_c$ are nondecreasing and $P_c$ is nonincreasing in $c$, with $a_0 = z_0 = 0$ and $P_0 = 1$.

*Proof.* On a given path $S_t$ is nondecreasing in $t$, so $\tau_c$ is nondecreasing in $c$ and so is $\min(\tau_c, \tau_h)$. The event $\{T < \min(\tau_c, \tau_h)\}$ therefore grows with $c$ and the payoff $\pi(S_{T+1}) \ge 0$ on it does not depend on $c$, so $z_c$ is nondecreasing. The complementary event shrinks, so $P_c$ is nonincreasing. More steps are taken as $c$ grows, so $a_c$ is nondecreasing. At $c = 0$ the firm hands off before the first step. $\square$

Without self-transfer, $z_{c'} - z_c = E[\pi(S_{T+1})\,\mathbf 1\{\tau_c \le T < \tau_{c'}\}]$ is strictly positive for consecutive integer counts in the single-type case, and likewise $P_c - P_{c'}$, because the event has positive probability when $q \in (0,1)$ and $\mu > 0$. Self-transfer is independent of the completion indicators and does not change these arguments; we checked the strict version without self-transfer numerically and use only the weak version with it.

### Proof of Proposition 1

Consider the state after some steps, with counts $N = (N_1, \dots, N_J)$ and no transfer so far. Stopping now costs $H$. Taking one more step and then stopping costs
$$k + c\sum_j\mu_j + E\Big[s\,H + (1-s)\big(qF\,\pi(N+e) + (1-q)H\big)\Big],$$
where $e = (e_1, \dots, e_J)$ are the errors in the step and $s = 1 - \prod_j (1-\theta_{hj})^{e_j}$ is the probability that the agent transfers the task. Independence of the Poisson counts gives $E[1-s] = \rho$ and
$$E\big[(1-s)\,(1 - \pi(N+e))\big] = \prod_j (1-\theta_{wj})^{N_j}\,\exp\Big(-\sum_j \mu_j\tilde\theta_j\Big),$$
so that $E[(1-s)\pi(N+e)] = \rho - \prod_j (1-\theta_{wj})^{N_j}\exp(-\sum_j\mu_j\tilde\theta_j)$. Substituting, one more step followed by a hand-off is at least as good as handing off now if and only if
$$k + c\sum_j\mu_j + qF\rho - qF\prod_j(1-\theta_{wj})^{N_j}e^{-\sum_j\mu_j\tilde\theta_j} \le qH\rho,$$
which rearranges to $\prod_j (1-\theta_{wj})^{N_j} \ge R$, or $\sum_j w_j N_j \le -\ln R$. The left-hand side of this inequality is nonincreasing as errors accumulate, and a self-transfer ends the task, so once handing off is at least as good as one more step it remains so at all later states. The problem is therefore monotone in the sense of Chow, Robbins, and Siegmund (1971, Theorem 3.5), and the one-step look-ahead rule is optimal. The boundary cases follow from the inequality. With $\theta_{hj} = 0$ and one type, the rule is Equation (A1). $\square$

We also verified the closed form against value iteration on the count vector: it agreed with the optimal stopping decision in 150 random single-type parameter sets and in all 3,025 states of 25 random two-type models.

### Proof of Proposition 2

Every policy $\pi$ has expected cost $A_\pi + H P_\pi$, where $A_\pi$ is the expected cost of the agent's steps and of wrong outputs and $P_\pi$ is the probability that a person takes over; neither depends on $H$. The optimal cost $G(H) = \inf_\pi (A_\pi + H P_\pi)$ is therefore concave and nondecreasing in $H$, with $G(0) = 0$. Let $\bar C$ be the cost of never handing off, so that the best static choice costs $\min\{H, \bar C\}$, and let $V(H) = \min\{H, \bar C\} - G(H)$. For $H \le \bar C$, $V(H) = H - G(H)$ is convex with $V(0) = 0$ and $V \ge 0$, and a convex function that is zero at the origin and nonnegative is nondecreasing. For $H \ge \bar C$, $V(H) = \bar C - G(H)$ is nonincreasing because $G$ is nondecreasing. $\square$

### Proof of Proposition 3

*(a), (b).* By Lemma A1 the cost of threshold $c$ at check quality $d$ and hand-off cost $H$ is $J(c, d, H) = a_c + F(d)\,z_c + H P_c + v(d)$ with $F(d) = F_u - d(F_u - F_d)$. For $d' > d$, $J(c, d', H) - J(c, d, H) = -(d'-d)(F_u - F_d) z_c + v(d') - v(d)$, which is nonincreasing in $c$ because $z_c$ is nondecreasing. For $H' > H$, $J(c, d, H') - J(c, d, H) = (H'-H) P_c$, which is nonincreasing in $c$ because $P_c$ is. Both differences are monotone in $c$ (decreasing differences), so by the monotone comparative statics theorem (Topkis 1978; Milgrom and Shannon 1994) the set of minimizing thresholds is nondecreasing in $d$ and in $H$ in the strong set order. The same argument with the roles reversed, using that $J(c', d, H) - J(c, d, H) = a_{c'} - a_c + F(d)(z_{c'} - z_c) + H(P_{c'} - P_c)$ is nonincreasing in $d$ for $c' > c$ because $F(d)$ falls with $d$, gives that the optimal check quality is nondecreasing in $c$.

*(c).* Let $G(H, F) = \min_c \{a_c + F z_c + H P_c\}$. It is concave and piecewise linear in $F$ with $\partial G/\partial F = z_{c^*(H,F)}$ almost everywhere (envelope theorem), so $V(H; d) = G(H, F_u) - G(H, F(d)) = \int_{F(d)}^{F_u} z_{c^*(H,f)}\,df$. By (b), $c^*(H, f)$ is nondecreasing in $H$ for every $f$ and $z_c$ is nondecreasing in $c$, so the integrand and hence $V$ are nondecreasing in $H$. For $H$ large enough the firm never hands off, $c^* = \infty$ for every $f$ in the range, and $V = (F_u - F(d))\,z_\infty = d\,(F_u - F_d)\,z_\infty$. When hand-offs are so cheap that $c^* = 0$, $z_0 = 0$ and $V = 0$. With $v(d) = \kappa d^2$ the net gain $d(F_u-F_d)z_\infty - \kappa d^2$ is maximized at $d = (F_u - F_d)z_\infty/(2\kappa)$, with value $[(F_u-F_d)z_\infty]^2/(4\kappa)$. $\square$

*(d).* Mark each error with an independent uniform variable and let the agent transfer the task at an error whose mark is below $\theta_h$. A larger $\theta_h$ makes $\tau_h$ weakly earlier on every path, so the event $\{T < \min(\tau_c, \tau_h)\}$ shrinks, and since the payoff $\pi(S_{T+1}) \ge 0$ does not depend on $\theta_h$, $z_c$ is nonincreasing in $\theta_h$; $z_\infty$ is its limit in $c$. $\square$

We checked (a), (b), and (c) numerically in 40 random parameter sets each, with and without self-transfer (half of the sets had $\theta_h = 0$): no violations of the monotonicity of $a_c$, $z_c$, and $P_c$, of the monotonicity of the optimal threshold in $H$ and in $d$ (with costs within $10^{-9}$ treated as tied, since neighbouring large thresholds are reached with probability below $10^{-16}$ and have identical cost up to rounding), of the monotonicity and the plateau of the value of verification, or of the envelope identity.

### Proof of Proposition 4

Let $A(P)$ be the lower convex hull of the points (probability that a task is handed to a person, cost excluding the hand-off cost) of the threshold policies; randomizing over thresholds makes every point of the hull achievable. $A$ is convex and decreasing. The system cost per task is $f(P) = A(P) + hP + \omega P\,W(\Lambda P)$, which is convex because $\lambda W(\lambda)$ is convex (Lemma A2). The decentralized outcome is the point at which each task, taking $\tilde H = h + \omega W(\Lambda P)$ as the price of a hand-off, minimizes $A(P') + P'\tilde H$ over the hull; because the best response is nonincreasing in $\tilde H$ and $\tilde H$ is increasing in $P$, the resulting $P_{\text{dec}}$ is unique.

Suppose $P_{\text{dec}} < P_{\text{sys}}$. Write $A'_\pm$ for the one-sided derivatives. The equilibrium condition at $P_{\text{dec}}$ (which is not the upper corner) gives $-A'_+(P_{\text{dec}}) \le h + \omega W(\Lambda P_{\text{dec}})$. Optimality of $P_{\text{sys}}$ (above the lower corner, since $P_{\text{sys}} > P_{\text{dec}}$) gives $h + \omega M(P_{\text{sys}}) \le -A'_-(P_{\text{sys}})$, where $M(P) = \frac{d}{dP}[P\,W(\Lambda P)] = W + \Lambda P\,W' \ge W$. Convexity of $A$ gives $A'_+(P_{\text{dec}}) \le A'_-(P_{\text{sys}})$. Chaining,
$$h + \omega M(P_{\text{sys}}) \le -A'_-(P_{\text{sys}}) \le -A'_+(P_{\text{dec}}) \le h + \omega W(\Lambda P_{\text{dec}}) < h + \omega W(\Lambda P_{\text{sys}}) \le h + \omega M(P_{\text{sys}}),$$
a contradiction. Hence $P_{\text{dec}} \ge P_{\text{sys}}$. The wedge between the marginal and the average delay cost is $\omega\Lambda P W'$. The two outcomes can coincide at a vertex of the hull, where the subdifferential is an interval, or at a corner. $\square$

### Lemma A2 (convexity of the queueing delay)

In the M/M/1 queue the mean number waiting is $L_q = \rho^2/(1-\rho)$ with $\rho = \lambda/m$, whose second derivative is positive, and the mean wait $W_q = \lambda/(m(m-\lambda))$ increases with $\lambda$. In the M/G/1 queue with Poisson arrivals, $L_q = \lambda^2 E[S^2]/(2(1-\rho))$ is convex and increasing. For the M/M/c queue, convexity of the mean queue size in the traffic intensity is due to Grassmann (1983). Since $L_q(0) = 0$, $W_q = L_q/\lambda$ is nondecreasing. Adding the service time, which is constant, adds a term linear in $\lambda$ to $\lambda W(\lambda)$. In the Allen–Cunneen approximation the delay is the M/M/c delay multiplied by a constant $(C_a^2 + C_s^2)/2$, so $\lambda W(\lambda)$ is a positive multiple of $L_q$ and remains convex. We checked convexity and the monotonicity of $W_q$ numerically for $c \in \{1, 2, 3, 5, 10, 20, 50\}$ on a grid of 4,001 loads. The Allen–Cunneen formula is an approximation, and convexity for the exact G/G/c queue is not guaranteed. $\square$

## Appendix B. Details of the experiments

*Models and access.* All agents were accessed through OpenRouter at temperature 0.5. The commercial models were run with low reasoning effort, and prompt caching was enabled for Claude Sonnet 5.5. Requests to a given model may be served by several providers. We excluded two providers for the Llama models that rejected histories containing parallel tool calls, and providers of DeepSeek-V3.1 whose tool templates failed. Llama-3.1-8B often returned tool arguments that were not valid JSON, for example two objects concatenated; in both studies we kept the first object and recorded the event instead of ending the run. Failures caused by the provider were retried, and failures caused by the agent's output were kept as outcomes.

*Study 1.* We used $\tau^2$-bench version 2.0 in text mode with its airline and retail task sets, the default language-model agent, and the default user simulator, played by GPT-4.1-mini. Success is the benchmark's environment check, which compares the final database with the database produced by the correct sequence of actions; we did not use language-model judges. The injection intercepts the environment's response to the agent's tool calls. Injected calls are not executed, and the benchmark's evaluation replays them with the same injected response, so that injections cannot change the database. Llama agents were run with three repetitions, and DeepSeek-V3.1 and the commercial models with two because of provider rate limits and cost.

*Study 2.* The 87 bugs come from youtube-dl (38), thefuck (32), tqdm (7), httpie (5), fastapi (3), cookiecutter (1), and tornado (1). For each bug we built the buggy version with its dependencies in a separate environment, added the developer's test files from the fixed version, and recorded the fail-to-pass and pass-to-pass tests by running them before and after applying the developer's patch. Each run starts from a clean copy of the buggy version and is reverted afterwards, and runs on the same bug are serialized across agents. The agent's prompt contains the identifiers of the failing tests and the last lines of their output. Tool outputs are truncated to 4,000 characters, file views to 150 lines, and test runs to 300 seconds.

*Analysis.* Agent errors are tool calls that the real environment rejected. Success estimates use all runs, pair injected and control runs by task and repetition, and use a task-clustered bootstrap with 1,000 resamples (2,000 for the splits of Section 5.3). The split into $\theta_h$ and $\theta_w$ counts a run as a transfer if it contains a call to `transfer_to_human_agents`; the additive and the model-consistent estimators are defined in Section 5.3. The classification of the two calls after the injection point into cross-check, retry, and neither uses the tool names logged for each call; arguments were not logged. The total cost of the 11,352 runs, including pilots, was about US\$330.

*Replication.* The replication package contains the run-level logs and the code of the experiments. The scripts for the splits, the tables, the figures, the numerical checks of the propositions, and the build of this document are in the repository.

{{TA1}}


## Appendix C. Calibration of costs

The numerical results use the costs in Table C1, expressed in dollars. Where a value comes from a vendor or other secondary source, we say so; these were found by web search and several were not checked against the original reports (the SQM Group white paper, the ICMI and MetricNet benchmarks, and the Gartner figure). They should be verified before the values are relied on. Values measured in our own experiments come from the run logs in the replication package.

{{CALIB}}

*Table C1. Costs used in the numerical results.*

The wrong-output cost $F$ and the ratio $F/H$ drive the thresholds. Table C2 shows the threshold for an agent with $\theta_w = 0.12$, $\theta_h = 0.05$, and a Claude Sonnet 5.5-like error rate, for a range of $H$ and $F$. The smallest ratio $F/H$ at which the count rule binds within 10, 5, 3, and 2 errors is {{BE10}}, {{BE5}}, {{BE3}}, and {{BE2}} at $H = \$8.82$.

{{SENS}}

*Table C2. Count at which the firm should hand off, by hand-off cost $H$ (rows) and wrong-output cost $F$ (columns), for $\theta_w = 0.12$ and $\theta_h = 0.05$.*

The cost of a wrong output depends on the domain. Table C3 gives the evidence we found for each domain and the resulting range of $F$ and of the ratio $F/H$ with $H = \$8.82$.

| Domain | Evidence | $F$ (ratio $F/H$) | Reliability |
|---|---|---|---|
| Any customer service | One repeat contact, reported to cost about as much as a first contact ($8–16) | $8.82–16 (1.0–1.8) | Vendor rule of thumb |
| Retail | Return processing reported at $10–20, $20–30, or $15–30 per return, or about 30% of the item price (Optoro, as reported by NBC); chargeback fee $15–50 and an all-in cost of about $128 per chargeback (attributed to Mastercard and Javelin) | $29 (repair contact plus $20 return processing) to $157 (plus one chargeback): 3.3–17.8 | Secondary and vendor sources; no primary source confirmed |
| Airline | *Moffatt v. Air Canada*, 2024 BCCRT 149: CA\$650.88 in damages, CA\$36.14 interest, and CA\$125 fees, CA\$812.02 in all (about US\$600; the exchange rate is approximate), after a chatbot gave wrong fare information. EU261 flat compensation of €250, €400, or €600 by distance for cancellations and denied boarding | $8.82 (repair only) to about $609 (every wrong output a severe case); $39 if one in twenty is severe (assumption): 1–69 | Case: tribunal decision, known through law-firm summaries. Share of severe cases: assumption |
| Code repair | Developer time to repair the defect; median wage of software developers about $65 per hour (BLS, May 2025, derived from the annual median of $135,980); hours per defect not sourced | Of the same order as the cost of a hand-off, because a developer repairs it (about 1–3) | Wage: official. Hours: assumption |

*Table C3. Evidence on the cost of repairing a wrong output, by domain.*

*Sources.* *Moffatt v. Air Canada* (https://decisions.civilresolutionbc.ca/crt/crtd/en/525448/1/document.do) and a summary by the American Bar Association (https://www.americanbar.org/groups/business_law/resources/business-law-today/2024-february/bc-tribunal-confirms-companies-remain-liable-information-provided-ai-chatbot/); EU261 as summarized by an airline help page (https://help.ryanair.com/hc/en-ie/articles/12891928880401-Regulation-EU261); return processing costs (https://www.nbcnews.com/news/us-news/retail-returns-890-billion-problem-rcna183359; https://www.clickpost.ai/blog/how-much-do-returns-cost-retailers); chargeback costs (https://www.chargeflow.io/blog/understanding-chargeback-fees-and-costs-a-merchants-guide; https://hyperswitch.io/blog/the-true-cost-of-a-chargeback); U.S. Bureau of Labor Statistics, software developers (https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm); SQM Group first-call-resolution white paper (https://survey.sqmgroup.com/pdf/FCRWhitepaper2020.pdf); vendor roll-up of cost-per-resolution benchmarks (https://www.retellai.com/learn/cost-per-resolution-benchmarks-for-ai-and-human-handled-calls); vendor-reported cost per AI resolution (https://fin.ai/learn/ai-customer-service-cost-savings-industry); repeat-contact costs (https://www.kustomer.com/glossary/cost-per-contact/; https://televerde.com/what-a-repeat-contact-really-costs-in-your-contact-center/); handle-time benchmarks as summarized by an aggregator (https://stealthagents.com/research/customer-support-average-handle-time-statistics-2026/); U.S. Bureau of Labor Statistics, Occupational Outlook Handbook, customer service representatives (https://www.bls.gov/ooh/office-and-administrative-support/customer-service-representatives.htm).
