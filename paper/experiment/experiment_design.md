# Experiment Design (Pre-registration Draft): Loss Aversion and Sunk Cost in AI-Repair Escalation Decisions

Status: design only, not run. Companion to `paper/paper_ISR.md` (Section 4.8, Appendix F). Simulation support: `simulate_experiment.py`, `results_experiment_sim.txt`.

## 1. Purpose
Estimate, from incentivized choices, (i) the loss-aversion weight Λ on per-attempt payments, (ii) the sunk-cost discount γ, (iii) the choice noise τ, and test the predictions that follow from Propositions 10–11.

## 2. Hypotheses (directional, to be pre-registered)
- **H1 (loss aversion).** At equal rational depth, participants make fewer attempts under per-attempt pricing than under a success fee. Prediction from Prop. 10(a): depth_A < depth_B when Λ > 1.
- **H2 (sunk cost).** Displaying cumulative spending on the current defect increases the number of attempts beyond the rational depth (Prop. 11(a)); the effect is larger for later attempts.
- **H3 (contract preference).** When the two contracts have equal expected cost, a majority choose the success fee; the share is higher in the loss-framed condition.
- **H4 (offsetting).** Under per-attempt pricing, the mean deviation from the rational depth is smaller when both biases are active (cumulative-spend display on) than the sum of the separate deviations (Prop. 11(c)). Exploratory.
- **H5 (belief updating).** Elicited success probabilities after failures decline more slowly than the Bayesian q_n = a/(a+b+n) (under-inference from failures) or faster (algorithm aversion); the direction is exploratory.

## 3. Design
- **Participants.** Software professionals (developers, QA, engineering managers) recruited on an online research panel, with filters for current or recent software employment and at least two years of experience; N = 400 target plus 15% attrition margin (see §6). A separate pilot of 20 participants checks comprehension and timing.
- **Task.** Each participant manages 12 simulated defects. For each defect, an AI service proposes patches. After each failed patch, the participant chooses *request another attempt* or *escalate to a human engineer*. A defect ends on success or escalation. Attempt outcomes are generated from a hidden defect-specific probability p ~ Beta(a, b) with (a, b) = (0.2, 0.5), displayed to participants as an explained distribution ("most defects are either easy or very hard") together with the current posterior success probability q_n after each failure.
- **Payoffs.** Each participant starts each defect with an endowment equal to the value of the defect; costs are charged in experimental points converted at a fixed rate into a bonus: the human escalation cost H, the firm's own verification cost v per attempt, and the contract-specific vendor payment. Bonus equals total points remaining on a randomly selected set of 3 defects (random-lottery incentive), so that each decision matters and mental accounting of the whole session is limited.
- **Contract (within-subject, counterbalanced).** (A) per-attempt fee w ∈ {1, 2, 4}, charged for every attempt; (B) success fee f ∈ {0.3H, 0.5H, 0.7H}, charged only on success. Levels are crossed with H ∈ {60, 100, 150} points and chosen so that the rational depth under A and B coincide on matched defect pairs.
- **Between-subject factors (2 × 2).** (i) *Sunk-cost salience*: the screen shows (on) or hides (off) the cumulative points spent on the current defect. (ii) *Payment framing*: payments described neutrally ("fee per attempt") or with a loss frame ("you pay even if the attempt fails" for A; "you pay nothing unless the fix works" for B).
- **Contract choice block (end of session).** Six choices between a per-attempt contract and a success fee with equal rational expected cost (computed from the displayed distribution), and a Becker–DeGroot–Marschak elicitation of willingness to pay for each form, to estimate Λ model-free.
- **Belief elicitation (subset of decisions).** After randomly selected failures, participants state the probability that the next attempt succeeds, incentivized with a quadratic scoring rule.
- **Controls.** Comprehension quiz (must pass to proceed), two attention checks, demographics, experience, risk and loss-aversion survey items (Gächter et al. 2010-style lottery task).

## 4. Measures
Primary: number of attempts per defect (depth); deviation from rational depth N*; contract choices; WTP gap between forms; stop/continue decisions at each state (n, contract terms).
Secondary: response times; elicited beliefs; accuracy of the participant's own post-task estimate of spending.

## 5. Analysis plan
1. **Reduced form.** Mixed-effects models with participant random effects. Depth (count) with negative binomial; deviation from N* with linear mixed models; contract choice with mixed logit. H1: contract form effect (within); H2: salience effect (between) and its interaction with attempt index; H3: share against 50% (binomial test) and framing effect.
2. **Structural.** Pooled discrete-choice likelihood over all stop/continue decisions:
   P(continue | n, terms) = Λ_logit((q_n X − (1 − γ·1[n ≥ 1]) Y) / τ),
   with X = H, Y = Λ w + v under A, and X = H − f, Y = v under B; participant random effects on τ; bootstrap standard errors clustered by participant. Hypotheses: Λ > 1 (H1), γ > 0 (H2), γ larger with spend display on.
3. **Robustness.** Alternative sunk-cost specifications (additive in cumulative spend; saturating), probability weighting, heterogeneity in (Λ, γ) by experience, and exclusion of participants failing attention checks.
4. **Multiple testing.** Holm correction over the five hypotheses.
5. **Exclusions** (pre-registered): failed comprehension after two attempts, failed both attention checks, completion time below 1/3 of the pilot median.

## 6. Sample size and power
- Simulation (`simulate_experiment.py`, 40 replications per size, true Λ = 1.8, γ = 0.25, τ = 1.5): with 100 / 200 / 400 participants × 12 defects the structural estimator recovers Λ = 1.87 ± 0.32, 1.80 ± 0.22, 1.83 ± 0.12; γ = 0.26 ± 0.11, 0.24 ± 0.08, 0.26 ± 0.04 (mean ± sd across replications). 400 participants gives sd 0.12 for Λ and 0.04 for γ.
- Reduced-form tests (two-sided α = .05, 80% power): between-subject effect d = 0.3: 175 per cell; d = 0.2: 393 per cell. Within-subject (contract crossover) dz = 0.3: 88 participants; dz = 0.2: 197.
- With 400 participants in the four between-subject cells (100 per cell), the within-subject tests are well powered (H1, H3) and the between-subject salience test (H2) detects d ≈ 0.4; if smaller effects matter, raise to 700 (175 per cell).

## 7. A single participant is not sufficient
One developer yields at most a dozen defect decisions with an unknown noise level; neither Λ and γ, which are population parameters, nor any between-condition effect can be separated from that person's idiosyncrasies. One participant is useful only for debugging the interface in the pilot.

## 8. Procedure and timing
Instructions and quiz (4 min) → practice defect (2 min) → 12 defects (12 min) → contract-choice block and BDM (5 min) → survey (3 min). About 26 minutes.

## 9. Ethics, data, and registration
Minimal risk; informed consent; no personal data beyond panel IDs; data stored under restricted access; IRB approval required before launch; pre-register hypotheses, exclusions, and analysis on a public registry (OSF or AsPredicted) before data collection; share de-identified data and code.

## 10. Budget (rough estimate; verify current panel fees)
Base pay about USD 4 plus average bonus about USD 4 per participant; 400 participants plus pilot: about USD 3,500 before platform fees, roughly USD 4,500–5,000 with fees.

## 11. Limitations
Vignette-type incentives are small relative to real engineering costs; participants are online-panel professionals, not purchasing decision makers; the Beta process is displayed, whereas real firms must learn it; sunk-cost and loss-aversion parameters estimated here are those of individuals in a simulated task, not organizations. A follow-up with engineering managers from a partner firm is the natural extension.
