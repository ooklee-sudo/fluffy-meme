# Direction A: Strengthening the Theory (revision package for "Pricing Forgetting")

Status: draft text for insertion into v4_1. The new results (Propositions 9–11) were checked
numerically (brute-force developer best responses, exhaustive knapsack on 2,000 random
instances, grid search for the investment threshold); the checks agree with the closed forms below.

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

## 3. Honest assessment of what remains

- Props 10 and 11 are closed-form and simple. Their value is the *insight* (a ceiling on audit power; a
  threshold for investment), so the Discussion must carry that argument, not the algebra.
- The audit game is still complete-information. The step that would most raise the paper's theoretical depth
  is **private information**: the developer knows ρ_i, the regulator observes only a noisy test signal. That is a
  screening/mechanism-design problem (optimal penalty schedule contingent on signals; possible
  separation between honest and under-unlearning types) and would answer the obvious reviewer question,
  "why does the regulator not just observe the residue?" I have not derived it here.
- Prop 9 treats p_i as audit budget on a common test; heterogeneous δ_i and a regulator choosing δ jointly
  is a straightforward but longer extension.
- Experiments do not test the new propositions. Even so, the claim now rests on theory, so the experiment can
  stay as an illustration. P8's test (public vs rotated benchmark) is cheap to add if you want one empirical hook.
