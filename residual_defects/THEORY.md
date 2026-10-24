# Theory: verification effort, tool quality and liability (working draft)

Status: propositions P1-P6 are proved below (by hand) and checked numerically in `elasticity_check.py` and
`theory_check.py`. Items marked **Conjecture** are not proved. Novelty versus the literature is NOT established
(see `MODEL_NOTE.md`, literature section).

## 0. Setup
A developer writes code of size `s` with a tool of defect intensity `lam > 0` (lower is better). Introduced defects are
`Poisson(lam s)`. Verification effort `e >= 0` costs `C(e)` (increasing) and finds each defect independently with probability
`1 - S(e)`; `S(0)=1`, `S' < 0`, hazard `h = -S'/S`. By Poisson thinning the residual count is `R ~ Poisson(lam s S(e))`.
Each residual defect costs `ell`. The developer bears the share `delta = 1 - phi - phi_v` (users bear `phi`, the vendor
`phi_v`), so the developer minimises

    D(e; lam) = C(e) + A lam s S(e),     A = delta * ell.

Write `a := C''/C' - h'/h`. **Standing assumption (interior, regular):** a unique `e* > 0` solves the first-order
condition (FOC) `C'(e) = A lam s S(e) h(e)` and the second-order condition (SOC) `a + h > 0` holds at `e*`.
**Baseline B:** `S(e) = exp(-theta e)`, `C(e) = c e`; interior iff `A lam s theta > c`.

Under B: `S(e*) = c / (A lam s theta)`, `e* = (1/theta) ln(A lam s theta / c)`, `E[R] = lam s S(e*) = c / (delta ell theta)`.

## P1. Offsetting elasticity (general)
Let `R* = lam s S(e*(lam))`. Then

    eps := d ln R* / d ln lam = a / (a + h)        (evaluated at e*).

*Proof.* Let `F(e, lam) = C'(e) - A lam s S(e) h(e)`. Since `d/de[S h] = S(h' - h^2)`, using the FOC
`A lam s S = C'/h`:  `F_e = C'' - (C'/h)(h' - h^2) = C'(a + h) > 0` by the SOC. Also `F_lam = -A s S h = -C'/lam`.
The implicit function theorem gives `de*/dlam = 1 / (lam (a + h))`. Then
`d ln R*/d ln lam = 1 + lam (S'/S) de*/dlam = 1 - h/(a + h) = a/(a + h)`. QED

Corollaries. (a) B: `a = 0`, `eps = 0` (full offsetting). (b) `C = c e^g`, exponential `S`: `eps = (g-1)/((g-1) + theta e*)`.
(c) Linear cost, `S = (1 + theta e/k)^-k`: `h = theta/(1 + theta e/k)`, `h'/h = -(theta/k)/(1 + theta e/k)`, so `a = h/k` and
**`eps = 1/(1+k)`**, independent of `e*` and `lam`. (d) Rising hazard (`h' > 0`, e.g. Weibull `beta > 1`) gives `a < 0`: `eps < 0`,
over-offsetting. Numerics: `elasticity_check.py` (18 specifications, formula = finite difference to 3-4 digits).

## P2. The value of quality is independent of liability (baseline)
Let `V(lam) = min_e D` (developer's cost) and `W(lam) = C(e*) + ell lam s S(e*)` (social cost at the developer's choice).
Under B, for every `delta in (0, 1]`:

    V'(lam) = W'(lam) = W_fb'(lam) = c / (theta lam),

where `W_fb` is the first-best social cost (`delta = 1`, effort chosen by the planner).

*Proof.* Envelope theorem: `V' = A s S(e*)`. By the FOC, `A s S(e*) = C'(e*)/(lam h(e*))`, which is `c/(theta lam)` under B.
For `W`: `W' = ell s S* + [C' - ell lam s S* h] e*'`. Under B, `S* = c/(A lam s theta)` so `ell s S* = c/(delta lam theta)`;
`C' - ell lam s S* h = c - c/delta`; `e*' = 1/(theta lam)` (P1). Hence `W' = (c/(theta lam))[1/delta + 1 - 1/delta] = c/(theta lam)`.
First best is the case `delta = 1`. QED

General form (any `C`, `S`): `V'(lam) = C'(e*)/(lam h(e*))`. For linear cost and the heavy tail of P1(c) this is
`c (1 + theta e*/k) / (theta lam)`, which depends on `delta` through `e*`: outside B, liability does affect the value of quality.

Interpretation: tool quality only saves verification cost (residual density is constant), so externalities do not distort the
vendor's incentive to improve quality at the margin; they distort the *level of verification*.

## P2b. Deadweight loss of the externality does not depend on tool quality (baseline)
Under B: `W(lam; delta) = (c/theta) [ln(delta ell lam s theta / c) + 1/delta]`, hence

    L(delta) := W(lam; delta) - W(lam; 1) = (c/theta) (1/delta - 1 + ln delta)  >= 0,

zero iff `delta = 1`, strictly decreasing in `delta` on `(0, 1]`, and independent of `lam` and `s`.
*Proof.* `c e* = (c/theta) ln(A lam s theta/c)` and `ell lam s S* = c/(delta theta)`; subtract the `delta = 1` case;
`x - 1 - ln x >= 0` with `x = 1/delta`; `dL/d delta = (c/theta)(delta - 1)/delta^2 < 0`. QED
Consequence: better tools do not reduce the loss from under-verification caused by weak liability.

## P3. Warranties cannot signal quality when the developer knows lam (baseline)
If the vendor bears the share `phi_v`, the vendor's expected payout is `phi_v ell E[R] = phi_v c / (delta theta)`, with
`delta = 1 - phi - phi_v`; it does not depend on `lam`. So the single-crossing condition fails: all vendor types face the same
expected warranty cost and no separating equilibrium in warranties exists. Moreover, `L(delta)` is decreasing in `delta`, so
raising `phi_v` (lowering `delta`) raises the deadweight loss: a warranty is a moral-hazard device against the developer.
*Proof.* `E[R] = c/(delta ell theta)` from the FOC (`lam`, `s` cancel). QED (checked in `theory_check.py`, P3.)

## P4. With beliefs, warranty separation is governed by belief responsiveness
Suppose the developer chooses `e` using a belief `lam_hat` (possibly a function of the true `lam`), under B. Then
`E[R | lam] = lam c / (A lam_hat theta)`, so

    d ln E[R | lam] / d ln lam = 1 - rho,    rho := d ln lam_hat / d ln lam.

No learning (`rho = 0`): payout `proportional to lam` (single crossing, maximal separation). Full learning (`rho = 1`): payout flat (P3).
*Proof.* FOC with `lam_hat` gives `S(e) = c/(A lam_hat s theta)`; multiply by `lam s`. QED

**Conjecture C1 (learning).** Under Gamma-Poisson learning with the posterior-mean stopping rule,
`E[R_tau | lam]` is increasing in `lam` with elasticity in `(0,1)`. Simulation (`theory_check.py`, 30,000 projects, prior
`Gamma(2,1)`): decile slope of `ln E[R_tau|lam]` on `ln lam` is 0.67, i.e. `rho_hat ~ 0.33`; unconditional `E[R_tau] = 0.0362`
vs `r* = c/(A theta) = 0.0357` (earlier 2-SE gap was sampling noise). Not proved; optimality of the stopping rule is also open.

## P5. Adverse selection with an unobserved quality (baseline; static effort)
Let the developer choose `e` from a belief equal to the pool mean `lam_bar` and `lam` vary in the pool. Then the expected cost is
`(c/theta) [ln(A lam_bar s theta / c) + 1]`, so heterogeneity within the pool does not matter, only its mean.
*Proof.* `E[c e + A lam s S(e)] = c e + A lam_bar s S(e)` is linear in `lam` and is minimised at the stated `e`. QED
Willingness to pay for the pool versus an outside option `lam0`: **`WTP = (c/theta) ln(lam0 / lam_bar)`**.

Vendors have type `lam` and a cost `k(lam)` of supplying it, with `k` decreasing in `lam` (quality is costly). A type participates
iff `k(lam) <= p`. Let `m(x) = E[lam | lam >= x]` (increasing in `x`). In a competitive pool with threshold `x` (types `lam < x` exit)
and price `p = k(x)`, the equilibrium condition is `G(x) := (c/theta) ln(lam0/m(x)) - k(x) = 0`.
(i) Full participation is an equilibrium iff `G(lam_lo) >= 0`, i.e. `k(lam_lo) <= (c/theta) ln(lam0/lam_bar_all)`.
(ii) If `G(lam_lo) < 0` the best types cannot be sustained at the full-pool price; an equilibrium, if any, has a threshold `x > lam_lo`
with `G(x) = 0` and a worse pool (`m` rises). (iii) Multiple equilibria are possible. (iv) No trade if `G < 0` everywhere.
Numerics (`theory_check.py`, P5; types `Gamma(2, 2)`, `lam0 = 3`, `k = kappa max(0, 1 - lam/4)`): `kappa = 0.8, 1.2`: full
participation and a second, worse equilibrium (threshold 1.31 / 0.60, participating share 0.26 / 0.66); `kappa >= 1.6`: no trade.
The proofs of (i)-(iv) are direct from the definitions; the equilibrium concept (competitive vendors, developers who price the pool
mean) is an assumption, and welfare ranking of the equilibria is not done.

## P6. A verification standard removes offsetting
If a binding minimum `e >= e_bar` applies, residual density is `lam s S(e_bar)`, so `d ln R / d ln lam = 1`: quality improvements pass
through one for one. Under B the private choice is below first best by `e_fb - e* = (1/theta) ln(1/delta)`, independent of `lam`; the
social cost `c e + ell lam s S(e)` is convex in `e`, so a standard `e_bar` improves welfare for type `lam` iff `W(e_bar) < W(e*)`.
Because the first-best level depends on `lam` and a uniform `e_bar` does not, a single standard over-verifies better tools: a
quantitative trade-off is left open. (Elementary; no separate numerical check.)

## 7. Vendor stage
Setting: a continuum of developers (mass `N`) with types `kappa = c/theta` (verification cost per unit of detection speed) and
common stakes; a vendor chooses quality `lam < lam0` (outside option `lam0`, e.g. coding without the tool) and a price.
All results below are under baseline B unless stated. Check: `vendor_check.py`.

### P7. Separation of the tool market from the liability regime (baseline)
(a) Willingness to pay of type `kappa` is `WTP = V(lam0) - V(lam) = kappa ln(lam0/lam)` for every `delta`, `ell`, `s`.
(b) The social benefit of adoption `W(lam0) - W(lam)` is the same `kappa ln(lam0/lam)`.
(c) Hence total welfare is additive: *tool-market surplus* (independent of the liability regime) minus `N L(delta)`
(the P2b loss). A vendor that extracts type-by-type surplus chooses its quality margin independently of the liability regime, and
the quality FOC is `kappa/lam = -K'(lam)`-type, i.e. the same as the planner's (P2).
(d) Shifting liability between the vendor and users, holding the developer's share `delta` fixed, changes no behaviour:
it is a transfer. Only the developer's share matters for welfare (a least-cost-avoider result: the party who controls
verification should bear the loss).
*Proof.* From `V(lam) = (c/theta)[ln(A lam s theta/c) + 1]` and `W(lam) = (c/theta)[ln(delta ell lam s theta/c) + 1/delta]` the
`lam`-differences are `kappa ln(lam0/lam)` and do not contain `A`, `s`, `delta`. QED

**Failure outside the baseline (data-calibrated heavy tail).** With `S(u) = (1 + theta u/k)^-k`, `theta = 206`, `k = 0.63` (the
all-sample fit, `u` = fraction of the test suite), linear cost, and an illustrative stake `ell s = 20`, the willingness to pay
for improving `lam` from 1.0 to 0.5 falls with the developer's share:

| delta | 1.0 | 0.7 | 0.4 | 0.2 |
|---|---|---|---|---|
| WTP relative to delta = 1 | 1.00 | 0.80 | 0.57 | 0.37 |

So with the estimated tail, weakening the developer's liability lowers the value of tool quality and hence the vendor's
quality incentive (exactly `delta^eps`, see P10). P7 is a baseline benchmark, not a robust empirical claim. The stake `ell s = 20` is illustrative, not calibrated.

### P8. Monopoly under-provides quality by a factor of two (closed form)
Take `kappa ~ U[0, kbar]`, a fixed quality cost `K(lam) = K0/lam`, zero marginal cost, one product `(lam, p)`. The monopolist sells to
`kappa >= p/g`, `g = ln(lam0/lam)`, so `p* = kbar g/2`, profit `N kbar g/4 - K0/lam`, and
`lam_M = 4 K0/(N kbar)`. The planner (everyone served) maximises `N kbar g/2 - K0/lam`: `lam_S = 2 K0/(N kbar)`.
**`lam_M = 2 lam_S`.** Welfare loss = quality distortion + exclusion of types `kappa < kbar/2`, the latter `N kbar g(lam_M)/8`.
Example (`N=1, kbar=1, K0=0.3, lam0=3`): surplus 0.305 at `lam_S`, 0.094 under monopoly (0.208 before the exclusion loss 0.115).
Under B none of this depends on the liability regime. *Proof.* FOCs as stated. QED (checked numerically.)

### P9. Warranty signalling with two types (baseline; learning enters through rho)
Types `lam_H < lam_L`, `r = lam_L/lam_H`. A vendor offers a warranty with ratio `w = phi_v/delta'`, where `delta'` is the developer's
share after the warranty (`delta' = delta0/(1+w)`). Developers pay `kappa ln(lam0/lam_hat)` for the believed type. A developer who
meets a mimicking L-type with belief H partly learns the truth: effort is set for `lam_hat = lam_H^(1-rho) lam_L^rho`
(**assumption**: log-linear learning). Then:
- mimic payout `= kappa w r^(1-rho)`; honest H payout `= kappa w`;
- L does not mimic iff `w >= ln r / r^(1-rho)`; H prefers separating to being taken for L iff `w <= ln r`.
- **Cheapest separating warranty `w* = ln r / r^(1-rho)`** (least-cost separating equilibrium, selected by the intuitive
  criterion - assumption). H's net gain from separating is `kappa ln r (1 - r^-(1-rho))`.
- `rho = 0`: `w* = ln r / r <= 1/e`; `rho -> 1`: `w* -> ln r` and H's gain `-> 0` (warranties cannot signal; consistent with P3).
- Cost of separating: the developer's share falls to `delta0/(1+w*)`, so welfare falls by `N_H [L(delta0/(1+w*)) - L(delta0)]`:
  signalling quality through a warranty destroys verification (a moral-hazard cost).
*Proof.* Substitute `R = c lam_L/(A' theta lam_hat) = (c/(A' theta)) r^(1-rho)` into the payout `phi_v ell R` and compare with
`kappa(ln r - ...)`. QED (checked numerically for `rho in {0, .5, .8}`, `r in {1.5, e, 5, 10}`.)

### Not done in the vendor stage
Price competition and vertical differentiation (several vendors); the continuum-of-types signalling equation; dynamic learning by
vendors; welfare comparison "warranty signalling vs unravelling" (P5 vs P9); the general-tail extension of P8 (P7's failure means
the factor of two is baseline-specific).

## 8. Heavy-tail generalisation (linear cost, `S(e) = (1 + theta e/k)^-k`, `eps = 1/(k+1)`)
Check: `heavy_check.py` (all formulas below equal the numerical optimum to 5-6 digits). Interior iff `Z := A lam s theta / c > 1`.

### P10. Closed forms
The FOC gives `(1 + theta e*/k)^(k+1) = Z`, so `1 + theta e*/k = Z^eps` and `R* = lam s Z^(-k eps)` (elasticity `eps`, as in P1(c)). Then
- developer cost `V(lam) = (c/theta) [ (k+1) Z^eps - k ]`;
- social cost at the privately chosen effort `W(lam) = (c/theta) [ (k + 1/delta) Z^eps - k ]`;
- willingness to pay `WTP = V(lam0) - V(lam) = (c/theta)(1/eps)(A theta s/c)^eps [lam0^eps - lam^eps]`, which is **proportional to `delta^eps`**.
*Proof.* `A lam s = c Z/theta`, so `A lam s S(e*) = (c/theta) Z^eps` and `c e* = (ck/theta)(Z^eps - 1)`; add. For `W`, `ell lam s = (c/(delta theta)) Z`.
Limit `k -> infinity` (`eps -> 0`): `V -> (c/theta)(1 + ln Z)`, the baseline. QED
This explains the table in P7 exactly: `0.7^eps = 0.8035`, `0.4^eps = 0.5700`, `0.2^eps = 0.3725` for `k = 0.63`.

### P11. Private value of quality understates its social value; the externality loss shrinks with quality
(a) Social benefit of adopting quality `lam` over `lam0` (at the privately chosen effort) divided by private WTP is
**`psi = (k + 1/delta)/(k + 1) >= 1`**, equal to 1 iff `delta = 1` (or `k -> infinity`, the baseline of P2).
For `k = 0.63`: `psi = 1.26, 1.92, 3.45` at `delta = 0.7, 0.4, 0.2` (matches the numerics).
(b) The externality loss `L_k(lam, delta) = W(lam; delta) - W(lam; 1) = (c/theta)(ell lam s theta/c)^eps [ (k + 1/delta) delta^eps - (k+1) ]`
is non-negative and **increases in `lam` with elasticity `eps`**: unlike P2b (where `L` was independent of quality), better tools
shrink the loss caused by weak developer liability, but only by the factor `lam^eps`.
*Proof.* Subtract the `delta = 1` case in P10; non-negativity because first best minimises the social cost; the `lam` factor is `Z^eps`. QED

### P12. Monopoly quality distortion with a heavy tail
Let types differ in a scalar multiplier `nu ~ U[0, nubar]` (assumption; e.g. verification cost `c` at fixed `theta`, `nu ~ c^(1-eps)`),
`WTP_nu = nu G(lam)`, `G = (lam0^eps - lam^eps)/eps`, social benefit `psi * WTP`, fixed cost `K0/lam`, zero marginal cost. Then
`lam_M^(1+eps) = 4 K0/(N nubar)`, `lam_S^(1+eps) = 2 K0/(N nubar psi)` and

    lam_M / lam_S = (2 psi)^(1/(1+eps)).

For `k -> infinity`, `delta = 1`: ratio 2 (P8). For the estimated `k = 0.63`: **1.54 at `delta = 1`, 2.07 at `delta = 0.5`, 3.31 at `delta = 0.2`**
(`k` in 0.51-0.78 changes these only in the third digit). So the heavy tail makes the monopoly distortion milder when developers bear
all losses, but weak developer liability enlarges it through two channels: lower `WTP` (`delta^eps`) and higher social value (`psi`).
*Proof.* FOCs: `-N nubar G'(lam)/4 = K'` with `G' = -lam^(eps-1)`; same for the planner with `psi/2`. QED

### What this changes
- P7 (separation of tool market and liability regime) is exact only in the baseline. With the estimated tail, **developer liability is a
  complement of tool quality**: it raises the value of better tools (`delta^eps`), and weak liability lowers both quality and verification.
- The policy claim "put the loss on the developer" is strengthened, not weakened: the baseline saw only the verification channel, the
  heavy tail adds a quality channel.
- Illustration numbers use `ell s = 20`, not calibrated; only the interior condition `Z > 1` depends on it. The `k` used is the
  estimate from the HumanEval+ pilot under random test order, not an estimate of developers' real verification technology.

## What is proved, checked, conjectured
| Item | Status |
|---|---|
| P1 elasticity `a/(a+h)`, `1/(1+k)`, over-offsetting | Proved; numerically checked |
| P2, P2b value of quality / loss independent of `lam` | Proved (B); numerically checked |
| P3 warranty cannot signal with known `lam` | Proved (B); numerically checked |
| P4 payout elasticity `1 - rho` | Proved (B); numerically checked |
| C1 learning gives `rho_hat ~ 0.33` | Simulation only; **Conjecture** |
| P5 lemons characterisation | Definitions and linearity proved; equilibria numerical; welfare ranking open |
| P6 verification standard | Elementary; trade-off open |
| P7 separation of tool market and liability | Proved (B); fails with the estimated heavy tail (numerical, illustrative stakes) |
| P8 monopoly quality factor 2 | Proved (uniform types, `K0/lam`); numerically checked |
| P9 cheapest separating warranty `ln r / r^(1-rho)` | Proved under stated assumptions (two types, log-linear learning); numerically checked |
| P10 heavy-tail closed forms, `WTP ~ delta^eps` | Proved; numerically checked |
| P11 `psi = (k+1/delta)/(k+1)`, `L_k ~ lam^eps` | Proved; numerically checked |
| P12 monopoly ratio `(2 psi)^(1/(1+eps))` | Proved (uniform multiplier, `K0/lam`); numerically checked |

## Link to the data
`bootstrap_k.py` estimates `k = 0.63` (95% CI 0.51-0.78; 0.72 without timeouts) from 25,120 LLM samples, i.e. `eps ~ 0.58-0.62`
under linear cost and random test order. `sensitivity_k.py`: across defect definitions and test orders `eps` lies in 0.52-0.66
(0.82 only for an adversarial long-inputs-first order), see `MODEL_NOTE.md`. P2's general form shows that with such a tail the value of quality depends on `delta`.
