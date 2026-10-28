"""Builds Theory_Draft.docx: economic theory of monitoring and taking back tasks delegated to AI agents."""
import json
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
N = json.load(open("numerics.json")); LJ = json.load(open("learning.json")); HJ = json.load(open("h_sensitivity.json"))
d = Document()
st = d.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Malgun Gothic")
for s in d.sections: s.left_margin = s.right_margin = Inches(1)
def P(text, bold=False, italic=False, align=None, size=None):
    p = d.add_paragraph(); r = p.add_run(text); r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    if align: p.alignment = align
    return p
def EQ(text): p = P(text, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER); return p
def H1(t): d.add_heading(t, level=1)
def H2(t): d.add_heading(t, level=2)
def PROP(title, body): p = d.add_paragraph(); r = p.add_run(title + " "); r.bold = True; p.add_run(body).italic = True
def TABLE(head, rows):
    t = d.add_table(rows=1, cols=len(head)); t.style = "Light Grid Accent 1"
    for i, h in enumerate(head): t.rows[0].cells[i].text = h
    for row in rows:
        cs = t.add_row().cells
        for i, v in enumerate(row): cs[i].text = str(v)
    d.add_paragraph()
p = N["params"]; o = N["optimal"]
P("Theory draft (working paper section) — not for circulation", italic=True, size=9)
P("When to Take the Task Back: Self-Exciting Errors and the Economics of Monitoring AI Agents", bold=True, size=15)
P("Ook Lee, Hanyang University · draft of " + "28 October 2026", size=10)

H1("1. Purpose and positioning")
P("Firms increasingly delegate multi-step work to autonomous AI agents and keep a human able to take the task back. "
  "The design question an information system must answer is not whether the agent errs, but when an observed error history "
  "should trigger a hand-off. Our empirical analysis of SWE-agent trajectories shows that agent errors cluster for two reasons: "
  "tasks differ in difficulty (heterogeneity), and an error raises the chance of the next one (contagion, or self-excitation). "
  "This section builds a decision model in which both sources matter and derives what each implies for monitoring rules.")
P("The model draws on four strands of economic theory. (i) Optimal stopping and sequential decisions (Wald 1947; Shiryaev 1963): "
  "the hand-off is a stopping time chosen on the basis of a growing error history. (ii) The economics of information and the "
  "informativeness principle (Blackwell 1953; Holmström 1979): a signal has value only if it is informative about the hidden state "
  "that drives costs, which tells us when the timing of errors, not just their number, should enter a monitoring rule. "
  "(iii) Heterogeneity versus state dependence (Heckman 1981): the econometric distinction we estimate maps onto two distinct "
  "sources of monitoring value. (iv) Bayesian learning and quitting (Jovanovic 1979): under heterogeneity the principal learns the "
  "agent's task-specific error rate and quits a bad match, as a worker quits a bad job. "
  "For IS, the contribution is a theory of control design for human–AI delegation (Kirsch 1997; Fügener et al. 2022): "
  "which signal to monitor, where to set the threshold, and for which tasks monitoring is worth building.")

H1("2. Model")
P("A firm delegates a task to an AI agent. Time is discrete, t = 0, 1, 2, …. At the start of each step the firm either lets the agent "
  "take the step or hands the task to a human, which ends the game at cost H > 0. A step costs k > 0 plus c > 0 per error made in it. "
  "After each step the task is completed with probability q ∈ (0, 1), independently of the error history (Assumption A3 below relaxes "
  "this in the discussion).")
P("Errors are self-exciting. The number of errors in step t is")
EQ("e_t | x_t ~ Poisson(μ + x_t),     x_{t+1} = δ x_t + α e_t,     x_0 = 0,")
P("where μ > 0 is the baseline error rate, x_t ≥ 0 is the excess intensity built up by past errors, α ≥ 0 is the jump in intensity "
  "per error and δ ∈ [0, 1] is the per-step decay. Equivalently x_t = α Σ_{s<t} δ^{t−1−s} e_s, the discrete-time Hawkes (1971) process "
  "we estimate. Its branching ratio n = α/(1−δ) is the expected number of further errors that one error triggers. "
  "Since E[x_{t+1} | x_t] = ρ x_t + αμ with ρ = δ + α, the error process is stable (ρ < 1) exactly when n < 1.")
P("Assumptions. A1 (observability): the firm observes each step's errors. A2 (stationarity): μ, α, δ, k, c, q, H do not change over time. "
  "A3 (completion independent of errors): q does not depend on x. A4 (heterogeneity, Section 3.4 only): μ is task-specific, "
  "μ ~ Gamma(a, b) (shape a, rate b), unknown to the firm.")
P("With μ known, the state is x and the minimum expected cost W solves the Bellman equation")
EQ("W(x) = min{ H,  C(x) },     C(x) = k + c(μ + x) + (1 − q) E[ W(δx + αe) ],   e ~ Poisson(μ + x).")

H1("3. Results")
H2("3.1 The hand-off rule is a threshold on excess intensity")
PROP("Proposition 1 (threshold).", "The Bellman equation has a unique bounded solution W, which is nondecreasing in x. The firm hands "
     "the task back if and only if x_t ≥ x*, where x* = inf{x : C(x) ≥ H} (x* = ∞ if the set is empty).")
P("The intuition is that a higher excess intensity raises today's expected error cost and, because the Poisson family is ordered by "
  "first-order stochastic dominance, makes tomorrow's state worse as well. The proof (Appendix A) uses the contraction property of "
  "the Bellman operator (modulus 1 − q) and the fact that it preserves monotonicity. Numerically, x* falls as n rises: from "
  f"{N['sensitivity_branching'][0]['x_star']:.2f} at n = 0 to {N['sensitivity_branching'][-1]['x_star']:.2f} at n = 1.05 "
  "under the calibration in Section 4. More contagious agents should be taken back sooner.")
H2("3.2 When is counting errors enough?")
PROP("Proposition 2 (sufficient statistic).", "A rule that hands off when the cumulative error count N_t = Σ_{s<t} e_s reaches a "
     "fixed bound is optimal if δ = 1 (no decay), since then x_t = α N_t. If δ < 1 and α > 0 and x* is interior, every count rule is "
     "strictly suboptimal: histories with the same count but different timing lie on opposite sides of the threshold.")
P("This is the informativeness principle in a stopping problem. What drives costs is x, and N is a sufficient statistic for x only "
  "when errors never decay. Otherwise recent errors carry more information than old ones, and a recency-weighted score, the "
  "Hawkes intensity, is the right thing to monitor. Proposition 4 shows the converse practical point: when contagion is weak, "
  "the loss from using a count rule is small, which is what our observational early-warning results find.")
H2("3.3 The cost of autonomy and the role of criticality")
PROP("Proposition 3 (cost of never handing off).", "If the firm never hands off, its expected cost is")
EQ("C_U = (k + cμ)/q + [cαμ/(1 − ρ)] · [1/q − 1/(1 − (1 − q)ρ)],     ρ = δ + α,")
P("which is finite if and only if (1 − q)ρ < 1. It rises with α and δ, and diverges as (1 − q)ρ ↑ 1.", italic=True)
P("The first term is the cost of an agent whose errors do not spread; the second is the extra cost of contagion. "
  "A supercritical agent (n ≥ 1) has finite expected cost only because the task may end first.")
PROP("Proposition 4 (contagion value of monitoring).", "Let V_C = min{H, C_U} − W(0) be the value of monitoring relative to the "
     "best static choice (hand off at once, or never). Then V_C ≥ 0; V_C = 0 if α = 0; and C_U − W(0) → ∞ as (1 − q)ρ ↑ 1, while "
     "V_C stays bounded by H − W(0).")
P("Monitoring therefore matters most for agents close to criticality. In the calibrated example the value against never handing off "
  "is zero up to n = 0.4 and then rises steeply: " + ", ".join(
      f"{r['value_vs_never']:.1f} at n = {r['branching']}" for r in N["sensitivity_branching"] if r["branching"] in (0.6, 0.8, 0.9, 1.0)) +
  " (costs in units of one step).")
H2("3.4 Heterogeneity: monitoring as learning")
P("Now let α = 0 but let μ be unknown and task-specific (A4). After t steps with N_t errors the posterior is Gamma(a + N_t, b + t), "
  "and next-step errors are negative binomial with mean (a + N_t)/(b + t). The state is (t, N_t).")
PROP("Proposition 5 (learning and a rate rule).", "Under A4 with α = 0 the firm hands off at step t if and only if N_t ≥ N*(t). "
     "As t grows the rule approaches a rate rule: hand off when the posterior mean (a + N_t)/(b + t) exceeds μ* = (qH − k)/c, "
     "the error rate at which autonomy and hand-off cost the same.")
P("Here the count is sufficient, but its bound must grow with elapsed steps: five errors in five steps signal a bad task; five in "
  "eighty do not. This is the quitting logic of job matching (Jovanovic 1979). The two propositions give opposite prescriptions: "
  "contagion calls for weighting recent errors more, heterogeneity calls for normalising by elapsed time. "
  "Which one an IS designer should build depends on which source dominates, exactly the decomposition our econometrics delivers. "
  f"In the calibrated example (Llama-70B) N*(t) is {LJ['swe-agent-llama-70b']['count_threshold']['0']}, "
  f"{LJ['swe-agent-llama-70b']['count_threshold']['10']}, {LJ['swe-agent-llama-70b']['count_threshold']['40']} and "
  f"{LJ['swe-agent-llama-70b']['count_threshold']['80']} at t = 0, 10, 40 and 80, close to the asymptotic line "
  f"μ*(b + t) − a with μ* = {(0.06*40-1)/5:.2f}.")
H2("3.5 For which tasks is monitoring worth building?")
PROP("Proposition 6 (value peaks at indifference).", "For either source of value, the value of monitoring relative to the best "
     "static choice, as a function of the hand-off cost H, is maximised at H = C̄, the expected cost of letting the agent finish "
     "(C̄ = C_U with contagion; C̄ = (k + cE[μ])/q with heterogeneity). It is convex and increasing below C̄ and nonincreasing above it.")
P("The proof is short (Appendix A): the optimal cost is the lower envelope of policies whose costs are affine in H, hence concave in H. "
  "Information is valuable only when it can change the decision, and it is most likely to do so for marginal tasks, where taking "
  "the task back and letting the agent finish cost about the same. Tasks that are cheap to reassign, or very expensive to reassign, "
  "gain little from monitoring. This is a design prediction an IS manager can act on: invest in real-time error monitoring for "
  "tasks near the margin of delegation.")
d.add_picture("fig_theory_H.png", width=Inches(4.6))
P(f"Figure 1. Value of monitoring against the hand-off cost H (Llama-70B calibration). Dashed lines mark C̄ for each source "
  f"({HJ['C_U_contagion']:.2f} and {HJ['C_U_learning']:.2f}); the numerical maxima fall exactly there, at "
  f"{max(r['contagion_value'] for r in HJ['rows']):.2f} and {max(r['learning_value'] for r in HJ['rows']):.2f}, "
  f"about {100*max(r['contagion_value'] for r in HJ['rows'])/HJ['C_U_contagion']:.0f}–"
  f"{100*max(r['learning_value'] for r in HJ['rows'])/HJ['C_U_learning']:.0f}% of the expected cost.", size=9)

H1("4. Linking the theory to the evidence")
P("We calibrate the model with the heterogeneity-adjusted Hawkes estimates from the SWE-agent data and illustrative costs "
  f"(k = {p['k']:g}, c = {p['c']:g}, q = {p['q']:g}, H = {p['H']:g}). The two sources of value are computed separately: the "
  "contagion value with μ fixed at its mean, and the learning value with α = 0 and μ drawn from the estimated Gamma distribution.")
rows = []
for m, lab in (("swe-agent-llama-8b", "Llama-8B"), ("swe-agent-llama-70b", "Llama-70B"), ("swe-agent-llama-405b", "Llama-405B")):
    r = LJ[m]; rows.append([lab, f"{r['branching']:.2f}", f"{r['re_cv']:.2f}", f"{r['contagion_value']:.3f}", f"{r['learning_value']:.3f}"])
TABLE(["Agent", "Branching n", "CV of μ", "Contagion value (H = 40)", "Learning value (H = 40)"], rows)
P(f"Three findings follow. First, at H = 40, far above the cost of letting the agent finish, both values are small (under 0.5% of "
  f"the expected cost of about 21–24), so a simple rule loses little. In the main calibration the optimal threshold x* = {o['x_star']:.2f} "
  f"is rarely reached; W(0) = {o['W0']:.2f} against C_U = {N['C_U_never_hand_off']:.2f}. This matches our observational result that "
  "intensity-based early warning barely beats counting (AUC 0.55). Second, all three agents are subcritical once heterogeneity is "
  "accounted for (n = 0.38–0.56), whereas a model that ignores heterogeneity puts them at 1.5–2.1, in the region where "
  "Proposition 4 says monitoring is worth a great deal. Ignoring heterogeneity would therefore lead a designer to overinvest in "
  "contagion monitoring and to use the wrong kind of rule (recency-weighted instead of rate-based). Third, the learning value is "
  "larger than the contagion value for every agent, and it rises quickly with heterogeneity: with the 70B mean, it is "
  + ", ".join(f"{r['learning_value']:.2f} at CV = {r['cv']}" for r in LJ["cv_sensitivity_70b_mean"]) + ".")

H1("5. Testable predictions")
for t in [
    "H1 (causal contagion). Injecting an error into an agent's trajectory raises the hazard of a further agent error over the next "
    "steps, with a jump α and decay δ that match the observational estimates, net of task fixed effects.",
    "H2 (criticality). The value of intensity-based monitoring over a count rule rises with the branching ratio. Agents or settings "
    "with higher n (for example longer contexts or weaker error recovery) benefit more.",
    "H3 (threshold). The optimal intensity threshold x* falls with n and with c/H.",
    "H4 (rule form). In task pools with high heterogeneity and low contagion, rate-based rules (errors per step) outperform both "
    "raw counts and recency-weighted scores; the ranking reverses when contagion dominates.",
    "H5 (marginal tasks). The cost saving from monitoring is largest for tasks whose hand-off cost is close to the expected cost of "
    "letting the agent finish, and small for tasks far from that margin.",
]: d.add_paragraph(t, style="List Bullet")
P("H1, H2 and H4 can be tested with a fault-injection experiment on a public agent benchmark: inject a controlled error at a random "
  "step, compare against a sham injection on the same task, and vary the injection rate to move n. H3 and H5 can be tested by "
  "simulation on the experimental estimates, or in a vignette study with practitioners choosing hand-off points.")

H1("6. Limitations and notes for revision")
for t in [
    "The empirical model is a Bernoulli version (probability of at least one error 1 − exp(−λ)) with a time trend in the baseline; "
    "the theory uses Poisson counts and no trend. A rising baseline would lower thresholds over time, partly offsetting the rate rule "
    "in Proposition 5.",
    "The costs k, c, q, H are illustrative. The qualitative results (Propositions 1–6) do not depend on them; the numbers do.",
    "Completion is assumed independent of errors (A3). If errors also lower the completion probability, the hand-off motive is "
    "stronger and thresholds fall; the threshold structure survives if q(x) is nonincreasing.",
    "Contagion and heterogeneity are analysed separately. The joint model has state (t, N_t, x_t) and no conjugate posterior; "
    "solving it numerically is the next step.",
    "Simulated costs (threshold rule 23.80; never 23.80; best count rule 23.63) agree with the analytic W(0) = 23.51 within Monte Carlo "
    "error (about 0.2), confirming that at the main calibration the rules are indistinguishable.",
    "The firm here is a single decision maker. A principal-agent version (the human who takes over has private effort costs, or the "
    "agent vendor chooses α) is a natural extension and would strengthen the ISR fit.",
]: d.add_paragraph(t, style="List Bullet")

H1("Appendix A. Proofs")
P("Proposition 1. Let T be the Bellman operator on bounded functions on [0, ∞). For bounded W1, W2, |TW1 − TW2| ≤ (1 − q)‖W1 − W2‖, "
  "so T is a contraction and has a unique fixed point W with 0 ≤ W ≤ H. If W is nondecreasing, then for each e the map x ↦ W(δx + αe) is "
  "nondecreasing, and because Poisson(μ + x) increases in x in first-order stochastic dominance, E[W(δx + αe)] is nondecreasing in x. "
  "Hence C, and TW = min{H, C}, are nondecreasing. The set of nondecreasing bounded functions is closed, so the fixed point is "
  "nondecreasing. Since c > 0, C is strictly increasing, and the stopping region {x : C(x) ≥ H} is an interval [x*, ∞).")
P("Proposition 2. With δ = 1, x_t = αN_t and the rule x_t ≥ x* is the rule N_t ≥ x*/α. With δ < 1 and α > 0, compare a history with "
  "one error at step t − 1 and one with one error at step t − j, j > 1: the counts are equal but the intensities are α and αδ^{j−1} < α. "
  "Extending this to histories near x*, both histories occur with positive probability, and any count rule takes the same action on "
  "both, while the optimal rule takes different actions. Because C is strictly increasing, the count rule's action is strictly worse "
  "on one of them.")
P("Proposition 3. With no hand-off, E[x_{t+1}] = ρE[x_t] + αμ and x_0 = 0, so E[x_t] = αμ(1 − ρ^t)/(1 − ρ). The step t is reached "
  "with probability (1 − q)^t, so C_U = Σ_t (1 − q)^t [k + cμ + cE[x_t]], which sums to the expression given when (1 − q)ρ < 1 and "
  "diverges otherwise. Derivatives in α and δ are positive term by term.")
P("Proposition 4. W(0) ≤ min{H, C_U} because both static choices are feasible policies. If α = 0, x_t ≡ 0, the history carries no "
  "information, and W(0) = min{H, C_U}. W(0) ≤ H for all parameters, while C_U → ∞ as (1 − q)ρ ↑ 1 by Proposition 3.")
P("Proposition 5. Under A4 the posterior after (t, N) is Gamma(a + N, b + t), and the predictive count is negative binomial with "
  "size a + N and success probability (b + t)/(b + t + 1). This family increases in N in first-order stochastic dominance, and the "
  "expected step cost k + c(a + N)/(b + t) is strictly increasing in N. Backward induction on a truncated horizon (whose terminal "
  "value matters with probability (1 − q)^T) gives a value nondecreasing in N for each t, so the stopping region at t is {N ≥ N*(t)}. "
  "As t → ∞ the posterior concentrates at μ, the problem approaches the known-μ problem with α = 0, whose solution is to hand off iff "
  "(k + cμ)/q ≥ H, that is μ ≥ μ*.")
P("Proposition 6. Every policy π has expected cost A_π + H·P_π, with A_π the expected cost of agent steps and P_π the probability of "
  "a hand-off; neither depends on H. The optimal cost W(0; H) = inf_π (A_π + H P_π) is therefore concave and nondecreasing in H, "
  "and W(0; 0) = 0. Write V(H) = min{H, C̄} − W(0; H). For H ≤ C̄, V(H) = H − W(0; H) is convex with V(0) = 0 and V ≥ 0, so on "
  "[0, C̄] it is maximised at C̄ and, being convex and nonnegative from zero, is nondecreasing. For H ≥ C̄, V(H) = C̄ − W(0; H) is "
  "nonincreasing. Hence V is maximised at H = C̄.")

H1("References (to verify before submission)")
for r in [
    "Blackwell, D. (1953). Equivalent comparisons of experiments. Annals of Mathematical Statistics, 24(2), 265–272.",
    "Fügener, A., Grahl, J., Gupta, A., & Ketter, W. (2022). Cognitive challenges in human–artificial intelligence collaboration: "
    "Investigating the path toward productive delegation. Information Systems Research, 33(2), 678–696.",
    "Hawkes, A. G. (1971). Spectra of some self-exciting and mutually exciting point processes. Biometrika, 58(1), 83–90.",
    "Heckman, J. J. (1981). Heterogeneity and state dependence. In S. Rosen (Ed.), Studies in Labor Markets (pp. 91–140). University of Chicago Press.",
    "Holmström, B. (1979). Moral hazard and observability. Bell Journal of Economics, 10(1), 74–91.",
    "Jovanovic, B. (1979). Job matching and the theory of turnover. Journal of Political Economy, 87(5), 972–990.",
    "Kirsch, L. J. (1997). Portfolios of control modes and IS project management. Information Systems Research, 8(3), 215–239.",
    "Puterman, M. L. (1994). Markov Decision Processes: Discrete Stochastic Dynamic Programming. Wiley.",
    "Shiryaev, A. N. (1963). On optimum methods in quickest detection problems. Theory of Probability and Its Applications, 8(1), 22–46.",
    "Wald, A. (1947). Sequential Analysis. Wiley.",
    "Yang, J., Jimenez, C. E., Wettig, A., Lieret, K., Yao, S., Narasimhan, K., & Press, O. (2024). SWE-agent: Agent-computer "
    "interfaces enable automated software engineering. NeurIPS 2024.",
]: d.add_paragraph(r)

H1("한국어 요약")
for t in [
    "모형: 기업이 AI 에이전트에 다단계 작업을 맡기고, 매 단계 계속할지 사람에게 넘길지(비용 H) 결정한다. 오류는 자기흥분(Hawkes) 과정을 따른다(분기비 n = α/(1−δ)).",
    "명제 1: 최적 규칙은 '초과 강도 x가 임계값 x*를 넘으면 넘긴다'. n이 클수록 x*는 낮아진다(빨리 회수).",
    "명제 2: 오류 개수만 세는 규칙은 오류 영향이 감쇠하지 않을 때(δ=1)만 최적. 아니면 최근 오류에 가중치를 둬야 한다(Holmström 정보성 원리).",
    "명제 3–4: 방치 비용 C_U의 닫힌 해. 임계(n→1) 근처에서 모니터링 가치가 급증한다.",
    "명제 5: 과제 이질성만 있으면 베이지안 학습 문제가 되고, 최적 규칙은 '경과 단계 대비 오류율' 규칙(직업 매칭 이론의 이직 논리).",
    "명제 6: 모니터링 가치는 넘기는 비용 H가 '끝까지 맡길 때의 기대비용'과 같을 때 최대 → 경계선에 있는 과제에만 모니터링 투자가 의미 있다.",
    "실증 연결: 이질성을 보정하면 세 모델 모두 n = 0.38–0.56(임계 미만), 보정하지 않으면 1.5–2.1로 과대평가 → 잘못된 모니터링 설계로 이어짐. 보정치에서는 단순 규칙과 차이가 작으며, 이는 관찰자료에서 조기경보 AUC 0.55와 일치.",
    "검증 가능한 가설 H1–H5와 오류 주입 실험 설계를 제시. 한계: 비용 모수는 예시값, 이질성과 전염의 결합 모형은 아직 미해결.",
]: d.add_paragraph(t, style="List Bullet")
d.save("Theory_Draft.docx"); print("saved")
