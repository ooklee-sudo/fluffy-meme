## 3. Model

**Setting.** A firm sends a stream of tasks to an AI agent. A task is carried out in steps; a step is one action of the agent, such as a tool call. A step costs $k$, and each error made in it costs a further $c$. After each step the task is completed with probability $q$, independently of everything else. At the start of each step the firm may instead hand the task to a human reviewer, which ends the agent's involvement and costs $H$. The cost $H$ includes the reviewer's time to take over and finish the task.

**Errors and what they cause.** An error is a tool call that the environment rejects. Errors are of types $j = 1, \dots, J$, and the number of type-$j$ errors in a step is Poisson with mean $\mu_j$. An error of type $j$ has two possible consequences, which we keep apart because the data separate them (Section 5).

- *Derailment.* With probability $\theta_{wj}$ the error derails the task. A derailed task still runs on and may be completed, but its output is wrong, and the firm then pays $F$ to detect and repair it. The firm does not observe derailment directly.
- *Self-transfer.* With probability $\theta_{hj}$ the error leads the agent to transfer the task to a person on its own. The task ends and costs $H$, exactly as if the firm had handed it off, but the firm did not choose the timing.

Errors are independent across steps and types. We write $\tilde\theta_j = \theta_{wj} + \theta_{hj} - \theta_{wj}\theta_{hj}$ for the probability that an error has at least one consequence.

**What the firm sees and controls.** The firm sees every error and its type, but not derailment. It chooses when to hand off, as a function of the history of errors. In Section 4.2 it also chooses the quality $d \in [0,1]$ of a check on finished outputs. A derailed output is caught with probability $d$, in which case repair costs $F_d$; otherwise the wrong output reaches the customer and costs $F_u > F_d$. The expected cost of a derailed completion is therefore $F(d) = F_u - d\,(F_u - F_d)$, and the check costs $v(d)$, with $v$ convex and increasing. In Section 4.3 hand-offs queue for a limited number of reviewers.

**Timing and cost.** At the start of step $t$ the firm hands off or lets the agent act. If the agent acts, the step cost is incurred, errors arrive, the agent may transfer the task, and otherwise the task is completed with probability $q$. If it completes, the firm pays $F(d)$ times the probability that the task has been derailed. The firm minimizes expected total cost.

**Assumptions.** (A1) Errors and their types are observed. (A2) Parameters are known and constant. (A3) Completion occurs with probability $q$ whatever the error history; errors affect the correctness of the output only through derailment.

*Terms.* A *hand-off* is a transfer chosen by the firm; a *self-transfer* is a transfer chosen by the agent; *escalation* covers both.
