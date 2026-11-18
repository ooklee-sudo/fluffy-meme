## 6. Discussion

### 6.1 Implications for research

**Reversing a delegation is a design problem with its own structure.** Work on human–AI delegation has mostly asked whether a task should be given to an AI (Baird and Maruping 2021; Fügener et al. 2022). Once an agent acts over many steps, the question that follows is when the task should be taken back, by whom, and with what evidence. The decision can be taken by the firm, by the agent, or by both, and the two sources of escalation do different things: the firm's rule should follow the probability that errors lead to wrong outputs, while the agent's own transfers determine how much work reaches the reviewers.

**The same observed pattern can come from different mechanisms.** Bursts of errors, which practitioners often call cascades, are consistent with contagion, with differences in task difficulty, and with persistence inside a run. In our observational corpus most of the clustering is difficulty. In the experiments a misleading message has effects that last only a few calls. What differs most across agents and error types is not whether errors spread but what the agent does next. Counting errors without asking what they lead to will misjudge both risk and workload.

**Success rates hide a distinction that matters economically.** After a misleading message, task success falls for two of the three agents we split, and in our first analysis we read this as wrong outputs. The transcripts show that for those two agents it is mostly the agent handing the task to a person. Both reduce success on a benchmark that scores the final state, but one costs a repair and the other a reviewer's time, and they call for different responses. Evaluations of agents that report a single success rate should record at least whether the agent escalated. This is a methodological point from the agents we tested, and we do not claim that it holds for others.

**Randomized fault injection is cheap enough to be routine.** The 11,352 runs reported here cost about US\$330. Agent behavior can be manipulated at low cost and under full control, which makes it possible to test behavioral claims about agents with the standards used for claims about people. We used it to separate errors that arrive by chance from errors that cause others, and to separate two consequences of an error.

**Oversight capacity and tool accuracy belong in the same model.** Capacity models of human review take the demand for review as given, as a function of a risk score or of reviewer error rates (Lykouris and Weng 2024; Wang and Rachev 2026; Lin and Zhang 2026). Our evidence suggests that, for multistep agents, demand also depends on the accuracy of the agent's tools: a misleading message nearly doubled one agent's transfer rate. This is one agent in one domain.

### 6.2 Implications for practice

1. **Classify the errors your agent meets, and measure what each kind leads to.** Count errors by their probability of leading to a wrong output (Proposition 1). An error type that never does should carry no weight, however often it occurs. The rule only binds when a wrong output costs at least about two human contacts (Appendix C), so a firm should first estimate that cost. Where a wrong output is no more than a repeat contact, the rule hardly matters. Where it brings a return and a possible chargeback, as in retail, or a severe case, as in airline, an agent like Claude Sonnet 5.5 should be handed off after a few errors. A small injection experiment, in which known errors of each type are inserted at random points of real tasks, estimates these probabilities and the rate of agent-initiated transfers. Our design used 328 runs per arm for each commercial agent (164 tasks, two repetitions). With a paired design and a task-level standard deviation of the difference of about 0.45, that detects effects of about 0.10 or larger with 80% power (the standard error is $0.45/\sqrt{164} \approx 0.035$, and the minimum detectable effect is 2.8 times that). Smaller effects, such as a drop of a few points, would need more runs.

2. **Treat tool accuracy as an input to staffing.** For one agent, a single misleading tool message changed the share of tasks reaching a person from 40% to 74%. A firm that connects an agent to enterprise data should plan reviewer capacity for the error rate of those data sources and not only for the agent's own reliability, and should expect data governance and capacity planning to move together. This should be confirmed with more agents and domains before it is generalized.

3. **Do not set escalation thresholds from the observed queue.** A rule that reacts to how busy the reviewers look ignores the delay a new case causes for others and hands off too much (Proposition 4). Use the marginal cost of a reviewer's time, which exceeds the average wait whenever waits rise with load.

4. **Decide where to monitor and where to verify.** Monitoring pays most for tasks at the margin of delegation, where handing off costs about what letting the agent finish costs (Proposition 2). Verification of finished outputs is worth more the harder it is to reach a person, and it substitutes for escalation (Proposition 3): when a check is cheap and good, escalation can wait for more errors. An agent that transfers tasks on its own already removes some wrong outputs, so it lowers the value of checking. In our experiments the coding agent can run the tests and its effects were smaller. We did not manipulate this.

5. **Agents differ in what they do after an error, so calibrate per agent and recalibrate on change.** After a misleading message GPT-6.1-terra mostly transferred, Claude Sonnet 5.5 mostly continued and sometimes finished wrong, and DeepSeek-V3.1 did both. The same rule would be wrong for at least two of them, and a new model version can change the behavior. The injection experiment can be repeated on each version.

### 6.3 Limitations and future research

*Evidence.*

- There are two task domains, one with a simulated customer and one with bugs from seven Python projects. Injected errors are exogenous and may differ from the agent's own errors, which arise when it is already confused. Our misleading message reads like the agent's own mistake and states something false at the same time, and the design does not separate the two.
- The commercial models were run at low reasoning effort and at temperature 0.5, requests may have been served by more than one provider, and model versions change quickly.
- The two channels are separated by whether a run contains a transfer to a person, and for one agent the result is sensitive to how the split is made. We have not separated tasks for which a transfer is the correct action, and the logs do not record the agent's messages, so we do not know why it transferred.
- The analyses of the two channels were chosen after we saw the data and were not pre-registered.
- We did not manipulate verification. The substitution between verification and escalation is a result of the model, and its only support in the data is that the pattern across domains agrees with it.

*Model.*

- The firm is a single decision maker with known, constant parameters, and the costs of a hand-off, of a wrong output, and of delay are calibrated from secondary sources and our run logs (Appendix C). The cost of a wrong output in particular depends on the domain, and the conclusions about thresholds depend on its ratio to the cost of a hand-off. The agent's own transfers are exogenous probabilities and not the result of a strategic choice.
- Errors are independent across steps, and the probability that an error derails a task does not depend on history. The observational data suggest a persistent component that we do not model.
- The capacity extension uses an approximation for queues with variable arrivals (Allen–Cunneen) and neglects reviewer fatigue and the quality of review (Turan 2026; Wang and Rachev 2026).

*Directions.* (i) Manipulate verification directly and test whether the threshold rises as the model predicts. (ii) Log the agent's messages to learn why it escalates and to separate tasks that call for a transfer. (iii) Study natural errors alongside injected ones. (iv) Let the vendor of the agent choose its reliability, or the reviewer choose effort, which turns the hand-off rule into part of a contract. (v) Learn the parameters online as the firm deploys.

## 7. Conclusion

Firms that deploy AI agents must decide when to take a task back, who should decide, and how many people the answer requires. We have shown that the firm's rule should count errors by their probability of leading to a wrong output; that an agent's own transfers set the workload of reviewers and hardly change the firm's threshold; that verification of outputs substitutes for escalation and is worth most when people are hardest to reach; and that a rule set against the observed queue hands off too much. In randomized experiments with five agents, transient failures did not change the success of the commercial models. A misleading tool message sent one agent's work to people far more often without producing more wrong outputs, and produced wrong outputs in another. What an error leads to matters more than how many errors occur, and the accuracy of an agent's tools is a staffing decision as much as a technical one.
