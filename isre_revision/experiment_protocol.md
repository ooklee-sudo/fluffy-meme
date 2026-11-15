# Experiment protocol: Does verification respond to AI tool quality, and by how much?

A preregistered, incentivized online experiment that estimates the offsetting elasticity ε
directly, tests whether it matches the elasticity predicted from the detection technology, and tests
the liability and error-composition channels. It reuses the 25,120 HumanEval+ solutions already
generated for Section 7, so the detection probability of every defect shown to a participant is known
in advance.

---

## 1. Questions and preregistered hypotheses

| # | Hypothesis | Model source | Test |
|---|---|---|---|
| H1 | Participants run fewer tests per function when the assistant is better. | Prop. 1, de*/dλ > 0 | Effort, within subject |
| H2 | Offsetting is partial: 0 < ε < 1. Shipped defects fall with tool quality, but less than proportionally. | Prop. 2 | ε̂ = ln(R_H/R_L)/ln(λ_H/λ_L); reject ε = 0 and ε = 1 |
| H3 | ε̂ equals the elasticity predicted from the served pool, CV²/(1+CV²) evaluated at observed effort. | Prop. 2(b) | Equivalence test (TOST), bounds ±0.15 |
| H4 | A lower penalty share δ reduces effort and reduces willingness to pay for the better assistant, in proportion δ^ε. | Props 4–5 | Between-subject δ; BDM WTP elicitation |
| H5 | Holding λ fixed, an assistant whose defects are subtler (lower θ) ships more defects, with elasticity −(1−ε). | Prop. 3 | Study 2 |

Exploratory: whether participants' beliefs about tool quality are calibrated, and whether
reading-based detection (flags without a failing test) responds to tool quality the way testing does.

---

## 2. Design (Study 1: main)

**2 (assistant quality, within subject) × 2 (liability share, between subject).**

- **Assistant quality λ.** Two blocks of 20 functions each, from "Assistant A" and "Assistant B".
  The low-defect assistant serves functions drawn so that the expected number of defect clusters per
  function is λ_L = 0.15. The high-defect assistant uses λ_H = 0.60, matching the range in Table 1
  (Claude Haiku 5.5: 0.08; Llama 3.1 8B: 0.65). Block order and assistant labels are counterbalanced.
- **Holding error composition fixed (key to identifying ε).** In both arms, the *defective*
  functions are drawn from the **same** pool, stratified on the per-defect failure share f/M. The arms
  then differ only in how many defective functions they serve, not in how detectable those defects
  are. The survivor CV is identical across arms by construction (η = 0), so the λ contrast
  identifies ε cleanly.
- **Liability share δ.** Penalty per shipped defect: $1.00 (δ = 1) or $0.40 (δ = 0.4).
  Randomized at the participant level.

### Task screen
For each function the participant sees the specification (docstring) and the AI-generated code,
and has three actions:

1. **Run a test ($0.02 each).** Executes one *hidden* HumanEval+ input, drawn uniformly without
   replacement, and shows input, expected output and actual output. This makes verification cost
   linear and observable, and it reproduces exactly the random-order detection process calibrated in
   Section 7.
2. **Fix.** Available after a failing test. The defect cluster revealed by that failure is removed
   (implemented by swapping in the solution's nearest variant without that failure signature, or by
   marking the cluster as fixed for payoff purposes). Detected = removed, as in the model.
3. **Flag without a test.** Free. If the function truly contains a defect, all its clusters are
   removed; if not, the participant pays a false-alarm charge of $0.10. This captures verification by
   reading, which the model's e also covers.
4. **Accept.** Ship the function and move on.

**Payoff.** $20 base + $10 bonus endowment − $0.02 × tests − δ × $1 × shipped defect clusters
− $0.10 × false flags. Shipped defects are scored after the session on the *full* test suite, using
the manuscript's failure-signature definition of a defect.

**Information.** Before each block participants are told the assistant's historical rate ("about 1 in
7 functions from Assistant A has a bug" / "about 1 in 2 from Assistant B") and complete 3 practice
functions from that assistant with feedback. This matches the model, in which the developer knows λ.

**WTP elicitation (H4).** After both blocks, a Becker–DeGroot–Marschak elicitation of the maximum
amount the participant would pay to use the better assistant for a further block of 10 functions, one
of which is randomly implemented.

### Model predictions at these parameters
With k = 0.63, mean per-test detection 0.40, test cost $0.02 and penalty $1, the median participant
optimally runs **1.5 tests per function with the better assistant and 5.7 with the worse one**,
and ε = 0.61, so shipped defects fall to 4^−0.61 ≈ 43% of their level when λ falls fourfold rather
than to 25%. At δ = 0.4, predicted effort falls to 0.4 and 2.6 tests respectively.

---

## 3. Study 2 (error composition, H5)

Same task and incentives, δ = 1. **Within subject, λ fixed at 0.40 in both blocks.** One block draws
defects from the subtle half of the f/M distribution (fail < 22% of inputs), the other from the obvious
half. The model predicts more shipped defects in the subtle block with
d ln R / d ln θ = −(1 − ε), and allows effort to move in either direction. This is the first
behavioural test of the "plausible-but-wrong" channel that makes the paper specific to AI. Sample:
N ≈ 150. Study 2 can run after Study 1 and use its ε̂ to preregister the predicted contrast.

Optional Study 3 (miscalibrated trust): give a label that overstates the worse assistant's quality, so
that believed λ < true λ, and measure the excess in shipped defects. This links to the ρ-learning
parameter of the original Section 6 and to the automation-bias literature.

---

## 4. Sample, power and cost

`sim_power.py` simulates the design under the model, with heterogeneous participant costs
(lognormal), implementation noise in effort, and optionally item-level heterogeneity and participants
who make only part of the optimal adjustment. ε̂ is estimated from pooled shipped defects, with a
participant bootstrap.

| Scenario | N | Items/block | mean ε̂ (sd) | Power vs ε = 0 | Power vs ε = 1 |
|---|---|---|---|---|---|
| Model-optimal behaviour | 60 | 20 | 0.63 (0.08) | 1.00 | 0.98 |
| Model-optimal behaviour | 120 | 20 | 0.63 (0.06) | 1.00 | 1.00 |
| Half adjustment, noisy, item heterogeneity | 120 | 20 | 0.83 (0.06) | 1.00 | 0.77 |
| Half adjustment, noisy, item heterogeneity | 240 | 20 | 0.82 (0.05) | 1.00 | 0.96 |
| Quarter adjustment, noisy, item heterogeneity | 240 | 20 | 0.90 (0.04) | 1.00 | 0.60 |

**Recommendation: N = 240 for Study 1 (120 per liability arm), 20 functions per block.** Complete
offsetting (ε = 0) is rejected in every scenario. Detecting a *weak* behavioural response is what
drives the sample size, and N = 240 gives ≥ 95% power if participants make at least half the optimal
adjustment. H4 (the δ × λ interaction) is powered as a secondary hypothesis only. Say so in the
preregistration.

**Participants.** Prolific with a programming prescreen plus a 5-minute Python screening quiz (pass
≥ 4/5), or Upwork freelancers for a professional subsample. Exclude anyone who fails two attention
checks or completes a block in under 4 minutes.

**Duration and cost.** About 50 minutes (consent, tutorial, 6 practice items, 40 items, WTP, survey).
Base $20 + average bonus ≈ $6 → ≈ $26 × 240 ≈ **$6.2k for Study 1**, plus platform fees (~33% on
Prolific) → ≈ $8k; Study 2 ≈ $4.5k. A student pilot (N ≈ 30) before launch to calibrate timing and
the test price.

---

## 5. Measures

- **Effort:** tests run per function (primary); time on function; code-viewer scroll depth and
  flags without a test (secondary).
- **Shipped defects:** clusters remaining at Accept, scored on the full suite (primary for ε̂).
- **Detection:** clusters found by tests or flags.
- **Beliefs:** after each block, "How many of the last 20 functions do you think had a bug?"
- **Covariates:** years of Python, professional status, prior AI-assistant use, risk attitude (one
  incentivized lottery choice).

---

## 6. Analysis plan (preregister)

1. **ε̂ (H2).** Poisson regression of shipped clusters per function on log λ_arm with participant fixed
   effects. The coefficient on log λ is ε̂. Standard errors clustered by participant. Report the pooled
   ratio estimator and the participant bootstrap as robustness. Block-1-only between-subject
   estimate as a check for contrast effects.
2. **Effort (H1).** Poisson/negative-binomial regression of tests per function on arm, participant FE.
3. **Prediction test (H3).** Compute the model-implied ε from the served pool's survivor CV at each
   participant's realized effort, average, and run TOST of ε̂ − ε_pred within ±0.15.
4. **Liability (H4).** Effort ~ arm × δ. WTP ratio WTP(δ=0.4)/WTP(δ=1) against the predicted 0.4^ε ≈
   0.57.
5. **Study 2 (H5).** d ln R / d ln θ against −(1 − ε̂_Study1).
6. **Deviations.** If many participants run zero tests in the better-assistant block, which is the
   corner where Z < 1, report the share at the corner and estimate ε on the interior subsample as
   secondary.

---

## 7. Threats and mitigations

| Threat | Mitigation |
|---|---|
| Test-running is more stylized than real verification | The flag-without-test channel captures reading. Report both. The stylization is deliberate: it makes S(e) known, so H3 is a sharp test. |
| Experimenter demand ("they want me to test less") | Neutral assistant labels (A/B), with the quality information given as a historical frequency. Same instructions across arms. |
| Order and contrast effects | Counterbalance. Report block-1 between-subject estimates. |
| Online participants are not professional developers | Screening quiz. Upwork professional subsample. Heterogeneity by experience. |
| HumanEval+ functions are short | Acknowledge, and note that the detection technology is measured for exactly the code shown, which is what H3 needs. External validity is argued from the calibration across defect definitions. |

**Ethics.** IRB approval at your institution, preregistration on OSF or AsPredicted, and payment no
lower than the platform's recommended hourly rate at the median completion time.

---

## 8. What it buys the paper

- A direct estimate of the behavioural mechanism (objection 4).
- A sharp test of the paper's distinctive claim, that offsetting is predicted by the detection
  technology (H3).
- The first behavioural evidence on the error-composition channel (H5, objection 2).
- The empirical section becomes: calibration (technology) → experiment (behaviour) → field data
  (appendix).
