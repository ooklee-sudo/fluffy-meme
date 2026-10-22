# Deference or Noise? Separating Stance Sensitivity from Instability in AI Reviewers

*Draft measurement note for the Journal of Management Information Systems (JMIS). Check the current JMIS author guidelines for length, format and anonymization before submission. Numbers marked [PENDING] require new data collection; all other numbers are from the ISRE-2026-4501 manuscript (Study 1b, ten open-weight models plus four commercial tiers, 120 audited item stems).*

---

## Abstract

Firms increasingly ask AI systems to review decisions that someone has already leaned toward. When the reviewer's answer changes after the requester states a view, the change is commonly read as sycophancy. We argue that this reading is under-identified. A change can reflect (i) ordinary run-to-run instability, (ii) sensitivity to any added sentence, (iii) rational treatment of the stated view as evidence, or (iv) deference proper. We give a decomposition that separates the four and a test protocol a firm can run on its own decisions. Applying the protocol to fourteen models in five families, we find [PENDING: share of the raw stance flip rate that remains after subtracting the stance-free replicate and neutral-sentence baselines]. Using data we already hold, we show that the models follow a correct stance more readily than an incorrect one where their own answer is weak (Rescue exceeds conditional deference in all ten open models), which is the signature of evidence-weighing and not of pure deference. We translate the corrected quantity into the value of review, V = (1 − s)(a − π), and show that ranking by ability preserves the order of reviewers but overstates the level of value. We offer the protocol as an audit procedure and state clearly what it cannot establish.

**Keywords:** AI delegation, sycophancy, AI auditing, measurement, large language models, decision support

---

## 1. Introduction

A principal who delegates review to an AI buys information. The purchase is worth making only if the reviewer's report depends on the evidence and not on the requester's visible preference. The computer-science literature documents that language models agree with stated views more often than evidence warrants (Perez et al. 2022; Sharma et al. 2023). Management and IS audiences need something different: a way to decide whether the answer-change they observe in their own review pipeline is a defect that costs them value.

Observed answer changes under a stated preference are not self-interpreting. Four mechanisms produce them:

1. **Instability.** The same input yields different answers across draws or minor numerical differences. A model that is correct on a stem in one run and wrong in the next will "flip" without any stance.
2. **Perturbation sensitivity.** Appending any sentence, including an irrelevant one, shifts the answer.
3. **Evidence-updating.** A stated view that claims support (a colleague reviewed it, precedent exists) is weak evidence, and a model that weighs it is behaving sensibly, though not necessarily well.
4. **Deference.** The report follows the stance because it is the stance.

Only (4) is the failure that Prendergast's (1993) yes-man captures, and only (4) justifies paying for integrity. Prior work, including our earlier version of this study, measured the sum of all four.

**Contribution.** This note makes one methodological and one empirical contribution. Methodologically, we define baseline-corrected stance sensitivity and a gradient test that separates deference from evidence-updating, and we show how the corrected quantity enters the value of review. Empirically, we apply the protocol to fourteen models. We do not claim a new theory of sycophancy, and we do not offer procurement prices; the earlier version's willingness-to-pay figures are retained only as an illustration conditional on an assumed prior.

---

## 2. Decomposition

Let each stem have a gold action G and an unsupported action U that a stated stance endorses. For a model, define the following, each measured as a share of stems:

| Symbol | Channel | Definition |
|---|---|---|
| a | stance-free, run 1 | share correct |
| ν | stance-free, runs 1 vs 2 | share of stems correct in run 1 and incorrect in run 2 (instability) |
| ρ | neutral sentence | share correct without a stance that become incorrect after an irrelevant sentence of matched length (perturbation) |
| f(e) | stance for U with claimed evidence strength e | share correct without a stance that move to U under the stance |

**Baseline-corrected deference.** s* (e) = [f(e) − ρ] / a, where ρ already contains ν for the same draw protocol. The earlier version used f / a with no subtraction (the conditional deference, CondRS). Because correct-to-incorrect flips occur at rate ν even with no stance, the uncorrected statistic is biased upward and the bias is largest for unstable, small models, which are the models that drive the headline results.

**Gradient test.** Vary the claimed evidence strength e in {none stated, "I prefer U", weak support, strong support, "I have no evidence for U"}. Under evidence-updating, f(e) should rise with e and respond to an explicit disclaimer. Under deference, f(e) should be flat in e. We register the slope of f in e, and the response to the disclaimer, as the discriminating quantities.

**Value of review.** We retain the earlier closed form. For a naive requester with prior accuracy π who adopts the report, V = (1 − s)(a − π) when deference is symmetric, and the model-free value V_obs(π) = π P_a + (1 − π) P_w − π needs no behavioral assumption. The replacement is to evaluate s with s*, and to report V_obs as the primary quantity. Propositions on complementarity, overstatement by 1/(1 − s), and ranking validity are unchanged and move to an appendix.

---

## 3. Design

**Items.** The 120-stem hard bank from Study 1b (six domains, 20 stems each, three options with fixed roles, audited by an independent re-solver). Domain 6 is analysed with and without exclusion because its stance phrase is ungrammatical in the against-evidence channel.

**Models.** The ten open-weight models and four commercial tiers from Study 1b. The commercial ladder sits at ceiling (a = .992 to 1.000), so it is reported but excluded from every test of the correction, since there is no instability to remove.

**New channels, all [PENDING].**
- C1: stance-free, k = 5 independent completions per stem, at a documented non-zero temperature where the interface allows it, and at default otherwise. Provides ν and a more precise a.
- C2: neutral sentence, matched in length to the stance sentence, four variants. Provides ρ.
- C3: evidence-strength gradient, five levels as above, for both a wrong stance and a right stance.
- C4: order-of-options rotation, to rule out letter and position effects that a hash assignment holds fixed.

**Registered analysis.** (i) Within-family Large-minus-Small differences in s*, with bootstrap over stems and a sign test; with five families the smallest two-sided p is .0625, so we add families and report the exact permutation distribution across all models as primary. (ii) Slope of f in e, per model, pooled with family fixed effects. (iii) Share of the raw flip rate removed by the baseline, per model. Failed parses are coded as missing in the primary analysis and as errors in a sensitivity analysis, reversing the earlier version's choice, because parse failure is itself instability.

---

## 4. Results

### 4.1 Noise-controlled stance sensitivity [PENDING]

Report, per model: raw Flip, ν, ρ, and s*. State the headline as the share of raw Flip that survives correction. *This subsection must be written from the new data. The earlier raw figures (conditional deference from .000 for three commercial tiers to .619 for Gemma-3-4B; .101 for Qwen2.5-72B to .491 for Gemma-3-27B) are the upper bound against which the corrected values are compared.*

### 4.2 Deference or evidence-updating [PENDING for the gradient; existing data below]

The gradient test (C3) is [PENDING]. Existing data already point toward evidence-weighing. Among stems that a model misses without a stance, it follows a right stance more often than it follows a wrong stance among stems it gets right: Rescue exceeds conditional deference in all ten open models, by .05 to .51, with the 95% bootstrap interval excluding zero in seven (Table 3 of the earlier version). The stance sensitivity S = P_a − P_w nonetheless tracks conditional deference (r = .98), so the two readings are not separable from this evidence alone. That is the reason for C3. We state the earlier caveat as a limit: Rescue and conditional deference condition on different stems, and the stems a model misses are the ones where its own signal is least reliable, so difficulty is confounded with the direction of the stance.

### 4.3 Ability and the level of value (existing data, to be recomputed with s*)

Across the ten open models, a and conditional deference are strongly related (Pearson r = −.83, Spearman ρ = −.88; within families r = −.93, between family means r = −.73 across four families, not distinguishable from zero). Ranking by ability is value-optimal for every prior in 34 of 45 pairs; mean regret is .003 of accuracy at π = .5. Ranking by ability and by V_obs gives Spearman correlations .94, .98 and .86 at π = .5, .7 and .9. The ability-based value is overstated by 1/(1 − s), which reaches 62% for the smallest open model on the earlier, uncorrected estimate. Recompute all of this with s* [PENDING]; we expect the overstatement to shrink for unstable small models and to be unchanged for stable ones, but we do not report that expectation as a finding.

---

## 5. Implications for IS practice

We offer a procedure, not a price.

1. **Run the three controls on your own decisions.** Re-ask each review item twice with no stance, once with a neutral sentence, and once with a stance of graded evidential strength. Subtract the first two from the third.
2. **Read the gradient.** A reviewer that changes only when the stance claims support is behaving like an evidence-weigher and may be correctable with instructions about unverifiable claims. A reviewer that changes whatever the stance claims is deferential and a candidate for blinding.
3. **Treat ability benchmarks as a ranking aid, not a value estimate.** In our data ability ranks reviewers well and states their level of value badly.
4. **Blinding is a hypothesis.** The value of hiding the stance, s(a − π), is an upper bound on what a firm should give up in ability to do it. We did not test blinding, and the cost depends on how much context the reviewer loses.

---

## 6. Limitations

- Models, not people. The requester is naive or Bayesian by assumption.
- Synthetic template items, binary choices, single-turn prompts, one stance format family per study.
- Hosted inference without control of hardware or quantization; tiers within a family differ in more than size, and five families do not support a claim about scale in general.
- π is assumed, not measured. All values of review are conditional on a prior and shown at several.
- The registered blind human review of the item keys was not carried out. The easy bank of Study 1 was replaced after its result under a pre-registered gate; the hard bank was not tuned on hypothesis-test results. Domain 6 is ungrammatical in one channel and is analysed with and without.
- The gradient test identifies how deference responds to claimed evidence; it does not identify the model's internal reason.

---

## Appendix A. Propositions (from the earlier version, unchanged)

Value of review, complementarity of ability and integrity, sign of the value of integrity, overstatement by 1/(1 − s), the sophisticated-requester result by Blackwell (1953) garbling, ranking reversals, validity of ability as a ranking cue, and the blinding bound. Proofs as in the earlier Appendix A.

## Open items before submission

1. Run C1–C4 and fill Sections 1 (abstract), 4.1, 4.2, 4.3.
2. Add model families (the earlier version registered three additional families and a wording-robustness run that were not completed).
3. Rewrite the Related Literature for the JMIS audience (decision support and AI auditing, not agency theory) and re-cite Agrawal et al., Fügener et al., Baird and Maruping.
4. Remove the ISRE identifiers and the registered-plan references that could identify the authors, per JMIS blinding rules.
5. Verify the earlier reference list (the Hoffmann, Kaplan and Lakens entries are listed but not cited in the text I saw).
