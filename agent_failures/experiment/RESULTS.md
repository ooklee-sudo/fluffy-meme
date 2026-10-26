# tau-bench fault-injection experiment: results

Run 26 Oct 2026. Harness: `run_faults.py`; analysis: `analyze_faults.py`; per-episode data: `runs/*.jsonl`, `results/episodes.csv`. Agents: GPT-4.1-mini (retail 114 tasks, airline 50 tasks) and Llama-3.3-70B (retail 114 tasks), user simulator GPT-4.1-mini, 2 seeds, 3 conditions (baseline; raw = HTML 400 page returned as a normal tool result; typed = {ok:false, code, retryable, provenance}), 30% of write calls faulted (write not applied). 1,645 episodes with a database outcome. Total API cost about $21.

## Main results
| Model, domain | Condition | n | Success | Claims completion | False success (claim and DB mismatch) | Share of failures that were false success |
|---|---|---|---|---|---|---|
| GPT-4.1-mini, retail | baseline | 228 | .610 | .693 | .211 | .54 |
| | raw | 227 | .551 | .626 | .189 | .42 |
| | typed | 227 | .559 | .670 | .225 | .51 |
| GPT-4.1-mini, airline | baseline | 98 | .429 | .612 | .439 | .77 |
| | raw | 97 | .392 | .567 | .433 | .71 |
| | typed | 97 | .454 | .608 | .412 | .76 |
| Llama-3.3-70B, retail | baseline | 224 | .103 | .031 | .027 | .03 |
| | raw | 222 | .108 | .032 | .023 | .03 |
| | typed | 225 | .120 | .053 | .027 | .03 |

## What the data show
1. **False success is common without any injected fault**: 21% of GPT-4.1-mini retail episodes and 44% of airline episodes ended with a completion claim although the final database state was wrong (54% and 77% of failures).
2. **Hypotheses H1 and H2 are not supported.** Raw faults did not raise false success (paired task-level differences vs baseline: retail -2.2 pp [-8.8, 4.4]; airline -1.0 pp [-12, 10]; Llama retail -0.4 pp [-2.2, 1.3]), and typed envelopes did not lower it relative to raw (typed minus raw: +3.5 pp [-3.1, 9.7]; airline 0.0 [-12, 12]; Llama +0.4 [-1.8, 2.6]). The intervals are wide enough to hide effects of about 5 to 10 pp, but the point estimates do not point toward the predicted benefit.
2b. **Typed envelopes did not stop completion claims after a failed write.** Among GPT-4.1-mini episodes with an unrecovered faulted write, the share that claimed completion was 30% under raw and 30% under typed in retail (n = 37 each), and 31% versus 27% in airline (n = 13 and 11). This subgroup is post-treatment and small.
3. **Injected faults explain little of the problem.** Of 187 false successes in the fault conditions, 29 (16%) came from episodes with an unrecovered faulted write.
4. **Monitors.** Among 652 episodes with a completion claim, 284 were false successes. A ledger rule (claim and an unrecovered failed write) had precision .83 but recall .10; an LLM judge reading the transcript had precision .64 and recall .27. A claim-versus-state check against the database finds all of them by construction.

## Limits
Two domains of customer service, three agent configurations, synthetic faults, an LLM user simulator, an LLM claim detector (agrees with a regex detector in 88% of episodes), a floor effect for Llama (10% success, almost no completion claims), and confidence intervals computed over tasks (seeds averaged). H3 (completion gated on state) was evaluated only as a monitor, not as an intervention that blocks claims.
