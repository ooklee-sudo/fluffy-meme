"""Builds the ISR manuscript (blinded) and its title page.
Numbers are read from the analysis outputs so that the text and the results cannot drift apart."""
import json
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

HERE = Path(__file__).resolve().parent; ROOT = HERE.parent
INJ = json.load(open(ROOT / "inject" / "inject_results.json"))
DER = json.load(open(ROOT / "theory" / "derail.json"))
NUM = json.load(open(ROOT / "theory" / "numerics.json"))
HS = json.load(open(ROOT / "theory" / "h_sensitivity.json"))
OBS = json.load(open(ROOT / "hawkes_re_results_all.json"))
PIL = json.load(open(ROOT / "pilot_results.json"))
LAB = {"llama8b": "Llama-3.1-8B", "llama70b": "Llama-3.1-70B", "deepseek": "DeepSeek-V3.1"}
OBSM = {"swe-agent-llama-8b": "Llama-3.1-8B", "swe-agent-llama-70b": "Llama-3.1-70B", "swe-agent-llama-405b": "Llama-3.1-405B"}
TITLE = "When Should the Firm Take the Task Back? Error Dynamics and the Economics of Monitoring Autonomous AI Agents"


def new_doc():
    d = Document()
    for s in d.sections:
        s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Inches(1)
    st = d.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    st.paragraph_format.line_spacing = 2.0; st.paragraph_format.space_after = Pt(0)
    for name in ("Heading 1", "Heading 2", "Heading 3"):
        h = d.styles[name]; h.font.name = "Times New Roman"; h.font.size = Pt(12); h.font.bold = True
        h.font.italic = name == "Heading 3"; h.font.color.rgb = None
        h.element.rPr.rFonts.set(qn("w:asciiTheme"), "") if False else None
        rf = h.element.rPr.find(qn("w:rFonts"))
        if rf is not None:
            for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
                if rf.get(qn(a)) is not None: del rf.attrib[qn(a)]
            rf.set(qn("w:ascii"), "Times New Roman"); rf.set(qn("w:hAnsi"), "Times New Roman")
        h.paragraph_format.line_spacing = 2.0; h.paragraph_format.space_before = Pt(12); h.paragraph_format.space_after = Pt(0)
    # page numbers
    p = d.sections[0].footer.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(); f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.text = "PAGE"; f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "end")
    r._r.append(f1); r._r.append(it); r._r.append(f2)
    return d


d = new_doc()
def P(text, indent=True, align=None, italic=False, bold=False, size=None, spacing=None):
    p = d.add_paragraph()
    if indent: p.paragraph_format.first_line_indent = Inches(0.5)
    if align is not None: p.alignment = align
    if spacing: p.paragraph_format.line_spacing = spacing
    r = p.add_run(text); r.italic = italic; r.bold = bold
    if size: r.font.size = Pt(size)
    return p
def RICH(parts, indent=True):
    p = d.add_paragraph()
    if indent: p.paragraph_format.first_line_indent = Inches(0.5)
    for t, sty in parts:
        r = p.add_run(t); r.bold = "b" in sty; r.italic = "i" in sty
    return p
def EQ(text, num):
    from docx.enum.text import WD_TAB_ALIGNMENT
    p = d.add_paragraph(); ts = p.paragraph_format.tab_stops
    ts.add_tab_stop(Inches(3.25), WD_TAB_ALIGNMENT.CENTER); ts.add_tab_stop(Inches(6.5), WD_TAB_ALIGNMENT.RIGHT)
    p.add_run("\t"); r = p.add_run(text); r.italic = True; r.font.size = Pt(11); p.add_run(f"\t({num})")
def PROP(label, text):
    RICH([(label + " ", "b"), (text, "i")])
def H1(t): d.add_heading(t, level=1)
def H2(t): d.add_heading(t, level=2)
def H3(t): d.add_heading(t, level=3)
def TABLE(caption, head, rows, note=None, widths=None):
    P(caption, indent=False, bold=True, spacing=1.0)
    t = d.add_table(rows=1, cols=len(head)); t.style = "Table Grid"
    for i, h in enumerate(head):
        c = t.rows[0].cells[i]; c.text = ""; r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(10)
    for row in rows:
        cs = t.add_row().cells
        for i, v in enumerate(row):
            cs[i].text = ""; r = cs[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(10)
    for row in t.rows:
        for c in row.cells:
            for pp in c.paragraphs: pp.paragraph_format.line_spacing = 1.0
    if note: P(note, indent=False, size=10, spacing=1.0)
    d.add_paragraph()
def FIG(path, caption, width=5.8):
    d.add_picture(str(path), width=Inches(width)); d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    P(caption, indent=False, size=10, spacing=1.0); d.add_paragraph()
def PAGEBREAK(): d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

f2 = lambda x: f"{x:.2f}"; f3 = lambda x: f"{x:.3f}"
ci = lambda c, k=3: f"[{c[0]:.{k}f}, {c[1]:.{k}f}]"
S = {m: INJ[m]["success"] for m in INJ}; Wn = {m: INJ[m]["window"] for m in INJ}; LG = {m: INJ[m]["lag_logit"] for m in INJ}
TH = DER["theta"]; n_runs = sum(INJ[m]["n_runs"] for m in INJ)
re = {m: OBS[m]["re_hawkes"] for m in OBSM}; ho = {m: OBS[m]["hawkes_only"] for m in OBSM}
bt = {m: OBS["bootstrap_branching_" + m] for m in OBSM}
cal = {(r["model"], r["F"]): r for r in DER["calibrated"]}

# ---------------------------------------------------------------- title block and abstract (blinded)
P(TITLE, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
P("Abstract", indent=False, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
P("Firms increasingly delegate multistep work to autonomous AI agents while keeping the option to hand a task back to a person. "
  "We ask when that option should be exercised. We model delegation as an optimal stopping problem in which agent errors may excite "
  "further errors, tasks differ in difficulty, and an error may derail a task so that its output is wrong. The model yields simple "
  "hand-off rules and shows that the signal a monitoring system should track depends on which of these channels operates. "
  "Recency-weighted intensity matters only under strong contagion, error rates matter under heterogeneity, and the error count "
  "suffices under derailment. The value of monitoring peaks for tasks at the margin of delegation. We then estimate the channels. "
  "In 80,036 public software-engineering trajectories, errors cluster strongly, but most clustering reflects heterogeneity. In a "
  f"randomized fault-injection experiment with {n_runs:,} agent runs, injected errors do not trigger lasting error cascades, yet a "
  f"single error lowers task success by up to {abs(S['deepseek']['single_minus_control']['diff'])*100:.0f} percentage points. "
  "The economic cost of agent errors therefore lies less in cascades than in derailment, and the hand-off rules that follow are "
  "simple to implement.", indent=False, spacing=2.0)
P("Keywords: AI agents; delegation; human–AI collaboration; monitoring; optimal stopping; Hawkes process; field experiment",
  indent=False, italic=True)
PAGEBREAK()

# ---------------------------------------------------------------- 1 Introduction
H1("1. Introduction")
P("A growing share of knowledge work is now carried out by software agents built on large language models. Unlike a predictive "
  "model that returns a score for a person to act on, an agent takes a sequence of actions on its own: it queries databases, edits "
  "code, books and cancels reservations, and talks to customers. Organizations that adopt such agents rarely give up control "
  "altogether. They keep a person who can intervene, and they need a rule that tells the system when to call that person. "
  "Customer-service platforms escalate a conversation to a human representative, coding assistants stop and ask for review, and "
  "operations teams set limits on how many failed tool calls an agent may make before it is halted. These rules are information "
  "systems design choices, and at present they are set largely by intuition.")
P("The design problem is economic. Letting the agent continue is cheap per step but risky, because an agent that has started to go "
  "wrong may keep going wrong or may finish the task with a wrong result. Taking the task back is safe but costly, because a person "
  "must pick up the work. The firm observes a stream of signals, of which tool errors are the most immediate, and must decide at "
  "each step whether the evidence justifies the cost of intervention. The question we address is therefore: when should a firm "
  "take a task back from an autonomous agent, and what should its monitoring system track to make that decision well?")
P("The answer depends on why errors occur. Practitioners often describe agent failures as cascades: one mistake leads the agent "
  "into a confused state, and further mistakes follow. If that is how errors arise, a monitoring system should weight recent errors "
  "heavily and react quickly to bursts. Errors may instead cluster because some tasks are simply harder than others, in which case "
  "the burst is a symptom of a difficult task rather than a cause of further trouble. A third possibility, which our experiment "
  "brings to the fore, is that an error does its damage not by producing more errors but by derailing the task, so that the agent "
  "carries on and completes the job incorrectly. These three channels, which we call contagion, heterogeneity, and derailment, have "
  "different implications for what should be monitored and when control should be withdrawn.")
P("We develop a model of delegation in which a firm assigns a task to an agent and, at every step, chooses between letting the agent "
  "continue and handing the task to a person. Errors follow a self-exciting point process of the kind introduced by Hawkes (1971), "
  "which allows past errors to raise the rate of future ones. Task-level heterogeneity enters through an unknown baseline error "
  "rate, and derailment enters through a probability that an error spoils the eventual output. Drawing on the theory of optimal "
  "stopping (Wald 1947, Shiryaev 1963, Chow et al. 1971) and on the economics of information (Blackwell 1953, Holmström 1979), we "
  "characterize the optimal hand-off rule under each channel and under their combination.")
P("The analysis delivers three results that matter for design. First, the sufficient statistic for the hand-off decision differs "
  "across channels. Under contagion it is a recency-weighted error intensity; under heterogeneity it is the error rate per step; "
  "under derailment it is the cumulative error count, so that a rule of the form “hand off after the N-th error” is exactly "
  "optimal, and we give N in closed form. Second, the value of contagion-based monitoring is small for agents whose error process is "
  "far from critical and grows without bound as the process approaches criticality. Third, whatever the channel, the value of "
  "monitoring is greatest for tasks at the margin of delegation, where handing the task back costs about as much as letting the "
  "agent finish. This last result gives managers a way to decide where monitoring infrastructure is worth building.")
P(f"We then bring two sources of evidence to bear on the channels. The first is a corpus of 80,036 public trajectories of an "
  f"open-source software-engineering agent driven by three sizes of an open-weight model. Errors in these trajectories cluster "
  f"strongly, and a naive self-exciting model implies that each error triggers more than one further error. Once task "
  f"heterogeneity is modeled, the implied branching ratio falls to between {re['swe-agent-llama-70b']['branching']:.2f} and "
  f"{re['swe-agent-llama-405b']['branching']:.2f}, well below the critical value of one. Observational data cannot, however, "
  f"separate contagion from persistence within a run. The second source is therefore a randomized experiment. Using a public "
  f"benchmark of customer-service tasks, we ran {n_runs:,} agent conversations with three models and injected errors at random "
  f"points, either as system failures or as failures that read like the agent's own mistake. Injected system failures did not raise "
  f"later error rates, and errors that read like the agent's own mistakes raised the error rate only on the next call. Injected "
  f"errors did, however, lower task success, by as much as {abs(S['deepseek']['single_minus_control']['diff'])*100:.0f} percentage "
  f"points for the strongest model. The evidence thus points away from cascades and toward derailment.")
P("The paper makes three contributions. For research on human–AI delegation in information systems (Baird and Maruping 2021, "
  "Fügener et al. 2022), it offers a formal account of when control should be withdrawn from an agentic system and shows that the "
  "answer turns on an identifiable property of the agent's error process. For research on IS control (Kirsch 1997), it connects the "
  "choice of what to monitor to the informativeness principle: a monitoring signal is worth collecting only to the extent that it is "
  "informative about the state that drives costs. For practice, it shows that simple count-based escalation rules, which are already "
  "common, are not merely convenient but optimal under the channel that our experiment finds to dominate, and it shows how the "
  "threshold can be calibrated from a modest experiment of the kind we report.")
P("The remainder of the paper is organized as follows. Section 2 reviews related work. Section 3 presents the model, and Section 4 "
  "derives the results. Section 5 reports the observational and experimental evidence and calibrates the model. Section 6 discusses "
  "implications and limitations, and Section 7 concludes. Proofs and experimental details are in the appendices.")

# ---------------------------------------------------------------- 2 Related work
H1("2. Related Literature")
H2("2.1. Delegation to Agentic Systems")
P("Information systems research has long examined how people allocate work between themselves and technology. Recent work treats "
  "AI systems as agents to which tasks are delegated rather than as tools that people use. Baird and Maruping (2021) develop a "
  "framework for delegation to and from agentic IS artifacts and emphasize that delegation involves an ongoing allocation of rights "
  "and responsibilities. Berente et al. (2021) describe the management of AI as a problem of balancing autonomy, learning, and "
  "inscrutability. Fügener et al. (2022) show experimentally that people delegate poorly to AI because they misjudge their own "
  "and the system's competence, which suggests that delegation decisions are better made by rule than by unaided judgment. Our "
  "work shares this focus on delegation but addresses a question that becomes central once agents act over many steps: not whether "
  "to delegate, but when to revoke a delegation already made.")
H2("2.2. Control and Monitoring in Information Systems")
P("A second stream studies control, the means by which a principal ensures that work is carried out as intended. Kirsch (1997) "
  "shows that managers of IS projects combine formal and informal control modes and adapt them to what can be observed and "
  "measured. Monitoring an autonomous agent is a formal behavior control in this sense, and the question of which behaviors to "
  "measure is the familiar one of choosing control mechanisms that are informative about outcomes. In agency theory, Holmström "
  "(1979) shows that a signal should enter a contract if and only if it carries information about the agent's action beyond what "
  "other signals already provide. We apply the same logic to a stopping problem: the timing of errors should enter a hand-off rule "
  "only when it is informative about the hidden state that determines future costs.")
H2("2.3. Optimal Stopping, Learning, and the Value of Information")
P("The decision to take a task back is a stopping problem. Sequential analysis (Wald 1947) and quickest detection (Shiryaev 1963) "
  "study when to stop observing a process and act, and the theory of monotone stopping problems (Chow et al. 1971) identifies "
  "conditions under which a myopic rule is optimal; we use that result to obtain a closed-form threshold under derailment. When "
  "the agent's error rate on a task is unknown, the firm learns about it as the task unfolds, much as a worker learns about the "
  "quality of a job match and quits when the posterior turns unfavorable (Jovanovic 1979). Blackwell (1953) provides the general "
  "notion of when one information structure is more valuable than another, and our result on the value of monitoring at the margin "
  "of delegation is a specific instance of the principle that information is valuable only when it can change a decision.")
H2("2.4. Heterogeneity, State Dependence, and Agent Reliability")
P("Distinguishing true contagion from heterogeneity is a classic problem in econometrics. Heckman (1981) shows that persistence in "
  "observed outcomes can arise either because past outcomes change future behavior or because units differ in unobserved ways, "
  "and that the two have different policy implications. The same issue arises for agent errors, and we address it with a "
  "random-effects self-exciting model and, more decisively, with randomized injection. In computer science, benchmarks such as "
  "SWE-agent (Yang et al. 2024) and τ-bench (Yao et al. 2024, Barres et al. 2025) measure whether agents complete tasks, and a "
  "growing literature documents how agents fail. These studies report success rates; they do not model the dynamics of errors "
  "within a run or derive the decision rules that a firm deploying agents needs.")

# ---------------------------------------------------------------- 3 Model
H1("3. Model")
P("A firm assigns a task to an AI agent. Time is discrete and indexed by steps t = 0, 1, 2, …, where a step is one action of the "
  "agent, such as a tool call. At the start of each step the firm either lets the agent take the step or hands the task to a "
  "person. Handing off ends the agent's involvement at cost H > 0, which includes the person's time to take over and complete the "
  "task. A step costs k > 0 plus c > 0 for each error made in it. After each step the agent completes the task with probability "
  "q ∈ (0, 1).")
P("Errors follow a discrete-time self-exciting process. The number of errors in step t is")
EQ("e_t | x_t ~ Poisson(μ + x_t),    x_{t+1} = δx_t + αe_t,    x_0 = 0,", 1)
P("where μ > 0 is the baseline error rate, x_t ≥ 0 is the excess intensity built up by past errors, α ≥ 0 is the increase in "
  "intensity caused by one error, and δ ∈ [0, 1] is the rate at which that increase persists from one step to the next. "
  "Equivalently, x_t = α Σ_{s<t} δ^{t−1−s} e_s. The branching ratio n = α/(1 − δ) is the expected number of further errors that a "
  "single error triggers, directly or through its descendants. Because E[x_{t+1} | x_t] = ρ x_t + αμ with ρ = δ + α, the error "
  "process is stable if and only if n < 1; we call an agent subcritical, critical, or supercritical according to whether n is "
  "below, equal to, or above one.")
P("We allow two further channels. Heterogeneity: the baseline rate μ is specific to the task and drawn from a gamma distribution "
  "with shape a and rate b; the firm knows the distribution but not the draw. Derailment: each error independently derails the "
  "task with probability θ ∈ [0, 1]. A derailed agent continues to work and still completes the task with probability q per step, "
  "but its output is wrong, and the firm then bears an additional cost F > 0 to detect and repair it. Derailment is not observed "
  "directly; the firm sees only errors. The parameter θ captures the experimental finding, reported in Section 5, that errors lower "
  "the probability of a correct outcome without necessarily producing further errors.")
P("We maintain the following assumptions throughout. (A1) The firm observes the errors made in each step. (A2) The parameters "
  "(μ or its distribution, α, δ, θ, k, c, q, H, F) are known and constant over time. (A3) Completion occurs with probability q per "
  "step regardless of the error history; errors affect whether the completed output is correct only through derailment. Assumption "
  "A3 replaces the stronger assumption, common in reliability models, that errors leave the outcome unaffected. We analyze each "
  "channel in isolation before turning to their combination. With μ known and θ = 0, the state is the excess intensity x, and the "
  "minimum expected cost W satisfies")
EQ("W(x) = min{H, C(x)},  C(x) = k + c(μ + x) + (1 − q) E[W(δx + αe)],  e ~ Poisson(μ + x).", 2)

# ---------------------------------------------------------------- 4 Analysis
H1("4. Analysis")
H2("4.1. Contagion: A Threshold on Excess Intensity")
PROP("Proposition 1.", "Equation (2) has a unique bounded solution W, which is nondecreasing in x. The firm hands the task back if "
     "and only if x_t ≥ x*, where x* = inf{x : C(x) ≥ H}.")
P("The intuition is straightforward. A higher excess intensity raises the expected error cost of the current step and, because the "
  "Poisson family is ordered by first-order stochastic dominance, makes the next state worse as well. The proof in Appendix A uses "
  "the fact that the Bellman operator is a contraction with modulus 1 − q and preserves monotonicity. In numerical work the threshold "
  f"falls as the branching ratio rises, from {NUM['sensitivity_branching'][0]['x_star']:.2f} at n = 0 to "
  f"{NUM['sensitivity_branching'][-1]['x_star']:.2f} at n = 1.05 under the calibration used in Section 5: more contagious agents "
  "should be taken back sooner.")
PROP("Proposition 2.", "If δ = 1, the rule that hands off when the cumulative error count N_t reaches a fixed bound is optimal. "
     "If δ < 1, α > 0, and x* lies in the interior of the attainable range, every rule based on N_t alone is strictly suboptimal.")
P("Proposition 2 is the informativeness principle applied to a stopping problem. What determines future costs is the excess "
  "intensity, and the error count is a sufficient statistic for it only when the effect of an error never decays. When it does "
  "decay, two histories with the same number of errors but different timing imply different intensities, and a rule that ignores "
  "timing must treat them alike. A monitoring system for a contagious agent should therefore weight recent errors more heavily "
  "than old ones.")
PROP("Proposition 3.", "If the firm never hands off and θ = 0, its expected cost is "
     "C_U = (k + cμ)/q + [cαμ/(1 − ρ)]·[1/q − 1/(1 − (1 − q)ρ)], which is finite if and only if (1 − q)ρ < 1.")
PROP("Proposition 4.", "Let V_C = min{H, C_U} − W(0) be the value of contagion-based monitoring relative to the better of the two "
     "static choices (hand off immediately or never). Then V_C ≥ 0, V_C = 0 when α = 0, and C_U − W(0) grows without bound as "
     "(1 − q)ρ approaches one.")
P("Propositions 3 and 4 locate the value of contagion-based monitoring near criticality. For an agent well below criticality, an "
  "error raises the intensity briefly, and the threshold in Proposition 1 is rarely reached; the optimal rule then differs little "
  "from never intervening. In the calibration of Section 5 the value relative to never handing off is zero up to n = 0.4 and rises "
  f"to {[r for r in NUM['sensitivity_branching'] if r['branching'] == 0.8][0]['value_vs_never']:.1f} and "
  f"{[r for r in NUM['sensitivity_branching'] if r['branching'] == 1.0][0]['value_vs_never']:.1f} units of step cost at n = 0.8 and "
  "n = 1.0.")
H2("4.2. Heterogeneity: Monitoring as Learning")
P("Suppose next that α = θ = 0 but that μ is unknown. After t steps with N_t errors the posterior is gamma with shape a + N_t and "
  "rate b + t, and errors in the next step follow a negative binomial distribution with mean (a + N_t)/(b + t). The state is "
  "(t, N_t).")
PROP("Proposition 5.", "Under heterogeneity alone, the firm hands off at step t if and only if N_t ≥ N*(t). As t grows, the rule "
     "approaches a rate rule: hand off when (a + N_t)/(b + t) exceeds μ* = (qH − k)/c.")
P("The count remains sufficient here, but its bound must rise with the number of steps taken. Five errors in five steps signal a "
  "hard task; five errors in eighty do not. This is the logic of quitting a poor job match. Propositions 2 and 5 give opposite "
  "prescriptions, one favoring recency and the other normalizing by elapsed time, and the econometric question of which channel "
  "dominates therefore has direct design consequences.")
H2("4.3. Derailment: The Error Count Is Sufficient")
P("Now let α = 0 and μ be known, but let each error derail the task with probability θ > 0. After N errors the posterior "
  "probability that the task is derailed is π_N = 1 − (1 − θ)^N, which depends on the history only through the count. A step "
  "costs k + cμ in expectation; if the task completes, the firm bears F with the probability that it has been derailed by then.")
PROP("Proposition 6.", "Under derailment, the optimal policy hands the task back as soon as the cumulative error count reaches "
     "N*, the smallest integer N such that")
EQ("(1 − θ)^N ≤ [1 − (qH − k − cμ)/(qF)] · e^{μθ},", 3)
P("with N* = 0 if qH ≤ k + cμ (the agent is never worth using) and N* = ∞ if the right-hand side is not positive (the agent is "
  "always worth using).", italic=True)
P("The proof (Appendix A) uses the monotone case of optimal stopping. Because the count never decreases and the one-step gain from "
  "continuing falls as the count rises, the set of states in which stopping beats one more step is absorbing, and the myopic rule "
  "is optimal (Chow et al. 1971). The proposition gives a direct justification for count-based escalation rules of the kind "
  "already used in practice and shows how to set the bound. The threshold falls as θ and F rise and as H falls. It does not depend "
  "on when the errors occurred, which is the opposite of the conclusion under contagion. Value iteration on the count reproduces "
  "the closed form in every parameter configuration we examined.")
H2("4.4. Combining the Channels")
PROP("Proposition 7.", "When contagion and derailment operate together, the state is (x, N). The minimum expected cost is "
     "nondecreasing in both arguments, the stopping region is an upper set, and the critical count N*(x) is nonincreasing in x.")
P("When both channels are present, the optimal rule is a count threshold that is lowered temporarily after a burst of errors. "
  "How much the burst matters depends on δ. When excitation decays within one or two steps, as our experiment suggests, the "
  "adjustment applies only to the step immediately after an error, and the rule is close to a pure count rule.")
H2("4.5. Where Monitoring Is Worth Building")
PROP("Proposition 8.", "For each channel and for their combination, let C̄ be the expected cost of never handing off and let "
     "V(H) = min{H, C̄} − W(0; H) be the value of monitoring as a function of the hand-off cost. Then V is nondecreasing on "
     "[0, C̄], nonincreasing on [C̄, ∞), and maximized at H = C̄.")
P("The proof is short. Every policy has an expected cost of the form A + H·P, where P is the probability that it hands off, so the "
  "optimal cost is a lower envelope of affine functions of H and is therefore concave. The value of monitoring is then convex below "
  "C̄ and nonincreasing above it. The result says that monitoring pays most for tasks at the margin of delegation, where taking "
  "the task back costs about as much as letting the agent finish. Tasks that are cheap to reassign can simply be reassigned, and "
  "tasks that are very expensive to reassign will be left with the agent whatever the monitor reports. Figure 1 shows the value of "
  "contagion-based and learning-based monitoring as functions of H; both peak exactly at the corresponding C̄.")
FIG(ROOT / "theory" / "fig_theory_H.png",
    f"Figure 1. Value of monitoring as a function of the hand-off cost H. The dashed lines mark the expected cost of letting the agent "
    f"finish ({HS['C_U_contagion']:.2f} under contagion, {HS['C_U_learning']:.2f} under heterogeneity). Parameters: k = 1, c = 5, "
    f"q = 0.06, with error parameters from the Llama-3.1-70B estimates in Table 1.", width=4.6)

# ---------------------------------------------------------------- 5 Evidence
H1("5. Empirical Evidence")
P("The theory makes the design of a monitoring system depend on three quantities: the strength and persistence of contagion (α "
  "and δ), the dispersion of task difficulty, and the probability that an error derails a task (θ). We estimate them in two "
  "steps. Observational data on a large number of agent runs tell us how much errors cluster and how much of the clustering can be "
  "attributed to heterogeneity. A randomized experiment then identifies the causal effect of an error on later errors and on task "
  "success.")
H2("5.1. Observational Evidence from Software-Engineering Trajectories")
P("We use a public corpus of trajectories produced by SWE-agent (Yang et al. 2024), an open-source agent that resolves GitHub "
  "issues, driven by three sizes of Llama-3.1 (Nebius 2024). The corpus contains 80,036 trajectories. We code an error whenever the "
  "environment rejects an agent action: an edit that fails a syntax check, a command that does not exist, a missing file, a "
  "malformed call, or a timeout. Outputs of the file viewer are excluded because they cannot fail in this sense. About 22% of steps "
  "contain an error.")
P(f"Errors cluster strongly. The probability of an error is {PIL['clustering']['p_err_after_err']:.2f} after an error and "
  f"{PIL['clustering']['p_err_after_ok']:.2f} after a successful step. Part of this gap reflects heterogeneity: when errors are "
  f"permuted within each trajectory, which preserves each trajectory's error rate and destroys any dependence, the gap is "
  f"{PIL['clustering']['perm_null_mean']:.3f} on average, against an observed {PIL['clustering']['diff']:.3f}. A conditional logit "
  f"model with trajectory fixed effects gives a positive coefficient on decayed past errors (0.25 to 0.31 across decay rates) where "
  f"the same model on permuted sequences gives {PIL['fixed_effects_placebo_beta_mean']:.2f}.")
P("Table 1 reports maximum likelihood estimates of the self-exciting model with and without a gamma-distributed baseline. Without "
  "heterogeneity, the branching ratio exceeds one for all three models, which would place them in the supercritical regime where "
  "Proposition 4 makes monitoring very valuable. With heterogeneity, the ratio falls by a factor of three to four, to between 0.38 "
  "and 0.56, and the likelihood ratio tests reject both restricted models. Two features of the data caution against reading the "
  "remaining excitation as causal. Persistence within a run, such as an agent stuck in a malformed workspace, produces the same "
  "pattern as contagion. And the early-warning value of the error stream is small: the number of errors in the first eight steps "
  f"predicts eventual failure with an area under the curve of only {PIL['early_warning_auc_first8_steps']['error_count']:.2f}.")
rows = []
for m, lab in OBSM.items():
    rows.append([lab, f"{OBS[m]['n_traj']:,}", f2(ho[m]["branching"]), f2(re[m]["branching"]), f"[{bt[m]['lo']:.2f}, {bt[m]['hi']:.2f}]",
                 f2(re[m]["alpha"]), f2(re[m]["delta"]), f2(re[m]["re_cv"]), f"{OBS[m]['LR_hawkes_given_re']:.0f}"])
TABLE("Table 1. Self-Exciting Models of Agent Errors in SWE-Agent Trajectories",
      ["Model", "Trajectories", "n, no heterogeneity", "n, with heterogeneity", "95% bootstrap", "α", "δ", "CV of μ", "LR, excitation"],
      rows, note="Notes. Discrete-time Hawkes model with baseline μ_i(1 + t)^γ and gamma-distributed μ_i, first 60 steps of each "
      "trajectory with at least six steps. Up to 3,000 trajectories per model. n = α/(1 − δ). The likelihood ratio (LR) tests excitation "
      "given heterogeneity (two degrees of freedom). Bootstrap intervals use 15 resamples warm-started at the estimate and may understate "
      "uncertainty. Estimates in the subcritical range are robust to five starting values.")
H2("5.2. A Randomized Fault-Injection Experiment")
H3("Design.")
P(f"To separate contagion from persistence, we injected errors at random into agent runs. We used τ²-bench (Barres et al. 2025), a "
  f"public benchmark in which an agent serves simulated customers of an airline (50 tasks) and a retailer (114 tasks) through tool "
  f"calls on a database and in which success is verified by comparing the final database with the correct one. We ran three agents: "
  f"Llama-3.1-8B and Llama-3.1-70B, which match the observational data, and DeepSeek-V3.1, a stronger open-weight model. The "
  f"simulated customer was played by GPT-4.1-mini. Each task was run in four arms. In the control arm nothing was changed. In the "
  f"single arm the agent's j-th tool call, with j drawn uniformly from {{1, 2, 3}}, was not executed and returned a message stating "
  f"that the service was temporarily unavailable. In the blame arm the call returned instead a message of the form "
  f"“<argument> ‘<value>’ not found,” which reads like the agent's own mistake and mimics the benchmark's genuine error "
  f"messages. In the multi arm each call after the first was replaced by the unavailability message with probability 0.25, up to "
  f"three times. Control runs carry a virtual injection point drawn in the same way. Injected calls never changed the database. "
  f"Each task–arm cell was run three times for the Llama models and twice for DeepSeek-V3.1, whose provider limited request rates, "
  f"giving {n_runs:,} runs. Appendix B gives further details.")
P("We measure agent errors as tool calls that the real environment rejects, excluding the injected calls themselves. Because the "
  "injected errors are randomized, a comparison of later error rates between injected and control runs identifies the causal effect "
  "of an error on subsequent errors, which is the quantity α in the model. The comparison of success rates identifies the total "
  "effect of an error on the outcome, which maps into θ.")
H3("Results.")
rows = []
for m in ("llama8b", "llama70b", "deepseek"):
    s = S[m]
    rows.append([LAB[m], INJ[m]["n_runs"], f"{s['control']['rate']:.3f}"] +
                [f"{s[a + '_minus_control']['diff']:+.3f} {ci(s[a + '_minus_control']['ci'])}" for a in ("single", "blame", "multi")])
TABLE("Table 2. Task Success by Experimental Arm", ["Agent", "Runs", "Control success", "Single − control", "Blame − control", "Multi − control"],
      rows, note="Notes. Success is the benchmark's database check. Differences are paired by task and repetition; 95% intervals from "
      "1,000 bootstrap resamples of tasks.")
rows = []
for m in ("llama8b", "llama70b", "deepseek"):
    g = lambda k: f"{LG[m][k]['b']:+.2f} ({LG[m][k]['se']:.2f})"
    w = Wn[m]
    rows.append([LAB[m], f"{INJ[m]['lag_logit_n']['base_rate']:.3f}", g("inj1"), g("blm1"), g("err1"), g("err2"),
                 f"{w['single_post']['diff']:+.3f} {ci(w['single_post']['ci'])}", f"{w['blame_post']['diff']:+.3f} {ci(w['blame_post']['ci'])}"])
TABLE("Table 3. Effect of Errors on Subsequent Agent Errors",
      ["Agent", "Base error rate", "Injected, unavailable (lag 1)", "Injected, not found (lag 1)", "Own error (lag 1)", "Own error (lag 2)",
       "Δ error rate, 5 calls (single)", "Δ error rate, 5 calls (blame)"], rows,
      note="Notes. Columns 3–6: logit of an agent error on indicators of injected and own errors one or two calls earlier, with task fixed "
      "effects and the log position of the call; coefficients with standard errors. Injected errors are randomized, so their coefficients "
      "are causal. Columns 7–8: difference in the agent error rate over the five calls after the (virtual) injection point; 95% intervals "
      "from a task-clustered bootstrap.")
P(f"Three findings stand out. First, system failures did not cause further errors. After an injected unavailability message, the "
  f"log-odds of an error on the next call fell for every model, and the error rate over the following five calls was unchanged or "
  f"lower. The agents retried, and the retry usually succeeded. Second, errors that read like the agent's own mistake produced a "
  f"short burst in two of the three models. The lag-one coefficient was {LG['llama8b']['blm1']['b']:+.2f} for Llama-3.1-8B and "
  f"{LG['deepseek']['blm1']['b']:+.2f} for DeepSeek-V3.1, but the effect was gone by the second or third call, and Llama-3.1-70B "
  f"showed none. In terms of the model, α is positive for some agents but δ is close to zero, which implies a small branching "
  f"ratio. Third, the coefficients on the agent's own past errors are much larger than the causal coefficients on injected errors. "
  f"Most of the clustering seen in uncontrolled data therefore reflects persistence of difficulty within a run rather than errors "
  f"causing errors, consistent with the heterogeneity-adjusted estimates in Table 1.")
P(f"The effect of errors on success tells a different story (Table 2 and Figure 2). A single injected error lowered DeepSeek-V3.1's "
  f"success rate from {S['deepseek']['control']['rate']:.2f} to {S['deepseek']['single']['rate']:.2f}, a fall of "
  f"{abs(S['deepseek']['single_minus_control']['diff'])*100:.0f} percentage points, even though the model made almost no further "
  f"errors. Repeated unavailability messages lowered Llama-3.1-70B's success by {abs(S['llama70b']['multi_minus_control']['diff'])*100:.0f} "
  f"points. Llama-3.1-8B succeeded on only {S['llama8b']['control']['rate']*100:.0f}% of tasks in any arm and had little to lose. "
  f"Because the stronger model's later calls were almost all accepted by the environment, the loss of success must come from "
  f"what it did after the failure rather than from further failed calls; a plausible mechanism, which we did not code "
  f"systematically, is that the agent abandons or changes the requested action once a call has failed. In the terms of the model, "
  f"the error derailed the task rather than the agent.")
FIG(ROOT / "inject" / "fig_inject.png",
    "Figure 2. Fault-injection experiment. (a) Logit coefficients of a later agent error on an error one, two, and three calls "
    "earlier (left to right within each color), with 95% intervals; injected errors are randomized. (b) Task success by arm with "
    "95% intervals.", width=6.3)
H2("5.3. Calibrating the Hand-Off Rule")
P("The experiment allows us to estimate θ directly. If each error derails a task with probability θ and derailment turns a success "
  "into a failure, the ratio of success rates in the single and control arms is 1 − θ. Table 4 reports the estimates and the "
  "thresholds implied by Proposition 6 for three values of the cost of a wrong output F, holding the other costs at the values used "
  "above (k = 1, c = 5, q = 0.06, H = 40, μ = 0.054). For DeepSeek-V3.1 the firm should take the task back after the second error "
  "when F is 40 or 60 and after the first when F is 100. For Llama-3.1-70B, whose estimated θ is smaller and less precise, the "
  "threshold is two to six errors. For Llama-3.1-8B the estimate is not distinguishable from zero, and the model recommends no "
  "count-based intervention because the agent's outcome is poor whether or not it errs.")
rows = []
for m, lab, key in (("llama8b", "Llama-3.1-8B", "Llama-8B"), ("llama70b", "Llama-3.1-70B", "Llama-70B"), ("deepseek", "DeepSeek-V3.1", "DeepSeek-V3.1")):
    t = TH[m]
    r40, r60, r100 = cal[(key, 40.0)], cal[(key, 60.0)], cal[(key, 100.0)]
    ns = lambda r: "none" if r["n_star_dp"] is None else str(r["n_star_dp"])
    rows.append([lab, f"{t['single']['theta']:.2f} {ci(t['single']['ci'], 2)}", f"{t['multi_per_injection']['theta']:.2f} {ci(t['multi_per_injection']['ci'], 2)}",
                 ns(r40), ns(r60), ns(r100), f"{r60['value_vs_static']:.2f}"])
TABLE("Table 4. Derailment Probability and Optimal Hand-Off Thresholds",
      ["Agent", "θ from single arm", "θ per injection, multi arm", "N*, F = 40", "N*, F = 60", "N*, F = 100", "Value of rule, F = 60"], rows,
      note="Notes. θ = 1 − success(single)/success(control); the multi-arm estimate divides the log success ratio by the mean number of "
      "injections. N* from Proposition 6 with the single-arm θ (set to zero where negative); value relative to the better static choice, "
      "in units of step cost. Value iteration reproduces every closed-form threshold.")
P(f"Two qualifications apply. The estimates treat an injected system failure as representative of the agent's own errors, which "
  f"need not be the case, and the blame arm gives similar values ({TH['deepseek']['blame']['theta']:.2f} for DeepSeek-V3.1 and "
  f"{TH['llama70b']['blame']['theta']:.2f} for Llama-3.1-70B). And the value of the rule depends on F: for DeepSeek-V3.1 it rises "
  f"from {cal[('DeepSeek-V3.1', 40.0)]['value_vs_static']:.1f} to {cal[('DeepSeek-V3.1', 100.0)]['value_vs_static']:.1f} units of "
  f"step cost as F rises from 40 to 100, as Figure 3 shows. Monitoring is thus most valuable for capable agents deployed on tasks "
  f"where an undetected wrong output is expensive.")
FIG(ROOT / "theory" / "fig_derail.png",
    "Figure 3. Value of the optimal count rule relative to the better static choice, as a function of the derailment probability θ, "
    "for three costs of a wrong output F. Dotted lines mark the experimental estimates for Llama-3.1-70B and DeepSeek-V3.1.", width=4.6)

# ---------------------------------------------------------------- 6 Discussion
H1("6. Discussion")
H2("6.1. Implications for Research")
P("The central implication is that the design of human oversight for agentic systems should start from the mechanism that "
  "generates agent errors. The same observational pattern, bursts of errors, is consistent with contagion, heterogeneity, and "
  "persistent difficulty, and these mechanisms call for different signals. Research on human–AI delegation has concentrated on "
  "whether and how much people should rely on AI (Fügener et al. 2022). Once agents act over many steps, the analogous question is "
  "dynamic: under what evidence should a delegation be revoked? Our model shows that the answer can be stated in terms of a few "
  "estimable parameters, and our experiment shows that these parameters can be measured with a design that any firm deploying an "
  "agent could replicate.")
P("The results also qualify an influential intuition about agent failure. The image of an agent that spirals after its first "
  "mistake is supported by the raw data, which show strong clustering, but not by the randomized evidence, which shows that injected "
  "errors leave later error rates largely unchanged. What the evidence does support is that errors change outcomes. A theory of "
  "agent reliability that counts errors without asking what they do to the result will therefore misjudge risk. For IS research on "
  "control, the derailment channel suggests that outcome controls, such as verification of the final result, deserve attention "
  "alongside the behavior controls that monitoring represents.")
P("Finally, the analysis illustrates the value of combining econometric decomposition with experimentation in research on AI "
  "systems. Agent behavior can be manipulated at low cost and with full control over the treatment, which makes experiments of the "
  f"kind we report inexpensive; the {n_runs:,} runs reported here cost less than US$200 in model usage. This opens a path to "
  "testing behavioral claims about AI agents with the same standards that the field applies to claims about people.")
H2("6.2. Implications for Practice")
P("Three design principles follow. First, before building elaborate monitoring, a firm should establish whether its agent's "
  "errors are contagious. If, as in our experiment, the excitation from an error fades within a step, then recency-weighted alarms "
  "add little, and a count of errors per task is the right statistic. Second, the threshold should be set from the probability that "
  "an error derails a task and from the cost of a wrong output, both of which can be estimated with a small injection experiment on "
  "the firm's own tasks; Proposition 6 then gives the threshold in closed form. Our estimates suggest that capable agents may need "
  "tighter thresholds than weak ones, because they have more to lose from derailment. Third, monitoring investment should be "
  "targeted at tasks near the margin of delegation, where the cost of taking the task back is close to the expected cost of letting "
  "the agent finish (Proposition 8).")
H2("6.3. Limitations and Future Research")
P("Several limitations qualify our conclusions. The experiment covers a single family of customer-service tasks, one simulated "
  "customer, and two kinds of injected error; agents on other tasks, such as long software-engineering sessions, may show stronger "
  "and more persistent excitation. The injected errors are exogenous by design and may differ from the agent's own errors, which "
  "arise when the agent is already confused. The models we study are open-weight models available through a commercial router, and "
  "requests were served by more than one provider. Llama-3.1-8B frequently produced malformed tool arguments; we parsed them "
  "leniently so that runs could continue, which differs from the benchmark's default behavior. On the theoretical side, the costs k, "
  "c, H, and F are illustrative, and the model treats the firm as a single decision maker. A natural extension would let the "
  "vendor of the agent choose its reliability, or let the person who takes over exert unobserved effort, turning the hand-off rule "
  "into an element of a contract. We leave these extensions to future work.")

# ---------------------------------------------------------------- 7 Conclusion
H1("7. Conclusion")
P("Firms that deploy autonomous agents must decide when to take tasks back. We have shown that the optimal decision rule depends "
  "on whether errors are contagious, whether tasks differ in difficulty, and whether errors derail outcomes, and that each "
  "mechanism points to a different monitoring signal. Large observational data and a randomized experiment indicate that, for the "
  "agents we study, contagion is weak and short-lived while derailment is substantial. Under these conditions, a simple rule that "
  "hands a task back after a small, calibrated number of errors is not a crude approximation but the optimal policy.")

# ---------------------------------------------------------------- References
PAGEBREAK()
H1("References")
refs = [
    "Baird A, Maruping LM (2021) The next generation of research on IS use: A theoretical framework of delegation to and from agentic IS artifacts. MIS Quart. 45(1):315–341.",
    "Barres V, Dong H, Ray S, Si X, Narasimhan K (2025) τ²-Bench: Evaluating conversational agents in a dual-control environment. Preprint, submitted June 9, https://arxiv.org/abs/2506.07982.",
    "Berente N, Gu B, Recker J, Santhanam R (2021) Managing artificial intelligence. MIS Quart. 45(3):1433–1450.",
    "Blackwell D (1953) Equivalent comparisons of experiments. Ann. Math. Statist. 24(2):265–272.",
    "Chow YS, Robbins H, Siegmund D (1971) Great Expectations: The Theory of Optimal Stopping (Houghton Mifflin, Boston).",
    "Fügener A, Grahl J, Gupta A, Ketter W (2022) Cognitive challenges in human–artificial intelligence collaboration: Investigating the path toward productive delegation. Inform. Systems Res. 33(2):678–696.",
    "Hawkes AG (1971) Spectra of some self-exciting and mutually exciting point processes. Biometrika 58(1):83–90.",
    "Heckman JJ (1981) Heterogeneity and state dependence. Rosen S, ed. Studies in Labor Markets (University of Chicago Press, Chicago), 91–140.",
    "Holmström B (1979) Moral hazard and observability. Bell J. Econom. 10(1):74–91.",
    "Jovanovic B (1979) Job matching and the theory of turnover. J. Political Econom. 87(5):972–990.",
    "Kirsch LJ (1997) Portfolios of control modes and IS project management. Inform. Systems Res. 8(3):215–239.",
    "Nebius (2024) SWE-agent trajectories. Dataset, Hugging Face, https://huggingface.co/datasets/nebius/SWE-agent-trajectories.",
    "Puterman ML (1994) Markov Decision Processes: Discrete Stochastic Dynamic Programming (Wiley, New York).",
    "Shiryaev AN (1963) On optimum methods in quickest detection problems. Theory Probab. Appl. 8(1):22–46.",
    "Wald A (1947) Sequential Analysis (Wiley, New York).",
    "Yang J, Jimenez CE, Wettig A, Lieret K, Yao S, Narasimhan K, Press O (2024) SWE-agent: Agent-computer interfaces enable automated software engineering. Adv. Neural Inform. Processing Systems 37.",
    "Yao S, Shinn N, Razavi P, Narasimhan K (2024) τ-bench: A benchmark for tool-agent-user interaction in real-world domains. Preprint, submitted June 17, https://arxiv.org/abs/2406.12045.",
]
for r in refs:
    p = P(r, indent=False); p.paragraph_format.left_indent = Inches(0.5); p.paragraph_format.first_line_indent = Inches(-0.5)

# ---------------------------------------------------------------- Appendix A
PAGEBREAK()
H1("Appendix A. Proofs")
RICH([("Proof of Proposition 1. ", "b"), ("Let T denote the operator on the right-hand side of (2), acting on bounded functions on "
      "[0, ∞). For bounded W₁ and W₂, |TW₁(x) − TW₂(x)| ≤ (1 − q)‖W₁ − W₂‖, so T is a contraction and has a unique fixed point W with "
      "0 ≤ W ≤ H (Puterman 1994). Suppose W is nondecreasing. For each e, x ↦ W(δx + αe) is nondecreasing; because Poisson(μ + x) "
      "increases in x in first-order stochastic dominance, E[W(δx + αe)] is nondecreasing in x. Hence C and TW = min{H, C} are "
      "nondecreasing. The set of bounded nondecreasing functions is closed under uniform convergence, so the fixed point is "
      "nondecreasing. Because c > 0, C is strictly increasing, and {x : C(x) ≥ H} is an interval [x*, ∞). ∎", "")], indent=False)
RICH([("Proof of Proposition 2. ", "b"), ("If δ = 1, x_t = αN_t, and the rule x_t ≥ x* is the rule N_t ≥ x*/α. If δ < 1 and α > 0, "
      "two histories with the same count can have different intensities; for example, a single error at step t − 1 gives x_t = α, "
      "whereas a single error at step t − j with j > 1 gives αδ^{j−1} < α. When x* is interior, histories of this kind on either side "
      "of x* occur with positive probability. A count rule takes the same action on both, whereas the optimal rule does not, and "
      "because C is strictly increasing the count rule's action is strictly worse on one of them. ∎", "")], indent=False)
RICH([("Proof of Proposition 3. ", "b"), ("Without hand-off, E[x_{t+1}] = ρE[x_t] + αμ with x_0 = 0, so E[x_t] = αμ(1 − ρ^t)/(1 − ρ). "
      "Step t is reached with probability (1 − q)^t, so C_U = Σ_t (1 − q)^t[k + cμ + cE[x_t]], which sums to the stated expression "
      "when (1 − q)ρ < 1 and diverges otherwise. ∎", "")], indent=False)
RICH([("Proof of Proposition 4. ", "b"), ("Both static choices are feasible, so W(0) ≤ min{H, C_U}. If α = 0, then x_t = 0 for all t, "
      "the history carries no information, and W(0) = min{H, C_U}. Since W(0) ≤ H for all parameters and C_U diverges as "
      "(1 − q)ρ → 1 by Proposition 3, C_U − W(0) grows without bound. ∎", "")], indent=False)
RICH([("Proof of Proposition 5. ", "b"), ("The posterior after (t, N) is gamma with shape a + N and rate b + t, and the predictive "
      "count is negative binomial with size a + N and success probability (b + t)/(b + t + 1). This family increases in N in "
      "first-order stochastic dominance, and the expected step cost k + c(a + N)/(b + t) is strictly increasing in N. Backward "
      "induction on a horizon T, whose terminal value matters with probability at most (1 − q)^T, yields a value function that is "
      "nondecreasing in N for each t, so the stopping region at t is {N ≥ N*(t)}. As t → ∞ the posterior concentrates at μ, and "
      "the problem converges to the known-μ problem with α = 0, whose solution is to hand off if and only if (k + cμ)/q ≥ H. ∎", "")], indent=False)
RICH([("Proof of Proposition 6. ", "b"), ("With α = 0 and μ known, the posterior probability of derailment after N errors is "
      "π_N = 1 − (1 − θ)^N, so N is a sufficient state. Consider the one-step look-ahead comparison: stop now at cost H, or take one "
      "more step and then stop. The latter costs k + cμ + q F E[π_{N+e}] + (1 − q) H, where E[1 − π_{N+e}] = (1 − θ)^N E[(1 − θ)^e] "
      "= (1 − θ)^N e^{−μθ}. Stopping is at least as good if and only if qH ≤ k + cμ + qF[1 − (1 − θ)^N e^{−μθ}], which rearranges to "
      "(3). The right-hand side of this inequality is nondecreasing in N, and N never decreases, so once the inequality holds it "
      "holds at all later states. The problem is therefore monotone in the sense of Chow et al. (1971, Theorem 3.5), and the "
      "one-step look-ahead rule is optimal. The boundary cases follow directly from the inequality. ∎", "")], indent=False)
RICH([("Proof of Proposition 7. ", "b"), ("With both channels the state is (x, N) and the Bellman operator is "
      "TW(x, N) = min{H, k + c(μ + x) + E[q F π' + (1 − q) W(δx + αe, N + e)]}, where π' = 1 − (1 − θ)^{N+e} and e ~ Poisson(μ + x). "
      "The operator is a contraction with modulus 1 − q. If W is nondecreasing in (x, N), the integrand is nondecreasing in e, x, "
      "and N, and e increases stochastically in x, so TW is nondecreasing; the fixed point inherits the property. The stopping "
      "region {C(x, N) ≥ H} is therefore an upper set, and for each x the smallest stopping count N*(x) is nonincreasing in x. ∎", "")], indent=False)
RICH([("Proof of Proposition 8. ", "b"), ("Every policy π has expected cost A_π + H·P_π, where A_π is the expected cost of the agent's "
      "steps and wrong outputs and P_π is the probability of hand-off; neither depends on H. The optimal cost W(0; H) = inf_π "
      "(A_π + H P_π) is therefore concave and nondecreasing in H, with W(0; 0) = 0. For H ≤ C̄, V(H) = H − W(0; H) is convex with "
      "V(0) = 0 and V ≥ 0, and a convex function that is zero at the origin and nonnegative is nondecreasing on [0, C̄]. For H ≥ C̄, "
      "V(H) = C̄ − W(0; H) is nonincreasing. Hence V is maximized at H = C̄. ∎", "")], indent=False)

# ---------------------------------------------------------------- Appendix B
H1("Appendix B. Details of the Experiment")
P("Implementation. We used τ²-bench version 2.0 in text mode with its original airline and retail task sets, the default "
  "language-model agent, and the default user simulator. Agents and the user simulator were accessed through OpenRouter with "
  "temperature 0.5. Success is the benchmark's environment check, which compares the final database with the database produced by "
  "the correct sequence of actions; we did not use the language-model judges. The injection was implemented by intercepting the "
  "environment's response to the agent's tool calls. Injected calls were not executed, and the benchmark's evaluation replays them "
  "with the same injected response, so that injections cannot change the database.", indent=False)
P("Providers and malformed output. Requests to a given model may be served by several providers. We excluded two providers for the "
  "Llama models that rejected histories containing parallel tool calls, and one provider for DeepSeek-V3.1 whose tool template "
  "failed. Llama-3.1-8B often returned tool arguments that were not valid JSON, for example two objects concatenated; we kept the "
  "first object and recorded the event, rather than ending the run as the benchmark would. Failures caused by the provider were "
  "retried; failures caused by the agent's output were kept as outcomes.", indent=False)
P(f"Analysis. Agent errors are tool calls that the real environment rejected. The window analysis compares the error rate over the "
  f"five calls after the injection point with the same window in control runs, using runs that reached the injection point. The "
  f"lag regressions pool all arms, include task fixed effects and the log of the call position, and are estimated on tasks with "
  f"variation in the outcome. Intervals use 1,000 bootstrap resamples of tasks. The total cost of the {n_runs:,} runs, including "
  f"pilots, was about US$180. Code and run-level data are available in the replication package.", indent=False)

d.save(HERE / "ISR_Manuscript.docx")

# ---------------------------------------------------------------- title page
d = new_doc()
P(TITLE, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
d.add_paragraph()
P("Ook Lee", indent=False, align=WD_ALIGN_PARAGRAPH.CENTER)
P("Department of Information Systems, Hanyang University, Seoul, Republic of Korea, ooklee@hanyang.ac.kr", indent=False, align=WD_ALIGN_PARAGRAPH.CENTER)
d.add_paragraph()
for lab, t in [
    ("Funding. ", "The author received no external funding for this research."),
    ("Conflict of interest. ", "The author declares no competing interests."),
    ("Data availability. ", "The software-engineering trajectories are publicly available on Hugging Face (nebius/SWE-agent-trajectories). "
     "The fault-injection code, run-level results, and analysis scripts will be deposited in a public repository upon acceptance."),
    ("Use of generative AI. ", "The author used a generative AI assistant (Claude, Anthropic) to help write analysis code, run the "
     "experiment, and edit the text. The author designed the study, checked all analyses, and takes full responsibility for the content."),
]:
    RICH([(lab, "b"), (t, "")], indent=False)
d.save(HERE / "ISR_Title_Page.docx")
print("saved")
