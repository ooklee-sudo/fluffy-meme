## 4. Analysis

### 4.1 Count errors by what they cause

Write $N_j$ for the number of type-$j$ errors so far, $w_j = -\ln(1-\theta_{wj})$ for the weight of a type-$j$ error, and $\rho = \exp(-\sum_j \mu_j\theta_{hj})$ for the probability that the agent does not transfer the task in a step.

**Proposition 1 (count rule).** The optimal policy hands the task to a person at the first step at which the weighted count $\sum_j w_j N_j$ reaches $-\ln R$, where
$$R = e^{\sum_j \mu_j \tilde\theta_j}\left[\frac{k + c\sum_j \mu_j}{qF} - \rho\,\frac{H-F}{F}\right].$$
If $R \ge 1$ the firm should hand off at once. If $R \le 0$, or if all $\theta_{wj} = 0$ and $R < 1$, it should never hand off on account of errors.

*In words.* Count each error by how likely it is to lead to a wrong output, and hand off when the total gets large enough. An error type that never produces a wrong output should not be counted at all, however often it occurs. Without self-transfer ($\theta_{hj} = 0$) the rule reduces to the single-type threshold of Equation (A1) in Appendix A.

*Remark (what self-transfer changes).* The agent's own transfers affect the threshold only through the factors $e^{\sum_j\mu_j\tilde\theta_j}$ and $\rho$, which differ from one by terms of order $\mu$. In numerical examples ($\theta_w$ between 0.1 and 0.3, $F = 60$ or $100$) the optimal count did not change when $\theta_h$ was varied from 0 to 0.8, except in one case ($\theta_w = 0.3$, $F = 60$), where it fell from two to one. The threshold is set by $\theta_w$. Self-transfer matters for how much work reaches the reviewers (Section 4.3) and for the value of verification (Section 4.2), not for when the firm should step in.

Figure 1 shows the threshold as a function of $\theta_w$ for three costs of repairing a wrong output. With the costs calibrated in Appendix C, a hand-off costs $H = \$8.82$, and a wrong output costs at least one more human contact ($F = \$12.35$). The threshold is set mainly by the ratio $F/H$. With $\theta_w = 0.12$ the count rule binds within ten errors only if a wrong output costs at least {{BE10}} times a hand-off, within five errors at {{BE5}} times, and within three at {{BE3}} times. For Claude Sonnet 5.5, whose estimate of $\theta_w$ after a misleading message is about 0.12 across customer service (0.15 to 0.18 in retail), the threshold is {{SONNET_N}}. For GPT-6.1-terra $\theta_w$ is indistinguishable from zero and no count rule is warranted, even though its misleading errors have large consequences in another way: they send work to reviewers (Section 5).

{{FIG1}}

### 4.2 Escalation and verification are substitutes

Let $G(H, F)$ be the expected cost of the best count rule for a given hand-off cost $H$ and wrong-output cost $F$. Call the saving relative to the better of the two static choices (always hand off, never hand off) the *value of monitoring*, and call $V(H; d) = G(H, F_u) - G(H, F(d))$ the *value of verification at quality $d$*.

**Proposition 2 (monitoring pays at the margin).** Let $\bar C$ be the expected cost of never handing off. The value of monitoring is nondecreasing in $H$ up to $H = \bar C$ and nonincreasing beyond it.

*In words.* Monitoring is worth building for tasks where taking the work back costs about as much as letting the agent finish. Tasks that are cheap to reassign can simply be reassigned, and tasks that are very costly to reassign stay with the agent whatever the monitor reports.

**Proposition 3 (verification substitutes for escalation).**

(a) The optimal count threshold is nondecreasing in the quality $d$ of the output check, and the optimal check quality is nondecreasing in the threshold: tighter escalation lowers the value of checking.

(b) The optimal threshold is nondecreasing in the hand-off cost $H$.

(c) The value of verification $V(H; d)$ is nondecreasing in $H$. It is zero when hand-offs are so cheap that the firm always hands off, and it equals $d\,(F_u - F_d)\,z_\infty$ when the firm never hands off, where $z_\infty$ is the probability that a task finishes derailed when the firm never intervenes. With $v(d) = \kappa d^2$ the check that is worth buying in that case has quality $d = (F_u - F_d)\,z_\infty/(2\kappa)$ and a net gain of $[(F_u - F_d)\,z_\infty]^2/(4\kappa)$.

(d) The probability $z_c$ of finishing derailed, and with it the largest value of verification $d\,(F_u - F_d)\,z_\infty$, is nonincreasing in the agent's self-transfer probability $\theta_h$.

*In words.* Checking outputs and stepping in during the run do the same job, so more of one means less of the other. Escalation is worth most at the margin of delegation; verification is worth most when people are hardest to reach. An agent that transfers tasks on its own also lowers the need to check its outputs, because a task that has been handed over cannot end with a wrong output.

Figure 2 shows which combination of controls is best as the cost of reaching a person and the cost of verifying one output vary, without self-transfer and with frequent self-transfer ($\theta_h = 0.5$). Self-transfer lowers the value of verification. The probability of finishing derailed when the firm never intervenes falls from {{F2_Z0}} to {{F2_Z1}}, and verification is adopted in {{F2_NV1}} of the {{F2_N}} cases shown, against {{F2_NV0}} without self-transfer. We did not manipulate verification in our experiments. The coding agent can run the tests, which checks its own work, and its effects were smaller than those of the customer-service agent, which is consistent with the ordering of Figure 2 but does not test it.

{{FIG2}}

### 4.3 Reviewer capacity

So far the hand-off cost $H$ is a constant. With a limited number of reviewers, each hand-off also delays the others, and the cost of a hand-off depends on how many tasks are handed off. Suppose tasks arrive at rate $\Lambda$ and a hand-off waits in a queue with mean delay $W(\lambda)$ at hand-off rate $\lambda = \Lambda P$, where $P$ is the probability that a task is handed off under the firm's rule. Delay costs $\omega$ per unit of time. The hand-off cost becomes $H_{\text{eff}} = h + \omega W(\lambda)$, where $h$ is the reviewer's working cost.

**Proposition 4 (do not set the rule from the observed wait).** Suppose $\lambda W(\lambda)$ is convex and $W$ is increasing, as in the M/M/1 and M/G/1 queues and, by Grassmann (1983), in the M/M/c queue. A firm that sets its rule against the average wait it observes hands off at least as often as the system optimum, which accounts for the delay each hand-off imposes on others. The wedge between the marginal and the average delay cost per hand-off is $\omega\Lambda P\,W'(\Lambda P)$, which is positive whenever waits rise with load and is what the average-wait rule ignores. The two rules coincide only where the policy frontier has a kink or at a corner.

*In words.* A rule that looks at how busy the reviewers seem now ignores the delay that a new case causes for everyone behind it, so it escalates too much.

In the calibrated example of Figure 3, an agent with the error rate of DeepSeek-V3.1 and a wrong output that costs five times a hand-off, the extra cost of the average-wait rule peaks at {{F3_PEAKS}} when the same total capacity is split across 1, 2, 5, or 10 reviewers. Pooling delays the loss to higher arrival rates but raises its peak. The loss is much smaller when a wrong output is cheaper ({{F3_F22}} at $F = \$22$) and negligible for an agent that rarely errs (at most {{F3_SON}} at the error rate of Claude Sonnet 5.5), because few tasks are then handed off by the firm's rule. The proposition therefore matters mainly for error-prone agents and costly wrong outputs. We use an approximation (Allen–Cunneen) for queues with variable arrivals. We present Proposition 4 as an application of Naor's (1969) externality, and capacity-dependent thresholds also appear in Wang and Rachev (2026), so we treat this part as supporting.

{{FIG3}}

*Link to Section 5.* In this extension the arrival rate of work at the reviewers is not a primitive. It is $\Lambda P$, where $P$ depends on the agent's self-transfer probability $\theta_h$ as well as on the firm's rule. In our data a misleading tool message changed GPT-6.1-terra's transfer rate from 0.40 to 0.74, which nearly doubles the load on the reviewers while changing the firm's threshold hardly at all (the Remark in Section 4.1). The accuracy of the tools the agent relies on therefore enters the staffing decision directly.
