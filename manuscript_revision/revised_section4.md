# 4. A Formal Model of Choosing and Accepting  *(replacement for Section 4)*

This section formalizes the frame shift. It has three parts: the developer's decision problem, stated as a utility-maximization problem under each regime (4.1–4.3); a dynamic extension (4.4–4.6); and a game among vendors, an organization, and developers, with its solution concept and equilibrium (4.7). All proofs are in Online Appendix B. Every closed form was also checked against a brute-force evaluation of the problem it solves (`verify_model.py`).

## 4.1 Environment

**Task.** A task can be implemented expediently (E) or with quality (Q). A task that ends as E imposes a rework cost R > 0, incurred at date 2. The rework cost R is task-specific, drawn from a continuous distribution F with positive density on (0, ∞), and known to the developer when she decides. Developer time is valued at v per unit. Q requires a units of time more than E.

**Dates.**
- Choice regime (no assistant): the developer decides at date 0 how the task will be built at date 1.
- Acceptance regime (assistant): an artifact arrives at date 1. All of the developer's decisions are taken at date 1, and rework, if any, falls at date 2.

**Artifact (acceptance regime).** The artifact is an instance of E with probability q (the model's maintainability-defect rate) and an instance of Q with probability 1 − q.
- Inspecting it takes time k, drawn from a continuous distribution G, independent of R.
- Refactoring a detected instance of E into Q takes time r.
- Each artifact is *noticed* without inspection, if it is an instance of E, with probability ηφ (η ≤ ½).
- With probability α it is *accepted by default*, i.e. no deliberation takes place. Default acceptance applies only to artifacts the developer has not noticed to be defective.

**Behavioral parameters.** The rational benchmark is β = φ = λ = 1 and α = 0.

| Symbol | Name | Role |
|---|---|---|
| β ∈ (0,1] | present bias | weight on all future relative to present payoffs |
| φ ∈ (0,1] | perception | perceived defect rate is φq, and noticing probability is ηφ |
| α ∈ [0,1) | default share | share accepted without deliberation |
| λ ≥ 1 | loss aversion | weight on the time cost of changing a possessed artifact |

**Self-admission.** A developer who knows a shortcut is in the code self-admits it with probability σ. A developer who is unaware of the shortcut self-admits with probability σφ, proportional to the risk she perceives.

## 4.2 The developer's utility and beliefs

**Preferences.** At date t the developer maximizes the decision utility

U_t = u_t + β Σ_{τ>t} δ^{τ−t} u_τ,  with u_τ = −v·(time spent at τ) − (rework cost incurred at τ),

where δ ≤ 1 is the long-run discount factor. The weight λ ≥ 1 multiplies time spent changing or removing an artifact already in hand. This is the standard gain–loss specification, with retaining the artifact as the reference point. Welfare is evaluated with β = λ = 1.

**Beliefs.** The developer believes the artifact is E with probability φq. She knows the noticing technology. When deciding whether to inspect an artifact she has not noticed to be defective, she values the event "E and not noticed" at q̃ ≡ φq(1 − ηφ). This neglects the information in the absence of a defect signal. A Bayesian posterior would divide by 1 − ηφ·φq. We call this *noticing neglect* and keep it as a behavioral assumption, because it keeps the closed forms below tractable. Replacing q̃ by the Bayesian posterior preserves every sign result.

**Sophistication.** The developer is *naive*. At date 0 she believes that her date-1 self will not be present biased (β = 1), although she does expect to feel loss aversion λ tomorrow as she does today. Naivety matters only for planning, and so only for the lapse rate in 4.3.

## 4.3 The developer's decision problems

**Choice regime.** At date 0 the developer compares Q and E. Choosing Q instead of E costs a units of time at date 1 and avoids the rework R at date 2:

U₀(Q) − U₀(E) = −βδ·v·a + βδ²·R.

She chooses E if and only if

  v·a > δ·R.  (1)

Present bias cancels, because it scales both sides equally.

**Acceptance regime.** The date-1 decision tree is solved by backward induction.

1. *Refactoring.* A detected instance of E is refactored if and only if it improves U₁. The cost r is incurred now and the saving R comes at date 2:

   λ·v·r < β·δ·R.  (2)

2. *Inspection.* An unnoticed artifact that is not accepted by default is inspected if and only if the cost of inspecting is below the expected gain. Inspecting costs v·k now. It pays only if the artifact is E (perceived joint probability q̃) and refactoring is worthwhile, in which case the gain is βδR − λvr. So she inspects if and only if

   v·k < q̃ · max{0, βδR − λvr}.  (3)

3. *Outcome.* Debt remains when the artifact is E and is not both detected and refactored. Let σ be as in 4.1.

**Debt probabilities.** Let ρ(R) = 1[λvr < βδR] indicate that refactoring is worthwhile. Then

D_C(v) = P(E chosen) = F(va/δ),

D_A(v) = q · E_R[ ηφ(1 − ρ) + (1 − ηφ)(1 − (1 − α) ρ · G(q̃·(βδR − λvr)/v)) ].

D_A*(v) denotes D_A in the rational benchmark.

**Plans.** At date 0 the naive developer plans to refactor a detected instance if and only if λvr < δR, because she expects her date-1 self to have β = 1. Her date-1 self then refactors if and only if (2) holds. A *lapse* is the event "planned but not carried out":

  βδR ≤ λvr < δR.  (4)

**Three statistics.**
- The *self-admitted share* is S = P(self-admitted | debt).
- The *possession effect* is P = P(defer refactoring | detected E, artifact in hand, r = a) − P(E chosen ex ante at the same cost) = F(λva/(βδ)) − F(va/δ).
- The *lapse rate* is the probability of event (4), per detected instance of E. The Section 4.3 figure of 0.21 is the *joint* probability q·P(4), the probability that the artifact is E and a plan lapses. We report the joint probability and state this in the text.

## 4.4 Results for the single decision

**Result 1 (decomposition).** D_A(v₁) − D_C(v₀) = [D_A*(v₀) − D_C(v₀)] + [D_A*(v₁) − D_A*(v₀)] + [D_A(v₁) − D_A*(v₁)]. The first term (price effect) is ≤ 0 if r ≤ a and k = 0. The second (acceleration effect) is ≥ 0 if v₁ ≥ v₀. The third (behavioral wedge) is ≥ 0, and > 0 if any wedge binds on a set of tasks of positive probability.

*Proof.* The decomposition is an identity (add and subtract D_A*(v₀) and D_A*(v₁)).
- *Price effect.* With k = 0 and β = φ = λ = 1, every artifact is inspected, so D_A* = q·F(vr/δ) ≤ F(va/δ) = D_C when r ≤ a and q ≤ 1.
- *Acceleration effect.* For fixed (R, k), raising v weakly lowers the left side of (3) relative to its right side and weakly tightens (2). So debt is pointwise weakly increasing in v.
- *Wedge.* Each wedge weakens (2) or (3) pointwise. β < 1 and λ > 1 lower βδR − λvr. φ < 1 lowers q̃ (which is increasing in φ because η ≤ ½) and lowers the noticing probability. α > 0 removes inspections. Debt is therefore pointwise weakly higher. It is strictly higher on any set of positive probability where a wedge changes a decision. ∎

**Result 2 (observational equivalence and separation).**
(a) If D_A(v₀) < q, there is v₁ ≥ v₀ with D_A*(v₁) = D_A(v₀).
(b) In the rational benchmark, S = σ, P = 0, and the lapse rate is 0, for all v, q and G.
(c) Under the wedges, S < σ if and only if φ < 1 and some debt is undetected. P > 0 if and only if β < 1 or λ > 1. The lapse rate is positive if and only if β < 1.

*Proof.*
(a) D_A* is continuous and weakly increasing in v (Result 1, assuming G continuous). D_A*(v₀) ≤ D_A(v₀) by the wedge. As v → ∞, nothing is refactored and D_A* → q > D_A(v₀). The intermediate value theorem gives v₁.
(b) Detected-but-unrefactored debt is admitted with probability σ, and with φ = 1 undetected debt is too, so S = σ. At r = a the date-1 refactoring condition is the ex ante condition (1), so P = 0. Planning and execution coincide when β = 1, so there are no lapses.
(c) S = σ·[P(det, ¬ref) + φP(undet)] / [P(det, ¬ref) + P(undet)], which is below σ if and only if φ < 1 and P(undet) > 0. P > 0 iff λ/β > 1, because F has positive density. The lapse event (4) has positive probability iff β < 1, because λ cancels from the two sides of (4). ∎

**Result 3 (reliability paradox).** Let inspection time be uniform on [0, K], B ≡ βδR − λvr > 0 constant, and q̂ ≡ vK/[φ(1 − ηφ)B]. Then

  D(q) = q(1 − ηφ)[1 − (1 − α)·min{1, q/q̂}].

D is *non-monotone* in q if α < ½. It is decreasing in q on (q*, q̂), so a more reliable model produces more debt there, and increasing elsewhere, where q* = q̂/[2(1 − α)]. If α ≥ ½, D is increasing in q everywhere.

*Proof.* The inspection probability is min{1, q/q̂}. For q ≥ q̂, D = αq(1 − ηφ), which is increasing. For q < q̂, D′(q) = (1 − ηφ)[1 − 2(1 − α)q/q̂], which is negative iff q > q*, and q* < q̂ iff α < ½. ∎

## 4.5 Dynamics: debt traps

Let H be the stock of unresolved debt and let refactoring become harder with the stock, r(H) = r₀(1 + γH). In each period n artifacts arrive. A share p of the artifacts not accepted by default is inspected. In this section p is exogenous, so φ, η and K do not enter. A detected instance of E is refactored if and only if (2) holds at r(H). A fraction μ of the stock is repaid each period, so

  H_{t+1} = (1 − μ)H_t + I(H_t; β),  I(H; β) = A + C·F(λvr₀(1 + γH)/(βδ)),

where A = nq[1 − (1 − α)p] and C = nq(1 − α)p. Steady states solve I(H; β) = μH.

**Result 4 (debt traps and hysteresis).** Let rework costs be lognormal with median R_m and log-dispersion s, ε ∈ (0, ½), and z = Φ⁻¹(1 − ε). A low-debt state and a trap, both stable and separated by an unstable steady state, coexist whenever β ∈ (β₁(ε), β₂(ε)) with

β₁(ε) = λvr₀[1 + γ(A + Cε)/μ] / (δR_m e^{−sz}),  β₂(ε) = λvr₀[1 + γ(A + C(1 − ε))/μ] / (δR_m e^{sz}).

The interval is non-empty if e^{2sz} < [1 + γ(A + C(1 − ε))/μ] / [1 + γ(A + Cε)/μ]. Because the closed-form condition is only sufficient, its union over ε recovers the region exactly in the paper's illustration. In the illustration the region is β ∈ (0.646, 0.843).

*Proof.* Appendix B. The bounds follow from requiring the sigmoid F(·) to cut the line μH from above at three points. The result was verified numerically.

## 4.6 Learning

Let q̂ₜ = φq evolve with learning speed κ. Developers learn from inspected artifacts, an unbiased sample, and from rework they attribute to generated code, which occurs with probability θ per instance of undetected debt:

  q̂′ = q̂ + κ[s(q̂) + θ(1 − s(q̂))](q − q̂),

where s(q̂) is the inspection probability and inspection takes at least k_min. Define the threshold belief q̂_c by s(q̂) = 0 for q̂ ≤ q̂_c.

**Result 8 (self-confirming complacency).** (a) If θ > 0 or q̂₀ > q̂_c, then q̂ → q. (b) If θ = 0 and q̂₀ ≤ q̂_c, no one inspects, no evidence is observed, and the belief is self-confirming. (c) In case (b), a mandate requiring inspection for T periods removes the wedge permanently if and only if (1 − κ)^T(q − q̂₀) < q − q̂_c.

*Proof.* Appendix B. Part (c) follows from the geometric convergence q − q̂_T = (1 − κ)^T(q − q̂₀) under mandatory inspection, together with the fact that beliefs above q̂_c sustain inspection.

## 4.7 The strategic extension: a formal game

### 4.7.1 The game

**Players.** Vendors j = 1,…,J (J = 1 is a monopoly; J ≥ 2 is Bertrand competition), a developer D (a representative developer, with n = 1 artifacts per period), and an organization O.

**Offers.** Each vendor simultaneously offers a contract (f_j, p_j) ∈ [0, 1] × ℝ₊, where f_j is the interface *friction* (the effort needed to accept a suggestion without deliberation) and p_j is a per-period license price. The marginal cost of supplying a tool is m ≥ 0, and friction is free to supply. Friction lowers the default share to

α(f) = α₀(1 − f)

and costs the developer v·c·f²/2 of time per artifact, incurred now.

**Governance g ∈ {D, O}** (a parameter of the game, known to all). Governance determines *whose payoff selects the tool*:
- g = D: developer-led adoption. The developer chooses the offer that maximizes her perceived payoff.
- g = O: organization-led adoption. The organization chooses the offer that maximizes its long-run payoff.

**Bypass (g = O only).** After the organization has selected a tool, the developer may bypass it and use an unsanctioned tool. A fringe supplier offers the developer's most-preferred friction f_D at price m. Bypass costs her ε ≥ 0 per period (shadow IT, including the unsanctioned license).

**Task level.** Given the tool, the developer solves the decision problem of 4.3. Rework costs are constant at R̄ and inspection time is uniform on [0, K], so that

- Δ_p ≡ φq(1 − ηφ)(βδR̄ − λvr) is the *perceived* value of inspecting an artifact, with B = βδR̄ − λvr > 0.
- Δ ≡ q(1 − ηφ)(δR̄ − vr) is its *long-run* value (β = φ = λ = 1 in the evaluator's own valuation, but with the true noticing probability).

**Assumption A.** 0 < Δ_p ≤ vK (so that inspection is interior) and the interior friction values below are at most 1. *Lemma 0:* Δ_p ≤ Δ, with equality if and only if β = φ = λ = 1. This holds because B ≤ δR̄ − vr and φ ≤ 1.

**Developer payoff.** Let s_p = Δ_p/(vK) be her inspection probability. Her perceived cost of the interface, per artifact, is

J(f) = v·c·f²/2 − α₀·f·W_p,  where W_p = Δ_p²/(2vK).

Here W_p is the perceived value of the option to deliberate. It equals the perceived gain Δ_p·s_p minus the expected inspection time cost Δ_p²/(2vK), which gives Δ_p²/(vK) − Δ_p²/(2vK). Each unit of friction moves an α₀ share of artifacts from default acceptance into deliberation. Her payoff from tool j is S₀ − p_j − J(f_j), where S₀ is the gross perceived benefit of the tool (including speed gains), assumed large enough that adoption is viable.

**Organization payoff.** Given the developer's inspection behavior (s_p), the organization's long-run valuation of deliberating is

W_O = Δ·s_p − Δ_p²/(2vK) = Δ_p(2Δ − Δ_p)/(2vK),

and its cost of an interface is C_O(f) = v·c·f²/2 − α₀·f·W_O. Its payoff from tool j is S₀^O − p_j − C_O(f_j), where S₀^O is its gross benefit.

**Timing.** (1) Vendors offer (f_j, p_j). (2) The adopter, D or O depending on g, selects a vendor. (3) If g = O, the developer decides whether to bypass. (4) Task-level decisions follow 4.3.

**Information and tie-breaking.** All parameters are common knowledge. Ties are broken in favor of the sanctioned tool (the developer complies when indifferent) and, among vendors, by equal splitting.

**Solution concept.** Subgame-perfect Nash equilibrium (SPNE), in pure strategies: task-level decisions are solved first, then bypass, then adoption, then vendors' simultaneous offers.

### 4.7.2 Results

**Result 5 (friction wedge).** Define

f_D = α₀Δ_p²/(2v²cK) and f_O = α₀Δ_p(2Δ − Δ_p)/(2v²cK), each capped at 1.

f_D minimizes the developer's perceived cost J, and f_O minimizes the organization's cost C_O. At interior values f_O − f_D = α₀Δ_p(Δ − Δ_p)/(v²cK) ≥ 0, with equality if and only if Δ_p = Δ, which holds in the rational benchmark for every v.

*Proof.* J and C_O are strictly convex in f, with first-order conditions v·c·f = α₀W_p and v·c·f = α₀W_O. Substituting W_p and W_O gives the formulas. Lemma 0 gives the sign. ∎

**Result 6 (governance, not competition).**
(a) *g = D.* In every SPNE with J ≥ 1, the adopted tool has friction f_D. With J = 1 the price is p = S₀ − J(f_D). With J ≥ 2 the price is p = m.
(b) *g = O, ε = ∞ (no bypass).* In every SPNE, the adopted tool has friction f_O.
(c) Debt under g = O is lower than under g = D if and only if some wedge binds.

*Proof.*
*(a), J = 1.* The monopolist maximizes p − m subject to the developer's participation constraint S₀ − p − J(f) ≥ 0, so p = S₀ − J(f) and profit is S₀ − J(f) − m. J is strictly convex, so the unique profit maximizer is f_D.
*(a), J ≥ 2.*
- *Zero profit.* Suppose a selected vendor j earns p_j > m. Any rival can offer (f_D, p′) with p′ just below p_j + J(f_j) − J(f_D) ≥ p_j, win all the demand, and earn p′ − m > 0. Because a deviation is profitable, p_j = m in equilibrium.
- *Friction.* Suppose a selected vendor has f_j ≠ f_D at p_j = m. It can deviate to (f_D, m + η′) for small η′ > 0, which still gives the developer strictly more surplus, and so earn η′ > 0. So f_j = f_D.
- *Existence.* The profile in which every vendor offers (f_D, m) is an SPNE, since any offer with p ≥ m gives the developer less surplus than (f_D, m).
*(b)* The same arguments apply with the organization's payoff S₀^O − p − C_O(f) in place of the developer's, so f_O replaces f_D. With J = 1 the monopolist extracts the organization's surplus and with J ≥ 2 competition drives the price to m.
*(c)* Debt is decreasing in f, since friction moves artifacts from default acceptance into deliberation, and f_O > f_D if and only if Δ_p < Δ (Result 5). ∎

*Remark.* The offer game is simultaneous in (f, p). If vendors chose friction first and prices second (a quality-then-price game), vertical differentiation would let a vendor soften price competition by offering lower perceived surplus (Shaked and Sutton 1982). Result 6(a) for J ≥ 2 therefore relies on simultaneous offers or on contestable entry. This is the maintained assumption.

**Result 7 (shadow AI constraint).** With g = O and bypass cost ε, the equilibrium friction is f = f_D + min{f_O − f_D, √(2ε/(vc))}. The constraint binds, and the organization closes only part of the gap, if and only if f_O − f_D > √(2ε/(vc)).

*Proof.* The developer bypasses if and only if J(f) − J(f_D) > ε. J is quadratic with minimum f_D, so J(f) − J(f_D) = (v·c/2)(f − f_D)², and she complies if and only if |f − f_D| ≤ √(2ε/(vc)). The organization's payoff is strictly concave in f with maximum at f_O ≥ f_D. If it chooses a bypassed tool, its payoff is that at f_D, which is strictly lower than at the nearest compliant friction. Its best compliant choice is therefore min{f_O, f_D + √(2ε/(vc))}. ∎

**Illustration.** With the parameters of Figure 3 (q = 0.5, R̄ = 2, r = 0.4, K = 0.6, α₀ = 0.8, c = 0.15, η = 0.5, v = δ = 1) and β = 0.5, φ = 0.6, λ = 1.2: Δ_p = 0.109 and Δ = 0.56, so f_D = 0.053, f_O = 0.491, and the bypass margin is √(2·0.005/0.15) = 0.258. The implementable friction is therefore 0.311.

**Note on the Section 4.2–4.3 illustrations.** These use a lognormal rework cost with median va and log-dispersion s = 0.79, η = 0.5, and λ = 1 in the behavioral configuration. With these values the price effect is −0.24, the wedge is +0.32, debt rises from 0.50 to 0.58, rational acceleration matches the behavioral level at v₁ = 2.9v₀, the self-admitted share is 0.33, the possession effect is 0.31 (and 0.27 with λ = 1.8 alone), and the lapse rate, as the joint probability, is 0.21.

## 4.8 From the model to the propositions

*(unchanged from the current Section 4.8, with the following correction to Result 3's description: "more reliable models can increase debt" holds on (q*, q̂) only, and debt is non-monotone in reliability when α < ½.)*
