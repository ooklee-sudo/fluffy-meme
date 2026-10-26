---
title: "When Agent Failures Look Like Success: Three Controls for Enterprise IT"
author: "Ook Lee"
---

*Department of Information System, Hanyang University, Seoul, Korea. ooklee@hanyang.ac.kr*

**Abstract.** Language-model agents now sit in enterprise workflows where a ticket can look closed while nothing changed in the system of record. Three recent studies, one preprint on a production runtime, one workshop paper on benchmark trajectories, and one preprint on long-lived agents, point to the same operational lesson: failures that turn into fluent prose are hard for people and for other language models to catch. This article draws three controls for integration teams from that evidence: type tool faults, gate completion on system state, and monitor the gap between claims and state. A small simulation illustrates the first control and is not offered as evidence. The article lists what the sources do and do not show.

**Keywords:** IT operations, large language models, agents, reliability, observability

# The problem

An agent calls a tool. The tool returns an error page. A wrapper passes the page into the next prompt. The agent writes a calm summary of work that did not happen, and the dashboard shows HTTP 200. Wu calls this pattern "fail-plausible" [1]: the system does not merely fail to report an error; the language model turns the error into plausible narrative.

Three sources describe the pattern from different angles.

- **A production runtime.** Over eight weeks, Wu documented 22 incidents in one continuously running assistant runtime and found a failure whose error signal never reached a human in actionable form at least 28 times. About 70 percent were found by a person reading the output; unit tests caught almost none of this failure class, although the system ran 4,286 of them [1].
- **Benchmark trajectories.** Advani analyzed 9,876 tau2-bench trajectories from eight model families. False success, where the agent claims completion although the final state does not match, was 45 to 48 percent of failures in the airline and retail domains, 3 percent in the dual-control telecom domain, and 75.8 percent of failures among self-assessing agents on AppWorld. No language-model judge exceeded an AUROC of 0.65 on tau2-bench, while simple detectors on the closing message reached 0.83 [2].
- **Long-lived agents.** Zhu and colleagues show that deployed agents degrade after day one even with frozen weights. In their compression scenario, the memory policy affected the half-life of capability more than the choice of model [3].

An industry measurement fits the same picture: Datadog reported that about 5 percent of LLM requests failed in production and that nearly 60 percent of those failures came from capacity limits [4]. These are the failures that transport-level monitoring can see. A silent false success does not raise that counter.

# Three controls

The evidence supports operational controls that integration teams own, not a purchasing decision.

**1. Type tool faults.** Every connector returns a small envelope, for example {ok, code, retryable, provenance}, and raw error pages and stack traces never re-enter the prompt. The design principle follows Wu's finding that silent fabrications start from polluted context [1].

**2. Gate completion on system state.** Words such as done, verified, refunded, and booked are not allowed in a final message until the system of record confirms the change. This addresses the false-success pattern that Advani measured [2].

**3. Monitor the gap between claims and state.** Alert when a completion claim has no matching mutation. Advani's results suggest not relying on another language model as the first monitor, because judges did not exceed an AUROC of 0.65 while cheap detectors on the closing message did better [2]. A language model can serve as a sampled secondary review.

# An illustration, not evidence

To show how the first control works, we trained a small word-level language model from scratch and ran it as a 240-ticket service desk in which the harness set the environment state and the model wrote the assistant's closing line (Table 1). The model is a toy and the desk is simulated. The table shows that when error text was allowed into the prompt, the model claimed completions that the record would deny, and that typed envelopes removed the effect in this setting. It does not estimate how often this happens in practice.

*Table 1. Simulated desk. Closing lines from a toy language model; record flags set by the harness.*

| Ticket class | n | Claimed complete | Record refunded | Mismatch |
|---|---|---|---|---|
| True success | 90 | 89 | 90 | 0 |
| Stale connector cache | 40 | 39 | 0 | 39 |
| 400 page leaked into a digest | 50 | 50 | 0 | 50 |
| Typed envelope (http_400) | 30 | 0 | 0 | 0 |
| Empty retrieval | 30 | 0 | 0 | 0 |
| Total | 240 | 178 | 90 | 89 (37%) |

# What the sources do not show

Wu's study covers one runtime and is a preprint [1]. Advani's results come from benchmarks, and the 45 to 76 percent range spans two benchmarks with very different protocols; the telecom domain shows that the rate depends on the setting [2]. Zhu and colleagues' half-life finding concerns one scenario [3]. Datadog's report measures transport-visible failures [4]. None of these sources tests the three controls in production, and the simulation above is a toy. The controls are hypotheses with a plausible mechanism and consistent indirect support. A direct test would compare, on a public benchmark with ground-truth state, the false-success rate under raw faults, typed faults, and gated completion.

# References

[1] W. Wu, "When errors become narratives: A longitudinal taxonomy of silent failures in a production LLM agent runtime," arXiv:2606.14589, Jun. 2026 (preprint).

[2] L. Advani, "From confident closing to silent failure: Characterizing false success in LLM agents," in *Workshop on Failure Modes in Agentic AI (FAGEN), ICML*, 2026; arXiv:2606.09863.

[3] J. Zhu et al., "Your agents are aging too: Agent lifespan engineering for deployed systems," arXiv:2605.26302, May 2026 (preprint).

[4] Datadog, "State of AI Engineering 2026," press release and report, 2026. [Online]. Available: https://www.datadoghq.com/about/latest-news/press-releases/datadog-state-of-ai-engineering-report-2026/

---

*Notes for the author (delete before submission).* (1) I removed the McKinsey and Digital Applied citations because I could not verify the claims attributed to them, and removed the carbon section because the per-call energy figure it relies on has no source. (2) I did not re-run the simulation; Table 1 is copied from your draft. (3) Add the real-case test in `evaluation_design.md` if you want a claim stronger than "hypothesis." (4) Reference style is generic IEEE-like; adapt it to the target journal.
