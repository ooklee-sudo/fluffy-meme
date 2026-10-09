[Date]

Editor-in-Chief
*Decision Support Systems*

**Re: Submission of the research article "Time-invariant pricing of shared LLM inference capacity under phase-varying demand"**

Dear Editor,

We are pleased to submit the manuscript named above for consideration as a research article in *Decision Support Systems*.

Providers of large language model (LLM) inference sell capacity that their users share, and two decisions follow: what to charge per token and how many servers to provision. In practice the first is usually a single price that does not change over time, and the second is made with arrival models that assume a constant rate. Our manuscript asks when this decision rule is wrong, how large the loss is, and how much a short posted price schedule recovers. The setting is a queueing model in which demand moves between phases (hours of the day, bursts) and users react to the current price and expected delay.

The main results are the following. First, the welfare-optimal price in a phase equals the congestion toll and rises with the phase's demand, so a flat price is first best only when the phases are alike; the loss of the best flat price has an exact integral form. Second, when phases switch fast relative to the queue, a flat price becomes first best in the limit, and numerical results show where in between the loss is largest. Third, a schedule with two to four price levels recovers most of the gain of hourly prices. Fourth, we calibrate the model on public Azure and BurstGPT traces. On a trace with a strong daily cycle, a flat price loses between 11 and 19 percent of the welfare of hour-by-hour prices across 18 sets of assumed parameters, and a two-level peak and off-peak schedule removes 65 to 73 percent of that loss. Poisson-based capacity planning understates the servers needed for a delay target by about a quarter on one conversation trace and by more than 80 percent on a code trace.

We believe the paper fits the journal because it gives decision makers concrete rules for two decisions that support the operation of AI services: how to plan capacity from workload logs, and how to design and test a posted price schedule. The analysis is tied to data that practitioners can replicate, and the manuscript is explicit about the conditions under which the rules do not apply, for example when demand is dominated by unpredictable multi-day swings. We also state the limitations of the work, including the assumed service-time and demand parameters, the local nature of some of the analytical results for schedules, and the absence of competition among providers.

To the best of our knowledge, the manuscript is original, has not been published previously and is not under consideration for publication elsewhere. I have read and approved the submitted version and agree to its submission to *Decision Support Systems*. I declare no competing interests [to be confirmed]. As required, the manuscript includes a declaration of the use of generative AI tools in its preparation. The traces are public, and our code and result tables are available at [repository URL].

[Optional: We suggest the following reviewers, who have no conflict of interest with me: (1) [Name, affiliation, e-mail]; (2) [Name, affiliation, e-mail]; (3) [Name, affiliation, e-mail]. We ask that [Name] not be asked to review because of [reason].]

Thank you for considering our work. We look forward to your response.

Sincerely,

Ook Lee
Department of Information Systems, Hanyang University, Seoul, Republic of Korea
ooklee@hanyang.ac.kr
