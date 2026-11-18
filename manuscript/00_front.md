---
title: "When to Escalate? Reviewer Capacity and the Design of Human Oversight for AI Agents"
---

## Abstract

Firms increasingly let AI agents carry out multistep tasks while keeping a limited pool of human reviewers ready to take over. Work reaches those reviewers from two directions: from the firm, through a rule such as "hand off after N errors," and from the agent itself, which can transfer a task to a person. We ask how these two sources should be combined with output verification and with reviewer capacity. In our model an error may lead to a wrong output, which is costly to repair, or to a transfer by the agent, which adds to the reviewers' load. The firm's best rule counts each type of error by how likely it is to produce a wrong output. Verification and escalation substitute for one another, and verification is worth most when reviewers are hardest to reach. A rule calibrated to the observed average wait hands off too often. We test the model with 80,036 public agent trajectories and with randomized fault-injection experiments involving five agents (11,352 runs). Transient failures did not affect the two commercial models. A misleading tool message raised GPT-6.1-terra's transfer rate from 0.40 to 0.74, mostly in retail tasks, without increasing wrong outcomes, whereas it pushed Claude Sonnet 5.5 toward wrong outputs in retail (about 0.15 to 0.18 per message). We detect no such effect in the 50 airline tasks. What an error leads to matters more than how many errors occur, and the accuracy of an agent's tools bears on how many reviewers a firm needs.

**Keywords:** AI agents; human oversight; escalation; reviewer capacity; optimal stopping; randomized experiment
