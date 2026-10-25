---
journal: Information Systems Research (INFORMS) — manuscript
status: Draft v5 — prose revised; analytical model with costs calibrated from public wage, price and annotation data; no field data (Appendix D). Behavioral extensions and the experiment design are in paper_ISR_long.md and are not part of this manuscript.
---

# Who Pays for the Next Attempt? Contract Design and Escalation Rules for AI-Assisted Software Maintenance

**Authors:** [Author names, affiliations] · **Corresponding author:** [email]

**Keywords:** AI–human task allocation; escalation; outcome-based pricing; IT service contracts; software maintenance; large language models; double marginalization; optimal stopping

---

## Abstract

Firms increasingly buy AI-based defect repair as a pay-per-use service. A large language model proposes patches, the firm verifies them, and defects that the model cannot fix are escalated to human engineers. We study how the vendor's pricing rule, per attempt or per verified fix, interacts with the firm's escalation rule when defects differ in how easily they are repaired and every failure therefore carries information about the next attempt. The firm's optimal rule is a reservation threshold that holds for any distribution of repair difficulty and takes the closed form N\* = ⌈aH/c − a − b⌉ when difficulty is Beta-distributed. Per-attempt prices above marginal cost cause the firm to stop too early, a form of double marginalization. A success fee of Hk/(k+v) restores the efficient depth, yet a monopolist sets a higher fee. The reason is an *incentive rent of sequential search*: inducing deep sampling requires leaving the firm a gain on earlier attempts, which amounts to 78–82% of the surplus in our calibrations. Among linear pay-per-use contracts the pure success fee is optimal for the vendor, and a lump-sum fee would remove all distortions. When vendors know their quality privately, only success fees can credibly signal it, and under competition the distortion disappears only if vendors are close substitutes. Open repair data (574 bugs and 45 models in RepairBench, plus a new experiment with 40 samples per bug) show strongly heterogeneous difficulty in all 84 model–dataset combinations, and a threshold fitted to half of the bugs performs within 0.4–1.7% of the best cap in hindsight on the rest. Calibrating costs to public wage statistics, task-time annotations, and price lists shows that the conclusions are strongest when verification is cheap relative to human repair.

---

## 1. Introduction

Software maintenance absorbs most of the lifetime cost of information systems (Lientz and Swanson 1980), and AI repair agents based on large language models are beginning to change how that work is organized. A firm can send a defect first to an AI service, accept any patch that passes its tests, and escalate to an engineer only if the AI fails. Research on AI augmentation has shown that arrangements of this kind succeed or fail on how tasks are allocated and how delegation is designed (Raisch and Krakowski 2021; Fügener et al. 2022). Two questions that arise concretely in this setting have received little attention: how many failed attempts a firm should tolerate before it escalates, and how the vendor's price structure shapes that choice.

Both questions turn on a regularity that is easy to overlook. Repair by a language model is stochastic, so the same defect can be attempted several times, but defects differ greatly in how likely a single attempt is to succeed. Some are fixed almost every time and others almost never. A run of failures is therefore bad news about the defect itself, and the value of one more attempt declines as failures accumulate. A firm that plans with the average success rate will never stop, and a firm that fixes the number of attempts by convention ignores both its own cost of human repair and the price the vendor charges.

The vendor's pricing matters because it determines what an additional attempt costs the firm. When the vendor charges per attempt, for example per call or per token, the firm pays for every attempt, including the many that fail on hard defects. When the vendor charges only for a verified fix, the firm pays for success alone and the vendor absorbs the compute cost of failures. Practitioners debate these two structures, but to our knowledge no analysis links them to the firm's escalation decision, to the vendor's profit, and to total surplus in a single model.

We make four contributions. First, we model the escalation of defects from AI to humans as a sequential search problem with an outside option and embed it in a game between a vendor and a buyer, which connects the literature on AI delegation to the literature on IT contracting. Second, we show that per-attempt pricing above cost causes double marginalization, that a success fee of Hk/(k+v) restores the efficient depth, and that a monopolist nevertheless sets a higher fee and induces too little sampling (Propositions 2–4). Third, we identify the force behind these results, an *incentive rent of sequential search*. For any distribution of repair difficulty, we prove that the vendor's optimal pay-per-use contract is a pure success fee and that a lump-sum fee would remove every distortion (Propositions 5 and 6). Fourth, we show that private information about vendor quality reverses the order of profits across contract forms, so that only a success fee can serve as a credible signal (Proposition 7), and that competition removes the distortion only among close substitutes and not merely among many vendors (Proposition 8). We test the premises of the model on open repair data and report numerical equilibria whose cost parameters are calibrated to public sources.

This is a theory article that applies and extends search theory and vertical-contracting theory to a new information systems phenomenon, pay-per-use AI services, and illustrates the model with open data. We write for two audiences: academics working on the economics of information systems, IT sourcing and governance, and human–AI work design, and practitioners who procure or price AI-assisted software services, such as chief information officers, engineering and procurement managers, and AI vendors.

The paper proceeds as follows. Section 2 reviews the literature and states our theoretical positioning. Section 3 presents the model and a running example. Section 4 derives the firm's escalation rule, the monopoly contracts, the incentive rent, and the effects of private vendor quality and competition. Section 5 reports numerical equilibria and a sensitivity analysis. Section 6 tests the premises of the model on open repair data. Sections 7 to 9 discuss extensions, implications, and limitations.

---

## 2. Related Literature and Theoretical Positioning

*IT contracting and outsourcing.* Information systems research has long studied how clients and vendors contract for software and IT services. Whang (1992) models contracting for software development as a game in which the user knows the value of the system better than the developer, and the developer learns its own costs as work proceeds. Gopal et al. (2003) analyze the choice between fixed-price and time-and-materials contracts in offshore software projects. They find that requirement uncertainty, team size, and resource shortage explain the choice and that the choice affects vendor profit, with the main risk borne by the vendor under fixed price and by the client under time and materials. Chen and Bharadwaj (2009) study contract structures in IT outsourcing through the lenses of transaction cost, agency, and relational exchange theories, and Susarla et al. (2010) examine contract extensiveness, duration, and extendibility as responses to holdup under incomplete contracts. Bajari and Tadelis (2001) offer the counterpart from procurement economics: because renegotiation after the fact is costly, cost-plus contracts are preferred to fixed-price contracts when projects are more complex. Dey et al. (2010) build a contract-theoretic model of software outsourcing in which fixed-price contracts suit simple, short projects, time-and-materials contracts suit complex projects when auditing is effective, and a performance-based quality-level agreement can reach the first-best outcome.

These papers compare contracts that pay for inputs, such as time and materials or cost-plus, with contracts that pay for a deliverable. Per-attempt and per-result pricing of AI services has the same input–output structure, but two features change the analysis. The input is a stochastic attempt whose failure carries information about the next one, and the buyer, not the vendor, decides sequentially how many attempts to purchase. The relevant friction is therefore the buyer's decision to continue, and the quantity we study is an incentive rent in that decision. It differs from the risk allocation and renegotiation costs that the contracting papers emphasize.

*Usage-based and performance-based pricing.* Information systems researchers have also analyzed pricing structures for IT services and online advertising that resemble the contracts we study. Ma and Seidmann (2015) model competition between a software-as-a-service provider that charges per transaction and a traditional off-the-shelf software vendor, and they identify market regimes that range from dominance of one provider to segmented and competitive markets. In online advertising, Asdemir et al. (2012) compare input-based pricing (per impression) with performance-based pricing (per click) in a principal–agent model, and Hu et al. (2016) analyze cost per click and cost per action as incentive contracts and find that publishers and advertisers have conflicting preferences between them. Dellarocas (2012) identifies a form of double marginalization in performance-based advertising and discusses enhancements to pay-per-action mechanisms that aim to restore efficient pricing. Ladas et al. (2022) compare product selling with pay-per-use service as competing business models. Fitoussi and Gurbaxani (2012) show empirically that the performance metrics written into outsourcing contracts shape their incentive content and that strong direct incentives are used less often when less measurable objectives are present. The closest analogy to our results is thus the choice between paying for input and paying for performance. What distinguishes our setting is that the buyer controls the quantity of attempts sequentially while learning from failures, and this produces the incentive rent that drives our results. Our double marginalization differs in kind from that of Dellarocas (2012): it concerns the number of attempts that the buyer chooses to purchase and not the price of a conversion. The conflict of interest that Hu et al. (2016) find between publishers and advertisers has a parallel in our finding that vendors prefer success fees where buyers often would not.

*Agency and incentives.* Agency theory frames the choice of contract in terms of information, outcome uncertainty, incentives, and risk (Eisenhardt 1989). Holmström and Milgrom (1991) show that when pay both allocates risk and rewards effort and the agent performs several tasks, incentives tied to measurable outcomes can pull effort away from dimensions that are not measured. Our success fee pays for an outcome that the buyer can verify with tests. The advantage of paying for results in our model comes with this multitask caveat, which we discuss in Section 8.

*Human–AI collaboration.* Research in information systems and management studies how people work with AI and delegate tasks to it. Raisch and Krakowski (2021) argue that automation and augmentation are interdependent and not alternatives. Fügener et al. (2021) show that working with AI can raise individual accuracy while reducing the diversity of human knowledge available to a group. Fügener et al. (2022) find that human–AI teams outperform the AI alone when the AI delegates work to humans but not when humans delegate work to the AI, and that humans delegate poorly. Ibrahim et al. (2021) show how human judgment can be elicited so that it improves algorithmic prediction. Experimental and field evidence documents productivity effects of AI assistants for programming and writing (Peng et al. 2023; Brynjolfsson et al. 2025), and Yeverechyahu et al. (2024) study how an LLM coding assistant affects open-source activity. This work concerns individual and team performance with AI. We study its organizational counterpart in software repair, namely the escalation boundary at which a firm hands a defect from the AI to a person and the way the vendor's price structure moves that boundary. Because humans delegate imperfectly (Fügener et al. 2022), a rule based on observable quantities, such as a threshold computed from past success rates and costs, is a natural design.

*Pricing of information goods and search.* Pricing structure matters for the profit from information goods. Sundararajan (2004) shows that adding a fixed fee to a nonlinear usage-based scheme can raise profits when transaction costs exist, and Bakos (1997) shows that information systems lower buyers' search costs and thereby sellers' market power. Our lump-sum result (Proposition 6) and the role of differentiation under competition (Proposition 8) are counterparts of these findings in the market for AI services. The sequential structure of our model draws on search theory (Stigler 1961; McCall 1970; Weitzman 1979). The rent we identify is related to the information rents of optimal mechanism design (Myerson 1981), and the distortion we find is related to double marginalization in vertical relations (Spengler 1950; Tirole 1988).

*Software maintenance and automated repair.* Maintenance absorbs a large share of lifecycle effort (Lientz and Swanson 1980), and its cost depends on system structure and volatility (Kemerer and Slaughter 1999; Banker and Slaughter 2000). Repair by language models is evaluated with tests and reported as pass@k (Chen et al. 2021; Le Goues et al. 2012; Xia et al. 2023; Jimenez et al. 2024; Silva and Monperrus 2025), and repeated sampling raises coverage with diminishing returns (Brown et al. 2024). These studies measure capability and not the economic decision of how many attempts to buy. For the wider economics of AI, see Agrawal et al. (2018).

*Theoretical positioning.* We apply and extend three bodies of theory: contract and agency theory, which address what to pay for; search theory, which addresses when to stop; and vertical contracting, which addresses how a seller's price distorts a buyer's quantity. The new theoretical content has three parts. The first is the incentive rent of sequential search, which holds for any distribution of repair difficulty and explains both the optimal pay-per-use contract and the under-supply of sampling. The second is the reversal of the order of profits across contract forms under private vendor quality, which makes outcome-based pricing the only credible signal. The third is the role of differentiation, more than the number of vendors, in competition. The setting is specific to information systems for three reasons: success can be verified cheaply by tests, software meters attempts at near-zero marginal cost, and a vendor's quality is a private property of a model that buyers cannot observe directly.

*Testable implications.* The model yields predictions that can be examined with contract and usage data. First, outcome-based pricing should be more common where vendors are few or differentiated, and per-attempt pricing close to cost should prevail where vendors are close substitutes (Proposition 8). Second, buyers for whom human repair is expensive relative to per-attempt verification should tolerate deeper sampling, and observed escalation thresholds should fall as the price per attempt rises (Proposition 1). Third, vendors with market power should rely on result-based fees and not on per-attempt fees when repair difficulty is heterogeneous (Proposition 5). Fourth, high-quality vendors should be more likely to offer outcome-based terms (Proposition 7). Fifth, where prepayment or access fees are feasible, observed sampling should be closer to the efficient depth (Proposition 6).

---

## 3. Model

A firm faces a stream of defects, and a monopolist vendor offers an AI repair service. The game has three stages. First, the vendor announces a contract. Second, the firm either accepts it or rejects it, in which case a human repairs every defect at cost *H*. Third, for each defect the firm requests attempts one at a time, verifies each patch at its own cost, and either accepts a patch that passes or escalates the defect to a human.

Each defect has a latent per-attempt success probability *p* drawn from a distribution F. Neither party observes *p*. Given *p*, attempts are independent, and both parties observe whether each attempt passes the firm's tests. Let T denote the index of the first successful attempt. Then S(j) = P(T > j) = E[(1−p)^j], and after n consecutive failures the probability that the next attempt succeeds is q\_n = E[p(1−p)^n]/E[(1−p)^n]. For F = Beta(*a*, *b*) these expressions become S(j) = B(a, b+j)/B(a, b) and q\_n = a/(a+b+n), where B denotes the beta function. We write E(N) = Σ\_{j<N} S(j) for the expected number of attempts under a cap of N attempts and P(N) = 1 − S(N) for the probability that the defect is repaired within N attempts.

An attempt costs the vendor *k* in compute and costs the firm *v* in tests, triage, and review. Verification is assumed to be accurate. The vendor can offer one of two contracts. Under a per-attempt contract (A), the firm pays *w* ≥ *k* for every attempt. Under a success-fee contract (B), the firm pays *f* ≤ *H* for each verified fix and nothing for failed attempts. We refer to both as pay-per-use contracts because payments depend only on realized attempts and outcomes. As a joint benchmark, a planner who internalizes both costs faces a cost per attempt of *k* + *v*. Relative to human-only repair, the total surplus from a cap of N attempts is

W(N) = H·P(N) − (k + v)·E(N),

which does not depend on the transfer between the parties. We denote by N^FB the cap that maximizes W.

### 3.1 A running example

We use a single configuration throughout the paper. It is also the base case of the tables below. Repair difficulty has a = 0.12 and b = 0.39, the median fit to RepairBench reported in Section 6. A human repair costs H = $100, an attempt costs the firm v = $1, and an attempt costs the vendor k = $0.20. Under this distribution the first attempt succeeds with probability 23.5% on average, but the distribution is U-shaped: 47% of defects have a per-attempt success probability below 1%, and 22% have one above 50%. Failure is therefore informative. After ten failures the probability that the next attempt succeeds has fallen from 23.5% to 1.1%, because ten failures are strong evidence that the defect belongs to the nearly unsolvable group. Measured in dollars, the first attempt is worth q₀H = $23.5 to the firm, the second $7.9, the third $4.8, and the tenth $1.26, against a social cost per attempt of k + v = $1.20. The eleventh attempt is worth $1.14. The efficient depth is therefore N^FB = 10 (Figure 1a).

![**Figure 1.** The running example (a = 0.12, b = 0.39, H = 100, v = 1, k = 0.2). (a) The marginal value of the next attempt, q\_n H, falls steeply with the number of failures n and crosses the efficient cost k + v after ten attempts. (b) For each depth N, the bar shows the total surplus W(N) split into the most a vendor can keep, R(N), and the incentive rent the firm must keep, G\_min(N) (Section 4.3).](contracts/fig_intuition.png){width=85%}

**Table 1. Running example: surplus and its split by attempt budget N.** Entries are dollars per defect. P(N) is the probability that the AI repairs the defect within N attempts, E(N) the expected number of attempts, W(N) the surplus relative to human-only repair, G\_min(N) the rent the firm must keep to be willing to go N attempts deep, and R(N) = W(N) − G\_min(N) the most the vendor can keep (Section 4.3).

| N | P(N) | E(N) | W(N) | G\_min(N) | R(N) |
|---|---|---|---|---|---|
| 1 | 0.235 | 1.00 | 22.33 | 0.00 | 22.33 |
| 2 | 0.296 | 1.76 | 27.49 | 1.96 | 25.53 |
| 3 | 0.330 | 2.47 | 30.01 | 4.43 | 25.58 |
| 5 | 0.370 | 3.79 | 32.44 | 10.11 | 22.33 |
| 10 | 0.420 | 6.82 | 33.86 | 26.50 | 7.36 |

Deeper sampling raises the surplus from $22.3 to $33.9 per defect, but the share that a vendor can keep falls from all of it at N = 1 to 22% at N = 10. The vendor's maximum, $25.6, is reached at N = 3. These numbers anticipate the equilibria discussed in Sections 4 and 5.

---

## 4. Results

### 4.1 The firm's escalation rule

**Proposition 1 (Reservation rule).** For every non-degenerate F, q\_n is strictly decreasing in n. Under contract A the firm makes attempt n+1 if and only if q\_n·H > w + v, and under contract B if and only if q\_n·(H − f) > v. For F = Beta(a, b) the budgets are
N\_A(w) = max{0, ⌈aH/(w+v) − a − b⌉} and N\_B(f) = max{0, ⌈a(H−f)/v − a − b⌉},
and the efficient budget is N^FB = max{0, ⌈aH/(k+v) − a − b⌉}.

*Proof.* Let E\_n denote expectation under the tilted law proportional to (1−p)^n dF, so that q\_n = E\_n[p] and q\_{n+1} = (E\_n p − E\_n p²)/(1 − E\_n p). By Jensen's inequality this is at most E\_n p = q\_n, with strict inequality unless p is degenerate under that law. Because q\_n is decreasing, once continuing ceases to be preferable it never becomes preferable again, so the one-step look-ahead rule is optimal (Chow et al. 1971). In state n the firm compares stopping, at cost H, with making one more attempt and then stopping, at cost (w+v) + (1−q\_n)H under A or v + q\_n f + (1−q\_n)H under B. ∎

The threshold rises with the cost of human repair, falls with the price of an attempt, and falls with difficulty, that is, with a lower a or a higher b. A homogeneous model, in which p is constant, would prescribe either never stopping or never starting, so it is heterogeneity that makes the rule interior. The running example illustrates the logic. A firm that used the average success rate would value every attempt at $23.5 and never stop, whereas the true value of the third attempt is $4.8 and that of the tenth is $1.26. At an effective cost of $1.20 per attempt the firm stops after ten attempts. At $6 per attempt, a price of $5 plus its own $1, it stops after ⌈12/6 − 0.51⌉ = 2.

### 4.2 Pay-per-use contracts under monopoly

**Proposition 2 (Double marginalization).** Under contract A with w > k, N\_A(w) ≤ N^FB, and surplus falls below its first-best level whenever w lowers the budget.

*Proof.* N\_A is decreasing in w, so N\_A(w) ≤ N\_A(k) = N^FB. Moreover, W(N+1) − W(N) = S(N)[q\_N H − (k+v)] is positive if and only if N < N^FB, so W increases up to N^FB. ∎

**Proposition 3 (Efficient success fee).** Under contract B with f^e = Hk/(k+v), N\_B(f^e) = N^FB, and the vendor earns k/(k+v) of the first-best surplus.

*Proof.* Since (H − f^e)/v = H/(k+v), the thresholds coincide. Vendor profit is f^e P − kE = (k/(k+v))[HP − (k+v)E]. ∎

In the running example, a per-attempt price of $5 makes the firm stop after two attempts and reduces the surplus from $33.9 to $27.5 per defect (Table 1). A success fee of f^e = 100 × 0.2/1.2 = $16.67 leaves the firm $83.3 per success. Because q₉ × 83.3 = 1.05 exceeds v = 1 while q₁₀ × 83.3 = 0.95 does not, the firm again stops after ten attempts, and the vendor keeps one-sixth of the $33.9, or $5.6.

**Proposition 4 (The monopoly fee exceeds the efficient fee).** Let N^FB ≥ 1 and Π(f) = f·P(N\_B(f)) − k·E(N\_B(f)). Because N\_B is an integer-valued step function of f, (a) Π is strictly increasing within each step, and for every f′ ≤ f^e there exists f > f^e with Π(f) > Π(f′); and (b) the budget at the vendor's optimum satisfies n̂ ≤ N^FB, with strict inequality unless the best fee lies in the same step as f^e, in which case the vendor raises the fee without changing the firm's depth.

*Proof sketch (full proof in Appendix E).* The firm's budget equals n exactly for f ∈ [φ\_n, φ\_{n−1}), where φ\_n = H − v/q\_n. Let L(n) be the vendor's profit at the lower end of this step and R(n) the supremum of its profit within the step. Then R(n) − L(n−1) = S(n−1)[q\_{n−1}H − (k+v)], which is negative if and only if attempt n is inefficient. For n > N^FB we therefore have R(n) ≤ L(n−1) < R(n−1), so R is strictly decreasing beyond N^FB. ∎

Numerically, the vendor's best step lies strictly below N^FB in 289 of 293 random parameter draws. In the other four draws the vendor raises the fee within the efficient step.

### 4.3 The incentive rent of sequential search

**Proposition 5 (Incentive rent and the optimal linear contract).** For N ≥ 1 define the incentive rent
G\_min(N) = v·[P(N)/q\_{N−1} − E(N)] = v·Σ\_{j<N} S(j)·(q\_j/q\_{N−1} − 1) ≥ 0.
(a) G\_min(1) = 0, G\_min is nondecreasing in N, and G\_min ≡ 0 if and only if difficulty is homogeneous.
(b) For every contract with per-attempt fee w ≥ 0 and success fee f ≤ H under which the firm chooses depth N ≥ 1, the vendor's profit satisfies
Π(w, f) ≤ R(N) − (w/v)·G\_min(N), where R(N) = W(N) − G\_min(N) = Σ\_{j<N} S(j)[q\_j φ\_{N−1} − k] and φ\_{N−1} = H − v/q\_{N−1}.
(c) R(N) is approached only by the pure success fee (w = 0, f ↑ φ\_{N−1}), and a positive per-attempt component strictly lowers profit whenever N ≥ 2 and difficulty is heterogeneous.
(d) The vendor's optimal depth maximizes R(N), and R(N+1) − R(N) = S(N)[q\_N H − (k+v)] − v·P(N)·(1/q\_N − 1/q\_{N−1}), so n̂ ≤ N^FB. For the Beta family the last factor equals 1/a.

*Proof sketch (full proof in Appendix E).* The firm chooses depth N only if q\_{N−1}(H−f) > w + v, that is, only if f < φ\_{N−1} − w/q\_{N−1}. Substituting this bound into Π = (w−k)E + fP gives Π < R(N) − w[P/q\_{N−1} − E]. Participation holds at the corner (0, φ\_{N−1}) because P ≥ q\_{N−1}E. ∎

To make the firm willing to try the N-th attempt, whose probability of success is low, the vendor must price the marginal success at φ\_{N−1} = H − v/q\_{N−1}. Every earlier attempt succeeded more often than the marginal one, so the firm keeps an infra-marginal gain on those attempts, and this gain is G\_min(N). It is zero when difficulty is homogeneous and grows with the dispersion of success probabilities. Because the vendor's profit is the surplus net of this rent, the vendor samples too little. The pure success fee delivers any depth at the lowest cost because a per-attempt fee collects revenue from attempts on which the firm's marginal gain is smallest.

The running example makes the mechanism concrete. To make the firm go three attempts deep, the vendor can charge at most φ₂ = H − v/q₂ = 100 − 1/0.0478 = $79.1 per verified fix. That leaves the firm $20.9 on each success, exactly its break-even cost v/q₂ of buying a success with the third attempt. The first two attempts succeed more often, so the firm has gained on them, and its total gain is G\_min(3) = $4.43. To induce ten attempts the vendor must cut the fee to φ₉ = $20.8, and the rent grows to $26.5 of the $33.9 surplus (Table 1).

Consider an illustrative backlog of 1,000 defects. Human-only repair costs $100,000. A monopolist charging per attempt sets w = q₀H − v = $22.5, so the firm tries once per defect and the AI repairs 235 defects. The vendor earns $22.3 thousand and the firm saves almost nothing, so the service looks cheap per call yet adds little for its buyer. A monopolist charging per verified fix sets $79.1, the firm tries up to three times, the AI repairs 330 defects, the vendor earns $25.6 thousand, and the firm saves $4.4 thousand. The efficient policy samples up to ten times and repairs 420 defects, for a joint surplus of $33.9 thousand, of which the per-attempt price leaves $22.3 thousand and the success fee $30.0 thousand.

**Proposition 6 (Lump-sum neutralization).** Suppose the vendor may also charge a fee T₀ that is independent of attempts and outcomes. Then (w, f, T₀) = (k, 0, W(N^FB)) implements N^FB and gives the vendor the entire surplus, and for any (w, f) the vendor can recapture G\_min through T₀ without changing the firm's budget.

*Proof.* T₀ enters the firm's cost as a constant and therefore does not enter any one-step comparison in Proposition 1. ∎

The distortions in this paper therefore stem from pay-per-use pricing. A lump sum is unattractive when the firm cannot judge quality before using the service, when procurement is made defect by defect, or when prepayment is costly.

**Table 2. The incentive rent (H = 100, v = 1, k = 0.2).**

| Heterogeneity (a, b) | N^FB | W(N^FB) | G\_min(N^FB) | Vendor's maximum at N^FB, R(N^FB) | Rent / W(N^FB) | Vendor's optimal depth n̂, R(n̂) |
|---|---|---|---|---|---|---|
| RepairBench-like (0.12, 0.39) | 10 | 33.9 | 26.5 | 7.4 | 78% | 3, 25.6 |
| SWE-Verified-like (0.25, 0.34) | 21 | 63.5 | 52.2 | 11.3 | 82% | 4, 50.2 |
| Synthetic (0.40, 3.0) | 30 | 43.9 | 35.1 | 8.8 | 80% | 10, 30.4 |

A vendor that wanted the efficient depth would have to leave the firm about four-fifths of the surplus.

### 4.4 Market structure

*Private vendor quality.* Suppose the vendor knows its type θ ∈ {H, L}, with success parameters a\_H > a\_L (common b and k), and the firm holds a prior μ that the type is H.

**Proposition 7 (Profit-order reversal).** For any common depth N ≥ 1, (a) under contract A the low type earns weakly more, (w−k)E\_L(N) ≥ (w−k)E\_H(N); and (b) under contract B the high type earns strictly more when f > 0, fP\_H(N) − kE\_H(N) > fP\_L(N) − kE\_L(N).

*Proof.* The Beta family is ordered by likelihood ratio in a, so S(j) = E[(1−p)^j] is decreasing in a. Hence S\_H ≤ S\_L, which implies E\_H ≤ E\_L and P\_H ≥ P\_L, with strict inequality in P for N ≥ 1. ∎

Per-attempt pricing pays for failures, so it rewards the less capable vendor at any depth, and a per-attempt contract therefore cannot credibly signal quality. A success fee can. A less capable vendor needs more attempts to deliver the same fix. When it is paid per attempt it bills those attempts, and when it is paid per fix it absorbs their cost. Numerically (Section 5.2), a high-quality vendor usually separates by lowering its fee below the full-information monopoly fee, which makes the firm sample deeper and partly corrects the monopoly under-sampling.

*Competition among differentiated vendors.* A unit mass of firms chooses among n symmetric vendors (same a, b, and k) and human-only repair. Firm i's value from vendor j is G\_j + σε\_ij, where ε\_ij follows a Gumbel distribution, G\_j is the firm's saving at its optimal budget under vendor j's contract, and σ measures differentiation. Shares are logit, and vendors choose the price of their contract form in a symmetric Bertrand–Nash equilibrium.

**Proposition 8 (Limits of competition).** (a) As σ → 0, that is, with close substitutes, per-attempt pricing converges to w = k and the efficient depth N^FB. Success fees converge to the zero-profit fee f\_0 ≤ f^e, so the firm over-samples (N\_B(f\_0) ≥ N^FB) and surplus is weakly below first best. (b) Let ρ = e^{S^FB/σ} − 1. For large σ, (n+1)s\_j ∈ [1−ρ, 1+ρ] at every price with positive profit, so every best response earns at least a fraction (1−ρ)/(1+ρ) of the monopoly profit per served firm. If the monopoly step is unique with margin Δ, the equilibrium budget equals the monopoly budget once σ > S^FB / ln(1 + Δ/(2Π\_m − Δ)). Market coverage tends to n/(n+1).

*Proof.* (a) With w = k the firm's threshold is the efficient one. For contract B, zero profit f\_0 P = kE and participation vE + f\_0 P ≤ HP together give (k+v)E ≤ HP and hence f\_0 = kE/P ≤ Hk/(k+v). (b) At best responses G ∈ [0, S^FB], and the share equals (1+δ\_j)/(n+1+Σδ\_k) with δ ∈ [0, ρ], from which the bounds follow. A price outside the monopoly step earns at most (1+ρ)(Π\_m − Δ)/(n+1), which is below (1−ρ)Π\_m/(n+1) when ρ < Δ/(2Π\_m − Δ). ∎

Differentiation, more than the number of vendors, determines whether competition removes the distortion; intermediate cases are solved numerically in Section 5.3. The intuition is as follows. With logit demand, a vendor's share responds to its price in proportion to how much the price changes the firm's saving relative to the dispersion σ of firms' idiosyncratic preferences. When σ is small, firms barely prefer one vendor to another, a small price cut attracts everyone, and competition drives prices toward cost. When σ is large relative to the surplus, a price cut moves few firms, so each vendor acts as a monopolist over its own customers and entry mostly divides the market. In Section 5.3, moving from one vendor to ten with σ = 30 raises coverage from 50% to 91% of firms, but the per-attempt budget stays at one attempt.

---

## 5. Numerical Equilibria

The shape parameters (a, b) come from the empirical fits in Section 6. Tables 2 to 4 use H = 100, v = 1, and k = 0.2 in dollars, which lie inside the ranges calibrated from public sources in Section 5.4 for H and between the function-level and agentic ranges for k. Section 5.4 shows how the conclusions change across those ranges. Because budgets are integers, the vendor's optimal price has no closed form, so we compute equilibria on price grids or by exact enumeration of budget steps.

### 5.1 Monopoly: per-attempt versus success fee

**Table 3. Monopoly equilibria (H = 100, v = 1, k = 0.2).** Entries are the optimal price, the firm's budget N, the vendor's profit, the firm's saving, and welfare as a share of first best.

| Heterogeneity (a, b) | Per-attempt | Success fee |
|---|---|---|
| RepairBench-like (0.12, 0.39) | w\* = 22.5, N=1, 22.3, 0.01, 66% | f\* = 79.0, N=3, 25.6, 4.4, 89% |
| SWE-Verified-like (0.25, 0.34) | w\* = 41.3, N=1, 41.1, 0.03, 65% | f\* = 85.6, N=4, 50.2, 6.0, 88% |
| Synthetic (0.40, 3.0) | w\* = 4.4, N=5, 17.3, 11.9, 66% | f\* = 69.0, N=10, 30.4, 7.2, 85% |

A per-attempt monopolist prices the first attempt (w ≈ q₀H − v), and the firm stops after one. The success fee extracts less per defect but sustains deeper sampling.

We also drew 296 random parameter sets, with a ∈ [0.05, 0.6], b ∈ [0.1, 4], H ∈ [30, 500], v/H ∈ [0.001, 0.03], and k/v ∈ [0.1, 3]. The success fee raises the vendor's profit in 99% of the draws and total surplus in 100%. Median surplus is 91% of first best (interquartile range 88–94%) under the success fee against 65% (55–77%) under per-attempt pricing, and the median budgets are 28 at first best, 1 under per-attempt pricing, and 6 under the success fee. The firm's own saving is higher under the success fee in only 67% of the draws, so outcome-based pricing can transfer surplus to the vendor, and a side payment or a two-part tariff may then be needed.

### 5.2 Private vendor quality

Take a\_H = 0.25, a\_L = 0.08, b = 0.35, H = 100, v = 1, and k = 0.2. The reversal of profit order is stark. At fee levels w = 10 and f = 50 and depth N = 10, the low type earns 73.8 under per-attempt pricing against the high type's 46.5, whereas under the success fee it earns 14.8 against 32.6. In 60 random draws, the low type would mimic the high type's full-information contract in 98% of cases. A separating linear contract exists in 77% of the draws (46 draws) and is always a success fee. Separation costs the high type a median 11.0% of its profit (interquartile range 7.1–16.8%). The induced budget is at least as large as under full information in 76% of those draws, and total surplus and the firm's saving are higher under separation in 74% of them (median increases of 7% and 9.7). In the remaining quarter of draws the high type cannot separate by any linear contract and the market pools. Signaling by generosity thus partly offsets the monopoly distortion. These are numerical results under off-path beliefs that assign any other contract to the low type.

### 5.3 Competition

**Table 4. Differentiated-Bertrand equilibria, RepairBench-like case (first-best N = 10).** Entries are the budget N and welfare as a share of first-best welfare for the same n and σ.

| σ | Vendors n | Per-attempt: N, welfare | Success fee: N, welfare |
|---|---|---|---|
| 1 | 2 | 9, 1.00 | 11, 1.00 |
| 10 | 2 | 3, 0.90 | 7, 0.97 |
| 10 | 5 | 4, 0.95 | 9, 1.00 |
| 30 | 2 | 1, 0.81 | 4, 0.94 |
| 30 | 5 | 1, 0.86 | 4, 0.96 |
| 30 | 10 | 1, 0.89 | 5, 0.98 |

With close substitutes (σ = 1) one rival suffices. With strongly differentiated vendors (σ = 30) the per-attempt equilibrium stays at the monopoly budget of one attempt even with ten vendors, and entry only widens coverage, from 50% to 91% of firms, as Proposition 8(b) predicts. The bound in Proposition 8(b) is conservative, since the monopoly budget is already reached at σ = 100. In 240 cells of a random sweep, the per-attempt equilibrium is not deviation-proof in 71% of cells, meaning that a vendor gains by switching to a success fee, while the success-fee equilibrium is deviation-proof in 76%. Vendors prefer the success fee in 55–100% of the cells, whereas the firm's saving is higher under per-attempt pricing in 68–98%. Vendors thus choose the contract form that raises surplus but that firms often like less.

### 5.4 Calibration of the cost parameters and sensitivity

The cost parameters are calibrated from public sources accessed on 25 October 2026.

*Human repair cost H.* The US Bureau of Labor Statistics (Occupational Outlook Handbook) reports a median hourly wage of $64.44 for software developers in May 2025. Employer Costs for Employee Compensation (private industry, June 2022, the latest release we retrieved) put benefits at 29.5% of total compensation, so the loaded cost is $64.44 / (1 − 0.295) ≈ $91 per hour. The annotated time to fix for SWE-bench Verified, as summarized by Epoch AI, is under 15 minutes for 39% of tasks, 15 minutes to 1 hour for 52%, 1–4 hours for 8%, and above 4 hours for 3 tasks. With bucket midpoints the expected hands-on time is 0.52 hours, which gives H ≈ $48 for an engineer who knows the code. METR's check found these estimates likely to be optimistic, although its sample consisted of only six tasks, so we allow two to four times that time for an unfamiliar engineer. H therefore ranges from about $15 for a 10-minute fix through $50 to $200, and up to $400 or more for multi-hour fixes, before any context-transfer overhead.

*Vendor cost per attempt k.* We multiply observed token usage by the OpenRouter price list. For function-level repair in RepairBench, a non-reasoning attempt uses about 1,700 input and 800 output tokens, and a reasoning model such as o4-mini uses about 1,400 input and 10,400 output tokens. At list prices, k is $0.0001–0.0013 for small and mid-sized open models, $0.011 for a frontier model at 800 output tokens, and $0.0006–0.11 with reasoning-length outputs of 10,400 tokens borrowed from the o4-mini case ($0.047 for o4-mini itself). For repository-level agents, the SWE-bench submission READMEs report $0.60 (Bracket), $0.64 (Moatless with Claude 4 Sonnet), and $0.84 (Cortexa) per task. Overall, k ranges from $0.0003 to about $0.1 at function level and from about $0.6 to $3 for agents. Our own HumanEvalFix runs were billed $0.00002–0.00004 per attempt for models with 3–8 billion parameters.

*Firm cost per attempt v.* If verification is an automated test run, v is the cost of continuous integration, about $0.01–0.50. If an engineer spends two to ten minutes triaging each candidate patch, v is about $3–15 at $91 per hour. This is the least well-grounded input, because it is a judgement based on the loaded wage and not a measured quantity.

*Sensitivity.* We evaluate all combinations on a grid within each regime for three heterogeneity profiles: the RepairBench-like fit, the SWE-Verified-like calibration, and a HumanEvalFix-Llama-like fit with a = 0.50 and b = 0.58. The monopoly equilibria are computed exactly, using the profit at the top of each budget step (Appendix E). Table 5 summarizes the results across the three profiles for the points at which AI repair is worth using (N^FB ≥ 1).

**Table 5. Sensitivity of the main conclusions across calibrated ranges.** Entries are ranges across the three heterogeneity profiles, with 100–180 grid points per profile.

| Regime (H, v, k grids) | AI repair worth using | Welfare: success fee > per-attempt | Vendor profit: success fee ≥ per-attempt | Firm saving: success fee > per-attempt | Median welfare / first best: per-attempt; success fee | Vendor's depth below N^FB | Median rent share of W(N^FB) |
|---|---|---|---|---|---|---|---|
| Function-level, automated verification (H $15–400; v $0.01–0.5; k $0.0003–0.1) | 100% | 97–100% | 100% | 97–100% | 0.48–0.54; 0.87–0.93 | 100% | 90–91% |
| Function-level, manual triage (H $15–400; v $3–15; k $0.0003–0.1) | 75–88% | 22–57% | 100% | 22–57% | 0.72–0.91; 0.87–0.91 | 61–86% | 67–95% |
| Repository-level agents (H $50–800; v $0.1–5; k $0.6–3) | 100% | 76–95% | 100% | 76–95% | 0.56–0.67; 0.92–0.93 | 92–100% | 37–44% |

Three findings stand out. First, the vendor's preference for the success fee is robust: its profit is at least as high under the success fee at 100% of the grid points in every regime. Second, the welfare advantage of the success fee is strong where an attempt is cheap relative to human repair, at 97–100% of points under automated verification and 76–95% for agentic repair, and weak when manual triage makes each attempt expensive (22–57%). In the latter regime the efficient depth is small (median 2–6), so a per-attempt monopolist that stops the firm after one or two attempts loses little. Third, the incentive rent is large where depth is valuable, about nine-tenths of the surplus under automated verification and 37–44% for agents, so vendors undersample at 61–100% of the points.

Figure 2 shows the pattern in terms of cost ratios. When H/v is below about 30, the efficient depth is one or two attempts and both contract forms are nearly efficient. Above that level, welfare under per-attempt monopoly falls to 0.4–0.6 of first best while the success fee stays near 0.85–0.9. The conclusions of Sections 4 and 5 therefore apply to regimes with H/v of about 30 or more, which cover automated verification and agentic repair and exclude cheap fixes that require expensive per-attempt human review.

![**Figure 2.** Welfare (share of first best) under per-attempt and success-fee monopoly, and the incentive rent as a share of surplus at the first-best depth, as functions of H/v and k/v (a = 0.12, b = 0.39). Blank cells are combinations in which AI repair is not worth using.](contracts/fig_sensitivity.png){width=70%}

---

## 6. Evidence on the Model's Premises

The model rests on three premises: difficulty is heterogeneous (P1), failures are informative (P2), and a threshold fitted to historical defects performs well out of sample (P3). We examine them with open data.

*RepairBench.* RepairBench (Silva and Monperrus 2025) contains 574 single-function Java bugs (484 from Defects4J v2 and 90 from GitBug-Java), with ten sampled patches per bug and model, each scored by the full test suite. After we require ten samples per bug and at least 80 bugs per combination, 84 model–dataset combinations remain (22,856 records). The Beta-binomial distribution fits better than the homogeneous binomial in all 84 combinations, both by AIC and by held-out likelihood on a 50/50 split by bug identifier. The median fitted parameters are a = 0.12 and b = 0.39, a U-shaped distribution, and a median 59% of bugs are never solved in ten samples. The median thresholds at H/c = 10, 30, 100, and 300 are 1, 3, 11, and 34. We fit the rule on half of the bugs and evaluate it exactly on the other half, with caps of up to ten attempts and costs in units of c. The rule comes within 0.4–1.7% of the best cap in hindsight and costs 34–67% less than a ten-sample cap for H/c between 3 and 10. A ten-sample cap costs more than human-only repair when H/c ≤ 10.

*HumanEvalFix with 40 samples per bug.* To study caps beyond ten attempts, we sampled 40 patches for each of the 164 Python bugs in HumanEvalFix from three small models (Llama-3.2-3B, Ministral-8B, and Gemma-3-4B, at temperature 1.0), a total of 19,680 samples at a cost of $0.56. The Beta-binomial improves AIC over the binomial by thousands of points in all three models (for example, from 7,293 to 739). A fit to the first ten samples predicts coverage at 40 samples to within 2.6 points; for Llama, for instance, the observed coverage is 0.927 and the predicted coverage is 0.909. For Gemma and Llama the fitted rule is within about 1% of the best cap. For Ministral, which solves 96% of the bugs and leaves a small unsolvable residue, the rule oversamples (N between 9 and 40, against a best cap in hindsight of 3 to 7) and costs 19–40% more than the best cap at H/c ≤ 30. The Beta tail assigns positive success probability to bugs that are never solved, and a training half of 82 bugs cannot identify that share. A firm should therefore validate the fitted threshold with a sweep of caps on held-out defects.

*SWE-bench.* The official submission logs are pass@1 by rule, so attempt-level data do not exist there. Two published pass@1 and pass@k pairs identify the Beta parameters, which amounts to a calibration and not a test. DeepSWE on the Verified set implies (0.25, 0.34), and the Lite series of Brown et al. (2024) implies (0.12, 0.65), again with a < 1. Coverage exceeds the rate at which a verifier selects the correct patch (71.0% versus 59.2%, and 75% versus 68.4%), so at the repository level success is observed only through an imperfect verifier, which lowers the benefit of success in the thresholds.

---

## 7. Extensions

If a patch that passes the firm's tests is wrong with probability e and a wrong patch causes downstream cost L, the benefit H in the thresholds becomes H − eL. Weaker tests therefore shorten the justified search, and under a success fee, disputes over what counts as a verified fix become a cost to both parties.

Several further directions follow naturally: latency and severity-contingent thresholds, defect classes with their own (a, b), continuous vendor types and menus of contracts, multi-sourcing, and dynamic learning of (a, b) across defects. Behavioral frictions on the buyer's side, such as loss aversion toward per-attempt payments or sunk-cost effects, are also plausible, but they would require experimental evidence to parameterize and are not modeled here.

---

## 8. Discussion

Our results make four theoretical points. The economically relevant decision in AI-assisted maintenance is whether to continue after a failure, not the pass@k capability of the model. A seller's markup distorts per-attempt contracts, and competition removes the distortion only if vendors are close substitutes. The underlying force is an incentive rent of sequential search, which explains why vendors prefer pure success fees, why they induce too little sampling, and why a lump sum would restore efficiency. Finally, outcome-based pricing raises surplus but not necessarily the buyer's share, which parallels the conflict of interest between publishers and advertisers that Hu et al. (2016) document for performance-based advertising pricing.

For managers, the model suggests a simple procedure for buyers. A buyer should sample each of a few hundred historical defects several times (ten samples per defect suffice) and record whether each attempt passes. The buyer then fits the Beta-binomial distribution of the counts to obtain (a, b), computes the cost per attempt c as the vendor's price plus its own verification cost, and sets the threshold N\* = ⌈aH/c − a − b⌉. In the running example, c = $1.2 gives 10 attempts and c = $6 gives 2. The buyer should check the threshold against a sweep of caps on held-out defects, because the HumanEvalFix experiment shows that a fit can oversample when the share of unsolvable defects is small, and recompute it whenever the vendor's price or the cost of human repair changes. If a vendor quotes a price per fix, the same rule applies with the net value H − f in place of H and with v as the cost of an attempt. Buyers should also negotiate a success fee close to Hk/(k+v) in return for volume. Vendors gain from outcome-based pricing, including under competition, but they should recognize that per-attempt pricing near cost is efficient in commodity markets with close substitutes. Platforms and governance bodies should publish per-sample outcomes and per-attempt costs, which are the inputs on which these contracts depend and which current leaderboards do not report.

The analysis has limitations. First, H, v, and k are calibrated from public statistics and price lists (Section 5.4) but not measured at a firm, and v is the least well grounded; benchmark bugs, which are single functions with complete tests, are also easier to verify than industrial defects. Second, we assume that attempts are conditionally independent given p, whereas samples drawn from the same prompt and model are probably positively correlated, which would make failures more informative and lower the thresholds. Third, vendors are symmetric, competition is logit and one-shot, and private information is analyzed for two types and linear contracts, so the separation and competition results are numerical. Fourth, patch quality is binary. A success fee pays for passing the tests, so a vendor paid per verified fix may neglect quality dimensions that the tests do not measure, which is the multitask problem of Holmström and Milgrom (1991); we do not model it. Fifth, public benchmarks may overlap with the training data of the models.

Several extensions would change the results in predictable directions. Correlated attempts would lower the thresholds. Imperfect verification replaces H with H − eL, where e is the share of accepted patches that are wrong and L is their downstream cost, and so would also lower them. Learning about (a, b) by the firm and the vendor over time would allow the firm to refine its rule and the vendor its contract. Multi-sourcing would give the firm a second price to compare and so act like competition. An improving vendor, whose model raises a over time, lies outside our one-shot model.

The analytical results do not depend on field data, but the contract predictions, outcome-based pricing under market power and per-attempt pricing among close substitutes, and the cost parameters would be tested directly in a study with a partner firm (Appendix D).

---

## 9. Conclusion

An AI repair service creates two linked decisions: how long the buyer lets the AI keep trying, and how the vendor charges for trying. When defects differ in difficulty, the buyer's optimal rule is a threshold that rises with the cost of human repair and falls with the price and difficulty of attempts. Charging per attempt above cost makes the buyer give up too early. A pure success fee is the vendor's best pay-per-use contract, but because inducing deep sampling requires leaving the buyer an incentive rent, even a success fee leads to too little sampling. A lump sum would remove every distortion, and competition does so only among close substitutes. Public repair data support the premises of heterogeneous difficulty and informative failures, and a threshold fitted to past defects usually performs close to the best cap, although it can oversample when the unsolvable share is small and poorly identified. The next step is to test the contract predictions on a firm's repair and billing records.

---

## References

*(Bibliographic details were checked against web sources on 25 October 2026. Items whose volume or pages could not be confirmed are cited without them; see `submission/reference_verification.md`. Verify all entries against the originals before submission.)*

- Agrawal, A., Gans, J., and Goldfarb, A. (2018). *Prediction Machines: The Simple Economics of Artificial Intelligence.* Harvard Business Review Press.
- Asdemir, K., Kumar, N., and Jacob, V. S. (2012). Pricing models for online advertising: CPM vs. CPC. *Information Systems Research*, 23(3), 804–822.
- Bajari, P., and Tadelis, S. (2001). Incentives versus transaction costs: A theory of procurement contracts. *RAND Journal of Economics*, 32(3), 387–407.
- Bakos, J. Y. (1997). Reducing buyer search costs: Implications for electronic marketplaces. *Management Science*, 43(12), 1676–1692.
- Banker, R. D., and Slaughter, S. A. (2000). The moderating effects of structure on volatility and complexity in software enhancement. *Information Systems Research*, 11(3), 219–240.
- Brown, B., et al. (2024). Large language monkeys: Scaling inference compute with repeated sampling. arXiv:2407.21787.
- Brynjolfsson, E., Li, D., and Raymond, L. (2025). Generative AI at work. *Quarterly Journal of Economics*, 140. https://doi.org/10.1093/qje/qjae044.
- Chen, M., et al. (2021). Evaluating large language models trained on code. arXiv:2107.03374.
- Chen, Y., and Bharadwaj, A. (2009). An empirical analysis of contract structures in IT outsourcing. *Information Systems Research*, 20(4), 484–506.
- Chow, Y. S., Robbins, H., and Siegmund, D. (1971). *Great Expectations: The Theory of Optimal Stopping.* Houghton Mifflin.
- Dellarocas, C. (2012). Double marginalization in performance-based advertising: Implications and solutions. *Management Science*, 58(6), 1178–1195.
- Dey, D., Fan, M., and Zhang, C. (2010). Design and analysis of contracts for software outsourcing. *Information Systems Research*, 21(1), 93–114.
- Eisenhardt, K. M. (1989). Agency theory: An assessment and review. *Academy of Management Review*, 14(1), 57–74.
- Fitoussi, D., and Gurbaxani, V. (2012). IT outsourcing contracts and performance measurement. *Information Systems Research*, 23(1), 129–143.
- Fügener, A., Grahl, J., Gupta, A., and Ketter, W. (2021). Will humans-in-the-loop become borgs? Merits and pitfalls of working with AI. *MIS Quarterly*, 45(3). https://doi.org/10.25300/MISQ/2021/16553.
- Fügener, A., Grahl, J., Gupta, A., and Ketter, W. (2022). Cognitive challenges in human–artificial intelligence collaboration: Investigating the path toward productive delegation. *Information Systems Research*, 33(2), 678–696.
- Gopal, A., Sivaramakrishnan, K., Krishnan, M. S., and Mukhopadhyay, T. (2003). Contracts in offshore software development: An empirical analysis. *Management Science*, 49(12), 1671–1683.
- Holmström, B., and Milgrom, P. (1991). Multitask principal–agent analyses: Incentive contracts, asset ownership, and job design. *Journal of Law, Economics, and Organization*, 7(special issue), 24–52.
- Hu, Y. J., Shin, J., and Tang, Z. (2016). Incentive problems in performance-based online advertising pricing: Cost per click vs. cost per action. *Management Science*, 62(7), 2022–2038.
- Ibrahim, R., Kim, S.-H., and Tong, J. (2021). Eliciting human judgment for prediction algorithms. *Management Science*, 2314–2325. https://doi.org/10.1287/mnsc.2020.3856.
- Jimenez, C. E., Yang, J., Wettig, A., Yao, S., Pei, K., Press, O., and Narasimhan, K. (2024). SWE-bench: Can language models resolve real-world GitHub issues? *International Conference on Learning Representations (ICLR 2024).*
- Kemerer, C. F., and Slaughter, S. (1999). An empirical approach to studying software evolution. *IEEE Transactions on Software Engineering*, 25(4), 493–509.
- Ladas, K., Kavadias, S., and Loch, C. (2022). Product selling vs. pay-per-use service: A strategic analysis of competing business models. *Management Science*, 68(7), 4964–4982.
- Le Goues, C., Nguyen, T., Forrest, S., and Weimer, W. (2012). GenProg: A generic method for automatic software repair. *IEEE Transactions on Software Engineering.*
- Lientz, B. P., and Swanson, E. B. (1980). *Software Maintenance Management.* Addison-Wesley.
- Ma, D., and Seidmann, A. (2015). Analyzing software as a service with per-transaction charges. *Information Systems Research*, 26(2), 360–378.
- McCall, J. J. (1970). Economics of information and job search. *Quarterly Journal of Economics*, 84(1), 113–126.
- Myerson, R. B. (1981). Optimal auction design. *Mathematics of Operations Research*, 6(1), 58–73.
- Peng, S., Kalliamvakou, E., Cihon, P., and Demirer, M. (2023). The impact of AI on developer productivity: Evidence from GitHub Copilot. arXiv:2302.06590.
- Raisch, S., and Krakowski, S. (2021). Artificial intelligence and management: The automation–augmentation paradox. *Academy of Management Review*, 46(1), 192–210.
- Silva, A., and Monperrus, M. (2025). RepairBench: Leaderboard of frontier models for program repair. *LLM4Code Workshop (ICSE 2025).* arXiv:2409.18952.
- Spengler, J. J. (1950). Vertical integration and antitrust policy. *Journal of Political Economy*, 58(4).
- Stigler, G. J. (1961). The economics of information. *Journal of Political Economy*, 69(3), 213–225.
- Sundararajan, A. (2004). Nonlinear pricing of information goods. *Management Science*, 50(12), 1660–1673.
- Susarla, A., Subramanyam, R., and Karhade, P. (2010). Contractual provisions to mitigate holdup: Evidence from information technology outsourcing. *Information Systems Research*, 21(1), 37–55.
- Tirole, J. (1988). *The Theory of Industrial Organization.* MIT Press.
- Weitzman, M. L. (1979). Optimal search for the best alternative. *Econometrica*, 47(3), 641–654.
- Whang, S. (1992). Contracting for software development. *Management Science*, 38(3), 307–324.
- Xia, C. S., Wei, Y., and Zhang, L. (2023). Automated program repair in the era of large pre-trained language models. *Proceedings of the 45th International Conference on Software Engineering (ICSE 2023)*, 1469–1481.
- Yeverechyahu, D., Mayya, R., and Oestreicher-Singer, G. (2024). The impact of large language models on open-source innovation: Evidence from GitHub Copilot. arXiv:2409.08379.

---

## Appendix A. Survival Function and Posterior Predictive (Beta Family)

Given p, P(T > j | p) = (1−p)^j. Integrating over p ~ Beta(a, b) gives S(j) = B(a, b+j)/B(a, b). After n failures the posterior is Beta(a, b+n), whose mean is a/(a+b+n) = q\_n.

## Appendix B. Estimation

With counts (n samples, k successes) per defect, the Beta-binomial likelihood is C(n,k)·B(k+a, n−k+b)/B(a,b). First-success data censored at K attempts contribute B(a+1, b+t−1)/B(a,b) for a defect solved at attempt t and B(a, b+K)/B(a,b) for an unsolved one. Both likelihoods are maximized over (log a, log b) with the Nelder–Mead algorithm.

## Appendix C. Reproducibility

The replication package contains the code for the contract equilibria (`contracts.py`, `robustness.py`), private quality (`asymmetric.py`, `asym_sweep.py`), competition (`diff_bertrand.py`, `diff_sweep.py`), proof checks (`verify_proofs.py`) and distribution-free checks of Propositions 1, 5, and 6 (`general_theory.py`); the empirical analyses of RepairBench (`load_repairbench.py`, `analyze.py`), the SWE-bench logs (`swebench_repo_level.py`) and the HumanEvalFix sampling and analysis (`sample_humanevalfix.py`, `analyze_hef.py`); and the cost calibration and sensitivity analysis (`calibration.py`, `sensitivity.py`, `fig_sensitivity.py`).

## Appendix D. Field-Data Request and Design (Not Executed)

For each defect, a partner firm would provide an identifier and type; timestamps of arrival, each AI attempt, verification, escalation, and closure; for each attempt, the test outcome, token counts, the compute cost billed by the vendor, and the verifier's effort; the escalation outcome; the engineering hours and fully loaded cost of human repair; later defects traced to AI patches; and the contract terms. The design would randomize the attempt cap within strata defined by defect type and severity for at least a quarter, estimate (a, b) by stratum from the first part of the sample, and compare the realized cost per resolved defect under the reservation rule with that under the firm's existing cap. If the vendor offers both contract forms, the contract could be randomized across teams. Attempt-level outcomes and costs suffice, so neither source code nor defect text is needed.

## Appendix E. Proofs

**Lemma A (steps).** Under contract B, N\_B(f) = n ≥ 1 if and only if q\_n(H−f) ≤ v < q\_{n−1}(H−f), that is, f ∈ [φ\_n, φ\_{n−1}) with φ\_n = H − v/q\_n. For the Beta family φ\_n = H − v(n+a+b)/a, so the steps have equal width v/a. Also N\_B(f) = 0 if and only if f ≥ φ\_0. At f = φ\_n the firm is indifferent about attempt n+1 and stops.

**Lemma B (comparison across a step boundary).** Let L(n) = φ\_n P(n) − kE(n) and R(n) = φ\_{n−1}P(n) − kE(n). Then
R(n) − L(n−1) = φ\_{n−1}[P(n) − P(n−1)] − k[E(n) − E(n−1)] = S(n−1)[φ\_{n−1}q\_{n−1} − k] = S(n−1)[q\_{n−1}H − (k+v)],
using P(n) − P(n−1) = q\_{n−1}S(n−1), E(n) − E(n−1) = S(n−1), and q\_{n−1}(H − φ\_{n−1}) = v. The sign of this expression is the sign of the efficiency of attempt n, which is equivalent to the sign of φ\_{n−1} − f^e.

**Proof of Proposition 4.** Profit within step n is fP(n) − kE(n), which has slope P(n) > 0. Hence L(n) < Π < R(n) in the interior of the step, and R(n) − L(n) = (φ\_{n−1} − φ\_n)P(n) > 0. Let n₀ = N^FB ≥ 1, so that f^e ∈ [φ\_{n₀}, φ\_{n₀−1}). For (b), if n > n₀ then φ\_{n−1} ≤ φ\_{n₀} ≤ f^e, so Lemma B gives R(n) ≤ L(n−1) < R(n−1). Thus R is strictly decreasing from n₀ onward and n̂ ≤ n₀. For (a), take f′ ≤ f^e with n = N\_B(f′) ≥ n₀. If n = n₀, any f ∈ (f^e, φ\_{n₀−1}) has Π(f) > Π(f′) by monotonicity within the step. If n > n₀, then Π(f′) < R(n) < R(n₀), and the supremum of Π on (f^e, φ\_{n₀−1}) equals R(n₀). ∎

**Proof of Proposition 5.** (a) Each term of G\_min is nonnegative because q\_j ≥ q\_{N−1} for j < N. For N = 1, P(1)/q₀ − E(1) = 1 − 1 = 0. When N increases to N+1, the existing terms weakly rise because q\_N ≤ q\_{N−1}, and the new term is zero. (b) The firm chooses depth N only if q\_{N−1}(H−f) > w+v, so f < φ\_{N−1} − w/q\_{N−1}. Then Π = (w−k)E + fP < (w−k)E + [φ\_{N−1} − w/q\_{N−1}]P = R(N) − w[P/q\_{N−1} − E]. The identity R(N) = W(N) − G\_min(N) follows from φ\_{N−1}P − kE = HP − (k+v)E − v[P/q\_{N−1} − E]. (c) At (0, φ\_{N−1}) participation holds because vE + φ\_{N−1}P ≤ HP is equivalent to q\_{N−1}E ≤ P, which is true because P = Σ\_{j<N} S(j)q\_j. (d) G\_min(N+1) − G\_min(N) = vP(N)(1/q\_N − 1/q\_{N−1}) follows from P(N+1) = P(N) + q\_N S(N) and E(N+1) = E(N) + S(N), while W(N+1) − W(N) = S(N)[q\_N H − (k+v)]. ∎
