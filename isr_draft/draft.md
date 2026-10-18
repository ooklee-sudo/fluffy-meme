---
title: "Who Controls the Agents' Resources? Decision-Rights Convertibility and the Entrenchment of Control in Agentic Information Systems"
---

# Abstract

Organizations are starting to delegate resource-allocation decisions to networks of autonomous agents built on large language models (LLMs), yet we know little about how the governance arrangements embedded in such systems determine who ends up controlling scarce resources. Drawing on IT governance and cumulative-advantage theory, we argue that concentration of control in agentic systems need not stem from agent intent. It can arise from a design property we call *rights convertibility*, the degree to which formal decision rights can be exchanged for operational access. We develop propositions on how convertibility interacts with resource scarcity, the binding force of allocation authority, and accountability infrastructure to produce entrenched control. We then outline a controlled multi-agent experimental design that tests these propositions with behavioral traces rather than agent discourse. The framework recasts power concentration as a decision-rights design problem for agentic information systems.

**Keywords:** agentic information systems; IT governance; decision rights; large language model agents; multi-agent systems; cumulative advantage; mechanism design

# 1. Introduction

Firms increasingly deploy LLM-based agents that negotiate, schedule, procure, and allocate on behalf of human principals. As these agents begin to interact with one another, and not only with people, the information system stops being a passive tool and becomes a setting in which allocation outcomes are produced through agent-to-agent exchange. Existing research on AI in organizations has concentrated on the human–AI interface, such as trust, adoption, and augmentation. Far less attention has gone to a prior question for system designers: when agents share scarce resources and hold some governance rights over them, who comes to control those resources, and does that control persist?

This question matters because agentic systems inherit their governance from their designers. Voting interfaces, allocation privileges, and reputation records are design choices, and they are made before any agent acts. The IT governance literature has long treated the assignment of decision rights as the central lever through which organizations shape behavior (Weill and Ross 2004; Sambamurthy and Zmud 1999). That literature, however, assumes human actors whose interests, norms, and hesitations moderate how formal rights are used. Whether the same assumptions hold when the rights holders are LLM agents is an open empirical and theoretical matter.

Recent evidence suggests it cannot be taken for granted. Zhang and Shang (2026) report that LLM agents placed in a minimal executable world, with scarce tasks and basic mechanisms for transfer, election, and allocation, spontaneously form economic relations, including exchanges of votes for future access. Their setting is short and small, and it was built to demonstrate emergence rather than persistence. We take their finding as a point of departure and ask the follow-on question that matters for governance: under what design conditions do such exchanges harden into durable concentration of control?

Our work is closest to a small but growing body of LLM-based agent simulations of economic and political life. The LLM Economist framework (Karten et al. 2025), for instance, places LLM worker agents under a planner agent and shows that periodic persona-level voting can improve welfare under decentralized governance. Its objective, however, is policy design: the question is whether a governance procedure converges toward a socially desirable outcome. Ours is the complementary question of whether, and under what rules, governance positions become captured. In that setting the planner is a mechanism-design device with a well-defined objective, whereas in ours office is held by agents with private interests, and the object of study is how those agents use it.

Two further differences set our design apart. First, prior simulations tend to run over short horizons and to examine aggregate outcomes (Zhang and Shang 2026; see also recent critiques of the short horizons and thin aggregate measurement in generative-agent economies). We instead study persistence directly, using spell lengths, exclusion duration, and the half-life of control, which short runs cannot reveal. Second, existing work treats the voting rule as a given feature of the environment. We treat it, together with allocation authority and accountability records, as a manipulated design variable, which is what allows us to attribute differences in entrenchment to governance and not to the particular scenario.

We make three contributions. First, we introduce *rights convertibility* as a design-level construct that links political (decision) rights to economic (access) rights. Second, we integrate IT governance, agency, and cumulative-advantage perspectives into a model of entrenchment in agentic systems. Third, we derive testable propositions and a research design that identifies governance effects from behavioral traces, which avoids the interpretive problems of relying on what agents say.

# 2. Theoretical Background

## 2.1 Decision rights as a governance design variable

IT governance research defines governance as the specification of decision rights and accountability structures that encourage desirable behavior in the use of IT (Weill and Ross 2004). Sambamurthy and Zmud (1999) showed that arrangements for who decides, centrally or locally, produce systematic differences in how organizations use technology. Platform research extends this logic to ecosystems, where governance mechanisms such as decision rights, control, and pricing shape participant behavior and platform evolution (Tiwana et al. 2010). A shared assumption across these streams is that a right and its exercise are separable: a formal right to decide is one thing, and what the holder actually does with it depends on incentives and social context.

In agentic systems that separation may be thinner. Agents act on the mechanisms exactly as specified, and they have no organizational loyalties or reputational ties beyond those the system itself records. The design of the mechanism therefore carries more of the explanatory load than it does with human actors.

## 2.2 Delegation to autonomous agents

Agency theory frames delegation as a problem of aligning an agent's actions with a principal's interests under information asymmetry (Jensen and Meckling 1976; Eisenhardt 1989). Applied to LLM agents, the standard version of the problem concerns a single agent and a single principal. Multi-agent settings add a layer that this framing underplays: agents may hold delegated authority *over one another*. When an elected or appointed agent controls allocation, the other agents become, in effect, subjects of that authority, and the question shifts from alignment with the principal to the internal distribution of control among agents. Work on machine behavior argues that such collective outcomes need to be studied as phenomena in their own right, since they cannot be read off the properties of individual models (Rahwan et al. 2019). Researchers have also begun to use LLMs as simulated economic agents, which makes experiments of this kind feasible, subject to the usual caveats about validity (Horton 2023).

## 2.3 Cumulative advantage and entrenchment

Why would control persist? Sociological and economic accounts of cumulative advantage show how early positional gains can feed on themselves (Merton 1968), and how small early differences can lock in outcomes when returns to position increase (Arthur 1989). Institutional accounts make a related point about political economy: when those who hold political power can steer economic opportunity toward their supporters, and economic advantage in turn helps retain political power, institutions become extractive and self-perpetuating (Acemoglu and Robinson 2012). Ostrom (1990) provides the counterweight, documenting rule configurations, notably monitoring and graduated accountability, under which shared resources are governed without capture.

Taken together, these literatures suggest a feedback mechanism that is specific to systems where rights are convertible. If decision rights can be exchanged for access, and access sustains the capacity to win further decision rights, the system contains a reinforcing loop. Whether the loop operates, and whether it is dampened, should depend on identifiable design features.

# 3. Conceptual Model and Propositions

## 3.1 Constructs

*Rights convertibility* (RC) is the extent to which a formal decision right (for example, a vote or an office) can be exchanged, by promise or transfer, for operational access to scarce resources. It is a property of the system's mechanisms and not of any agent's disposition.

*Authority binding* (AB) is the degree to which an officeholder's allocation decision is executed by the system without further approval. High AB means that the holder's choice determines outcomes directly.

*Resource scarcity* (RS) is the ratio of available productive opportunities to agents' demand for them.

*Accountability infrastructure* (AI) is the extent to which past allocation and transfer behavior is recorded and visible to all agents, and enforceable through sanction or electoral consequence.

*Capability asymmetry* (CA) is the dispersion of agents' reasoning capability and initial endowments.

*Entrenchment of control* (EC) is the outcome of interest: the persistence of a single agent's or stable coalition's control over allocation, and the duration for which others are excluded from access.

## 3.2 Propositions

**P1 (Convertibility as a precondition).** Entrenchment of control is greater when rights convertibility is high than when it is low. When decision rights cannot be traded for access, differences in who holds office do not translate into durable differences in who holds resources.

**P2 (Scarcity and binding as amplifiers).** Authority binding and resource scarcity each strengthen the positive relationship between rights convertibility and entrenchment. Scarcity raises the value of access, and binding raises the certainty that an allocator can deliver it, so both raise the returns to converting rights.

**P3 (Accountability as a dampener).** Accountability infrastructure weakens the relationship between rights convertibility and entrenchment, because it raises the cost of breaking commitments and exposes patterns of favoritism to electoral consequence. We expect the effect to depend on whether visibility is paired with a means of acting on it, and not on visibility alone.

**P4 (Capability asymmetry as a selector).** Capability asymmetry does not by itself create entrenchment, but it influences *which* agents capture it when convertibility is high. Agents with greater reasoning capability or endowment are more likely to occupy persistent allocator positions.

**P5 (Rule form).** Electoral rules that raise the cost of assembling a decisive, tradable majority reduce entrenchment relative to simple plurality, conditional on convertibility being held constant.

Figure 1 (to be drawn) will depict RC as the central driver of EC, with RS and AB as positive moderators, AI as a negative moderator, and CA as a selection factor on the identity of the entrenched agent.

# 4. Research Design (Outline)

We propose a controlled multi-agent experiment built on the executable-world approach of Zhang and Shang (2026), extended to longer horizons, larger populations, and a wider set of model families. The unit of analysis is the simulated world. Governance variables are manipulated across worlds: scarcity, whether allocation authority is binding, the electoral rule, and the presence of a public record of agent behavior. Rights convertibility is varied by altering whether transfers and access commitments can be conditioned on votes. Capability asymmetry is manipulated through homogeneous versus mixed populations and through reasoning mode.

All outcomes are derived from logged, state-changing events and not from agent language. Entrenchment is measured as the share of periods in which one agent or stable coalition holds allocation control, the half-life of control spells, the Gini coefficient of cumulative access, and the longest consecutive exclusion. We will report the fraction of access commitments honored as a measure of commitment reliability. Inference relies on exact permutation tests and mixed-effects models that account for world-level clustering.

Because the validity of LLM-agent simulation is a legitimate concern, the design includes three safeguards: (i) ablations that remove survival framing, political vocabulary, and energy consequences while preserving the mechanisms; (ii) prompt-variation and model-version robustness checks; and (iii) a human-subjects benchmark in which participants play the same game under a subset of the conditions, which allows us to assess where agent and human dynamics diverge.

# 5. Anticipated Contributions

For theory, the paper extends IT governance from human organizational actors to settings where rights holders are autonomous agents, and it identifies a mechanism, rights convertibility, through which formal governance produces durable concentration of control. For research, it supplies a design that separates governance effects from agent discourse. For practice, it offers designers of agentic systems a concrete way to reason about which decision-rights architectures invite entrenchment and which constrain it, before such systems are deployed at scale.

# References

Acemoglu, D., and Robinson, J. A. 2012. *Why Nations Fail: The Origins of Power, Prosperity, and Poverty*. New York: Crown.

Arthur, W. B. 1989. "Competing Technologies, Increasing Returns, and Lock-In by Historical Events," *The Economic Journal* (99:394), pp. 116-131.

Eisenhardt, K. M. 1989. "Agency Theory: An Assessment and Review," *Academy of Management Review* (14:1), pp. 57-74.

Horton, J. J. 2023. "Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus?" NBER Working Paper.

Jensen, M. C., and Meckling, W. H. 1976. "Theory of the Firm: Managerial Behavior, Agency Costs and Ownership Structure," *Journal of Financial Economics* (3:4), pp. 305-360.

Merton, R. K. 1968. "The Matthew Effect in Science," *Science* (159:3810), pp. 56-63.

Ostrom, E. 1990. *Governing the Commons*. Cambridge: Cambridge University Press.

Rahwan, I., et al. 2019. "Machine Behaviour," *Nature* (568), pp. 477-486.

Sambamurthy, V., and Zmud, R. W. 1999. "Arrangements for Information Technology Governance: A Theory of Multiple Contingencies," *MIS Quarterly* (23:2), pp. 261-290.

Tiwana, A., Konsynski, B., and Bush, A. A. 2010. "Platform Evolution: Coevolution of Platform Architecture, Governance, and Environmental Dynamics," *Information Systems Research* (21:4), pp. 675-687.

Weill, P., and Ross, J. W. 2004. *IT Governance: How Top Performers Manage IT Decision Rights for Superior Results*. Boston: Harvard Business School Press.

Karten, S., Li, W., Ding, Z., Kleiner, S., Bai, Y., and Jin, C. 2025. "LLM Economist: Large Population Models and Mechanism Design in Multi-Agent Generative Simulacra," arXiv:2507.15815.

Zhang, L., and Shang, S. 2026. "AI Agent Economics: Can Autonomous Economic Behavior Emerge among AI Agents under Minimal External Conditions?" arXiv:2608.03076.
