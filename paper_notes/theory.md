# Theory: flat vs. phase-dependent pricing under bursty demand (draft for the manuscript)

Status: Propositions 1-3 have short proofs below and were checked numerically (results/theory_props.md,
results/theory_verify.md). Proposition 4 is a local (second-order) result; its numerical check shows it is accurate for
small demand dispersion and not beyond. Everything is in the quasi-static model; see Section 5 for when that is reasonable.

## 1. Model and assumptions
Phases k = 1..K occur with long-run probabilities pi_k > 0. In phase k the request rate is lambda (a decision of users);
the queue is in steady state at that rate (quasi-static).
- **A1 (delay).** d: [0,c) -> [1,inf) is C^2, strictly increasing, convex, d -> inf as lambda -> c. d(lambda) is the mean
  sojourn time; user delay cost is 1 per unit of time. (The M/M/c Erlang-C sojourn satisfies this; verified numerically
  for c = 1, 2, 7, 45, and it is flat to machine precision for small lambda when c is large.) Total delay cost
  D(lambda) = lambda d(lambda); toll function t(lambda) = lambda d'(lambda) = D'(lambda) - d(lambda). Note t' = d' + lambda d'' > 0.
- **A2 (demand).** Inverse demand in phase k: P_k(lambda) = P (1 - lambda/Lambda_k), P > 1. Gross value B_k(lambda) = int_0^lambda P_k.
  Users observe the phase and the posted price p_k (not the queue). They join until marginal value equals full cost:
  P_k(lambda) = p_k + d(lambda). Demand potentials Lambda_k may differ across phases.
- **A3 (welfare).** W_k(p) = B_k(lambda_k(p)) - D(lambda_k(p)) with lambda_k(p) the equilibrium rate; W(p) = sum_k pi_k W_k(p).
  A marginal serving cost c0 per request is handled by replacing P with P - c0 (Section 4).

## 2. Results
**Lemma 1.** For p < P - 1 the equilibrium rate lambda_k(p) is unique and C^1, with derivative -kappa_k(p), where
kappa_k = 1 / (P/Lambda_k + d'(lambda_k)) > 0.
*Proof.* The map lambda -> P_k(lambda) - d(lambda) is strictly decreasing from P - 1 > 0; apply the implicit function theorem. QED

**Lemma 2 (first best).** w_k(lambda) = B_k(lambda) - D(lambda) is strictly concave (B_k concave, D'' = 2d' + lambda d'' > 0). Its
unique maximiser lambda_k* > 0 solves P_k(lambda) = D'(lambda). It is implemented by the price p_k* = t(lambda_k*).
*Proof.* P_k(0) = P > 1 = D'(0) gives lambda_k* > 0. At equilibrium p = P_k(lambda) - d(lambda); at lambda_k* this is D' - d = t. QED

**Proposition 1 (tolls rise with demand).** If Lambda_j > Lambda_k then lambda_j* > lambda_k* and p_j* > p_k*.
*Proof.* P (1 - lambda/Lambda) is strictly increasing in Lambda for lambda > 0, so P_j(lambda_k*) > P_k(lambda_k*) = D'(lambda_k*).
Since P_j - D' is strictly decreasing in lambda and positive at lambda_k*, its root lambda_j* exceeds lambda_k*. Since t' > 0, p_j* > p_k*. QED

**Proposition 2 (flat price).** (a) W_k'(p) = -kappa_k(p) (p - t(lambda_k(p))) and W_k is strictly increasing on p < p_k*,
strictly decreasing on p > p_k*. (b) If the Lambda_k are not all equal, no flat price attains the first best: W(p) < W^FB for every p.
Every optimal flat price p^f satisfies min_k p_k* < p^f < max_k p_k* and sum_k pi_k kappa_k(p^f)(p^f - t(lambda_k(p^f))) = 0.
If all Lambda_k are equal, the flat price p^f = p* is first best.
*Proof.* (a) Differentiate: W_k' = (B_k' - D') lambda_k' = (P_k(lambda) - d - lambda d')(-kappa_k) = -kappa_k (p - t(lambda_k)),
using P_k(lambda_k) = p + d(lambda_k). By Lemma 2, w_k is strictly increasing in lambda below lambda_k* and decreasing above, and
lambda_k(p) is strictly decreasing, so W_k increases for p < p_k* and decreases for p > p_k*. (b) W_k(p) <= W_k(p_k*) with
equality only at p = p_k*; if the p_k* differ (Proposition 1) no p equals all of them. For p <= min p_k* every W_k is nondecreasing
and at least one is strictly increasing, so W' > 0; symmetrically W' < 0 for p >= max p_k*. The first-order condition is W'(p^f) = 0. QED

**Proposition 3 (exact loss).** For any flat price p,
Loss(p) = W^FB - W(p) = sum_k pi_k int_p^{p_k*} kappa_k(s) (t(lambda_k(s)) - s) ds >= 0, each integral being nonnegative.
*Proof.* W_k(p_k*) - W_k(p) = int_p^{p_k*} W_k'(s) ds and part (a) of Proposition 2. QED
(Checked: code trace 4.8265 direct vs 4.8264 by the integral; conversation trace 31.8094 vs 31.8093.)

**Proposition 4 (local loss, Harberger-type).** Let omega_k = kappa_k (1 + kappa_k t'(lambda_k*)). Then W_k''(p_k*) = -omega_k and
Loss(p^f) = (1/2) sum_k pi_k omega_k (p_k* - pbar)^2 + o(max_k (p_k* - pbar)^2),  pbar = sum pi_k omega_k p_k* / sum pi_k omega_k.
Consequently if Lambda_k = Lbar (1 + s z_k), the loss is C s^2 + o(s^2) with C = (1/2)(Lbar dp*/dLambda)^2 sum pi_k omega_k (z_k - zbar_omega)^2 > 0:
it is zero for Poisson-like (s = 0) and grows quadratically with dispersion.
*Proof.* From W_k' = -kappa (p - t(lambda(p))): W_k'' = -kappa'(p)(p - t) - kappa (1 - t' lambda') and at p = p_k* the first term
vanishes and lambda' = -kappa. Taylor-expand each W_k around p_k* and maximise the quadratic over p. By Proposition 1 and the implicit
function theorem p_k* is C^1 in Lambda_k. QED
Numerical check (results/theory_verify.md): conversation trace, spread 0.02 / 0.05 / 0.1: exact 0.0363 / 0.2241 / 0.8704
vs formula 0.0349 / 0.2189 / 0.8765; code trace, spread 0.02: 0.1747 vs 0.1832. The formula overshoots for large spreads
(code trace spread 0.3: exact 2.92 vs 12.7), so it is a local result only. **The earlier "Harberger" column in results/theory_check.md uses
kappa instead of omega and understates the loss by roughly an order of magnitude; it should not be used.**

**Remark (what is NOT true).** A provider that prices as if every phase had the mean potential charges p_blind = p*(Lbar). Whether this is
above or below the optimal flat price depends on the curvature of Lambda -> p*(Lambda): code trace p_blind = 6.06 vs p^f = 1.85
(above), conversation trace 5.36 vs 6.38 (below). "Ignoring burstiness underprices" is therefore not a general result.

## 3. Relation to the closest paper (McDougall & Sankaralingam, EC'26, arXiv 2609.40098)
I read the abstract, the related-work paragraph and the limitations in the PDF text; I did not check their proofs.
- Their result is a separation theorem for three-dimensional private types (willingness to pay, task volume, time preference);
  "optimal per-task prices are volume-independent", which they present as support for flat per-token pricing.
- That is a statement about linearity in volume, not about constancy over time. Our result is about time: even when the
  price is linear in volume, a price that does not vary with the demand phase loses welfare (Proposition 2).
- They state they "abstract from queueing dynamics and capacity constraints; incorporating stochastic demand would connect the
  framework to dynamic pricing and congestion externalities" - the gap this paper fills. So the two results are complementary,
  not contradictory; the paper should say so explicitly and not describe ours as "breaking" theirs.
- Open modelling gap: combining their private-information screening with our phase process (does the separation theorem survive
  when the cost of a tier depends on the phase?) is the natural next theorem.

## 4. Marginal serving cost and market price ratios (results/cost_calibration.md)
With serving cost c0 the planner's choke value is P - c0 and users pay c0 + p_k. Observed list-price ratios are small: 2x time-of-day
(DeepSeek), 3.5-4x priority vs flex. Calibrating c0 so the model's peak/off-peak price ratio equals 4x or 2x:
- code trace: c0 ~ 3.9 (4x) and ~ 8.4 (2x); flat-price loss stays 10.0% and 9.9% of first best;
- conversation trace: c0 ~ 1.6 (4x) and ~ 4.8 (2x); flat-price loss 6.3% and 6.1%.
So the extreme ratio at c0 = 0 (31x, 7x) is an artefact of ignoring cost; matching market ratios does not make the flat-price loss disappear.
c0 itself is not observed (only its effect on the ratio is calibrated), so this is consistency, not identification.

## 5. When is the quasi-static approximation reasonable?
It treats the queue as being in steady state within each phase. It underestimates delay in short bursts. The exact CTMC check
(code-trace MMPP, dwell time multiplied by f) is in results/theory_check.md Part C when finished: f = 0.2: flat loss 12.3%, f = 1: 20.9%
of the phase-dependent welfare (an exact-CTMC planner comparison, different normalisation from the quasi-static numbers above).
