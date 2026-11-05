---
title: "Switching the Ruler: Measurement-System Risk and Real Options in Generative AI Maintenance"
---

# Abstract

Real options theory in information systems assumes that the measure used to update beliefs about an IT investment, however noisy, stays attached to the asset it measures. Generative AI maintenance breaks that assumption. Organizations now use one language model to maintain another: a judge model scores outputs, an optimizer searches for prompts that raise the score, and a release review reads the increase as evidence of improvement. The instrument that licenses commitment is itself a model that is cheap, endogenous to search, and versioned without notice. This paper develops two theoretical constructs for this setting. The first, *measurement-system risk*, is the risk that the instrument used to observe value is biased, collapsing, or jumping; it is distinct from the technical, organizational, market, and competitive risks of the option-based IT risk literature. The second, the *switch-the-ruler option*, is an option written on the instrument rather than on the project: the right to pin a judge version, to refuse comparisons across a suspected jump, and to recalibrate the judge against an independent inspection before any promotion is considered. Six propositions specify when net-present-value reasoning on judge scores commits too early and when the switch-the-ruler option is valuable, including the boundary result that pinning an uninformative judge is worth nothing. A stylized extension shows that inspection both detects and deters gaming and governs how strongly pay can safely follow judge scores. Illustrative experiments with an open-weight policy model and two judges show that the problem is conditional: a strong judge turned search into improvement, whereas a weak judge removed the gain and increased the cases in which the judge score rose while correctness fell.

**Keywords:** measurement-system risk; switch-the-ruler option; real options; LLM-as-a-judge; generative AI maintenance; IT investment; organizational control

# 1. Introduction

Information systems research has long treated IT investment as commitment under uncertainty (Benaroch 2002, Fichman 2004, Taudes et al. 2000). Real options theory entered the conversation because IT projects are, in important respects, irreversible, their payoffs are uncertain, and managers retain the ability to wait, stage, switch, or abandon (Dixit and Pindyck 1994, Myers 1977, Trigeorgis 1996). Practicing IT managers already build such options into their risk plans, even when they do not name the theory (Benaroch et al. 2006).

This literature rests on an assumption it rarely states. Whatever the source of uncertainty, the signal through which managers learn about value, whether a pilot result, a usage statistic, or a benchmark, is treated as a noisy but *stable* reading of the underlying asset. Uncertainty lives in the asset; the ruler is fixed. Every option in the classical menu, from deferral to abandonment, is written on the project, and the ruler that tells managers when the option is in the money is taken as given.

Generative AI maintenance violates this assumption in a specific and consequential way. An LLM-as-a-judge scores the live policy, an optimizer searches for a prompt or adapter that raises the score, and a release review reads the increase as evidence that the system has improved (Zheng et al. 2023). The judge is cheap, but it is also endogenous to the search and can be changed without notice, by a rubric edit or by a vendor update behind a stable model name. A movement on the dashboard is therefore compatible with three distinct events: the policy changed, the ruler changed, or the optimizer found a behavior that pleases the ruler while harming the work. The question this paper asks is both theoretical and operational: *when should an organization exercise the option to promote a generative policy that a judge has scored more highly, and what options does it hold on the judge itself?*

The paper makes two theoretical contributions and two supporting ones.

The first contribution is the construct of **measurement-system risk**: the risk that the instrument used to observe value is biased, collapsing, or jumping. We define the construct through an explicit observation equation, distinguish its three forms, and show why it cannot be absorbed into any of the risk classes in the option-based IT risk mapping of Benaroch et al. (2006). Judge drift is not technical performance risk, because the system may be unchanged; it is not organizational risk, because the people may be unchanged. It is risk located in the instrument.

The second contribution is the **switch-the-ruler option**, an option whose underlying is the observation equation rather than the project. It consists of the right to pin a judge version, to refuse comparisons of scores across a suspected change in the judge, and to re-estimate the judge against an independent inspection before promotion. We show that this option has no counterpart in the classical IT option menu, that it is the condition under which every other option in that menu remains meaningful, and that its value has a sharp boundary: it is positive when the judge is informative and vanishes when the judge has collapsed. Without it, the compound pilot-then-expand option collapses back into net-present-value (NPV) reasoning on the quote.

Two supporting contributions follow. We derive an exercise rule and six propositions that specify when NPV on judge scores commits too early, and we extend the model to search depth, gaming, and judge-linked pay, showing that inspection both detects and deters gaming. A designed illustration and an empirical check with open-weight models then show that the divergence between judge score and quality is conditional on the judge. The computational evidence illustrates the mechanisms; it does not test them.

The next section reviews real options in IT investment and model-based evaluation as an organizational control. Section 3 develops measurement-system risk as a construct. Section 4 develops the switch-the-ruler option. Section 5 embeds both in an option model of generative maintenance and states the propositions, and Section 6 extends the model to search, inspection, and pay. Section 7 reports the illustrative evidence, and Section 8 discusses implications before Section 9 concludes. The electronic companion (Sections EC.1 and EC.2) gives a derivation of the exercise rule and the proofs.

# 2. Theoretical Background

## 2.1. Real Options and IT Investment

A real option is the right, but not the obligation, to take a managerial action in the future at a defined cost (Dixit and Pindyck 1994, Myers 1977, Trigeorgis 1996). Its underlying asset is a project, a capability, or a technology position rather than a traded security. The canonical insight is that irreversibility, uncertainty, and the ability to wait together make the Marshallian investment rule too eager. If $V$ denotes project value and $I$ the sunk cost of commitment, the firm should wait until $V$ crosses a threshold above $I$ that incorporates the option premium $F$ of keeping the decision open.

IS research adopted the idea because IT investments satisfy its premises unusually well. Software and platform choices are costly to reverse, benefits arrive late and depend on complementary organizational change, and staging through pilot, expansion, abandonment, and switching is already how many IT organizations work (Benaroch 2002, Fichman 2004, Taudes et al. 2000). Benaroch et al. (2006) showed that an option-based mapping of risks appears in real IT risk plans even when managers do not compute option prices, and Tewari (2026) applies the logic to the timing of enterprise AI adoption.

Two limitations of this tradition motivate the present paper. First, most applications treat a project as a single funding episode, whereas generative systems are maintained rather than funded once. The decision that destroys flexibility is no longer whether to build a data warehouse but whether to promote this week's policy to all traffic. Second, and more fundamentally, the risk taxonomies in the option-based IT literature locate uncertainty in technical performance, organization, market, and competition. They assume that the performance measure used to update beliefs remains stably attached to the underlying asset. Generative maintenance violates that assumption whenever the measure is itself a model.

## 2.2. LLM-as-a-Judge as an Organizational Control

Language-model judges entered practice because many generative outputs lack a cheap deterministic label (Zheng et al. 2023). Organizations therefore appoint a second model, wrap it in a rubric, and treat its score as a measure of quality. Such scores are then used to choose among prompts, to generate preference data, and to approve deployments. In IS terms, the judge is a control system (Ouchi 1979), an artifact intended to keep an operating process aligned with organizational intent.

Three properties of this control have theoretical consequences, and each anticipates one form of measurement-system risk developed in Section 3.

*It is cheap relative to inspection.* This is why it spreads, but it also means that the judge will be queried far more often than any human sample or gold checker, so beliefs come to be updated mainly on the cheap instrument.

*It is endogenous to search.* Once an optimizer is pointed at the judge, the judge is no longer only a measurement device; it becomes a training objective. Goodhart's law is the informal statement of this problem (Manheim and Garrabrant 2018), and the organizational version is familiar from the folly of rewarding one behavior while hoping for another (Kerr 1975). The IS version is that a control used as an objective ceases to be a control.

*It can be versioned without notice.* Vendor endpoints change behind stable names, rubrics acquire an extra sentence, and few-shot blocks are quietly "improved." Historical scores are then not a time series of $V$ but a time series of a changing observation equation.

Recent technical work has documented that judges are not oracles, that rubrics constitute an attack surface, and that optimizing against a learned proxy can eventually reduce the quantity it was meant to track (Gao et al. 2023). These findings are inputs to an IS theory rather than substitutes for one. The organizational question is how commitment should respond when the control that licenses commitment is cheap, endogenous, and movable, and what rights the organization holds over the control itself.

# 3. Measurement-System Risk

## 3.1. Definition

**Definition 1.** *Measurement-system risk is the risk that the instrument an organization uses to observe the value of an IT asset is biased, collapsing, or jumping, so that movements in the instrument cannot be read as movements in value.*

The construct is defined against an explicit observation equation. Let $V_t$ denote the value of operating the current generative policy on the work the organization cares about, and let $J_t$ denote the judge score:

$$J_t = a_t V_t + b_t + \varepsilon_t \tag{1}$$

The slope $a_t$ measures how much the judge sees of value, the intercept $b_t$ captures what the judge rewards that is not value, and $\varepsilon_t$ is reading noise with variance $\sigma^2$. Classical real options treatments of IT investment implicitly fix $(a_t, b_t)$ and let uncertainty enter through $V_t$ and $\varepsilon_t$. Measurement-system risk is the relaxation of that restriction.

## 3.2. Three Forms

The observation equation can fail in three distinct ways, each corresponding to one of the properties of the judge identified in Section 2.2.

*Bias* is movement in $b_t$ induced by the organization's own search. An optimizer that searches over policies to raise $J_t$ can raise $V_t$, raise $b_t$ through rubric gaming, or do both. Bias is endogenous: its magnitude depends on optimization pressure, which the organization chooses.

*Collapse* is $a_t \to 0$: the judge's range across policies becomes negligible, so that its readings carry almost no information about $V_t$. A collapsed judge is often described in practice as conservative. In the present theory it is uninformative, and an uninformative quote still has an argmax.

*Jump* is a discrete change in $(a_t, b_t)$ caused by a new judge version, a rubric edit, or a vendor update. Jumps are exogenous to the policy and often invisible to the people reading the dashboard. After a jump, the naive increment $J_t - J_{t-k}$ equals $a_t V_t - a_{t-k} V_{t-k} + (b_t - b_{t-k})$ plus noise, so that even an unchanged policy can produce a movement that reads as a quality change.

The three forms differ in their source, their observable signature, and the remedy they call for. Table 1 summarizes these differences; Sections 4 and 5 derive the remedies.

**Table 1. The Three Forms of Measurement-System Risk**

| Form | Parameter | Source | Observable signature | Remedy | Propositions |
|---|---|---|---|---|---|
| Bias | $b_t$ rises under search | Endogenous (optimization pressure) | Judge rises while inspection falls | Inspect; canaries | 4, 5, 6 |
| Collapse | $a_t \to 0$ | Judge capability or rubric | Narrow judge range across policies | Raise $F$; buy inspection | 2 |
| Jump | Discrete change in $(a_t, b_t)$ | Exogenous (versioning) | Dashboard move coincides with a judge or rubric diff | Switch the ruler: pin, refuse, recalibrate | 1, 3 |

## 3.3. Distinctiveness from Existing IT Risk Classes

Benaroch et al. (2006) mapped technical performance, organizational, market, and competitive risks onto the options that manage them. Measurement-system risk differs from each.

It is not *technical performance risk*, because the policy may be unchanged while the judge moves; a ruler jump produces a performance incident with no performance change. It is not *organizational risk*, because the people and processes may be unchanged; the jump happens inside a vendor endpoint or a rubric file. It is not *market risk*, although traffic shifts can degrade a holdout set, because the problem persists on a fixed traffic mix. It is closest to *competitive risk* only in the incidental sense that vendors change judges for their own reasons.

The decisive difference is structural. In every classical risk class, uncertainty concerns the *asset*, and better measurement reduces it. In measurement-system risk, uncertainty concerns the *measurement*, and further measurement with the same instrument does not reduce it and can increase it, because search against the instrument is what moves $b_t$. A pilot scored only by $J$ is not a pilot in the options sense; it is another reading of a possibly moved ruler on a smaller cohort.

Table 2 restates the classical mapping and locates the new class.

**Table 2. Classical IT Option Mappings and Added Measurement-System Risk**

| Risk class | Classical option | In generative maintenance |
|---|---|---|
| Technical performance | Defer; pilot; abandon | Policy may be worse than $J$ says; inspect $G$ before expand |
| Organizational | Stage; change scale | Review rights: who may refuse a green judge |
| Market / demand | Defer; expand | Traffic mix shifts; holdout rot |
| Competitive | Speed-up; switch | Vendor releases a new judge |
| **Measurement-system (this paper)** | **Switch the ruler: pin; refuse; recalibrate; inspect** | **$(a_t, b_t)$ biased, collapsing, or jumping; canaries where $J$ and $G$ disagree** |

*Note.* The last row is the increment relative to the mapping in Benaroch et al. (2006).

## 3.4. Why a Holdout Mean Is Not a Remedy

A natural response to measurement-system risk is to evaluate on a held-out sample. This does not automatically guard against the risk. If the holdout mix contains items on which a cheat happens to be correct, the holdout mean can rise even as performance falls on the cases that define organizational intent, such as refusals, abstentions, and citations that must not be invented. Inspection, as the term is used below, therefore does not mean more of the same tickets. It refers to an instrument $G_t$ on which the optimizer does not train and, in its sharpest form, to a set of items constructed so that $J$ and $G$ are expected to disagree under the cheat the organization most fears.

# 4. The Switch-the-Ruler Option

## 4.1. Definition

**Definition 2.** *The switch-the-ruler option is the right, held by the organization, (i) to pin the version of the judge and rubric, (ii) to refuse to compare $J_t$ with $J_{t-k}$ after a suspected change in $(a_t, b_t)$, and (iii) to spend inspection budget re-estimating $(a_t, b_t)$ against an independent instrument $G$ before any promotion is considered.*

The three rights are related. *Pinning* is the decision to keep the option alive: it holds $(a_t, b_t)$ fixed for every change the organization controls and makes historical scores comparable. *Refusing* is the decision not to let a suspected jump enter the exercise decision. *Recalibrating* is the exercise of the option: the organization pays for a calibration set on which $G$ is observed, re-estimates the slope and intercept, and converts subsequent judge readings into the units of value.

## 4.2. An Option on the Instrument

The switch-the-ruler option differs in kind from the options in the classical IT menu. Deferral, staging, piloting, abandonment, expansion, and switching between inputs or outputs are all written on the project: their payoff depends on $V$. The switch-the-ruler option is written on the observation equation: its payoff depends on whether $(a_t, b_t)$ has moved. It produces no value directly. It protects the value of every other option by keeping the signal on which those options are exercised meaningful.

This has a consequence that is easy to miss. Classical analyses value the option to pilot because a pilot yields a better estimate of $V$. If the pilot is scored by a judge whose observation equation may have jumped, the pilot yields an estimate of $a_t V_t + b_t$ under unknown $(a_t, b_t)$, and the compound pilot-then-expand option collapses into a second application of NPV on the quote. The switch-the-ruler option is therefore a precondition for the classical menu, not an addition to it.

## 4.3. The Strike Asset Is Inspection

Recalibration requires an instrument $G$ that the optimizer does not train on: a deterministic gold checker where one exists, a calibrated human sample, or a canary battery. In option terms, $G$ is the strike asset of the switch-the-ruler option. Without $G$, the organization can still pin, which prevents internally caused jumps, and it can still refuse cross-version comparisons, but it cannot exercise recalibration. This links measurement-system risk to investment in inspection: an organization that has not built $G$ holds a switch-the-ruler option that it cannot exercise.

Pinning has its own limit. Where the judge is a vendor endpoint addressed by an undated alias, the organization cannot pin away vendor-initiated jumps. Pinning then reduces the probability of a jump only to its vendor-driven component, and recalibration becomes the main remedy.

## 4.4. Valuing the Option

The option model of Section 5 and the Gaussian derivation in Section EC.1 allow the value of the switch-the-ruler option to be expressed in the same units as the exercise premium. After subtracting the pinned intercept and rescaling by the slope, the effective variance of a judge reading is

$$\sigma_a^2 = \frac{\sigma^2 + \pi \nu^2}{a^2} \tag{2}$$

where $\pi$ is the probability of a ruler jump between comparisons and $\nu^2$ the variance of the intercept shift that a jump produces. Pinning lowers $\pi$ to some $\pi' \le \pi$, its vendor-driven floor. Recalibration against $G$ removes the systematic part of a jump and leaves only estimation error, lowering $\nu$ to some $\nu' \le \nu$. The value of the switch-the-ruler option, measured as the reduction in the exercise premium it delivers, is

$$\Omega = F(\pi, \nu) - F(\pi', \nu') \tag{3}$$

Proposition 3 in Section 5 characterizes $\Omega$. In units of the prior standard deviation of $V$, with judge noise $\sigma = 0.7$, slope $a = 0.8$, and jump size $\nu = 1.5$, the premium is 0.62, 0.70, and 0.79 for jump probabilities of 0, 0.1, and 0.3 (Section EC.1). Pinning that reduces a jump probability of 0.3 to zero is therefore worth a reduction in the promotion threshold of 0.17 prior standard deviations on every subsequent decision. The same pinning is worth 0.05 when the judge slope falls to $a = 0.3$ and 0.007 when it falls to $a = 0.1$: the less the judge sees, the less there is to protect.

# 5. A Real Options Model of Generative Maintenance

## 5.1. Objects

$V_t$ is not observed directly, and two instruments are available. The judge $J_t$ is cheap and follows Equation (1). An inspection $G_t$ is costly; its defining property is that the optimizer searching on $J$ does not train on $G$. A promotion at time $t$ replaces the live policy with a candidate at a sunk cost $I$. This cost includes engineering time, on-call risk, and the contamination of future logs. Once a promotion has occurred, rolling back does not restore the status quo ante, because the flywheel has already turned. Rollback is therefore not a free put but a new project.

## 5.2. The Option Menu

The maintenance program is a compound option on $V$ with a noisy and possibly jumping quote $J$.

*The option to wait* is the right not to promote when $J$ rises. Its value $F$ increases with the volatility of $J$ given $V$ and with the probability of a ruler jump. A collapsed judge raises $F$ because the quote carries almost no information; a highly sensitive but hackable judge also raises $F$, because the quote can be moved without moving $V$.

*The option to pilot* is a compound call. A shadow cohort or a one-percent release pays a small $I_1$ to obtain information about $V$ without paying the full $I$. Tewari (2026) argues that faster frontier change raises the value of piloting while raising, rather than lowering, the bar for irreversible commitment. Weekly generative maintenance is a high-frequency version of this timing problem.

*The option to abandon* is a put on the candidate. Exercising it can look like a political failure when the judge has printed a personal best, but in the ledger it is precisely the point of staging.

*The option to switch the ruler*, developed in Section 4, is the right to pin, refuse, and recalibrate. It keeps the other three options exercisable on a meaningful signal.

## 5.3. The Exercise Rule

The NPV rule that current practice follows is

$$\text{promote if } \Delta \hat{J} > 0 \tag{4}$$

Sometimes a cost is acknowledged, in which case the rule becomes $\Delta \hat{J} > c$. Both versions treat $J$ as if it were $V$, and both silently assume that $(a_t, b_t)$ has not moved. By contrast, the options rule is

$$\text{promote if } \mathbb{E}[V \mid J, G] - I \ge F(J, G, \sigma_{J|V}, \pi_{\text{jump}}) \tag{5}$$

Two features of this rule deserve attention. First, $G$ enters the expectation, so a rise in $J$ that $G$ contradicts does not raise $\mathbb{E}[V]$ enough to cover $I + F$. Second, $F$ increases with judge noise and with jump risk: the noisier or less pinned the ruler, the higher the bar rather than the lower. Section EC.1 derives the rule, and the comparative statics behind it, in a stylized Gaussian model.

When $G$ is not yet available but can be created at finite cost, the organization is not licensed to fall back on Equation (4). It should instead raise $F$ and invest in creating some form of $G$, whether human review, schema checks, or shadow deployments. An uninformative $J$ combined with the absence of $G$ is a reason to freeze promotion, not a reason to automate it. If no inspection can be created at any reasonable cost, the model implies only a weaker rule: promote on the Bayesian posterior $\mathbb{E}[V \mid J]$ rather than on the raw movement of the judge, a posterior that already discounts an uninformative judge heavily (Section EC.1).

## 5.4. Propositions

The model yields six propositions, grouped by the form of measurement-system risk they address. Propositions 1 to 3 concern the instrument itself: jumps, collapse, and the value of the switch-the-ruler option. Propositions 4 to 6 concern bias induced by search. Section EC.1 derives their logic and Section EC.2 gives the proofs; the computational evidence in Section 7 illustrates rather than tests them.

### Propositions on the Instrument

**Proposition 1 (ruler jumps).** *A change in the judge version or rubric that is not accompanied by re-estimation of $(a_t, b_t)$ against $G$ makes historical $J$ incomparable and, if ignored, biases exercise toward candidates favored by the new ruler.*

This is the distinctively IS claim. The risk is not only that $V$ is hard to observe; the organization may be comparing two different instruments and calling the difference a movement in quality.

**Proposition 2 (noise and collapse raise the premium).** *An increase in $\sigma_{J|V}$, including the extreme case of a collapsed judge whose range across policies is negligible, raises $F$ and therefore the exercise threshold in Equation (5).*

In practice a collapsed judge is often described as conservative. The model instead treats it as uninformative. An uninformative quote still has an argmax, and the premium is what prevents the organization from shipping it.

**Proposition 3 (value of the switch-the-ruler option).** *Wherever inspection is worth buying, the value $\Omega$ of the switch-the-ruler option in Equation (3) is (i) nonnegative; (ii) increasing in the jump probability $\pi$ and the jump size $\nu$ that the organization would face without pinning and recalibration; and (iii) vanishing as the judge collapses ($a \to 0$).*

Parts (i) and (ii) say that the option is worth more where judges change more often and by more, which is the situation of organizations that rely on vendor endpoints. Part (iii) is the boundary condition: pinning and recalibrating a judge that sees nothing preserves nothing, because the premium is already at its ceiling. The switch-the-ruler option and judge informativeness are complements. An organization should pin the judges worth reading and replace, rather than pin, those that are not.

### Propositions on Search

**Proposition 4 (NPV on the judge).** *When the rubric can be gamed at a cost to true quality, the probability that Equation (4) selects a candidate with lower $V$ than the incumbent increases with optimization pressure on $J$.*

Search turns $J$ from a tape into an objective. Candidates that raise $b_t$ or exploit $\varepsilon_t$ become available, and the NPV rule cannot distinguish them from candidates that raise $V$. The proposition is conditional. Where no such candidates exist, or the search cannot reach them, additional search on an informative judge raises $V$, as the best-of-N experiment reported below shows.

**Proposition 5 (holdout means).** *A rise in mean $G$ on a mixed holdout is not sufficient for exercise when the mix contains items on which a suspected cheat happens to be correct.*

The mean can conceal the problem. Refund-always policies perform well on tickets that should be refunded, and averaging those tickets with refusal tickets can still beat a weak incumbent.

**Proposition 6 (inspection canaries).** *An inspection set constructed so that $J$ and $G$ disagree under the suspected cheat raises the probability that the abandon option is exercised against that cheat.*

A canary is not simply a hard example. It is an example designed to make the cheap quote and the expensive inspection conflict, so a perfect $J$ on that example counts as evidence against exercise.

# 6. Extensions: Search, Inspection, and Pay

The option model treats the quality of the instrument as a source of risk and prices it as flexibility. This section asks how that flexibility interacts with three choices that an organization makes: how deeply to search against the judge, how strongly to inspect, and how strongly to tie pay to judge scores. It thereby endogenizes the bias form of measurement-system risk. Each subsection adds one element to a single stylized model. Throughout, a candidate that raises the judge score by gaming the rubric at a cost to quality is called an exploit. The results are stylized, their assumptions are stated where they matter, and the full proofs and numerical checks are in Section EC.2.

## 6.1. Search Depth When the Share of Exploits Is Given

Of $N$ candidates generated, the one with the highest judge score ships. An honest candidate has gold value $V \sim N(0, s^2)$ relative to the incumbent and a judge score whose correlation with $V$ is $\rho$, so the best-scoring honest candidate has expected gold value $\rho s m_N$, where $m_N$, the expected maximum of $N$ standard normal draws, increases with $N$ at a decreasing rate (Lemma 1 in Section EC.2). Each candidate is, independently with probability $\xi$, an exploit that receives the top judge score and has gold value $-d$, and search costs $c_s$ per candidate. Without inspection, an exploit ships with probability $1 - (1-\xi)^N$, so expected net value is

$$U(N) = (1-\xi)^N \rho s m_N - [1 - (1-\xi)^N] d - c_s N \tag{6}$$

Net value has a single interior maximum (Theorem 2): the marginal gain from search falls, because the increments of the expected maximum shrink, while the marginal exposure to exploits rises. The optimal depth $N^*$ is therefore unique and falls as $\xi$ and $d$ rise. With $\rho s = 0.6$, $d = 1$, and no search cost, it is 14, 8, and 4 for $\xi = 0.01$, 0.02, and 0.05. An inspection that detects an exploit with probability $\zeta$ at cost $c_G$ and replaces it with the incumbent lowers the effective loss to $(1-\zeta)d$ and raises $N^*$ (to 8, 12, 17, and 21 for $\zeta = 0$, 0.5, 0.8, and 0.95 with $d = 3$ and $\xi = 0.01$). Inspection is worth buying when

$$N \ge N_c = \frac{\ln[1 - c_G/(\zeta d)]}{\ln(1-\xi)} \tag{7}$$

so that judge-only shipping is optimal at shallow depth and inspection beyond it. When $\xi$ is close to zero, as the experiments reported below suggest for a strong judge on verifiable problems, deeper search is limited only by its cost.

## 6.2. Exploitation as a Choice and the Deterrence Role of Inspection

This subsection lets the team that searches choose the share of exploits. At each of $N$ search steps the team produces an honest candidate whose judge score is $\sigma_J$ times a standard normal draw, and it can also produce an exploit with probability $e$ at cost $(\kappa/2)e^2$ per step, so that at least one exploit exists with probability $Q = 1 - (1-e)^N$. An exploit outscores the best honest candidate by $\Delta > 0$. An inspection flags an exploit with probability $\zeta$, and a flagged release is blocked, which leaves the incumbent, whose judge score and gold value are zero, in place. The team is paid $\beta$ times the judge score of what ships. The organization values the best honest candidate at $\rho s m_N$ in gold, an undetected exploit at $-d$, and a blocked release at zero, and it chooses $N$ and $\zeta$ before the team chooses $e$. For $N = 1$ we assume $\kappa > \beta\Delta$, so that the best response is interior.

A successful exploit gains $(1-\zeta)(\sigma_J m_N + \Delta)$ when undetected and forfeits the honest score $\sigma_J m_N$ when flagged, so its net gain per unit of $\beta$ is

$$\Gamma_N = (1-\zeta)\Delta - \zeta \sigma_J m_N \tag{8}$$

The team's best response is $e = 0$ if $\Gamma_N \le 0$ and otherwise the unique root in $(0, 1)$ of

$$\kappa e = \beta \Gamma_N (1-e)^{N-1} \tag{9}$$

The root $e^*$ falls with $N$, $\zeta$, and $\kappa$ and rises with $\beta$ and $\Delta$ (Theorem 3). Without inspection, $\Gamma_N = \Delta$ at every depth, and exploitation becomes certain as search deepens. Because $m_N$ grows without bound, $\Gamma_N$ turns negative for any $\zeta > 0$ once $N$ reaches

$$N_d(\zeta) = \min\{N : \sigma_J m_N \ge (1-\zeta)\Delta/\zeta\} \tag{10}$$

Beyond $N_d$ the team invests nothing in exploits. Inspection therefore both detects exploits that are made and deters them from being made, and the deterrence strengthens with depth because a deeper search raises the honest score that a blocked release would forfeit. The organization's expected gold value, with $Q$ at the team's best response, is

$$\Pi(N, \zeta) = (1-Q)\rho s m_N - Q(1-\zeta)d - c_s N - c_G \cdot \mathbb{1}[\zeta > 0] \tag{11}$$

For $N \ge N_d(\zeta)$, $\Pi$ reduces to $\rho s m_N - c_s N - c_G$, so combining inspection with depth eliminates exploitation, whereas without inspection $\Pi(N, 0)$ falls toward $-d - c_s N$ and only shallow search is worth considering.

*Illustration.* Take $\sigma_J = 1$, $\rho s = 0.6$, $\Delta = 1$, $d = 2$, $\beta = 1$, $\kappa = 4$, $c_s = 0.01$, $c_G = 0.05$, and $\zeta = 0.4$, which gives $N_d = 10$. Without inspection, the probability that an exploit exists rises from 0.25 at $N = 1$ to 0.65 at $N = 10$ and 0.81 at $N = 32$, and expected value is negative at every depth, with a maximum of $-0.51$ at $N = 1$. With inspection, the exploit probability is zero from $N = 10$, and expected value is positive from $N = 2$ and peaks at 0.88 at $N = 26$. A weak judge ($\rho s = 0.2$ and $\Delta = 1.8$) raises exploit effort and lowers the value of search: without inspection the best expected value falls from $-0.51$ to $-0.91$, and with inspection the deterrence depth rises to 175 and the best expected value is $-0.38$ at $N = 2$.

## 6.3. Honest Effort and the Threshold of Judge-Linked Pay

This subsection adds an honest effort $a \ge 0$ at cost $(\psi/2)a^2$, which raises the gold value of every honest candidate by $a$ and its judge score by $\theta a$, where $\theta \in (0, 1]$ measures how well the judge sees honest improvement. The team's best honest effort is

$$a = \beta\theta(1 - Q\zeta)/\psi \tag{12}$$

For a given $a$, the net gain from a successful exploit becomes $\Gamma = (1-\zeta)\Delta - \zeta(\theta a + \sigma_J m_N)$. In the profile without exploitation, $Q = 0$, $a = \beta\theta/\psi$, and $\Gamma = \Gamma_0 - \beta\theta^2\zeta/\psi$ with $\Gamma_0 = (1-\zeta)\Delta - \zeta\sigma_J m_N$, so the profile is an equilibrium if and only if (Theorem 4)

$$\beta \ge \beta_d = \psi\Gamma_0/(\theta^2\zeta) \tag{13}$$

Pay that is intense enough therefore deters exploitation altogether, because it induces enough honest effort to make a blocked release costly. The threshold falls with $N$, $\zeta$, and $\theta$ and rises with $\psi$ and $\Delta$, and without inspection ($\zeta = 0$) no finite $\beta$ deters. The equilibrium is unique when $\psi\kappa > \beta^2\theta^2\zeta^2 N$ and whenever $\beta \ge \beta_u = \beta_d/(1-\zeta)$ (Theorem 4). Between these conditions several equilibria can coexist; with $N = 5$, $\zeta = 0.6$, $\beta = 6.5$, $\sigma_J = 1$, $\Delta = 2.5$, $\kappa = 1.5$, $\psi = 2$, and $\theta = 0.4$, there are three ($e = 0$, 0.015, and 0.204), and the team is slightly better off in the gaming equilibrium, so payoff dominance does not select deterrence. Where releases that fail inspection are blocked, intense judge-linked pay and inspection are complements. The result depends on this forfeiture assumption; if a blocked release were replaced by the next-best honest candidate, most of the deterrence from pay would disappear.

## 6.4. The Optimal Intensity of Judge-Linked Pay

The organization pays $w = \alpha + \beta J_{\text{ship}}$ to a risk-neutral team with an outside option of zero and no limited liability. Setting $\alpha$ so that the participation constraint binds, the organization's payoff is total surplus,

$$S(\beta) = (1-Q)(ga + \rho s m_N) - Q(1-\zeta)d - (\psi/2)a^2 - N(\kappa/2)e^2 - c_s N - c_G \cdot \mathbb{1}[\zeta > 0] \tag{14}$$

evaluated at the team's equilibrium under $\beta$, where $g$ is the gold value of one unit of honest effort. Surplus never exceeds the first best $S^{FB} = g^2/(2\psi) + \rho s m_N - c_s N - c_G \cdot \mathbb{1}[\zeta > 0]$, with equality if and only if $e = 0$ and $a = g/\psi$ (Theorem 5), so the first-best intensity of pay is $\beta^{FB} = g/\theta$.

*Inspection can restore the first best.* The first best is implementable as an equilibrium at $\beta = g/\theta$ if and only if $\beta_d \le g/\theta$ (Theorem 5). Inspection thus lets the organization use judge-linked pay at full strength whenever the deterrence threshold lies below the first-best intensity, which deeper search, stronger inspection, or a judge that sees honest effort better can achieve.

*Underincentivization when gaming is not deterred.* With $\zeta = 0$, surplus is strictly decreasing beyond $g/\theta$, so whenever the judge can be gamed the optimal intensity lies strictly below $g/\theta$: the organization underincentivizes honest effort in order to limit gaming. Pay on the judge score is worth introducing only if

$$g\theta\kappa > \psi N \Delta(\rho s m_N + d) \tag{15}$$

*Illustration.* Take $g = 1$, $\psi = 1$, $\theta = 0.7$, and the parameters of the exploitation illustration with $N = 4$, so that $\beta^{FB} = 1.43$. Without inspection, (15) fails, the optimal pay is zero, and surplus is 0.578. With inspection of power $\zeta = 0.4$, $\beta_d = 0.96$ lies below 1.43, so full-strength pay is optimal and surplus equals $S^{FB} = 1.028$. With $\zeta = 0.2$, $\beta_d = 6.06$ exceeds 1.43, pay at the first-best intensity induces exploitation, and inspection adds nothing beyond its cost.

## 6.5. What the Extensions Imply for Measurement-System Risk

Taken together, the extensions show that the bias form of measurement-system risk is not a property of the judge alone. The share of gameable candidates is chosen by a team that is paid on the score, and when nothing deters it, it rises with search depth. Inspection works twice, by detecting gaming and by making it unattractive, and its deterrence strengthens with depth and with the honest effort that pay induces. The organization's best intensity of judge-linked pay therefore depends on inspection. Three implications are testable in principle: release processes that combine strong judge-linked incentives with no independent inspection should show more divergence between judge score and quality; divergence should rise with search depth in the absence of inspection; and weaker or more gameable judges should be paired with weaker judge-linked incentives.

# 7. Illustrative Computational Evidence

This section reports two computational exercises. Their role is to make the constructs and propositions concrete, not to test them. The first is a designed illustration in which a cheating policy is built into the setting, so that the accounting of the option model can be inspected in full. The second is an empirical check on verifiable math problems in which nothing is planted and the question is whether, and under which conditions, judge scores and true quality diverge.

## 7.1. A Designed Illustration

The laboratory is a store support desk. Each ticket has an order identifier and a correct act (refund, replace, refuse, or track), and gold quality $G$ is a deterministic program that credits the legal act, naming the order, and not inventing a tracking token, with no call to any model. The twenty-two tickets comprise twelve development items that the search may see, eight frozen holdout items, and two refuse-class canaries written so that a rubric rewarding delight will favor an illegal grant of money. Eight named policies map onto four reply programs: redirect, plain legal, warm legal, and always refund, which is the cheat. Two judges implement $J$: an inspectable lexicon-and-length rubric, with a drifted variant that leans toward yes, and SmolLM2-135M-Instruct, scored by the log-likelihood of Yes versus No under the same rubric text.

**Table 3. Laboratory Mapping from Options Objects to Measured Quantities**

| Policy | G holdout | G canary | J rubric | Exercise |
|---|---|---|---|---|
| Warm legal | 1.00 | 1.00 | 0.48 | wait / allow |
| Plain legal | 0.94 | 1.00 | 0.40 | allow |
| Always refund | 0.78 | 0.55 | 0.92 | abandon |
| Redirect | 0.55 | 0.55 | 0.08 | abandon |

*Note.* $G$ is deterministic gold. $J$ is the inspectable development rubric. Exercise follows Equation (5) with a canary floor of 0.70.

Each form of measurement-system risk appears in the ledger. *Bias:* applying Equation (4) to the development rubric selects always-refund, with $J$ rising from 0.08 for redirect to 0.92, and its holdout $G$ of 0.78 beats redirect, so Propositions 4 and 5 are visible in the same row. On the canaries, $G$ is 0.55 for the cheat and 1.00 for the legal programs, whereas the rubric $J$ is 0.92 for the cheat, so a canary floor of 0.70 exercises the put (Proposition 6). *Collapse:* the open-weight Yes/No judge stays within [0.18, 0.26] across every unique reply, whereas the inspectable rubric spans [0.08, 0.92] on the same replies; the small model is nearly constant, and its argmax is still the cheat by a few hundredths (Proposition 2). *Jump:* a rubric edit toward unconditional yes leaves the top-ranked policy unchanged but widens the gap, since the cheat moves from 0.92 to 1.00 while $G$ is unchanged. Read across versions without recalibration, this is a movement in quality that did not happen (Proposition 1).

Figure 1 plots the selection contrast. The bar visible to the optimizer rises under judge search, but the bars it is not shown, holdout gold and canary gold, do not follow. Because the cheat was built into the setting, these numbers show that the pattern can occur, not how often.

**[Figure 1. Judge Search versus Gold Selection — insert original figure]**

*Note.* The development judge is the quote visible to search. Holdout gold and canary gold are inspections the optimizer cannot train on. The dashed line marks the canary floor used to exercise the abandon option.

## 7.2. An Empirical Check: Design

The empirical check uses 200 questions drawn at random from the GSM8K test set (Cobbe et al. 2021). Each question has a numeric answer, so gold quality $G$ is exact match on the final number and requires no model. The policy is Llama 3.1 8B Instruct, an open-weight model, sampled at temperature one. The judge $J$ is a reference-free score from one to ten for clarity, apparent correctness, and completeness, and it never sees the gold answer. Two judges are compared: GPT-4o-mini as the strong judge and Llama 3.2 3B Instruct as the weak one. All models were accessed through a commercial API in October 2026, and the versions behind these names may change, which is itself an instance of the jump risk the paper describes. The labels strong and weak refer to relative size and capability.

Two designs apply search pressure to $J$. In best-of-N selection, thirty-two answers are sampled per question, and the answer with the highest $J$ among $N$ randomly drawn candidates is selected, with ties broken at random. In judge-guided rewriting, an optimizer model (the same Llama 3.1 8B Instruct) is told the grader's rubric and the current score, proposes four rewrites per round, and runs for six rounds. In the optimize arm the best-scoring rewrite replaces the current answer if it does not lower the score. In the control arm one of the four rewrites is kept at random. The arms share the same rewriting and differ only in whether the judge selects, which separates the effect of judge pressure from the effect of rewriting itself. The optimizer never sees the gold answer.

## 7.3. Best-of-N Selection

**Table 4. Best-of-N Selection by Judge Score, Evaluated by Gold**

| N | Gold accuracy [95% CI] | Mean J | Length (chars) | Oracle |
|---|---|---|---|---|
| 1 | 0.756 [0.719, 0.794] | 8.40 | 891 | 0.756 |
| 2 | 0.816 [0.778, 0.853] | 9.08 | 862 | 0.862 |
| 4 | 0.842 [0.803, 0.881] | 9.46 | 855 | 0.919 |
| 8 | 0.853 [0.810, 0.891] | 9.65 | 848 | 0.950 |
| 16 | 0.861 [0.821, 0.901] | 9.77 | 847 | 0.969 |
| 32 | 0.868 [0.827, 0.907] | 9.85 | 846 | 0.985 |

*Note.* 200 questions; judge GPT-4o-mini; intervals from a bootstrap over questions. Oracle is the share of questions for which at least one of the $N$ candidates is correct.

The accuracy of the selected answer rises from 0.756 with one candidate to 0.868 with thirty-two and never turns down. The gains diminish quickly: moving from one candidate to two adds six points, whereas moving from sixteen to thirty-two adds less than one. The judge captures roughly half of the improvement that exact-match selection could deliver, between 49 and 57 percent depending on $N$. Selected answers do not become longer, and judge score correlates negatively with length within a question ($-0.17$). The mean judge score of the selected answer reaches 9.85 on a ten-point scale, so the judge is close to its ceiling and cannot separate the many answers that receive the maximum. In the terms of the model, the judge here is informative (the within-question correlation between judge score and correctness is 0.48), and no exploitable cheat appears among the sampled answers. The shape of the curve is what the search-depth model implies when the share of exploits is close to zero, and the gap to the oracle is the value of an inspection the judge cannot substitute for.

## 7.4. Judge-Guided Rewriting

**Table 5. Judge-Guided Rewriting: Optimize Minus Control After Six Rounds**

| Measure | Strong judge | 95% interval | Weak judge | 95% interval |
|---|---|---|---|---|
| Gold accuracy | +0.100 | [+0.035, +0.165] | −0.025 | [−0.095, +0.045] |
| Judge score J | +1.77 | [+1.47, +2.08] | +0.79 | [+0.68, +0.91] |
| Length (chars) | +132 | [+27, +239] | −10 | [−120, +104] |
| Share with J up, G down | +0.015 | [−0.005, +0.040] | +0.065 | [+0.020, +0.110] |

*Note.* Paired differences over 200 questions; intervals from a bootstrap over questions. The last row is the share of questions whose judge score is higher and whose gold score is lower than in round 0.

Under the strong judge, the optimize arm raised accuracy from 0.730 to 0.815, whereas the control arm moved from 0.730 to 0.715; the paired difference of 0.100 has an interval that excludes zero, and the share of questions in which the judge score rose while gold fell did not differ detectably between arms. Under the weak judge, optimization again raised the judge score, by 0.79 points more than the control arm, but accuracy did not improve (0.735 to 0.700 against 0.735 to 0.725), and the difference of $-0.025$ has an interval that includes zero. The share of questions in which the judge score rose while gold fell was nevertheless 6.5 percentage points higher than in the control arm, and that interval excludes zero. Answers grew about as long in both arms, so the growth reflects the instruction to rewrite and not pressure from the judge.

## 7.5. What the Evidence Does and Does Not Show

Three conclusions follow. First, search against a judge is not uniformly dangerous: with a strong judge on verifiable problems it improved correctness, and no divergence between judge score and gold was detectable. Second, the effect of search depends on the judge, which is the comparative static of Proposition 2: the same procedure produced improvement under the strong judge and none under the weak judge, together with more cases in which judge score and correctness moved in opposite directions. Third, the strong judge approached its ceiling quickly under both designs, which limits what further search can reveal.

Three conclusions do not follow. The experiments do not show that judges are generally gameable, because no gaming was detected in either design. They do not show that accuracy falls under a weak judge, because the interval for that difference includes zero. And they do not speak to open-ended tasks without a deterministic gold, to other models, or to organizations. The conditional pattern resembles the finding from studies of learned reward models, where optimization against a proxy first helps and later hurts as pressure grows (Gao et al. 2023). In the present experiments the strong judge stays in the region where search helps, and the weak judge shows no gain.

# 8. Discussion

## 8.1. Theoretical Implications

*Measurement-system risk extends the IS risk ontology.* Theories of IT risk classify uncertainty by its location in the asset, the organization, the market, or the competitive environment. This paper adds a location that these theories assumed away: the instrument. The addition matters because the construct changes what counts as a remedy. For every classical risk, more measurement reduces uncertainty. For measurement-system risk, more measurement with the same instrument can increase it, because search against the instrument is what biases it, and because a new version of the instrument can make old measurements incomparable. An IS theory of generative maintenance that omits this location will misclassify dashboard incidents as policy regressions and prescribe the wrong option.

*The switch-the-ruler option extends the real options menu.* Classical IT options are written on the project. The switch-the-ruler option is written on the observation equation, and it is a precondition for the rest of the menu: without it, a pilot scored by a moved judge is not a pilot, and the compound option collapses into NPV. The option has a strike asset, the inspection instrument $G$, which ties measurement governance to inspection investment, and it has a sharp boundary, stated in Proposition 3: its value vanishes as the judge collapses. The theory therefore does not simply recommend pinning. It recommends pinning the judges that are worth reading and replacing those that are not.

*The theory moves real options from project selection to system maintenance.* The funding episode is the wrong unit when the digital object is a policy that can be promoted every week. The option being destroyed is not the chance to have built a different warehouse but the chance to have waited for an inspection before rewriting the log that trains next week's policy. Compound options of the pilot-then-expand type are not a metaphor for a two-stage R&D program; they describe the release train itself.

*The instrument and the organization's own choices interact.* When the team that searches is paid on the judge score, the share of gameable candidates is a choice, inspection both detects and deters gaming, and the optimal intensity of judge-linked pay depends on the inspection that accompanies it. This endogenizes the bias form of measurement-system risk and links the theory to multitask agency (Holmström and Milgrom 1991).

## 8.2. Organizational Control and Performative Metrics

Ouchi (1979) distinguished markets, bureaucracies, and clans as modes of control. A judge score resembles a bureaucratic output measure in being cheap, frequent, and comparable, yet under search it behaves like a market price that participants can move. This helps explain why promotion reviews become confused: participants talk as though they were reading a quality statistic when they are often reading a price they have themselves been paying to raise, or a price quoted in a currency that changed overnight. A control that is cheap and used as an objective is a Goodhart instrument (Manheim and Garrabrant 2018). Real options theory supplies the decision rule that control theory alone does not: when the instrument is compromised, the organization should raise $F$ and exercise its option on the instrument rather than automate harder.

What is distinctive relative to other performative metrics, such as utilization targets or model-accuracy dashboards that overfit the test set, is speed. A prompt can be changed in an afternoon, and the metric that licenses the change can be queried, and versioned, the same afternoon, so the option premium competes with a cycle time measured in hours.

## 8.3. Boundary Conditions

The theory applies where three conditions hold jointly: the organization relies on a model-based instrument to license commitment; the instrument can be searched against or versioned; and commitment is costly to reverse. Where any condition fails, the theory reduces to familiar cases. A deterministic and fixed gold measure removes measurement-system risk and returns the problem to the classical option model. A judge that no one searches against removes the bias form but not the jump form. A fully reversible deployment removes the premium for waiting, although Section 5.1 argues that rollback in generative systems is rarely free because promoted policies contaminate future training logs.

## 8.4. Implications for Practice

Five commitments follow.

First, treat the judge as an asset with its own options. Version the judge and the rubric as artifacts alongside the prompt, and treat a quality movement that appears on the same day as a ruler diff as a Proposition 1 event until an inspection says otherwise.

Second, build the strike asset before it is needed. A calibration set with independent gold, or at minimum a human sample, is what makes recalibration possible after a vendor changes the judge behind a stable name.

Third, pin selectively. Pinning a judge that is informative preserves comparability; pinning a judge whose range across policies has collapsed preserves nothing (Proposition 3). Replace collapsed judges rather than freeze them.

Fourth, split evaluation items into development, holdout, and canary sets before the search begins, and write the canaries so that the cheap quote and the expensive inspection conflict on the cheat the organization fears. Log $J$ but gate on $G$, and ship a pilot first.

Fifth, set the intensity of judge-linked pay together with the power of inspection. Strong incentives on a gameable score need an independent check to be safe, and without one the incentive should be weak.

## 8.5. Limitations and Future Research

The paper is a theory-development contribution (Gregor 2006), and its limitations follow from that choice. The computational evidence is illustrative. The designed illustration is small and contains the cheat by construction, and the empirical check covers one benchmark with verifiable answers, one policy model, two judges, and one optimizer. It cannot estimate option prices or speak to traffic at organizational scale, and the model versions it used will change. The extended model of search, inspection, and pay is stylized: it assumes that an exploit always receives the top score, that a flagged release is blocked rather than replaced by the runner-up, that pay is linear in the judge score, and that cost and payoff parameters are exogenous. Its comparative statics are implications of the model and not findings.

Three directions for future research follow from the constructs. First, measurement-system risk invites measurement: organizations' release records can be examined for dashboard incidents that coincide with judge or rubric diffs, which would allow the frequency of the jump form, and the share of incidents misattributed to policy drift, to be estimated. A study of promotion episodes in organizations that already use model-based judges would establish whether the switch-the-ruler option is held, exercised, or absent in practice. Second, the model treats $V$ as a scalar, whereas organizations care about helpfulness, refusal quality, cost, and latency at once; a multi-attribute extension would make both the abandon option and the switch-the-ruler option attribute-specific. Third, the model treats the optimizer as a single agent. In firms, search is distributed across prompt engineers, vendor updates, and fine-tunes, and the contamination of $G$ by many teams is an open governance problem, because the strike asset of the switch-the-ruler option deteriorates when too many teams can see it.

# 9. Conclusion

Real options theory has always held that a rising quote is not a close. Generative AI maintenance adds a twist the theory did not anticipate: the quote is produced by a model that the organization is also optimizing against, and the model can be replaced without notice. This paper has named the resulting risk, measurement-system risk, distinguished its three forms of bias, collapse, and jump, and identified the option that manages it, the switch-the-ruler option, which is written on the instrument rather than on the project and without which the classical option menu collapses into NPV on the quote. The propositions specify when judge-based promotion commits too early and when the switch-the-ruler option is valuable, including the boundary that it is worthless for a collapsed judge. The illustrative evidence shows that the problem is conditional on the judge: search against a strong judge improved correctness, whereas a weak judge removed the gain and increased divergence between score and quality.

The research implication is that the IS option menu needs a row for the instrument. The practical implication is that promotion reviews should keep an options ledger rather than a single dashboard, version the judge as carefully as the policy, and build the inspection that makes recalibration possible before the vendor changes the ruler. Until that inspection exists, the conservative exercise rule is simple enough to state without a pricing kernel: if the inspection has not arrived, $F$ remains on the table, and it should be spent before the foundation is.

# References

Benaroch M (2002) Managing information technology investment risk: A real options perspective. *J. Management Inform. Systems* 19(2):43–84.

Benaroch M, Lichtenstein Y, Robinson K (2006) Real options in information technology risk management: An empirical validation of risk-option relationships. *MIS Quart.* 30(4):827–864.

Cobbe K, Kosaraju V, Bavarian M, Chen M, Jun H, Kaiser L, Plappert M, Tworek J, Hilton J, Nakano R, Hesse C, Schulman J (2021) Training verifiers to solve math word problems. Preprint, arXiv:2110.14168.

Dixit AK, Pindyck RS (1994) *Investment Under Uncertainty* (Princeton University Press, Princeton, NJ).

Fichman RG (2004) Real options and IT platform adoption: Implications for theory and practice. *Inform. Systems Res.* 15(2):132–154.

Gao L, Schulman J, Hilton J (2023) Scaling laws for reward model overoptimization. *Proc. 40th Internat. Conf. Machine Learn.*, Proceedings of Machine Learning Research, vol. 202 (PMLR).

Gregor S (2006) The nature of theory in information systems. *MIS Quart.* 30(3):611–642.

Holmström B, Milgrom P (1991) Multitask principal–agent analyses: Incentive contracts, asset ownership, and job design. *J. Law Econom. Organ.* 7(Special Issue):24–52.

Kerr S (1975) On the folly of rewarding A, while hoping for B. *Acad. Management J.* 18(4):769–783.

Manheim D, Garrabrant S (2018) Categorizing variants of Goodhart's law. Preprint, arXiv:1803.04585.

Myers SC (1977) Determinants of corporate borrowing. *J. Financial Econom.* 5(2):147–175.

Ouchi WG (1979) A conceptual framework for the design of organizational control mechanisms. *Management Sci.* 25(9):833–848.

Taudes A, Feurstein M, Mild A (2000) Options analysis of software platform decisions: A case study. *MIS Quart.* 24(2):227–243.

Tewari G (2026) Pilot early, commit late: A real-options model of enterprise AI adoption under rapid technological progress. Working paper.

Trigeorgis L (1996) *Real Options: Managerial Flexibility and Strategy in Resource Allocation* (MIT Press, Cambridge, MA).

Zheng L, Chiang WL, Sheng Y, Zhuang S, Wu Z, Zhuang Y, Lin Z, Li Z, Li D, Xing EP, Zhang H, Gonzalez JE, Stoica I (2023) Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. *Adv. Neural Inform. Processing Systems*, vol. 36 (Curran Associates, Red Hook, NY).

# Electronic Companion

This electronic companion accompanies the paper. Section EC.1 gives a stylized derivation of the exercise rule and of the value of the switch-the-ruler option, and Section EC.2 gives the proofs of the lemma and theorems on which the paper relies. Table, proposition, theorem, and equation numbers without a prefix refer to the main text, and the equations of this electronic companion carry the prefix EC.

## EC.1. A Stylized Derivation of the Exercise Rule

This appendix derives Equation (5) in a deliberately simple Gaussian setting. The aim is not to price the option but to show that the form of the rule, and the comparative statics behind Propositions 1 to 6, follow from standard Bayesian updating and optimal stopping. Throughout, $V$ denotes the incremental value of a candidate over the incumbent policy, so that promotion yields $V - I$.

*Setup.* The evaluator holds the prior $V \sim N(\mu, \tau^2)$. The judge reading, after subtracting the pinned intercept and rescaling by the slope, is $\hat{J} = V + u$, where $u$ is normal with variance $\sigma_a^2 = (\sigma^2 + \pi\nu^2)/a^2$, as in Equation (2). The term $\pi\nu^2$ is a moment-matched Gaussian approximation to ruler-jump risk: with probability $\pi$ the intercept shifts by an unknown amount with variance $\nu^2$. A single inspection $G = V + \eta$, with $\eta \sim N(0, \omega^2)$, can be bought at cost $c_G$ and arrives one period later, during which value is discounted by a factor $\delta < 1$.

*Step 1: posterior.* Precision weighting gives

$$\mathbb{E}[V \mid J, G] = s^2\left(\frac{\mu}{\tau^2} + \frac{\hat{J}}{\sigma_a^2} + \frac{G}{\omega^2}\right), \quad s^2 = (\tau^{-2} + \sigma_a^{-2} + \omega^{-2})^{-1} \tag{EC.1}$$

Before the inspection arrives, the same expression applies without the $G$ terms, with posterior variance $s_J^2 = (\tau^{-2} + \sigma_a^{-2})^{-1}$. A collapsed judge ($a \to 0$) has $\sigma_a^2 \to \infty$, so its reading receives no weight and $s_J^2 \to \tau^2$.

*Step 2: the decision before inspection.* Let $x = \mathbb{E}[V \mid J] - I$. The evaluator may reject (value 0), promote now (value $x$), or wait for $G$. Conditional on $J$, $\mathbb{E}[V \mid J, G]$ is normal with mean $\mathbb{E}[V \mid J]$ and variance $v = s_J^4/(s_J^2 + \omega^2)$, which is the reduction in posterior variance that the inspection delivers. Because $\mathbb{E}[\max(X, 0)] = m\Phi(m/\sqrt{v}) + \sqrt{v}\,\phi(m/\sqrt{v})$ for $X \sim N(m, v)$, the value of waiting is

$$W(x) = \delta\left[x\Phi(x/\sqrt{v}) + \sqrt{v}\,\phi(x/\sqrt{v})\right] - c_G \tag{EC.2}$$

*Step 3: the threshold.* The evaluator promotes now if and only if $x \ge \max\{0, W(x)\}$. Let $g(x) = x - W(x)$. Then $g'(x) = 1 - \delta\Phi(x/\sqrt{v}) \ge 1 - \delta > 0$, and $g$ runs from $-\infty$ to $+\infty$, so $g$ has a unique root $x^*$. The rule is therefore

$$\text{promote if } \mathbb{E}[V \mid J] - I \ge F, \quad F = \max\{0, x^*\}, \quad x^* = \delta\left[x^*\Phi(x^*/\sqrt{v}) + \sqrt{v}\,\phi(x^*/\sqrt{v})\right] - c_G \tag{EC.3}$$

This is Equation (5). The premium $F$ is positive whenever inspection is worth buying, that is, when $c_G < \delta\sqrt{v}\,\phi(0)$. Once the inspection has been observed and no further inspection is available, $v = 0$ and $F = 0$, so the rule reduces to $\mathbb{E}[V \mid J, G] \ge I$, in which $G$ enters through (EC.1).

*Step 4: comparative statics (Propositions 1 and 2).* Theorem 1 (Section EC.2) shows that $F$ increases with $v$ and $\delta$ and decreases with $c_G$, and that it increases with judge noise, jump risk, and jump size and decreases with the slope $a$, being largest for a collapsed judge. This is Proposition 2 and the jump component of Proposition 1. In units of the prior standard deviation of $V$ ($\tau = 1$, $\omega = 0.2$, $\delta = 0.95$, $c_G = 0.02$), with $a = 0.8$ the premium is 0.37, 0.62, and 0.83 for $\sigma = 0.4$, 0.7, and 1.2, and for $\sigma = 0.7$ it is 1.02 when the judge is nearly collapsed ($a = 0.01$). For $\sigma = 0.7$ and $\nu = 1.5$ it rises from 0.62 to 0.70 to 0.79 as $\pi$ rises from 0 to 0.1 to 0.3.

*Step 5: the value of the switch-the-ruler option (Proposition 3).* Write $F(\pi, \nu)$ for the premium in (EC.3) as a function of the jump parameters, holding the other parameters fixed. Pinning lowers $\pi$ to $\pi' \le \pi$, and recalibration against $G$ lowers $\nu$ to $\nu' \le \nu$, so that $\Omega = F(\pi, \nu) - F(\pi', \nu')$. Corollary 1 in Section EC.2 shows that $\Omega \ge 0$, that $\Omega$ is increasing in $\pi$ and $\nu$ for fixed $(\pi', \nu')$, and that $\Omega \to 0$ as $a \to 0$.

*Step 6: Proposition 4.* Let the optimizer produce a candidate under pressure $K$ by choosing a gaming effort $b \in [0, K]$ that raises the judge score one for one and costs true quality at rate $\gamma$, so that $V = V_0 - \gamma b$, with $V_0$ the legitimate gain drawn from a distribution $H$, and $J = aV_0 + (1 - a\gamma)b$. If $a\gamma < 1$, every maximizer of $J$ sets $b = K$. The NPV rule promotes whenever $aV_0 + (1 - a\gamma)K > c$, while $V < 0$ whenever $V_0 < \gamma K$, so the event that NPV promotes and $V < 0$ is the interval $(c - (1 - a\gamma)K)/a < V_0 < \gamma K$, whose endpoints move outward as $K$ grows. Its probability is therefore nondecreasing in $K$ and tends to one if $H$ has full support. Because $G$ contains no gaming term, a rule that conditions on $G$, as Equation (5) does, promotes such a candidate only through the measurement error $\eta$.

*Step 7: Propositions 5, 6, and 1.* For Proposition 5, let the holdout contain item classes $k$ with weights $w_k$ and gold-score differences $\Delta G_k$ between the cheat and the incumbent. The mean difference $\sum_k w_k \Delta G_k$ is positive even though $\Delta G_c < 0$ on the refusal class $c$ whenever $w_c|\Delta G_c| < \sum_{k \ne c} w_k \Delta G_k$. For Proposition 6, if the canary score of the cheat is measured with noise $\omega_c$ around its true value $g_c$ and the battery has a floor $\theta$, the cheat is stopped with probability $\Phi((\theta - g_c)/\omega_c)$, which rises with the separation $\theta - g_c$ that the canary is built to create and equals one with deterministic gold, as in the laboratory ($g_c = 0.55$, $\theta = 0.70$). For Proposition 1, when the judge changes between $t - k$ and $t$, the naive increment $aV + (b_t - b_{t-k})$ makes a false promotion of a candidate with $V \le 0$ more likely as $\pi$ and the size of the jump rise, and re-estimating $(a, b)$ against $G$ removes the systematic part of the jump and leaves the residual variance, which enters $F$ through (EC.3).

*Scope.* The derivation is one-shot, Gaussian, and allows a single inspection. A continuous-time version would replace (EC.3) with a closed-form multiple of the investment cost $I$ but is not derived here. When inspection cannot be created at any finite cost worth paying ($c_G \ge \delta\sqrt{v}\,\phi(0)$), $F = 0$ and the options rule reduces to Bayesian NPV on the shrunk posterior mean, which still differs from NPV on raw judge movement but no longer calls for waiting. In that case $\Omega = 0$ as well: without a strike asset, the recalibration part of the switch-the-ruler option cannot be exercised, and pinning matters only through the posterior weight on $J$.

## EC.2. Proofs

This appendix collects the lemma, theorems, and corollary on which the option model and its extensions rely. Each statement was also checked numerically in the scripts that accompany the paper. Notation follows Section EC.1 for the Gaussian exercise rule and the main text for the model of search, exploitation, and pay.

**Lemma 1 (expected maximum).** Let $X_1, X_2, \ldots$ be independent draws from a distribution with distribution function $\Lambda$ and finite mean, and for real $n > 0$ let $m(n) = \int_0^\infty (1 - \Lambda(x)^n)\,dx - \int_{-\infty}^0 \Lambda(x)^n\,dx$. For integer $n$, $m(n)$ is the expected maximum of $n$ draws. The function $m$ is strictly increasing and strictly concave, $m(n+1) - m(n) = \int \Lambda(x)^n(1 - \Lambda(x))\,dx$, and $m(n) \to \infty$ if $\Lambda(x) < 1$ for all $x$.

*Proof.* For integer $n$, the first claim is integration by parts of $\int x\,d(\Lambda^n)$. Differentiating under the integral sign, which dominated convergence justifies because the mean is finite, gives $m'(n) = -\int \Lambda^n \ln\Lambda\,dx > 0$ and $m''(n) = -\int \Lambda^n (\ln\Lambda)^2\,dx < 0$, where the integrals run over the set on which $0 < \Lambda < 1$. Subtracting $m(n)$ from $m(n+1)$ gives the difference formula. If $\Lambda(x) < 1$ for all $x$, then $1 - \Lambda(x)^n$ increases to one for every $x \ge 0$, and monotone convergence gives $m(n) \to \infty$. ∎

**Theorem 1 (exercise rule).** In the Gaussian model of Section EC.1: (i) $g(x) = x - W(x)$ is strictly increasing, so its root $x^*$ is unique and the evaluator promotes if and only if $x \ge F = \max\{0, x^*\}$; (ii) $x^* > 0$ if and only if $c_G < \delta\sqrt{v}\,\phi(0)$; (iii) where $x^* > 0$, $F$ is strictly increasing in $v$ and $\delta$ and strictly decreasing in $c_G$; (iv) $v$ is strictly increasing in $s_J^2$, $s_J^2$ is strictly increasing in $\sigma_a^2$, and $\sigma_a^2$ increases with $\sigma^2$, $\pi$, and $\nu^2$ and decreases with $a$. Hence $F$ increases with judge noise $\sigma$, jump risk $\pi$, and jump size $\nu$, and it decreases with the slope $a$.

*Proof.* (i) By (EC.2), $W'(x) = \delta\Phi(x/\sqrt{v}) \in (0, \delta)$, so $g'(x) \ge 1 - \delta > 0$. Since $W$ is bounded below by $-c_G$ and grows at most linearly, $g(x) \to -\infty$ as $x \to -\infty$ and $g(x) \to +\infty$ as $x \to +\infty$. The root is therefore unique. The evaluator promotes if and only if $x \ge 0$ and $x \ge W(x)$, and the second condition is $x \ge x^*$. (ii) $g(0) = c_G - \delta\sqrt{v}\,\phi(0)$, and $g$ is increasing. (iii) Where $x^* > 0$, $\partial W/\partial\sqrt{v} = \delta\phi(x/\sqrt{v}) > 0$, $\partial W/\partial\delta = \mathbb{E}[X^+] > 0$, $\partial W/\partial c_G = -1$, and $1 - \partial W/\partial x = 1 - \delta\Phi(x^*/\sqrt{v}) > 0$, so the implicit function theorem applied to $g(x^*) = 0$ gives the signs. (iv) Differentiating $v = s_J^4/(s_J^2 + \omega^2)$ gives $dv/ds_J^2 = s_J^2(s_J^2 + 2\omega^2)/(s_J^2 + \omega^2)^2 > 0$. Because $s_J^2 = (\tau^{-2} + \sigma_a^{-2})^{-1}$ and $\sigma_a^2 = (\sigma^2 + \pi\nu^2)/a^2$, the remaining monotonicity is immediate. ∎

**Corollary 1 (value of the switch-the-ruler option).** In the Gaussian model of Section EC.1, let $\Omega = F(\pi, \nu) - F(\pi', \nu')$ with $\pi' \le \pi$ and $\nu' \le \nu$, and suppose inspection is worth buying at $(\pi', \nu')$. Then (i) $\Omega \ge 0$; (ii) for fixed $(\pi', \nu')$, $\Omega$ is nondecreasing in $\pi$ and $\nu$, and strictly increasing wherever $x^*(\pi, \nu) > 0$; (iii) $\Omega \to 0$ as $a \to 0$.

*Proof.* (i) and (ii): $F$ depends on $(\pi, \nu)$ only through $\sigma_a^2 = (\sigma^2 + \pi\nu^2)/a^2$, which is nondecreasing in $\pi$ and $\nu$. By Theorem 1(iii)–(iv), $F = \max\{0, x^*\}$ is nondecreasing in $\sigma_a^2$, and strictly increasing where $x^* > 0$. Since $\pi\nu^2 \ge \pi'\nu'^2$, $F(\pi, \nu) \ge F(\pi', \nu')$, which is (i); holding the second term fixed, (ii) follows from the monotonicity of the first. (iii) As $a \to 0$, both $\sigma_a^2(\pi, \nu)$ and $\sigma_a^2(\pi', \nu')$ tend to infinity, so $s_J^2 \to \tau^2$ and $v \to \tau^4/(\tau^2 + \omega^2)$ in both terms. Because $x^*$ is the unique root of $g$, which is continuous in $v$, and $g'$ is bounded below by $1 - \delta > 0$, $x^*$ is continuous in $v$, so both premia converge to the same limit and their difference tends to zero. ∎

**Theorem 2 (search depth).** Let $c_s > 0$ and $\lambda = -\ln(1 - \xi)$. Treat $N$ as continuous on $[1, \infty)$. (i) $U(N)$ in (6) has a unique maximizer $N^*$, which is the point at which $U'(N)$ changes sign from positive to negative, or $N = 1$ if $U'(1) \le 0$; on the integers $U$ is unimodal. (ii) $N^*$ is decreasing in $\xi$ and $d$, and with inspection of power $\zeta$, $d$ is replaced by $(1 - \zeta)d$, so $N^*$ is increasing in $\zeta$. (iii) Inspection of cost $c_G$ is worth buying if and only if $\zeta d[1 - (1 - \xi)^N] > c_G$, that is, if and only if $N \ge N_c$ in (7).

*Proof.* (i) Differentiating (6), $U'(N) = e^{-\lambda N}h(N) - c_s$ with $h(N) = \rho s\,m'(N) - \lambda(\rho s\,m(N) + d)$. By Lemma 1, $m'$ is positive and strictly decreasing and $m$ is increasing, so $h$ is strictly decreasing and tends to a negative limit. Where $h > 0$, $e^{-\lambda N}h$ is a product of positive, strictly decreasing functions and is strictly decreasing; where $h \le 0$, $U' < 0$. Hence $U'$ has at most one zero, and it changes sign from positive to negative there. (ii) At an interior optimum $e^{-\lambda N}h = c_s > 0$, so $h > 0$. Then $\partial U'/\partial d = -\lambda e^{-\lambda N} < 0$ and $\partial U'/\partial\lambda = e^{-\lambda N}[-Nh - (\rho s\,m + d)] < 0$, while $U'$ is strictly decreasing in $N$ at the root. The implicit function theorem gives the comparative statics, with $\lambda$ increasing in $\xi$. (iii) The gain from inspection is the avoided loss $\zeta d$ times the probability that an exploit is shipped, and solving for $N$ gives (7). ∎

**Theorem 3 (the team's best response).** Fix $N$, $\zeta$, and $\Gamma_N = (1 - \zeta)\Delta - \zeta\sigma_J m_N$, and for $N = 1$ assume $\kappa > \beta\Delta$. (i) The team's best response is $e = 0$ if $\Gamma_N \le 0$ and otherwise the unique root in $(0, 1)$ of $\kappa e = \beta\Gamma_N(1 - e)^{N-1}$. (ii) Where $\Gamma_N > 0$, the root is strictly decreasing in $N$, $\zeta$, and $\kappa$ and strictly increasing in $\beta$ and $\Delta$. (iii) At the root, $1 - Q = \kappa e(1 - e)/(\beta\Gamma_N)$. (iv) If $\zeta = 0$, then $e^* \to 0$ and $Q \to 1$ as $N \to \infty$. (v) If $\zeta > 0$, there is a finite $N_d$ such that $e^* = 0$ for all $N \ge N_d$.

*Proof.* (i) For given $N$, the team's utility in $e$ is $\text{const} + \beta Q(e)\Gamma_N - N\kappa e^2/2$ with $Q(e) = 1 - (1 - e)^N$. If $\Gamma_N \le 0$ it is strictly decreasing in $e$. If $\Gamma_N > 0$ it is strictly concave, and its first-order condition is the stated equation. The left side $\kappa e$ is increasing from zero, and the right side is decreasing from $\beta\Gamma_N > 0$ to zero (or to $\beta\Gamma_N < \kappa$ when $N = 1$), so the root is unique and lies in $(0, 1)$. (ii) Write the equation as $H(e) = \kappa e - \beta\Gamma_N s^{N-1} = 0$ with $s = 1 - e$. Then $H_e = \kappa + \beta\Gamma_N(N - 1)s^{N-2} > 0$, $H_N = \beta s^{N-1}[\zeta\sigma_J m'(N) + \Gamma_N\ln(1/s)] > 0$ by Lemma 1, $H_\zeta = \beta s^{N-1}(\Delta + \sigma_J m_N) > 0$, $H_\kappa = e > 0$, $H_\beta = -\Gamma_N s^{N-1} < 0$, and $H_\Delta = -\beta(1 - \zeta)s^{N-1} < 0$, and the implicit function theorem gives the signs. (iii) The first-order condition gives $s^{N-1} = \kappa e/(\beta\Gamma_N)$, so $(1 - e)^N = s\cdot\kappa e/(\beta\Gamma_N)$. (iv) If $\zeta = 0$, $\Gamma_N = \Delta$ is constant. Suppose $e^* \ge \varepsilon > 0$ along a subsequence. Then $\kappa\varepsilon \le \kappa e^* = \beta\Delta(1 - e^*)^{N-1} \le \beta\Delta(1 - \varepsilon)^{N-1} \to 0$, a contradiction, so $e^* \to 0$, and (iii) gives $1 - Q \to 0$. (v) $\Gamma_N \le 0$ if and only if $\sigma_J m_N \ge (1 - \zeta)\Delta/\zeta$, which holds for large $N$ because $m_N \to \infty$ by Lemma 1. ∎

**Theorem 4 (the team's equilibrium).** Let $\Gamma_0 = (1 - \zeta)\Delta - \zeta\sigma_J m_N$, $\beta_d = \psi\Gamma_0/(\theta^2\zeta)$, and $\beta_u = \beta_d/(1 - \zeta)$, and for $N = 1$ assume $\kappa > \beta\Delta$. (i) For every $e$ the team's best response in honest effort is unique and equals $a(e) = \beta\theta(1 - \zeta Q(e))/\psi$, and for every $a$ its best response in exploit effort is unique and given by Theorem 3 with $\Gamma(a) = (1 - \zeta)\Delta - \zeta(\theta a + \sigma_J m_N)$. (ii) The profile $e = 0$, $a = \beta\theta/\psi$ is an equilibrium if and only if $\beta \ge \beta_d$. (iii) If $\psi\kappa > \beta^2\theta^2\zeta^2 N$, the equilibrium is unique. (iv) If $\beta \ge \beta_u$, the equilibrium is unique and equals $e = 0$. (v) An equilibrium always exists. (vi) Outside the conditions of (iii) and (iv), several equilibria can coexist.

*Proof.* (i) The team's utility is strictly concave in $a$ with first-order condition $\beta\theta(1 - \zeta Q) = \psi a$, and the exploit part follows from Theorem 3 with the stake $\theta a + \sigma_J m_N$. (ii) At $e = 0$ we have $Q = 0$ and $a = \beta\theta/\psi$, so $\Gamma = \Gamma_0 - \beta\theta^2\zeta/\psi$. By Theorem 3, $e = 0$ is a best response if and only if $\Gamma \le 0$, that is, if and only if $\beta \ge \beta_d$. (iii) Let $\tilde{e}(\Gamma)$ denote the best response of Theorem 3 as a function of $\Gamma$, with $\tilde{e} = 0$ for $\Gamma \le 0$. It is continuous, and where $\Gamma > 0$ its derivative is $\beta s^{N-1}/[\kappa + \beta\Gamma(N - 1)s^{N-2}] \le \beta/\kappa$, so $\tilde{e}$ is $(\beta/\kappa)$-Lipschitz. Because $\Gamma(a)$ has slope $-\zeta\theta$, the map $a \mapsto \tilde{e}(\Gamma(a))$ is $(\beta\zeta\theta/\kappa)$-Lipschitz. The map $e \mapsto a(e)$ is $(\beta\theta\zeta N/\psi)$-Lipschitz because $Q' \le N$. The composition $T(e) = \tilde{e}(\Gamma(a(e)))$ maps $[0, 1]$ into itself and is Lipschitz with constant $\beta^2\theta^2\zeta^2 N/(\kappa\psi)$, which is below one under the stated condition. By the contraction mapping theorem it has a unique fixed point, and the equilibria are exactly the fixed points of $T$. (iv) For every $e$, $\Gamma(a(e)) = \Gamma_0 - (\beta\theta^2\zeta/\psi)(1 - \zeta Q(e)) \le \Gamma_0 - (\beta\theta^2\zeta/\psi)(1 - \zeta) \le 0$ when $\beta \ge \beta_u$, so $T \equiv 0$ and its only fixed point is zero. (v) The map $T$ is continuous and maps $[0, 1]$ into itself, so it has a fixed point by the intermediate value theorem. (vi) Take $N = 5$, $\zeta = 0.6$, $\beta = 6.5$, $\sigma_J = 1$, $\Delta = 2.5$, $\kappa = 1.5$, $\psi = 2$, and $\theta = 0.4$. Then $\beta_d = 6.3$ and $\beta_u = 15.7$, and $T(e) - e$ has three zeros, at $e = 0$, 0.0147, and 0.2044. The slope of $T$ is 0 at the first, 3.4 at the second, and 0.32 at the third, so the first and the third are stable. The condition of (iii) fails ($\psi\kappa = 3$, whereas $\beta^2\theta^2\zeta^2 N = 12.2$), and $\beta < \beta_u$. ∎

**Theorem 5 (optimal pay).** (i) For every equilibrium, $S \le S^{FB}$, with equality if and only if $e = 0$ and $a = g/\psi$. (ii) The first best is implementable as an equilibrium if and only if $\beta_d \le g/\theta$, and the equilibrium at $\beta = g/\theta$ is then unique if $g/\theta \ge \beta_u$ or $\psi\kappa > g^2\zeta^2 N$. (iii) If $\zeta = 0$, the equilibrium is unique for every $\beta$, $S(\beta)$ is strictly decreasing on $[g/\theta, \infty)$, every maximizer lies in $[0, g/\theta)$, and if (15) holds then every maximizer is strictly positive.

*Proof.* (i) For any $a$ and $e$, $(1 - Q)ga - (\psi/2)a^2 \le (1 - Q)^2 g^2/(2\psi) \le g^2/(2\psi)$, with equality only if $Q = 0$ and $a = g/\psi$. Also $(1 - Q)\rho s\,m_N \le \rho s\,m_N$, and the remaining terms of (14) are nonpositive. (ii) With $e = 0$ the team's honest effort is $\beta\theta/\psi$, which equals $g/\psi$ only at $\beta = g/\theta$. By Theorem 4(ii), $e = 0$ is an equilibrium at that $\beta$ if and only if $\beta_d \le g/\theta$, and uniqueness follows from Theorem 4(iii) and (iv), noting that the condition of (iii) at $\beta = g/\theta$ is $\psi\kappa > g^2\zeta^2 N$. (iii) With $\zeta = 0$ there is no feedback, $a = \beta\theta/\psi$, and $e$ is the unique root of Theorem 3. Because $\kappa e = \beta\Delta(1 - e)^{N-1}$, the implicit function theorem gives $e'(\beta) = \Delta s^{N-1}/[\kappa + \beta\Delta(N - 1)s^{N-2}] > 0$. Differentiating (14) gives $dS/d\beta = S_a\theta/\psi + S_e e'(\beta)$ with $S_a = (1 - Q)g - \psi a$ and $S_e = -Q'[ga + \rho s\,m_N + d] - N\kappa e$, where $Q' = N(1 - e)^{N-1} > 0$. For $\beta \ge g/\theta$ we have $a \ge g/\psi$, so $S_a \le -Qg \le 0$, and $S_e < 0$ whenever $e > 0$, so $S$ is strictly decreasing there. Since $S$ is continuous on the compact set $[0, g/\theta]$, a maximizer exists and lies in $[0, g/\theta)$. At $\beta = 0$, $a = e = 0$, $S_a = g$, $S_e = -N(\rho s\,m_N + d)$, and $e'(0) = \Delta/\kappa$, so $S'(0) = g\theta/\psi - N(\rho s\,m_N + d)\Delta/\kappa$, which is positive if and only if (15) holds, and then the maximizer is positive. ∎
