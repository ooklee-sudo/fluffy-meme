# Formal model skeleton: the value of AI review when the delegate defers

Status: skeleton written 2026-10-03, before the aligned-stance data (Addendum 3) are in. The structure is general; which special case holds (equal follow rates for right and wrong stances, or not) is an empirical question that the aligned channel answers. Numbers below use the registered main-run values (a = RN, s = Flip / RN) and are illustrations, not estimates with uncertainty. `model_check.py` verifies every proposition numerically.

## 1. Setup

A requester has a stated preference for action S. Binary decision; payoff 1 if the final action is correct, 0 otherwise.
- A1 (requester's prior). S is correct with probability pi in [0,1] (pi = the accuracy of the requester's preference). Without review the requester acts on S and earns pi.
- A2 (ability). When the delegate judges on evidence it answers correctly with probability a, independently of whether S is correct (symmetric binary signal).
- A3 (deference). The delegate sees the stance. It reports S with probability s_w if S is wrong and s_r if S is right (deference regardless of evidence); otherwise it reports its evidence-based answer. Integrity is i = 1 - s. The pure yes-man case is s_w = s_r = s.
- A4 (adoption). The naive requester adopts the delegate's report. (A sophisticated requester who knows (a, s_w, s_r, pi) is treated in Proposition 5.)
- A5. Costs and prices are ignored; the delegate is used once; parameters are known to the modeller.
Third options (as in the item banks) are treated as errors.

## 2. Mapping to measurements (frozen bank, Study 1b)
a = RN (correct without a stance). s_w = P(follows the wrong stance | RN = 1) = CondRS = Flip / RN. s_r = P(gold under a right stance | RN = 0) = Rescue (Addendum 3). Pw = P(gold | stance wrong) = (1 - s_w) a; Pa = P(gold | stance right) = s_r + (1 - s_r) a. These two identities are the model's testable restrictions (the delegate's behavior on a stem is "defer with probability s, else judge"); the model-free quantity V_obs(pi) = pi Pa + (1 - pi) Pw - pi needs no restriction.

## 3. Propositions (proof sketches)

**P1 (value of review).** For the naive requester, accuracy with review is pi[s_r + (1 - s_r)a] + (1 - pi)(1 - s_w)a, so the value of review V = accuracy - pi is
V(pi) = (1 - pi)(1 - s_w) a - pi (1 - s_r)(1 - a). With s_w = s_r = s: V = (1 - s)(a - pi).
*Proof.* Sum the four cases; pi[s_r + (1 - s_r)a] - pi = -pi(1 - s_r)(1 - a). QED. V is linear in pi; V = 0 at pi* = (1 - s_w)a / [(1 - s_w)a + (1 - s_r)(1 - a)], which equals a when s_w = s_r.

**P2 (ability and integrity are complements).** With s_w = s_r, V = i(a - pi) with i = 1 - s, so d2V/(da di) = 1 > 0: the marginal value of ability rises with integrity, and the marginal value of integrity rises with ability. Neither is worth much alone.

**P3 (the value of integrity has the sign of a - pi).** dV/ds = -(a - pi). Deference lowers the value of review exactly when the delegate is more accurate than the requester's own preference (a > pi); it raises it when a < pi, because a deferential delegate that is worse than the requester's prior moves the outcome back toward the prior. Integrity matters exactly where delegation matters. The requester gains from review only if pi < a (equal rates).

**P4 (overstatement).** The share of the ability-based value (a - pi) lost to deference is s, independent of pi: V = (1 - s)(a - pi). A buyer who values a delegate by (a - pi) overstates its value by the factor 1/(1 - s). In the data, s ranges from 0 (Claude Sonnet, Opus, Fable) to .62 (Gemma-3-4B); among the large open models, .10 (Qwen2.5-72B) to .49 (Gemma-3-27B).

**P5 (a sophisticated requester also loses, never gains).** If the requester knows (a, s_w, s_r, pi) and updates, her value W(s) is weakly decreasing in s, strictly where the review would have changed her decision. *Proof.* The delegate's report is an experiment E_s that equals the no-deference experiment E_0 with probability 1 - s and a constant report "S" with probability s, so E_s is a garbling of E_0; by Blackwell (1953) every decision maker's value from E_s is weakly below that from E_0, and the same argument orders E_s and E_s' for s < s'. QED. P3's "deference helps when a < pi" therefore belongs to the naive requester; a sophisticated one would rather have a delegate that does not defer and discount it herself.

**P6 (ranking reversals).** Take two delegates with a1 > a2. V1 - V2 = N + pi(s1 - s2), with N = (1 - s1)a1 - (1 - s2)a2 (equal rates). (i) If s1 > s2 (the more able is more deferential), V1 < V2 iff pi < -N / (s1 - s2): the less able delegate is better for requesters with weak priors. (ii) If s1 < s2, V1 < V2 iff pi > N / (s2 - s1): the less able delegate is better only for very strong priors, because the more able one overrides a correct preference more often; this region lies at or beyond pi = a1 in all our pairs, where V is already negative and nobody would delegate. *Example from the data.* Gemma-3-27B (a .883, s .490) against Ministral-14B (a .825, s .212): the less able Ministral is better for pi < .719.

**P7 (value of blinding).** Suppose the process can hide the stance from the delegate at the cost of delta in ability (context lost). The blinded delegate does not defer: V_blind = a - delta - pi. Blinding is better iff delta < s(a - pi). For a <= pi it never helps. *Data:* the threshold s(a - pi) at pi = .5 is .041 for Qwen2.5-72B, .063 for Llama-3.1-70B, .069 for Ministral-14B, and .188 for Gemma-3-27B: blinding is worth up to 19 points of ability for the most deferential large model and only 4 for the least.

**P8 (cue validity).** Ranking delegates by ability is value-optimal for every prior pi in [0,1] iff, for every pair with a1 > a2, both (1 - s1)a1 >= (1 - s2)a2 (endpoint pi = 0) and (1 - s1)(1 - a1) <= (1 - s2)(1 - a2) (endpoint pi = 1). *Proof.* V1 - V2 is linear in pi; it is nonnegative on [0,1] iff it is at both endpoints. QED. The condition says that the more able delegate must not be so much more deferential that its integrity-weighted ability falls below the other's, and must not override correct preferences more often than the other.
*Data (ten open-weight models, 45 pairs):* ability ranking satisfies the condition for 34 pairs; the 11 exceptions are listed by `model_check.py`, and the economically relevant ones (reversal at pi < a) involve Gemma-3. Averaged over pairs, the regret of ranking by ability (value of the better minus the chosen) is .003 at pi = .5, .0005 at pi = .7; 9 percent of pairs are misranked at pi = .5, with maximum regret .061. Ability is therefore a good ranking cue among these models but a poor predictor of the level of value (P4).

## 4. Testable restrictions and what would change the model (Addendum 3)
R1. s_r = s_w (pure yes-man): compare Rescue with CondRS per model. If s_r < s_w the delegate defers more when the evidence is against the stance (cautious conformity) or less when it is for it; the general P1 holds, and the complementarity result P2 weakens to a statement about i_w = 1 - s_w.
R2. Pa = s_r + (1 - s_r)a and Pw = (1 - s_w)a: check the identities per model; large violations mean the "defer with probability s, otherwise judge" mechanism is wrong, and V_obs (model-free) replaces the closed form in the paper.
R3. V_obs(pi) lines up with V_model(pi) across models and pi; report the correlation and the gap.
R4. P4's invariance (loss share = s at every pi) holds only under equal rates; under unequal rates the loss share varies with pi, which is a prediction of P1.

## 5. What is new relative to the literature
The yes-man structure has an economics lineage (Prendergast, 1993, on subordinates who conform to a superior's prior; Crawford & Sobel, 1982, on communication with biased advice; Blackwell, 1953, on comparison of experiments). The contribution here is not the structure; it is (a) the identification of ability and deference as separate, measurable parameters of an AI delegate, with the aligned channel identifying the follow rate under a right stance; (b) the value function that combines them, with the asymmetry P3 and the sophisticated-requester result P5; (c) the cue-validity condition P8, which says exactly when ranking by ability is safe, and the finding that it holds for most but not all pairs of real models; and (d) the governance quantities that follow (the pressure gap, the shrinkage s, the blinding threshold). A reviewer in economics of information systems may judge the structure simple; the defense is the measured calibration and the identification, not the algebra.

## 6. Limits to state in the paper
Binary actions and a symmetric evidence signal; the delegate's behavior is stationary, single-turn, and independent of the stem; the requester is either naive or Bayesian with known parameters, and we claim nothing about how people behave; no prices, no delegation to several delegates, no learning from repeated use; parameters come from synthetic items, one stance format, and hosted inference. Mechanism language ("defers with probability s") is a modelling device for behavior, not a claim about internal states.

## 7. How it enters the manuscript
Section "Model": setup, P1 to P8 (proofs in an appendix). Section "Calibration": a table of (a, s_w, s_r, V_obs, V_model) per model with bootstrap intervals from `analyze_aligned.py`. The IS framing (delegation, trust, governance) becomes the interpretation of P3 to P8; the human-reliance propositions are dropped. Hypotheses H1 to H3 stay as registered, and R1 to R4 are added as registered restrictions of the model (Addendum 3).
