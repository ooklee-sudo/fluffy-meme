import json, sys
import numpy as np
import os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from isr_lib import *

R = os.path.join(HERE, "..", "..", "results") + os.sep
main = json.load(open(R + "dynamic_bertrand.json"))["models"]
rows = json.load(open(R + "sens2_rows.json"))
eqs = json.load(open(R + "equilibria_states.json"))
base = [r for r in rows if r["name"] == "base"][0]
cart, shr = main["cartel (joint profit)"], main["market_share_contest (original)"]
EH, EL = eqs["uniform_start"], eqs["random_start_seed1"]
hiX, loX = base["hi"], base["lo"]            # high / low capacity equilibria of the base scenario
assert abs(hiX["mean_capacity"] - EH["mean_capacity"]) < 0.01 and abs(loX["mean_capacity"] - EL["mean_capacity"]) < 0.01

# ---- facts computed from the results (so the text cannot drift from the numbers) ----
N = len(rows)
multi = [r for r in rows if r["n_eq"] >= 2]
unconv_runs = sum(r["n_unconverged"] for r in rows)
unconv_scn = [r["name"] for r in rows if r["n_unconverged"]]
mono_fail = [r for r in rows if r["checks"]["price_monotone_violations"] > 0]
p1_all = all(r["checks"]["prop1_top_price_strictly_dominant"] and r["checks"]["prop1_top_price_modal"] for r in rows)
order_ok = all(r["mean_capacity"][0] >= r["cartel_cap"] - 0.05 and r["mean_capacity"][1] <= r["contest_cap"] + 0.05 for r in rows)
only_scarce = [r for r in rows if r["n_eq"] == 1 and abs(r["mean_capacity"][1] - r["cartel_cap"]) < 0.05]
gaps_min = min(r["contest_cap"] - r["mean_capacity"][1] for r in rows)
gaps_max = max(r["contest_cap"] - r["mean_capacity"][0] for r in rows)
multi_cs_ok = all(r["hi"]["consumer_surplus"] > r["lo"]["consumer_surplus"] and r["welfare_hi"] < r["welfare_lo"] for r in multi)
print("gaps", gaps_min, gaps_max, "multi CS/W ordering", multi_cs_ok)
print("N", N, "multi", len(multi), "unconv runs", unconv_runs, unconv_scn, "mono fail", len(mono_fail), "P1", p1_all, "order", order_ok, "only scarce", len(only_scarce))
assert p1_all and order_ok and multi_cs_ok

f2 = lambda x: "%.2f" % x
f1 = lambda x: "%.1f" % x
def rng(t, fmt=f2):
    lo, hi = t
    return fmt(lo) if abs(hi - lo) < 0.005 * max(1, abs(hi)) * (1 if fmt is f2 else 1) and fmt(lo) == fmt(hi) else "%s–%s" % (fmt(lo), fmt(hi))

TS = lambda d: d["profit_total"] + d["consumer_surplus"]
W_H, W_L = TS(hiX), TS(loX)

doc = new_doc()

# =============================== TITLE PAGE ===============================
def center(text, size=12, bold=False, after=0, italic=False):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(after)
    rich(p, text, size=size, bold=bold, italic=italic)
    return p

center("Price Competition and Capacity Investment in LLM Inference Markets:", 14, True)
center("A Dynamic Bertrand–Edgeworth Game", 14, True, after=14)
p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(6)
rich(p, "Abstract", bold=True)
abstract = (
    "Providers of large language model (LLM) inference compete on posted prices, yet the capacity behind those prices takes a period to build and "
    "cannot be adjusted for free. We model two providers that post prices under capacity constraints and adjust discrete GPU capacity with a "
    "one-period lag and sunk costs, while demand moves among three Markov regimes. With simultaneous pricing, pricing and capacity separate in a logit "
    "Markov perfect equilibrium; scarcity makes the reservation price dominant, and abundance leaves markups bounded by twice the price step. Across %d settings, "
    "equilibrium capacity lies between a joint-profit benchmark and a market-share contest, but equilibria are often multiple. When prices are committed in "
    "alternating moves, a two-price analysis shows that tacit collusion is sustainable for intermediate discount factors and that capacity becomes a strategic "
    "complement, which creates a high-capacity equilibrium that simultaneous pricing rules out. A controlled experiment shows that price commitment, not the timing of "
    "capacity decisions, raises equilibrium capacity. We draw implications for capacity disclosure, switching rules, and repricing frequency, and we mark what the model does not test." % N)
p = doc.add_paragraph(); p.paragraph_format.line_spacing = 1.15; p.paragraph_format.space_after = Pt(10)
rich(p, abstract, size=11)
p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(0)
rich(p, "*Keywords*: cloud computing; generative AI; capacity investment; Bertrand–Edgeworth competition; Markov perfect equilibrium; dynamic oligopoly; IT infrastructure markets", size=11)
page_break(doc)

# =============================== 1. INTRODUCTION ===============================
h1(doc, "1. Introduction")
body(doc, "Between the second half of 2023 and the second half of 2025, the median hourly price of renting an NVIDIA H100 GPU from a large cloud provider fell from "
          "about $7.76 to $6.26, and the median price on GPU marketplaces fell from about $2.58 to $1.95 over a shorter window (Silicon Data 2026). "
          "Over the same period the four largest U.S. cloud and platform firms spent on the order of $410 to $435 billion on capital expenditure in 2025 alone, "
          "most of it directed at data-center capacity, and company guidance for 2026 was higher still (Platformonomics 2026). Capacity was expanding quickly, "
          "prices were falling, and yet price levels across provider types stayed far apart. The pattern raises a question that sits between industrial "
          "organization and information systems (IS): how do price competition and capacity investment interact when new capacity is slow and costly to "
          "install, demand for inference is volatile, and a rival can take customers whenever one's own servers are full?")
body(doc, "The IS and operations literature has long studied the pricing and sizing of computing capacity, but mostly from the perspective of a single "
          "provider or a given set of competitors choosing service levels (Mendelson 1985, Dewan and Mendelson 1990, Cachon and Harker 2002, Allon and Federgruen 2007, "
          "Bapna et al. 2008). The industrial organization literature, in turn, has a sharp theory of capacity-constrained price competition (Levitan and Shubik 1972, "
          "Kreps and Scheinkman 1983, Osborne and Pitchik 1986) and a toolkit for dynamic investment games (Maskin and Tirole 1988, Ericson and Pakes 1995, "
          "Besanko and Doraszelski 2004). What is missing, and what the market for LLM inference makes timely, is the combination: an infrastructure market in which "
          "firms post prices every period, capacity is a lumpy state variable that carries a lag and a sunk cost, and demand shifts between regimes.")
body(doc, "We build that combination as a dynamic game between two providers. In each period a provider chooses a posted price from a finite grid and a discrete "
          "capacity action (hold, add one GPU node, or retire one). Customers buy from the cheaper provider until its capacity binds and then spill over to the "
          "rival, which is the Bertrand–Edgeworth allocation. Capacity chosen today is usable next period, and changing capacity costs a sunk amount, in the spirit of Rust (1987). "
          "We solve for a stationary Markov perfect equilibrium (MPE) with extreme-value payoff shocks, so that the equilibrium is a logit MPE (McKelvey and Palfrey 1995, "
          "Doraszelski and Satterthwaite 2010).")
body(doc, "The paper makes four contributions. First, we show that when prices are not state variables, pricing and capacity separate exactly (Proposition 1). Prices are the "
          "solution to a static logit pricing game in each state, and capacity is the solution to a dynamic game whose flow payoffs come from those prices. This "
          "result is useful analytically and, as we show, computationally. Second, we characterize the pricing game at the two ends of the capacity spectrum. When "
          "installed capacity falls short of demand, posting the reservation price is a dominant strategy (Proposition 2). When both firms can serve the whole market, "
          "the only pure-strategy equilibria are symmetric price pairs whose markup cannot exceed twice the step of the price grid (Proposition 3), which is the Bertrand "
          "paradox in discrete clothing. Third, we compute equilibria for %d parameter settings and compare them with a joint-profit benchmark and with a market-share "
          "contest. Equilibrium capacity always lies between the two benchmarks, but the equilibrium is frequently not unique, and the equilibria that consumers prefer "
          "are not the ones that maximize total surplus. Fourth, we make prices state variables by letting the firms move in alternation and commit to a price until their next "
          "move, as in Maskin and Tirole (1988). In a two-price benchmark we prove that commitment sustains supra-competitive prices for intermediate discount factors "
          "(Proposition 4) and makes capacity a strategic complement, so that a high-capacity equilibrium exists that simultaneous pricing rules out (Proposition 5). "
          "Numerically, commitment produces price cycles and higher prices at fixed capacities, and a controlled timing experiment shows that it is commitment, not the "
          "timing of capacity decisions, that raises equilibrium capacity." % N)
body(doc, "We are careful about what the paper does not do. In the baseline model prices are not payoff-relevant state variables, so the pricing stage is a repeated static game and cannot "
          "generate Edgeworth cycles or tacit collusion; Section 7 relaxes this assumption with alternating moves. The analytical results of that section are for a two-price benchmark "
          "and rest on explicit equilibrium selection; the numerical extension is solved at moderate payoff noise only, because the equilibrium iteration does not converge reliably for "
          "small noise; and price cycles are a numerical finding that we do not prove. The parameters are illustrative. "
          "We compare the model with public data on GPU rental prices, token prices, and capital expenditure, but only qualitatively, and one price ratio is the only parameter that those data "
          "discipline. The numerical results should be read as the output of a transparent, replicable model, not as estimates of the market.")
body(doc, "The remainder of the paper proceeds as follows. Section 2 positions the paper in the literature. Section 3 sets out the model, and Section 4 states the "
          "analytical results. Section 5 reports the base-case equilibria, Section 6 the sensitivity and equilibrium-selection analysis, and Section 7 the extension to dynamic "
          "price competition. Section 8 compares the model with public data. Section 9 draws implications for platform design and policy, Section 10 discusses limitations, and Section 11 concludes. "
          "Proofs and computational details are in the appendices.")

# =============================== 2. RELATED LITERATURE ===============================
h1(doc, "2. Related Literature")
body(doc, "*Pricing and capacity of computing services.* An established IS and operations literature treats computing as a service facility whose users bear delay costs. "
          "Mendelson (1985) and Dewan and Mendelson (1990) study how to price and size internal computing capacity when queueing delays matter, and Cachon and Harker (2002) "
          "and Allon and Federgruen (2007) extend the analysis to competing service providers that choose prices and delay standards. Bapna et al. (2008) design a market for "
          "grid computing resources. Armbrust et al. (2010) frame the economics of elastic cloud capacity. These papers are mostly static or consider one decision-maker; "
          "we add dynamic capacity investment under adjustment frictions among a small number of strategic rivals.")
body(doc, "*Capacity-constrained price competition.* Edgeworth’s observation that capacity limits can destroy pure-strategy price equilibria was formalized by Levitan and "
          "Shubik (1972) and Osborne and Pitchik (1986). Kreps and Scheinkman (1983) showed that when capacity is chosen first and prices second, the outcome is the Cournot "
          "outcome, and Davidson and Deneckere (1986) showed how the result depends on the rationing rule. Our stage game uses efficient rationing, and the same logic "
          "appears in our Propositions 2 and 3: scarcity restores market power, and abundance removes it. What our setting adds is that capacity is chosen repeatedly, with a lag and "
          "a sunk cost, while demand is stochastic.")
body(doc, "*Dynamic oligopoly and computation.* Maskin and Tirole (1988) analyze Markov-perfect price competition and show that Edgeworth cycles can arise when firms "
          "alternate moves and prices are state variables. Ericson and Pakes (1995) and Pakes and McGuire (1994) provide the framework for computing MPE with investment, and "
          "Besanko and Doraszelski (2004) apply it to capacity dynamics and endogenous size asymmetries. Doraszelski and Satterthwaite (2010) show how extreme-value shocks "
          "ensure existence, and Besanko et al. (2010) document multiple equilibria in related dynamic models. The structural-estimation side of this literature, from Rust (1987) "
          "to Aguirregabiria and Mira (2007) and Bajari, Benkard, and Levin (2007), indicates how a model like ours could be taken to data. Our contribution relative to this "
          "work is the separation result and its application to an IT infrastructure market.")

# =============================== 3. MODEL ===============================
h1(doc, "3. Model")
h2(doc, "3.1 State, demand, and timing")
body(doc, "Two providers, *i* ∈ {A, B}, operate in discrete time. Provider *i* owns *m*_{i} ∈ {0, 1, …, *M* − 1} GPU nodes, each of which can serve κ requests per period, "
          "so its capacity is *K*_{i} = κ*m*_{i}. Aggregate demand is a number of requests per period, λ ∈ {10, 25, 45} (low, medium, high), and the regime follows a Markov "
          "chain with transition matrix *P*_{λ}. The payoff-relevant state is")
eq(doc, "*S* = (*m*_{A}, *m*_{B}, λ).", "1")
body(doc, "In each period both providers observe *S* and simultaneously choose an action *a*_{i} = (*p*_{i}, *k*_{i}), where *p*_{i} is a posted price from a finite grid "
          "\U0001D4AB = {0.4, 0.8, 1.2, 1.5} (the largest value, p̄ = 1.5, is customers’ reservation price) and *k*_{i} ∈ {0, 1, 2} is hold, expand, or contract. "
          "Capacity follows")
eq(doc, "*m*_{i}′ = max{0, min{*M* − 1, *m*_{i} + 1[*k*_{i} = 1] − 1[*k*_{i} = 2]}},", "2")
body(doc, "so that a node added in period *t* serves customers from period *t* + 1 on. This is the provisioning lag. Changing capacity costs *FC*_{i} for an expansion and "
          "0.3*FC*_{i} for a contraction, paid in the period of the decision.")
h2(doc, "3.2 Allocation and payoffs")
body(doc, "Customers are homogeneous and, up to the reservation price, inelastic. Directed demand to provider *i* is *d*_{i} = λ if *p*_{i} < *p*_{j}, λ/2 if *p*_{i} = *p*_{j}, and 0 "
          "otherwise. Each provider serves its directed demand up to its capacity, and customers rejected by one provider move to the other at no cost, so that")
eq(doc, "*q*_{i} = min{*K*_{i}, *d*_{i} + max(0, *d*_{j} − *K*_{j})}.", "3")
body(doc, "The assumption of costless spillover is deliberate. It is the frictionless-switching benchmark, and we return to it when we discuss portability remedies in Section 9. "
          "Period profit is")
eq(doc, "Π_{i} = (*p*_{i} − *c*)*q*_{i} − ψ max(0, *d*_{i} − *K*_{i}) − *P*_{k}*m*_{i} − AC_{i}(*k*_{i}),", "4")
body(doc, "where *c* is the marginal serving cost, ψ is a service-level penalty per request that a provider was asked to serve but could not, *P*_{k} is the holding cost of a node, and "
          "AC_{i}(*k*) is the adjustment cost just described. Two features of (4) matter for what follows. Profit does not depend on the capacity action except through AC_{i}, and "
          "prices do not enter the law of motion (2).")
h2(doc, "3.3 Equilibrium")
body(doc, "Each provider also receives an additive payoff shock ε_{i}(*a*) for every joint action *a* = (*p*, *k*), drawn independently over actions, periods, and providers from a Type I "
          "extreme-value distribution with scale ρ. A stationary MPE consists of strategies σ_{i}(*a* | *S*) and value functions *V*_{i}(*S*) such that, with discount factor β,")
eq(doc, "*v*_{i}(*a* | *S*) = Σ_{a_{j}} σ_{j}(*a*_{j} | *S*) [ Π_{i}(*S*, *a*, *a*_{j}) + β Σ_{λ′} *P*_{λ}(λ′ | λ) *V*_{i}(*m*_{i}′, *m*_{j}′, λ′) ],", "5")
eq(doc, "σ_{i}(*a* | *S*) = exp(*v*_{i}(*a* | *S*)/ρ) / Σ_{a′} exp(*v*_{i}(*a*′ | *S*)/ρ),    *V*_{i}(*S*) = ρ [ γ + ln Σ_{a} exp(*v*_{i}(*a* | *S*)/ρ) ],", "6")
body(doc, "where γ is Euler’s constant. The logit form serves two purposes. It matches the extreme-value assumption that is standard in the structural dynamic-game literature, and it "
          "guarantees that an equilibrium exists in the pricing game even in states where no pure-strategy equilibrium does, which is the Edgeworth problem. As ρ shrinks, "
          "behavior approaches best-response behavior.")
h2(doc, "3.4 Benchmarks and parameters")
body(doc, "We compare the equilibrium with two benchmarks. The *joint-profit benchmark* has a single decision-maker choose both firms’ prices and capacity actions to maximize the sum "
          "of profits, with no shocks; it stands in for the outcome of perfect coordination. The *market-share contest* replaces the pricing game by a single posted price and splits "
          "demand in proportion to installed capacity, *d*_{i} = λ*m*_{i}/(*m*_{i} + *m*_{j}) (equal split if both are zero), a reduced form that is common in capacity-race models. "
          "Both use the same cost parameters and state space. Table 1 lists the parameters. They are illustrative, and Section 6 varies each of them.")
caption(doc, "Table 1. Parameters of the base scenario.")
table(doc, ["Parameter", "Symbol", "Value"],
      [["Requests served per node per period", "κ", "15"],
       ["Demand regimes (low, medium, high)", "λ", "10, 25, 45"],
       ["Regime transition matrix (rows: from low, medium, high)", "*P*_{λ}", "(.7, .2, .1), (.2, .6, .2), (.1, .3, .6)"],
       ["Price grid / reservation price", "\U0001D4AB / p̄", "{0.4, 0.8, 1.2, 1.5} / 1.5"],
       ["Marginal serving cost", "*c*", "0.3"],
       ["Node holding cost per period", "*P*_{k}", "2"],
       ["Expansion cost (A, B); contraction share", "*FC*_{A}, *FC*_{B}", "12, 15; 0.3"],
       ["Penalty per directed-but-unserved request", "ψ", "0.3"],
       ["Discount factor", "β", "0.95"],
       ["Scale of payoff shocks", "ρ", "1"],
       ["Nodes per firm", "*M* − 1", "4 (so 0 to 4 nodes)"]],
      [3.6, 1.1, 1.8])
note(doc, "Note. The model has 75 states (5 × 5 nodes, 3 demand regimes). Each firm has 12 actions (4 prices × 3 capacity actions).")

# =============================== 4. ANALYSIS ===============================
h1(doc, "4. Analytical Results")
body(doc, "The first result is structural. It holds under two maintained properties of the model: prices do not affect the transition of the state, and the capacity action does "
          "not affect current profit except through its own adjustment cost.")
p = body(doc, "**Proposition 1 (Separation).** Every logit MPE has the product form σ_{i}(*p*, *k* | *S*) = σ_{i}^{P}(*p* | *S*) σ_{i}^{K}(*k* | *S*). The pricing component "
              "σ^{P} is a logit quantal-response equilibrium of the static game with payoffs Π_{i}(*S*, *p*_{i}, *p*_{j}) in each state, and the capacity component σ^{K} is a logit MPE "
              "of a dynamic capacity game in which firm *i* has flow payoff −AC_{i}(*k*_{i}), plus the pricing component’s inclusive value, and continuation values as in (5).", indent=True)
# remove the markdown-style bold markers from the line above (typeset as bold run instead)
for r in list(p.runs):
    pass
body(doc, "The proof is in Appendix A. The intuition is that, because the rival’s price affects my payoff only through the stage profit and the rival’s capacity action affects it only "
          "through the continuation value, my expected payoff from an action (*p*, *k*) is the sum of a term in *p* and a term in *k*. With independent extreme-value shocks, additively "
          "separable payoffs produce independent logit choices. Computationally, the result replaces a 12 × 12 game in each state with a 4 × 4 pricing game, solved once, and a "
          "3 × 3 capacity game, solved inside the value iteration. We verify that the two solution methods agree to five decimals in Section 5.")
body(doc, "The next two results describe the pricing game at its extremes. Let *K*_{i} = κ*m*_{i} denote installed capacity in the current state.")
body(doc, "**Proposition 2 (Scarcity).** Suppose *K*_{A} + *K*_{B} ≤ λ and *K*_{i} > 0. Then the reservation price p̄ strictly dominates every lower price for firm *i* in the stage game. "
          "Consequently, in the logit equilibrium p̄ is firm *i*’s modal price, and its probability tends to one as ρ → 0.")
body(doc, "**Proposition 3 (Abundance).** Suppose *K*_{A} ≥ λ and *K*_{B} ≥ λ, and let *p*_{min} > *c* be the lowest grid price. The pure-strategy Nash equilibria of the stage game are "
          "exactly the symmetric pairs (*p*, *p*) in which either *p* = *p*_{min} or the next lower grid price *p*⁻ satisfies *p*⁻ − *c* ≤ (*p* − *c*)/2. In particular, any pure-strategy "
          "equilibrium price *p* above *p*_{min} has *p* − *c* ≤ 2(*p* − *p*⁻), twice the local step of the price grid.")
body(doc, "Proposition 2 is the Kreps–Scheinkman logic in our setting. When the market cannot be served by both firms together, undercutting wins no extra volume, so the high price is "
          "free. Proposition 3 is the Bertrand paradox. If either firm could serve everybody, the other firm’s price is the only thing that matters, and the only equilibria are "
          "symmetric. The markup that survives is bounded by the coarseness of the grid, so with a fine grid it vanishes. We will see in Section 6 that this has consequences for how robust "
          "the capacity results are. Taken together, the propositions say that in this market capacity is the only source of market power. A firm earns margin when, and only when, total "
          "installed capacity is short of demand, and any additional node a firm builds raises its holding cost while eroding the margin it earns on the nodes it already has.")
body(doc, "The propositions do not by themselves tell us how much capacity firms will build or how many equilibria exist. For that we compute.")

# =============================== 5. BASE-CASE RESULTS ===============================
h1(doc, "5. Base-Case Equilibria")
h2(doc, "5.1 Computation")
body(doc, "We solve the model by nested fixed point. The pricing game in each of the 75 states is solved as a logit quantal-response equilibrium by damped best-response iteration. The capacity "
          "game is then solved inside a value iteration, with the 3 × 3 stage game in each state solved by the same iteration. Value updates are damped (step 0.3) and we stop "
          "when the largest change in any value is below 10^{−4}. A reference implementation that solves the full 12 × 12 game directly produces the same equilibrium to five "
          "decimals in the base scenario (average price 1.12607, industry profit 12.9059, mean capacity 59.7798), which is a numerical check on Proposition 1. Because the model may have "
          "several equilibria, we run each scenario from one uniform starting point and three random starting points. Appendix B gives the details, and the code accompanies the paper (see the Replication Note).")
h2(doc, "5.2 Prices and capacity in the base scenario")
body(doc, "Figure 1 shows the equilibrium expected price by state. The pattern is the one Propositions 2 and 3 predict. The price sits at the reservation price whenever total capacity is "
          "short of demand, which in the high-demand regime covers every pair with up to three nodes in total. It falls to about 0.8 once both firms hold enough capacity to serve the "
          "current regime alone, and with low demand the price is already near 0.8 as soon as each firm has one node. Capacity acts as a commitment to compete: the more capacity a rival "
          "holds, the lower the price a firm can sustain.")
doc.add_picture(R + "price_by_state.png", width=Inches(6.4))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
caption(doc, "Figure 1. Equilibrium expected posted price by number of nodes (A on the vertical axis, B on the horizontal axis) and demand regime, base scenario, equilibrium reached from the uniform start.")
body(doc, "The base scenario has two stationary outcomes, which differ mainly in how much capacity the firms hold. Table 2 shows behavior at selected states in each. In the *capacity-heavy* "
          "equilibrium, reached from the uniform starting point, the firms end up with about two nodes each (59.8 request-units of capacity on average). In the *capacity-scarce* equilibrium, "
          "reached from many random starting points, the firms end up with one node and two nodes, so that total capacity (45.0) equals peak demand and the firms are asymmetric in size, "
          "although their adjustment costs differ only modestly. Size asymmetry that arises without any difference in fundamentals is a familiar feature of dynamic capacity games "
          "(Besanko and Doraszelski 2004), and which firm is large depends on the equilibrium selected.")
def cap_str(x): return "/".join("%.2f" % v for v in x["capacity"])
def srow(key):
    a, b = EH["states"][key], EL["states"][key]
    return [key, "%.2f" % a["A"]["E_price"], cap_str(a["A"]) + " | " + cap_str(a["B"]), "%.2f" % b["A"]["E_price"], cap_str(b["A"]) + " | " + cap_str(b["B"])]
caption(doc, "Table 2. Equilibrium behavior at selected states in the two base-scenario equilibria.")
table(doc, ["State (*m*_{A}, *m*_{B}, λ)", "Capacity-heavy: E[price]", "Hold / expand / contract (A | B)", "Capacity-scarce: E[price]", "Hold / expand / contract (A | B)"],
      [srow(k) for k in ["(1,1,Med)", "(1,1,High)", "(2,1,High)", "(2,2,Med)", "(2,2,High)", "(3,3,Med)"]],
      [1.15, 0.95, 1.7, 0.95, 1.7], size=9)
note(doc, "Note. Expected price is identical for the two firms in these states. Probabilities are those of the logit equilibrium strategies.")
body(doc, "Three features of Table 2 deserve mention. First, expansion occurs when capacity is short relative to demand: in the capacity-heavy equilibrium at state (1,1) with high demand, "
          "A expands with certainty and B with probability 0.27; in the medium-demand state only B expands. Second, there is no capacity race in the sense of both firms expanding "
          "simultaneously when one expansion would suffice: the joint probability of two simultaneous expansions is at most 0.27 in any state shown and is essentially zero in the stationary "
          "distribution. Third, when capacity is redundant, as at (3,3) with medium demand, nodes are retired: both firms do so with probability 0.95 in the capacity-heavy equilibrium, and in the capacity-scarce one the smaller firm retires a node with probability 0.99 while the larger firm holds. That is the shakeout one would expect, although it need not be symmetric.")
h2(doc, "5.3 Comparison with the benchmarks")
caption(doc, "Table 3. Stationary averages under the ergodic distribution of each equilibrium (base scenario).")
def col(d, cartel=False):
    cs = d["consumer_surplus"]
    return [f2(d["avg_price"]), f2(d["profit_total"]), f2(cs), f2(d["profit_total"] + cs), f1(d["mean_capacity"]), f1(d["excess_capacity"]),
            "%.1f / %.1f" % (d["mean_nodes_A"], d["mean_nodes_B"])]
labels = ["Average transaction price", "Industry profit per period", "Consumer surplus per period", "Total surplus per period", "Mean installed capacity", "Mean excess capacity", "Mean nodes (A / B)"]
cH, cL, cC, cS = col(hiX), col(loX), col(cart), col(shr)
table(doc, ["", "Bertrand MPE, capacity-heavy", "Bertrand MPE, capacity-scarce", "Joint-profit benchmark", "Market-share contest"],
      [[labels[i], cH[i], cL[i], cC[i], cS[i]] for i in range(len(labels))], [2.0, 1.1, 1.1, 1.1, 1.1], size=9)
note(doc, "Note. Consumer surplus is (p̄ − *p*)*q* summed over firms. Excess capacity is E[max(κ(*m*_{A} + *m*_{B}) − λ, 0)]. The joint-profit and contest rows are computed from the "
          "uniform starting point only.")
body(doc, "Three comparisons stand out. Price competition transfers surplus to consumers: consumers receive %s in the capacity-heavy equilibrium and %s in the capacity-scarce one, against nothing "
          "under either benchmark, because both of those charge the reservation price. Industry profit in the two Bertrand equilibria is %.0f%% and %.0f%% of the joint-profit level. "
          "Installed capacity under Bertrand pricing is between that of the joint-profit benchmark (45.0) and that of the contest (%.1f). The contest overbuilds by a wide margin because "
          "capacity is the only way to win share, whereas under price competition an extra node mostly intensifies the price war."
          % (f2(hiX["consumer_surplus"]), f2(loX["consumer_surplus"]), 100 * hiX["profit_total"] / cart["profit_total"], 100 * loX["profit_total"] / cart["profit_total"], shr["mean_capacity"]))
body(doc, "The two Bertrand equilibria rank differently. Consumers prefer the capacity-heavy equilibrium (consumer surplus %s versus %s). Total surplus, which here is profit plus consumer "
          "surplus, is higher in the capacity-scarce equilibrium (%s versus %s), because served demand is the same in the two and the capacity-heavy equilibrium carries about one more node, "
          "at a holding cost of 2 per period, plus the associated adjustment costs. The efficiency loss from the extra capacity is about %.1f%% of total surplus. A regulator or platform designer "
          "who cares about consumers and one who cares about total surplus would therefore select different equilibria, a point we return to in Section 9."
          % (f2(hiX["consumer_surplus"]), f2(loX["consumer_surplus"]), f2(W_L), f2(W_H), 100 * (W_L - W_H) / W_L))

# =============================== 6. ROBUSTNESS ===============================
h1(doc, "6. Sensitivity and Equilibrium Selection")
body(doc, "We vary the scale of the payoff shocks, marginal cost, adjustment costs, the discount factor, the service-level penalty, the demand process, and the price grid, one at a time around the base "
          "scenario, for %d scenarios in all. Each scenario is solved from the uniform starting point and from three random starting points, and we report the range of outcomes across the equilibria found. "
          "In the base scenario we also ran twelve additional random starts; five converged to the capacity-heavy outcome and seven to the capacity-scarce one, and no other outcome appeared. Table 4 "
          "and Figure 2 summarize the results." % N)
def cell_range(t, fmt):
    lo, hi = t
    a, b = fmt(lo), fmt(hi)
    return a if a == b else "%s–%s" % (a, b)
srows = []
for r in rows:
    pr = (r["profit_total"][0] / r["cartel_profit"], r["profit_total"][1] / r["cartel_profit"])
    nm = r["name"].replace("rho=", "ρ = ").replace("beta=", "β = ").replace("fc x", "*FC* × ").replace("fc symmetric (13.5,13.5)", "*FC* equal (13.5, 13.5)").replace("mc=", "*c* = ").replace("sla=", "ψ = ").replace("grid ", "price grid: ").replace("price ratio 0.31 (8 prices)", "price grid: 8 prices, floor/ceiling = 0.31").replace("demand ", "demand: ")
    srows.append([nm, str(r["n_eq"]) + ("*" if r["n_unconverged"] else ""), cell_range(r["avg_price"], f2), cell_range(r["mean_capacity"], f1), f1(r["cartel_cap"]) + " / " + f1(r["contest_cap"]),
                  cell_range(r["consumer_surplus"], f2), cell_range(pr, lambda x: "%.0f%%" % (100 * x))])
caption(doc, "Table 4. Equilibrium outcomes across %d scenarios. Ranges are over the equilibria found." % N)
table(doc, ["Scenario", "Distinct outcomes", "Avg. price", "Mean capacity", "Cartel / contest capacity", "Consumer surplus", "Industry profit, % of cartel"], srows,
      [1.85, 0.7, 0.8, 0.85, 0.95, 0.85, 0.9], size=8)
note(doc, "Note. Distinct outcomes are counted by rounding mean capacity and average price. An asterisk marks scenarios in which at least one run did not meet the convergence tolerance (%s). "
          "Demand scenarios change the stationary mean of λ (base 25.3; persistent 26.5; i.i.d. 26.7; growth-skewed 33.2), so their levels are not directly comparable with the base scenario." % "; ".join("%s: %d of 4 runs" % (r["name"], r["n_unconverged"]) for r in rows if r["n_unconverged"]))
doc.add_picture(R + "sensitivity_capacity.png", width=Inches(5.6))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
caption(doc, "Figure 2. Mean installed capacity in the Bertrand equilibria found (circles, joined when more than one), the joint-profit benchmark (diamonds), and the market-share contest (squares). Where a circle is hidden behind a diamond, the Bertrand outcome equals the joint-profit capacity.")
body(doc, "Four findings are robust, and two are not. The robust ones come first.")
body(doc, "*Ordering.* In all %d scenarios, equilibrium capacity under Bertrand competition is at least as large as the joint-profit benchmark and no larger than the contest. The contest "
          "holds between %.0f and %.0f request-units more capacity than the Bertrand equilibria, depending on the scenario, and in several scenarios it comes close to the maximum the state space allows "
          "(120). Price competition does not eliminate excess capacity, but it weakens the capacity race that a share rule induces." % (N, gaps_min, gaps_max))
body(doc, "*Scarcity pricing.* The condition of Proposition 2 holds in every state we checked in every scenario. The reservation price is strictly dominant and is the modal price in all of them. "
          "The result is exact and does not depend on the numerical parameters.")
body(doc, "*Multiplicity.* %d of the %d scenarios have two or more distinct equilibrium outcomes. In every one of them the outcomes differ in capacity, and in each the high-capacity outcome is better for "
          "consumers and worse for total surplus. Multiplicity is therefore a feature of the model, not an artifact of one parameter choice." % (len(multi), N))
body(doc, "*Profit dissipation.* Industry profit under Bertrand competition is between %.0f%% and %.0f%% of the joint-profit level across scenarios, so competition always costs the firms a substantial share of "
          "what coordination would earn."
          % (100 * min(r["profit_total"][0] / r["cartel_profit"] for r in rows), 100 * max(r["profit_total"][1] / r["cartel_profit"] for r in rows)))
body(doc, "The two results that are *not* robust matter just as much. First, the capacity-heavy equilibrium is fragile. It disappears, and only the capacity-scarce outcome remains, when the price "
          "grid is refined to eight or sixteen points, when marginal cost is very low (0.1) or high (0.4), and when the service-level penalty is zero. (With a higher penalty, ψ = 0.6, the reverse happens: only the capacity-heavy outcome was found, so ψ affects which equilibrium is reached.) The grid result is what Proposition 3 leads one to expect: in states "
          "where both firms have ample capacity, the margin that makes a second node worthwhile is a product of coarse price steps, and a finer grid removes much of it. We have no analogous argument for the marginal-cost and penalty cases. We therefore regard the "
          "capacity-heavy equilibrium as an artifact of discretization in part, and we place more weight on the finding that Bertrand capacity lies at or above the joint-profit level than on any "
          "specific amount above it. Second, we had expected the expected price to fall weakly as the rival adds capacity. This holds exactly in %d of %d scenarios, but it fails by small amounts "
          "in the other %d (finer grids, large payoff shocks, and a high service-level penalty). We therefore state it as an empirical regularity in the base case, not as a proposition."
          % (N - len(mono_fail), N, len(mono_fail)))
body(doc, "Finally, convergence was a practical issue. Of %d solver runs, %d did not meet the tolerance of 10^{−4} within the iteration limit (%s). Their results are included in Table 4, "
          "but they should be treated with caution." % (N * 4, unconv_runs, ", ".join("%s: %d" % (r["name"].replace("rho=", "ρ = ").replace("fc x", "FC × "), r["n_unconverged"]) for r in rows if r["n_unconverged"])))


# =============================== 7. DYNAMIC PRICE COMPETITION ===============================
pg = json.load(open(R + "price_game.json"))
jsens = json.load(open(R + "joint_dynamic_sens.json"))
jstart = json.load(open(R + "joint_dynamic_starts.json"))
jdyn = json.load(open(R + "joint_dynamic.json"))
import collections
by = collections.OrderedDict()
for r_ in jsens:
    by.setdefault(r_["name"], {"alt": [], "sim": []})[r_["kind"]].append(r_)
rg = lambda xs, k: (min(x[k] for x in xs), max(x[k] for x in xs))
alt_ok = [n_ for n_, v in by.items() if all(x["converged"] for x in v["alt"])]
alt_bad = [n_ for n_ in by if n_ not in alt_ok]
strict = [n_ for n_ in alt_ok if rg(by[n_]["alt"], "mean_capacity")[0] > rg(by[n_]["sim"], "mean_capacity")[1] + 0.05]
weak = [n_ for n_ in alt_ok if rg(by[n_]["alt"], "mean_capacity")[0] >= rg(by[n_]["sim"], "mean_capacity")[0] - 0.2]
profit_lower = [n_ for n_ in alt_ok if rg(by[n_]["alt"], "profit_total")[1] < rg(by[n_]["sim"], "profit_total")[0]]
profit_higher = [n_ for n_ in alt_ok if rg(by[n_]["alt"], "profit_total")[0] > rg(by[n_]["sim"], "profit_total")[1]]
print("dyn-pricing joint:", len(by), "alt ok", len(alt_ok), "strict", len(strict), "weak", len(weak), "profit lower", len(profit_lower), "higher", len(profit_higher), "alt bad", alt_bad)
assert len(weak) == len(alt_ok)
a0 = [r_ for r_ in jstart["alternating"] if r_["converged"]]; s0 = jstart["simultaneous"]
assert len(set(round(r_["mean_capacity"], 1) for r_ in a0)) == 1 and len(a0) == len(jstart["alternating"])

h1(doc, "7. Dynamic Price Competition")
h2(doc, "7.1 Alternating commitments")
body(doc, "In the baseline model both firms choose prices simultaneously every period, so a price is gone as soon as the period ends. Real platforms reprice less often than they could, and a price posted today "
          "stays in force while rivals respond. Maskin and Tirole (1988) capture this with alternating moves: firms take turns, and the price a firm sets remains fixed for its rival’s next move. Prices "
          "then become state variables, and equilibrium behavior can depend on the history of prices through the state, which is what allows undercutting cycles and prices above the static Bertrand level.")
body(doc, "We adopt this protocol while keeping the rest of the model unchanged. In each period exactly one firm, the mover *q*, is active and the roles alternate. The mover chooses a price and a capacity action "
          "(*p*, *k*); its price then stays in force until its next move two periods later. Both firms earn the flow profit (4) every period from the prices currently in force. The state seen by the mover is "
          "(*m*_{A}, *m*_{B}, λ, *p*_{r}), where *p*_{r} is the rival’s committed price. The mover’s own old price is payoff-irrelevant, because it is re-chosen. With the same extreme-value shocks, the mover’s "
          "choice-specific value is")
eq(doc, "*v*_{q}(*p*, *k* | *S*, *p*_{r}) = Π_{q}(*m*, *p*, *p*_{r}) − AC_{q}(*k*) + β Σ_{λ′} *P*_{λ}(λ′ | λ) *V*_{q}^{r}(*m*′, λ′, *p*),", "7")
eq(doc, "*V*_{q}^{q}(*S*, *p*_{r}) = ρ [ γ + ln Σ_{a} exp(*v*_{q}(*a*)/ρ) ],    *V*_{r}^{q}(*S*, *p*_{r}) = Σ_{a} σ_{q}(*a* | *S*, *p*_{r}) [ Π_{r}(*m*, *p*, *p*_{r}) + β Σ_{λ′} *P*_{λ}(λ′ | λ) *V*_{r}^{r}(*m*′, λ′, *p*) ],", "8")
body(doc, "where *V*_{i}^{s} is the value to firm *i* when firm *s* is about to move and *m*′ reflects the mover’s capacity action. Two features of this protocol matter for interpretation. Prices are now committed, "
          "which softens competition by itself, and each firm adjusts capacity only every second period, which changes the pace of investment. We do not separate these effects.")
body(doc, "The equilibrium operator in (7) and (8) is not a contraction, and plain value iteration converges to a unique outcome only for large payoff noise. At ρ = 2 it converges, to the same outcome, from all nine "
          "starting points we tried; for smaller ρ it cycles. We therefore use two routes. For the fixed-capacity analysis, the game has only 96 unknowns, and we track the equilibrium from ρ = 4 down to ρ = 0.1 by "
          "Newton continuation. For the joint game with capacity, we report ρ = 2 and compare it with simultaneous pricing at the same ρ and the same eight-point price grid (0.4 to 1.5).")

tc = json.load(open(R + "theory_checks.json"))
h2(doc, "7.2 An analytical benchmark with two prices")
body(doc, "To see what drives the numerical results, we strip the model down. There are two prices, *L* < *H*, with margins *m*_{L} = *L* − *c* and *m*_{H} = *H* − *c*; demand is a constant *D* per period; the "
          "service-level penalty is zero; and capacities are fixed. Write *l* = *m*_{L}*D*/2 and *h* = *m*_{H}*D*/2 for the per-period profit of each firm when both post *L* and when both post *H*, and let *r* = *h*/*l* = *m*_{H}/*m*_{L}. "
          "We take 1 < *r* < 2, the case in which undercutting is statically profitable: a firm that undercuts a rival at *H* earns *m*_{L}*D* = 2*l* > *h*, so with ample capacity the simultaneous-move game has the "
          "unique equilibrium (*L*, *L*), the Bertrand paradox. Under alternating moves a pure Markov strategy maps the rival’s committed price into the mover’s own price. Two strategies matter: *always-L*, and *matching*, which plays the rival’s price.")
body(doc, "**Proposition 4 (Commitment and tacit collusion).** Let both firms have ample capacity (*K*_{i} ≥ *D*) and 1 < *r* < 2. (a) Always-*L* is a Markov perfect equilibrium for every β. (b) Matching is a "
          "Markov perfect equilibrium if and only if 2 − *r* ≤ β ≤ 1/*r*, and each firm then earns *h* per period, the full collusive profit. (c) Always-*H* and the profile that plays *H* against *L* and *L* against *H* are not equilibria, "
          "so no symmetric pure profile generates a price cycle.")
body(doc, "Part (b) shows that commitment alone can support tacit collusion without any explicit threat, and the two bounds have different meanings. The lower bound is the usual one: the firms must be patient enough that the "
          "gain from undercutting, which lasts one period before the rival matches, does not exceed the loss from the resulting price war. The upper bound is specific to Markov strategies. If firms are very patient, a firm facing a rival at *L* "
          "prefers to restore the high price, because the rival, who matches, follows one move later. Matching is then not credible, and the equilibrium unravels. Collusion is therefore sustainable for intermediate discount factors only, "
          "which is the kind of restoration incentive that underlies Edgeworth cycles. The result is verified by exhaustive enumeration: all 16 pure profiles at each of %d grid points in (*r*, β) give exactly the equilibrium set stated in (a) and (b), with %d mismatches "
          "(Appendix B). With asymmetric capacities, pure cycles do exist: when one firm is scarce and the other ample, the profile in which the scarce firm matches and the ample firm plays the opposite price generates a four-move cycle, "
          "and it is an equilibrium for small β (in our enumeration for β ≤ *r* − 1 when *r* ≤ 1.5), but not in the range of β on which Proposition 5 relies."
          % (tc["prop4"]["points"], len(tc["prop4"]["mismatches"])))
body(doc, "The second result concerns the capacity decision. Let each firm choose once whether to be *scarce*, with capacity *D*/2, or *ample*, with capacity *D*, at an extra holding cost φ > 0 per period. "
          "Capacity is long-lived, so the payoff from a capacity pair is the per-period profit in the steady state of the pricing equilibrium that is played. Both firms scarce means total capacity equals demand, and by the argument of "
          "Proposition 2 each posts *H* and earns *h*. For the mixed pair, let *A* be scarce and *B* ample. Matching and always-*L* are replaced by the profile *E1*: the scarce firm always posts *L*, and the ample firm posts *H* against *L* and *L* against *H*. "
          "In *E1* the scarce firm earns *l* and the ample firm earns *h*, the same payoffs as in the unique (mixed) equilibrium of the simultaneous-move game.")
caption(doc, "Table 5. Per-period payoffs from capacity choices in the two-price benchmark (first entry: row firm).")
table(doc, ["Capacities", "Simultaneous pricing", "Alternating (committed) pricing"],
      [["(scarce, scarce)", "*h*, *h*", "*h*, *h*"],
       ["(ample, scarce)", "*h* − φ, *l*", "*h* − φ, *l*  (profile *E1*)"],
       ["(ample, ample)", "*l* − φ, *l* − φ", "*h* − φ, *h* − φ  (matching)"]],
      [1.6, 2.2, 2.7], size=10)
note(doc, "Note. 1 < *r* < 2. The alternating-pricing column uses matching in (ample, ample) and *E1* in (ample, scarce), which requires max(2 − *r*, *r* − 1) ≤ β ≤ min(1/*r*, (2 − *r*)/(*r* − 1)).")
body(doc, "**Proposition 5 (Capacity as a strategic complement).** Suppose 1 < *r* ≤ (1 + √5)/2 and max(2 − *r*, *r* − 1) ≤ β ≤ min(1/*r*, (2 − *r*)/(*r* − 1)); this interval is nonempty exactly when *r* ≤ (1 + √5)/2. "
          "(a) With simultaneous pricing, scarce capacity is strictly dominant, and (scarce, scarce) is the unique equilibrium of the capacity game. "
          "(b) With alternating pricing, with matching played in (ample, ample) and *E1* in the mixed pairs, (scarce, scarce) is an equilibrium, (ample, ample) is an equilibrium if and only if φ ≤ *h* − *l*, and the mixed pairs are not equilibria. "
          "(c) If φ > *h* − *l*, (ample, ample) is not an equilibrium outcome under any pricing continuation whose outcome settles on constant prices.")
body(doc, "Proposition 5 explains the numerical capacity result. Under simultaneous pricing the return to ample capacity is −φ whatever the rival does, because ample capacity buys nothing against an ample rival, so firms stay scarce, and total capacity equals peak demand, "
          "as in the capacity-scarce equilibrium of Section 5. Under committed pricing the return to ample capacity is −φ against a scarce rival but *h* − *l* − φ against an ample one: the extra margin that survives in the collusive "
          "equilibrium is worth defending, so one firm’s expansion makes the other’s more attractive. Capacity decisions become strategic complements, and a high-capacity equilibrium appears in which both firms are worse off than in the scarce one (*h* − φ < *h*). "
          "That is a capacity race in the sense of the introduction, and it is generated by commitment, not by a market-share rule. Two caveats apply. The (scarce, scarce) equilibrium also remains, so Proposition 5 shows that a high-capacity equilibrium exists, "
          "not that it is selected; and it requires the pricing subgames to be played on the stated profiles, which is an equilibrium-selection assumption that the numerics of Section 7.4 do not need.")

h2(doc, "7.3 Fixed capacities: numerical price dynamics")
body(doc, "Holding capacities fixed isolates the pricing dynamics. Figure 3 plots the equilibrium path in which each mover plays its most likely price, at ρ = 0.1, with the demand regime held fixed. "
          "With scarce capacity (one node each) and medium demand, both firms post the reservation price in every period, as in Proposition 2. With ample capacity (three nodes each) and medium demand, the path is "
          "an Edgeworth cycle. The firms undercut each other one grid step at a time, from 1.50 down to 0.87; then one firm undercuts to the floor price of 0.40, and the rival restores the price to 1.50, "
          "after which undercutting resumes. The cycle lasts six moves. With ample capacity and high demand, both firms stay at the floor price and no cycle appears. We have no closed-form account of why the "
          "cycle disappears at high demand, and we report it as a numerical finding.")
body(doc, "The cycles are not a robust property of the model. If demand is held constant at the medium level, the equilibrium at \u03c1 = 0.1 is a price war at the floor price and no cycle appears; with demand constant at the high level, a four-move "
          "cycle appears instead; and with the three-regime demand process of the baseline, the cycle appears at medium demand. In a deterministic game with constant demand and zero marginal cost, an exhaustive search over symmetric pure profiles with four to six equally "
          "spaced prices found no cyclic equilibrium, so the cycles reported here involve demand risk or mixed behavior and cannot be taken as a general result. We use them to illustrate the mechanism, not to establish it.")
doc.add_picture(R + "edgeworth_cycle.png", width=Inches(6.5))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
caption(doc, "Figure 3. Equilibrium price paths under alternating moves at fixed capacities, ρ = 0.1. Each firm’s price stays in force until its next move. Demand regime is held fixed.")
def pg_row(a, b, rho):
    c = [c_ for c_ in pg["cases"] if (c_["mA"], c_["mB"]) == (a, b) and c_["rho_target"] == rho][0]
    A, S_ = c["alt"], c["static"]
    return ["(%d, %d)" % (a, b), "%.1f" % rho, f2(A["avg_price"]), f2(S_["avg_price"]), f2(A["profit_total"]), f2(S_["profit_total"]), f2(A["consumer_surplus"]), f2(S_["consumer_surplus"])]
caption(doc, "Table 6. Dynamic (alternating-move) versus simultaneous-move pricing at fixed capacities.")
table(doc, ["Nodes (*m*_{A}, *m*_{B})", "ρ", "Avg. price: dynamic", "Avg. price: simult.", "Profit: dynamic", "Profit: simult.", "Cons. surplus: dynamic", "Cons. surplus: simult."],
      [pg_row(1, 1, 1.0), pg_row(2, 2, 1.0), pg_row(3, 3, 1.0), pg_row(1, 3, 1.0), pg_row(1, 1, 0.1), pg_row(3, 3, 0.1), pg_row(1, 3, 0.1)],
      [1.0, 0.4, 0.8, 0.8, 0.75, 0.75, 0.85, 0.85], size=8)
note(doc, "Note. Averages are over the ergodic distribution of the demand regime and prices. Profit is industry profit net of node holding costs, which are 2 per node and so are 12 with three nodes each; "
          "negative profit for simultaneous pricing with ample capacity reflects those costs. The case (2, 2) did not converge below ρ ≈ 0.32 and is shown at ρ = 1 only.")
cc = [c_ for c_ in pg["cases"] if (c_["mA"], c_["mB"]) == (3, 3) and c_["rho_target"] == 0.1][0]
body(doc, "Table 6 compares dynamic with simultaneous pricing at the same capacities and the same noise. The dynamic average price is higher at every capacity pair we solved. The gap is small when capacity is scarce "
          "(1.41 against 1.35 at one node each when ρ = 1), and it is largest when capacity is ample: with three nodes each the dynamic price is %s against %s under simultaneous pricing at ρ = 0.1. "
          "In the cycle, the mover prices below the rival in %.0f%% of moves, matches it in %.0f%%, and prices above it in %.0f%%. Consumers are better off under simultaneous pricing at every capacity pair, "
          "and the industry is better off under dynamic pricing. In short, committing to a price for two periods softens price competition, and the softening is strongest where the static Bertrand logic would otherwise "
          "drive prices to cost."
          % (f2(cc["alt"]["avg_price"]), f2(cc["static"]["avg_price"]), 100 * cc["alt"]["share_undercut"], 100 * cc["alt"]["share_match"], 100 * cc["alt"]["share_above_rival"]))
h2(doc, "7.4 Joint capacity and pricing")
body(doc, "We now let each mover choose capacity as well. At ρ = 2 with the eight-point grid, the dynamic-pricing equilibrium is unique across all nine starting points. Mean installed capacity is %s request-units, "
          "against %s–%s under simultaneous pricing (nine starts). The average price is %s against %s–%s, industry profit is %s against %s–%s, and consumer surplus is %s against %s–%s."
          % (f1(a0[0]["mean_capacity"]), f1(min(r_["mean_capacity"] for r_ in s0)), f1(max(r_["mean_capacity"] for r_ in s0)),
             f2(a0[0]["avg_price"]), f2(min(r_["avg_price"] for r_ in s0)), f2(max(r_["avg_price"] for r_ in s0)),
             f2(a0[0]["profit_total"]), f2(min(r_["profit_total"] for r_ in s0)), f2(max(r_["profit_total"] for r_ in s0)),
             f2(a0[0]["consumer_surplus"]), f2(min(r_["consumer_surplus"] for r_ in s0)), f2(max(r_["consumer_surplus"] for r_ in s0))) +
          " Dynamic pricing therefore leads firms to hold close to one more node (12 to 13 request-units, against 15 per node) than they do under simultaneous pricing, and the extra capacity costs the industry profit while it slightly benefits consumers. "
          "The mechanism is consistent with the fixed-capacity results. The margins that survive in the cycles make a second node worth building even when both firms could serve the market, "
          "which weakens the capacity discipline that price competition imposes in the baseline.")
def jr(n_):
    v = by[n_]
    cell = lambda k, fmt: ("%s–%s" % (fmt(rg(v["alt"], k)[0]), fmt(rg(v["alt"], k)[1])) if fmt(rg(v["alt"], k)[0]) != fmt(rg(v["alt"], k)[1]) else fmt(rg(v["alt"], k)[0]),
                           "%s–%s" % (fmt(rg(v["sim"], k)[0]), fmt(rg(v["sim"], k)[1])) if fmt(rg(v["sim"], k)[0]) != fmt(rg(v["sim"], k)[1]) else fmt(rg(v["sim"], k)[0]))
    nm = n_.replace("base (rho=2, 8 prices)", "base (ρ = 2, 8 prices)").replace("rho=", "ρ = ").replace("beta=", "β = ").replace("fc x", "*FC* × ").replace("mc=", "*c* = ").replace("sla=", "ψ = ").replace("demand ", "demand: ").replace("grid ", "price grid: ")
    c1, c2 = cell("mean_capacity", f1); p1, p2 = cell("profit_total", f1); s1, s2 = cell("consumer_surplus", f1)
    return [nm + ("*" if n_ in alt_bad else ""), c1, c2, p1, p2, s1, s2]
caption(doc, "Table 7. Joint capacity and pricing: dynamic (alternating-move) versus simultaneous-move pricing (ρ = 2 unless varied).")
table(doc, ["Scenario", "Capacity: dynamic", "Capacity: simult.", "Profit: dynamic", "Profit: simult.", "Cons. surplus: dynamic", "Cons. surplus: simult."],
      [jr(n_) for n_ in by], [1.7, 0.85, 0.85, 0.85, 0.85, 0.9, 0.9], size=8)
note(doc, "Note. Ranges are over starting points (two for dynamic pricing, three for simultaneous pricing). An asterisk marks scenarios in which the dynamic-pricing runs did not reach the convergence tolerance (both runs in each); their figures are unreliable.")
body(doc, "Table 7 varies the same parameters as Section 6. Among the %d scenarios in which the dynamic-pricing runs converged, dynamic pricing yields strictly more capacity than every simultaneous-pricing equilibrium found in %d, "
          "and never less capacity than the lowest simultaneous-pricing equilibrium. Industry profit is lower under dynamic pricing in %d of the %d and higher in %d; the profit comparison is therefore not robust, "
          "and the capacity comparison is. In the remaining %d scenarios (%s) the dynamic-pricing runs did not converge, and we draw no conclusion from them."
          % (len(alt_ok), len(strict), len(profit_lower), len(alt_ok), len(profit_higher), len(alt_bad),
             ", ".join(n_.replace("rho=", "ρ = ").replace("mc=", "*c* = ").replace("grid ", "price grid: ") for n_ in alt_bad)))

te = json.load(open(R + "timing_experiment.json"))
tby = collections.OrderedDict()
for r_ in te:
    tby.setdefault((r_["scenario"], r_["design"]), []).append(r_)
scn = list(collections.OrderedDict.fromkeys(k[0] for k in tby))
mean = lambda sc, d, k: float(np.mean([x[k] for x in tby[(sc, d)]]))
assert all(x["converged"] for v in tby.values() for x in v)
commit = [mean(sc, "C2", "mean_capacity") - mean(sc, "C1", "mean_capacity") for sc in scn]
timing = [mean(sc, "C1", "mean_capacity") - mean(sc, "C0", "mean_capacity") for sc in scn]
timing_s = [mean(sc, "C1s", "mean_capacity") - mean(sc, "C0", "mean_capacity") for sc in scn]
print("timing experiment: commitment effect", [round(x, 1) for x in commit], "timing", [round(x, 1) for x in timing], [round(x, 1) for x in timing_s])
h2(doc, "7.5 A controlled timing experiment")
body(doc, "The alternating-move game differs from the baseline in two ways at once: prices are committed for two periods, and each firm adjusts capacity only every second period, in alternation. The comparison in Section 7.4 therefore confounds "
          "price commitment with the timing of capacity decisions. To separate them we add two designs that keep simultaneous pricing every period and change only when capacity can be adjusted. In design C1 the firms take turns: firm A may adjust capacity "
          "in even periods and firm B in odd periods, exactly as in the alternating game. In design C1s both firms adjust together every second period. C0 is the baseline (capacity every period, simultaneous pricing) and C2 is the alternating game with committed prices. "
          "Since prices are not state variables in C0, C1 and C1s, Proposition 1 applies and those three designs are solved exactly as the baseline. The contrast C1 − C0 isolates the effect of slower, staggered capacity decisions; "
          "the contrast C2 − C1 isolates price commitment, because C1 and C2 stagger capacity in the same way.")
rows8 = []
for sc in scn:
    cell = lambda d: ("%s–%s" % (f1(min(x["mean_capacity"] for x in tby[(sc, d)])), f1(max(x["mean_capacity"] for x in tby[(sc, d)]))) if f1(min(x["mean_capacity"] for x in tby[(sc, d)])) != f1(max(x["mean_capacity"] for x in tby[(sc, d)])) else f1(min(x["mean_capacity"] for x in tby[(sc, d)])))
    rows8.append([sc.replace("rho=", "ρ = ").replace("base (rho=2)", "base (ρ = 2)").replace("mc=", "*c* = ").replace("fc x", "*FC* × ").replace("beta=", "β = "), cell("C0"), cell("C1"), cell("C1s"), cell("C2")])
caption(doc, "Table 8. Mean installed capacity under four timing designs (range over three starting points).")
table(doc, ["Scenario", "C0: simult. prices, capacity every period", "C1: simult. prices, capacity staggered", "C1s: simult. prices, capacity synchronized every 2nd period", "C2: committed prices, capacity staggered"],
      rows8, [1.3, 1.3, 1.3, 1.4, 1.3], size=9)
note(doc, "Note. All 72 runs converged. Eight-point price grid, ρ = 2 unless varied. Capacity is in request-units (15 per node).")
body(doc, "Table 8 shows that the timing of capacity decisions matters little, and price commitment matters a great deal. Staggering capacity decisions changes mean capacity by between %s and %s request-units across the six scenarios (%s to %s when the "
          "adjustments are synchronized instead), whereas adding price commitment on top of the staggering raises it by between %s and %s. The smallest commitment effect occurs at ρ = 3, where payoff noise is large; in the other five scenarios it is between %s and %s. "
          "We conclude that the higher capacity of Section 7.4 is a consequence of price commitment and not of the slower pace of capacity adjustment. The experiment has limits. It changes capacity timing in two specific ways, and it cannot rule out interactions "
          "between price commitment and which firm moves first within the period."
          % (f1(min(timing)), f1(max(timing)), f1(min(timing_s)), f1(max(timing_s)), f1(min(commit)), f1(max(commit)),
             f1(min(c_ for sc, c_ in zip(scn, commit) if sc != "rho=3")), f1(max(c_ for sc, c_ in zip(scn, commit) if sc != "rho=3"))))

h2(doc, "7.6 What changes relative to the baseline")
body(doc, "Three of the baseline conclusions need qualification. Proposition 3, which bounds markups by twice the price step, applies to the simultaneous-move stage game. With committed prices, Proposition 4 shows that the full collusive price can be sustained in a Markov perfect equilibrium without any explicit collusion "
          "(for intermediate discount factors), and the numerical cycles show markups well above that bound. The finding that capacity is the only source of market power also needs an addendum: committed prices are "
          "a second source, and they interact with capacity, because the margins they preserve are what make additional capacity worthwhile. Finally, the capacity-race comparison in Section 6 is partly reversed. "
          "Under dynamic pricing the equilibrium capacity is higher than under simultaneous pricing in the scenarios that converged, and Sections 7.2 and 7.5 trace this to price commitment: "
          "commitment makes capacity a strategic complement, and slower capacity adjustment does not by itself raise capacity. The weakening of the capacity race that we attributed to price competition therefore "
          "depends on how often firms can reprice. The results of this section are less complete than those of the baseline: they rely on moderate payoff noise, on an alternating protocol that also changes the "
          "pace of investment, and on a solver that fails to converge in some scenarios.")

# =============================== 7. PUBLIC DATA ===============================
h1(doc, "8. Consistency with Public Data")
h2(doc, "8.1 What the data can and cannot discipline")
body(doc, "We do not estimate the model. Public data on this market are aggregated, are often published by vendors with commercial interests, and do not identify a dynamic game with adjustment "
          "costs. We use them in two limited ways: to set the ratio between the lowest and highest price in the grid, and to check whether the model’s qualitative implications are "
          "consistent with what is observed. The per-node capacity κ, the adjustment costs, the demand-regime process, and the scale of the payoff shocks are not identified by these data, and "
          "Section 6 treats them as free parameters.")
body(doc, "Table 9 summarizes the evidence. The strongest series is the H100 rental price index reported by Silicon Data (2026), which separates hyperscalers, marketplaces, and specialized “neoclouds.” "
          "From the second half of 2023 to the second half of 2025 the hyperscaler median fell by about 19%, and from the second half of 2024 to the second half of 2025 the marketplace median fell by "
          "about 24%, while the neocloud median rose by about 11%. The hyperscaler price remained about 3.2 times the marketplace price at the end of the period. Epoch AI (2025) reports that the "
          "price of reaching a fixed level of LLM performance has fallen between 9 and 900 times per year, depending on the benchmark and threshold, with a rate of about 40 times per year for "
          "GPT-4-level performance on a PhD-level science test, and cautions that the fastest declines are recent and may not persist.")
caption(doc, "Table 9. Public evidence and the model.")
table(doc, ["Observation (source)", "Reading in the model", "Status"],
      [["H100 hourly rental price falls as supply expands: hyperscaler median $7.76 (2023 H2) to $6.26 (2025 H2); marketplace median $2.58 (2024 H2) to $1.95 (2025 H2) (Silicon Data 2026)",
        "Price falls when capacity becomes ample relative to demand (Proposition 3, Figure 1). The model’s decline from scarce to ample states is about 45% in the base case.",
        "Direction consistent; magnitude not targeted"],
       ["Hyperscaler price remains about 3.2 times the marketplace price in 2025 H2 (Silicon Data 2026)",
        "With homogeneous service and frictionless switching, ample capacity implies a single price (Proposition 3). A persistent gap implies differentiation, commitment contracts, or switching frictions that the model omits. Slower repricing (price commitment) raises prices relative to continuous repricing in Section 7, a candidate explanation that we do not test.",
        "Inconsistent with the homogeneous-good benchmark"],
       ["Token prices at fixed capability fall 9 to 900 times per year (Epoch AI 2025)",
        "Largely a cost-side and product-quality phenomenon (smaller models, better hardware). The model holds marginal cost fixed, so this is outside its explanatory scope.",
        "Not addressed"],
       ["Four hyperscalers’ capital expenditure of roughly $410–435 billion in 2025 and higher 2026 guidance (Platformonomics 2026)",
        "Expansion occurs mainly when capacity is short relative to demand (Table 2). The demand process here is stationary, so a secular rise in demand, which probably drives this spending, is outside the model.",
        "Qualitatively compatible; not testable"],
       ["Lowest-to-highest price ratio: marketplace / hyperscaler = 1.95/6.26 = 0.31 (Silicon Data 2026)",
        "Used to set the price floor-to-ceiling ratio in one scenario (floor 0.465, ceiling 1.5, eight prices).",
        "Calibrated (single parameter)"]],
      [2.55, 2.75, 1.2], size=9, align_first_left=True, left_all=True)
note(doc, "Note. The sources are vendor and tracker publications, not audited data. See the discussion in the text and the references.")
h2(doc, "8.2 The price-ratio scenario")
rr = [r for r in rows if r["name"].startswith("price ratio")][0]
body(doc, "Setting the price floor to 0.31 of the ceiling, with eight price points, yields a single equilibrium outcome in all four runs. Mean capacity equals the joint-profit level (%s), the average price is "
          "%s, consumer surplus is %s, and industry profit is %.0f%% of the joint-profit benchmark. This is the same qualitative outcome as in the other refined-grid scenarios of Section 6, and it "
          "confirms that the capacity-heavy equilibrium of the coarse base grid does not survive a more realistic price range."
          % (f1(rr["mean_capacity"][0]), f2(rr["avg_price"][0]), f2(rr["consumer_surplus"][0]), 100 * rr["profit_total"][0] / rr["cartel_profit"]))
body(doc, "What this check shows, and what it does not show, should be stated plainly. The model reproduces the sign of the price response to capacity expansion, and its prediction that excess capacity should be "
          "limited under price competition is not contradicted by the data. It does not reproduce the persistent dispersion in prices across provider types, and it cannot be taken as evidence on the "
          "level of any parameter. A serious test would estimate the model on panel data on prices, capacity, and utilization by provider, using the two-step methods of Aguirregabiria and Mira (2007) "
          "or Bajari, Benkard, and Levin (2007). Our separation result simplifies the second step of such an exercise, because the pricing game can be taken to data separately from the investment game.")

# =============================== 8. IMPLICATIONS ===============================

emp = json.load(open(R + "empirical_repricing.json"))
eb = emp["0.005"]["variants"]["baseline"]
allv = [v for th in emp.values() for v in th["variants"].values()]
gap_h = emp["0.005"]["host_type_gap"]["hyperscaler"]["median_log_rel_price"]
h2(doc, "8.3 An exploratory test of the repricing prediction")
body(doc, "The extension of Section 7 predicts that providers that commit to prices for longer should post higher prices for the same service. We checked this on public list prices, with strong caveats. "
          "We rebuilt a monthly panel of API list prices from the git history of the community-maintained price file of the open-source LiteLLM project (BerriAI 2026), covering September 2023 to October 2026. "
          "For eleven open-weight model families sold by many hosts (for example Llama 3.1 and 3.3 70B and two DeepSeek models), we compared each host’s log price with the cross-host median for the same family and month, and regressed it on the "
          "host’s monthly repricing rate computed on its other model families, with family-by-month fixed effects. The sample has %d host-family-month observations and %d hosts."
          % (eb["n_obs"], eb["n_providers"]))
body(doc, "The estimated sign is the opposite of the prediction, and it is not statistically distinguishable from zero. A one-standard-deviation higher repricing rate (about 1.7 percentage points per month) goes with a log price that is %.2f higher in the baseline "
          "(permutation p = %.2f). The coefficient is positive in all %d specifications that vary the threshold for counting a price change (0.5, 2, and 5 percent) and the sample (all hosts, with host-type controls, specialist hosts only, excluding aggregators); "
          "it ranges from %.2f to %.2f log points per standard deviation, with permutation p-values between %.2f and %.3f. We therefore read the result as neither supporting nor refuting the model."
          % (eb["per_sd"], eb["perm_p"], len(allv), min(v["per_sd"] for v in allv), max(v["per_sd"] for v in allv), min(v["perm_p"] for v in allv), max(v["perm_p"] for v in allv)))
body(doc, "Two features of the data limit what can be concluded. First, the repricing measure is very noisy: the average monthly repricing rate is %.1f percent, about a third of the hosts show essentially none, and %.0f percent of recorded price changes are increases, which "
          "suggests that the record reflects when contributors updated the file at least as much as when providers changed prices. Second, hyperscalers post much higher prices for the same open-weight model (a median of %.2f log points, or about %.0f percent, above the family median), "
          "in line with the persistent gap in GPU rental prices in Section 8.1, but this gap cannot be separated from service-level, bundling, and data-residency differences. A convincing test needs a direct record of price changes, which we have begun to "
          "collect (a daily panel of host-level prices and availability from a public API) and plan to extend with archived provider price pages."
          % (100 * emp["0.005"]["overall"]["monthly_repricing_rate"], 100 * emp["0.005"]["overall"]["share_changes_that_are_increases"], gap_h, 100 * (np.exp(gap_h) - 1)))

h1(doc, "9. Implications for Platform Design and Policy")
body(doc, "The model is stylized, and its implications are therefore conditional. In what follows we separate what the computed results support from what they only suggest.")
h2(doc, "9.1 Supported by the computed results")
body(doc, "*Price levels follow scarcity, not adjustment costs.* Across the scenarios, price is high where installed capacity falls short of demand and low where it is ample, as Propositions 2 and 3 say. "
          "Changing the cost of adjusting capacity has little effect on prices. Halving adjustment costs gives an average price of %s and doubling them %s, compared with %s in the base case, and the "
          "associated capacity ranges overlap. For a platform operator or a regulator, this suggests that policies that make provisioning cheaper, by themselves, are unlikely to lower prices if "
          "total capacity remains short of peak demand. Policies that change the aggregate capacity relative to demand matter more."
          % (cell_range([r for r in rows if r["name"] == "fc x0.5"][0]["avg_price"], f2), cell_range([r for r in rows if r["name"] == "fc x2"][0]["avg_price"], f2), cell_range(base["avg_price"], f2)))
body(doc, "*Equilibrium selection is a policy variable.* When equilibria are multiple, which one a market lands in is shaped by expectations and by what firms can observe about each other. In the base "
          "scenario the capacity-heavy equilibrium raises consumer surplus by %s per period and lowers total surplus by %s, which is about %.1f%% of the total. Whether that is a good trade depends on how a "
          "decision-maker weights consumers and firms, and the model gives no reason to think that the answer is the same for a competition authority and for a platform."
          % (f2(hiX["consumer_surplus"] - loX["consumer_surplus"]), f2(W_L - W_H), 100 * (W_L - W_H) / W_L))
body(doc, "*Share-based competition invites overbuilding.* In every scenario the market-share contest holds more capacity than any Bertrand equilibrium we found, by at least %.0f request-units. If customers contract in ways "
          "that tie revenue to installed share, for example through long-term reservations that favor the provider with the most committed capacity, the investment race is likely to be more intense than "
          "under spot price competition. Our model does not include contracts, so this is an implication of the reduced-form share rule, not a test of any real contract." % gaps_min)
h2(doc, "9.2 Suggestive, not tested")
body(doc, "*Capacity disclosure.* If a market has multiple equilibria, public information on rivals’ capacity and utilization can act as a coordination device. Our results suggest that it could "
          "coordinate on either equilibrium, and in the capacity-scarce one prices are higher and consumers are worse off. Regulators who consider mandatory disclosure of capacity and utilization "
          "for transparency reasons should therefore weigh the possibility that it facilitates coordination on scarcity. The model cannot say which effect dominates.")
body(doc, "*Switching and portability.* Recent interventions in cloud markets focus on switching frictions: the UK Competition and Markets Authority (2025) found that technical and commercial barriers to switching, including egress fees and licensing practices, "
          "weaken competition between the leading providers, the EU Data Act (Regulation (EU) 2023/2854) provides for the removal of switching charges from January 2027, and a Federal Trade Commission "
          "staff study (2025) examined how investments by cloud providers in AI developers may raise switching costs for the developers. Our model sits at the frictionless end of this spectrum, since rejected requests "
          "spill to the rival at no cost, and it implies that frictionless switching does not discipline prices when aggregate capacity is short of demand (Proposition 2). In the model, portability "
          "helps consumers when capacity is ample and does little when it is not. This is a statement about the benchmark and not about the effect of any specific rule: a model with switching costs "
          "would be needed to evaluate them, and we make no claim about the size of that effect.")
body(doc, "*Repricing frequency.* In the extension of Section 7, committing to a price for a period supports higher prices at fixed capacities and, through the strategic complementarity of Proposition 5, a larger installed capacity. "
          "A testable implication is that, other things equal, providers that reprice less often should post higher prices and carry more excess capacity than providers that reprice continuously. List prices that change a few times a year and marketplace "
          "prices that change daily are an obvious comparison, but our model is far too stylized to attribute the observed gap to this channel. Our exploratory check in Section 8.3 found the opposite sign, statistically insignificant, with a very noisy repricing measure, so the prediction remains untested.")
body(doc, "*Design of commitments.* Because capacity is the only source of margin in the model, platform features that let a provider make its capacity visible and credible, such as reserved "
          "capacity and service-level guarantees, have two edges. They reassure customers, and they can soften competition if they let providers hold scarce capacity without losing demand. Whether "
          "they do so in practice is an empirical question that our model does not answer.")

# =============================== 9. LIMITATIONS ===============================
h1(doc, "10. Limitations and Extensions")
body(doc, "Several limitations deserve emphasis. The analytical results on dynamic pricing are for a two-price benchmark with explicit equilibrium selection and with capacity treated as a long-lived choice; "
          "we do not prove the price cycles that appear numerically, which depend on the demand process, and the extension is solved only at moderate payoff noise. In the baseline the pricing stage is static by construction. Demand is inelastic up to a reservation price and products are homogeneous, which is why the model "
          "cannot explain the persistent price gap between hyperscalers and marketplaces; differentiation by latency, reliability, or bundled services is the obvious extension. We study two symmetric-"
          "information firms and do not allow entry, even though entry appears to have been important in this market. Marginal cost is constant, whereas costs per token have fallen quickly. "
          "The price grid is coarse and the extreme-value shocks smooth the undercutting logic, so the exact price levels should not be taken literally. Equilibria are found by iteration from a "
          "limited number of starting points, and we cannot rule out other equilibria, or confirm uniqueness in scenarios in which we found one. The market-share benchmark was solved from the "
          "uniform starting point only. Finally, three of the %d solver runs did not converge to the tolerance, as noted above." % (N * 4))
body(doc, "Extensions that we think are most valuable are an estimated version with panel data on provider prices and capacity, a model with differentiated products and switching costs that can be "
          "used to evaluate portability rules, and a version with sticky prices that can generate cycles.")

# =============================== 10. CONCLUSION ===============================
h1(doc, "11. Conclusion")
body(doc, "We have studied capacity investment and price competition in a market in which capacity arrives with a lag and at a sunk cost, and in which providers compete on price. The analysis yields "
          "a separation of pricing and capacity, and it shows that scarcity makes the reservation price dominant while abundance leaves only markups bounded by the price grid. Numerically, price "
          "competition keeps capacity below the level induced by a market-share contest and never below the joint-profit level, but equilibria are often multiple and consumers and total surplus rank "
          "them differently. The main practical lesson is that in a market like this one, whether prices are high depends less on the cost of adjusting capacity than on whether total capacity is "
          "scarce relative to peak demand, and that remedies that help customers move between providers matter most when capacity is ample. These conclusions come from a stylized model, and the "
          "comparison with public data is qualitative. We hope the model and the code that accompanies it are a useful starting point for estimation.")

# =============================== REPLICATION / DECLARATIONS ===============================
h1(doc, "Replication Note")
body(doc, "All code, parameter files, and result files are provided as an anonymized supplementary archive for the review process (bertrand_mpe.py for the model, sensitivity.py for the scenario and equilibrium-selection runs, "
          "make_sens_tables.py for the tables; alternating.py, price_game.py, joint_dynamic*.py, timing_experiment.py, theory_checks.py and make_price_figs.py for Section 7; the scripts in the empirical folder for Section 8.3). The base run takes about two minutes on a laptop-class CPU; the full sensitivity analysis takes roughly one hour on four cores.")

# =============================== APPENDIX A ===============================
page_break(doc)
h1(doc, "Appendix A. Proofs")
body(doc, "*Proof of Proposition 1.* Fix a state *S* and rival strategy σ_{j}. Because rival’s price affects Π_{i} only through the stage profit (4), and rival’s capacity action affects the "
          "continuation state only through the transition (2), the expected payoff in (5) of action (*p*, *k*) is *v*_{i}(*p*, *k* | *S*) = *f*_{i}(*p* | *S*) + *g*_{i}(*k* | *S*), where "
          "*f*_{i}(*p* | *S*) = Σ_{p_{j}} σ_{j}^{P}(*p*_{j} | *S*) Π_{i}^{0}(*S*, *p*, *p*_{j}) and *g*_{i}(*k* | *S*) = −AC_{i}(*k*) + β Σ_{k_{j}} σ_{j}^{K}(*k*_{j} | *S*) "
          "Σ_{λ′} *P*_{λ}(λ′ | λ) *V*_{i}(*m*_{i}′(*k*), *m*_{j}′(*k*_{j}), λ′). Here Π^{0} is the stage profit excluding adjustment costs, and σ_{j}^{P}, σ_{j}^{K} are "
          "the marginals of σ_{j}; only the marginals enter, whatever the correlation between *p*_{j} and *k*_{j}. The logit form of (6) with an additively separable index gives "
          "σ_{i}(*p*, *k* | *S*) = [exp(*f*_{i}(*p*)/ρ) / Σ_{p′} exp(*f*_{i}(*p*′)/ρ)] × [exp(*g*_{i}(*k*)/ρ) / Σ_{k′} exp(*g*_{i}(*k*′)/ρ)], which is a product of marginals. "
          "Applying this to both firms, the marginals of σ_{j} in the expressions for *f*_{i} and *g*_{i} are the logit marginals, so σ^{P} is a logit quantal-response equilibrium of the stage game, "
          "and σ^{K} is a logit equilibrium of the capacity game with continuation values *V*_{i}. Finally, ln Σ_{p,k} exp((*f* + *g*)/ρ) = ln Σ_{p} exp(*f*/ρ) + ln Σ_{k} exp(*g*/ρ), so "
          "*V*_{i}(*S*) = ργ + ρ ln Σ_{p} exp(*f*_{i}/ρ) + ρ ln Σ_{k} exp(*g*_{i}/ρ); the first logsum is a function of the state alone and enters the capacity game only through *V*. □")
body(doc, "*Proof of Proposition 2.* Let *K*_{A} + *K*_{B} ≤ λ and *K*_{i} > 0, and fix *p*_{j}. We first show that *q*_{i} = *K*_{i} for every *p*_{i}. If *p*_{i} < *p*_{j}, then *d*_{i} = λ ≥ *K*_{i}, "
          "so *q*_{i} = *K*_{i}. If *p*_{i} > *p*_{j}, then *d*_{i} = 0 and *d*_{j} = λ, so *q*_{i} = min{*K*_{i}, max(0, λ − *K*_{j})} = *K*_{i}, because λ − *K*_{j} ≥ *K*_{i}. If *p*_{i} = *p*_{j}, then "
          "*d*_{i} = *d*_{j} = λ/2; if *K*_{j} ≤ λ/2 then *q*_{i} = min{*K*_{i}, λ − *K*_{j}} = *K*_{i}, and if *K*_{j} > λ/2 then *K*_{i} ≤ λ − *K*_{j} < λ/2 and *q*_{i} = min{*K*_{i}, λ/2} = *K*_{i}. "
          "Quantity is therefore *K*_{i} regardless of prices. Directed demand *d*_{i} is weakly decreasing in *p*_{i}, so the service-level penalty is weakly smaller at a higher price. Hence "
          "Π_{i}(p̄, *p*_{j}) − Π_{i}(*p*, *p*_{j}) ≥ (p̄ − *p*)*K*_{i} > 0 for every *p* < p̄ and every *p*_{j}. Since *f*_{i}(*p*) is an expectation of stage profits, *f*_{i}(p̄) − *f*_{i}(*p*) ≥ "
          "(p̄ − *p*)*K*_{i} > 0, so by Proposition 1 σ_{i}^{P}(p̄) > σ_{i}^{P}(*p*), and the ratio σ_{i}^{P}(p̄)/σ_{i}^{P}(*p*) ≥ exp((p̄ − *p*)*K*_{i}/ρ), which diverges as ρ → 0. □")
body(doc, "*Proof of Proposition 3.* Let *K*_{A}, *K*_{B} ≥ λ and consider a pure profile (*p*_{i}, *p*_{j}). Suppose *p*_{i} < *p*_{j}. Then *d*_{i} = λ ≤ *K*_{i}, so firm *i* serves everyone and "
          "*q*_{j} = min{*K*_{j}, 0 + max(0, λ − *K*_{i})} = 0, and firm *j* earns zero. By matching *p*_{i}, firm *j* earns (*p*_{i} − *c*)λ/2 > 0, since *p*_{i} ≥ *p*_{min} > *c* and "
          "λ/2 ≤ *K*_{j}, so no asymmetric profile is an equilibrium. At a symmetric profile (*p*, *p*) each firm earns (*p* − *c*)λ/2, raising the price yields zero, and the best "
          "downward deviation is to the next lower grid price *p*⁻, which yields (*p*⁻ − *c*)λ because then *d*_{i} = λ ≤ *K*_{i} and no penalty is incurred. The deviation is unprofitable if and only if "
          "(*p*⁻ − *c*) ≤ (*p* − *c*)/2, and if *p* = *p*_{min} there is no lower price. For the bound, write *p*⁻ = *p* − *h*. The condition becomes *p* − *c* − *h* ≤ (*p* − *c*)/2, "
          "that is, *p* − *c* ≤ 2*h*. □")
body(doc, "*Remark.* Proposition 3 describes pure-strategy equilibria. We do not claim that the stage game has no mixed-strategy equilibria in these states, and in the logit equilibrium with ρ > 0 the price "
          "distribution is spread over the grid. By McKelvey and Palfrey (1995), limit points of logit equilibria as ρ → 0 are Nash equilibria of the stage game.")


body(doc, "*Proof of Proposition 4.* Write *V* for a firm’s value and use the one-shot deviation principle, which applies because the game is a discounted Markov game with finite state space. A firm earns 2*l* if it undercuts a rival at *H* "
          "(it serves all demand at *L*), *l* when both post *L*, *h* when both post *H*, and zero when it is the dearer firm. Let the mover face a rival at price *p*_{r}. "
          "(a) *Always-L.* After the first move both firms are at *L* and each earns *l*, so the value at any state with the rival at *L* is *l*/(1 − β). A deviation to *H* against a rival at *L* yields zero in the move period, and zero again in the next "
          "period because the rival keeps *L*, after which the mover returns to *L*: its value is β²*l*/(1 − β) < *l*/(1 − β). Against a rival at *H* (a transient state), complying yields 2*l* + β*l*/(1 − β); deviating to *H* yields "
          "*h* + 0 + β²*l*/(1 − β), and the difference is 2*l* + β*l* − *h* > 0 because *h* < 2*l*. "
          "(b) *Matching.* Prices stay at (*H*, *H*) forever and the value is *h*/(1 − β). Against a rival at *H*, deviating to *L* gives 2*l* now and then (*L*, *L*) forever, since the rival matches: 2*l* + β*l*/(1 − β). "
          "Complying is weakly better if and only if *h* ≥ *l*(2 − β), that is, β ≥ 2 − *r*. Against a rival at *L* (off the path), complying gives *l*/(1 − β), whereas raising the price to *H* gives zero now and then, because the rival matches, "
          "(*H*, *H*) forever: β*h*/(1 − β). Complying is weakly better if and only if *l* ≥ β*h*, that is, β ≤ 1/*r*. "
          "(c) *Always-H:* deviating to *L* against a rival at *H* gives 2*l* in the move period and again in the next period, because the rival keeps *H*, after which the mover returns to *H*: 2*l*(1 + β) + β²*h*/(1 − β), versus *h*/(1 − β); "
          "the difference is (2*l* − *h*)(1 + β) > 0. *Anti-matching* (*H* against *L*, *L* against *H*): from a rival at *L* the mover posts *H*, the rival (facing *H*) posts *L*, and the mover (facing *L*) posts *H* again, so the mover earns zero forever; "
          "deviating to *L* earns at least *l* in the move period, a strict gain. □")
body(doc, "*Proof of Proposition 5.* Payoffs. For (scarce, scarce), total capacity equals *D*, so each firm sells *D*/2 whatever the prices (the argument of Proposition 2) and *H* is dominant under either protocol; each earns *h*. "
          "Consider (ample, scarce), with *A* scarce and *B* ample, and the flows (*A*, *B*): at (*L*, *L*) (*l*, *l*); at (*L*, *H*) (*l*, *h*), since *A* sells its capacity *D*/2 and the residual *D*/2 goes to *B* at *H*; at (*H*, *L*) (0, 2*l*); at (*H*, *H*) (*h*, *h*). "
          "In the simultaneous game, *A* is indifferent when *B* plays *H* with probability *l*/*h*, and *B* is indifferent when *A* plays *H* with probability *r* − 1 < 1; the equilibrium is mixed, *A* earns *l* and *B* earns *h*. "
          "Profile *E1* (*A* always *L*; *B* plays *H* against *L* and *L* against *H*) puts the outcome at (*L*, *H*) forever, with flows (*l*, *h*). The deviation checks are: for *A*, against *B* at *H*, deviating to *H* gives *h* + β²*l*/(1 − β) "
          "(because *B* then undercuts, so *A* earns zero in the next period) against *l*/(1 − β), which is worse for the deviator if and only if *l*(1 + β) ≥ *h*, that is, β ≥ *r* − 1; against *B* at *L*, deviating to *H* gives β²*l*/(1 − β) < *l*/(1 − β). "
          "For *B*, against *A* at *L*, deviating to *L* gives *l* + β(*l* + β*h*/(1 − β)) < *h*/(1 − β) since *l* < *h*; against *A* at *H* (off the path), complying (undercutting) gives 2*l* + β*l* + β²*h*/(1 − β) and deviating to *H* gives *h*/(1 − β); "
          "complying is weakly better if and only if *l*(2 + β) ≥ *h*(1 + β), that is, β ≤ (2 − *r*)/(*r* − 1). So *E1* is an equilibrium if and only if *r* − 1 ≤ β ≤ (2 − *r*)/(*r* − 1). "
          "(a) With simultaneous pricing the payoff matrix of Table 5 gives scarce capacity a higher payoff against either rival action (*h* > *h* − φ and *l* > *l* − φ), so scarce capacity is strictly dominant. "
          "(b) For the dynamic columns, the return to choosing ample over scarce is −φ against a scarce rival and *h* − *l* − φ against an ample rival. Hence (scarce, scarce) is an equilibrium, (ample, ample) is an equilibrium if and only if φ ≤ *h* − *l*, "
          "and in a mixed pair the ample firm would switch to scarce (gaining φ), so mixed pairs are not equilibria. "
          "(c) At any pricing outcome with constant prices, total per-period profit is at most 2*h* (it equals 2*h* at (*H*, *H*) and at most 2*l* < 2*h* elsewhere), so one firm earns at most *h* − φ net of holding cost in (ample, ample). "
          "Deviating to scarce capacity and posting *L* guarantees *l* each period against any rival price (a scarce firm at *L* sells *D*/2 whether it ties or undercuts), and the pricing outcome after the deviation has constant prices in the subgames we consider, "
          "so the deviation is profitable whenever *h* − φ < *l*. "
          "Nonemptiness of the interval for β: the four inequalities that must hold are 2 − *r* ≤ 1/*r*, which is (*r* − 1)² ≥ 0; 2 − *r* ≤ (2 − *r*)/(*r* − 1), which is *r* ≤ 2; *r* − 1 ≤ 1/*r*, and *r* − 1 ≤ (2 − *r*)/(*r* − 1). "
          "The last two are both equivalent to *r*² − *r* − 1 ≤ 0, that is, *r* ≤ (1 + √5)/2. □")
body(doc, "*Remark (cycles with asymmetric capacities).* With one scarce firm *A* and one ample firm *B*, the profile in which *A* matches the rival’s price and *B* plays the opposite price traces the four-move cycle (*H*, *L*), (*L*, *L*), (*L*, *H*), (*H*, *H*) "
          "(prices of *A* and *B*), with flows (0, 2*l*), (*l*, *l*), (*l*, *h*), (*h*, *h*). Writing *V*_{k} = *f*_{k} + β*V*_{k+1} around the cycle and checking the four one-shot deviations gives four inequalities in (*r*, β). "
          "We solved them numerically, and they agree with the enumeration of all pure profiles at every point of a grid of 197 values of β and five values of *r*. "
          "The cycle is an equilibrium for small β and not on the interval of Proposition 5.")

h1(doc, "Appendix B. Computation")
body(doc, "*Algorithm.* (i) For each of the 75 states, solve the 4 × 4 logit pricing game by damped best-response iteration (damping 0.1, tolerance 10^{−12}). (ii) Start from value functions equal "
          "to zero and uniform capacity strategies (or the random draws described below). In each outer iteration, form the 3 × 3 payoff matrices from the current continuation values and solve each "
          "state’s game by damped iteration (damping 0.3, tolerance 10^{−10}), then update *V* with step 0.3, adding the pricing component’s inclusive value. (iii) Stop when the maximum change in any "
          "value is below 10^{−4}. We use the stage-game solutions from the final iteration to compute the stationary distribution of the induced Markov chain exactly, by power iteration, and "
          "report ergodic averages.")
body(doc, "*Verification.* A reference implementation solves the full 12 × 12 game in each state without using Proposition 1. In the base scenario it reproduces the decoupled solution to five decimals "
          "(average price 1.12607, industry profit 12.9059, consumer surplus 9.47719, mean capacity 59.77984, excess capacity 34.43501). The reference implementation is several times slower (a base-scenario solve took about five minutes, against under two for the decoupled "
          "solver) and was not used for the sensitivity analysis.")
body(doc, "*Starting points.* Start 0 uses uniform strategies and zero values. Starts 1 to 3 draw each state’s capacity strategies from a Dirichlet(1, 1, 1) distribution and initial values uniformly "
          "from [0, 150]; the draws are seeded and reproducible. Twelve further random starts in the base scenario are described in Section 6.")
body(doc, "*Alternating-move game.* The fixed-capacity game has 96 value-function unknowns (4 value arrays over 3 demand regimes and 8 rival prices). We solve it by damped value iteration at \u03c1 = 4 and then by Newton continuation "
          "in \u03c1 (finite-difference Jacobian, backtracking line search, step bisection on failure) down to \u03c1 = 0.1; the case with two nodes each stalled at \u03c1 \u2248 0.32. The joint game with capacity has 2,400 unknowns; "
          "it is solved by damped value iteration (step 0.5, tolerance 10^{\u22129}) at \u03c1 = 2 and 3, and by Newton continuation from \u03c1 = 2 to 1.7 in one run. Nine starting points (eight random value functions and one zero start) "
          "give the same outcome at \u03c1 = 2. For \u03c1 \u2264 1 value iteration does not converge in either game, which is why Section 7 reports moderate noise.")
body(doc, "*Timing experiment.* Designs C1 and C1s use the baseline pricing stage (a static logit equilibrium in each state, independent of the value function) and a two-phase capacity game: in C1 firm A may change capacity in phase 0 and B in phase 1; in C1s both "
          "may change capacity in phase 0 and neither in phase 1. The non-adjusting firm\u2019s value is its expected continuation under the adjusting firm\u2019s logit choice. Each design is solved from three starting points (one uniform, two random value functions) at the stated \u03c1, "
          "by damped value iteration with the tolerance 10^{\u22127}. C0 uses the decoupled baseline solver and C2 the alternating-move solver.")
body(doc, "*Verification of Propositions 4 and 5.* theory_checks.py enumerates all 16 pure Markov profiles of the two-price alternating game for ample capacities at %d combinations of *r* \u2208 (1, 2) and \u03b2 \u2208 (0, 1) (boundary points excluded), solves the induced Markov chain exactly, "
          "and tests the one-shot-deviation conditions. The equilibrium set equals the one in Proposition 4 at every point. For the mixed capacity pair it checks that *E1* is an equilibrium exactly on the stated interval at %d points (%d mismatches), that its flows are (*l*, *h*), "
          "and that inside the interval of Proposition 5 matching and *E1* are simultaneously equilibria of their subgames at all %d tested points (%d failures). In every pure equilibrium of the mixed pair whose prices settle on constants the scarce firm earns at least *l* (%s); "
          "%d of %d (equilibrium, first-mover) outcomes in that subgame involve price cycles."
          % (tc["prop4"]["points"], tc["prop5"]["E1_points"], tc["prop5"]["E1_mismatches"], tc["prop5"]["inside_J_points"], tc["prop5"]["inside_J_failures"],
             "confirmed" if tc["prop5"]["scarce_flow_at_least_l_in_every_constant_price_pure_MPE"] else "violated",
             tc["prop5"]["pure_MPE_outcomes_constant_vs_cyclic"][1], sum(tc["prop5"]["pure_MPE_outcomes_constant_vs_cyclic"])))
body(doc, "*Propositions as numerical checks.* In each scenario, we verify Proposition 2 directly by comparing the payoff of the reservation price against every lower price against every rival price in "
          "all states with *K*_{A} + *K*_{B} ≤ λ and both capacities positive, and by checking that it is the modal price. We also check for monotonicity of the equilibrium expected price in rival capacity.")

# =============================== REFERENCES ===============================
page_break(doc)
h1(doc, "References")
refs = [
 "Aguirregabiria V, Mira P (2007) Sequential estimation of dynamic discrete games. *Econometrica* 75(1):1–53.",
 "Allon G, Federgruen A (2007) Competition in service industries. *Oper. Res.* 55(1):37–55.",
 "Armbrust M, Fox A, Griffith R, Joseph AD, Katz R, Konwinski A, Lee G, Patterson D, Rabkin A, Stoica I, Zaharia M (2010) A view of cloud computing. *Commun. ACM* 53(4):50–58.",
 "Bajari P, Benkard CL, Levin J (2007) Estimating dynamic models of imperfect competition. *Econometrica* 75(5):1331–1370.",
 "Bapna R, Das S, Garfinkel R, Stallaert J (2008) A market design for grid computing. *INFORMS J. Comput.* 20(1):100–111.",
 "BerriAI (2026) LiteLLM model prices and context window file, git history. Accessed October 13, 2026, https://github.com/BerriAI/litellm.",
 "Besanko D, Doraszelski U (2004) Capacity dynamics and endogenous asymmetries in firm size. *RAND J. Econom.* 35(1):23–49.",
 "Besanko D, Doraszelski U, Kryukov Y, Satterthwaite M (2010) Learning-by-doing, organizational forgetting, and industry dynamics. *Econometrica* 78(2):453–508.",
 "Cachon GP, Harker PT (2002) Competition and outsourcing with scale economies. *Management Sci.* 48(10):1314–1333.",
 "Competition and Markets Authority (2025) Cloud services market investigation: Final decision. July 2025, United Kingdom.",
 "Davidson C, Deneckere R (1986) Long-run competition in capacity, short-run competition in price, and the Cournot model. *RAND J. Econom.* 17(3):404–415.",
 "Dewan S, Mendelson H (1990) User delay costs and internal pricing for a service facility. *Management Sci.* 36(12):1502–1517.",
 "Doraszelski U, Satterthwaite M (2010) Computable Markov-perfect industry dynamics. *RAND J. Econom.* 41(2):215–243.",
 "Epoch AI (2025) LLM inference price trends. Data insight, March 12, 2025. https://epoch.ai/data-insights/llm-inference-price-trends (accessed October 13, 2026).",
 "Ericson R, Pakes A (1995) Markov-perfect industry dynamics: A framework for empirical work. *Rev. Econom. Stud.* 62(1):53–82.",
 "European Parliament and Council (2023) Regulation (EU) 2023/2854 on harmonised rules on fair access to and use of data (Data Act). *Official Journal of the European Union*, December 22, 2023.",
 "Federal Trade Commission (2025) Staff report on AI partnerships and investments 6(b) study. January 17, 2025, Washington, DC.",
 "Kreps DM, Scheinkman JA (1983) Quantity precommitment and Bertrand competition yield Cournot outcomes. *Bell J. Econom.* 14(2):326–337.",
 "Levitan R, Shubik M (1972) Price duopoly and capacity constraints. *Internat. Econom. Rev.* 13(1):111–122.",
 "Maskin E, Tirole J (1988) A theory of dynamic oligopoly, II: Price competition, kinked demand curves, and Edgeworth cycles. *Econometrica* 56(3):571–599.",
 "McKelvey RD, Palfrey TR (1995) Quantal response equilibria for normal form games. *Games Econom. Behav.* 10(1):6–38.",
 "Mendelson H (1985) Pricing computer services: Queueing effects. *Commun. ACM* 28(3):312–321.",
 "OpenRouter (2026) Model endpoints API. Accessed October 13, 2026, https://openrouter.ai/docs.",
 "Osborne MJ, Pitchik C (1986) Price competition in a capacity-constrained duopoly. *J. Econom. Theory* 38(2):238–260.",
 "Pakes A, McGuire P (1994) Computing Markov-perfect Nash equilibria: Numerical implications of a dynamic differentiated product model. *RAND J. Econom.* 25(4):555–589.",
 "Platformonomics (2026) Follow the CAPEX: 2025 retrospective. Accessed October 13, 2026, https://platformonomics.com.",
 "Rust J (1987) Optimal replacement of GMC bus engines: An empirical model of Harold Zurcher. *Econometrica* 55(5):999–1033.",
 "Silicon Data (2026) H100 rental price over time. Accessed October 13, 2026, https://www.silicondata.com/blog/h100-rental-price-over-time.",
]
for t in refs:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.5)
    p.paragraph_format.first_line_indent = Inches(-0.5)
    p.paragraph_format.line_spacing = 2.0
    rich(p, t)

OUTDIR = os.path.join(HERE, "..")
os.makedirs(OUTDIR, exist_ok=True)
cp = doc.core_properties
cp.author = ""; cp.last_modified_by = ""; cp.title = "Price Competition and Capacity Investment in LLM Inference Markets"; cp.comments = ""; cp.subject = ""
doc.save(os.path.join(OUTDIR, "03_Manuscript_Blinded.docx"))
print("saved")
