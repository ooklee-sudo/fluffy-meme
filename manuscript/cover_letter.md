[Date]

[Name of the Editor or Department Editor]
*Manufacturing & Service Operations Management*
INFORMS

**Re: Submission of "When to Escalate? Reviewer Capacity and the Design of Human Oversight for AI Agents"**

Dear [Name of the Editor],

We submit the enclosed manuscript for consideration as a regular article in *Manufacturing & Service Operations Management*.

Firms now let AI agents carry out multistep tasks, such as answering a customer's request through a series of tool calls, while keeping a limited pool of people ready to take over. The paper asks when a task should be taken back from such an agent, who should make that call, and how many reviewers the answer requires. Work reaches the reviewers from two directions: from the firm, through a rule such as "hand off after N errors," and from the agent itself, which may transfer a task to a person. We model how these two sources combine with verification of finished outputs and with reviewer capacity, and we test the model with a large observational corpus of agent trajectories (80,036 trajectories) and with randomized fault-injection experiments (five agents, 11,352 runs, two task domains).

The model gives three results. The firm's best rule counts each type of error by the probability that it leads to a wrong output, and an agent's own transfers hardly change that threshold even though they change the reviewers' load a great deal. Verification of outputs and escalation during the run are substitutes, and verification is worth most when reviewers are hardest to reach. A rule that sets the hand-off threshold from the observed average wait hands off too often. The experiments show that what an error leads to matters more than how many errors occur. After a misleading tool message, GPT-6.1-terra's rate of transferring the case to a person rose from 0.40 to 0.74 (from 0.32 to 0.73 in retail tasks, where the effect is concentrated) without more wrong outputs, whereas Claude Sonnet 5.5 mostly kept going and sometimes finished with a wrong output (about 0.15 to 0.18 per message in retail). Applying the model with costs calibrated from industry sources, the threshold depends mainly on the cost of a wrong output relative to the cost of a hand-off, and we give domain-specific ranges for retail and airline.

We want to be clear about what is and is not new. Operations research already studies capacity-dependent deferral and escalation to a congested human queue, and our capacity results build on that work (for example, Lykouris and Weng 2024; Wang and Rachev 2026; Lin and Zhang 2026). The contribution of the paper is different: an error model for multistep agents in which errors have distinct consequences, randomized evidence on what agents do after an error, and the finding that the volume of escalations depends on the accuracy of an agent's tools. We are also explicit about the limits of the evidence. The volume result comes from one agent, mainly in one domain; the airline sample is small; the two consequences of an error are separated by an estimator on which one agent's result depends; and we did not manipulate verification directly.

We believe the paper fits the journal's interest in AI in operations and in human–AI collaboration, and in the design of escalation policies and staffing for service systems that use AI. A replication package with the run-level data, code, and analysis scripts accompanies the submission.

Declarations. The manuscript is original and is not under review elsewhere. [If required by the journal: An earlier version of this work was submitted to another journal; the present version has been substantially revised, with a new analysis that separates the agent's own transfers from wrong outputs, a calibration of costs in dollars, and a domain-level analysis.] [Describe the use of AI tools in preparing the manuscript, as required by the journal's policy.] The authors have no conflicts of interest to declare [confirm]. [Optional: suggested department editor and reviewers, and any reviewers to exclude.]

Thank you for considering our work. We would be glad to provide any further information.

Sincerely,

[Author name(s)]
[Affiliation]
[Email]
