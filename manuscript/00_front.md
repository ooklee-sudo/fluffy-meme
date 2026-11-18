---
title: "When to Escalate? Reviewer Capacity and the Design of Human Oversight for AI Agents"
---

## Abstract

Firms deploy AI agents on streams of multistep tasks and rely on a limited pool of human reviewers to take over when an agent goes wrong. Work reaches those reviewers from two sources: the firm, through a rule such as "hand off after N errors," and the agent, which may transfer a task to a person on its own. We study how the two combine with verification of outputs and with reviewer capacity. In our model an error can lead to a wrong output, which is costly to repair, or to a transfer by the agent, which loads the reviewers. We show that the firm's best rule counts each error type by the probability that it leads to a wrong output; that verification and escalation are substitutes, with verification worth most when reviewers are hardest to reach; and that a rule set from the observed average wait hands off too often. We use 80,036 public agent trajectories and randomized fault-injection experiments with five agents (11,352 runs). Transient failures did not change the success of the two commercial models. A misleading tool message raised GPT-6.1-terra's rate of transferring to a person from 0.40 to 0.74 without increasing wrong outcomes, and led Claude Sonnet 5.5 to wrong outputs (about 0.12 per message). What an error leads to matters more than how many errors occur, and the accuracy of an agent's tools affects how many reviewers a firm needs.

**Keywords:** AI agents; human oversight; escalation; reviewer capacity; optimal stopping; randomized experiment
