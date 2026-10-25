
# Who Pays for the Next Attempt? Contract Design and Escalation Rules for AI-Assisted Software Maintenance

**Keywords:** AI–human task allocation; escalation; outcome-based pricing; IT service contracts; software maintenance; large language models; double marginalization; optimal stopping

---

## Abstract

Firms increasingly buy AI-based defect repair as a pay-per-use service: a large language model proposes patches, the firm verifies them, and unresolved defects are escalated to human engineers. We study how the vendor's pricing (per attempt or per verified fix) and the firm's escalation rule interact when defects differ in how easily they are repaired, so that every failed attempt is informative about the next. The firm's optimal rule is a reservation threshold, N\* = ⌈aH/c − a − b⌉ under Beta-distributed difficulty, and the threshold structure holds for any heterogeneity distribution. Per-attempt prices above cost make the firm stop too early (double marginalization). A success fee of Hk/(k+v) restores the efficient depth, but a monopolist sets a higher fee. Deeper sampling requires leaving the firm an *incentive rent of sequential search*, 78–82% of surplus in our calibrations, so the vendor samples too little. Among linear pay-per-use contracts the pure success fee is optimal for the vendor, and a lump-sum fee would remove every distortion. When vendors privately know their quality, only success fees can signal it, and a high-quality vendor separates by lowering its fee, which raises welfare. In a differentiated-Bertrand game, competition removes the distortion only when vendors are close substitutes. On open repair data (RepairBench: 574 bugs, 45 models; a new 40-sample HumanEvalFix experiment) difficulty is heterogeneous in all 84 model–dataset combinations, and a threshold fitted on half the bugs performs within 0.4–1.7% of the best cap in hindsight. Calibrating costs to public wage statistics, task-time annotations, and API price lists shows that the conclusions are strongest when verification is cheap relative to human repair; a field-validation design is provided.

---

## 1. Introduction

Software maintenance absorbs most of the lifetime cost of information systems (Lientz and Swanson 1980), and LLM-based repair agents change how that work is organized. A firm can route a defect first to an AI service, accept a patch that passes its tests, and escalate to a person only if the AI fails. Research on AI augmentation stresses that such arrangements succeed or fail on the allocation of tasks and the design of delegation (Raisch and Krakowski 2021; Fügener et al. 2022), but two questions that arise concretely have been left open: how many failed attempts should a firm tolerate before escalating, and how does the vendor's price structure shape that choice?

Both questions turn on a regularity that is easy to overlook. Repair is stochastic, so a defect can be attempted repeatedly, but defects differ enormously in how likely an attempt is to succeed: some are fixed almost every time, others almost never. A run of failures is therefore *bad news about the defect itself*, and the marginal value of another attempt falls as failures accumulate. A firm that plans with an average success rate would never stop; a firm that fixes the number of attempts by convention ignores both its own cost of human repair and the vendor's price.

Pricing matters because it sets the cost of an additional attempt as the firm sees it. Under *per-attempt* pricing (per call or per token), the firm bears the price of every attempt, including the many that fail on hard defects. Under *outcome-based* pricing, it pays only for a verified fix and the vendor bears the compute cost of failures.

**Contributions.** (1) We model AI–human escalation as a sequential search problem with an outside option inside a vendor–buyer game, linking the AI-delegation and IT-contracting literatures. (2) We show that per-attempt pricing above cost causes double marginalization, that a success fee of Hk/(k+v) restores efficiency, and that a monopolist nevertheless sets a higher fee and samples too little (Propositions 2–4). (3) We identify the underlying force, an *incentive rent of sequential search*, and prove, for any heterogeneity distribution, that the vendor's optimal pay-per-use contract is a pure success fee and that a lump-sum fee removes all distortions (Propositions 5–6). (4) We show that private vendor quality reverses profit order across contract forms so that only success fees can signal quality (Proposition 7), and that competition removes the distortion only among close substitutes (Proposition 8). (5) We test the model's premises on open repair data and report numerical equilibria calibrated to them.

**Article type and audience.** This is a theory article in the ISR sense: it applies and extends search theory and vertical-contracting theory to a new IS phenomenon (pay-per-use AI services), derives propositions, and illustrates the model with open repair data. The intended audience is academics working on the economics of information systems, IT sourcing and governance, and human–AI work design, and practitioners who procure or price AI-assisted software services (chief information officers, engineering and procurement managers, and AI vendors).

---

## 2. Related Literature

**AI–human collaboration and delegation.** Productivity gains from AI depend on how work is divided and on how well people know when to delegate (Raisch and Krakowski 2021; Fügener et al. 2022; Brynjolfsson et al. 2023); the economics of prediction treats AI as lowering the cost of prediction while leaving verification and judgement with humans (Agrawal et al. 2018). We model the *escalation boundary* in a setting where the AI's output is checkable and each failure is informative.

**IT service contracting and maintenance.** Work on software and IT services contracts studies the allocation of risk and incentives between client and vendor (Whang 1992; Bajari and Tadelis 2001; Gopal et al. 2003); work on maintenance documents workload volatility and its dependence on system structure (Kemerer and Slaughter 1999; Banker and Slaughter 2000). We add a contract dimension specific to generative AI services: the unit of payment can be an attempt or a result.

**Vertical contracting and search.** A seller's markup over marginal cost makes a buyer under-purchase relative to the joint optimum (Spengler 1950; Tirole 1988); we apply this logic to the number of attempts. The sequential structure follows search theory (Stigler 1961; McCall 1970; Weitzman 1979), with the twist that the success probability is learned from failures through heterogeneity across defects. The rent we identify is the infra-marginal gain of sequential search familiar from Pandora-box problems and from virtual surplus in optimal mechanisms.

**Automated program repair.** LLM-based repair is evaluated by tests and reported as pass@k (Chen et al. 2021; Le Goues et al. 2012; Xia and Zhang 2023; Jimenez et al. 2024; Silva and Monperrus 2025), and repeated sampling raises coverage with diminishing returns (Brown et al. 2024). These papers measure capability, not the economic choice of how many attempts to buy.

---

## 3. Model

**Players and timing.** A firm faces a stream of defects; a monopolist vendor offers an AI repair service. (1) The vendor announces a contract. (2) The firm accepts, or rejects and has every defect repaired by a human at cost *H*. (3) For each defect the firm requests attempts sequentially, verifies each patch at its own cost, and stops on an accepted patch or escalates to a human.

**Defects.** Each defect has a latent per-attempt success probability *p* ~ F, unobserved by both parties; given *p*, attempts are independent and their outcomes (pass or fail the firm's tests) are observed by both. Let T be the index of the first success, S(j) = P(T > j) = E[(1−p)^j], and q_n = P(attempt n+1 succeeds | n failures) = E[p(1−p)^n]/E[(1−p)^n]. For F = Beta(*a*, *b*), S(j) = B(a, b+j)/B(a, b) and q_n = a/(a+b+n). Let E(N) = Σ_{j<N} S(j) be the expected number of attempts under a cap N and P(N) = 1 − S(N) the probability of repair within N attempts.

**Costs.** An attempt costs the vendor *k* and the firm *v* (tests, triage, review); verification is accurate.

**Contracts.** (A) *Per-attempt:* the firm pays *w* ≥ *k* per attempt. (B) *Success fee:* the firm pays *f* ≤ *H* per verified fix and nothing for failures. The joint benchmark treats the cost per attempt as *k* + *v*. Total surplus relative to human-only repair for a cap N is

W(N) = H·P(N) − (k + v)·E(N),

independent of the transfer. N^FB maximizes W. We call (A) and (B) *pay-per-use* contracts, since payments depend only on realized attempts and outcomes.

---

## 4. Results

### 4.1 The firm's escalation rule

**Proposition 1 (Reservation rule).** For every non-degenerate F, q_n is strictly decreasing in n. Under contract A the firm makes attempt n+1 iff q_n·H > w + v; under B iff q_n·(H − f) > v. For F = Beta(a, b) the budgets are
N_A(w) = max{0, ⌈aH/(w+v) − a − b⌉}, N_B(f) = max{0, ⌈a(H−f)/v − a − b⌉},
and N^FB = max{0, ⌈aH/(k+v) − a − b⌉}.

*Proof.* Let E_n be expectation under the tilted law ∝ (1−p)^n dF, so q_n = E_n[p] and q_{n+1} = (E_n p − E_n p²)/(1 − E_n p) ≤ E_n p = q_n by Jensen, strictly unless p is degenerate under that law. Since q_n is decreasing, once continuing stops being preferred it never is again, so the one-step look-ahead rule is optimal (Chow, Robbins, and Siegmund 1971). In state n the comparison is stopping (cost H) versus one more attempt and then stopping: (w+v) + (1−q_n)H under A, or v + q_n f + (1−q_n)H under B. ∎

The threshold rises with the cost of human repair, falls with the price of an attempt, and falls with difficulty (low *a*, high *b*). A homogeneous model (constant p) would prescribe never stopping or never starting; heterogeneity is what makes the rule interior.

### 4.2 Pay-per-use contracts under monopoly

**Proposition 2 (Double marginalization).** Under A with w > k, N_A(w) ≤ N^FB, and surplus is below its first-best level whenever w lowers the budget.

*Proof.* N_A decreases in w, so N_A(w) ≤ N_A(k) = N^FB. W(N+1) − W(N) = S(N)[q_N H − (k+v)] is positive iff N < N^FB, so W increases up to N^FB. ∎

**Proposition 3 (Efficient success fee).** Under B with f^e = Hk/(k+v), N_B(f^e) = N^FB; the vendor earns k/(k+v) of the first-best surplus.

*Proof.* (H − f^e)/v = H/(k+v), so the thresholds coincide. Vendor profit is f^e P − kE = (k/(k+v))[HP − (k+v)E]. ∎

**Proposition 4 (The monopoly fee exceeds the efficient fee).** Let N^FB ≥ 1 and Π(f) = f·P(N_B(f)) − k·E(N_B(f)). Because N_B is an integer step function of f: (a) Π is strictly increasing within each step, and for every f′ ≤ f^e there is f > f^e with Π(f) > Π(f′); (b) the budget at the vendor's optimum satisfies n̂ ≤ N^FB, strictly unless the best fee lies in the same step as f^e, in which case the vendor raises the fee without changing the firm's depth.

*Proof sketch (full proof in Appendix E).* The firm's budget is n exactly for f ∈ [φ_n, φ_{n−1}), φ_n = H − v/q_n. Let L(n) be the profit at the lower end and R(n) the supremum of profit within step n. Then R(n) − L(n−1) = S(n−1)[q_{n−1}H − (k+v)], which is negative iff attempt n is inefficient. For n > N^FB, R(n) ≤ L(n−1) < R(n−1), so R is strictly decreasing beyond N^FB. ∎

Numerically the vendor's best step is strictly below N^FB in 289 of 293 random draws; in the other four it raises the fee within the efficient step.

### 4.3 The incentive rent of sequential search

**Proposition 5 (Incentive rent and optimal linear contract).** For N ≥ 1 define the incentive rent
G_min(N) = v·[P(N)/q_{N−1} − E(N)] = v·Σ_{j<N} S(j)·(q_j/q_{N−1} − 1) ≥ 0.
(a) G_min(1) = 0, G_min is nondecreasing in N, and G_min ≡ 0 iff difficulty is homogeneous.
(b) For every contract with per-attempt fee w ≥ 0 and success fee f ≤ H under which the firm chooses depth N ≥ 1, the vendor's profit satisfies
Π(w, f) ≤ R(N) − (w/v)·G_min(N), where R(N) = W(N) − G_min(N) = Σ_{j<N} S(j)[q_j φ_{N−1} − k], φ_{N−1} = H − v/q_{N−1}.
(c) R(N) is approached only by the pure success fee (w = 0, f ↑ φ_{N−1}); a positive per-attempt component strictly lowers profit whenever N ≥ 2 and difficulty is heterogeneous.
(d) The vendor's optimal depth maximizes R(N), and R(N+1) − R(N) = S(N)[q_N H − (k+v)] − v·P(N)·(1/q_N − 1/q_{N−1}); hence n̂ ≤ N^FB. For the Beta family the last factor is 1/a.

*Proof sketch (full proof in Appendix E).* The firm chooses depth N only if q_{N−1}(H−f) > w + v, i.e. f < φ_{N−1} − w/q_{N−1}. Substituting into Π = (w−k)E + fP gives Π < R(N) − w[P/q_{N−1} − E]. Participation holds at the corner (0, φ_{N−1}) because P ≥ q_{N−1}E. ∎

*Interpretation.* To make the firm willing to try the N-th attempt, whose success probability is low, the vendor must price the marginal success at φ_{N−1} = H − v/q_{N−1}. Every earlier attempt succeeded more often than the marginal one, so the firm keeps an infra-marginal gain, G_min(N). It is zero when difficulty is homogeneous and grows with dispersion. The vendor's profit is surplus net of this rent, so it samples too little, and the pure success fee delivers any depth most cheaply because a per-attempt fee collects revenue from attempts where the firm's marginal gain is smallest.

**Proposition 6 (Lump-sum neutralization).** If the vendor may also charge a fee T₀ independent of attempts and outcomes, then (w, f, T₀) = (k, 0, W(N^FB)) implements N^FB and gives the vendor the entire surplus; for any (w, f), T₀ can recapture G_min without changing the firm's budget.

*Proof.* T₀ is a constant in the firm's cost and does not enter any one-step comparison of Proposition 1. ∎

The distortions in this paper therefore stem from pay-per-use pricing. A lump sum is unattractive when the firm cannot judge quality before using the service, when procurement is per defect, or when prepayment is costly.

**Table 1. The incentive rent (H = 100, v = 1, k = 0.2).**

| Heterogeneity (a, b) | N^FB | W(N^FB) | G_min(N^FB) | Vendor's maximum at N^FB, R(N^FB) | Rent / W(N^FB) | Vendor's optimal depth n̂, R(n̂) |
|---|---|---|---|---|---|---|
| RepairBench-like (0.12, 0.39) | 10 | 33.9 | 26.5 | 7.4 | 78% | 3, 25.6 |
| SWE-Verified-like (0.25, 0.34) | 21 | 63.5 | 52.2 | 11.3 | 82% | 4, 50.2 |
| Synthetic (0.40, 3.0) | 30 | 43.9 | 35.1 | 8.8 | 80% | 10, 30.4 |

A vendor that wanted the efficient depth would leave the firm about four-fifths of the surplus.

### 4.4 Market structure

**Private vendor quality.** Suppose the vendor knows its type θ ∈ {H, L} with success parameters a_H > a_L (common b, k) and the firm has prior μ on H.

**Proposition 7 (Profit-order reversal).** For any common depth N ≥ 1, (a) under A the low type earns weakly more: (w−k)E_L(N) ≥ (w−k)E_H(N); (b) under B the high type earns strictly more when f > 0: fP_H(N) − kE_H(N) > fP_L(N) − kE_L(N).

*Proof.* The Beta family is ordered by likelihood ratio in *a*, so S(j) = E[(1−p)^j] is decreasing in a: S_H ≤ S_L, hence E_H ≤ E_L and P_H ≥ P_L, strictly for N ≥ 1 in P. ∎

Per-attempt pricing pays for failures, so it rewards the worse vendor at any depth, and a per-attempt contract cannot credibly signal quality; a success fee can. Numerically (Section 5.2), a high-quality vendor usually separates by *lowering* its fee below the full-information monopoly fee, which makes the firm sample deeper and partly corrects the monopoly under-sampling.

**Competition among differentiated vendors.** A unit mass of firms chooses among *n* symmetric vendors (same *a*, *b*, *k*) and human-only repair; firm *i*'s value from vendor *j* is G_j + σε_ij with Gumbel ε, where G_j is its saving at its optimal budget under j's contract and σ measures differentiation. Shares are logit, and vendors choose the price of their contract form in a symmetric Bertrand–Nash equilibrium.

**Proposition 8 (Limits of competition).** (a) As σ → 0 (close substitutes), per-attempt pricing converges to w = k and the efficient depth N^FB; success fees converge to the zero-profit fee f_0 ≤ f^e, so the firm over-samples (N_B(f_0) ≥ N^FB) and surplus is weakly below first-best. (b) Let ρ = e^{S^FB/σ} − 1. For σ large, (n+1)s_j ∈ [1−ρ, 1+ρ] at every price with positive profit, so every best response earns at least [(1−ρ)/(1+ρ)] of the monopoly profit per served firm; if the monopoly step is unique with margin Δ, the equilibrium budget equals the monopoly budget once σ > S^FB / ln(1 + Δ/(2Π_m − Δ)). Coverage tends to n/(n+1).

*Proof.* (a) With w = k the firm's threshold is the efficient one. For B, zero profit f_0 P = kE and participation vE + f_0P ≤ HP give (k+v)E ≤ HP and hence f_0 = kE/P ≤ Hk/(k+v). (b) With G ∈ [0, S^FB] at best responses, the share is (1+δ_j)/(n+1+Σδ_k) with δ ∈ [0, ρ]; the bounds follow, and a price outside the monopoly step earns at most (1+ρ)(Π_m − Δ)/(n+1) < (1−ρ)Π_m/(n+1) when ρ < Δ/(2Π_m − Δ). ∎

Differentiation, more than the number of vendors, determines whether competition removes the distortion; intermediate cases are solved numerically in Section 5.3.

---

## 5. Numerical Equilibria

Code in the replication package (anonymized for review). The shape parameters (a, b) come from the empirical fits in Section 6. Tables 1–3 use H = 100, v = 1, k = 0.2 (dollars), which lie inside the ranges calibrated from public sources in Section 5.4 (H) or between its function-level and agentic ranges (k); Section 5.4 shows how the conclusions change across those ranges. Integer budgets rule out closed forms for the vendor's optimal price, so equilibria are computed on price grids or by exact enumeration of budget steps.

### 5.1 Monopoly: per-attempt versus success fee

**Table 2. Monopoly equilibria (H = 100, v = 1, k = 0.2).** Entries: optimal price, firm's budget N, vendor profit, firm's saving, and welfare as a share of first-best.

| Heterogeneity (a, b) | Per-attempt | Success fee |
|---|---|---|
| RepairBench-like (0.12, 0.39) | w\* = 22.5, N=1, 22.3, 0.01, 66% | f\* = 79.0, N=3, 25.6, 4.4, 89% |
| SWE-Verified-like (0.25, 0.34) | w\* = 41.3, N=1, 41.1, 0.03, 65% | f\* = 85.6, N=4, 50.2, 6.0, 88% |
| Synthetic (0.40, 3.0) | w\* = 4.4, N=5, 17.3, 11.9, 66% | f\* = 69.0, N=10, 30.4, 7.2, 85% |

A per-attempt monopolist prices the *first* attempt (w ≈ q₀H − v) and the firm stops after one; the success fee extracts less per defect but sustains deeper sampling.

Over 296 random draws (a ∈ [0.05, 0.6], b ∈ [0.1, 4], H ∈ [30, 500], v/H ∈ [0.001, 0.03], k/v ∈ [0.1, 3]): the success fee raises vendor profit in 99% of draws and total surplus in 100% (median 91% of first-best, interquartile range 88–94%, versus 65%, 55–77%, under per-attempt pricing); median budgets are 28 (first-best), 1 (per-attempt), 6 (success fee). The firm's own saving is higher under the success fee in only 67% of draws, so outcome-based pricing can transfer surplus to the vendor and a side payment or two-part tariff may be needed.

### 5.2 Private quality

For a_H = 0.25, a_L = 0.08, b = 0.35, H = 100, v = 1, k = 0.2, the profit-order reversal is stark: at fee levels w = 10 and f = 50 and depth N = 10, the low type earns 73.8 under per-attempt pricing against the high type's 46.5, and under the success fee 14.8 against 32.6. In 60 random draws, the low type would mimic the high type's full-information contract in 98%; a separating linear contract exists in 77% (46 draws), always a success fee; separation costs the high type a median 11.0% of profit (interquartile range 7.1–16.8%); the induced budget is at least the full-information one in 76% of those draws, and total surplus and the firm's saving are higher under separation in 74% (median +7% and +9.7). In the remaining quarter the high type cannot separate by any linear contract and the market pools. Signaling by *generosity* thus partly offsets the monopoly distortion. These are numerical results under off-path beliefs that assign any other contract to the low type.

### 5.3 Competition

**Table 3. Differentiated-Bertrand equilibria, RepairBench-like case (first-best N = 10).** Entries: budget N, welfare as a share of first-best welfare for the same n and σ.

| σ | Vendors n | Per-attempt: N, welfare | Success fee: N, welfare |
|---|---|---|---|
| 1 | 2 | 9, 1.00 | 11, 1.00 |
| 10 | 2 | 3, 0.90 | 7, 0.97 |
| 10 | 5 | 4, 0.95 | 9, 1.00 |
| 30 | 2 | 1, 0.81 | 4, 0.94 |
| 30 | 5 | 1, 0.86 | 4, 0.96 |
| 30 | 10 | 1, 0.89 | 5, 0.98 |

With close substitutes (σ = 1) one rival suffices; with strongly differentiated vendors (σ = 30) the per-attempt equilibrium stays at the monopoly budget of one attempt even with ten vendors, and entry only widens coverage (from 50% to 91% of firms), as Proposition 8(b) predicts. The bound of Proposition 8(b) is conservative: the monopoly budget is reached at σ = 100. In 240 cells of a random sweep, the per-attempt equilibrium is not deviation-proof (a vendor gains by switching to a success fee) in 71% and the success-fee equilibrium is deviation-proof in 76%; vendors prefer the success fee in 55–100% of cells, while the firm's saving is higher under per-attempt pricing in 68–98%. Vendors thus pick the contract form that raises surplus but that firms often like less.

### 5.4 Calibration of the cost parameters and sensitivity

**Sources** (accessed 25 October 2026; code the replication package (anonymized for review), `sensitivity.py`).

*Human repair cost H.* The US Bureau of Labor Statistics (Occupational Outlook Handbook) reports a median hourly wage of $64.44 for software developers in May 2025. Employer Costs for Employee Compensation (private industry, June 2022, the latest release we retrieved) put benefits at 29.5% of total compensation, so a loaded cost is $64.44 / (1 − 0.295) ≈ $91 per hour. The annotated time to fix for SWE-bench Verified (Epoch AI's summary of the annotation) is under 15 minutes for 39% of tasks, 15 minutes to 1 hour for 52%, 1–4 hours for 8%, and above 4 hours for 3 tasks; with bucket midpoints the expected hands-on time is 0.52 hours, hence H ≈ $48 for an engineer familiar with the code. METR's check found these estimates likely optimistic (its sample was only six tasks), so we allow 2–4 times that time for an unfamiliar engineer: **H ranges from about $15 (a 10-minute fix) through $50 to $200, up to $400 or more for multi-hour fixes**, before any context-transfer overhead.

*Vendor cost per attempt k.* We multiply observed token usage by the OpenRouter price list. For function-level repair in RepairBench, a non-reasoning attempt uses about 1,700 input and 800 output tokens, and a reasoning model such as o4-mini about 1,400 input and 10,400 output tokens. At list prices the cost k is $0.0001–0.0013 for small and mid-sized open models, $0.011 for a frontier model at 800 output tokens, and $0.0006–0.11 with reasoning-length outputs of 10,400 tokens borrowed from the o4-mini case ($0.047 for o4-mini itself). For repository-level agents, SWE-bench submission READMEs report $0.60 (Bracket), $0.64 (Moatless with Claude 4 Sonnet) and $0.84 (Cortexa) per task. **k ranges from $0.0003 to about $0.1 at function level and about $0.6–3 for agents.** (Our own HumanEvalFix runs billed $0.00002–0.00004 per attempt for 3–8B models.)

*Firm cost per attempt v.* If verification is an automated test run, v is the CI cost, about $0.01–0.50. If an engineer spends 2–10 minutes triaging each candidate patch, v is about $3–15 at $91 per hour. This is the least well-grounded input; it is a judgement based on the loaded wage and not a measured quantity.

**Sensitivity.** We evaluate all combinations on a grid within each regime and three heterogeneity profiles (the RepairBench-like fit, the SWE-Verified-like calibration, and a HumanEvalFix-Llama-like fit with a = 0.50, b = 0.58), computing the monopoly equilibria exactly (profit at the top of each budget step; Appendix E). Table 4 summarizes, across the three profiles, the points at which AI repair is worth using (N^FB ≥ 1).

**Table 4. Sensitivity of the main conclusions across calibrated ranges** (ranges across the three heterogeneity profiles; grids: 100–180 points per profile).

| Regime (H, v, k grids) | AI repair worth using | Welfare: success fee > per-attempt | Vendor profit: success fee ≥ per-attempt | Firm saving: success fee > per-attempt | Median welfare / first best: per-attempt; success fee | Vendor's depth below N^FB | Median rent share of W(N^FB) |
|---|---|---|---|---|---|---|---|
| Function-level, automated verification (H $15–400; v $0.01–0.5; k $0.0003–0.1) | 100% | 97–100% | 100% | 97–100% | 0.48–0.54; 0.87–0.93 | 100% | 90–91% |
| Function-level, manual triage (H $15–400; v $3–15; k $0.0003–0.1) | 75–88% | 22–57% | 100% | 22–57% | 0.72–0.91; 0.87–0.91 | 61–86% | 67–95% |
| Repository-level agents (H $50–800; v $0.1–5; k $0.6–3) | 100% | 76–95% | 100% | 76–95% | 0.56–0.67; 0.92–0.93 | 92–100% | 37–44% |

*Findings.* (i) The vendor's preference for the success fee is robust: its profit is at least as high in 100% of the points in every regime. (ii) The welfare advantage of the success fee is strong where an attempt is cheap relative to human repair (automated verification: 97–100% of points; agentic repair: 76–95%) and weak when manual triage makes each attempt expensive (22–57%), because the efficient depth is then small (median 2–6) and a per-attempt monopolist that stops the firm after one or two attempts loses little. (iii) The incentive rent is large where depth is valuable, about nine-tenths of the surplus under automated verification and 37–44% for agents, so vendors undersample in 61–100% of points. (iv) Figure 1 shows the pattern in the cost ratios: when H/v is below about 30 the efficient depth is one or two attempts and both contract forms are near-efficient; above it, per-attempt monopoly welfare falls to 0.4–0.6 of first best while the success fee stays near 0.85–0.9. The conclusions of Sections 4–5 therefore apply to the regimes with H/v of about 30 or more, which covers automated verification and agentic repair and excludes cheap fixes with expensive per-attempt human review.

![**Figure 1.** Welfare (share of first best) under per-attempt and success-fee monopoly, and the incentive rent as a share of surplus at the first-best depth, as functions of H/v and k/v (a = 0.12, b = 0.39). Blank cells are combinations in which AI repair is not worth using.](/home/user/fluffy-meme/paper/contracts/fig_sensitivity.png){width=5.2in}

---

## 6. Evidence on the Model's Premises

The model rests on (P1) heterogeneous difficulty, (P2) informative failures, and (P3) good out-of-sample performance of a threshold fitted to history. Code in the replication package (anonymized for review).

**RepairBench** (Silva and Monperrus 2025): 574 single-function Java bugs (484 Defects4J v2, 90 GitBug-Java), ten sampled patches per bug and model, scored by the full test suite; 84 model × dataset combinations after requiring ten samples and at least 80 bugs (22,856 records). The Beta-binomial beats the homogeneous binomial in all 84 by AIC and held-out likelihood (50/50 split by bug identifier); median fitted a = 0.12, b = 0.39 (U-shaped), median 59% of bugs never solved in ten samples. Median thresholds at H/c = 10, 30, 100, 300 are 1, 3, 11, 34. Fitted on half the bugs and evaluated exactly on the other half (caps up to ten, cost in units of c), the reservation rule is within 0.4–1.7% of the best cap in hindsight and 34–67% below a ten-sample cap for H/c between 3 and 10; a ten-sample cap costs more than human-only repair when H/c ≤ 10.

**HumanEvalFix, 40 samples per bug** (new; Python, 164 bugs; Llama-3.2-3B, Ministral-8B, Gemma-3-4B at temperature 1.0; 19,680 samples, $0.56 total). The Beta-binomial improves AIC over the binomial by thousands of points in all three (for example 7,293 to 739). A fit to the first ten samples predicts coverage at 40 samples within 2.6 points (for example Llama observed 0.927, predicted 0.909). For Gemma and Llama the fitted rule is within about 1% of the best cap. For Ministral, which solves 96% of bugs and leaves a small unsolvable residue, the rule oversamples (N = 9–40 against a hindsight best of 3–7) and costs 19–40% more than the best cap at H/c ≤ 30, because the Beta tail assigns positive success probability to bugs that are never solved and half a sample of 164 bugs cannot identify that share. A firm should therefore validate the fitted threshold against a held-out cap sweep.

**SWE-bench.** The official submission logs are pass@1 by rule, so attempt-level data do not exist there. Two published pass@1/pass@k pairs identify the Beta parameters (calibration, not a test): DeepSWE (Verified) gives (0.25, 0.34) and the Lite series of Brown et al. (2024) gives (0.12, 0.65), again with a < 1. Coverage exceeds the verifier-selected rate (71.0% vs. 59.2%; 75% vs. 68.4%), so at repository level success is observed only through an imperfect verifier, which lowers the benefit of success in the thresholds.

---

## 7. Extensions

**Imperfect verification.** If a passing patch is wrong with probability e at downstream cost L, the benefit H in the thresholds becomes H − eL; weaker tests shorten the justified search, and in contract B disputes over what counts as a verified fix become a cost.

**Further directions.** Latency and severity-contingent thresholds, defect classes with their own (a, b), continuous vendor types and contract menus, multi-sourcing, dynamic learning of (a, b) across defects, and behavioral frictions on the buyer's side (for example loss aversion toward per-attempt payments or sunk-cost effects), which require experimental evidence to parameterize and are not modeled here.

---

## 8. Discussion

**Theory.** (1) The economically relevant decision is whether to continue after a failure, not the pass@k capability. (2) A seller's markup distorts per-attempt contracts, and competition removes it only if vendors are close substitutes. (3) The underlying force is an incentive rent of sequential search, which explains why vendors prefer pure success fees, why they sample too little, and why a lump sum would restore efficiency. (4) Outcome-based pricing raises surplus, but not necessarily the buyer's share.

**Managerial implications.** *Buyers* should estimate (a, b) from their own repair logs, compute the threshold from H and the full cost per attempt (including verification), validate it on held-out defects, and negotiate a success fee near Hk/(k+v) in return for volume. *Vendors* gain from outcome-based pricing, including under competition, but should recognize that in commodity markets with close substitutes per-attempt pricing near cost is efficient. *Platforms and governance bodies* should publish per-sample outcomes and per-attempt costs, which determine the contracts' inputs and are invisible in current leaderboards.

**Limitations.** (1) H, v, and k are calibrated from public statistics and price lists (Section 5.4) but not measured on a firm, and v is the least well grounded; benchmark bugs (single functions with complete tests) are easier to verify than industrial defects. (2) Attempts are conditionally independent given p; correlation across samples would make failure more informative. (3) Vendors are symmetric, with logit competition and a one-shot game; private information is analyzed for two types and linear contracts, and the separation and competition results are numerical. (4) Patch quality is binary. (5) Public benchmarks may overlap with training data.

**Field validation.** The analytical results do not depend on field data, but the contract predictions (outcome-based pricing under market power, per-attempt pricing among close substitutes) and the cost parameters would be tested directly by a study with a partner firm (Appendix D).

---

## 9. Conclusion

An AI repair service creates two linked decisions: how long the buyer lets the AI try, and how the vendor charges for trying. When defects differ in difficulty, the buyer's optimal rule is a threshold that rises with the cost of human repair and falls with the price and difficulty of attempts. Charging per attempt above cost makes the buyer give up too early; a pure success fee is the vendor's best pay-per-use contract, but because deep sampling requires leaving the buyer an incentive rent, even it samples too little. A lump sum would remove every distortion; competition does so only among close substitutes. Public repair data support the premises of heterogeneous difficulty and informative failures, and a threshold fitted to past defects usually performs close to the best cap, though it can oversample when the unsolvable share is small and poorly identified. The next step is to test the contract predictions on a firm's repair and billing records.

---

## References

*(Verify details against the originals before submission.)*

- Agrawal, A., Gans, J., and Goldfarb, A. (2018). *Prediction Machines.* Harvard Business Review Press.
- Bajari, P., and Tadelis, S. (2001). Incentives versus transaction costs: A theory of procurement contracts. *RAND Journal of Economics*, 32(3), 387–407.
- Banker, R. D., and Slaughter, S. A. (2000). The moderating effects of structure on volatility and complexity in software enhancement. *Information Systems Research*, 11(3), 219–240.
- Brown, B., et al. (2024). Large language monkeys: Scaling inference compute with repeated sampling. arXiv:2407.21787.
- Brynjolfsson, E., Li, D., and Raymond, L. (2023). Generative AI at work. NBER Working Paper 31161.
- Chen, M., et al. (2021). Evaluating large language models trained on code. arXiv:2107.03374.
- Chow, Y. S., Robbins, H., and Siegmund, D. (1971). *Great Expectations: The Theory of Optimal Stopping.* Houghton Mifflin.
- Fügener, A., Grahl, J., Gupta, A., and Ketter, W. (2022). Cognitive challenges in human–artificial intelligence collaboration. *Information Systems Research*, 33(2), 678–696.
- Gopal, A., Sivaramakrishnan, K., Krishnan, M. S., and Mukhopadhyay, T. (2003). Contracts in offshore software development. *Management Science*, 49(12), 1671–1683.
- Jimenez, C. E., et al. (2024). SWE-bench. *ICLR 2024.*
- Kemerer, C. F., and Slaughter, S. (1999). An empirical approach to studying software evolution. *IEEE Transactions on Software Engineering*, 25(4), 493–509.
- Le Goues, C., Nguyen, T., Forrest, S., and Weimer, W. (2012). GenProg. *IEEE Transactions on Software Engineering*, 38(1), 54–72.
- Lientz, B. P., and Swanson, E. B. (1980). *Software Maintenance Management.* Addison-Wesley.
- McCall, J. J. (1970). Economics of information and job search. *Quarterly Journal of Economics*, 84(1), 113–126.
- Raisch, S., and Krakowski, S. (2021). Artificial intelligence and management. *Academy of Management Review*, 46(1), 192–210.
- Silva, A., and Monperrus, M. (2025). RepairBench. *LLM4Code Workshop (ICSE 2025).* arXiv:2409.18952.
- Spengler, J. J. (1950). Vertical integration and antitrust policy. *Journal of Political Economy*, 58(4), 347–352.
- Stigler, G. J. (1961). The economics of information. *Journal of Political Economy*, 69(3), 213–225.
- Tirole, J. (1988). *The Theory of Industrial Organization.* MIT Press.
- Weitzman, M. L. (1979). Optimal search for the best alternative. *Econometrica*, 47(3), 641–654.
- Whang, S. (1992). Contracting for software development. *Management Science*, 38(3), 307–324.
- Xia, C. S., and Zhang, L. (2023). Automated program repair in the era of large pre-trained language models. *ICSE 2023.*

---

## Appendix A. Survival Function and Posterior Predictive (Beta)

Given p, P(T > j | p) = (1−p)^j; integrating over p ~ Beta(a, b) gives S(j) = B(a, b+j)/B(a, b). After n failures the posterior is Beta(a, b+n) with mean a/(a+b+n) = q_n.

## Appendix B. Estimation

With counts (n samples, k successes) per defect the Beta-binomial likelihood is C(n,k)·B(k+a, n−k+b)/B(a,b); first-success data censored at K attempts contribute B(a+1, b+t−1)/B(a,b) (solved at t) or B(a, b+K)/B(a,b) (unsolved). Both are maximized over (log a, log b) by Nelder–Mead (the replication package (anonymized for review)).

## Appendix C. Reproducibility

- Contracts and equilibria: `cd paper/contracts && python3 contracts.py && python3 robustness.py`; private quality: `asymmetric.py`, `asym_sweep.py`; competition: `diff_bertrand.py`, `diff_sweep.py`; proof checks: `verify_proofs.py`; distribution-free checks (Propositions 1, 5, 6): `general_theory.py`.
- RepairBench: `cd paper/empirical && python3 load_repairbench.py <repairbench>/results && python3 analyze.py`; SWE-bench: `python3 swebench_repo_level.py <experiments>/evaluation`; HumanEvalFix: `cd paper/empirical/sampling && python3 sample_humanevalfix.py <model> 40 && python3 analyze_hef.py`.
- Cost calibration and sensitivity: `cd paper/contracts && python3 calibration.py && python3 sensitivity.py && python3 fig_sensitivity.py`.

## Appendix D. Field-Data Request and Design (Not Executed)

**Variables per defect:** identifier and type; timestamps of arrival, each AI attempt, verification, escalation, closure; per attempt, test outcome, token counts, vendor-billed compute cost, verifier effort; escalation outcome; human engineering hours and fully loaded cost; post-merge defects traced to AI patches; contract terms.
**Design:** randomize the attempt cap within strata (type, severity) for at least a quarter; estimate (a, b) by stratum from the first part, compare realized cost per resolved defect under the reservation rule and the firm's existing cap; if the vendor offers both contract forms, randomize contract by team.
**Confidentiality:** attempt-level outcomes and costs suffice; code and defect text are not needed.

## Appendix E. Proofs

**Lemma A (steps).** For contract B, N_B(f) = n ≥ 1 iff q_n(H−f) ≤ v < q_{n−1}(H−f), i.e. f ∈ [φ_n, φ_{n−1}) with φ_n = H − v/q_n (Beta: φ_n = H − v(n+a+b)/a, equal step width v/a); N_B(f) = 0 iff f ≥ φ_0. At f = φ_n the firm is indifferent about attempt n+1 and stops.

**Lemma B (boundary comparison).** With L(n) = φ_n P(n) − kE(n) and R(n) = φ_{n−1}P(n) − kE(n),
R(n) − L(n−1) = φ_{n−1}[P(n) − P(n−1)] − k[E(n) − E(n−1)] = S(n−1)[φ_{n−1}q_{n−1} − k] = S(n−1)[q_{n−1}H − (k+v)],
using P(n) − P(n−1) = q_{n−1}S(n−1), E(n) − E(n−1) = S(n−1), and q_{n−1}(H − φ_{n−1}) = v. The sign is that of the efficiency of attempt n, equivalently of φ_{n−1} − f^e.

**Proof of Proposition 4.** Profit within step n is fP(n) − kE(n) with slope P(n) > 0, so L(n) < Π < R(n) in the interior, and R(n) − L(n) = (φ_{n−1} − φ_n)P(n) > 0. Let n₀ = N^FB ≥ 1, so f^e ∈ [φ_{n₀}, φ_{n₀−1}). *(b)* For n > n₀, φ_{n−1} ≤ φ_{n₀} ≤ f^e, so by Lemma B R(n) ≤ L(n−1) < R(n−1): R is strictly decreasing from n₀ on, hence n̂ ≤ n₀. *(a)* Take f′ ≤ f^e with n = N_B(f′) ≥ n₀. If n = n₀, any f ∈ (f^e, φ_{n₀−1}) has Π(f) > Π(f′) by monotonicity within the step. If n > n₀, Π(f′) < R(n) < R(n₀) and the supremum of Π on (f^e, φ_{n₀−1}) equals R(n₀). ∎

**Proof of Proposition 5.** (a) Each term of G_min is nonnegative since q_j ≥ q_{N−1}; N = 1 gives P(1)/q₀ − E(1) = 1 − 1 = 0; from N to N+1 existing terms weakly rise (q_N ≤ q_{N−1}) and the new term is zero. (b) The firm chooses depth N only if q_{N−1}(H−f) > w+v, so f < φ_{N−1} − w/q_{N−1}. Then Π = (w−k)E + fP < (w−k)E + [φ_{N−1} − w/q_{N−1}]P = R(N) − w[P/q_{N−1} − E], and R(N) = W(N) − G_min(N) follows from φ_{N−1}P − kE = HP − (k+v)E − v[P/q_{N−1} − E]. (c) At (0, φ_{N−1}) participation holds since vE + φ_{N−1}P ≤ HP ⇔ q_{N−1}E ≤ P, true because P = Σ_{j<N} S(j)q_j. (d) G_min(N+1) − G_min(N) = vP(N)(1/q_N − 1/q_{N−1}) from P(N+1) = P(N) + q_N S(N), E(N+1) = E(N) + S(N), and W(N+1) − W(N) = S(N)[q_N H − (k+v)]. ∎

