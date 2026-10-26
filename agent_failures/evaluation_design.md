# Design: a real-case test of "claimed completion versus system state"

**Goal.** Replace the simulated desk (Table 1) with measurements on a public benchmark that has a ground-truth system state and real LLM agents.

**Benchmark.** tau-bench / tau2-bench (Sierra Research, MIT license, https://github.com/sierra-research/tau2-bench). Airline and retail domains have tools that modify a database, a simulated user, and a reward based on the final database state. Task sets are frozen (50 tasks per domain in text-v1).

**Measures.**
1. *False-success rate* = share of failed tasks (reward 0) in which the agent's last message claims the task is done. Advani's definition (arXiv:2606.09863) is the benchmark here; reuse its regex or classifier so numbers are comparable.
2. *Claim-state gap* = claimed completions minus completions confirmed by the database state, per 100 tasks.
3. *Fault leakage.* After injecting a tool fault, share of runs where the agent reports success.

**Conditions** (same tasks, same agent model, 3 seeds):
- A. Baseline harness (as released).
- B. Fault injection, raw: a fixed share (10%, 30%) of write-tool calls return an HTML 400 page or a stack trace as the tool output.
- C. Fault injection, typed: the same faults returned as {ok: false, code, retryable, provenance}.
- D. Gated completion: the harness refuses to let the agent emit "done/refunded/booked" unless a read-after-write check on the database passes.

**Agents.** Two or three inexpensive models available through the OpenRouter key (one small open-weight model, one mid-size commercial model) so the result does not hinge on one vendor.

**Hypotheses.** H1: B raises false success relative to A. H2: C removes most of the increase in B. H3: D lowers the claim-state gap to near zero without lowering true-success rate by more than a few points. These are testable and could fail.

**Analysis.** Paired comparison by task and seed; report counts, rates, and 95% bootstrap intervals; report true-success rate in every condition so a safer harness is not just a less capable one.

**Cost and effort (estimate, not measured).** 100 tasks x 4 conditions x 3 seeds x 2 models = 2,400 episodes; at roughly 20 to 40 model calls per episode (agent plus user simulator) this is on the order of 50,000 to 100,000 calls; with small models, a budget of tens of dollars is likely, but run a 20-task pilot first and measure. About 2 to 4 days of work, mostly harness changes.

**Threats.** The simulated user is itself an LLM; fault injection is synthetic (but applied to a real agent and real database); two domains are customer service, not IT operations; results will not generalize to every agent. State this in the paper.

**Why this answers the editor.** It supplies an implementation (harness changes released as code), an assessment on real agent runs with ground-truth outcomes, and independent public data, instead of a toy language model.
