"""Generate the DSS-format manuscript (anonymized main file, title page, highlights) from result JSONs."""
import json, sys
import numpy as np
from scipy import stats
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.text import WD_COLOR_INDEX
from sim import surrogate_coarse_value
from analysis import reference_hourly, reference_delay_cdf

OUT = "../dss_revision/"
J = lambda f: json.load(open(f))
s1 = J("results_study1.json")["summary"]
S2 = {k: J(f)["summary"] for k, f in [("sur", "results_study2_surrogate.json"), ("coa", "results_study2_coarse.json"),
                                       ("llm", "results_study3_llm.json")]}
R2 = J("results_study2_surrogate.json")["runs"]
beh = J("results_study3_behavior.json")
sens = {r["config"]: r for r in J("results_sensitivity.json")["rows"]}
llm = J("llm_table.json")["ratings"]
keys = [tuple(json.loads(k)) for k in llm]
lv = np.array(list(llm.values()))
sv = np.array([surrogate_coarse_value(k) for k in keys])
rho = stats.spearmanr(lv, sv)[0]


def grp(f):
    d = {}
    for k, v in zip(keys, lv):
        d.setdefault(f(k), []).append(v)
    return {g: float(np.mean(x)) for g, x in d.items()}


g_per, g_vol, g_rel = grp(lambda k: k[1]), grp(lambda k: k[3]), grp(lambda k: k[4])
g_not, g_emo, g_pd = grp(lambda k: k[5]), grp(lambda k: k[2]), grp(lambda k: k[0])
ref = reference_hourly()
conc = np.array([r["adopters"] for r in R2 if r["cond"] == "concentrated"])
dist = np.array([r["adopters"] for r in R2 if r["cond"] == "distributed"])
frac_below = float((conc < dist.mean()).mean())
sA = S2["sur"]


def p_(p):
    return "p < .001" if p < 0.001 else f"p = {p:.3f}".replace("0.", ".")


def f(x, n=2):
    return f"{x:.{n}f}"


def sgn(x, n=1):
    return f"{x:+.{n}f}"


doc = Document()
st = doc.styles["Normal"]
st.font.name = "Times New Roman"
st.font.size = Pt(11)
for s in doc.sections:
    s.left_margin = s.right_margin = Inches(1)
    s.top_margin = s.bottom_margin = Inches(1)
doc.styles["Normal"].paragraph_format.line_spacing = 1.5


def H(t, lvl=1):
    h = doc.add_heading(t, lvl)
    for r in h.runs:
        r.font.name = "Times New Roman"
        r.font.color.rgb = None
    return h


def P(t, italic=False, hl=False):
    p = doc.add_paragraph()
    r = p.add_run(t)
    r.italic = italic
    if hl:
        r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    return p


def table(rows, header=True, widths=None, caption=None, note=None):
    if caption:
        c = doc.add_paragraph()
        c.add_run(caption).bold = True
        c.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            cell = t.cell(i, j)
            cell.text = ""
            run = cell.paragraphs[0].add_run(str(v))
            run.font.size = Pt(9)
            cell.paragraphs[0].paragraph_format.line_spacing = 1.0
            if header and i == 0:
                run.bold = True
    if note:
        n = doc.add_paragraph()
        r = n.add_run(note)
        r.font.size = Pt(9)
        n.paragraph_format.line_spacing = 1.0
    doc.add_paragraph()


def figure(path, caption, w=6.0):
    doc.add_picture(OUT + "figures/" + path, width=Inches(w))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = doc.add_paragraph()
    c.add_run(caption).italic = True
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER


# ------------------------------------------------------------------ title/abstract
TITLE = ("Pre-testing social media campaigns with LLM-agent simulation: event-driven agent timing "
         "and the scale-versus-speed trade-off in seeding decisions")
t = doc.add_paragraph()
r = t.add_run(TITLE)
r.bold = True
r.font.size = Pt(16)
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
P("[Anonymized manuscript. Author names, affiliations, acknowledgements and funding details are in the separate title page.]", italic=True)

H("Highlights", 2)
HL = ["Agent timing in LLM simulators is set by a point process, not the simulation clock",
      "An LLM rates the urge to act; an inhomogeneous Poisson process decides when",
      f"At equal exposure budget, influencer seeding gave about {100*sA['adopters']['diff']/sA['adopters']['dist']:.0f}% more adopters",
      "Distributed seeding reached half its adopters sooner and varied far less",
      "Conclusions are unchanged when a rule-based oracle is replaced by LLM ratings"]
for h in HL:
    doc.add_paragraph(h, style="List Bullet")

H("Abstract", 2)
ABS = (
    "Managers who choose where to seed a social media campaign cannot test the options in the field without cost "
    "or disturbance, and simulation with large language model (LLM) agents is an attractive pre-test. Most such "
    "simulators, however, decide when agents act by fixed-interval polling, which imposes artificial synchrony and "
    "makes temporal outcomes such as the speed of diffusion partly a product of the simulation loop. We present "
    "Poisson-SNS, a simulator for campaign decision support in which each agent's next action time is drawn from an "
    "inhomogeneous Poisson process whose intensity combines a persona-specific circadian baseline with decaying "
    "stimuli from content exposure and feedback. An LLM is used only as an intensity oracle that rates, on a 0 to 5 "
    "scale, how strongly a situation moves a persona to act. We use the simulator to compare two seeding decisions "
    f"under an equal exposure budget. Concentrating the campaign on three high-degree influencers produced about "
    f"{100*sA['adopters']['diff']/sA['adopters']['dist']:.0f}% more adopters than seeding several hundred ordinary users "
    f"({f(sA['adopters']['conc'],0)} vs. {f(sA['adopters']['dist'],0)}, {p_(sA['adopters']['p'])}), but reached half of its "
    f"eventual adopters about {f(sA['t50']['diff'],1)} hours later and produced far more variable outcomes. These "
    "conclusions held when the rule-based oracle was replaced by ratings from LLM raters, and the scale advantage "
    "of concentration persisted across most, but not all, parameter and network variations; it disappeared on a "
    f"random network. Against an assumed reference profile, the proposed scheduler reproduced the daily activity "
    f"cycle far better than homogeneous Poisson and polling schedulers (r = {f(s1['ipp']['r'])} vs. {f(s1['hpp']['r'])} "
    f"and {f(s1['poll']['r'])}), although reply delays remained too long. Because no platform trace data were available, "
    "validation relies on parametric references, and the findings are hypotheses for field testing rather than "
    "prescriptions. The results show that the preferred seeding strategy depends on whether the decision maker "
    "values expected scale, speed, or predictability.")
P(ABS)
P("Keywords: decision support; LLM agents; agent-based simulation; social media campaigns; seeding strategy; "
  "inhomogeneous Poisson process; information diffusion")

# ------------------------------------------------------------------ 1 Introduction
H("1. Introduction")
P("A campaign manager planning a product launch, a public-health message, or a policy announcement faces a concrete "
  "choice: place the message with a few prominent accounts, or spread the same exposure thinly across many ordinary "
  "users. The choice involves more than which option yields more engagement. It involves what the decision maker "
  "values. A launch with a short attention window rewards speed, a brand that runs many campaigns may care mostly "
  "about expected reach, and a one-off announcement may call for an outcome that can be predicted in advance. "
  "Field experiments on this choice are expensive, can disturb the communities under study, and are hard to repeat, "
  "so decision makers rely on models and simulation to narrow the options before committing budget "
  "[DSS-REF: add Decision Support Systems papers on social media or viral marketing decision support and on seeding "
  "or influence maximization].", )
P("Agent-based simulation has long served this purpose (Bonabeau, 2002; Rand and Rust, 2011), and large language "
  "models (LLMs) have renewed its appeal. LLM agents can be given personas and can read, write, and react to "
  "natural-language content, which promises behavioral richness that rule-based agents lack (Park et al., 2023; "
  "Gao et al., 2023; Törnberg et al., 2023). [DSS-REF: add work that applies LLM agents to influencer selection "
  "and campaign pre-testing, and Decision Support Systems work on LLM-based decision support, after checking each "
  "publication venue.]")
P("A decision support tool is only as useful as the decisions it can be trusted to rank, and a less discussed "
  "weakness matters here. In most LLM-agent simulators the loop advances in discrete rounds, and every agent is "
  "queried once per round about whether and how to act. This embeds the assumption that human action is regular "
  "and synchronous. Empirical work points the other way: online activity follows daily cycles, arrives in bursts, "
  "and responds to triggers such as notifications (Barabási, 2005; Malmgren et al., 2008; Crane and Sornette, "
  "2008). If the loop sets the timing, then the speed of a cascade, which is exactly what a time-sensitive decision "
  "depends on, is partly produced by a modeling convention, and a recommendation that depends on speed inherits "
  "that artifact.")
P("We address this by treating action timing as a stochastic point process rather than as a clock. We build "
  "Poisson-SNS, a simulator in which each LLM agent acts at the event times of an inhomogeneous Poisson process "
  "(IPP). The intensity combines a persona-specific circadian baseline with stimuli that arise when an agent sees "
  "relevant content or receives feedback on its own posts. The LLM is used where it is most defensible, to judge how "
  "strongly a situation would move a persona to speak, and not to decide the clock time of the next action. The "
  "simulator is event-driven, so computation is spent only when something happens, and cascades of the "
  "self-exciting kind described by Hawkes (1971) can emerge.")
P("We use the simulator to answer three questions that follow from the decision problem. RQ1 (credibility): does "
  "the IPP scheduler reproduce the temporal regularities of online activity better than homogeneous Poisson and "
  "fixed-period polling schedulers, so that speed-related outputs can be taken seriously? RQ2 (decision): with an "
  "equal exposure budget, how do concentrated seeding on a few influencers and distributed seeding across many "
  "ordinary users compare on expected scale, on speed, and on the variability of outcomes? RQ3 (robustness): do the "
  "answers to RQ1 and RQ2 change when the intensity oracle is a rule-based function rather than an LLM, or when the "
  "manually set parameters and the network structure are varied?")
P("The paper contributes in three ways. First, it offers a simulator specification that separates the LLM's "
  "judgment of motivation from the timing mechanism, which makes the temporal assumptions inspectable and testable. "
  "Second, it shows what the simulator can tell a decision maker. In our synthetic setting no seeding strategy "
  "dominates: concentration gave more adopters in expectation, whereas distribution was faster and far more "
  "predictable, so the better choice depends on whether the objective is scale, speed, or predictability. Third, it "
  "reports where the simulator falls short, including a reply-delay distribution it did not match and a seeding "
  "advantage that depends on the network, and it sets out the platform data needed to test it. We are explicit "
  "about what the evidence supports. Without trace data from a real platform, behavioral validation is conducted "
  "against assumed reference profiles, so the findings are hypotheses to be field-tested and not prescriptions.")
P("The remainder of the paper reviews related work (Section 2), describes the simulator (Section 3), reports the "
  "evaluation (Section 4), and discusses implications for decision makers, limitations, and future work "
  "(Section 5). Section 6 concludes.")

# ------------------------------------------------------------------ 2 Related work
H("2. Related work")
H("2.1 Simulation for decision support in social media campaigns", 2)
P("[DSS-REF: This subsection should position the paper within Decision Support Systems literature on simulation-based "
  "and data-driven support for social media marketing, viral campaigns, and seed selection. No such papers were "
  "verified while drafting, so none are cited here; add them after reading the sources.]", hl=True)
H("2.2 Agent-based simulation and LLM agents", 2)
P("Agent-based modeling studies system-level outcomes that emerge from the interaction of heterogeneous, autonomous "
  "actors (Bonabeau, 2002; Gilbert, 2008), and it has a long record in marketing and diffusion research, where its "
  "credibility rests on careful specification and validation (Rand and Rust, 2011). Traditional agents follow "
  "hand-coded rules. LLM-based agents replace those rules with a generative model conditioned on a persona and the "
  "agent's observations. Park et al. (2023) showed that such agents can sustain believable individual and "
  "collective behavior in a small sandbox. Subsequent work has built social-network simulators on the same idea, "
  "including S3 (Gao et al., 2023), and has used LLM agents to compare news-feed algorithms (Törnberg et al., 2023).")
P("These systems generally leave the question of timing to the simulation loop. Calls to the model are expensive, "
  "which encourages coarse, uniform rounds. Yet if the loop is the source of timing, then temporal outcomes such as "
  "the volume of activity per hour, response delays, and the speed of cascades are partly determined by a modeling "
  "convention rather than by agent behavior. We take this to be a validity concern for decision support, and the "
  "simulator we propose is a response to it.")
H("2.3 Temporal point processes and human activity", 2)
P("A temporal point process describes events through a conditional intensity function λ(t), the instantaneous "
  "event rate given the history. A homogeneous Poisson process fixes λ(t) to a constant and produces memoryless, "
  "evenly spread events. Human communication departs from this in two ways. First, it is non-stationary, with strong "
  "daily and weekly cycles. Second, it is bursty, with heavy-tailed inter-event times that Barabási (2005) attributed "
  "to priority-based task queues, whereas Malmgren et al. (2008) showed that a cascading, non-homogeneous Poisson "
  "mechanism with circadian modulation can account for much of the same heavy tail. The latter account is the one "
  "most relevant here, because it suggests that a time-varying intensity, rather than an exotic waiting-time law, may "
  "be sufficient to generate realistic timing.")
P("Self-exciting processes add feedback. In a Hawkes process each event temporarily raises the intensity of future "
  "events (Hawkes, 1971). The mean number of direct descendants of an event, the branching ratio, indicates whether "
  "cascades die out (below one) or grow without bound (above one). Self-exciting models have been used to describe "
  "and forecast the popularity of online content (Crane and Sornette, 2008; Zhao et al., 2015). In our simulator, "
  "self-excitation is not imposed as a parametric kernel. It emerges from the interaction of exposure, stimulus, and "
  "action, and we estimate the branching ratio after the fact as a summary of the simulated cascades. "
  "Non-homogeneous Poisson processes can be simulated exactly by thinning, in which candidate events are drawn from a "
  "dominating homogeneous process and accepted with probability λ(t)/λ_max (Lewis and Shedler, 1979; Ogata, 1981). "
  "Thinning is the scheduling primitive we use.")
H("2.4 Influence, seeding, and diffusion", 2)
P("The question of whom to target has a substantial literature. The influence-maximization problem asks for the "
  "set of initial adopters that maximizes expected spread and has been shown to be computationally hard, with greedy "
  "approximations that have performance guarantees (Kempe et al., 2003). The influentials hypothesis holds that a "
  "small group of highly connected individuals drives diffusion, but Watts and Dodds (2007) argued, using a threshold "
  "model, that large cascades are driven at least as often by many easily influenced ordinary users. Empirically, "
  "Bakshy et al. (2011) found that the most influential Twitter users were those who had been influential before and "
  "had many followers, yet that targeting ordinary users could be cost-effective once costs are considered. Aral and "
  "Walker (2012) used a randomized field experiment to identify influential and susceptible members of a network, "
  "showing that the two roles can be distinguished.")
P("This body of work frames the comparison in the present study. We hold the exposure budget constant, so that "
  "differences cannot be attributed simply to the larger audience of an influencer, and we examine both the final "
  "scale and the speed of diffusion, because the verdicts in the literature differ partly by the outcome measured. "
  "The influence-maximization and threshold literatures typically evaluate final cascade size. Practitioners, in "
  "contrast, often care about how quickly a message gains traction, since attention decays.")

# ------------------------------------------------------------------ 3 Simulator
H("3. The Poisson-SNS simulator")
P("The design objective is that an LLM-agent simulator should generate action times endogenously, so that circadian "
  "rhythm, reactivity, and cascade dynamics emerge from agent state instead of from the simulation clock, and so "
  "that its outputs can serve as inputs to a campaign decision. Figure 1 shows the architecture, and the subsections "
  "below describe each component. Parameters that the design does not determine (Appendix A) are assumptions of this "
  "instantiation.")
figure("fig1_architecture.png", "Fig. 1. Architecture of the Poisson-SNS simulator.")
H("3.1 Platform environment", 2)
P("The environment is a text-based virtual platform. It maintains a directed follower graph, a store of items "
  "(original posts, comments, and retweets), and a bounded feed for each agent that holds the 40 most recent items "
  "shown to that agent. When an agent publishes content, each follower is exposed to it with probability "
  "p_view = 0.5, and comments are displayed with an additional visibility factor of 0.4 because replies are less "
  "prominent than original posts. Agents may also receive a notification when another agent comments on or retweets "
  "their content. Likes are recorded but do not propagate. The follower graph is generated by preferential attachment "
  "on in-degree, which yields a heavy-tailed follower distribution (Barabási and Albert, 1999). When an agent "
  "comments or retweets, it chooses among eligible feed items with probability proportional to its interest in the "
  "item's topic and an exponential recency weight with a two-hour time constant; the recency weight is an assumption "
  "of this instantiation, introduced so that reply delays are on a realistic scale.")
H("3.2 Persona agents", 2)
P("Each agent is assigned one of five personas (Table 1) that determine its baseline rate, its sensitivity to "
  "stimuli, its chronotype, and its propensity for each action type. Individual baseline rates are multiplied by a "
  "log-normal factor (σ = 0.4) and the chronotype is perturbed by a normal term (σ = 1.5 hours) to produce "
  "heterogeneity within personas. Each agent also has an interest vector over five topics drawn from a symmetric "
  "Dirichlet distribution with concentration 0.4, which makes interests concentrated rather than uniform.")
table([["Persona", "Share", "Base rate λ⁰ (1/h)", "Gain g", "Peak hour", "P(post / comment / retweet / like)"],
       ["Early adopter", "15%", "0.45", "1.3", "22", ".30 / .20 / .25 / .25"],
       ["Cynic", "15%", "0.30", "0.8", "23", ".20 / .45 / .05 / .30"],
       ["Trend follower", "25%", "0.40", "1.2", "21", ".15 / .15 / .40 / .30"],
       ["Lurker", "30%", "0.12", "0.6", "21", ".05 / .10 / .10 / .75"],
       ["News junkie", "15%", "0.70", "1.0", "20", ".40 / .20 / .20 / .20"]],
      caption="Table 1. Persona parameters",
      note="Note. When an agent selects an action that requires a feed item and none is eligible, it posts instead.")
H("3.3 Intensity model and scheduler", 2)
P("Let c_i(t) denote a mean-one daily activity profile for agent i with an evening peak, a smaller midday peak, and "
  "a night trough. The conditional intensity of agent i at time t is")
P("λ_i(t) = λ⁰_i · c_i(t) + S_i(t),   (1)")
P("where S_i(t) aggregates the stimuli received before t:")
P("S_i(t) = min{ S_max , Σ_j κ · g_i · I_ij · r_ij · exp(−(t − t_j)/τ) }.   (2)")
P("Here t_j is the time of the j-th stimulating event (an exposure to content or a notification), I_ij ∈ [0, 5] is the "
  "intensity rating returned by the oracle for the agent's state at that moment, r_ij ∈ {0.25, 0.50, 0.75} encodes "
  "the relevance of the item to the agent's interests (low, medium, high), g_i is the persona gain, κ = 0.16 is a "
  "global scale, and τ = 1 hour is the decay time. Feedback on an agent's own content (a comment or retweet) enters "
  "as a stimulus with a fixed relevance of 0.50. The cap S_max = 3 is a saturation chosen for this synthetic "
  "instantiation so that the additive sum remains finite under the exposure rule used here (Section 3.5). It is not "
  "an estimate of a platform-level carrying capacity.")
P("Next event times are drawn by thinning. For agent i at time t, the dominating rate is "
  "λ_max = λ⁰_i · max c + S_i(t), which is valid until the next stimulus arrives because the stimulus term decays. "
  "Candidate times are generated from a homogeneous process at rate λ_max and accepted with probability "
  "λ_i(s)/λ_max. Whenever a new stimulus raises S_i, the agent's pending event is invalidated and redrawn, which is "
  "exact because the Poisson process is memoryless. The simulator is thus fully event driven, and no agent is queried "
  "on a schedule.")
H("3.4 The intensity oracle", 2)
P("The oracle maps an agent's situation to an urge rating I ∈ [0, 5]. In the LLM instantiation, the model receives a "
  "system instruction to act as the behavior controller of a given user, together with the time of day, emotional "
  "state, the number of relevant items recently shown in the feed, the topical relevance of the latest item, and "
  "notification status, and it returns a rating (Appendix B). The model is not asked when the agent will act. Clock "
  "time is determined entirely by the process in Section 3.3, which makes the number of model calls independent of "
  "the simulated time span and allows ratings for recurring states to be cached.")
P("We implement two oracles behind one interface. The surrogate oracle is a deterministic function that is "
  "increasing in leisure time, relevant feed volume and relevance, notifications, and a positive emotional state, and "
  "it is used for the main experiments. The LLM oracle is a lookup table of ratings over a coarse state space of 1,600 "
  "states (four periods of the day, five personas, four emotions, ten combinations of feed volume and relevance, and "
  "the presence of a notification), described in Section 4.4. Because both are accessed through the same interface, "
  "the rest of the system is unchanged when one is substituted for the other.")
H("3.5 Stability of the additive intensity", 2)
P("A stability observation bears on the design, although it is specific to this parameterization and does not "
  "establish a general property of additive intensity models. With the persona rates of Table 1, an exposure "
  "probability of 0.5, and an uncapped additive stimulus at large κ, the evening process becomes supercritical: "
  "exposures trigger actions that trigger further exposures faster than stimuli decay. Capping the stimulus at "
  "S_max = 3 with κ = 0.16 produced a stable run with a clear diurnal pattern under those same settings. We "
  "therefore treat the cap as a design requirement of this simulator, and Section 4.5 examines how the main "
  "conclusion depends on κ, S_max, and p_view.")

# ------------------------------------------------------------------ 4 Evaluation
H("4. Evaluation")
H("4.1 General setup", 2)
P("Unless stated otherwise, simulations used the parameters in Table 1 and Section 3 (Appendix A), with the time unit "
  "set to hours. Study 1 used 800 agents (five new links per node) for 72 simulated hours with five "
  "replications per scheduler. Studies 2 and 3 used a 2,000-agent network (three new links per node) with an 18-hour "
  "warm-up, a campaign injected at 18:00, and outcomes counted over the following 48 hours; replications were paired "
  "by network and random seed across strategies. The code and results are available from an anonymized repository "
  "[link to be inserted after review]. The simulator was implemented from the specification in Section 3.")
H("4.2 Study 1: Behavioral plausibility of the scheduler (RQ1)", 2)
P("We compared three schedulers that share every other component: (a) the proposed IPP; (b) a homogeneous Poisson "
  "process (HPP) at each agent's mean base rate, which has no circadian or reactive structure; and (c) fixed-period "
  "polling, in which each agent acts every 1/λ⁰ hours with a random phase. Outcomes were the hourly distribution of "
  "posting events (posts, comments, and retweets) pooled over days and the distribution of reply delays, the time "
  "between an item's creation and a comment on it. The reference for the first was a stylized bimodal daily profile "
  "with a midday and an evening peak, and for the second a log-normal delay distribution with a median of 0.5 hours "
  "and a heavy right tail truncated at 48 hours. These references are assumptions, not empirical measurements. They "
  "encode qualitative regularities commonly reported for online activity, and they were chosen with functional forms "
  "different from those of the simulator, but they are not data.")
P("We report the Pearson correlation and total variation (TV) distance between the simulated and reference "
  "hour-of-day distributions, the Pearson χ² statistic (23 degrees of freedom), and the two-sample "
  "Kolmogorov–Smirnov statistic D for delays. Because simulated samples contain tens of thousands of events, χ² and "
  "KS tests reject at any conventional level for any imperfect model, so we interpret effect-size measures (r, TV, D) "
  "and treat significance tests as uninformative.")
table([["Scheduler", "Pearson r", "TV distance", "χ² (crit. 35.2)", "KS D (delay)", "Median delay (h)", "Variance/mean of hourly counts"],
       ["IPP (proposed)", f(s1['ipp']['r']), f(s1['ipp']['tv']), f"{s1['ipp']['chi2']:,.0f}", f(s1['ipp']['ks']), f(s1['ipp']['med_delay']), f(s1['ipp']['vmr'], 1)],
       ["HPP", f(s1['hpp']['r']), f(s1['hpp']['tv']), f"{s1['hpp']['chi2']:,.0f}", f(s1['hpp']['ks']), f(s1['hpp']['med_delay']), f(s1['hpp']['vmr'], 1)],
       ["Fixed-period polling", f(s1['poll']['r']), f(s1['poll']['tv']), f"{s1['poll']['chi2']:,.0f}", f(s1['poll']['ks']), f(s1['poll']['med_delay']), f(s1['poll']['vmr'], 1)],
       ["Reference (assumed)", "–", "–", "–", "–", "0.50", "–"]],
      caption="Table 2. Scheduler comparison (means over five replications)",
      note="Note. Reference distributions are assumed (see text). All χ² statistics exceed the critical value at α = .05, as do all KS tests.")
figure("fig2_hourly.png", "Fig. 2. Hourly distribution of posting events: assumed reference profile and three schedulers (mean of three 72-hour runs).")
P(f"Table 2 and Fig. 2 show that the IPP scheduler tracks the daily profile far better than either baseline (r = "
  f"{f(s1['ipp']['r'])} against {f(s1['hpp']['r'])} and {f(s1['poll']['r'])}). Neither HPP nor polling can produce a "
  "diurnal pattern, because neither contains a time-varying component, and the small negative correlations reflect "
  f"chance. IPP also lies closer to the reference on the reply-delay distribution (D = {f(s1['ipp']['ks'])} vs. "
  f"{f(s1['hpp']['ks'])} and {f(s1['poll']['ks'])}). The fit is nevertheless imperfect, and the discrepancies are "
  "systematic. In one representative 72-hour replication, the share of events between midnight and 6 a.m. was "
  f"16.9% against {100*ref[0:6].sum():.1f}% in the reference, the midday window (11:00 to 14:00) was underestimated "
  f"(13.2% vs. {100*ref[11:14].sum():.1f}%), and the evening window (19:00 to 23:00) fell short (27.2% vs. "
  f"{100*ref[19:23].sum():.1f}%). Reply delays are too long: the median is about {f(s1['ipp']['med_delay'],1)} hours against "
  f"0.5 hours in the reference, only {100*s1['ipp']['frac_5min']:.1f}% of replies occur within five minutes against "
  f"{100*float(reference_delay_cdf(5/60)):.1f}% in the reference. The pooled hourly counts are strongly overdispersed "
  f"(variance-to-mean ratio of {f(s1['ipp']['vmr'],0)}, against {f(s1['hpp']['vmr'],1)} under HPP), which reflects the "
  "clustering produced by cascades. We cannot say from these data whether that degree of clustering is realistic.")
P("We therefore conclude that the IPP scheduler is a clear improvement over the two baselines in reproducing the "
  "temporal structure of the assumed reference, but we do not claim statistical equivalence with it, and we do not "
  "claim a match to any real platform.")

H("4.3 Study 2: Seeding strategies and cascade dynamics (RQ2)", 2)
P("A campaign message on one topic was injected at 18:00 under four conditions. In the concentrated condition, the "
  "three accounts with the most followers posted the message. In the distributed condition, randomly chosen "
  "non-influencer accounts posted it, with accounts added until their combined follower count matched or exceeded "
  f"that of the concentrated condition (on average {f(sA['reach']['dist_n_seeds'],0)} accounts, with seed reach of "
  f"about {f(sA['reach']['dist'],0)} vs. {f(sA['reach']['conc'],0)} follower links in the distributed and concentrated "
  "conditions, respectively). A random-three condition with three random ordinary accounts served as a size-matched "
  "control, and a no-seed condition confirmed that organic activity does not generate campaign adoption. Adoption was "
  "defined as a retweet or comment on campaign content, counting each agent once. We recorded the number of adopters, "
  "the number of agents exposed, the times at which 10% and 50% of eventual adopters had adopted (t₁₀ and t₅₀, "
  "measured from the campaign start), and the branching ratio from a maximum-likelihood fit of a Hawkes process with a "
  "constant background and exponential kernel to the campaign event times. We ran 40 paired replications and "
  "compared the concentrated and distributed conditions with Wilcoxon signed-rank tests and bootstrap confidence "
  "intervals for the mean paired difference.")


def row(label, k, nd=1, d_nd=None):
    a = sA[k]
    d_nd = nd if d_nd is None else d_nd
    return [label, f(a["conc"], nd), f(a["dist"], nd), f"{sgn(a['diff'], d_nd)} [{f(a['ci'][0], d_nd)}, {f(a['ci'][1], d_nd)}]", "< .001" if a["p"] < 0.001 else f(a["p"], 3)]


table([["Outcome", "Concentrated", "Distributed", "Difference [95% CI]", "Wilcoxon p"],
       row("Adopters", "adopters", 1),
       row("Agents exposed", "exposed", 1),
       row("t₅₀ (hours)", "t50", 2),
       row("t₁₀ (hours)", "t10", 2),
       row("Hawkes branching ratio", "branching", 3),
       ["Adopters per unit seed reach", f(sA['adopters']['conc'] / sA['reach']['conc'], 3), f(sA['adopters']['dist'] / sA['reach']['dist'], 3), "–", "–"]],
      caption="Table 3. Seeding outcomes (40 paired replications; surrogate oracle)",
      note=f"Note. The random-three control yielded {f(sA['random3']['adopters'],1)} adopters and reached {f(sA['random3']['exposed'],1)} agents on average; the no-seed condition produced no campaign adoption.")
figure("fig3_seeding.png", "Fig. 3. Adopters within 48 hours (left) and time to half of the eventual adopters (right) by seeding strategy; points are individual replications and bars are means (surrogate oracle).")
P(f"Concentrating the campaign on three influencers produced about {100*sA['adopters']['diff']/sA['adopters']['dist']:.0f}% "
  f"more adopters than the distributed condition, and the concentrated condition had the larger outcome in "
  f"{100*sA['adopters']['conc_larger']:.0f}% of the paired replications (paired effect size d_z = {f(sA['adopters']['dz'])}). "
  f"It also reached more agents ({f(sA['exposed']['conc'],0)} vs. {f(sA['exposed']['dist'],0)}), so the advantage in "
  "adopters follows from reach rather than from a higher conversion of exposures: adopters per exposed agent were "
  f"similar ({f(sA['adopters']['conc']/sA['exposed']['conc'],2)} vs. {f(sA['adopters']['dist']/sA['exposed']['dist'],2)}). "
  "We did not test the mechanism. Plausible explanations include second-wave sharing by well-connected adopters "
  "and the larger audiences of high-degree accounts further along the cascade, but we have not separated them.")
P(f"The distributed condition was nevertheless faster. It reached half of its eventual adopters about "
  f"{f(sA['t50']['diff'],1)} hours earlier ({f(sA['t50']['dist'],2)} vs. {f(sA['t50']['conc'],2)} hours), consistent with "
  "hundreds of simultaneous points of exposure compared with three. The concentrated condition was also far more "
  f"variable (standard deviation of adopters of {f(sA['adopters']['conc_sd'],0)} vs. {f(sA['adopters']['dist_sd'],0)}), and "
  f"its outcomes ranged from {f(sA['adopters']['conc_min'],0)} to {f(sA['adopters']['conc_max'],0)}, whereas those of the "
  f"distributed condition ranged from {f(sA['adopters']['dist_min'],0)} to {f(sA['adopters']['dist_max'],0)} (Fig. 3). The "
  "extra variability is mostly upside, however. The distribution of concentrated outcomes has a long right tail, "
  f"and only {100*frac_below:.1f}% of concentrated replications fell below the mean of the distributed condition; the "
  "weakest concentrated replication was about as good as the weakest distributed one. What the distributed strategy "
  "offers is therefore speed and predictability rather than protection against a poor result. Thus the two "
  "strategies differ in expected scale, speed, and spread of outcomes, and no single strategy dominates. The "
  f"random-three control confirms that the advantage is not due to the number of seeds: three ordinary accounts "
  "produced essentially no cascade, because the process is close to critical and total cascade size scales with "
  "initial exposure.")
P(f"The estimated branching ratios were close to one in both conditions ({f(sA['branching']['conc'],3)} and "
  f"{f(sA['branching']['dist'],3)}). The difference of {f(sA['branching']['diff'],3)}, although statistically "
  "detectable, is too small to interpret as evidence that concentrated seeding is more viral. The fitted kernel decay "
  f"rate (about {f(sA['beta_mean'],1)} per hour, or a mean memory of roughly {60/sA['beta_mean']:.0f} minutes) is also "
  "faster than the one-hour stimulus decay built into the simulator, which indicates that a constant-background "
  "exponential Hawkes model is a misspecified summary of these non-stationary cascades. We therefore use the "
  "branching ratio only as a coarse index of criticality.")

H("4.4 Study 3: Rule-based versus LLM-rated intensity (RQ3)", 2)
P("To separate the effect of the oracle from the effect of coarsening, we compared three oracles: the original "
  "surrogate on the continuous state, the same surrogate on the 1,600 coarse states, and ratings from LLM raters on the "
  "same coarse states. No API access was used for rating. Ten independent instances of an LLM (Claude Sonnet) acted as "
  "raters; the 1,600 states were shuffled and divided into ten batches of 160, so each state was rated once and each "
  "rater saw a different random subset. Raters received the instruction in Appendix B, were told not to write code "
  "or formulas to compute scores, and had no access to the simulator. The ratings form a lookup table used by the "
  "simulator.")
P(f"The LLM ratings (mean {f(lv.mean())}, SD {f(lv.std(ddof=1))}, range {f(lv.min(),1)} to {f(lv.max(),1)}) correlated "
  f"strongly with the coarse surrogate (Spearman ρ = {f(rho)}), so the two oracles agree on the ordering of states "
  f"while differing in level and in some details. Ratings were lowest for lurkers (mean {f(g_per['lurker'])} vs. "
  f"{f(min(v for k,v in g_per.items() if k!='lurker'))} to {f(max(g_per.values()))} for other personas), increased with the "
  f"volume of relevant feed items ({f(g_vol[0])}, {f(g_vol[1])}, {f(g_vol[2])}, and {f(g_vol[3])} for 0, 1, 2, and 3 or "
  f"more items), with topical relevance ({f(g_rel[0])}, {f(g_rel[1])}, and {f(g_rel[2])} for low, medium, and high, among "
  f"states with items), and with the presence of a notification ({f(g_not[1])} vs. {f(g_not[0])}), and varied little by "
  f"time of day ({f(min(g_pd.values()))} to {f(max(g_pd.values()))}). Indifferent emotion lowered the rating "
  f"({f(g_emo['indifferent'])} vs. {f(min(v for k,v in g_emo.items() if k!='indifferent'))} to "
  f"{f(max(v for k,v in g_emo.items() if k!='indifferent'))}). Because each state was rated by only one rater, rater "
  "effects cannot be separated from state effects, and we could not measure the repeatability of ratings.")
sL, sC = S2["llm"], S2["coa"]


def r3(label, d, n):
    a = d["adopters"]
    return [f"{label} ({n})", f(a["conc"], 0), f(a["dist"], 0), f"{sgn(a['diff'],0)} ({'< .001' if a['p']<0.001 else f(a['p'],3)})",
            f"{100*a['conc_larger']:.0f}%", sgn(d["t50"]["diff"], 2)]


table([["Oracle (replications)", "Concentrated adopters", "Distributed adopters", "Difference (p)", "Concentrated larger", "t₅₀ difference (h)"],
       r3("Surrogate, continuous states", sA, 40), r3("Surrogate, coarse states", sC, 30), r3("LLM-rated, coarse states", sL, 30)],
      caption="Table 4. Sensitivity of seeding results to the intensity oracle",
      note=("Note. Differences are concentrated minus distributed; p-values are from Wilcoxon signed-rank tests. For the behavioral "
            f"comparison under IPP (five replications, 800 agents), the LLM oracle yielded r = {f(beh['llm:llm_table.json']['r'])}, "
            f"TV = {f(beh['llm:llm_table.json']['tv'],3)}, and D = {f(beh['llm:llm_table.json']['ks'],3)}, against r = {f(beh['coarse']['r'])}, "
            f"TV = {f(beh['coarse']['tv'],3)}, and D = {f(beh['coarse']['ks'],3)} for the surrogate on the same coarse states."))
P("The substantive conclusions were the same under all three oracles: the concentrated strategy produced more adopters "
  "and the distributed strategy was faster. The LLM oracle gave a concentrated advantage of similar size to the "
  "surrogate ratings, and in terms of behavioral plausibility it was practically indistinguishable from the "
  f"surrogate, and it did not repair the reply-delay shortfall (median {f(beh['llm:llm_table.json']['med_delay'])} hours). In short, the results "
  "of Studies 1 and 2 appear robust to the oracle, but the LLM oracle did not by itself improve fidelity.")

H("4.5 Sensitivity to manual parameters and network structure (RQ3)", 2)
P("Several parameters were set manually so that the synthetic system would not become supercritical. We therefore "
  "varied one setting at a time (κ, S_max, p_view, and the follower network) with 15 paired replications per "
  "configuration, comparing the concentrated and distributed conditions. Two alternative networks were used: a random "
  "network in which each agent follows three uniformly chosen others, and a community network with ten blocks in "
  "which 80% of follow links stay inside the block, with preferential attachment inside and across blocks.")
rows = [["Configuration", "Concentrated adopters", "Distributed adopters", "Difference [95% CI]", "Concentrated larger", "t₅₀ difference (h)"]]
for k, lab in [("base", "Base case"), ("kappa=0.12", "κ = 0.12"), ("kappa=0.2", "κ = 0.20"), ("S_max=2.0", "S_max = 2"),
               ("S_max=4.0", "S_max = 4"), ("p_view=0.4", "p_view = 0.4"), ("p_view=0.6", "p_view = 0.6"),
               ("net=random", "Random network"), ("net=community", "Community network")]:
    r = sens[k]
    rows.append([lab, f(r["conc"], 0), f(r["dist"], 0), f"{sgn(r['diff'],0)} [{sgn(r['lo'],0)}, {sgn(r['hi'],0)}]",
                 f"{100*r['frac']:.0f}%", sgn(r["t50diff"], 2)])
table(rows, caption="Table 5. One-at-a-time sensitivity of the seeding comparison (15 paired replications each)",
      note="Note. Adopters within 48 hours; the base case uses the first 15 seeds of Study 2, so it differs from Table 3.")
n_pos = sum(1 for k, r in sens.items() if k not in ("net=random",) and r["lo"] > 0)
n_all_pa = len(sens) - 1
P(f"On the preferential-attachment and community networks the concentrated condition had more adopters in every "
  f"configuration, and the 95% interval excluded zero in {n_pos} of {n_all_pa} of them; in the remaining configurations "
  "(S_max = 2, p_view = 0.4, and the community network) the interval included zero, so the direction is consistent "
  "but the evidence is weaker there. The speed advantage of the distributed condition was also positive in every "
  "such configuration. On the random network, cascades remained small (about "
  f"{f(sens['net=random']['conc'],0)} adopters) and the two strategies did not differ, which shows that the scale "
  "advantage of concentration depends on a heavy-tailed follower distribution. Because the base case reaches about "
  "criticality (Table 3), small parameter changes move the size of the effect considerably; the sign is more "
  "stable than the magnitude.")

# ------------------------------------------------------------------ 5 Discussion
H("5. Discussion")
H("5.1 Implications for decision makers", 2)
P("For campaign managers and platform operators who use simulation to pre-test seeding plans, the results suggest "
  "framing the decision around the objective rather than asking which strategy is better in general (Table 6). "
  "If the aim is the largest expected engagement, concentration on prominent accounts is favored in this setting. If "
  "the campaign is time sensitive, as in a product launch with a short attention window or a public-safety "
  "announcement, or if the outcome must be predictable, broad distribution is favored. Because the conclusions come "
  "from a synthetic network and assumed parameters, they should be treated as hypotheses for field testing and not as "
  "prescriptions.")
table([["Decision maker's objective", "Favored plan in this study", "Evidence"],
       ["Maximize expected number of adopters", "Concentrate on a few high-degree accounts", f"+{f(sA['adopters']['diff'],0)} adopters on average; positive on all heavy-tailed networks tested"],
       ["Reach half of the audience quickly", "Distribute across many ordinary accounts", f"t₅₀ about {f(sA['t50']['diff'],1)} h earlier"],
       ["Predictable outcome", "Distribute across many ordinary accounts", f"SD of adopters {f(sA['adopters']['dist_sd'],0)} vs. {f(sA['adopters']['conc_sd'],0)}"],
       ["Network without heavy-tailed followers", "No clear difference", "Random network: no detectable difference"]],
      caption="Table 6. Decision guide derived from the simulations")
H("5.2 Contributions to research", 2)
P("The simulator makes three contributions. First, it separates two roles that LLM-agent simulators usually merge. "
  "The LLM is used for a judgment it is plausibly able to make, namely how strongly a situation motivates a persona "
  "to speak, whereas timing is handled by a point process whose properties are well understood. This separation "
  "yields an explicit link between a language-model output and a rate parameter, and it makes the temporal "
  "assumptions inspectable and testable, which is not possible when timing is implicit in the simulation loop.")
P("Second, endogenous timing matters for conclusions. Because action times emerge from agent state, the simulator "
  "reproduces a daily cycle that polling and homogeneous schedules cannot, and it generates reactive cascades "
  "without a prescribed excitation kernel. The stability observation in Section 3.5 is narrower than a general "
  "result: under the exposure rule, persona gains, and circadian baseline used here, the additive form needs an "
  "explicit saturation if the simulator is to remain a finite event-driven process. Whether a real platform requires "
  "saturation, and at what level, is an empirical question this synthetic study cannot answer.")
P("Third, the seeding results qualify the influencer debate. Under an equal exposure budget, concentration on "
  "influencers produced more engagement in expectation, which is consistent with the view that high-degree accounts "
  "matter (Bakshy et al., 2011), yet distribution produced faster and more predictable diffusion, which is in the "
  "spirit of the argument that many ordinary users can do the work (Watts and Dodds, 2007). The simulation suggests "
  "that the two positions need not conflict once one separates the objective (scale vs. speed) and the "
  "requirement for predictability, and that the advantage of influencers depends on the follower distribution.")
H("5.3 Limitations and future research", 2)
P("Several limitations bound the conclusions. The most important is the absence of empirical reference data. The "
  "behavioral comparison in Study 1 uses parametric references that we specified, so the results show that the "
  "scheduler is closer to the assumed regularities than the alternatives are, not that it is close to any real "
  "platform. In addition, several design choices that the specification leaves open (the shape of the circadian "
  "profile, the emotion model, the surrogate coefficients, the recency weighting of feed items) were set by us and "
  "the recency weighting was adjusted so that reply delays are on a realistic scale, which makes the reported fit "
  "optimistic as a test of out-of-sample validity. A confirmatory evaluation should calibrate on one part of a real "
  "trace and test on a held-out part, for example using the timestamps of public posts and the reply delays of a "
  "public discussion platform. The simulator accepts such data without modification.")
P("Second, the sensitivity analysis varied one setting at a time on a small number of replications; it does not "
  "cover interactions, and the capped system operates close to criticality, so magnitudes are fragile. Third, the "
  "networks are synthetic, and real networks have community structure, homophily, and different degree "
  "distributions; our community network is a first step only. Fourth, the LLM ratings came from ten rater instances "
  "each rating a different batch of coarse states, so we could not test the repeatability of ratings, batching may "
  "induce anchoring across items, and the model never saw the full context of any individual agent. Finally, the "
  "median reply delay is too long and the tail too light, which indicates that a single exponential stimulus decay "
  "is too restrictive. A mixture of short and long decay components is a natural extension.")
P("Future work can proceed in three directions: confirmatory validation against real traces, a systematic "
  "sensitivity and robustness analysis including alternative network models and interactions among parameters, and "
  "richer oracles that supply the full agent context to the model on each call, together with studies of "
  "repeatability across models and prompts.")

H("6. Conclusion")
P("This study asked whether the timing of LLM agents in a simulated social platform should be determined by a polling "
  "clock or by a stochastic process driven by agent state, and what the answer means for a campaign decision. We "
  "specified and evaluated an inhomogeneous Poisson process simulator in which an LLM supplies the strength of an "
  "agent's stimulus and the process supplies the timing. The simulator reproduces a stylized daily profile much "
  "better than homogeneous or periodic scheduling, supports an equal-budget comparison of seeding strategies in "
  "which concentration raises expected scale and distribution raises speed and predictability, and yields "
  "conclusions that are robust to whether intensity is rule-based or LLM-assigned. The evidence is limited by the "
  "lack of real trace data, by manual parameterization, and by the dependence of the scale advantage on the network. "
  "We offer the simulator and the evaluation protocol so that these gaps can be closed in subsequent work.")

H("Declarations", 2)
P("Declaration of generative AI use: [to be completed by the authors. The ten LLM raters of Study 3 are part of the "
  "method and are described in Section 4.4; any use of generative AI in preparing the manuscript must be declared "
  "according to the journal's policy.]", hl=True)
P("Data and code availability: [anonymized repository link to be inserted.]", hl=True)
P("Declaration of competing interest, funding, and CRediT author statement: [see the title page.]", hl=True)

H("References")
REFS = [
    "Aral, S., Walker, D., 2012. Identifying influential and susceptible members of social networks. Science 337 (6092), 337–341.",
    "Bakshy, E., Hofman, J.M., Mason, W.A., Watts, D.J., 2011. Everyone's an influencer: quantifying influence on Twitter. In: Proceedings of the Fourth ACM International Conference on Web Search and Data Mining. ACM, New York, pp. 65–74.",
    "Barabási, A.-L., 2005. The origin of bursts and heavy tails in human dynamics. Nature 435 (7039), 207–211.",
    "Barabási, A.-L., Albert, R., 1999. Emergence of scaling in random networks. Science 286 (5439), 509–512.",
    "Bonabeau, E., 2002. Agent-based modeling: methods and techniques for simulating human systems. Proc. Natl. Acad. Sci. 99 (suppl. 3), 7280–7287.",
    "Crane, R., Sornette, D., 2008. Robust dynamic classes revealed by measuring the response function of a social system. Proc. Natl. Acad. Sci. 105 (41), 15649–15653.",
    "Gao, C., Lan, X., Lu, Z., Mao, J., Piao, J., Wang, H., Jin, D., Li, Y., 2023. S3: social-network simulation system with large language model-empowered agents. arXiv:2307.14984.",
    "Gilbert, N., 2008. Agent-Based Models. Sage Publications, Thousand Oaks, CA.",
    "Hawkes, A.G., 1971. Spectra of some self-exciting and mutually exciting point processes. Biometrika 58 (1), 83–90.",
    "Kempe, D., Kleinberg, J., Tardos, É., 2003. Maximizing the spread of influence through a social network. In: Proceedings of the Ninth ACM SIGKDD International Conference on Knowledge Discovery and Data Mining. ACM, New York, pp. 137–146.",
    "Lewis, P.A.W., Shedler, G.S., 1979. Simulation of nonhomogeneous Poisson processes by thinning. Nav. Res. Logist. Q. 26 (3), 403–413.",
    "Malmgren, R.D., Stouffer, D.B., Motter, A.E., Amaral, L.A.N., 2008. A Poissonian explanation for heavy tails in e-mail communication. Proc. Natl. Acad. Sci. 105 (47), 18153–18158.",
    "Ogata, Y., 1981. On Lewis' simulation method for point processes. IEEE Trans. Inf. Theory 27 (1), 23–31.",
    "Park, J.S., O'Brien, J.C., Cai, C.J., Morris, M.R., Liang, P., Bernstein, M.S., 2023. Generative agents: interactive simulacra of human behavior. In: Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology. ACM, New York.",
    "Rand, W., Rust, R.T., 2011. Agent-based modeling in marketing: guidelines for rigor. Int. J. Res. Mark. 28 (3), 181–193.",
    "Törnberg, P., Valeeva, D., Uitermark, J., Bail, C., 2023. Simulating social media using large language models to evaluate alternative news feed algorithms. arXiv:2310.05984.",
    "Watts, D.J., Dodds, P.S., 2007. Influentials, networks, and public opinion formation. J. Consum. Res. 34 (4), 441–458.",
    "Zhao, Q., Erdogdu, M.A., He, H.Y., Rajaraman, A., Leskovec, J., 2015. SEISMIC: a self-exciting point process model for predicting tweet popularity. In: Proceedings of the 21st ACM SIGKDD International Conference on Knowledge Discovery and Data Mining. ACM, New York, pp. 1513–1522.",
]
for r_ in REFS:
    p = doc.add_paragraph(r_)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.first_line_indent = Inches(-0.3)
P("The reference style (author-year, Elsevier-like) must be checked against the journal's current Guide for Authors.", italic=True, hl=True)

H("Appendix A. Simulation settings and assumptions")
table([["Parameter", "Value", "Remarks"],
       ["Stimulus scale κ", "0.16", "Set manually for this synthetic run; see Sections 3.5 and 4.5"],
       ["Stimulus decay τ", "1 hour", "Single exponential component"],
       ["Stimulus cap S_max", "3.0", "Synthetic saturation"],
       ["Exposure probability p_view", "0.5", "Posts and retweets"],
       ["Comment visibility factor", "0.4", "Multiplies p_view"],
       ["Feed capacity", "40 items", "Most recent items"],
       ["Recency weight for replies and retweets", "exp(−age/2 h)", "Assumption of this instantiation"],
       ["Circadian profile", "Floor 0.12 + evening Gaussian (sd 2.2 h) + midday Gaussian at 12.5 h (weight 0.45, sd 1.8 h)", "Normalized to mean one; assumption"],
       ["Emotion model", "excited / angry / happy / indifferent drawn with probabilities .20 / .15 / .30 / .35 at each oracle call", "Assumption"],
       ["Relevance level", "Low < 0.10 ≤ medium < 0.30 ≤ high (interest weight)", "Assumption"],
       ["Network (Study 1)", "800 agents, m = 5", "Preferential attachment"],
       ["Network (Studies 2–3)", "2,000 agents, m = 3", "Preferential attachment"],
       ["Horizon", "72 h (Study 1); 18 h warm-up plus 48 h (Studies 2–3)", "Campaign starts at 18:00"],
       ["Replications", "5 (Study 1); 40 / 30 / 30 (Studies 2–3); 15 (sensitivity)", "Paired by network and seed"]],
      caption="Table A.1. Global simulation parameters and assumptions")
H("Appendix B. Intensity oracle prompt")
P("The instruction below was given to each LLM rater; the persona and state fields in brackets were filled in "
  "programmatically.")
P("[System] You are the behavior controller of a virtual SNS user: (persona description). Given the user's current "
  "state and surroundings, rate on a real-valued scale from 0.0 to 5.0 the urge (Intensity) this user feels, within "
  "the next hour, to write a new post or leave a comment on the SNS.")
P("[Current situation] Time of day: [period]. Current emotion: [emotion]. Timeline update: [n] posts on topics of "
  "interest appeared in the feed within the last hour (the latest concerns a topic of [low / medium / high] interest). "
  "Notifications: [none / present].")
P("[Output] A rating between 0.0 and 5.0.")
doc.save(OUT + "DSS_manuscript_anonymized.docx")

# ------------------------------------------------------------------ title page + highlights file
tp = Document()
tp.styles["Normal"].font.name = "Times New Roman"
tp.add_heading("Title page (not sent to reviewers)", 1)
tp.add_paragraph(TITLE)
tp.add_paragraph("Authors: [names, affiliations, corresponding author, e-mail, ORCID]")
tp.add_paragraph("Acknowledgements and funding: [to be completed]")
tp.add_paragraph("CRediT author statement: [to be completed]")
tp.add_paragraph("Declaration of competing interest: [to be completed]")
tp.add_heading("Highlights (separate file, if the journal asks for one)", 1)
for h in HL:
    tp.add_paragraph(h, style="List Bullet")
tp.save(OUT + "DSS_title_page_and_highlights.docx")
print("saved")
