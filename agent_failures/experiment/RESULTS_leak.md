# Why do agents "claim completion" after a failed write? Transcript analysis

## What the earlier number measured
In `RESULTS.md`, 30% of GPT-4.1-mini episodes with an unrecovered failed write ended with a completion claim. That figure counts any completion claim in the final messages, including claims about other actions that did succeed. It is not a measure of claiming that the failed action was done.

## Manual reading (all 18 typed-condition episodes with an unrecovered failed write and a flagged claim)
File: `results/typed_unrecovered_claim_transcripts.txt`. My coding:

| Pattern | Episodes | Examples |
|---|---|---|
| Partial report: some actions done and confirmed by a successful write, the failed one disclosed (often with a transfer to a human) | 8 | retail 30/1, 78/1, 97/1, 102/1, 78/2, 104/2, 101/2; airline 42/1 |
| Claim is about an action that succeeded; the failed action was abandoned by the customer or later retried successfully | 5 | retail 72/1, 36/2, 100/2; Llama retail 57/2, 86/2 |
| The failure was disclosed but its cause was explained wrongly (e.g., "basic economy cannot be modified", "item not available") | 2 | airline 34/1; retail 76/1 |
| Claim true, but the wrong content was executed (wrong street number) | 1 | Llama retail 42/1 |
| **Completion claim with no successful write behind it** | **2** | airline 37/2 (cancellation reported as processed after the only cancel call failed); Llama retail 12/2 (return reported as processed; no write applied) |

So in 2 of 18 episodes (11%) the assistant told the customer that something was done although the write had failed. In 8 it reported the failure honestly, and in the others the claim was about other work.

## Systematic coding of all failed-write episodes (LLM coder)
`leak_analysis.py` classifies, for every raw or typed episode with an unrecovered failed write, what the assistant told the customer about the failed action: leak, disclosed, or silent.

| Condition | Episodes | Leak | Disclosed | Silent |
|---|---|---|---|---|
| raw (HTML 400 page, no error flag) | 75 | 3 (4.0%; 95% interval 0 to 9.3%) | 70 | 2 |
| typed (envelope with ok = false) | 77 | 6 (7.8%; 2.6 to 14.3%) | 70 | 1 |

The coder over-flags leaks: on the 18 typed episodes it labels 6 as leaks against my 2, so these rates are upper bounds (my manual reading of typed episodes gives about 3%).

## Reading
- With these models, a leaked HTML 400 page did not produce fabricated success: the assistants described it as a failure in 93% of episodes (70 of 75). The typed envelope did not improve on that (91%). The data give no support for the claim that typed envelopes remove fabricated completions, because there is little fabrication to remove in this setting.
- Task-level false success (database state wrong while the assistant claims completion) is common at baseline (21% of retail and 44% of airline episodes for GPT-4.1-mini) and has other causes: partial completion, wrong parameters, policy errors, misunderstood requests. A claim-versus-state check against the database catches these, a typed envelope does not.
- Limits: two customer-service domains; one injected fault type (HTTP 400 on writes, 30% rate); only two or three agent configurations; small subgroups (about 75 failed-write episodes per condition); LLM coding validated on 18 episodes only.
