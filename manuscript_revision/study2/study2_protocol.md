# Study 2: experimental test of the choosing-to-accepting frame shift (protocol draft)

Draft for the authors to adapt; needs institutional ethics approval and preregistration before data collection. Numbers marked *(simulated)* come from `power_simulation.py` in this folder, run on the paper's own model; they are design guidance, not evidence.

## 1. What the experiment must show

Aggregate debt cannot separate the behavioral theory from rational acceleration (Result 2a). Three statistics can: the possession effect, the lapse of planned refactoring, and the self-admitted share. This study measures the first two directly and, because the model gives each a closed form, recovers the two parameters behind them separately:

- λ, the extra weight on changing something already in hand (loss aversion);
- β, present bias.

**Decision rule from the model.** For a stated rework cost R (known) and a time cost c of improving the code, a developer improves the code if and only if:

| Condition | Decision | Threshold on ln R |
|---|---|---|
| **C**, choice: before any code exists | v·c < δ·R | τ_C = ln(c/δ) |
| **P**, plan: commit now to improve an artifact received next week (naive planner) | λ·v·c < δ·R | τ_P = τ_C + ln λ |
| **A**, accept: artifact in hand, decide now | λ·v·c < βδ·R | τ_A = τ_C + ln λ − ln β |

So ln λ = τ_P − τ_C, −ln β = τ_A − τ_P, and the possession effect is τ_A − τ_C = ln(λ/β). Rational acceleration predicts all three differences are zero for every value of the speed premium v.

## 2. Design

**Participants.** Professional software developers (at least two years of paid experience), recruited through a panel or professional network. Target **260 recruited, about 208 completing both sessions**.

**Within-subject, three conditions** (C, P, A), each with 8 decisions per participant (4 values of ln(R/c) × 2 repetitions), randomized in order within session. Total 24 decisions.

**Session 1.** Condition C decisions, then condition P decisions: "next week you will receive a working implementation of this feature; will you commit to improving it?"

**Session 2** (7 days later). Condition A decisions on the same cases as the P commitments. Lapse is a case with a commitment in P but no improvement in A.

**Stimuli.** Short realistic tasks, each presented with: stated time cost c (minutes of extra work to improve the code), stated future rework R (minutes of cleanup the code will cause later), and the working implementation (conditions P and A only). Design points x = ln(R/c) ∈ {−0.2, 0.3, 0.8, 1.3} bracket the predicted thresholds. R and c are shown in minutes so that the cost is concrete.

**Incentives.** The cost of each decision must fall on the participant's own money; if the extra work were paid by the hour, choosing it would cost nothing and the decisions would be cheap talk.
- Each participant gets a fixed participation fee plus a bonus endowment E.
- One decision per participant is drawn at random and carried out. Stated minutes convert to money at a fixed rate m: improving the code deducts c·m from the bonus now (condition C or A) or in session 2 (condition P); leaving it deducts R·m.
- Choose m so that the largest possible deduction is below E, and tell participants the rule and the conversion before the first decision.
- The random draw is a standard way to keep decisions incentive-compatible without paying for all of them.

**Exclusions (preregistered).** Failing an attention check; completing session 1 in under a minimum plausible time; not returning for session 2 (kept for conditions C and P, dropped for A and the lapse analysis).

## 3. Hypotheses

| | Hypothesis | Rational acceleration | Behavioral theory |
|---|---|---|---|
| H1 | Possession effect: τ_A − τ_C > 0 (P1b) | = 0 | > 0 if β < 1 or λ > 1 |
| H2 | Lapse: τ_A − τ_P > 0, i.e. more planned-but-undone than undone-but-done (P2) | = 0 | > 0 iff β < 1 |
| H3 | Loss aversion: τ_P − τ_C > 0 | = 0 | > 0 iff λ > 1 |

H2 is a net asymmetry (planned-and-not-done minus not-planned-and-done), not a raw lapse rate, because response noise alone produces both kinds of reversal equally.

## 4. Analysis plan

**Primary model.** Logit of "improves the code" on x = ln(R/c) and indicators for P and A, with standard errors clustered by participant. The coefficients map to thresholds: τ_P − τ_C = −γ_P/b, τ_A − τ_P = −(γ_A − γ_P)/b, τ_A − τ_C = −γ_A/b, with b the slope on x. Delta-method confidence intervals.

**Reporting.** Point estimates and intervals for ln λ and −ln β, not only significance. Results by experience level (an exploratory moderator). Two-sided tests at 5%; H1–H3 are the confirmatory family and reported together.

## 5. Power *(simulated)*

150 simulated experiments per cell; 24 decisions per participant; 20% attrition in session 2. Power is the share of simulations with a significant estimate of the correct sign.

| Scenario | N | H1 possession | H3 ln λ | H2 −ln β |
|---|---|---|---|---|
| β = 0.7, λ = 1.5, response noise 0.5 | 120–320 | 1.00 | 1.00 | 1.00 |
| β = 0.85, λ = 1.2, noise 0.5 | 160 / 240 | 1.00 | 0.94 / 1.00 | 0.83 / 0.96 |
| β = 0.7, λ = 1.5, noise 0.9, 15% random responders | 160 / 240 | 1.00 | 0.99 / 1.00 | 0.93 / 0.99 |
| β = 0.85, λ = 1.2, noise 0.9, 15% random responders | 160 / 240 / 320 | 0.92 / 0.99 / 1.00 | 0.45 / 0.63 / 0.87 | 0.38 / 0.49 / 0.63 |
| Rational (β = 1, λ = 1) | 120–320 | 0.01–0.05 | 0.00–0.03 | 0.01–0.06 |

**Reading.** The possession effect is detected reliably even under noise. Separating β from λ for mild effects needs about 240 completers or more; the 208 planned would leave the β estimate underpowered if effects are mild and responses are noisy. Recruit 320 if the budget allows. The false-positive rate under the rational model stays at or below about 6%.

## 6. The main threat to identification, and its remedy

H2 identifies β < 1 only if participants apply the same loss-aversion weight λ when they plan as when they execute. If they ignore it when planning, a developer with β = 1 and λ = 1.5 still shows a "lapse". In simulation this gave a false-positive rate for H2 of **0.89–1.00** across N = 120–320 *(simulated)*.

**Remedy: add a fourth condition.** P_hold: the participant already holds the artifact today and commits to improving it next week. Comparing P_hold with P (artifact not yet received) tests whether λ enters at the plan stage. If it does not, report H2 as a joint test of β < 1 and plan-stage inattention to possession, and rely on H1 and H3 as the confirmatory tests. Cost: 8 more decisions per participant (32 in total).

## 7. Review module (P3, P7, P8): outline only, power not computed

- **Appearance (P3, P7).** Participants review the same code diffs; authorship label (LLM or human) is crossed with actual authorship and with seeded maintainability defects. Outcomes: defects found, time per changed line, approval decision. The label effect at equal actual authorship isolates label-driven automation bias; the true-authorship effect isolates the appearance (fluency) wedge.
- **Default (P8).** Vary the keystroke cost of rejecting an inline suggestion and the quality of suggestions. Outcome: acceptance rate; the model predicts acceptance varies more with rejection cost than with quality.
- Needs its own power analysis once effect sizes from the refactoring module and a pilot are available.

## 8. Other threats and limits

- **External validity.** Short stated-cost tasks differ from real codebases; the within-subject comparison removes individual differences but not task artificiality.
- **Demand effects.** Participants may infer the purpose from the P/A contrast; the cover story and a debrief address this, and condition order is randomized.
- **Naivety.** The lapse logic assumes a naive planner. A sophisticated planner would not commit to what she expects not to do; H2 would then be understated.
- **Ethics.** Real stakes, a debrief about the purpose, and approval from the institution's review board before any recruitment.
- **Preregistration.** Register hypotheses, the primary model and exclusion rules before data collection; this file can be the basis.

## 9. Low-budget variant: one session, possession effect only

Drop session 2 and the plan condition. Each participant makes 8 decisions in condition C and 8 in condition A in a single sitting of about 20–25 minutes. Only H1 (the possession effect) is tested; β and λ cannot be separated and the lapse (H2) is not tested. Simulated power for H1 (`power_one_session.py`, 200 simulations per cell, two-sided 5%):

| Scenario | N = 60 | 80 | 100 | 120 |
|---|---|---|---|---|
| Rational (β = 1, λ = 1): false-positive rate | 0.02 | 0.02 | 0.01 | 0.03 |
| Mild (β = 0.85, λ = 1.2), noise 0.5 | 0.97 | 1.00 | 1.00 | 1.00 |
| Mild, noisier (noise 0.9, 15% random responders) | 0.59 | 0.72 | 0.88 | 0.86 |
| Weaker (β = 0.9, λ = 1.1), noise 0.5 | 0.73 | 0.81 | 0.87 | 0.92 |
| Weaker, noisier | 0.34 | 0.34 | 0.36 | 0.42 |
| Moderate (β = 0.7, λ = 1.5), either noise level | 1.00 | 1.00 | 1.00 | 1.00 |

**Reading.** About 100 participants is enough for a moderate or mild effect even with noisy responses. If the true effect is weak and responses are noisy, no feasible sample size here reaches adequate power. What is lost relative to the full design: the lapse test (the sharpest evidence for present bias), the separate estimates of β and λ, and the ability to detect plan-stage inattention.
