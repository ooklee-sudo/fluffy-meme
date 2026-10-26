---
title: "Verify the Record, Not the Report: Why Agent Completion Claims Need System-State Checks"
author: "Ook Lee"
---

*Ook Lee, Department of Information System, Hanyang University, Seoul, Korea; ooklee@hanyang.ac.kr*

**Abstract**—Language-model agents now close tickets, change orders, and cancel reservations, and they report their own results in fluent prose. Recent studies suggest that such reports can be wrong without anyone noticing. I tested what actually reduces the gap between what an agent says it did and what the system of record shows. I ran about 1,650 episodes of a public customer-service benchmark with two agent models, injected connector faults into 30 percent of write calls, and compared a raw error page with a typed error envelope. False success was common even without injected faults (21 to 44 percent of GPT-4.1-mini episodes). Injected faults barely changed it, because agents usually told the customer when a write had failed. Typed envelopes did not help measurably. A check of the claim against the database state is the control that matters.

**Keywords**—LLM agents, reliability, observability, software operations, verification

# The report is not the record

An agent calls a tool, the tool fails, and a few turns later the agent tells the customer that all is well. If the dashboard only records that the request returned a response, nobody finds out until the customer calls back. Engineers call this a silent failure, and language-model agents add a twist. Tool-using agents interleave reasoning and tool calls [6], and when the tool output does not support what the model wants to say, the model can produce a story of a success that never happened, the agent-side form of what the literature calls hallucination [7].

I wanted to know which controls reduce this risk. A common recommendation is to clean up the tool interface so that errors arrive in a typed, machine-readable envelope instead of as raw text that the model might paraphrase. Another is to ask a second language model to judge whether the first one's report is credible. A third is to compare the agent's claim with the state of the system. These three are cheap to describe and expensive to adopt in a real service catalog, so evidence on which of them works is worth having.

This article reports a controlled experiment on a public benchmark and draws practical conclusions for teams that put agents into workflows with write access. I make no claim about any particular vendor's agent, and the experiment tests one failure type under one injection scheme. The results, however, are clear enough to change what I would ask an integration team to build first.

# What earlier studies say

Three recent studies describe the problem from different angles. All three are preprints or workshop papers, and none has been through full journal review, so I treat them as evidence to be tested rather than as settled facts.

Wu documented eight weeks of operation of a continuously running assistant runtime [1]. The study records 22 incidents and a single meta-pattern, in which an error signal never reaches a human in actionable form, that appeared at least 28 times. About 70 percent of these failures were found by a person reading the output; unit tests, of which the system had more than 4,000, caught almost none of this class. Wu's term for the worst variant is "fail-plausible": the model converts an error into a calm narrative.

Advani analyzed 9,876 trajectories from a tool-use benchmark and an app-use benchmark [2]. In customer-service domains where the agent acts alone, 45 to 48 percent of the failures were false successes, meaning the agent said it had finished although the final state did not match the goal. The rate was only 3 percent in a domain where the user must also act, and it reached 75.8 percent among self-assessing agents on a coding benchmark. No language-model judge exceeded an AUROC of 0.65 on the customer-service trajectories, whereas simple detectors on the closing message did better.

Zhu and colleagues show that deployed agents degrade over time even with frozen weights, and that in their compression scenario the memory policy mattered more than the choice of model [3]. This is a reminder that reliability is a property of the whole harness, not of the model alone.

Two observations follow. False success is a documented, measurable phenomenon. And the proposed remedies, typed interfaces and judge models, have mostly been argued for rather than tested head-to-head. The experiment below is a small attempt to test two of them.

# A test on a public benchmark

I used τ-bench [4] and its successor τ²-bench [5], which place a tool-using agent in a simulated customer-service conversation. Each task has a database, a policy, and a simulated user, and the benchmark scores a run by comparing the final database state with the expected one. That scoring gives me what real deployments rarely have, a ground truth about what changed.

I ran the retail domain (114 tasks) and the airline domain (50 tasks). The agent was GPT-4.1-mini in both domains and Llama-3.3-70B in retail; the simulated user was GPT-4.1-mini. Each task ran twice under each of three conditions with identical tasks and seeds:

- **Baseline.** The benchmark as released.
- **Raw faults.** For each write call (cancel, modify, return, exchange), a deterministic pseudo-random draw, keyed to the call identifier, failed the call with probability 0.3. A failed call changed nothing in the database. The agent received a generic HTML "400 Bad Request" page as an ordinary tool result with no error flag, which imitates a connector that leaks a web error into the prompt.
- **Typed faults.** The same failures, with the same probability, returned as a typed envelope, {ok: false, code: http_400, retryable: true, provenance: connector name}, flagged as an error.

I kept a ledger of every write call (attempted, failed, applied). The benchmark's evaluator replays the agent's calls to rebuild the final state, so I made the fault decision depend on the call identifier; otherwise the replay would have applied writes that had failed in the live run.

The outcome measures are the following. *Success* means the final database matches the expected one. A *completion claim* means the agent's closing messages tell the customer that a requested change has been done, as judged by a language-model classifier whose labels agree with a simple pattern-matching detector in 88 percent of episodes. *False success* means a completion claim together with a database mismatch. For the failed-write analysis I coded what the agent told the customer about each write that failed and was never repeated successfully: it claimed the action was done (a leak), reported the failure (disclosed), or said nothing (silent). I also read all 18 typed-condition episodes with a failed write and a flagged claim, and the language-model coder over-flags leaks, so its rates are upper bounds. Differences are paired by task, averaged over seeds, and bootstrapped over tasks. The experiment comprises 1,645 episodes with a database outcome and cost about 21 US dollars in API charges. The code and the per-episode data are available from the author.

# Findings

## False success is common without any injected fault

Table 1 shows the baseline. In retail, 21 percent of GPT-4.1-mini episodes ended with a completion claim and a wrong database, which is 54 percent of its failures. In the airline domain the figures are 44 percent of episodes and 77 percent of failures. The weaker Llama agent succeeded in only 10 percent of retail tasks and rarely claimed completion, so it offers little room for comparison and I do not interpret its numbers beyond that.

*Table 1. Task outcomes by condition (episodes; share of episodes).*

| Agent, domain | Condition | n | Success | Claims completion | False success |
|---|---|---|---|---|---|
| GPT-4.1-mini, retail | Baseline | 228 | .61 | .69 | .21 |
| | Raw faults | 227 | .55 | .63 | .19 |
| | Typed faults | 227 | .56 | .67 | .23 |
| GPT-4.1-mini, airline | Baseline | 98 | .43 | .61 | .44 |
| | Raw faults | 97 | .39 | .57 | .43 |
| | Typed faults | 97 | .45 | .61 | .41 |
| Llama-3.3-70B, retail | Baseline | 224 | .10 | .03 | .03 |
| | Raw faults | 222 | .11 | .03 | .02 |
| | Typed faults | 225 | .12 | .05 | .03 |

## Injected faults barely moved false success

I expected raw error pages to raise false success and typed envelopes to bring it back down. Neither happened. Compared with baseline, raw faults changed GPT-4.1-mini's false-success rate by −2.2 percentage points in retail (95% interval −8.8 to 4.4) and −1.0 in airline (−12 to 10). Typed faults compared with raw faults changed it by +3.5 points in retail (−3.1 to 9.7) and 0.0 in airline (−12 to 12). The intervals are wide enough to hide an effect of five to ten points, so I cannot rule out a modest benefit. But the point estimates do not lean toward the predicted one, and in retail, success rates fell by five to six points under both fault conditions, as one would expect from losing writes (in the airline domain the changes were mixed).

## Agents mostly said so when a write failed

The more informative result is in the transcripts. In 152 episodes a write failed and was never repeated successfully. In 70 of the 75 raw-condition episodes and 70 of the 77 typed-condition episodes, the assistant told the customer that something had not worked or offered to transfer them to a human (Table 2). The language-model coder labeled 3 raw and 6 typed episodes as leaks, that is, the assistant said the failed action was done; my manual reading of the typed episodes suggests the true count is closer to 2 of 77. Modern models in this experiment recognized a raw HTML error page as an error. The typed envelope did not improve on that, because there was little left to improve.

*Table 2. What the assistant told the customer about a write that failed and was not repeated successfully.*

| Condition | Episodes | Reported the failure | Claimed it was done (coder; upper bound) | Silent |
|---|---|---|---|---|
| Raw error page | 75 | 70 | 3 | 2 |
| Typed envelope | 77 | 70 | 6 | 1 |

Why, then, does the earlier figure look so alarming? In the typed condition, 18 episodes combined a failed write with a completion claim. In eight of them the agent reported the successful actions as done and the failed one as failed. In five the claim concerned an action that had succeeded while the failed one was abandoned or later retried. In two the agent misattributed the cause, for example by saying that a reservation of a given fare class cannot be modified. One executed the right action with the wrong content, a street number off by two. In only two did the agent say something was done with no successful write behind it. A count of "claims completion" after a failure therefore overstates the leak, and a team that monitors such a count would chase mostly harmless messages.

## Where false success comes from

If the injected faults explain little, what does? Of 187 false successes in the two fault conditions, 29 (16 percent) occurred in episodes with an unrecovered failed write. The rest arose from the agent's own mistakes: a partial completion reported as complete, a wrong argument, a policy violation, a misread request. These errors are untouched by the format of the error message, because no tool reported an error at all. They are exactly the cases in which a human reading the transcript would also need to check the system.

## What can detect them

Among the 652 episodes with a completion claim, 284 were false successes. Table 3 compares two monitors that need no ground truth with the claim-versus-state check that I have only because the benchmark supplies the expected database. The ledger rule (flag a claim when any write failed and was never repeated) is precise but catches only one in ten. A language-model judge that reads the transcript, including the raw tool outputs, finds more but still misses about three of four, and a third of its alarms are wrong; this agrees with Advani's finding that judges struggle with this failure mode [2]. A comparison of the claim with the database state finds all of them by construction.

*Table 3. Monitors for false success among 652 episodes with a completion claim (284 false successes).*

| Monitor | Flags correct | Flags wrong | Missed | Precision | Recall |
|---|---|---|---|---|---|
| Ledger rule (claim after an unrepeated failed write) | 29 | 6 | 255 | .83 | .10 |
| Language-model judge reading the transcript | 76 | 42 | 208 | .64 | .27 |
| Claim versus database state | 284 | 0 | 0 | 1.0 | 1.0 |

# What to build first

The results favor a short list of controls, ordered by how much of the problem they address.

**1. Gate completion on system state.** Treat words such as "done", "refunded", "booked", and "cancelled" as privileged outputs. The agent may say them only after a read-after-write check shows that the system of record contains the change. The cost is one read per claimed mutation. This is the only control in my experiment that finds the false successes that do not involve an error.

**2. Make the claim machine-readable.** Ask the agent to end each task with a structured summary (action, object identifier, expected new state) alongside the prose. A verifier can then check each item against the database without parsing free text, and a mismatch can block the message or route the conversation to a person.

**3. Log the ledger, but do not rely on it.** Recording which write calls were attempted, failed, and applied is cheap and helps in post-mortems, and the ledger rule flagged correctly 83 percent of the time. It missed nine tenths of the false successes, so it is a complement to the state check, not a substitute.

**4. Audit with samples, not with a second model.** A judge reading transcripts costs more and, here, caught about a quarter of the problem. A better use of review capacity is a small human or scripted sample of closed tickets compared with the record, which also measures the false-success rate over time.

**5. Keep typed errors as hygiene.** I found no measurable benefit from typed envelopes in this experiment, so I would not present them to a steering committee as a fix for false success. They remain good engineering for retries, alerting, and observability, which this experiment does not test.

# Limits

The experiment covers two customer-service domains of one benchmark, one injected fault type (HTTP 400 on write calls, 30 percent of calls), a simulated user, and two or three agent configurations. Other models may react differently to a leaked error page (Wu reports fabricated narratives in a production runtime [1]), and other fault types, such as partial successes or timeouts that apply the change anyway, may produce different behavior. The subgroup of failed-write episodes is small (about 75 per condition), the leak coding was validated on 18 transcripts only, and the claim detector is a language model. I tested completion gating as a monitor, not as an intervention that blocks messages, so the effect of the gate on task success is untested. The benchmark's ground truth comes from a replayed script, which is stricter than many real tasks permit.

These limits cut both ways. They mean that I would not conclude that typed envelopes are useless, only that their value for this particular problem was not visible here. They also mean that the main message does not depend on the fault experiment at all: even without injected faults, one in five (retail) to two in five (airline) episodes of a capable agent ended with a claim the database did not support.

# Conclusion

Teams that deploy agents with write access should assume that some of the agent's reports are wrong in ways neither the agent nor a second model will reliably flag. The report is an assertion, and the record is the evidence. Build the check that compares the two, measure the gap on a sample, and treat error formatting and judge models as supporting tools rather than as the control.

# Acknowledgments

I used Claude (Anthropic), accessed through the Claude Code assistant, to write the experiment harness and analysis code, to run the experiments, and to draft and edit the text of this article. I reviewed the outputs and take responsibility for the content. [AUTHOR TO CONFIRM that this matches your actual use and what you checked.]

# References

[1] W. Wu, "When errors become narratives: A longitudinal taxonomy of silent failures in a production LLM agent runtime," arXiv:2606.14589, Jun. 2026 (preprint).

[2] L. Advani, "From confident closing to silent failure: Characterizing false success in LLM agents," in *Workshop on Failure Modes in Agentic AI (FAGEN), ICML*, 2026; arXiv:2606.09863.

[3] J. Zhu et al., "Your agents are aging too: Agent lifespan engineering for deployed systems," arXiv:2605.26302, May 2026 (preprint).

[4] S. Yao, N. Shinn, P. Razavi, and K. Narasimhan, "τ-bench: A benchmark for tool-agent-user interaction in real-world domains," arXiv:2406.12045, Jun. 2024.

[5] V. Barres, H. Dong, S. Ray, X. Si, and K. Narasimhan, "τ²-bench: Evaluating conversational agents in a dual-control environment," arXiv:2506.07982, Jun. 2025.

[6] S. Yao et al., "ReAct: Synergizing reasoning and acting in language models," in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2023; arXiv:2210.03629.

[7] Z. Ji et al., "Survey of hallucination in natural language generation," *ACM Comput. Surv.*, vol. 55, no. 12, 2023, doi: 10.1145/3571730.
