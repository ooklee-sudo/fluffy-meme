"""Fill the Section 5 template with generated tables -> msom_draft_evidence.md."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from section5_tables import TABLES
ROOT = Path(__file__).resolve().parent.parent

TEMPLATE = r'''# M&SOM 초안: 5절 Evidence

> 상태: 초안. 표는 `sim/section5_tables.py`가 분석 결과 JSON에서 생성한다 (`sim/build_evidence.py`로 이 파일 전체를 다시 만든다). 대괄호는 확인이 필요한 항목. 모든 분석은 사전등록되지 않은 탐색 분석이다.
> 숫자 기준: 인계율과 θ는 모두 **전체 런 기준**의 추정기(원고 Table 4와 같은 방식)이다. 앞선 메모의 0.39는 주입 지점에 도달한 쌍만 쓴 값이고 0.40이 이 절의 값이다 (0.3963).

---

## 5. Evidence

The model needs three quantities: how strongly errors beget errors, how likely an error is to lead to a wrong output (θ_w), and how likely it is to lead the agent to transfer the task itself (θ_h). We estimate the first from a large observational corpus and the other two from randomized fault injection.

### 5.1 Observational evidence from software-engineering trajectories

We use a public corpus of 80,036 trajectories of the open-source agent SWE-agent, driven by three sizes of an open-weight model (Llama-3.1 8B, 70B, 405B). We code an error whenever the environment rejects an action (an edit that fails a syntax check, a command that does not exist, a missing file, a malformed call, or a timeout); about 22% of steps contain one.

Errors cluster strongly. The probability of an error is 0.66 after an error and 0.10 after a successful step. Part of that gap is task difficulty: permuting errors within each trajectory, which keeps a trajectory's error rate but destroys dependence, leaves a gap of 0.434 against the observed 0.555. A self-exciting model without task heterogeneity puts all three models in the unstable range (branching ratio 1.48 to 2.08); once task difficulty varies (gamma-distributed baseline) the ratio falls to 0.38–0.56, and the likelihood-ratio tests still reject no excitation. Two features argue against reading the remainder as causal: persistence within a run (an agent stuck in a malformed workspace) looks like contagion, and the number of errors in the first eight steps predicts final failure with an area under the curve of only 0.55. [Values from the submitted manuscript, Section 5.1 and Table 1; bootstrap intervals use 15 resamples and may understate uncertainty.]

*What this does for the model.* Most of the clustering that practitioners call a cascade is differences between tasks. The observational data cannot separate contagion from persistence inside a run, which is why we randomize.

### 5.2 Randomized fault injection

*Design.* We inserted errors at a random point of each run, so that the comparison between injected and control runs identifies the causal effect of an error. In the *transient* arm the agent's j-th tool call (j drawn uniformly from 1, 2, 3) is not executed and returns a message that the service is temporarily unavailable. In the *misleading* arm the call returns a message of the form "<argument> '<value>' not found", which mimics the environment's own error messages and asserts, falsely, that the requested object does not exist. Control runs carry a virtual injection point drawn in the same way. Injected calls never change the state of the environment. A repeated-transient arm is reported in the appendix.

*Settings.* Customer service uses τ²-bench: 50 airline and 114 retail tasks, served through tool calls on a database; success is the final database matching the one produced by the correct actions, and the simulated customer is played by GPT-4.1-mini (7,872 runs). Code repair uses 87 real bugs from seven open-source Python projects (BugsInPy), with at most 30 turns; success requires every failing developer test to pass and no previously passing test to fail (3,480 runs). We ran five agents: Llama-3.1-8B and 70B, DeepSeek-V3.1, and two recent commercial models, GPT-6.1-terra and Claude Sonnet 5.5 (low reasoning effort), at temperature 0.5. The injection point was reached in 90–99% of runs, so intention-to-treat estimates are close to effects among runs where the error occurred. The 11,352 runs cost about US$330. Code, run-level logs, and analysis scripts are in the replication package.

### 5.3 What injected errors do

*Transient failures are mostly harmless.* After an unavailability message, GPT-6.1-terra's and Sonnet 5.5's success rates do not change, and the agents typically retry once with success. DeepSeek-V3.1 is the exception: its success falls by about 0.20 after either kind of error. [Manuscript Table 2.]

*A misleading message changes what the agent does.* Table 5.1 shows the effect on customer service.

{{ARMS}}

*Table 5.1. Customer service, misleading message versus control. Success and transfer rates over all runs; transfer = the agent called `transfer_to_human_agents`; intervals from a task-clustered bootstrap with 2,000 resamples.*

The fall in success for GPT-6.1-terra (0.77 to 0.46) goes together with a near-doubling of the share of runs in which the agent transfers the case to a human (0.40 to 0.74). DeepSeek-V3.1 shows the same pattern more weakly; Sonnet 5.5 does not transfer more.

*Two channels.* The model distinguishes a wrong output from a self-transfer, so we split the fall in success accordingly. Let θ be one minus the ratio of success in injected and control runs, as in the submitted manuscript. We split it in two ways. In the **additive** split, θ_h is the extra failures that include a transfer call and θ_w the extra failures that do not, each divided by control success, so that θ = θ_h + θ_w exactly. Because a transfer can replace a run that would otherwise have ended wrong, the additive θ_w can understate derailment, and for GPT-6.1-terra it is significantly negative. The **model-consistent** split assumes that error-induced transfer thins the runs that would not have transferred and that success without transfer is then thinned by (1 − θ_h)(1 − θ_w), which is the structure of the model in Section 3. The two splits bracket the answer.

{{DECOMP_MIS}}

*Table 5.2. Customer service, misleading message. θ is one minus the success ratio; θ_h is the probability that an error leads to a self-transfer, θ_w that it leads to a wrong output. Task-clustered bootstrap intervals.*

Three conclusions hold under both splits. First, **GPT-6.1-terra's drop is almost entirely self-transfer** (θ_h between 0.46 and 0.57) and its θ_w is not distinguishable from zero. Second, **Claude Sonnet 5.5 shows genuine wrong-output derailment** (θ_w about 0.11 to 0.13) and little self-transfer. Third, for **DeepSeek-V3.1 the split matters**: the additive split gives θ_w of 0.00, the model-consistent split 0.17, with a large θ_h (about 0.27) either way. We therefore report a range for DeepSeek. Llama-3.1-70B has low control success (0.33) and its intervals include zero, and Llama-3.1-8B (0.18) is too low to split; we do not interpret them.

*Transient failures* (appendix Table A.1) are largely harmless for the commercial models and carry both channels for DeepSeek-V3.1.

*What the agent does after the message (descriptive).* For a misleading message we classify the next two calls as a cross-check (a different read-only tool), a retry (the same tool again), or neither. In 94 of the 97 misleading-message runs of GPT-6.1-terra in which it did neither, the next call was a transfer. For this agent a misleading message also lowers cross-checking by 0.27 [−0.34, −0.20] relative to the paired control run. Success is highest when the agent checks elsewhere and lowest when it neither checks nor retries (Table 5.3).

{{BEHAV}}

*Table 5.3. Misleading arm: θ by what the agent did in the two calls after the message. Cross-checking is the agent's choice, so this is descriptive. Reading it causally is not safe, since an agent that accepts the false report is the one that stops looking.*

*Code repair.* Effects are smaller: a misleading message lowers DeepSeek-V3.1's and Sonnet 5.5's success by about 0.06 (95% intervals exclude zero), leaves GPT-6.1-terra (which repairs 99% of the bugs) unchanged, and the Llama agents succeed too rarely to learn from [manuscript Tables 2 and 4]. The coding environment has no transfer tool, so θ_h is zero and the whole effect is wrong output. One reason the effects may be smaller is that the coding agent can run the tests and discover that something is wrong; we did not manipulate this.

### 5.4 Calibrating the count rule

Proposition 1 needs θ_w, not θ. Table 5.4 compares the thresholds recommended by the submitted manuscript (which used the total θ) with the thresholds under each split, for a cost of a wrong output of F = 60 and F = 100, a hand-off cost H = 40, a step cost of 1, an error cost of 5, completion probability 0.06 and error rate 0.054 per step (illustrative costs).

{{NSTAR}}

*Table 5.4. Count at which the firm should hand off (F = 60 / F = 100); "no rule" = errors of this kind do not lower the success of this agent, "no rule needed" = the wrong-output risk is indistinguishable from zero.*

The firm-side rule changes materially for GPT-6.1-terra: a single misleading message does not call for a count-based hand-off on account of wrong output, because the agent hands off by itself. What that agent's behavior calls for instead is staffing (Section 4.3): a misleading message nearly doubles the share of tasks that reach the reviewers. For Sonnet 5.5 the threshold is a little higher than before (two to four errors). For DeepSeek-V3.1 it ranges from no rule to two.

### 5.5 Robustness and limits

- **How the split is made matters for one agent.** The DeepSeek-V3.1 conclusion changes between the two splits. We report both and do not choose.
- **A transfer is not always an error.** GPT-6.1-terra transfers in about 40% of control runs, and some tasks may call for a transfer. We classify a run by whether it contains any transfer call, and we have not separated tasks for which transfer is the correct action. Success among runs with a transfer is low (about 0.35 for GPT-6.1-terra after a misleading message), so transfers are mostly scored as failures, but the success metric (final database state) is not a measure of what the transfer is worth.
- **One agent, one domain for the volume result.** The near-doubling is for GPT-6.1-terra in customer service. DeepSeek-V3.1 shows a smaller increase (+0.21) and Sonnet 5.5 none. We do not claim that tool-output errors raise escalation volume in general.
- **The reason for a transfer is unknown.** The run-level logs record tool calls and not the agent's messages, so we cannot say what the agent told the customer or why it transferred.
- **Exogenous errors.** Injected errors do not arise from the agent's own confusion and may differ from natural errors; the misleading message reads like the agent's own mistake and asserts something false at the same time, and the design does not separate the two.
- **Exploratory.** The decomposition into two channels was made after seeing that most of the drop in success was transfer; our first interpretation, in the submitted manuscript, treated the whole drop as wrong output. We report the revised analysis, the scripts, and the logs so that readers can redo it.
- **Noise.** Agents sample at temperature 0.5, model versions change, and commercial requests may be served by more than one provider; intervals reflect task-level resampling only.

*Why this matters for design.* The threshold for stepping in depends on the probability that an error leads to a wrong output; the load on reviewers depends in addition on what the agent does on its own. A monitoring system that counts errors without asking what they lead to will both set the wrong threshold and misjudge the staffing it requires.

---

## 부록 표

{{DECOMP_TRA}}

*Table A.1. Customer service, transient failure. Same definitions as Table 5.2.*

## 재현

```bash
python3 -I sim/table4_two_component.py      # Table 5.2, A.1, 5.4 (writes sim/table4_two_component.json)
python3 -I sim/free_crosscheck_analysis.py replication/replication_agent_handoff/inject/results sim/free_crosscheck_results.json   # Table 5.3
python3 -I sim/free_transfer_decomposition.py replication/replication_agent_handoff/inject/results sim/free_transfer_results.json
python3 -I sim/build_evidence.py            # regenerates this file
```
'''

out = TEMPLATE
for k, v in TABLES.items(): out = out.replace("{{" + k + "}}", v)
assert "{{" not in out
(ROOT / "msom_draft_evidence.md").write_text(out)
print("wrote msom_draft_evidence.md,", len(out), "chars")
