---
journal: Information Systems Research (INFORMS) — manuscript format
status: Draft v1 — simulation-based; no empirical data yet
---

# When to Stop Asking the Machine: An Optimal-Stopping Theory of Budget Allocation in LLM-Based Automated Program Repair

**Authors:** [Author names, affiliations] · **Corresponding author:** [email]

**Keywords:** automated program repair; large language models; optimal stopping; search theory; real options; software maintenance; IT cost management; Bayesian learning

---

## Abstract

Large language models (LLMs) can repair software defects by sampling candidate patches, but each sample consumes compute, verification effort, and time, and success probabilities vary widely across defects. Practitioners set the number of attempts by convention (e.g., pass@k with k = 5 or 10) rather than by economic reasoning. We model LLM-based repair as a sequential search problem in the tradition of McCall (1970) and Weitzman (1979). A maintainer faces a defect whose per-attempt success probability is unknown and heterogeneous across defects (Beta-distributed). Each attempt costs *c*; if the LLM fails to produce a verified patch, the defect is escalated to a human engineer at cost *H*, which plays the role of the outside option. Because failed attempts are informative, the posterior expected success probability declines with the number of failures. We show that (i) the optimal policy is a reservation rule with closed-form threshold N\* = ⌈aH/c − a − b⌉; (ii) the one-step-look-ahead rule is globally optimal; (iii) the threshold is increasing in the human cost and decreasing in the attempt cost, and heterogeneity (low a, high b) lowers it; (iv) ignoring heterogeneity (a homogeneous-success-probability model) implies "never stop," an error that is costly; and (v) conditioning the threshold on observable defect types yields further savings. In a synthetic calibration, optimal stopping reduces the expected repair cost by 47.4% relative to human-only repair and by 13.8% relative to a conventional k = 10 cap, and a prior estimated from only 200 historical defects attains within 0.3% of the oracle cost. We discuss implications for IT governance, pricing of LLM repair services, and the design of agentic maintenance pipelines.

---

## 1. Introduction

Software maintenance consumes the majority of the lifecycle cost of information systems, and corrective maintenance (bug fixing) is its most visible component. Recent LLM-based repair tools generate candidate patches that are validated against test suites (Le Goues et al. 2012; Xia and Zhang 2023; Jimenez et al. 2024). Because LLM outputs are stochastic, organizations routinely draw multiple samples and accept the first one that passes validation. The evaluation literature summarizes this with pass@k (Chen et al. 2021), which describes *capability* but not *how many samples a firm should pay for*.

This is an economic decision. Each additional sample has a marginal cost (inference fees, test execution, queueing delay) and a marginal expected benefit (the probability of success times the human effort avoided). Two features make the problem non-trivial. First, defects are **heterogeneous**: some are fixed on almost every attempt, others essentially never. Second, because of this heterogeneity, **failures are informative**: after many failed attempts the defect is more likely to belong to the "hard" population, so the marginal value of another attempt falls even though the attempts are independent given the defect's difficulty. Fixed-k policies ignore this learning; homogeneous-probability models, which are common in capacity-planning calculations, miss it entirely.

**Research questions.**
RQ1. What is the optimal stopping rule for LLM repair attempts when the success probability is heterogeneous and unknown?
RQ2. How do the human-escalation cost, attempt cost, and defect heterogeneity shape the optimal budget?
RQ3. What is the economic loss from the practitioner heuristics (fixed k; homogeneous-probability planning)?
RQ4. How much historical data does a firm need to implement the rule, and how much do observable defect types add?

**Contributions.** (1) We formalize LLM repair budgeting as a sequential search problem with an outside option, importing search theory into the software-maintenance literature. (2) We derive a closed-form reservation threshold and comparative statics. (3) We show that the "obvious" homogeneous model prescribes never stopping and quantify the loss. (4) We give an estimation procedure (Beta-geometric maximum likelihood with right censoring) and show its data requirements. (5) We provide managerial guidance for IT governance.

---

## 2. Theoretical Background and Related Literature

**Sequential search and optimal stopping.** The economics of information (Stigler 1961) treats search as continuing until the expected marginal gain equals the marginal cost. McCall (1970) formalized job search with a reservation wage; Weitzman (1979) characterized optimal search among alternatives with reservation values; Wald (1945) laid out sequential analysis. Our setting differs in that the searched-for object (a passing patch) has a success probability that is learned from failures, which gives a Bayesian, declining hazard.

**Real options.** Dixit and Pindyck (1994) show that the option to continue or abandon a project has value that depends on the outside option and on information revealed over time. Escalation to a human engineer is the abandonment/outside option; each LLM attempt is a small, information-revealing investment.

**Automated program repair (APR).** Generate-and-validate repair (Le Goues et al. 2012) and LLM-based repair (Xia and Zhang 2023) report success rates and sometimes cost per fix, but budget allocation is typically fixed ex ante. Benchmarks such as SWE-bench (Jimenez et al. 2024) report resolved rates under fixed protocols. We complement this literature with a normative cost model.

**IT cost management in maintenance.** Treating AI-assisted maintenance as a production decision under uncertainty links to the IS literature on IT investment and governance; our contribution is a micro-level decision rule that can be embedded in such governance.

**Gap.** To our knowledge, existing work does not derive an economically optimal attempt budget under defect heterogeneity with an escalation outside option.

---

## 3. Model

**Environment.** A defect arrives and is handled by an LLM repair agent. Attempts are indexed *n* = 1, 2, …. Each attempt independently yields a validated patch with probability *p*, the defect-specific success probability. Each attempt costs *c* > 0 (inference, test execution, delay). The maintainer observes the outcome of each attempt (validated patch or failure) but not *p*.

**Heterogeneity (prior).** *p* ~ Beta(*a*, *b*) across defects, with *a*, *b* > 0. Small *a* with large *b* describes a portfolio dominated by hard defects. The mean is *a*/(*a*+*b*).

**Outside option.** If the maintainer stops without a validated patch, the defect is escalated to a human engineer at cost *H* > 0 (fully loaded, including context-transfer). Without loss of generality the human fix delivers the same value as a validated LLM patch, so the problem is cost minimization. (Section 6 relaxes this.)

**Payoff.** Total cost = *c*·(attempts made) + *H*·1{no validated patch}. The maintainer chooses a stopping time τ adapted to the history of outcomes to minimize expected cost.

**Learning.** After *n* consecutive failures, the posterior is Beta(*a*, *b*+*n*), and the posterior predictive probability that attempt *n*+1 succeeds is

q\_n = a / (a + b + n).  (1)

---

## 4. Analysis

**Proposition 1 (Declining marginal success).** q\_n is strictly decreasing in *n*, and q\_n → 0 as *n* → ∞.

*Proof.* Immediate from (1). ∎

*Interpretation.* Failures are bad news about the defect, in the same way that an applicant's failure to find a job after many interviews signals a poor match. The attempts are conditionally independent given *p* but unconditionally positively dependent through *p*.

**Proposition 2 (Optimal policy).** The optimal policy is a reservation rule: attempt *n*+1 is made if and only if q\_n·H > c. Equivalently, the maximum number of attempts is

N\* = max{ 0, ⌈ aH/c − a − b ⌉ }.  (2)

*Proof.* The state after *n* failures is fully summarized by *n* (a sufficient statistic since outcomes are exchangeable Bernoulli given *p*). In state *n*, continuing for exactly one more attempt and then stopping costs c + (1 − q\_n)H, whereas stopping now costs H; the difference is c − q\_n H. Since q\_n is decreasing (Prop. 1), once c − q\_n H ≥ 0 it holds for all larger *n*, so the stopping problem is monotone. For monotone problems, the one-step look-ahead rule is optimal (Chow, Robbins, and Siegmund 1971): if stopping is preferred to one more attempt-then-stop, it is preferred to any longer continuation, because the benefit of any further attempt is bounded by the benefit of the first, which has already fallen below its cost. Solving q\_n H > c for *n* gives n < aH/c − a − b, hence attempts are made for n = 0, 1, …, ⌈aH/c − a − b⌉ − 1, i.e., N\* attempts. ∎

**Proposition 3 (Comparative statics).**
(a) ∂N\*/∂H > 0 and ∂N\*/∂c < 0: a higher human cost or cheaper attempts justify more attempts. The relationship with H is approximately linear: N\* ≈ aH/c.
(b) ∂N\*/∂b < 0: a harder portfolio (more mass near zero success) justifies fewer attempts.
(c) ∂N\*/∂a > 0 when H/c > 1: a more favorable portfolio justifies more attempts. In the empirically relevant region H ≫ c.

*Proof.* Differentiate the argument of the ceiling in (2): aH/c − a − b has derivative a/c > 0 in H, −aH/c² < 0 in c, −1 < 0 in b, and (H/c − 1) > 0 in a when H > c. ∎

**Proposition 4 (Cost of the homogeneous model).** Suppose the maintainer ignores heterogeneity and plans with a constant success probability p̄ (e.g., the pooled success rate). Then if p̄H > c, the rule "attempt iff p̄H > c" never stops; if p̄H ≤ c, it never starts. Under heterogeneity, neither is optimal, and the "never stop" policy has expected cost strictly higher than the optimal one whenever N\* is finite.

*Proof.* With constant p̄, the marginal value of an attempt does not change with *n*, so the rule is time-invariant. By Proposition 2 the optimal policy under heterogeneity stops at finite N\*, and for every k ≥ N\*, the marginal cost of attempt k+1, c·S(k), exceeds its marginal benefit q\_k·H·S(k) (because q\_k·H ≤ c), so any larger cap has weakly higher expected cost, strictly so for k > N\*. ∎

**Expected cost under a cap *k*.** For any cap *k*,

E[cost(k)] = c·Σ\_{j=0}^{k−1} S(j) + H·S(k), where S(j) = P(T > j) = B(a, b+j) / B(a, b),  (3)

with *B* the beta function and *T* the number of attempts until the first success. Equation (3) is used for exact numerical evaluation in Section 5.

**Proposition 5 (Value of observable types).** Suppose defects carry an observable type *s* (e.g., issue category, affected module, stack-trace class) with type-specific parameters (a\_s, b\_s). The optimal policy sets N\*\_s using (2) for each type, and its expected cost is no greater than that of the best common cap, with strict inequality whenever the types induce different N\*\_s (and the common cap is not optimal for some type).

*Proof.* The common cap is a feasible policy in the type-contingent problem; Proposition 2 applied type by type yields the optimum. Strictness follows from uniqueness of each type's optimum. ∎

---

## 5. Numerical Study (Synthetic Calibration)

> **Note.** All parameter values below are *synthetic* and chosen to illustrate the mechanism. They are **not** estimated from real repair logs. Section 7 describes the empirical validation required before the magnitudes are used for decisions. Code: `paper/sim.py`, `paper/sim_types.py`; raw output: `paper/results.txt`.

**Setup.** Baseline: *a* = 0.4, *b* = 3.0 (mean success probability 0.118, strongly right-skewed), *H* = 100, *c* = 1 (cost units normalized to one LLM attempt). Monte Carlo with 400,000 simulated defects; exact expected costs from (3).

### 5.1 Optimal budget and benchmarks

| Policy | Expected cost per defect | vs. human-only |
|---|---|---|
| Human only (k = 0) | 100.00 | — |
| Fixed k = 1 | 89.26 | −10.7% |
| Fixed k = 3 | 77.01 | −23.0% |
| Fixed k = 5 | 70.08 | −29.9% |
| Fixed k = 10 | 61.06 | −38.9% |
| Fixed k = 20 | 54.64 | −45.4% |
| Fixed k = 40 | 52.56 | −47.4% |
| Fixed k = 80 | 56.43 | −43.6% |
| Fixed k = 160 | 68.09 | −31.9% |
| **Optimal stopping, N\* = 37** | **52.54** (exact: 52.63) | **−47.4%** |
| Homogeneous-p policy (never stops; capped at 300) | 87.65 | −12.4% |

*Findings.* (1) Equation (2) gives N\* = ⌈0.4·100/1 − 0.4 − 3.0⌉ = 37. Exact evaluation of (3) confirms that the global minimizer is *k* = 37 (cost 52.634 vs. 52.639 at *k* = 36; Monte Carlo noise made 36 appear best in simulation, which illustrates the flatness of the cost near the optimum). (2) The cost curve is U-shaped and asymmetric: stopping too early (k = 10) costs 16% more than optimal, while stopping too late (k = 160) costs 29% more. (3) The homogeneous-p policy "never stops," because p̄H = 0.118·100 > c; it performs only 12.4% better than human-only, because it spends most of the budget on the hard tail. (4) The LLM resolves 65.8% of defects under the optimal budget.

### 5.2 Comparative statics (N\* as H varies; *a* = 0.4, *b* = 3, *c* = 1)

| H | 10 | 50 | 100 | 200 | 500 |
|---|---|---|---|---|---|
| N\* | 1 | 17 | 37 | 77 | 197 |

N\* grows approximately linearly in H/c, as Proposition 3 predicts. Organizations with expensive engineering labor (large H) or cheap inference (small c) should allow much deeper LLM search; those with a cheap human option should escalate quickly.

### 5.3 Estimation from historical data

A firm does not know (a, b). We simulate a firm that observes *N* historical defects, each attempted up to 30 times (right-censored), estimates (a, b) by Beta-geometric maximum likelihood with censoring, and applies (2). Results over 100 replications:

| Training defects *N* | Mean cost (±SD) | Gap to oracle (52.63) |
|---|---|---|
| 50 | 53.42 ± 1.69 | +1.5% |
| 200 | 52.56 ± 0.22 | ≈ 0 |
| 1,000 | 52.41 ± 0.05 | ≈ 0 |

(Averages are over a fixed 50,000-defect evaluation set, so small deviations from the exact oracle cost reflect sampling noise in that set rather than gains over the oracle.) A few hundred historical attempts suffice; the loss is flat near the optimum, so estimation error has second-order cost.

### 5.4 Value of defect types

Three synthetic types: easy (a = 0.6, b = 2.0; 40%), medium (a = 0.3, b = 3.0; 40%), hard (a = 0.05, b = 4.0; 20%).

| Policy | Expected cost |
|---|---|
| Type-specific N\*\_s (easy 58, medium 27, hard 1) | 56.81 |
| Best common cap (k = 23) | 60.54 |
| Common cap k = 10 | 63.96 |
| Human only | 100.00 |

Type-contingent stopping reduces cost by 6.2% relative to the best common cap and by 11.2% relative to k = 10. The hard type is optimally escalated almost immediately (N\* = 1), which is economically equivalent to **triage**.

---

## 6. Extensions

1. **Value of delay.** Add a waiting cost *w* per attempt (queueing, developer blocked): replace *c* with *c* + *w* in (2). Time-critical defects (production incidents) therefore have a lower N\*.
2. **Imperfect verification.** If a passing patch is wrong with probability *e* (test overfitting), then successful attempts incur an expected downstream cost *e*·*L* (rework, incidents). The net benefit of success becomes *H* − *eL*, and N\* uses *H′* = *H* − *eL* in (2). Weak test suites thus shorten the economically justified search.
3. **Human-LLM complementarity.** If failed LLM attempts reduce the human cost (diagnosis logs, localization), *H* becomes *H*(n), decreasing in *n*; the reservation rule becomes q\_n·H(n) > c + (H(n) − H(n+1))(1 − q\_n), which lowers N\*.
4. **Risk aversion and budget constraints.** With a firm-level budget *B̄* across many defects, the problem becomes a knapsack/Lagrangian one: the multiplier λ acts as an effective attempt cost c + λ. Shadow prices then guide cross-team allocation.
5. **Learning across defects.** Updating (a, b) online yields an empirical-Bayes policy; Section 5.3 indicates fast convergence.
6. **Strategic pricing.** If an LLM vendor charges per attempt, the firm's demand for attempts is derived from (2): a price increase from c to c′ lowers the optimal budget by approximately aH(1/c − 1/c′); demand for attempts is therefore approximately unit-elastic in c. Vendors can use success-based pricing to shift risk.

---

## 7. Discussion

**Theoretical implications.** The framework imports the logic of search theory into software maintenance and shows that learning from failure, not only the cost parameters, determines the budget. The result that a homogeneous model prescribes "never stop" is a cautionary example of how ignoring unobserved heterogeneity produces qualitatively wrong policies, not just quantitatively inaccurate ones.

**Managerial implications.**
- **Replace conventional caps with a reservation rule.** Set the cap near aH/c, using in-house estimates of (a, b), and revisit it when LLM pricing or engineer cost changes.
- **Treat escalation as a designed outside option.** The cost H, including context-transfer friction, directly determines the economically justified automation depth.
- **Triage by type.** Differentiated budgets earned a further 6% in our calibration.
- **Monitor the cost curve, not the success rate.** Because the cost curve is flat near its minimum but steep in the tails, being roughly right matters more than being exactly right.

**Limitations.**
1. All numerical results are synthetic; magnitudes will differ with real data.
2. We assume conditional independence of attempts given *p*. Real samples from the same model and prompt are positively correlated (mode collapse), and sampling temperature or prompt changes may restore diversity. This effectively makes *p* decay faster than the Beta model implies, which would favor *lower* N\*. A prompt-diversification extension can be modeled by a decaying within-defect success probability.
3. We treat *a*, *b* as fixed; model upgrades shift the prior.
4. The human outside option is treated as deterministic.
5. Patch correctness is measured by tests; semantic correctness is not guaranteed.

**Empirical validation plan (future work).** (i) Collect attempt-level logs from repair benchmarks (e.g., Defects4J, SWE-bench subsets) and from an industrial partner, recording the outcome of each sample, token cost, and test time; (ii) fit the Beta-geometric model and compare with alternative mixtures (e.g., finite mixture of point masses, zero-inflated); (iii) perform out-of-sample evaluation of the reservation rule against fixed caps using time-based splits to avoid training-data leakage; (iv) conduct a field experiment randomizing the cap across issues to estimate realized savings.

---

## 8. Conclusion

We show that the question "how many patches should we sample?" has a clean economic answer: continue while the posterior-expected avoided human cost of one more attempt exceeds its cost, which yields a closed-form threshold N\* = ⌈aH/c − a − b⌉. The threshold rises with human cost, falls with attempt cost and defect difficulty, and cannot be recovered from a homogeneous success-rate model. In a synthetic calibration, the rule halves the cost of repair relative to human-only handling and beats a conventional k = 10 cap by about 14%, while requiring only a few hundred historical defects to implement. We hope the framework helps move AI-assisted maintenance from capability metrics (pass@k) toward decision-grade economic metrics.

---

## References

*(Verify details against the originals before submission.)*

- Chen, M., et al. (2021). Evaluating large language models trained on code. arXiv:2107.03374.
- Chow, Y. S., Robbins, H., and Siegmund, D. (1971). *Great Expectations: The Theory of Optimal Stopping.* Houghton Mifflin.
- Dixit, A. K., and Pindyck, R. S. (1994). *Investment under Uncertainty.* Princeton University Press.
- Jimenez, C. E., et al. (2024). SWE-bench: Can language models resolve real-world GitHub issues? *ICLR 2024.*
- Le Goues, C., Nguyen, T., Forrest, S., and Weimer, W. (2012). GenProg: A generic method for automatic software repair. *IEEE Transactions on Software Engineering*, 38(1), 54–72.
- McCall, J. J. (1970). Economics of information and job search. *Quarterly Journal of Economics*, 84(1), 113–126.
- Stigler, G. J. (1961). The economics of information. *Journal of Political Economy*, 69(3), 213–225.
- Wald, A. (1945). Sequential tests of statistical hypotheses. *Annals of Mathematical Statistics*, 16(2), 117–186.
- Weitzman, M. L. (1979). Optimal search for the best alternative. *Econometrica*, 47(3), 641–654.
- Xia, C. S., and Zhang, L. (2023). Automated program repair in the era of large pre-trained language models. *ICSE 2023.*

---

## Appendix A. Derivation of the Survival Function and Posterior Predictive

Given *p*, the number of attempts to first success is geometric: P(T > j | p) = (1 − p)^j. Integrating over p ~ Beta(a, b):

P(T > j) = ∫ (1−p)^j · p^{a−1}(1−p)^{b−1} / B(a,b) dp = B(a, b+j) / B(a, b).

The posterior after *n* failures is proportional to p^{a−1}(1−p)^{b+n−1}, i.e., Beta(a, b+n), with mean a/(a+b+n) = q\_n. Equivalently, q\_n = P(T = n+1 | T > n) = [B(a+1, b+n)/B(a,b)] / [B(a, b+n)/B(a,b)] = a/(a+b+n).

## Appendix B. Estimation with Right Censoring

For defects solved at attempt *t\_i* ≤ *K*: log-likelihood contribution log B(a+1, b+t\_i−1) − log B(a, b). For defects unsolved after *K* attempts: log B(a, b+K) − log B(a, b). Maximize over (log a, log b) using Nelder–Mead (implemented in `sim.py`).

## Appendix C. Reproducibility

`python3 paper/sim.py` reproduces Tables 5.1–5.3 (seed 42); `python3 paper/sim_types.py` reproduces Table 5.4.
