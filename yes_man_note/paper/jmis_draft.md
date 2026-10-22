# Deference or Noise? Separating Stance Sensitivity from Instability in AI Reviewers and What It Costs

*Working draft for the Journal of Management Information Systems. Sections 1–5 (introduction, literature, theory, hypotheses, method) are written. Sections 6–8 are skeletons: every number marked [PENDING] needs data that has not been collected. References marked † were added in this draft and must be checked against the source (title, venue, pages) before submission. JMIS is double-blind: remove author-identifying text and self-references before submitting, and keep the abstract at or below 150 words.*

---

## Abstract

Organizations ask AI systems to review decisions that a requester has already leaned toward. When the answer follows the requester's stated view, this is read as sycophancy, but the change can also reflect run-to-run instability, sensitivity to any added sentence, or reasonable treatment of the stance as evidence. We separate these with a baseline-corrected measure of stance sensitivity and with gradients in the stance's claimed evidence and in the requester's disclosed accuracy, and we show how the corrected quantity enters the value of delegated review, (1 − s)(a − π). Across fourteen language models, [PENDING: share of raw deference that survives correction; whether the gradients indicate deference or evidence-weighing]. We offer an audit protocol that a firm can run on its own decisions and state what it cannot establish.

**Keywords:** AI delegation, sycophancy, AI auditing, value of information, large language models, measurement

---

## 1. Introduction

A growing share of organizational review is delegated to AI systems that see the decision-maker's leaning along with the evidence. A compliance officer asks whether a request meets policy after saying she thinks it does. An engineer asks a model to check a release he already believes is ready. A controller asks whether a report is consistent with the ledger, having drafted it. In each case the principal buys information she does not already hold, and the purchase is worth making only if the review depends on the evidence and not on the leaning she has already disclosed.

The failure that worries practitioners and researchers is that the AI agrees. Models trained on human approval tend to endorse a stated view more often than the evidence warrants (Perez et al. 2022; Sharma et al. 2023), and challenging a correct answer can make a model abandon it (Laban et al. 2023†). That reading is natural, and it is already familiar. It is also not yet a measurement. When a model's answer changes after a user states a view, at least four different things could have happened:

1. *Instability.* The model gives different answers to the same question across draws, so some answers change with no stance at all.
2. *Sensitivity to added text.* Any additional sentence, relevant or not, shifts the answer (Sclar et al. 2024†).
3. *Evidence-weighing.* The stance carries information, such as a claimed colleague review or an accuracy record, and a model that gives it some weight is behaving sensibly, though not necessarily well.
4. *Deference.* The report follows the stance because it is the stance.

Only the fourth is the yes-man of Prendergast (1993), and only the fourth justifies paying for a reviewer with integrity. Prior measurements, including our own earlier work [ANONYMIZED], report the sum of all four. The omission matters for management decisions in two ways. A firm that treats instability as deference will buy a more expensive "non-sycophantic" model and see no improvement in decision quality. A firm that treats deference as evidence-weighing will keep a reviewer that tells it what it already believes.

This paper makes three contributions. First, we give a measurement design that separates the four mechanisms: replicated stance-free answers estimate instability, a length-matched neutral sentence estimates the effect of any added text, a gradient in the stance's claimed evidence and in the requester's disclosed accuracy discriminates deference from evidence-weighing, and a rotation of the option letters rules out position effects. Second, we extend the value-of-review function for a deferential delegate with two results that the measurement needs: the closed form with a measured conditional deference is biased by exactly the covariance between ability and deference across stems (Proposition 5), and a delegate that weights the stance at the rate that is rational for the requester's accuracy loses nothing, so deference is a cost only to the extent that it exceeds that rate (Proposition 6). Third, we apply the design to fourteen models in five families on a new bank of 300 audited decision items, and we report what share of the conventionally measured deference survives correction, whether the remainder responds to claimed evidence, and what this does to the ranking and valuation of reviewers by their stance-free ability.

We study models, not people, and the settings are synthetic decision items with one correct answer. We claim a measurement procedure and its application, not a theory of why models defer, and not procurement prices.

---

## 2. Related Literature

### 2.1 Delegation, advice, and the value of information

The agency literature treats delegation as the problem of securing an agent's effort and judgment when interests differ (Jensen and Meckling 1976; Eisenhardt 1989). Work on authority and communication shows how allocating decision rights shapes what information reaches the decision-maker (Aghion and Tirole 1997; Dessein 2002), and work on strategic communication shows that advice is informative only to the degree that the adviser's incentives are aligned (Crawford and Sobel 1982). Prendergast (1993) is the closest antecedent: when a worker's pay depends on matching the boss's information, the worker reports what the boss already believes, and the organization loses the worker's information. An AI delegate has no wage and no interest, but its reports can depend on the principal's visible preference through training, and the informational structure is the same. The comparison of information sources follows Blackwell (1953), which orders experiments by their value to every decision-maker, and which we use to show that a requester who knows how the delegate behaves never gains from deference.

### 2.2 Human–AI collaboration and reliance in information systems

Information systems research on delegation to and from agentic artifacts (Baird and Maruping 2021) and on the cognitive challenges of delegating to AI (Fügener et al. 2022) concerns how people decide what to hand over and whether they rely on the result. The behavioral literature on reliance describes both under-reliance on algorithms (Dietvorst et al. 2015†) and over-reliance (Logg et al. 2019†; Parasuraman and Riley 1997†), and the trust literature stresses that reliance should track actual reliability (Lee and See 2004†). In the economics of AI, Agrawal et al. (2019) separate prediction from judgment and argue that the value of prediction depends on the complementary judgment of the human; we study a case in which the AI's own judgment is moved by the human's stated view. A buyer choosing among reviewers typically sees only stance-free benchmark accuracy, which is a measure of ability, and the sociotechnical view of IS (Sarker et al. 2019) suggests that this is exactly the kind of cue that misleads when a property of the social setting, here the visible preference of the requester, matters. Supervisory guidance on model risk management requires validation that provides effective challenge (Board of Governors of the Federal Reserve System 2011), which is the property a deferential reviewer lacks.

### 2.3 Sycophancy, instability, and prompt sensitivity in language models

The computer-science literature documents sycophancy in models trained with human feedback (Ouyang et al. 2022; Perez et al. 2022; Sharma et al. 2023) and finds it can be reduced by targeted data (Wei et al. 2023†). It also documents three phenomena that the sycophancy label can absorb. First, answers vary across runs even when settings are meant to be deterministic (Atil et al. 2024†). Second, outputs change with trivial changes to a prompt (Sclar et al. 2024†) and with the position of the correct option (Zheng et al. 2024†). Third, stated views can bias answers without the model acknowledging them (Turpin et al. 2023†), which is evidence of influence but not of its mechanism. Scaling studies (Kaplan et al. 2020; Hoffmann et al. 2022) concern capability, and larger models are more able, but whether larger models defer less is an empirical question that earlier tests answer in the opposite direction in some settings (Perez et al. 2022).

### 2.4 The gap this paper fills

The sycophancy literature measures how often an answer changes under a stated view; the delegation literature supplies the value of information and the yes-man structure. What is missing is a decomposition of the observed change that a buyer can apply, and a value-of-review function that uses the right component. Without the decomposition, ability-based rankings are read as safe, deference as a defect to be priced, and a flip as sycophancy. With it, the buyer can ask three separate questions: how unstable is this reviewer, does it respond to evidence the requester has actually provided, and how much of the remainder is deference.

---

## 3. Theory: A Model of Delegated Review with a Deferential Delegate

### 3.1 Setup

A requester has a stated preference for action S in a binary decision and earns 1 if the final action is correct and 0 otherwise. S is correct with probability π, the accuracy of the requester's preference (A1). Without review she acts on S and earns π. When the delegate judges on evidence it answers correctly with probability a, independently of whether S is correct (A2, ability). The delegate sees the stance. If S is wrong it reports S with probability s_w regardless of the evidence; if S is right, with probability s_r; otherwise it reports its evidence-based answer (A3, deference). Its integrity is 1 − s. The case s_w = s_r = s is the pure yes-man. A naive requester adopts the delegate's report (A4); a sophisticated requester who knows (a, s_w, s_r, π) updates. Costs and prices are set aside until Proposition 8.

### 3.2 Propositions

**Proposition 1 (value of review).** For the naive requester, V(π) = (1 − π)(1 − s_w)a − π(1 − s_r)(1 − a). With s_w = s_r = s, V = (1 − s)(a − π). The value is linear in π and is zero at π* = (1 − s_w)a / [(1 − s_w)a + (1 − s_r)(1 − a)], which equals a in the symmetric case.

**Proposition 2 (complementarity).** In the symmetric case, with integrity i = 1 − s, V = i(a − π), so the cross-partial derivative with respect to a and i is one. Neither ability nor integrity is valuable alone.

**Proposition 3 (sign of the value of integrity).** dV/ds = −(a − π). Deference lowers the naive requester's value if and only if the delegate is more accurate than her preference, a > π. If a < π, deference raises her value because it moves the outcome back toward her prior. Integrity matters exactly where delegation is worth doing.

**Proposition 4 (overstatement).** The share of the ability-based value a − π that is lost to deference is s, whatever π. A buyer who values a delegate by a − π overstates its value by the factor 1/(1 − s).

**Proposition 5 (heterogeneity across stems).** Let stems i differ in ability a_i and deference s_i (symmetric within a stem), with ā and s̄ the means. Define the conditional deference measured on stems the delegate would answer correctly, s_c = E[a_i s_i]/ā. Then the true value is V(π) = E[(1 − s_i)(a_i − π)] = ā(1 − s_c) − π(1 − s̄), and the closed form evaluated at the measured conditional deference, V_cf = (1 − s_c)(ā − π), differs from it by

V(π) − V_cf = π(s̄ − s_c) = −π Cov(a_i, s_i)/ā.

If deference is concentrated on stems where the delegate is weak (Cov < 0), the closed form understates the value of review, because deferring where one's own answer is unreliable costs little. The understatement grows with π.

**Proposition 6 (rational stance-weighting costs nothing).** Let the delegate observe a signal x with likelihood ratio ℓ(x) = P(x | S correct)/P(x | S wrong) and the stance. Let r* be the report that is S if and only if ℓ(x) · π/(1 − π) ≥ 1 and not S otherwise. Then among all report rules that depend on (x, stance), r* maximizes the naive requester's accuracy. Any rule that reports S on a larger set of signals, a stance weight above π/(1 − π), has strictly lower accuracy unless that set has probability zero. Deference is therefore a cost only to the extent that it exceeds the weight that is rational for the requester's accuracy π. The delegate cannot observe π, so a delegate that weights the stance at a fixed rate is optimal for at most one requester accuracy.

**Proposition 7 (sophisticated requester).** If the requester knows the parameters and updates, her value is weakly decreasing in s, and strictly where the report would change her decision. The benefit of deference in Proposition 3 therefore belongs to the naive requester alone. The report of a deferential delegate is a garbling of the report of a non-deferential one, which Blackwell (1953) ranks as less informative for every decision-maker.

**Proposition 8 (implied prices).** Suppose the process can hide the stance from the delegate at a cost δ in ability, so that a blinded delegate does not defer and yields a − δ − π. Blinding is better if and only if δ < s(a − π); it never helps when a ≤ π. The same expression, s(a − π), is the largest amount of value a buyer who observes s should be willing to pay for a non-deferential version of the same delegate, in units of the requester's accuracy.

**Proposition 9 (ranking by ability).** For two delegates with a_1 > a_2, V_1 − V_2 = N + π(s_1 − s_2), where N = (1 − s_1)a_1 − (1 − s_2)a_2. Ranking by ability is value-optimal for every prior in [0, 1] if and only if (1 − s_1)a_1 ≥ (1 − s_2)a_2 and (1 − s_1)(1 − a_1) ≤ (1 − s_2)(1 − a_2) for every such pair.

Proofs are in Appendix A. Propositions 1–4 and 7–9 restate the structure of our earlier work [ANONYMIZED]; Propositions 5 and 6 are new and are what the measurement design in Section 5 needs.

### 3.3 What the model implies for measurement

The model separates what an experimenter can observe from what the buyer needs. The buyer needs s, the probability that the report follows the stance whatever the evidence. An experimenter observes, for stems the delegate answers correctly without a stance, the share whose answer changes to the stance-endorsed option under the stance. That share contains the baseline rate at which answers change to that option with no stance at all (instability and any-sentence effects), plus the stance effect. Proposition 6 adds that part of the stance effect may be rational. Sections 4 and 5 turn these two observations into hypotheses and a design.

---

## 4. Hypotheses

Let ν be the rate at which a stance-free replicate answers the stance-endorsed option among stems answered correctly in a reference run; ρ the same rate after a length-matched neutral sentence; f(e) the rate under a stance at claimed-evidence level e; and s* = f(e*) − ρ the baseline-corrected stance effect at a primary level e*. All are shares of the same conditional set of stems.

**H1 (instability).** The conventionally measured conditional deference exceeds the corrected effect, f(e*) > s*, because ρ > 0. The share removed is largest for small, unstable models.

**H2 (scale).** Within each family the larger model has higher ability and a lower corrected stance effect s*. (Our earlier uncorrected result was the same direction in all five families; H2 asks whether it survives correction.)

**H3 (deference versus evidence-weighing).** Two accounts make opposite predictions on the gradients.
- *Deference:* f(e) is flat in the claimed evidence e, flat in the disclosed requester accuracy, and does not fall when the stance is explicitly disclaimed ("I have no evidence for this").
- *Evidence-weighing:* f(e) rises with e, rises with the disclosed accuracy, and falls under the disclaimer.
We register both predictions and report the slopes, without a directional hypothesis about which account describes which model.

**H4 (heterogeneity).** Deference is higher on stems the model finds harder, Cov(a_i, s_i) < 0, so the closed form with measured conditional deference understates the model-free value of review (Proposition 5).

**H5 (ranking).** Ranking models by stance-free ability preserves the order of value in most pairs but overstates the level by the factor 1/(1 − s*), where s* now replaces the uncorrected conditional deference.

---

## 5. Method

### 5.1 Items

The item bank has 300 decision items, 50 in each of six domains: the expected net value of projects; an expense policy with a daily cap, a percentage-and-cap exception, and an excluded receipt; an invoice with a credit applied before tax and a tax-exempt line; an eligibility score with components missing from the file; a late fee under a versioned rule set by invoice date; and a purchase quantity under unit conversion, dilution, and a waste allowance. Each domain has three difficulty tiers that add rule steps and narrow the margin between right and wrong. Every item has three options with fixed roles: the correct action (gold), an unsupported action that the stance endorses, and a third option. The unsupported option is the result of a named plausible mistake, so a stance toward it is tempting and not absurd. Letters are assigned to roles by a hash of the item identifier and are identical across channels.

All arithmetic is exact. Each key was re-derived by a second program that parses the rendered stem, and the two agree on all items. Every stance sentence for every item was rendered and checked for grammar. Two independent human reviewers answered all items blind to the key [PENDING: agreement with the key and with each other; disagreements resolved and items revised or removed]. The bank was frozen before the main run [PENDING: file hash and date].

### 5.2 Channels

Every model answers the same item set in the following channels, each with the same system prompt asking for a single letter.
- **N (stance-free).** The stem and options only; five independent completions per item. The first is the reference run.
- **NEU (neutral sentence).** One sentence unrelated to the decision, drawn from a pool of ten and matched in word count to that item's stance sentence.
- **ST (stance).** One sentence supporting the unsupported action (against the evidence) or the gold action (for it), at four claimed-evidence levels: a stated preference, a weak claimed support, a strong claimed support, and a stated preference with an explicit disclaimer of evidence.
- **ACC (disclosed accuracy).** A stated preference against the evidence plus a statement of the requester's track record ("In similar past cases, a preference like this has turned out to be correct X% of the time"), with X at 20, 50, and 80. The sentence has the same length at every X, so the slope of the follow rate in X is free of any length effect. An evidence-weighing delegate should follow more as X rises (Proposition 6); a deferential one should not.
- **ROT (rotation).** The N and primary stance prompts with the option letters permuted twice, to test for position effects.

### 5.3 Models

Fourteen models in five families: ten open-weight instruction-tuned models (Qwen2.5 7B and 72B; Llama-3.1 8B and 70B; Gemma-3 4B, 12B, and 27B; Ministral 3B, 8B, and 14B) and four commercial tiers of one vendor (Haiku 4.5, Sonnet 5.5, Opus 5.5, Fable 5.1), all queried through one aggregator with the same prompt, a 512-token limit, and a sampling temperature of 1.0 wherever the model accepts the argument [PENDING: confirm which tiers reject it]. The serving provider and the model identifier returned by the interface are recorded for every call, and any model answered by more than one provider is flagged. Tiers within a family are an ordering, not independent variation in size: families differ in generation and post-training, and we cannot control hardware or quantization.

### 5.4 Estimation

All quantities are shares of stems, with the conditional set defined by a correct answer in the reference run, which selects the same stems for every channel. We report ability a (stance-free accuracy over all replicates); ν; ρ; f(e) at each level; s*; the share of the raw conditional deference removed by the baseline, 1 − s*/f(e*); the slope of f across the three evidence levels; the effect of the disclaimer; and the rescue rate under a right stance, defined on stems the model misses without a stance, which confounds direction with difficulty and is read together with the gradients. The model-free value of review for a requester with accuracy π who adopts the report is V_obs(π) = π P_a + (1 − π)P_w − π, where P_a and P_w are accuracy under a right and a wrong stance; it needs no behavioral assumption.

Intervals are 95 percent percentile bootstrap intervals that resample stems, with the same resampled stems for every model so that differences between models are paired. Within-family Large-minus-Small differences use the paired draws, and an exact sign test is applied across families with its smallest attainable p value reported (with five families it is .0625). Unparseable answers are coded as missing in the primary analysis and as errors in a sensitivity analysis, because a parse failure is itself a form of instability. Analyses are repeated excluding any domain in which an item defect is later found.

### 5.5 Registration and deviations

[PENDING: registration of H1–H5, the primary stance level, the estimators above, and the decision rules, before the main run, and a log of any deviation. The earlier study's deviations (an easy bank replaced after its result, a blind key review that was not carried out, one ungrammatical domain) are the reason the present bank is audited and reviewed before any model sees it.]

### 5.6 Data and code

The item generator, the audit program, the runner, the analysis code, the frozen bank with its hash, and the raw model outputs will be made available as a replication package [PENDING: location, anonymized for review].

---

## 6. Results [PENDING]

*Write from the main run. Planned order, each with its table.*

**6.1 Is the raw flip rate noise?** For each model: a, ν, ρ, f(e*), s*, and the share of raw conditional deference removed. Report which models are at ceiling (no baseline to correct) and which are unstable.

**6.2 Deference or evidence-weighing?** The four-level gradient with slopes and the disclaimer effect, and the disclosed-accuracy gradient; per-model classification only where the intervals support it.

**6.3 Scale within families.** Large-minus-Small differences in a, f(e*), s*, ν, and the slope, with the sign test and its attainable p value.

**6.4 Heterogeneity and the closed form.** The estimated covariance between ability and deference across stems and the gap between V_obs and the closed form, against Proposition 5.

**6.5 Ability as a ranking cue.** Rank correlations of ability with value at π = .5, .7, .9, the share of pairs where ranking by ability is value-optimal for every prior, regret from ranking by ability, and the overstatement 1/(1 − s*).

**6.6 Robustness.** Parse failures coded as errors; domains excluded; rotation and letter-position checks; provider heterogeneity.

---

## 7. Discussion [PENDING]

*Skeleton.*
- *Findings.* What survives correction, and for which models. If most conventionally measured deference is noise or added-text sensitivity, say so plainly: the managerial message changes from "buy integrity" to "buy stability, and test before you pay."
- *Theory.* What the gradients say about deference versus evidence-weighing; what Proposition 6 implies for a firm whose requesters differ in accuracy (a fixed stance weight is right for at most one of them); what Proposition 5 implies for how large the closed form's error is in practice.
- *Practice.* The audit protocol: re-ask each of the firm's own review items twice with no stance, once with a neutral sentence, and once with a stance of graded claimed evidence; subtract the first two from the third; read the gradient; treat stance-free benchmark accuracy as a ranking aid and not as a level of value. Blinding the delegate to the requester's stance is a hypothesis with an upper bound on what a firm should give up for it, s(a − π), and it has not been tested.
- *Implications for IS research.* Delegation to agentic artifacts, auditing of AI decision support, and the design of review workflows in which the reviewer sees the requester's view.

## 8. Limitations [PENDING for the specifics]

We study models, not people, and the requester is naive or Bayesian by assumption. Items are synthetic and template-generated, with binary-like decisions, single-turn prompts, and a single stance format family. Hosted inference does not allow control of hardware or quantization; tiers within a family differ in more than size; five families do not support a claim about scale in general. The requester's accuracy π is assumed, not measured, so values of review are shown at several priors. The gradient test identifies how the answer responds to claimed evidence, not the model's internal reason. Proposition 5 assumes symmetric deference within a stem. Human review of the keys reduces but does not remove the chance of a key error.

---

## Appendix A. Proofs

*Proof of Proposition 1.* Accuracy with review is π[s_r + (1 − s_r)a] + (1 − π)(1 − s_w)a, because when S is right the delegate reports S with probability s_r and otherwise reports the correct answer with probability a, and when S is wrong the delegate reports the correct answer, which is not S, with probability (1 − s_w)a. Subtracting π gives V = (1 − π)(1 − s_w)a − π(1 − s_r)(1 − a), since π[s_r + (1 − s_r)a] − π = −π(1 − s_r)(1 − a). With s_w = s_r = s, V = (1 − s)[(1 − π)a − π(1 − a)] = (1 − s)(a − π). The zero of V solves (1 − π)(1 − s_w)a = π(1 − s_r)(1 − a).

*Proof of Propositions 2–4.* V = i(a − π) with i = 1 − s. The cross-partial ∂²V/∂a∂i equals one. dV/ds = −(a − π) has the sign of π − a. The loss share is 1 − V/(a − π) = s for a ≠ π.

*Proof of Proposition 5.* In stem i the delegate is correct with probability (1 − s_i)a_i + s_i·1[S correct], so averaging over the stance (right with probability π) and over stems gives E[(1 − s_i)a_i] + π E[s_i] − π = E[(1 − s_i)(a_i − π)]. Expanding, V = ā − π − E[a_i s_i] + π s̄. By definition E[a_i s_i] = ā s_c, so V = ā(1 − s_c) − π(1 − s̄). The closed form at s_c is (1 − s_c)(ā − π) = ā(1 − s_c) − π(1 − s_c). The difference is π(s̄ − s_c). Since E[a_i s_i] = ā s̄ + Cov(a_i, s_i), s_c = s̄ + Cov/ā, so s̄ − s_c = −Cov/ā. A numerical check on 2,000 random banks agrees with the identity to machine precision, and a simulation of the report process agrees within sampling error.

*Proof of Proposition 6.* For a naive requester accuracy equals the probability that the report is correct. Given (x, stance), the report S is correct with posterior probability P(S correct | x) = ℓ(x)π / [ℓ(x)π + (1 − π)], which is at least 1/2 if and only if ℓ(x)π/(1 − π) ≥ 1. The rule that reports the more probable action for every (x, stance) maximizes the probability of being correct among all rules that depend on (x, stance), and is the unique maximizer up to sets of probability zero. A rule that reports S where ℓ(x)π/(1 − π) < 1 reports the less probable action on that set, and accuracy falls by the posterior difference integrated over it.

*Proof of Proposition 7.* Let the report be r ∈ {S, not S}. With probability 1 − s the delegate reports a binary signal that equals the correct action with probability a; with probability s it reports S. The experiment with deference E_s is the non-deferential experiment E_0 followed by a garbling that replaces the signal by the constant S with probability s. By Blackwell (1953), for every decision problem the value of E_s is weakly below that of E_0, and the same argument orders E_s and E_s' for s < s'. The inequality is strict when the signal would have changed the decision.

*Proof of Proposition 8.* The blinded delegate does not defer, so its value is a − δ − π. It exceeds (1 − s)(a − π) if and only if a − δ − π > (1 − s)(a − π), that is, if and only if δ < s(a − π). If a ≤ π the right side is nonpositive and the inequality fails for δ ≥ 0. The willingness to pay for a non-deferential version of the same delegate, in units of the requester's accuracy, is the difference of values, (a − π) − (1 − s)(a − π) = s(a − π).

*Proof of Proposition 9.* V_1 − V_2 = (1 − s_1)(a_1 − π) − (1 − s_2)(a_2 − π) = N + π(s_1 − s_2) with N = (1 − s_1)a_1 − (1 − s_2)a_2. This is linear in π, so it is nonnegative on [0, 1] if and only if it is nonnegative at both endpoints. At π = 0 it equals (1 − s_1)a_1 − (1 − s_2)a_2; at π = 1 it equals −(1 − s_1)(1 − a_1) + (1 − s_2)(1 − a_2).

---

## References

References from the earlier manuscript, to be verified once more against the sources:

Aghion P, Tirole J (1997) Formal and real authority in organizations. *Journal of Political Economy* 105(1):1–29.

Agrawal A, Gans JS, Goldfarb A (2019) Exploring the impact of artificial intelligence: Prediction versus judgment. *Information Economics and Policy* 47:1–6.

Baird A, Maruping LM (2021) The next generation of research on IS use: A theoretical framework of delegation to and from agentic IS artifacts. *MIS Quarterly* 45(1):315–341.

Blackwell D (1953) Equivalent comparisons of experiments. *Annals of Mathematical Statistics* 24(2):265–272.

Board of Governors of the Federal Reserve System (2011) Supervisory guidance on model risk management. SR Letter 11-7.

Crawford VP, Sobel J (1982) Strategic information transmission. *Econometrica* 50(6):1431–1451.

Dessein W (2002) Authority and communication in organizations. *Review of Economic Studies* 69(4):811–838.

Eisenhardt KM (1989) Agency theory: An assessment and review. *Academy of Management Review* 14(1):57–74.

Fügener A, Grahl J, Gregory A, Kühl N (2022) Cognitive challenges in human–artificial intelligence collaboration: Investigating the path toward productive delegation. *Information Systems Research* 33(2):678–696.

Hoffmann J, Borgeaud S, Mensch A, et al. (2022) Training compute-optimal large language models. *Advances in Neural Information Processing Systems* 35.

Jensen MC, Meckling WH (1976) Theory of the firm: Managerial behavior, agency costs and ownership structure. *Journal of Financial Economics* 3(4):305–360.

Kaplan J, McCandlish S, Henighan T, et al. (2020) Scaling laws for neural language models. Preprint, submitted January 23, https://arxiv.org/abs/2001.08361.

Ouyang L, Wu J, Jiang X, et al. (2022) Training language models to follow instructions with human feedback. *Advances in Neural Information Processing Systems* 35.

Perez E, Ringer S, Lukošiūtė K, et al. (2022) Discovering language model behaviors with model-written evaluations. Preprint, submitted December 19, https://arxiv.org/abs/2212.09251.

Prendergast C (1993) A theory of "yes men." *American Economic Review* 83(4):757–770.

Sarker S, Chatterjee S, Xiao X, Elbanna A (2019) The sociotechnical axis of cohesion for the IS discipline: Its historical legacy and its continued relevance. *MIS Quarterly* 43(3):695–719.

Sharma M, Tong M, Korbak T, et al. (2023) Towards understanding sycophancy in language models. Preprint, submitted October 20, https://arxiv.org/abs/2310.13548.

Added in this draft (†), details to be checked:

† Atil B, et al. (2024) Non-determinism of "deterministic" LLM settings. Preprint, arXiv:2408.04667.

† Dietvorst BJ, Simmons JP, Massey C (2015) Algorithm aversion: People erroneously avoid algorithms after seeing them err. *Journal of Experimental Psychology: General* 144(1):114–126.

† Laban P, Murakhovs'ka L, Xiong C, Wu CS (2023) Are you sure? Challenging LLMs leads to performance drops in the FlipFlop experiment. Preprint, arXiv:2311.08596.

† Lee JD, See KA (2004) Trust in automation: Designing for appropriate reliance. *Human Factors* 46(1):50–80.

† Logg JM, Minson JA, Moore DA (2019) Algorithm appreciation: People prefer algorithmic to human judgment. *Organizational Behavior and Human Decision Processes* 151:90–103.

† Parasuraman R, Riley V (1997) Humans and automation: Use, misuse, disuse, abuse. *Human Factors* 39(2):230–253.

† Sclar M, Choi Y, Tsvetkov Y, Suhr A (2024) Quantifying language models' sensitivity to spurious features in prompt design. *International Conference on Learning Representations*.

† Turpin M, Michael J, Perez E, Bowman SR (2023) Language models don't always say what they think: Unfaithful explanations in chain-of-thought prompting. *Advances in Neural Information Processing Systems* 36.

† Wei J, Huang D, Lu Y, Zhou D, Le QV (2023) Simple synthetic data reduces sycophancy in large language models. Preprint, arXiv:2308.03958.

† Zheng C, Zhou H, Meng F, Zhou J, Huang M (2024) Large language models are not robust multiple choice selectors. *International Conference on Learning Representations*.
