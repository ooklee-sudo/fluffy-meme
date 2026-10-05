# Direction A: Strengthening the Theory (revision package for "Pricing Forgetting")

Status: draft text for insertion into v4_1. Propositions 9–13 are new; all are checked numerically by
`verification/verify_propositions.py` (brute-force developer best responses, exhaustive knapsack,
grid search; Props 1, 2, 4, 5, 7, 8 are re-checked as well). All checks pass. Section 3 below resolves the five
limitations listed in the first version of this note.

---

## 0. Strategy in one paragraph

The duality (Prop 1), additive bias (Prop 3) and the audit condition (Prop 6) are too elementary to
carry a MISQ theory contribution on their own. Direction A shifts the paper's center of gravity from
"Shapley pricing" to **verification under inscrutability**: the developer both performs and measures
removal, so *what a regulator can enforce* is the paper's real subject. The Shapley material becomes
the measurement layer (Sections 3–4, shortened); the new core is a richer enforcement model with
three additions that each overturn a conclusion of the one-request, fixed-test model:

| New result | What it overturns / adds | IS hook |
|---|---|---|
| Prop 9 Triage | Under audit capacity, deterrence is rationed; the hardest-to-forget data is protected *least* (endogenous version of P3) | Berente et al. 2021 inscrutability; Angst et al. 2017 (institutional pressure) |
| Prop 10 Concealment ceiling | Audit power is **not** unboundedly substitutable: if the developer can cheaply tune unlearning to the known test, deterrence collapses above a threshold regardless of audit intensity | Wall et al. 2016 selective violation |
| Prop 11 Unlearnability investment | Converts the verbal claim in §5.1 into a theorem: enforcement and ex ante investment in unlearnability are complements | Gregory et al. 2021 (platform learning loop) |

---

## 1. New text: Section 5.4 onward (English, ready to paste)

Notation carried over from Section 5: developer's saving from approximate removal Δ = C − c;
revenue from residue βρ; gain from under-unlearning g = Δ + βρ; penalty cap F̄; audit probability p;
audit power δ; deterrence threshold θ = g/F̄.

### 5.4 Many Requests and Audit Triage

A developer rarely faces one request. Suppose there are m requests, request i with gain g_i = Δ_i + βρ_i,
penalty cap F̄_i, and harm H_i if residue is retained. Write θ_i = g_i/F̄_i. The regulator has an audit
capacity B (the expected number of audits it can run) and a test of given power δ common to all requests.
It chooses audit probabilities p_i ∈ [0,1] with Σ_i p_i ≤ B and maximizes the harm it prevents.
By Proposition 6, request i is deterred if and only if p_i δ ≥ θ_i.

**Proposition 9 (Triage).** (a) Request i can be deterred only if θ_i ≤ δ, and the cheapest way to
deter it uses p_i = θ_i/δ. (b) The regulator's problem is a 0–1 knapsack: choose a set D of requests to
deter, maximizing Σ_{i∈D} H_i subject to Σ_{i∈D} θ_i/δ ≤ B. (c) Order requests by H_i/θ_i, decreasing, and
deter them in this order until the first request j that does not fit. This yields at least OPT − H_j.
(d) Let ρ_i = r_i with negligible collateral damage, F_i = kφ̂_i, and compare a developer-estimated base
φ̂_i = φ_i − r_i with a third-party base φ_i. Then θ_i^D = (Δ_i + βr_i)/(k(φ_i − r_i)) ≥
θ_i^T = (Δ_i + βr_i)/(kφ_i), the ratio θ_i^D/θ_i^T = φ_i/(φ_i − r_i) increases in r_i, and the maximal
prevented harm under the developer base is weakly lower than under the third-party base.

*Proof.* (a), (b): immediate from Proposition 6 and p_i ≤ 1; extra audits on a deterred request are
wasted and audits below the threshold on an undeterred one prevent nothing, so the problem separates into
choosing D. (c): the LP relaxation of the knapsack is solved by the greedy order, its value equals the
greedy prefix plus a fraction of H_j ≤ H_j, and OPT is at most the relaxation. (d): substitute F_i into θ_i;
every weight is weakly larger under the developer base, so every set feasible under it is feasible under
the third-party base. ∎

*Reading.* Requests that are expensive to deter (large g_i, small F̄_i) are the ones left unprotected.
Large residue r_i raises g_i through βr_i, and, under a developer-set base, also shrinks the penalty base.
So data that is hard to forget is simultaneously the data the developer is most tempted to under-unlearn
and the data the regulator can least afford to protect. This is a **market-level** version of the
individual-bias result in Section 4.2, and it needs no assumption about unlearning mechanics.

### 5.5 Concealment and the Limits of Audit Power

Proposition 6 treats detection power δ as a property of the audit. In practice the developer can tune
its unlearning to the test it expects: suppress the outputs a benchmark probes while leaving the
underlying knowledge in place. Let the developer choose a concealment level x ∈ [0,1] that reduces the
detection probability to δ(1 − x) at cost κx²/2, κ > 0. Write z = pδF for the expected penalty absent
concealment. κ indexes how costly it is to conceal against the auditor's test; secret, rotating or
adaptive tests raise κ.

**Proposition 10 (Concealment ceiling).** The developer's cheapest expected penalty-plus-concealment cost
is ψ(z) = z − z²/(2κ) for z ≤ κ and κ/2 for z ≥ κ. Exact removal is optimal if and only if ψ(z) ≥ g.
Hence (a) deterrence is feasible only if g ≤ κ/2, whatever the audit intensity; (b) when feasible, it
requires z ≥ z̃ = κ(1 − √(1 − 2g/κ)); (c) z̃/g = (2/u)(1 − √(1 − u)) with u = 2g/κ ∈ (0,1], which lies
in (1,2] and is increasing in u: concealment raises the intensity needed to deter by at most a factor of 2,
but only up to the ceiling at which deterrence is lost entirely.

*Proof.* The developer minimizes z(1 − x) + κx²/2 over x ∈ [0,1]. The first-order condition gives
x* = min{1, z/κ}, and substituting gives ψ. ψ is increasing on [0, κ] with ψ(κ) = κ/2 and constant beyond.
Approximating is optimal when g > ψ(z) (ties go to exact removal), which gives the condition; solving
z − z²/(2κ) = g for the smaller root gives z̃. For (c), z̃/g = (κ/g)(1 − √(1 − 2g/κ)); substituting
u = 2g/κ gives the stated form, increasing in u with limits 1 and 2. ∎

**Corollary (design under concealment).** Proposition 7 holds with θ replaced by θ̃ = z̃/F̄. Deterrence is
feasible if and only if g ≤ κ/2 and θ̃ ≤ 1. Raising κ (test secrecy, rotation) is therefore a third lever,
beside p and δ, and it is the only one that restores deterrence when g > κ/2.

*Reading.* Strong audits help only up to a point: once concealment is cheap relative to the gain from
under-unlearning, more audit effort is wasted. This sharpens the claim of Section 7 that evaluation is
enforcement infrastructure: what matters is not only how strong the test is but how hard it is to anticipate.
The relearning results of Section 6.4 are consistent with this mechanism, since over-unlearning that
drives a standard score to zero (ε(∅) < 0) can coexist with recoverable knowledge, but we do not test it.

### 5.6 Investing in Unlearnability

Proposition 6 notes that the exact-removal cost C depends on training-time choices. We now model the
choice. Before requests arrive, the developer chooses s ∈ [0,1] (sharding, modular adapters), at cost
ιs²/2, which lowers the exact-removal cost per request to C̄ − λs; it expects m requests, and the
regulator's enforcement intensity z = pδF is committed beforehand. Let A = c − βρ + z be the expected cost
of approximate removal, g₀ = C̄ − c + βρ, and
Λ = mλ²/(2ι) if mλ ≤ ι, and Λ = λ − ι/(2m) otherwise.

**Proposition 11 (Investment threshold).** The developer invests s_e = min{1, mλ/ι} and removes every
request exactly if and only if z ≥ g₀ − Λ; otherwise it invests nothing and approximates (for z < g₀ − Λ).
Hence (a) the enforcement intensity needed for exact removal falls by Λ, which is increasing in the
number of expected requests m and in the efficiency λ²/ι of the technology; (b) investment is a
complement to enforcement: for z < g₀ − Λ there is no investment at all, and for z ≥ g₀ − Λ the
developer invests even where enforcement alone (z ≥ g₀) would not have deterred it.

*Proof.* Total cost is J(s) = m·min{C̄ − λs, A} + ιs²/2. For s with C̄ − λs ≥ A, J = mA + ιs²/2, which is
minimized at s = 0. For s with C̄ − λs ≤ A, J is convex with derivative −mλ + ιs, so on that region it is
minimized at max{ŝ, s_e}, where ŝ = (C̄ − A)/λ. If s_e < ŝ the region's minimum exceeds J(0) = mA.
If s_e ≥ ŝ, then J(s_e) ≤ mA iff C̄ − A ≤ λs_e − ιs_e²/(2m) = Λ, and the right side is at most λs_e, so this
condition already implies s_e ≥ ŝ. Rearranging with A = c − βρ + z gives z ≥ g₀ − Λ. ∎

*Reading.* A developer that expects many requests rationally commits sunk cost to modular training
precisely when enforcement is credible. This gives the claim "without credible enforcement, developers
have little reason to make it" a formal threshold, and it implies a policy comparison: a regulator can
buy the same deterrence with audits (cost increasing in θ) or by subsidizing investment (raising λ²/ι),
whichever is cheaper at the margin.

---

## 2. How to restructure the paper

**New title (optional):** *Auditing Forgetting: Enforcement, Concealment, and Compensation When Developers Measure Their Own Unlearning.*

**Abstract:** keep the Shapley/measurement sentence short; lead with the enforcement results (triage,
concealment ceiling, investment threshold). Remove the closing sentence listing untested predictions
and put that in Limitations.

**Contribution list (Section 1), suggested order:**
1. Enforcement under inscrutability: audit condition, triage, concealment ceiling, investment threshold (Props 6–11).
2. Measurement: duality and additive bias, so enforcement can rely on consistent values (Props 1, 3–5).
3. Replication exposure (Prop 2) as a design constraint on pricing.
4. Small experiment as illustration.

**Cuts:** Section 3.3 (LOO) to one paragraph; Section 3.4 merging example to a footnote; Sections 6.1–6.3
condensed to ~1 page, with the detailed tables to an appendix. Related work: shrink Data valuation and
Machine unlearning to 2–3 sentences each, and expand compliance and audit literature (Wall et al. 2016,
Angst et al. 2017, plus audit/inspection-game papers from economics).

**New predictions to state (testable, replaces P5/P6 overreach):**
- P7: undeterred requests concentrate on high-g, low-F̄ items (Prop 9).
- P8: unlearning evaluated with a secret or rotated test shows less residue than with a public benchmark when
  concealment is available (Prop 10).
- P9: developers expecting more requests adopt modular training only under credible enforcement (Prop 11).

---

## 3. Resolving the limitations

### 3.1 Prop 9 with heterogeneous, chosen audit power (replaces the common-δ version in 5.4)

Let the regulator choose a test power δ_i for each request at cost eδ_i²/2, and audits at cost a each.
The cost of deterring request i (θ_i ≤ 1) is
K(θ_i) = min over δ ∈ [θ_i, 1] of { aθ_i/δ + eδ²/2 }.

**Proposition 9\* (Triage with chosen power).** (a) K is strictly increasing in θ. In the interior regime
δ* = (aθ/e)^{1/3} ∈ [θ,1] it equals (3/2)e^{1/3}(aθ)^{2/3} and K′(θ) = a/δ*; if δ* = θ it equals
a + eθ²/2; if δ* = 1 it equals aθ + e/2. (b) Without a budget, request i is deterred if and only if
K(θ_i) ≤ H_i, which defines a cutoff θ̄(H_i) increasing in H_i. (c) With a total budget 𝓑, the problem is a 0–1
knapsack with weights K(θ_i); deterring in order of H_i/K(θ_i) until the first request j that does not fit
achieves at least OPT − H_j.

*Proof.* (a) For θ′ > θ the feasible set [θ′,1] ⊂ [θ,1] and the objective is increasing in θ at each δ, so
K(θ) < K(θ′). The regime formulas follow from Proposition 7(b); K′ = a/δ* in the interior regime by the
envelope theorem. (b) is Proposition 7(c) request by request. (c) as in Proposition 9(c). ∎

*Reading.* Allowing power to be chosen does not change the triage conclusion; it sharpens it. Because
K′ > 0, "hard-to-deter" (large θ_i) requests face rising marginal protection costs, so the unprotected set is
the upper tail of θ_i.

### 3.2 Noisy tests (new Proposition 12)

A real test returns a signal that can be positive when no residue exists. Let a test have detection
probability δ if residue is retained and false-positive probability α < δ if the data was removed exactly;
the penalty F is paid on a positive signal.

**Proposition 12 (Youden condition).** Exact removal is optimal if and only if pF(δ − α) ≥ (C − c) + βρ.
Hence the audit "power" in Propositions 6–11 is J = δ − α, Youden's index, not the sensitivity δ.

*Proof.* Exact removal yields −C − pαF; approximate removal yields −c + βρ − pδF. Comparing gives the
condition. ∎

*Reading.* A test with higher sensitivity and a higher false-positive rate may be strictly worse for
deterrence; and honest developers bear an expected penalty pαF, which becomes a deadweight cost if
penalties are not pure transfers. Benchmarks used for compliance should be judged by J, not by recall.

### 3.3 Private information: declare-and-pay (new Proposition 13)

This answers the reviewer question "why does the regulator not just observe the residue?" The residue is
private to the developer and is observed only through an audit. The regulator therefore sets a **liability
rule with self-assessment** (Section 5.3): the developer may keep residual knowledge, must declare the amount
r̂ ≤ r it retains, and pays contributors π per unit declared. An audit (probability p) detects an
undeclared amount with probability δ and imposes a fine f per undeclared unit; z = pδf ≤ pδf̄.
The developer first chooses unlearning effort e ≥ 0 at convex cost c(e), which determines the true residue
r(e) (decreasing, convex), earning revenue β per unit retained. Social harm is h per unit retained, with h > β.
The planner's objective is c(e) + (h − β)r(e).

**Proposition 13 (Declare-and-pay).** (a) Given r, the developer declares truthfully if and only if z ≥ π;
otherwise it declares nothing. Its cost per unit of residue is the **effective price** τ = min{π, z}.
(b) Effort e*(τ) minimizing c(e) + (τ − β)r(e) is nondecreasing in τ, so residue falls continuously with
audit intensity (there is no cliff). (c) With π = h, effort is socially efficient if and only if z ≥ h.
(d) In the linear–quadratic case c(e) = e²/2, r(e) = r₀(1 − e), the effort is clip{(τ − β)r₀, 0, 1}, the welfare
loss from an effective price τ < h is (h − τ)²r₀²/2, and a regulator facing audit cost a with test power δ and
fine cap f̄ chooses z* = h − a/(δf̄r₀²) whenever this is positive (and z* = 0 otherwise), with f = f̄.
(e) The second-best optimum leaves positive residue: r* = r₀(1 − (z* − β)r₀) > r₀(1 − (h − β)r₀).

*Proof.* (a) The developer chooses r̂ ∈ [0,r] to minimize πr̂ + z(r − r̂), linear in r̂ with slope π − z, so
r̂ = r if z ≥ π and r̂ = 0 otherwise (ties go to truthful reporting), and the minimized cost is min{π, z}·r.
(b) The objective c(e) + (τ − β)r(e) has cross-derivative r′(e) < 0 in (e, τ), so e* is nondecreasing in τ by
Topkis. (c) With π = h and z ≥ h we have τ = h and the developer's objective equals the planner's;
if z < h then τ < h and by (b) effort is lower, so strictly lower where the solution is interior. (d) The FOC
e = (τ − β)r₀ gives effort; the planner's objective is quadratic with curvature 1 in e, so the loss is half the
squared effort gap, ((h − τ)r₀)²/2. The regulator minimizes a·z/(δf̄) + (h − z)²r₀²/2 over z ∈ [0,h]
(p = z/(δf̄) ≤ 1; raising f lowers the audit cost of any z, so f = f̄); the FOC gives z*. (e) follows because
z* < h. ∎

*Reading.* (i) Proposition 6's cliff is an artifact of binary effort: with continuous effort, audit intensity
buys partial deterrence, and the optimal regime **tolerates positive residue**, more of it as audits get
costlier (a ↑), tests weaker (δ ↓), fines more capped (f̄ ↓). (ii) The audit condition reappears as z ≥ π: the
fine multiple must cover the damage rate over the detection probability, the Allingham–Sandmo logic of tax
compliance applied to retained knowledge. (iii) The declared amount pins down the compensation flow to
contributors, and π can be calibrated to the third-party Shapley value of the data (Proposition 1), tying
Section 3 to Section 5; the calibration itself is left to applications.

### 3.4 What the closed forms buy: Discussion text for Propositions 10 and 11 (English, paste into Section 7)

*Why closed forms matter here.* Propositions 10 and 11 are simple, and we do not present them as
technical contributions. They matter because each converts a debate about regulation into a falsifiable
threshold. Proposition 10 says that the effectiveness of auditing is bounded above by the developer's cost of
tuning its unlearning to the test, κ, and that the bound binds when the private gain from under-unlearning
exceeds κ/2. In practice this is the Goodhart problem of public unlearning benchmarks: a method that is
optimized against a known benchmark can suppress what the benchmark probes without removing the
knowledge, which is the pattern in which a standard score reaches zero while a relearning attack recovers the
knowledge (Section 6.4). The remedy the model points to is not more audits but less predictable ones:
undisclosed, rotating or adaptive tests that raise κ. Statutory caps matter in the same way, because the
penalty ceiling F̄ (for example the GDPR turnover-based fine ceiling in Article 83(5)) determines θ and thus
whether the threshold is crossed. Proposition 11 gives a threshold for investment: a developer commits to
modular or sharded training (Bourtoule et al. 2021) only if enforcement exceeds g₀ − Λ, and Λ rises with the
number of requests it expects. This implies that credible enforcement and ex ante unlearnability are
complements, and that a regulator may prefer to subsidize or mandate modular training where audits are
costly. Both statements have testable counterparts (Section 4 of this note) and could be wrong.

### 3.5 Empirical hook for the new propositions (design only; not run)

No GPU is available in this environment (no CUDA, no PyTorch), so none of the following has been executed.
The protocol reuses the existing TOFU/Qwen2.5-0.5B pipeline; the full 16-coalition exact-retraining step is
unchanged, and each configuration below needs only the all-groups-unlearned model and the retrained ∅ model.

1. **P8 (concealment).** For each unlearning strength s in the existing grid, add a developer arm that tunes
   unlearning against a public benchmark (gradient ascent plus a suppression/refusal loss on benchmark-format
   questions) with a tuning budget b ∈ {0, 1, 2, 4} (steps), which is the empirical analogue of x and κ.
   Measure (i) public-benchmark score, (ii) a held-out secret test (paraphrased and cross-format questions),
   and (iii) post-relearning performance. Concealment gap = (ii) − (i). Prediction: the gap grows with b and
   saturates (Proposition 10), and it is larger under the public test than under the secret one.
2. **Retrained control.** Apply the same relearning attack to the retrained ∅ model. Required for any reading of
   (iii) as residual knowledge.
3. **P7 (triage).** Re-run with groups duplicated k ∈ {1, 2, 4, 8}. Estimate g_i from relearning recovery and compute the
   protection cost K(θ_i). Prediction: protected set shrinks for high-k groups under a fixed budget.
4. **P9 (investment).** Compare exact-removal cost of a sharded (SISA-style) variant with full retraining, estimate
   λ, ι from measured compute, and check whether the simulated developer's choice matches the threshold z ≥ g₀ − Λ
   (a simulation with measured cost parameters, not a field test).
5. **Statistics.** Five seeds per cell, report intervals; pre-register P7–P9 and the saturation prediction.

---

## 4. Status of the original limitations

| Limitation | Status |
|---|---|
| Props 10/11 simple | Addressed in framing: Discussion text in 3.4 argues the value is the threshold, plus testable predictions |
| Complete information | Resolved in 3.3 (private residue, self-assessed declaration, audit-backed); the cliff disappears and second-best leaves residue |
| Heterogeneous / chosen power in Prop 9 | Resolved in 3.1 (K(θ), greedy bound) |
| Noisy tests (added) | Resolved in 3.2 (Youden index) |
| New props untested empirically | Numerical verification done (`verification/verify_propositions.py`, all pass); GPU experiment designed in 3.5, **not run** |

**Caveats that remain.** The mechanism in 3.3 assumes risk-neutral developers, a single audit per period, linear
fines, and exogenous h; richer screening (signals contingent contracts across several developer types) is not
derived. Numerical verification checks algebra, not empirical truth. The experimental protocol must be run before any
claim of empirical support.
