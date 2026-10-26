# Pre-registration draft: When are synthetic agents valid? Boundary conditions for LLM digital twins

Status: DRAFT. Not yet registered. Do not run the confirmatory study until this file has been registered (OSF or AsPredicted)
and the registration link has been added at the top of this file. The git commit time of the registered version is the time stamp of record.

## 0. What is exploratory and what is confirmatory

- Exploratory (already run, seen by the authors): twin simulations on 772 Twin-2K-500 mega-study participants (defaults, attraction effect,
  targeting fairness) with five models, three persona architectures, system-prompt template A; a pilot reasoning-effort x temperature grid (H6);
  twin results for framing and anchoring from the public Twin-2K-500 GPT-4.1 / Gemini 2.5 simulations. All propositions below were
  formulated after seeing these results. They are therefore hypotheses to be tested on new data, not findings.
- Confirmatory (not yet run): (C1) new simulated respondents, new random condition assignment, new prompt template B; (C2) field test on
  public A/B tests (Section 5). Human benchmarks are fixed, public, and listed in Section 3 before any confirmatory output is generated.

## 1. Theory in brief

A synthetic agent's response is generated from (a) retrieval of textual regularities about how people respond, (b) normative reasoning,
and (c) conditioning on a persona. Human biases arise additionally from experiential processes (attention, effort cost, affect, memory) that a
text-only agent does not bear. A twin is therefore valid for a treatment effect only inside a validity region defined by four conditions:

- V1 Textual channel: the treatment acts through information carried by the text of the stimulus (words, numbers, option structure).
- V2 Cost insensitivity: the effect is not mediated by effort, attention, or transaction costs borne by the decision maker.
- V3 Novelty: the paradigm is not available verbatim in training text, so recovery reflects generalization rather than recall.
- V4 Regime match: the agent's reasoning regime (deliberative versus fast) matches the human decision regime being simulated.

## 2. Propositions and directional predictions

Effect types: cue-based (loss framing, anchoring, attraction/decoy; V1 satisfied, V2 satisfied) and cost-based (defaults; V2 violated).
Discrepancy D = twin effect minus human effect, in the standardized unit of each effect.

- P1 (cue-based inflation). For cue-based effects, D > 0 in canonical paradigms (twin overshoots).
- P2 (cost-based dissociation). For defaults, D > 0 in the canonical paradigm (organ donation) and D <= 0 in the novel paradigm (green energy).
- P3 (familiarity). For defaults and fairness, D_novel - D_canonical < 0 (twin discrepancy is larger on canonical paradigms).
- P4 (reasoning). Within model, higher reasoning effort reduces the magnitude of cue-based effects and reduces factual error.
- P5 (co-movement). Across model x reasoning x temperature cells, standardized bias magnitude and factual error rate are positively
  correlated within model (resource-rational account). A null or negative correlation is reported as disconfirming.
- P6 (leakage). Naming the phenomenon in the prompt (theory-explicit architecture) increases effect magnitude relative to the
  demographics-only architecture for canonical paradigms.
- P7 (field boundary). On public headline A/B tests (textual treatments, V1 satisfied), twin-predicted winners agree with observed winners
  at a rate above chance, but twin-predicted effect sizes exceed observed effect sizes (D > 0).

## 3. Human benchmarks (fixed before any confirmatory output)

From public Twin-2K-500 mega-study data, computed by benchmarks/compute_human_benchmarks.py:
organ-donation default +4.4 pp (95% CI -3.5 to 12.3); green-energy default +24.7 pp (CI 16.9 to 32.4); attraction effect pooled log odds ratio
0.37 (CI 0.11 to 0.62); targeting fairness d = -0.54 (targeted rated less fair); loss framing d = 0.76-0.77; anchoring d(log) African UN
members 0.72-0.78, redwood height 1.49-1.69.

## 4. Confirmatory study C1 (twins)

- Respondents: Twin-2K-500 participants NOT in any mega-study file used in the exploratory run (the complement of the 772). Persona architectures:
  demographics-only and persona-summary. No respondent overlaps with the exploratory sample.
- Stimuli: identical stimulus text to the human experiments; condition assigned at random per respondent with equal probability, seed 2026.
- Models: the five exploratory models, with versions logged by date (claude-haiku-5.5, gpt-5.6-luna, gemini-3.7-flash, grok-4.3, llama-4-maverick).
- Prompt template B (different wording and ordering of instructions from template A); reasoning effort low; temperature 0.7.
- Sample: 600 respondents per phenomenon per architecture per model; one draw each.
- Primary outcomes: defaults (opt-out minus opt-in share, pp), attraction (log odds ratio), fairness (d), loss framing (d), anchoring (d on log estimates).
- Analysis: effect sizes with respondent-level bootstrap 95% CIs (2,000 resamples). P1-P3, P6 are evaluated as the sign of D or of the
  difference in D; a proposition is "supported" if its sign holds in at least 4 of 5 models and the pooled bootstrap CI excludes zero, "partly supported"
  if the sign holds in at least 4 of 5 models but the pooled CI includes zero, otherwise "not supported". Multiplicity: Benjamini-Hochberg across the
  pooled tests (q = 0.05).
- H6 grid (P4, P5) is rerun on new respondents with the same design as the pilot: 3 reasoning levels x 3 temperatures x 4 models, 100 respondents per
  study, plus the 26-item factual battery. Hallucination is reported as factual error rate on answerable items; fabrication on invented items is
  reported separately. Because the pilot showed near-zero fabrication with an explicit abstain option, the confirmatory battery adds 10 invented items
  without an abstain nudge in the instructions.
- Deviations from this document will be listed in the paper.

## 5. Confirmatory study C2 (field test)

- Data: the Upworthy Research Archive (Matias, Munger, Aubin Le Quere, Ebersole 2021). Use only tests flagged as not at risk of randomization imbalance;
  use the confirmatory-package split as the test set and never inspect twin performance on the exploratory package before registration.
- Task: for each test, the twin sees the headline variants (and, if available, the lede) as an experimental choice (which would you click?) and returns
  a click propensity for each variant. Unit of analysis is the test; sample of 1,000 tests drawn at random with seed 2026.
- Outcomes: pairwise winner agreement (twin-predicted best variant vs observed best variant, restricted to tests where the observed difference is
  statistically significant at p < 0.05), Spearman correlation of predicted and observed log odds of click across variants, and calibration slope of
  predicted on observed effect.
- Prediction (P7): agreement > 0.5, with exact binomial CI lower bound > 0.5 in at least 3 of 5 models; calibration slope > 1 (twins overstate effects).
