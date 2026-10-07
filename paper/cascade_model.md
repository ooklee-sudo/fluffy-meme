---
title: "An Expected-Cost Model of Screening Cascades for Machine-Written Scholarly Text"
subtitle: "Supplementary analytical model, calibrated on the pilot data (exploratory)"
---

# 1. Purpose and status

The pilot study compares a free count-based screen with LLM judges and simulates a cascade in which only the highest-scoring documents are sent to a judge. That simulation reports detection rates and judge cost, but it cannot say when a cascade is worth running. This note fills that gap with a small decision model. The model's *structure* is derived analytically; its *inputs* are partly measured (the screen's and the judge's class-conditional behavior, and the judge's price) and partly assumed (the cost of reviewing a flagged paper, the loss from a missed machine paper, and the base rate of machine papers). The assumed values are illustrative, and nothing here should be read as an estimate of any organization's costs. The analysis is exploratory.

# 2. Setup

An organization receives a stream of documents, a share π of which are machine-written. A free screen assigns each document a score s, with likelihood ratio ℓ(s) = f_M(s) / f_H(s), where f_M and f_H are the score densities of machine and human papers; we assume ℓ is nondecreasing in s. Given a base rate π, the posterior probability that a document with score s is machine-written is p(s; π) = πℓ(s) / (πℓ(s) + 1 − π).

The organization may send a document to a judge. A judged document is flagged with probability J if it is machine-written (the judge's detection rate) and a if it is human (its false-alarm rate), independently of s given the class. Four costs apply:

- c_J, the price of one judge call;
- c_R, the cost of investigating one flagged paper, assumed here to settle its status;
- L, the loss from each machine paper that is not flagged;
- nothing for the screen itself.

Documents that are not judged are not flagged. A cascade therefore consists of a depth: the screen score above which documents are judged.

# 3. Analytical results

**Proposition 1 (when to call the judge).** Sending a document with posterior p to the judge reduces expected cost, relative to not sending it, by

V(p) = p·[(L − c_R)J + c_R·a] − (c_J + c_R·a).

Hence it is worth sending if and only if p ≥ τ, where τ = (c_J + c_R·a) / ((L − c_R)J + c_R·a). If (L − c_R)J ≤ c_J, then τ ≥ 1 and the judge is never worth calling.

*Proof.* Not sending leaves expected cost L·p. Sending costs c_J + c_R(pJ + (1 − p)a) + L·p(1 − J). The difference is V(p), which is linear and increasing in p. ∎

Equivalently, a document should be judged if and only if the screen's likelihood ratio satisfies ℓ(s) ≥ ℓ* = ((1 − π)/π)·τ/(1 − τ).

**Proposition 2 (depth, base rate, and prices).** Because ℓ is nondecreasing in s, the set of documents worth judging, {s : ℓ(s) ≥ ℓ*}, expands as ℓ* falls. ℓ* is decreasing in π, so the cost-minimizing depth is nondecreasing in the base rate π. It is also nondecreasing in J and L and nonincreasing in c_J and c_R, because τ falls with J and L and rises with c_J and c_R.

*Proof.* ∂τ/∂c_J > 0; ∂τ/∂c_R has the sign of a·[(L − c_R)J + c_R·a] − (c_J + c_R·a)(a − J), which is positive when J > a; and τ falls with L and J. ℓ* is increasing in τ and decreasing in π. ∎

**Proposition 3 (blind spots).** τ rises as the judge's detection rate J falls, and the judge is never worth calling when J ≤ c_J/(L − c_R). If the screen cannot tell generators apart, the relevant detection rate for a stream that mixes generators with weights w_g is the weighted mean J̄ = Σ w_g·J_g, so a generator that the judge cannot detect lowers the value of the judge for the whole stream.

**Proposition 4 (precision at low base rates).** Among the documents a judge flags in an unscreened stream, the share that is machine-written is πJ / (πJ + (1 − π)a). It is low when π is small even for a judge with a small false-alarm rate. Screening before judging raises the effective base rate among judged documents, which raises this share and reduces wasted investigations.

# 4. Calibration

All class-conditional rates come from the 500 judged excerpts. The screen is the clustering-feature detector trained without the target generator, and the judge is Gemini 2.5 Pro flagging at a score of 50. At that threshold the judge flags 2% of human papers (a = 0.02) and detects 86% of GPT-4o papers, 89% of Llama papers, and 1% of Claude papers (J = 0.86, 0.89, and 0.01). The price is US$0.0174 per document, measured. The "mixture" row averages the three generators with equal weight (J̄ = 0.59). Table 1 gives the screen's recall at several depths, expressed as the share of human papers sent to the judge (f).

| Target | f = 5%: sent / sent and flagged | f = 20% | f = 50% | f = 100% |
|:--|:--|:--|:--|:--|
| GPT-4o | 0.64 / 0.55 | 0.98 / 0.85 | 1.00 / 0.87 | 1.00 / 0.87 |
| Claude | 0.17 / 0.00 | 0.61 / 0.00 | 0.86 / 0.00 | 1.00 / 0.01 |
| Llama | 0.73 / 0.66 | 0.87 / 0.80 | 0.99 / 0.89 | 1.00 / 0.89 |
| Mixture | 0.51 / 0.41 | 0.82 / 0.55 | 0.95 / 0.59 | 1.00 / 0.59 |

: Table 1. Share of machine papers sent to the judge, and sent and flagged, when the screen passes the stated share of human papers (empirical rates; no independence assumed).

# 5. Illustrative results

We set c_R = US$20 per flagged paper and consider losses of L = US$100 and US$500 per missed machine paper, and judge prices at the measured US$0.0174 and at 100 times that figure (US$1.74, for example a longer input or a reasoning model with a long output). These are assumptions chosen to show structure. Using the empirical rates and no independence assumption, we computed the cost of four policies per 1,000 documents: no screening, review everything above the screen threshold (screen only), judge every document, and the best cascade.

| L | Judge price | Base rate | Best cascade q* | No screening | Screen only | Judge on all | Cascade | Saving vs judge-all |
|:--|:--|:--|--:|--:|--:|--:|--:|--:|
| US$100 | ×1 | 1% | 14% | 1,000 | 973 | 948 | 594 | 37% |
| US$100 | ×1 | 10% | 41% | 10,000 | 6,225 | 5,652 | 5,420 | 4% |
| US$100 | ×1 | 30% | 67% | 30,000 | 12,647 | 16,104 | 15,955 | 1% |
| US$100 | ×100 | 1% | 5% | 1,000 | 973 | 2,671 | 767 | 71% |
| US$100 | ×100 | 10% | 24% | 10,000 | 6,225 | 7,374 | 6,051 | 18% |
| US$100 | ×100 | 30% | 56% | 30,000 | 12,647 | 17,826 | 16,959 | 5% |
| US$500 | ×1 | 1% | 36% | 5,000 | 3,465 | 2,582 | 2,284 | 12% |
| US$500 | ×1 | 10% | 59% | 50,000 | 12,092 | 21,986 | 21,795 | 1% |
| US$500 | ×100 | 1% | 18% | 5,000 | 3,465 | 4,304 | 2,713 | 37% |
| US$500 | ×100 | 10% | 45% | 50,000 | 12,092 | 23,708 | 22,684 | 4% |

: Table 2. Expected cost per 1,000 documents (US$) for the equal-weight mixture of generators, review cost US$20 per flagged paper (assumed). q* is the share of all documents sent to the judge at the cascade's optimum. The full grid, with per-generator results, is in the project repository.

![Figure 1. (A) Expected cost per 1,000 documents against the share of documents sent to the judge, with 10% machine papers, a loss of US$100 per missed paper, and review at US$20 per flagged paper. (B) Cost-minimizing share judged against the base rate. Both curves use the mixture of generators.](fig_formal_model.png)

Five patterns emerge, and they hold across the grid of assumptions.

1. **Depth rises with the base rate**, as Proposition 2 requires. For the mixture at L = US$100, the optimal share judged goes from 14% at a 1% base rate to 41% at 10% and 67% at 30% (Figure 1B).
2. **The judge's price is a minor part of total cost; its false alarms are not.** For the mixture at a 1% base rate, judging everything costs US$17 in judge calls, US$522 in investigations, and US$408 in missed papers per 1,000 documents. The cascade cuts investigations to US$102 by judging only 14% of documents, at the price of a small rise in missed papers (US$408 to US$490). The saving comes from avoiding false alarms, in line with Proposition 4: at a 1% base rate and a 2% false-alarm rate, only about 23% of the papers an unscreened judge flags are machine-written (77% at 10%, 93% at 30%).
3. **Savings are largest where machine papers are rare and the judge is expensive**, up to 71% of cost at a 1% base rate with a judge 100 times pricier, and small (1% to 5%) at a 30% base rate.
4. **At high base rates, reviewing a deep slice of the screen's output beats any use of the judge** under these assumed costs. This reflects the assumption that review is cheap and settles a paper perfectly; it is not a recommendation to review everything.
5. **The judge's blind spot makes it worthless for Claude papers.** Claude's J of 0.01 gives τ = 0.35 at L = US$100, so the judge is worth calling only when the screen's likelihood ratio is at least 53 at a 1% base rate (about 5 at 10%); in the data, the judge flagged none of the Claude papers the screen sent it. For the mixture, J̄ = 0.59 raises τ to 0.009 at L = US$100 (a likelihood ratio of 0.88 at a 1% base rate), against 0.006 for GPT-4o alone.

# 6. Implications

For organizations, the model identifies three quantities that determine the value of a cascade and that no outside study can supply: the base rate of machine papers, the cost of investigating a flagged paper, and the loss from a miss. Proposition 1 turns them into an operating rule that can be applied document by document: judge a paper if its posterior probability of machine origin, given the screen score and the base rate, is at least τ. It also shows that the screen's main economic contribution is not saving judge fees, which are small, but raising the base rate that the judge sees, so that its false alarms do not swamp its detections. The judge's detection rate matters more than its price, and a generator that the judge cannot detect removes much of its value.

# 7. Limitations of the model

The model assumes that investigating a flagged paper settles its status at a fixed cost, and that capacity is unlimited. Real review is imperfect, capacity is constrained, and false accusations of authors carry costs beyond the investigation, none of which is modeled. The costs c_R and L and the base rate are assumed, not measured, so the results are structural illustrations and not estimates. The judge's operating point is fixed at a threshold of 50 and is not optimized. Class-conditional rates are estimated from 196 human and about 93 machine papers per generator, and we report no uncertainty intervals for the cost curves. The mixture weights are equal, and the mixture mixes scores from detectors trained without each target generator, which assumes that the stream contains generators that the screen has not seen. Judging and flagging are costed per document, so strategic adaptation by authors is ignored, as is any three-way policy that flags very suspicious documents directly without judging them. Each of these extensions would be natural in a fuller treatment.
