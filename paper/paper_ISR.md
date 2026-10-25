---
journal: Information Systems Research (INFORMS) — manuscript structure
status: Draft v2 — analytical model + public-data calibration; field data NOT yet collected (see Appendix D)
---

# Who Pays for the Next Attempt? Contract Design and Escalation Rules for AI-Assisted Software Maintenance

**Authors:** [Author names, affiliations] · **Corresponding author:** [email]

**Keywords:** AI–human task allocation; escalation; outcome-based pricing; vendor contracting; software maintenance; large language models; double marginalization; optimal stopping

---

## Abstract

Firms increasingly buy AI-based defect repair as a service: a large language model (LLM) proposes patches, the firm verifies them, and unresolved defects are escalated to human engineers. Two design choices govern the economics of this arrangement. The firm chooses an *escalation rule*, i.e., how many AI attempts to allow before handing the defect to a person; the vendor chooses a *pricing rule*, i.e., whether to charge per attempt or per verified fix. We study the interaction as a Stackelberg game in which defects are heterogeneous in how easily they are repaired, so that each failed attempt is informative about whether the next one will succeed. We show that (i) the firm's optimal escalation rule is a reservation rule with closed-form threshold N\* = ⌈a·H/c − a − b⌉, where *H* is the cost of human repair, *c* the firm's effective cost per attempt, and (*a*, *b*) describe the heterogeneity of repair difficulty; (ii) per-attempt pricing above marginal cost produces a double-marginalization distortion, since the firm stops the AI too early; (iii) a success fee equal to the share k/(k+v) of the human cost implements the jointly optimal attempt budget and gives the vendor that share of the surplus; and (iv) a profit-maximizing vendor nevertheless sets a higher fee, so equilibrium sampling is again too shallow, but total surplus is far closer to the optimum than under per-attempt pricing. In a parameter sweep calibrated to public repair data, the success-fee contract raises vendor profit in 99% of draws and total surplus in all of them (median 91% vs. 65% of the first-best surplus), though the firm itself is better off in only two-thirds of draws, which identifies the conditions under which a side payment or two-part tariff is needed. We test the model's behavioural premises on open data: on RepairBench (574 bugs, 45 LLMs, 10 samples per bug) a heterogeneous-difficulty model beats a homogeneous one in all 84 model–dataset combinations, and an escalation threshold fitted on half the bugs attains within 0.4–1.7% of the best cap in hindsight on the other half. A new 40-sample experiment on HumanEvalFix shows that a fit to the first ten samples predicts coverage at forty within 2.6 points, but that the rule oversamples when only a small share of defects is unsolvable and history is short. We discuss implications for IT service contracting and for the governance of AI-augmented maintenance.

---

## 1. Introduction

Software maintenance absorbs most of the lifetime cost of information systems (Lientz and Swanson 1980), and the arrival of LLM-based repair agents changes how that work is organized. Instead of assigning every defect to an engineer, a firm can route it first to an AI service, accept a patch if it passes the firm's tests, and escalate to a person only if the AI fails. The management literature has stressed that AI–human arrangements succeed or fail on the *allocation of tasks* and the *design of delegation* (Raisch and Krakowski 2021; Fügener et al. 2022), but it has paid less attention to two questions that arise in this concrete setting: how many failed AI attempts a firm should tolerate before escalating, and how the vendor's price structure shapes that choice.

Both questions turn on a statistical regularity that is easy to overlook. LLM repair is stochastic, so the same defect can be attempted repeatedly, and a patch that passes the tests can be accepted at once. But defects differ enormously in how likely any single attempt is to succeed: some are fixed on almost every attempt, and some are almost never fixed. Because of this heterogeneity, a run of failures is *bad news about the defect itself*, and the marginal value of another attempt falls as failures accumulate. A firm that plans with an average success rate would never stop; a firm that fixes the number of attempts by convention (typically between five and ten) ignores both its own cost of human repair and the vendor's price.

The vendor's pricing then matters because it determines the cost of an additional attempt as the firm sees it. Under *per-attempt* pricing (a per-token or per-call fee), the firm bears the full price of every attempt, including the many that fail on hard defects. Under *outcome-based* pricing (a fee only for a verified fix), the firm pays only for success, and the vendor bears the compute cost of failures. Practitioners debate these structures, and some vendors have begun to offer success-based pricing, but there is little analysis of how the structures change the firm's escalation behavior, the vendor's profit, and total surplus.

**Research questions.**
RQ1. What is the firm's optimal escalation rule when repair difficulty is heterogeneous and unobserved?
RQ2. How does the vendor's contract (per-attempt vs. success fee) distort or restore the firm's attempt budget?
RQ3. Which contract does a profit-maximizing vendor choose, and what does it imply for the firm and for total surplus?
RQ4. Are the model's behavioural premises (heterogeneity, learning from failure) borne out in real repair data?

**Contributions.** (1) We formulate AI–human task allocation in maintenance as a sequential search problem with an outside option and embed it in a vendor–buyer Stackelberg game, linking the AI-delegation literature to the IT contracting literature. (2) We obtain a closed-form escalation threshold and show that per-attempt pricing creates a double-marginalization inefficiency. (3) We show that a success fee of Hk/(k+v) restores the efficient attempt budget, and that the vendor's optimal fee exceeds it. (4) We quantify the comparison in a calibrated sweep and identify when the firm loses from outcome-based pricing. (5) We test the premises on three open data sources (RepairBench, SWE-bench submissions, and a new multi-sample HumanEvalFix experiment).

---

## 2. Related Literature

**AI–human collaboration and delegation.** Research on AI augmentation shows that productivity gains depend on how work is divided between AI and people and on how well people know when to delegate (Raisch and Krakowski 2021; Fügener et al. 2022; Brynjolfsson et al. 2023). The economics of prediction treats AI as lowering the cost of a prediction while leaving judgement and verification with humans (Agrawal et al. 2018). We contribute a model of the *escalation boundary* in a specific production setting, in which the AI's output is checkable and each failure is informative.

**IT service contracting and software maintenance.** Work on software and IT services contracts studies the allocation of risk and incentives between client and vendor, including fixed-price and time-and-materials structures (Whang 1992; Bajari and Tadelis 2001; Gopal et al. 2003). Empirical work on maintenance documents the volatility of maintenance workloads and their dependence on system structure (Banker and Slaughter 2000; Kemerer and Slaughter 1999). We add a contract dimension specific to generative AI services: the unit of payment can be an attempt or a result.

**Vertical contracting and double marginalization.** When an upstream seller charges a markup over marginal cost on a unit input, a downstream buyer under-purchases relative to the joint optimum (Spengler 1950; Tirole 1988). We show that this logic applies to the number of AI attempts, and that outcome-based pricing changes the unit of purchase so that the distortion is reduced.

**Search and optimal stopping.** The sequential structure follows search theory (Stigler 1961; McCall 1970; Weitzman 1979), in which a decision maker continues until the expected marginal gain falls below the marginal cost, with a reservation rule characterizing the optimum. Our twist is that the success probability is learned from failures through heterogeneity across defects, which produces a declining marginal value of search.

**Automated program repair.** LLM-based repair evaluates patches by tests and reports pass@k (Chen et al. 2021; Le Goues et al. 2012; Xia and Zhang 2023; Jimenez et al. 2024; Silva and Monperrus 2025). Repeated sampling raises coverage with diminishing returns (Brown et al. 2024). These papers measure capability; they do not model the economic choice of how many attempts to buy.

---

## 3. Model

**Players and timing.** A firm faces a stream of defects. A monopolist vendor offers an AI repair service. The game has three stages. (1) The vendor announces a contract. (2) The firm accepts or rejects it; if it rejects, every defect is repaired by a human at cost *H*. (3) For each defect the firm sequentially requests AI attempts, verifies each returned patch at its own cost, and stops when it accepts a passing patch or decides to escalate to a human.

**Defects and attempts.** Each defect has a latent per-attempt success probability *p*, drawn from a Beta(*a*, *b*) distribution across defects with *a*, *b* > 0. Given *p*, attempts are independent. Neither player observes *p*, but both observe the outcome of each attempt (a patch either passes the firm's tests or does not). Let *T* be the index of the first successful attempt. Then

S(j) ≡ P(T > j) = B(a, b+j) / B(a, b),  (1)

and the posterior predictive probability that attempt *n*+1 succeeds, after *n* consecutive failures, is

q\_n = a / (a + b + n),  (2)

which is strictly decreasing in *n* (Appendix A).

**Costs.** A human repair costs *H*. Each AI attempt costs the vendor *k* (compute) and the firm *v* (running tests, triage, review). Let E(N) = Σ\_{j=0}^{N−1} S(j) denote the expected number of attempts under a cap *N*, and P(N) = 1 − S(N) the probability the AI resolves the defect within *N* attempts. Verification is assumed accurate here and relaxed in Section 7.

**Contracts.**
- **Per-attempt (A):** the firm pays *w* ≥ *k* for each attempt, so its effective cost per attempt is *c* = *w* + *v*.
- **Success fee (B):** the firm pays *f* ∈ [0, *H*] for each *verified* fix and nothing for failed attempts, so its cost per attempt is *v*; on success it pays *f* instead of *H*.
- **Joint benchmark:** a planner internalizes both cost types, so the effective cost per attempt is *k* + *v*.

**Payoffs.** The firm minimizes expected total cost; the vendor maximizes expected profit. Total surplus relative to human-only repair is the firm's saving plus the vendor's profit,

W(N) = H·P(N) − (k+v)·E(N),  (3)

which does not depend on the transfer between the parties.

---

## 4. Analysis

**Proposition 1 (Firm's escalation rule).** Under contract A with fee *w*, the firm makes attempt *n*+1 if and only if q\_n·H > *w* + *v*, i.e., it allows

N\_A(w) = max{0, ⌈ aH/(w+v) − a − b ⌉}  (4)

attempts. Under contract B with fee *f*, it makes attempt *n*+1 if and only if q\_n·(H − f) > *v*, i.e., it allows

N\_B(f) = max{0, ⌈ a(H−f)/v − a − b ⌉}.  (5)

Both are decreasing in the respective price. The jointly optimal budget is N^FB = max{0, ⌈ aH/(k+v) − a − b ⌉}.

*Proof.* After *n* failures the state is summarized by *n*. In state *n* the firm compares stopping (cost *H*) with trying once more and then stopping, whose cost under A is (w+v) + (1−q\_n)H, so continuing is preferred iff q\_n H > w+v. Because q\_n is decreasing (Appendix A), once the comparison fails it fails for every larger *n*, so the problem is monotone and the one-step look-ahead rule is optimal (Chow, Robbins and Siegmund 1971). Under B, one more attempt costs *v* and, with probability q\_n, replaces the human cost *H* with the fee *f*: continue iff q\_n(H−f) > v. Solving q\_n·X > Y for *n* with q\_n from (2) gives (4)–(5). The joint benchmark is (4) with *w* = *k*. ∎

**Proposition 2 (Double marginalization).** Under contract A with *w* > *k*, the firm's attempt budget is weakly below the jointly optimal one, N\_A(w) ≤ N^FB, and total surplus is weakly below its first-best level; the inequality is strict whenever *w* is large enough to lower the ceiling in (4).

*Proof.* N\_A is decreasing in *w*, so N\_A(w) ≤ N\_A(k) = N^FB. W(N) in (3) has increments W(N+1) − W(N) = S(N)(q\_N H − (k+v)), which are positive iff q\_N H > k+v, i.e., for N < N^FB, and non-positive afterward. So W is increasing up to N^FB and W(N\_A) ≤ W(N^FB), strictly when N\_A < N^FB. ∎

*Interpretation.* The vendor's markup *w* − *k* is an additional cost of each attempt that the firm treats as real but that is a pure transfer from the planner's point of view. This is the same structure as the classic double-marginalization result, applied to the number of purchased attempts.

**Proposition 3 (An efficient success fee).** Under contract B with *f*^e = H·k/(k+v), the firm's attempt budget equals the jointly optimal one, N\_B(f^e) = N^FB. The vendor's profit then equals k/(k+v) of the first-best surplus, and the firm retains v/(k+v) of it.

*Proof.* (H − f^e)/v = H v/((k+v)v) = H/(k+v), so (5) coincides with N^FB. Vendor profit is f^e P(N^FB) − k E(N^FB) = (k/(k+v))[H P(N^FB) − (k+v) E(N^FB)] = (k/(k+v))·W(N^FB). The firm's saving is the remainder. ∎

*Interpretation.* A fee tied to the human cost makes the firm's marginal calculus equal to the planner's. The vendor, who bears the compute cost of failed attempts, is compensated for them in the fee on success, and the firm no longer treats the vendor's markup as a cost of trying.

**Proposition 4 (The vendor's optimal fee exceeds the efficient fee).** In the continuous relaxation of the attempt budget, the vendor's profit Π(f) = f·P(N\_B(f)) − k·E(N\_B(f)) satisfies Π′(f^e) = P(N^FB) > 0. Hence a profit-maximizing vendor sets f\* > f^e, and the firm's resulting attempt budget N\_B(f\*) is strictly below N^FB.

*Proof (sketch).* Differentiating, Π′(f) = P(N) + [f·P′(N) − k·E′(N)]·N′(f), with P′(N) = q\_N S(N) and E′(N) = S(N) (the density of the marginal attempt). At N^FB the first-order condition of the joint problem gives q\_N H ≈ k+v, so that f^e q\_N S(N) − k S(N) = k S(N)[H q\_N/(k+v) − 1] ≈ 0 and the bracket vanishes up to integer rounding. Therefore Π′(f^e) ≈ P(N^FB) > 0. Since N\_B is decreasing in *f*, the vendor raises the fee beyond f^e, trading off a higher price per fix against shallower sampling. ∎

*Remark (two-part tariffs).* If the vendor could also charge a lump sum, it would set *w* = *k* and a fixed fee equal to the firm's surplus, implementing N^FB and capturing all of W(N^FB). We treat such contracts as a benchmark rather than as an equilibrium prediction, because a lump sum requires the vendor to know the firm's surplus (that is, (a, b) and H) and requires the firm to commit before observing performance. When these are private, the linear contracts above are the relevant ones.

**Numerical results for the equilibria.** Closed forms for the vendor's optimal *w* and *f* are not available because the attempt budget is an integer-valued step function. Section 5 therefore computes the Stackelberg equilibria numerically over a grid and a random parameter sweep.

---

## 5. Equilibrium Comparison

Code and outputs: `paper/contracts/contracts.py`, `robustness.py`, `results_contracts.txt`, `results_robustness.txt`. Parameters (*a*, *b*) are taken from empirical fits in Section 6; *H*, *v*, *k* are **illustrative** because no cost data are available publicly.

### 5.1 Selected scenarios

Illustrative case: H = $100, v = $1, k = $0.2. First-best surplus S^FB and equilibrium outcomes under each contract (N = attempt budget; welfare in dollars per defect and as a share of S^FB):

| Heterogeneity (a, b) | First-best N / S^FB | Per-attempt monopoly: w\*, N, vendor profit, firm saving, welfare | Success-fee monopoly: f\*, N, vendor profit, firm saving, welfare |
|---|---|---|---|
| RepairBench-like (0.12, 0.39) | 10 / 33.9 | 22.5, 1, 22.3, 0.01, 22.3 (66%) | 79.0, 3, 25.6, 4.4, 30.0 (89%) |
| SWE-Verified-like (0.25, 0.34) | 21 / 63.5 | 41.3, 1, 41.1, 0.03, 41.2 (65%) | 85.6, 4, 50.2, 6.0, 56.2 (88%) |
| Synthetic (0.40, 3.0) | 30 / 43.9 | 4.4, 5, 17.3, 11.9, 29.2 (66%) | 69.0, 10, 30.4, 7.2, 37.5 (85%) |

At the efficient fee f^e = Hk/(k+v) = $16.67 the attempt budget equals N^FB in each case and the vendor's share of surplus is 16.7% (= 0.2/1.2), as Proposition 3 states.

### 5.2 What drives the results

Under per-attempt pricing the monopolist sets the fee at roughly the value of the *first* attempt, q₀H − v, where q₀ = a/(a+b). With strongly U-shaped heterogeneity, q₀ is large and the first attempt resolves a sizable fraction of defects, so the vendor can extract nearly all of the firm's gain from the first attempt while the firm abandons further attempts (N = 1). The firm's saving is close to zero, and total surplus falls to about two-thirds of the optimum. Under a success fee, the vendor can no longer price the first attempt without also pricing the tail: a high fee reduces the firm's willingness to continue, but the firm still pays nothing for failures, so it keeps sampling longer (N = 3–10), and the fee is paid out of realized savings. Surplus rises to 85–89% of the optimum, and the vendor does better as well.

### 5.3 Robustness across parameters

Over 296 random draws with *a* ∈ [0.05, 0.6], *b* ∈ [0.1, 4] (log-uniform), *H* ∈ [30, 500] (log-uniform), v/H ∈ [0.001, 0.03], and k/v ∈ [0.1, 3]:

| Outcome | Result |
|---|---|
| Vendor profit higher under success fee | 99% of draws |
| Total surplus higher under success fee | 100% of draws |
| Firm saving higher under success fee | 67% of draws |
| Surplus as share of first-best, median (IQR) | per-attempt 0.65 (0.55–0.77); success fee 0.91 (0.88–0.93) |
| Median attempt budget | first-best 28; per-attempt monopoly 1; success-fee monopoly 6 |
| Vendor share at f^e vs. k/(k+v) | equal (max abs. difference 0.000) |

**The firm does not always gain.** In one-third of draws the firm is worse off under the success fee, because the vendor captures most of the larger surplus. Total surplus is higher in every draw, so a transfer could make both parties better off, for example a lower fee in exchange for a minimum-volume commitment or a two-part tariff. This identifies the circumstances in which the buyer should resist an outcome-based fee that is set close to the human repair cost.

### 5.4 Misjudging vendor quality

Suppose the firm sets its attempt budget on the belief a = 0.25 while the true difficulty parameter is lower (b = 0.39, H = 100, v = 1, k = 0.2). The firm's loss relative to choosing the budget with correct beliefs is:

| True *a* | Per-attempt (w = $2.0): loss | Success fee (f = f^e): loss |
|---|---|---|
| 0.15 | 1.10 | 0.95 |
| 0.10 | 3.49 | 3.00 |
| 0.05 | 9.02 | 7.83 |

The loss is about 13% smaller under the success fee because the firm pays for fewer of the wasted attempts, but the protection is modest: the firm still bears its own cost *v* of verifying every failed patch. Outcome-based pricing transfers the vendor's compute cost of failure, not the buyer's verification cost, which matters for how much risk the contract actually shifts.

---

## 6. Evidence on the Model's Premises from Open Repair Data

The model rests on three empirical premises: (P1) repair difficulty is heterogeneous across defects; (P2) failures are informative, so the value of an additional attempt declines; (P3) a reservation threshold estimated from past defects performs well out of sample. We test them on open data. All code is in `paper/empirical/`.

### 6.1 RepairBench (574 Java bugs, 45 LLMs, 10 samples per bug)

**Data.** RepairBench (Silva and Monperrus 2025; github.com/ASSERT-KTH/repairbench) records for each of 574 single-function bugs (484 Defects4J v2, 90 GitBug-Java) ten independently sampled patches per model, and whether each passes the full test suite. After requiring ten samples per bug and at least 80 bugs per combination, we obtain 84 model × dataset combinations (22,856 bug–model records). Only the number of successes *k* ∈ {0,…,10} per bug is used; the Beta-binomial likelihood is C(10,k)·B(k+a, 10−k+b)/B(a,b).

**P1 and P2: heterogeneity and informative failure.** The Beta-binomial beats the homogeneous binomial in **84/84** combinations by AIC and by held-out log-likelihood (bugs split 50/50 by a hash of the bug identifier). The median share of bugs with 0 of 10 successes is 0.59 against a median mean success rate of 0.22, and the median fitted parameters are *a* = 0.12 and *b* = 0.39, a U-shaped distribution: bugs are mostly either fixed nearly every time or almost never. A homogeneous model with the same mean (p̄ ≈ 0.22) would prescribe "never stop" at any realistic H/c. A zero-inflated variant, with a mass of bugs that are never solved, improves AIC in only 13/84 combinations and held-out likelihood in 36/84.

**Implied thresholds.** With N\* ≈ aH/c and small *a*, median thresholds are:

| H/c | 5 | 10 | 30 | 100 | 300 |
|---|---|---|---|---|---|
| N\* (Beta-binomial) | 1 | 1 | 3 | 11 | 34 |
| N\* (zero-inflated) | 1 | 1 | 3 | 10 | 26 |

**P3: out-of-sample performance.** For caps within the observed range, expected cost can be computed exactly from the real outcomes (for a bug with *k* successes among ten exchangeable samples, P(no success in first *j*) = C(10−k, j)/C(10, j)). Fitting on half the bugs and evaluating on the rest, averaged over the 84 combinations (cost in units of *c*; human-only equals H/c):

| H/c | Human only | Fixed k = 1 | Fixed k = 5 | Fixed k = 10 | Reservation rule (fit on training half) | Best fixed in hindsight |
|---|---|---|---|---|---|---|
| 3 | 3.00 | 3.34 | 5.87 | 8.95 | **2.96** | 2.95 |
| 5 | 5.00 | 4.91 | 7.20 | 10.19 | **4.77** | 4.69 |
| 8 | 8.00 | 7.25 | 9.19 | 12.05 | **7.21** | 7.15 |
| 10 | 10.00 | 8.81 | 10.51 | 13.28 | **8.78** | 8.73 |

The reservation rule is within 0.4–1.7% of the hindsight-optimal cap and 34–67% below the conventional ten-sample cap. A ten-sample cap costs more than human-only repair when H/c ≤ 10. The data limit the tests to caps of at most 10; thresholds for H/c ≥ 100 are model-based extrapolations (the Beta-binomial and zero-inflated medians differ by 8 attempts at H/c = 300).

**Cost heterogeneity across vendors.** Token usage is available for some models only. o4-mini averages about 10,400 completion tokens per attempt against 640–810 for DeepSeek-V3 and Qwen2.5-Coder, a 13–16× difference. The model makes the trade-off explicit: a stronger model has a larger *a* (o4-mini on Defects4J: a = 0.25, N\*(H/c = 100) = 25, versus DeepSeek-V3: a = 0.09, N\* = 9), but a much larger cost per attempt, which enters N\* through *c*.

### 6.2 Repository-level tasks (SWE-bench)

The official SWE-bench submission repository (github.com/SWE-bench/experiments) records, per submission, the single selected patch per task. All 111 submission READMEs we examined declare themselves pass@1 submissions, and none releases per-sample outcomes, so attempt-level data analogous to Section 6.1 do not exist there. A few READMEs report aggregate pass@k: DeepSWE-Preview (Qwen3-32B) gives pass@1 = 42.2% and pass@16 = 71.0% on SWE-bench Verified, with a verifier-selected rate of 59.2%; Cortexa (o3) gives pass@7 = 75% against a selected-patch rate of 68.4%. Brown et al. (2024) report 15.9% at one sample and 56% at 250 samples for DeepSeek-Coder-V2 on SWE-bench Lite.

Two published points identify (*a*, *b*) under the Beta-geometric model (calibration, not a test): DeepSWE gives (0.25, 0.34) and the Lite series gives (0.12, 0.65), both with *a* well below one and thresholds N\*(H/c = 100) of 25 and 12. Across 135 Verified and 84 Lite submissions, 5.8% (29/500) and 11.7% (35/300) of tasks are solved by no submission and the share of systems solving a task is widely dispersed (Beta fits (0.69, 0.77) and (0.44, 0.97)); because systems are not exchangeable samples, we read this as evidence of heterogeneous task difficulty, not as attempt-level parameters.

The gap between coverage and the selected rate (71.0% vs. 59.2%; 75% vs. 68.4%) shows that at repository level success is observed only through an imperfect verifier. This is the case treated in Section 7.

### 6.3 A new multi-sample experiment (HumanEvalFix)

Because RepairBench provides only ten samples, we sampled 40 patches per bug on HumanEvalFix (Python, 164 bugs) from three small open models (Llama-3.2-3B-Instruct, Ministral-8B, Gemma-3-4B-it; temperature 1.0), and ran the tests in an isolated subprocess. Total cost was under one dollar. Results are reported below (`paper/empirical/sampling/`).

### 6.4 Results of the 40-sample experiment

All 164 bugs were completed for each model (19,680 samples, zero failed calls, total billed cost $0.56).

| Model | Mean success | Bugs with 0/40 | Bugs with 40/40 | Beta-binomial (a, b) | AIC: binomial / BB / zero-inflated |
|---|---|---|---|---|---|
| Gemma-3-4B-it | 0.514 | 32% | 38% | (0.10, 0.09) | 7293 / 739 / 740 |
| Llama-3.2-3B-Instruct | 0.437 | 7% | 9% | (0.50, 0.58) | 4320 / 1180 / 1182 |
| Ministral-8B | 0.858 | 4% | 60% | (0.48, 0.09) | 3653 / 656 / 651 |

**Heterogeneity (P1, P2).** The Beta-binomial improves AIC over the homogeneous binomial by thousands of points in every model (e.g., 7,293 to 739 for Gemma), and the success distributions are strongly U-shaped, with 38–60% of bugs solved on every sample for two models and 32% never solved for the third. A zero-inflated variant is not preferred for Gemma or Llama, and is preferred only for Ministral (AIC 651 vs. 656).

**Extrapolation from ten samples to forty.** Fitting the Beta-geometric tail only to the first ten samples and predicting coverage at 40 samples gives:

| Model | Observed coverage @1 / 5 / 10 / 20 / 40 | Predicted from first-10 fit (BB) @1 / 5 / 10 / 20 / 40 |
|---|---|---|
| Gemma-3-4B-it | .514 / .622 / .650 / .667 / .677 | .519 / .614 / .645 / .674 / .700 |
| Llama-3.2-3B-Instruct | .437 / .730 / .817 / .876 / .927 | .454 / .733 / .812 / .869 / .909 |
| Ministral-8B | .858 / .937 / .950 / .956 / .957 | .856 / .945 / .963 / .975 / .983 |

Predictions are within 2.6 points of the observed coverage at 40 samples in every model, so a ten-sample fit supports extrapolation to roughly four times as many attempts for these models. The error is systematic: the Beta tail overstates the late-sample coverage (Ministral 0.983 predicted vs. 0.957 observed; Gemma 0.700 vs. 0.677), because a small share of bugs is never solved, a feature the zero-inflated fit recovers for Ministral (0.958).

**Out-of-sample policy (P3).** Fitting on half the bugs and evaluating on the other half (cost in units of *c*, human-only equals H/c; caps up to 40):

| Model | H/c | Fixed k = 1 | k = 5 | k = 10 | Reservation rule (BB) | Best fixed in hindsight |
|---|---|---|---|---|---|---|
| Gemma | 10 | 5.74 | 6.34 | 7.79 | **5.74** (N=1) | 5.73 (k=2) |
| Gemma | 30 | 15.21 | 13.68 | 14.49 | 13.83 (N=3) | 13.68 (k=5) |
| Gemma | 100 | 48.38 | 39.35 | 37.97 | **37.97** (N=10) | 37.97 (k=10) |
| Llama | 10 | 6.65 | 5.68 | 6.15 | **5.68** (N=5) | 5.68 (k=4) |
| Llama | 30 | 17.95 | 11.62 | 10.45 | 10.31 (N=17) | 10.30 (k=15) |
| Llama | 100 | 57.50 | 32.40 | 25.50 | **16.36** (N=40) | 16.36 (k=40) |
| Ministral | 10 | 2.43 | 2.34 | 2.73 | 2.65 (N=9) | 2.23 (k=3) |
| Ministral | 30 | 5.29 | 4.13 | 4.43 | 5.76 (N=27) | 4.12 (k=4) |
| Ministral | 100 | 15.29 | 10.42 | 10.37 | 12.60 (N=40) | 10.31 (k=7) |

For Gemma and Llama the fitted rule is within about 1% of the hindsight-optimal cap in every case (for Llama at H/c = 100, the cap of 40 is binding and the model-implied N\* is about 50, beyond the range the data can evaluate). A cap of ten cuts Llama's cost by 74% relative to human-only repair at H/c = 100, but the fitted rule cuts it by 84%.

**Where the rule fails.** For Ministral, which solves 96% of bugs and leaves only a small residue of hard ones, the fitted rule samples far too long (N = 9–40 against a hindsight best of 3–7) and costs 19–40% more than the best cap at H/c ≤ 30 (12.60 vs. 10.31, i.e., 22% more at H/c = 100). Two causes are visible. First, the Beta fit assigns positive success probability to bugs that are in fact never solved, which delays stopping. Second, with only 82 training bugs and a handful of never-solved ones, the zero-inflated fit estimated on the training half does not recover the unsolvable mass (the full-sample fit gives π = 0.04 and N\* = 4, 8, 16 at H/c = 10, 30, 100, much closer to the hindsight values 3, 4, 7 though still high). The practical implication is that the reservation rule needs enough history to identify the unsolvable share, and that a firm using it should audit the fitted threshold against a held-out cap sweep, which cost under one dollar per hundred bugs at the small-model prices used here. Even with the failure, the rule saves 87% relative to human-only repair at H/c = 100.



---

## 7. Extensions

1. **Imperfect verification.** If a patch that passes the firm's tests is wrong with probability *e* and a wrong patch causes downstream cost *L*, the benefit of success is H − eL in place of *H* in (4) and (5). A weaker test suite thus shortens the justified search; in contract B, disputes over what counts as a verified fix become a cost to both sides.
2. **Human–AI complementarity.** If failed attempts reduce the human cost (logs, localization), *H* falls with *n*, lowering the threshold.
3. **Latency and waiting costs.** Waiting costs add to *v* and lower the threshold for urgent defects, which suggests tiered escalation rules by severity.
4. **Heterogeneous defect classes.** Observable defect types with their own (a\_s, b\_s) imply type-specific thresholds. For the same fit, type-contingent thresholds lower expected cost relative to the best common cap (6.2% in the synthetic three-type example of `paper/sim_types.py`).
5. **Vendor quality uncertainty and signaling.** If the vendor knows its own *a* and the firm does not, a success fee may serve as a credible signal of quality, since only a high-*a* vendor profits at a given fee. We have not analyzed the resulting signaling game and leave it for future work; Section 5.4 provides only a first measure of the firm's exposure.
6. **Competition.** With multiple vendors, the vendor's markup in Propositions 2 and 4 shrinks; the extent to which competition restores efficiency depends on whether vendors differ in (a, b) and in *k*.
7. **Budget constraints and portfolios.** A firm-wide budget on attempts adds a shadow price to *c* in (4), generating a cross-team allocation rule.

---

## 8. Discussion

**Theoretical implications.** The paper makes three points that are separable from the particular numbers. First, the economically relevant unit in AI-assisted maintenance is the *decision to continue after a failure*, not the pass@k capability, and this decision has a simple reservation form once difficulty is heterogeneous. Second, vertical contracting theory carries over to AI services: a per-attempt fee above marginal cost makes the buyer stop too soon, and the distortion can be large when difficulty is strongly U-shaped, because the vendor can price the first attempt as a near-take-it-or-leave-it offer. Third, outcome-based pricing improves total surplus because it changes what the buyer perceives as the price of continuing, but it does not by itself make the buyer better off, which depends on the split.

**Managerial implications.**
- *Buyers* should (i) estimate (a, b) from their own repair logs, (ii) compute their threshold from H and from their own cost per attempt (including verification), and (iii) treat a success fee near the human repair cost as expensive even though it removes the risk of paying for failures; negotiate a fee closer to Hk/(k+v) in exchange for volume.
- *Vendors* gain from offering success-based pricing in most of our parameter range and should recognize that the optimal fee is above the efficient one; competing on the fee alone leaves surplus unrealized.
- *Platform and governance designers* should publish per-sample outcomes and per-attempt costs, since the inputs the contracts depend on (a, b, c) are currently invisible in public leaderboards.

**Limitations.**
1. *No field data.* H, k, and v are illustrative. The empirical sections use public benchmarks, not firm records, and benchmark bugs (single functions with complete tests) are easier to verify than industrial defects.
2. *Independence of attempts.* Conditional independence given *p* is an approximation; samples from the same prompt and model are positively correlated, which would make failure even more informative and lower the threshold.
3. *Monopoly vendor and complete information about (a, b).* Competition and asymmetric information (Section 7) are not analyzed.
4. *Static game.* We do not model repeated interaction, learning of (a, b) over time, or reputation.
5. *Single dimension of quality.* Patch quality is binary (passes tests or not); maintainability and security of accepted patches are not modeled.
6. *Threshold estimation error.* In the 40-sample experiment, the fitted threshold was 19–40% costlier than the best cap for one model whose residual of unsolved bugs was small (Section 6.4); the rule is only as good as the estimate of the tail.
7. *Training-data leakage.* Public benchmarks may overlap with model training data, which inflates success rates; the lower success on the recent GitBug-Java set is consistent with this.

**Field validation plan.** Appendix D lists the data a partner firm would need to provide (per-attempt outcomes, token/compute cost, verification time, escalation outcomes and human repair hours, and contract terms), and a randomized-cap experiment that would estimate realized savings and test Propositions 1–3 directly.

---

## 9. Conclusion

An AI repair service creates two linked decisions: how long the buyer lets the AI try, and how the vendor charges for trying. When defects differ in difficulty, the buyer's optimal rule is a reservation threshold that rises with the cost of human repair and falls with the price and difficulty. Charging per attempt above cost makes the buyer give up too early, and a vendor with market power can push the buyer to one attempt and leave it almost no surplus. A success fee fixes the buyer's incentive to continue and raises total surplus in our calibrations, but it leaves the question of who captures the gain, which suggests that the structure of the contract matters as much as its price. Public benchmark data support the premises: difficulty is strongly heterogeneous, failures are informative, and a threshold fitted to past defects usually performs almost as well as the best cap in hindsight, though it can oversample when the share of unsolvable defects is small and poorly identified. The next step is to test the contract predictions on a firm's repair and billing records.

---

## References

*(Verify details against the originals before submission.)*

- Agrawal, A., Gans, J., and Goldfarb, A. (2018). *Prediction Machines: The Simple Economics of Artificial Intelligence.* Harvard Business Review Press.
- Bajari, P., and Tadelis, S. (2001). Incentives versus transaction costs: A theory of procurement contracts. *RAND Journal of Economics*, 32(3), 387–407.
- Banker, R. D., and Slaughter, S. A. (2000). The moderating effects of structure on volatility and complexity in software enhancement. *Information Systems Research*, 11(3), 219–240.
- Brown, B., et al. (2024). Large language monkeys: Scaling inference compute with repeated sampling. arXiv:2407.21787.
- Brynjolfsson, E., Li, D., and Raymond, L. (2023). Generative AI at work. NBER Working Paper 31161.
- Chen, M., et al. (2021). Evaluating large language models trained on code. arXiv:2107.03374.
- Chow, Y. S., Robbins, H., and Siegmund, D. (1971). *Great Expectations: The Theory of Optimal Stopping.* Houghton Mifflin.
- Fügener, A., Grahl, J., Gupta, A., and Ketter, W. (2022). Cognitive challenges in human–artificial intelligence collaboration: Investigating the path toward productive delegation. *Information Systems Research*, 33(2), 678–696.
- Gopal, A., Sivaramakrishnan, K., Krishnan, M. S., and Mukhopadhyay, T. (2003). Contracts in offshore software development: An empirical analysis. *Management Science*, 49(12), 1671–1683.
- Jimenez, C. E., et al. (2024). SWE-bench: Can language models resolve real-world GitHub issues? *ICLR 2024.*
- Kemerer, C. F., and Slaughter, S. (1999). An empirical approach to studying software evolution. *IEEE Transactions on Software Engineering*, 25(4), 493–509.
- Le Goues, C., Nguyen, T., Forrest, S., and Weimer, W. (2012). GenProg: A generic method for automatic software repair. *IEEE Transactions on Software Engineering*, 38(1), 54–72.
- Lientz, B. P., and Swanson, E. B. (1980). *Software Maintenance Management.* Addison-Wesley.
- McCall, J. J. (1970). Economics of information and job search. *Quarterly Journal of Economics*, 84(1), 113–126.
- Raisch, S., and Krakowski, S. (2021). Artificial intelligence and management: The automation–augmentation paradox. *Academy of Management Review*, 46(1), 192–210.
- Silva, A., and Monperrus, M. (2025). RepairBench: Leaderboard of frontier models for program repair. *LLM4Code Workshop (ICSE 2025).* arXiv:2409.18952.
- Spengler, J. J. (1950). Vertical integration and antitrust policy. *Journal of Political Economy*, 58(4), 347–352.
- Stigler, G. J. (1961). The economics of information. *Journal of Political Economy*, 69(3), 213–225.
- Tirole, J. (1988). *The Theory of Industrial Organization.* MIT Press.
- Weitzman, M. L. (1979). Optimal search for the best alternative. *Econometrica*, 47(3), 641–654.
- Whang, S. (1992). Contracting for software development. *Management Science*, 38(3), 307–324.
- Xia, C. S., and Zhang, L. (2023). Automated program repair in the era of large pre-trained language models. *ICSE 2023.*

---

## Appendix A. Survival Function and Posterior Predictive

Given *p*, P(T > j | p) = (1−p)^j. Integrating over p ~ Beta(a, b): S(j) = B(a, b+j)/B(a, b). After *n* failures the posterior is Beta(a, b+n), with mean a/(a+b+n) = q\_n; equivalently q\_n = P(T = n+1 | T > n) = a/(a+b+n).

## Appendix B. Estimation

With counts (n samples, *k* successes) per defect, the Beta-binomial likelihood is C(n,k)·B(k+a, n−k+b)/B(a,b); with first-success data censored at *K* attempts, the contribution of a solved defect is B(a+1, b+t−1)/B(a,b) and of an unsolved one B(a, b+K)/B(a,b). Both are maximized over (log a, log b) by Nelder–Mead (`paper/empirical/analyze.py`, `paper/sim.py`).

## Appendix C. Reproducibility

- Contracts: `cd paper/contracts && python3 contracts.py && python3 robustness.py`.
- RepairBench: `cd paper/empirical && python3 load_repairbench.py <repairbench>/results && python3 analyze.py`.
- SWE-bench: `cd paper/empirical && python3 swebench_repo_level.py <experiments>/evaluation`.
- HumanEvalFix: `cd paper/empirical/sampling && python3 sample_humanevalfix.py <model> 40 && python3 analyze_hef.py`.
- Synthetic stopping illustration (v1 of this paper): `python3 paper/sim.py`, `python3 paper/sim_types.py`.

## Appendix D. Field-Data Request and Experimental Design (Not Yet Executed)

**Variables per defect (partner firm):** defect identifier and type; timestamps of arrival, each AI attempt, verification, escalation, and closure; for each AI attempt, outcome of the firm's tests, token counts, compute cost billed by the vendor, and verifier effort; whether and how the defect was escalated; engineering hours and fully loaded cost of human repair; post-merge defects traced to AI patches (to measure *e*); contract terms (per-attempt fee, success fee, minimums).

**Design:** randomize the attempt cap *N* across defects within strata (type, severity) over at least a quarter; estimate (a, b) by stratum from the first part of the sample, compare realized cost per resolved defect under the reservation rule and under the firm's existing cap; if the vendor offers both contract types, randomize contract by team to estimate the effect of the pricing structure on attempt behavior (Propositions 1–3).

**Ethics and confidentiality:** the firm's code and defect text are not required; attempt-level outcomes and costs suffice.
