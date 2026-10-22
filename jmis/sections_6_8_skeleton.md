# Sections 6–8: fillable skeleton

Every table maps to a file written by `analysis.py` (`model_metrics.csv`, `family_diffs.csv`, `sign_tests.csv`, `ranking.csv`). Metric names are in `code`. Numbers stay [PENDING] until the main run. Sentences in *italics* are conditional templates: keep the branch the data support and delete the other.

## 6. Results

**Overview paragraph.** [PENDING: N models analysed of 14; models at ceiling (a ≥ .98, excluded from the rescue rate only); models with fewer than 50 conditional stems (excluded from H1–H3); share of calls with unparseable answers; providers per model.]

### 6.1 Is the raw flip rate noise?

**Table 1.** One row per model, grouped by family. Columns: ability `a`; stance-free rate `nu` (ν); neutral-sentence rate `rho` (ρ); raw conditional deference `f_star` (f(e\*)); corrected `s_star` (s\*); share removed `removed`. Each as estimate [95% CI]. Flag ceiling models (no baseline to correct).

- *Across models, the baseline ρ accounts for a median of [PENDING]% of conventionally measured conditional deference (range [PENDING]–[PENDING]%).* / *The baseline is indistinguishable from zero for [PENDING] of 14 models, and the raw measure is a fair estimate for them.*
- *ν and ρ differ by [PENDING] (CI [PENDING]), so [added-text sensitivity adds little / adds [PENDING] to instability].* (Compare `nu` with `rho`.)
- H1: [supported / not supported]; rank correlation of ν with share removed = [PENDING].

### 6.2 Deference or evidence-weighing?

**Table 2.** Per model: f at pref, weak, strong, disclaimer (`f_pref`, `f_weak`, `f_strong`, `f_disclaimer`); `slope`; `disclaimer_effect`; `acc_20`, `acc_50`, `acc_80`; `acc_slope`; classification (deference-consistent / evidence-weighing-consistent / mixed / unclassified, per Table R1).

**Figure 1.** f against claimed evidence (three points plus disclaimer) and against disclosed accuracy X, one panel each, models as lines, CIs shaded. Colour by family, not by model.

- *[PENDING] of 14 models are evidence-weighing-consistent, [PENDING] deference-consistent, [PENDING] mixed.*
- Proposition 6 reading: a rise in f with X is evidence-weighing, and is costless only while the implied stance weight does not exceed π/(1 − π) at the disclosed X. [PENDING: compare the observed rise with that bound; the proposition gives a ceiling on rational weight, not a point prediction.]
- Caveat to keep: the gradients identify how the answer responds to claimed evidence, not why.

### 6.3 Scale within families

**Table 3.** Large minus Small by family for `a`, `f_star`, `s_star`, `nu`, `slope` with paired intervals (`family_diffs.csv`). Beneath: sign test rows from `sign_tests.csv` (families agreeing / families, exact p, smallest attainable p).

- *In [PENDING] of 5 families the larger model has higher ability and lower s\*; exact p = [PENDING] (smallest attainable .0625).*
- With five families the sign test can never reach conventional significance in a two-sided test; say this next to the p-value. Report intervals for each family as the main evidence.
- Families with a single model, or in which a model has fewer than 50 conditional stems, are listed and excluded from the sign test.

### 6.4 Heterogeneity and the closed form

**Table 4.** Per model: `cov_a_s`, `s_bar`, `s_c`, `a_bar`; model-free value `V_0.5`, `V_0.7`, `V_0.9`; gap `gap_0.7` against the Proposition 5 prediction `gap_pred_0.7`.

- *Cov(a_i, s_i) is negative for [PENDING] of 14 models; the closed form understates the model-free value by [PENDING] at π = .7.*
- Measurement note to keep: s_i is estimated from one stance draw and one neutral draw per stem, so Cov is noisy but not sign-biased. Because s_i here is the excess over the neutral baseline, the observed gap approximates, and does not equal, the Proposition 5 identity. Report both columns.

### 6.5 Ability as a ranking cue

**Table 5.** Rows π = .5, .7, .9: `spearman_a_V_*`, `regret_*`; plus `pairs_ability_optimal`; overstatement `overstate` (1/(1 − s\*)) per model in Table 1.

- *Ranking by ability preserves the order of value in [PENDING]% of pairs (CI [PENDING]), and the regret from choosing the top-ability model is [PENDING] accuracy points at π = .9.*
- *Ability overstates value by a median factor of [PENDING] (range [PENDING]–[PENDING]).* Where s\* is near 0, say the overstatement is small.
- H5: [supported / not supported].

### 6.6 Robustness

**Table 6.** Headline `s_star`, `removed`, and `slope` under: (a) unparseable answers coded as errors (`--missing error`); (b) each domain excluded in turn; (c) rotated letters (`rot_a`, `rot_f` against `a`, `f_pref`); (d) models answered by more than one provider, split by provider; (e) the mixture-corrected estimator `s_mix` = (f − ρ)/(1 − ρ).

- State which conclusions change. [PENDING]

## 7. Discussion

**7.1 Findings.** *Branch A (most raw deference is noise):* "Most of what the conventional measure reads as deference is [instability / added-text sensitivity]. For a buyer the message changes from 'buy integrity' to 'buy stability, and test before you pay'." *Branch B (deference survives):* "A share of [PENDING]% survives correction, is flat in claimed evidence, and does not respond to a disclaimer; this is the yes-man pattern, and it is not removed by raising ability." *Branch C (mixed):* "The result differs by model, and the classification in Table 2 is the finding."

**7.2 Theory.**
- Proposition 6 and heterogeneous requesters: a fixed stance weight is right for at most one requester accuracy π, so a firm whose requesters differ in accuracy cannot set one weight for all of them. [PENDING: say whether the observed slopes in X are steeper or flatter than rational.]
- Proposition 5: how large the closed-form error was in practice (Table 4); *if small, the closed form is adequate for valuation and the covariance is a diagnostic only.*
- Proposition 8: s(a − π) is an upper bound on what to give up for blinding the delegate to the stance. Untested: blinding was not run.

**7.3 Practice: audit protocol.** Re-ask each of the firm's own review items (i) twice with no stance, (ii) once with a neutral sentence of matched length, (iii) once with a stance at graded claimed evidence. Subtract (i) and (ii) from (iii), read the gradient, and treat stance-free benchmark accuracy as a ranking aid and not as a level of value. Give the minimum item count that makes the interval useful: [PENDING: from the bootstrap widths, items needed for ±0.05 on s\*].

**7.4 Implications for IS research.** Delegation to agentic artifacts (Baird and Maruping 2021); auditing of AI decision support; review workflows in which the reviewer sees the requester's view. Keep to what the evidence supports.

## 8. Limitations

Keep the existing paragraph and add the specifics below once known.

- Models, not people; the requester is naive or Bayesian by assumption; π is assumed, so value is shown at three priors.
- Synthetic, template-generated items with one correct answer; single-turn prompts; one family of stance wordings.
- Hosted inference: hardware, quantization, and silent model updates are uncontrolled. [PENDING: models answered by more than one provider; tiers that rejected the temperature argument.]
- Five families do not support a general claim about scale; the sign test cannot go below p = .0625.
- Tiers within a family differ in more than size.
- The gradient test identifies the response to claimed evidence, not the internal reason.
- Proposition 5 assumes symmetric deference within a stem; s_i is estimated from one draw per stem.
- The additive correction s\* = f − ρ understates deference if the effects combine as a mixture. [PENDING: state the sensitivity result.]
- Key errors: human review reduces but does not remove them. [PENDING: agreement figures and items changed.]
- Deviations from the registration: [PENDING: refer to Table R2].
