[Date]

[Name of Department Editor], Department of [Marketing / Information Systems / Decision Analysis]
*Management Science*

Dear Professor [Name],

I/We submit "Do Influencers Pay? Limited Attention, Engagement Elasticity, and Simulation-Based Pre-Tests for Seeding Decisions" for consideration in *Management Science* (suggested department: [Marketing / Information Systems]; suggested area editor, if the system allows: [name]).

**The question.** Firms pre-test social media campaigns in agent-based simulators, increasingly with LLM-driven agents, before choosing between seeding a few influencers and many ordinary users. The debate about such simulators concerns whether the agents behave realistically. We ask a different question: does the recommendation depend on modeling choices that are separate from agent realism?

**What we do.** We examine three such choices: the metric used to compare plans, the mechanism that schedules agent actions, and the assumed relation between an account's audience size and the attention each follower pays to it, which we summarize as an engagement elasticity β. We build an event-driven simulator (inhomogeneous Poisson activity with circadian rhythms and decaying stimuli), compare plans with discounted reach, certainty equivalents, conditional value at risk, and stochastic dominance, state a first-generation exposure result that links β to the ranking of the two strategies, and estimate β on 209,890 posts from six influencer campaigns on Weibo.

**What we find.** Under constant attention, concentrated seeding dominated at every hour and quantile, and the scale-versus-speed trade-off suggested by the time to half of a plan's own adopters was an artifact of scale normalization. Alternative schedulers preserved the ranking but roughly doubled the absolute gap between plans. The ranking reversed at modest elasticities (near 0.1 for discounted reach and downside risk, 0.2 to 0.3 for expected reach), with a band between the thresholds where time and risk preferences decide. The estimated elasticity is 0.66 (95% CI 0.63 to 0.68), well above both thresholds.

**Contribution.** The paper (i) shows that metric, timing, and attention choices outside the agent model can reverse or distort a seeding recommendation, with three practical principles for pre-tests; (ii) identifies the engagement elasticity as a boundary condition on the influentials-versus-ordinary-users debate; and (iii) turns that debate into an estimable quantity. We are explicit about scope: the simulator is rule-based and synthetic, and the elasticity estimate is descriptive and subject to upward biases, so we present the conclusions as hypotheses for field testing.

**Data and code.** The empirical analysis uses SAGraph, a public dataset released under a CC-BY 4.0 license. Code and per-run results are provided as an anonymized supplementary archive and will be deposited in a public repository upon acceptance.

The manuscript is not published and is not under review elsewhere. [AUTHOR TO COMPLETE: answer the submission system's questions about prior submissions truthfully; see checklist.] [AUTHOR TO COMPLETE: conflicts of interest, funding.]

Thank you for considering our work.

Sincerely,

[Name, affiliation, e-mail]
