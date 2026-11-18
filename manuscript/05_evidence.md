## 5. Evidence

The model needs three quantities: how strongly errors beget errors, how likely an error is to lead to a wrong output ($\theta_w$), and how likely it is to lead the agent to transfer the task itself ($\theta_h$). We estimate the first from a large observational corpus and the other two from randomized fault injection.

### 5.1 Observational evidence from software-engineering trajectories

We use a public corpus of 80,036 trajectories of the open-source agent SWE-agent, driven by three sizes of an open-weight model (Llama-3.1 8B, 70B, and 405B; Yang et al. 2024; Nebius 2024). We code an error whenever the environment rejects an action: an edit that fails a syntax check, a command that does not exist, a missing file, a malformed call, or a timeout. About 22% of steps contain an error.

Errors cluster strongly. The probability of an error is 0.66 after an error and 0.10 after a successful step. Part of that gap is task difficulty. Permuting errors within each trajectory, which keeps a trajectory's error rate but destroys dependence, leaves a gap of 0.434 against the observed 0.555. A self-exciting model of the Hawkes (1971) type, without task heterogeneity, puts all three models in the unstable range (a branching ratio between 1.48 and 2.08, Table 1). Once task difficulty varies, through a gamma-distributed baseline, the ratio falls to between 0.38 and 0.56, and likelihood-ratio tests still reject the absence of excitation. Two features argue against reading what remains as causal. Persistence within a run, such as an agent stuck in a malformed workspace, looks like contagion. And the number of errors in the first eight steps predicts the final failure with an area under the curve of only 0.55.

{{OBS}}

*Table 1. Self-exciting models of agent errors in SWE-agent trajectories, with and without a gamma-distributed baseline. The branching ratio is the expected number of further errors that one error triggers directly or through its descendants; α is the increase in intensity caused by one error and δ the rate at which it persists. The likelihood-ratio statistic tests excitation given heterogeneity (two degrees of freedom). Bootstrap intervals use 15 resamples, warm-started at the estimate, and may understate uncertainty.*

Most of the clustering that practitioners call a cascade is therefore differences between tasks. The observational data cannot separate contagion from persistence inside a run, which is why we randomize.

### 5.2 Randomized fault injection

*Design.* We inserted errors at a random point of each run, so that a comparison of injected and control runs identifies the causal effect of an error. In the *transient* arm the agent's $j$-th tool call, with $j$ drawn uniformly from $\{1, 2, 3\}$, is not executed and returns a message that the service is temporarily unavailable. In the *misleading* arm the call returns a message of the form "<argument> '<value>' not found," which mimics the environment's own error messages and asserts, falsely, that the requested object does not exist. Control runs carry a virtual injection point drawn in the same way. Injected calls never change the state of the environment. A third arm with repeated transient errors is reported in the replication package.

*Settings.* Customer service uses $\tau^2$-bench (Barres et al. 2025): 50 airline and 114 retail tasks served through tool calls on a database. Success is the final database matching the one produced by the correct actions, and the simulated customer is played by GPT-4.1-mini (7,872 runs). Code repair uses 87 real bugs from seven open-source Python projects (BugsInPy; Widyasari et al. 2020), with at most 30 turns. Success requires every failing developer test to pass and no previously passing test to fail (3,480 runs). We ran five agents: Llama-3.1-8B and 70B, DeepSeek-V3.1, and two recent commercial models, GPT-6.1-terra and Claude Sonnet 5.5, the latter two at low reasoning effort, all at temperature 0.5. The injection point was reached in 90–99% of runs, so intention-to-treat estimates are close to effects among runs in which the error occurred. The 11,352 runs cost about US\$330. Appendix B gives details, and code and run-level logs are in the replication package.

### 5.3 What injected errors do

*Transient failures are mostly harmless.* Table 2 shows that, after an unavailability message, the success of GPT-6.1-terra and Claude Sonnet 5.5 does not change in customer service, and the agents typically retry once and succeed. DeepSeek-V3.1 is the exception: its success falls by about 0.20 after either kind of error.

{{SUCCESS}}

*Table 2. Task success in the control arm and change in success after an injected error, by domain and agent. Differences are paired by task and repetition; 95% intervals come from a task-clustered bootstrap with 1,000 resamples.*

*A misleading message changes what the agent does.* In customer service it lowers success by 0.31 for GPT-6.1-terra, 0.20 for DeepSeek-V3.1, and 0.15 for Claude Sonnet 5.5. Table 3 shows that the fall for GPT-6.1-terra goes together with a near-doubling of the share of runs in which the agent transfers the case to a person.

{{ARMS}}

*Table 3. Customer service, misleading message versus control. Success and transfer rates over all runs; a transfer means that the agent called `transfer_to_human_agents`; intervals from a task-clustered bootstrap with 2,000 resamples.*

{{FIG4}}

*Two channels.* The model distinguishes a wrong output from a self-transfer, so we split the fall in success accordingly. Let $\theta$ be one minus the ratio of success in injected and control runs. We split it in two ways. In the *additive* split, $\theta_h$ is the extra failures that include a transfer call and $\theta_w$ the extra failures that do not, each divided by control success, so that $\theta = \theta_h + \theta_w$ exactly. A transfer can replace a run that would otherwise have ended wrong, so the additive $\theta_w$ can understate derailment, and for GPT-6.1-terra it is significantly negative. The *model-consistent* split assumes that error-induced transfer thins the runs that would not have transferred, and that success without a transfer is then thinned by $(1-\theta_h)(1-\theta_w)$, which is the structure of the model in Section 3. The two splits bracket the answer.

{{DECOMP_MIS}}

*Table 4. Customer service, misleading message. $\theta$ is one minus the success ratio; $\theta_h$ is the probability that an error leads to a self-transfer and $\theta_w$ that it leads to a wrong output. Task-clustered bootstrap intervals.*

Three conclusions hold under both splits (Table 4 and Figure 4). First, GPT-6.1-terra's drop is almost entirely self-transfer, with $\theta_h$ between 0.46 and 0.57, and its $\theta_w$ is not distinguishable from zero. Second, Claude Sonnet 5.5 shows genuine wrong-output derailment, with $\theta_w$ about 0.11 to 0.13, and little self-transfer. Third, for DeepSeek-V3.1 the split matters: the additive split gives a $\theta_w$ of 0.00 and the model-consistent split 0.17, with a large $\theta_h$ of about 0.27 either way. We therefore report a range for DeepSeek-V3.1. Llama-3.1-70B has low control success (0.33) and intervals that include zero, and Llama-3.1-8B (0.18) is too low to split; we do not interpret them. For transient failures (Appendix Table A1) the commercial models show neither channel, and DeepSeek-V3.1 shows both.

*What the agent does after the message.* For a misleading message we classify the next two calls as a cross-check (a different read-only tool), a retry (the same tool again), or neither. In 94 of the 97 misleading-message runs of GPT-6.1-terra in which it did neither, a transfer to a person appeared within the next two calls. For this agent a misleading message also lowers cross-checking by 0.27 (95% interval from $-0.34$ to $-0.20$) relative to the paired control run. Success is highest when the agent checks elsewhere and lowest when it neither checks nor retries (Table 5). Cross-checking is the agent's choice, so this is descriptive: an agent that accepts the false report is the one that stops looking, and the table cannot be read as the effect of checking.

{{BEHAV}}

*Table 5. Misleading arm: $\theta$ by what the agent did in the two calls after the message (95% intervals).*

*Code repair.* Effects are smaller (Table 2). A misleading message lowers the success of DeepSeek-V3.1 and Claude Sonnet 5.5 by about 0.06, with intervals that exclude zero, and leaves GPT-6.1-terra, which repairs 99% of the bugs, unchanged. The Llama agents succeed too rarely to learn from. The coding environment has no transfer tool, so $\theta_h$ is zero and the whole effect is wrong output. One reason the effects may be smaller is that the coding agent can run the tests and discover that something is wrong; we did not manipulate this.

### 5.4 Calibrating the count rule

Proposition 1 needs $\theta_w$ and not $\theta$. Table 6 compares the thresholds that follow from the undivided $\theta$ with those under each split, for a cost of a wrong output of $F = 60$ and $F = 100$, a hand-off cost $H = 40$, a step cost of 1, an error cost of 5, a completion probability of 0.06, and an error rate of 0.054 per step. These costs are illustrative.

{{NSTAR}}

*Table 6. Count at which the firm should hand off ($F = 60$ / $F = 100$). "No rule" means errors of this kind do not lower this agent's success; "no rule needed" means the wrong-output risk is indistinguishable from zero.*

The firm's rule changes materially for GPT-6.1-terra. A single misleading message does not call for a count-based hand-off on account of wrong output, because the agent hands off by itself. What that behavior calls for instead is staffing (Section 4.3): a misleading message nearly doubles the share of tasks that reach the reviewers. For Claude Sonnet 5.5 the threshold is two to four errors, a little higher than the undivided estimate suggests. For DeepSeek-V3.1 and a misleading message it ranges from no rule to two.

### 5.5 Robustness and limits

- *How the split is made matters for one agent.* The DeepSeek-V3.1 conclusion changes between the two splits. We report both and do not choose.
- *A transfer is not always an error.* GPT-6.1-terra transfers in about 40% of control runs, and some tasks may call for a transfer. We classify a run by whether it contains any transfer call and have not separated the tasks for which transfer is the correct action. Success among runs with a transfer is low (about 0.35 for GPT-6.1-terra after a misleading message), so transfers are mostly scored as failures. But the success measure, the final database state, does not say what a transfer is worth.
- *One agent and one domain for the volume result.* The near-doubling is for GPT-6.1-terra in customer service. DeepSeek-V3.1 shows a smaller increase (0.21) and Claude Sonnet 5.5 almost none. We do not claim that tool-output errors raise escalation volume in general.
- *The reason for a transfer is unknown.* The run-level logs record tool calls and not the agent's messages, so we cannot say what the agent told the customer or why it transferred.
- *Exogenous errors.* Injected errors do not arise from the agent's own confusion and may differ from natural errors. The misleading message reads like the agent's own mistake and asserts something false at the same time, and the design does not separate the two.
- *Exploratory analysis.* The split into two channels was made after we saw that most of the drop in success was transfer. An earlier version of this analysis treated the whole drop as wrong output. We report the revised analysis, the scripts, and the logs so that readers can redo it.
- *Noise.* Agents sample at temperature 0.5, model versions change, and requests to commercial models may be served by more than one provider. Intervals reflect task-level resampling only.

The threshold for stepping in depends on the probability that an error leads to a wrong output. The load on reviewers depends in addition on what the agent does on its own. A monitoring system that counts errors without asking what they lead to will both set the wrong threshold and misjudge the staffing it requires.
