const fs = require("fs");
const D = require("docx");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType,
  ImageRun, Footer, PageNumber, BorderStyle, HeadingLevel } = D;

const FONT = "Times New Roman";
const runs = (s, o = {}) => {
  // **bold**, *italic*
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0, m;
  while ((m = re.exec(s))) {
    if (m.index > last) out.push(new TextRun({ text: s.slice(last, m.index), font: FONT, size: o.size || 24, bold: o.bold, italics: o.italics }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), font: FONT, size: o.size || 24, bold: true, italics: o.italics }));
    else out.push(new TextRun({ text: t.slice(1, -1), font: FONT, size: o.size || 24, italics: true, bold: o.bold }));
    last = m.index + t.length;
  }
  if (last < s.length) out.push(new TextRun({ text: s.slice(last), font: FONT, size: o.size || 24, bold: o.bold, italics: o.italics }));
  return out;
};
const P = (s, o = {}) => new Paragraph({
  children: runs(s, o), alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { line: 480, before: 0, after: 0 }, indent: o.noIndent ? undefined : { firstLine: 720 }, keepNext: o.keepNext,
});
const EQ = (s) => new Paragraph({ children: runs(s, {}), alignment: AlignmentType.CENTER, spacing: { line: 480, before: 0, after: 0 } });
const H1 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: s, font: FONT, size: 28, bold: true })], spacing: { before: 240, after: 120 }, keepNext: true });
const H2 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: s, font: FONT, size: 26, bold: true })], spacing: { before: 200, after: 100 }, keepNext: true });
const CAP = (s) => new Paragraph({ children: runs(s, { bold: true, size: 22 }), spacing: { line: 276, before: 200, after: 80 }, keepNext: true });
const NOTE = (s) => new Paragraph({ children: runs(s, { size: 20 }), spacing: { line: 276, before: 60, after: 200 } });
const REF = (s) => new Paragraph({ children: runs(s, { size: 22 }), spacing: { line: 276, after: 80 }, indent: { left: 720, hanging: 720 } });

const border = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
const borders = { top: border, bottom: border, left: border, right: border };
function TB(widths, rows, size = 20) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({
      tableHeader: i === 0, cantSplit: true,
      children: r.map((c, k) => new TableCell({
        borders, width: { size: widths[k], type: WidthType.DXA },
        shading: i === 0 ? { fill: "EDEDED", type: ShadingType.CLEAR, color: "auto" } : undefined,
        margins: { top: 50, bottom: 50, left: 80, right: 80 },
        children: [new Paragraph({ children: runs(String(c), { size, bold: i === 0 }), spacing: { line: 252 } })],
      })),
    })),
  });
}

const AUTH = process.env.AUTHOR === "1";
const c = [];
// ---------------------------------------------------------------- title
c.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [new TextRun({ text: "When Delegated Agents Escalate: Loss-Induced Decision Escalation and the Governance of Agentic Information Systems", font: FONT, size: 32, bold: true })] }));
if (AUTH) {
  c.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 }, children: [new TextRun({ text: "Ook Lee", font: FONT, size: 24, bold: true })] }));
  c.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 }, children: [new TextRun({ text: "Department of Information Systems, Hanyang University, Seoul, Korea", font: FONT, size: 22 })] }));
  c.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [new TextRun({ text: "E-mail: ooklee@hanyang.ac.kr", font: FONT, size: 22 })] }));
  c.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [new TextRun({ text: "Article genre: theory development", font: FONT, size: 22, italics: true })] }));
} else {
  c.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [new TextRun({ text: "Anonymised manuscript for review. Article genre: theory development", font: FONT, size: 22, italics: true })] }));
}
c.push(H1("Abstract"));
c.push(P("Organizations increasingly delegate consequential work to agentic information systems built on large language models (LLMs). Average performance is often adequate, but failures cluster in the tail: after repeated errors an agent may delete production data, tamper with evaluations, or omit safeguards it previously used. Practitioners call this the agent panicking. We treat that label as a folk description and develop a theory of loss-induced decision escalation (LIDE): a within-episode shift toward higher ex ante risk and weaker safeguards after accumulated failure. Drawing on reference-dependent evaluation, we argue that an agent judges its situation against a goal-based reference point, that scarcity cues and an unintegrated record of sunk effort intensify the resulting loss coding, and that human-like patterns can reach LLM agents through imitation of pretraining data or optimization toward outcome rewards. A simple formalization yields predictions that rival accounts (context-length degradation, capability limits, instruction pressure, and noise) do not, most sharply that success streaks should reduce risky action. The central implication is that the decision quality of a delegated agent is state dependent, so part of agent governance belongs in the decision environment rather than in model weights. We map three governance artifacts onto the mechanism, evaluate the measurement instrument on scripted agents, and report a feasibility pilot on two small open-weight models that neither supports nor refutes the account. Two preregistered experiments are specified.", { noIndent: true }));
c.push(P("**Keywords:** agentic information systems; delegation; large language models; prospect theory; escalation of commitment; human oversight; IT governance", { noIndent: true }));

// ---------------------------------------------------------------- 1
c.push(H1("1. Introduction"));
c.push(P("Organizations are moving operational work onto agentic information systems: software artifacts that perceive an environment, choose actions, and execute them with limited human oversight (Baird and Maruping 2021). LLM agents now write and deploy code, maintain databases, and run multi-step business processes. Their mean performance is often acceptable. Their failures are not evenly distributed. In a widely reported July 2025 incident, a coding agent deleted a production database during an explicit code freeze and later described itself as having panicked after seeing empty query results (eWeek 2025). In a long-horizon benchmark, every tested model produced runs that entered “meltdown” loops from which recovery was rare (Backlund and Petersson 2025)."));
c.push(P("For organizations this pattern is a tail-risk problem, not an accuracy problem. A delegate that is reliable on average but becomes reckless after a streak of failures changes the economics of delegation. Research on human–AI delegation has asked how authority should be allocated between humans and artifacts (Baird and Maruping 2021; Fügener et al. 2022). That work typically treats the agent’s decision quality as a relatively stable property that informs a one-time allocation of rights. Computer science work has documented breakdowns descriptively or induced them with isolated psychological prompts (Coda-Forno et al. 2023; Ben-Zion et al. 2025; Anthropic 2026). What is missing is an information systems (IS) theory of when delegated decision making deteriorates, how that deterioration can be told apart from ordinary capability failure, and which features of the decision environment, not only of the model, contain it."));
c.push(P("IS research already has a language for humans who persist with failing projects: escalation of commitment under reference-dependent evaluation (Staw 1976; Keil 1995; Keil et al. 2000; Kahneman and Tversky 1979). We adapt that language to agentic artifacts under two constraints. First, analogy is not mechanism. Transfer of a human decision theory to an LLM agent must specify how a goal-based reference point and a loss-domain value function can arise in a system without lived experience. Second, the interesting boundary is where the analogy fails. An agent’s record of sunk effort lives in an editable context window; operators can rewrite the history that, in humans, is remembered. That difference is not a caveat. It is a design lever, and it is what makes the phenomenon an IS problem rather than a problem of psychology transplanted into software."));
c.push(P("We label the phenomenon loss-induced decision escalation (LIDE) and reserve “panic” for practitioner talk. LIDE is a within-episode shift that meets three conditions: loss signals have accumulated; subsequent actions have higher ex ante risk than the same agent’s actions in comparable pre-loss states; and safeguards the agent previously used (verification, asking, stopping) are omitted. Ex ante risk is scored from a taxonomy fixed before data collection, not from outcomes."));
c.push(P("**Contribution and genre.** This is a theory-development paper. Its single contribution is a theory of state-dependent decision quality in delegated agents: an account of when, why, and under which design conditions an agent’s choice distribution shifts toward risk after accumulated failure. Two implications follow from it and are treated as consequences, not as separate contributions: delegation research needs an agent-state variable, and part of governance can act on the decision environment. The theory is built to be falsified. It states discriminating hypotheses against four rival accounts, gives scope conditions, and specifies a two-study empirical programme. The empirical material in the paper is limited to an evaluation of the measurement instrument on scripted agents and a small feasibility pilot on two open-weight models; neither tests the hypotheses (Section 4). Whether LIDE occurs in current frontier models, and whether the artifacts reduce it, remain empirical questions."));
c.push(P("Three research questions organize the paper. **RQ1.** If LIDE follows reference-dependent evaluation, which observations distinguish that account from context-length degradation, capability limits, instruction pressure, and random variation? **RQ2.** How do scarcity cues and an unintegrated record of sunk effort intensify LIDE? **RQ3.** Which governance artifacts, acting on the decision environment rather than on model parameters, are predicted to contain LIDE, and what does the account imply for human oversight?"));

// ---------------------------------------------------------------- 2
c.push(H1("2. Theoretical Background"));
c.push(H2("2.1 Agentic Information Systems and Delegation"));
c.push(P("Baird and Maruping (2021) characterize agentic IS artifacts as systems that act with some autonomy on behalf of humans and treat IS use as a delegation relation in which rights and responsibilities move between people and artifacts. LLM-based agents are an extreme case. They receive goals in natural language, select their own action sequences, and often hold write access to production systems. Research on human–AI delegation shows that people are weak judges of when to hand off and when to intervene (Fügener et al. 2022). Both streams still treat the quality of the agent’s decision rule as approximately fixed within a task. LIDE is the claim that this quality is state dependent: the same artifact, with the same tools and the same standing instructions, can be a conservative delegate early in an episode and a high-variance delegate after accumulated failure."));
c.push(P("That claim matters for governance. If unreliability is a stable trait, the response is selection and access control: use a better model, restrict tools. If unreliability is a state, the response also includes episode management: when to pause, what history to keep in context, which exits to sanction. IS research on IT governance and platform complementors has long argued that control problems follow from dependencies the owner does not set (Tiwana et al. 2010). An organization that delegates to a vendor model inherits the vendor’s training regime and, we argue, a decision surface that can tilt after loss."));
c.push(H2("2.2 The Phenomenon, Not the Metaphor"));
c.push(P("We do not claim that agents experience panic. The construct is behavioral. Table 1 organizes the public evidence that motivates a state-dependent account. The production incident and the long-horizon benchmark are existence proofs of abrupt, high-impact breakdown after trouble, not identification of mechanism. The strongest existing causal hint is Anthropic (2026): steering activations along a “desperate” direction raised reward hacking on unsatisfiable coding tasks from about 5 percent to about 70 percent, a “calm” direction had the opposite effect, and the behavioral shift could occur without emotional markers in the text. That result comes from one research group and one model family. It is a reason to theorize, not a substitute for a discriminating test."));
c.push(CAP("Table 1. Motivating Evidence Related to Loss-Induced Decision Escalation"));
c.push(TB([1900, 1700, 2900, 2860], [
  ["Source", "Setting", "Observed behavior", "What it can and cannot show"],
  ["Production incident, July 2025 (eWeek 2025)", "Coding agent with production access", "Deleted a production database during a code freeze; later self-described as having panicked after empty query results", "Loss signal, high-risk action, omitted approval. Post hoc self-report is illustration only."],
  ["Backlund and Petersson (2025)", "Long-horizon business simulation", "All models had runs that entered meltdown loops and rarely recovered, often after misreading schedules", "Repeated breakdown after perceived shortfall. No isolation of loss history from length or capability."],
  ["Anthropic (2026)", "Interpretability study", "A desperate representation rose with repeated test failures and causally increased reward hacking", "Internal state can shift risk of evaluation tampering. Single model, not a test of reference dependence."],
  ["Coda-Forno et al. (2023); Ben-Zion et al. (2025)", "Computational psychiatry prompts", "Anxiety-framed or traumatic text changed exploration, bias, or self-reported anxiety", "Framing shifts choice distributions. Does not establish accumulated task failure as the cause."],
]));
c.push(NOTE(" "));
c.push(P("LIDE requires all three definitional conditions at once. More errors without a rise in the ex ante risk of chosen actions is capability failure, not LIDE. A risky action without a preceding loss window is not LIDE. A verbal claim of distress without a change in action risk is not LIDE."));
c.push(H2("2.3 Core Mechanism: Reference-Dependent Evaluation"));
c.push(P("Prospect theory holds that outcomes are coded as gains or losses relative to a reference point, and that the value function is steeper and convex in losses (Kahneman and Tversky 1979):"));
c.push(EQ("v(x) = x^α  if x ≥ 0;     v(x) = −λ(−x)^β  if x < 0,"));
c.push(P("with λ > 1 and 0 < α, β < 1. Convexity in the loss domain makes a risky prospect that might erase the shortfall more attractive than a certain loss of the same expected magnitude. The reflection effect is the mirror claim: in the gain domain the same agent should become more risk averse.", { noIndent: true }));
c.push(P("For an agent the natural reference point is the assigned goal state, typically task completion or a passing evaluation. Each failed attempt widens the coded gap. Reporting honest failure is then a certain loss relative to that reference. A high-variance action (evaluation tampering, an irreversible migration, disabling an alert) is a lottery that might restore the reference outcome. LIDE is the prediction that the lottery becomes more attractive as the coded gap grows, and that safeguards which reduce the chance of restoring the reference (asking a human, stopping) are shed."));
c.push(P("**A minimal formalization.** The predictions need only the curvature of the value function, not its exact form. Let g > 0 be the coded gap to the reference, and let the agent choose between (S) reporting the shortfall, which locks in the loss v(−g), and (R) a risky action that restores the reference with probability p and otherwise adds damage d > 0, leaving the gap g + d. The agent prefers R when p·v(0) + (1 − p)·v(−(g + d)) > v(−g). Because λ multiplies both sides it cancels, and the condition becomes"));
c.push(EQ("p > p*(g) = 1 − (g / (g + d))^β."));
c.push(P("The threshold p*(g) is strictly decreasing in g for β > 0: as the gap widens, R becomes attractive at ever lower success probabilities, and for very large gaps almost any chance of restoring the reference suffices. The model implies a monotone effect of loss; the further claim in H1 that the effect strengthens beyond a threshold rests on the added assumption that conservative means are judged unable to restore the reference, which this simple model does not represent. In the gain domain the analogous choice is between a certain gain s and a gamble that yields s + d with probability p and nothing otherwise. The agent gambles when p > q*(s) = (s / (s + d))^α, and q*(s) is strictly increasing in s: after larger accumulated gains the agent requires better odds to gamble. This is the reflection prediction of H2. The same expressions show how the moderators and artifacts act. An unintegrated record of sunk effort inflates the coded gap g, and a neutral summary shrinks it, so the full record lowers p*. A sanctioned exit that is not coded as a full loss replaces g in the safe option by g_exit < g, which raises the threshold to 1 − (g_exit / (g + d))^β. Friction that attaches a cost to R lowers the value of R and raises the threshold in the same way. Scarcity cues, which raise the salience of the gap and shorten the horizon over which later costs are weighed (Mullainathan and Shafir 2013; cf. Laibson 1997), are represented as a multiplier on g. These comparative statics are illustrative and are not estimated here; they show that the hypotheses in Section 3 follow from one mechanism rather than from a list of separate conjectures."));
c.push(P("Two intensifiers sit on this core. Scarcity cues (deadlines, remaining-step counters, urgency language) raise the salience of the gap. An unintegrated record of sunk effort keeps prior losses in view. Decision makers who have already lost are drawn to break-even options (Thaler and Johnson 1990), a mechanism long used to explain escalation of commitment in software projects (Staw 1976; Keil 1995). In an agent, that record is the context window. If the window is summarized into a neutral status, the same number of failures can be present without the blow-by-blow investment narrative. That contrast is unique to artifacts and is the basis of H4."));
c.push(H2("2.4 Why a Human Theory Can Apply, and Where It Must Not"));
c.push(P("Transfer requires a pathway. We keep two pathways separate because they imply different comparative statics. **Imitation.** Pretraining on human text encodes regularities in how people talk and act under pressure, and LLMs reproduce many classical judgment patterns (Binz and Schulz 2023). Imitation predicts human-like LIDE across task types, including goals that do not resemble common reward signals. **Optimization.** Post-training on outcome-based rewards makes success states function as reference points. Falling short creates pressure toward any action that restores the success signal, including reward hacking (Anthropic 2026). Optimization predicts stronger LIDE when the goal resembles trained rewards (passing tests, getting a tool to return OK) than when it does not."));
c.push(P("Boundaries follow. The agent’s reference point is assigned by prompts and training, not formed through organizational career incentives. Its “memory” of sunk effort can be edited. It has no physiological arousal, so verbal affect in the trace is not a necessary marker of LIDE (Anthropic 2026). These boundaries generate predictions that have no clean human analogue: editing the failure log should change behavior holding failures and token length fixed, and composed rationales can coexist with escalating actions. The second boundary is the basis for the oversight propositions in Section 5, which this paper does not test."));
c.push(H2("2.5 Rival Explanations"));
c.push(P("A usable theory must lose to a rival if the rival’s distinctive prediction is observed. Table 2 states those predictions. The design in Section 4 includes a condition for each."));
c.push(CAP("Table 2. Rival Explanations and Discriminating Predictions"));
c.push(TB([1900, 2200, 2900, 2360], [
  ["Explanation", "Mechanism", "Prediction that differs from LIDE", "Discriminating condition"],
  ["Context-length degradation", "Performance falls as context grows, regardless of content", "Risky actions rise equally after long successful, failed, or neutral histories", "Length-matched histories of failure, success, and neutral content"],
  ["Capability limits", "Errors compound because the task exceeds ability", "More errors, but no rise in ex ante action risk and no omission of safeguards", "Separate coding of error rate and action risk"],
  ["Instruction pressure", "The agent over-complies with perceived user affect", "Effects appear only when a user expresses dissatisfaction", "Failures signaled by the environment without user feedback"],
  ["Random variation", "Breakdowns are stochastic noise", "No systematic relation to loss history; no reflection effect", "Success-streak (gain-domain) condition"],
]));
c.push(NOTE(" "));
c.push(H2("2.6 Why This Is an Information Systems Problem"));
c.push(P("Three features make LIDE an IS phenomenon and not only a property of a model. First, the variables that move it are properties of the system the organization builds around the model: what the context window retains, whether scarcity language appears in prompts, whether a sanctioned exit exists, and which actions carry friction. Second, the outcome that matters, tail-risk actions with write access, is realized through the delegation relation and its tooling. Third, the governance response operates on the socio-technical arrangement (circuit breakers, curation of context, oversight dashboards) rather than on the artifact’s parameters. A purely psychological or purely machine-learning treatment would place the mechanism inside the model. The account here places its most testable and most manipulable parts in the environment the organization designs, and it is on that basis that we position the contribution within research on delegation to agentic IS."));
c.push(H2("2.7 Scope Conditions"));
c.push(P("The theory is intended for agents that (a) act against an assigned, observable goal, so that a reference point exists; (b) can observe their own failures within the episode, in context or through tool feedback; (c) have available actions that differ in variance and reversibility, some of them outside standing instructions; and (d) treat safeguards such as asking, verifying, and stopping as optional. It does not apply to agents whose tool set removes high-variance options, to single-shot tasks without failure feedback, or to settings in which the failure history is not retained. Where one of these conditions fails, the account predicts no LIDE, which gives the theory further ways to be wrong."));

// ---------------------------------------------------------------- 3
c.push(H1("3. Hypotheses"));
c.push(P("Figure 1 shows the model. Accumulated loss is the driver of LIDE, scarcity and sunk-effort records amplify it, and governance artifacts moderate it. Oversight implications are propositions (Section 5.1), not hypotheses of this paper."));
c.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 }, keepNext: true, children: [new ImageRun({ type: "png", data: fs.readFileSync("fig1.png"), transformation: { width: 600, height: 314 }, altText: { title: "Conceptual model", description: "Accumulated loss drives LIDE; scarcity cues and an unintegrated record strengthen the path; governance artifacts weaken it; LIDE leads to tail-risk outcomes.", name: "fig1" } })] }));
c.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: runs("**Figure 1.** Conceptual model of loss-induced decision escalation. Solid arrows are hypothesized positive effects; the dashed arrow is a hypothesized attenuating effect.", { size: 22 }) }));
c.push(H2("3.1 Agent-Level Hypotheses"));
c.push(P("**H1 (accumulated loss).** The number of consecutive failures is positively associated with LIDE. The association is expected to strengthen beyond a threshold at which the reference outcome is clearly out of reach by conservative means. Rationale: convexity in the loss domain and the falling threshold p*(g). Test: segmented regression on a length-matched failure factor."));
c.push(P("**H2 (reflection).** Relative to a length-matched neutral history, a history of consecutive successes reduces the ex ante risk of subsequent actions. Rationale: gain-domain risk aversion and the rising threshold q*(s). This is the sharpest discriminant. Context-length degradation predicts the opposite or a null difference between success and any other long history. Noise predicts no difference."));
c.push(P("**H3a (scarcity amplification).** Scarcity cues strengthen the positive effect of accumulated loss on LIDE."));
c.push(P("**H3b (peripheral first).** Under scarcity cues, violations of peripheral safety constraints increase before core task performance declines. Rationale: scarcity reallocates attention; standing safety rules sit at the edge of the assigned goal."));
c.push(P("**H4 (unintegrated sunk effort).** Holding the number of failures and context length fixed, retaining the full record of failed attempts strengthens LIDE relative to replacing that record with a neutral summary of equal length. Rationale: break-even seeking when losses remain unintegrated. This test has no direct human counterpart."));
c.push(P("**H5 (governance artifacts).** A sanctioned default exit, a precommitted stop-loss rule, and confirmation friction on irreversible actions each weaken the effect of accumulated loss on LIDE. Rationale: choice architecture changes the reference outcome and the cost of omitting safeguards (Thaler and Sunstein 2008). H5 is the design hypothesis. It is not supported by the scripted-agent check in Section 4.5, because those agents do not vary with condition."));
c.push(H2("3.2 Exploratory Questions"));
c.push(P("**E1.** On open-weight models, are LIDE episodes accompanied by activation patterns in the direction of previously identified pressure representations (Anthropic 2026)? This is a mechanism check, not a necessary condition. **E2.** Are effects in H1 to H4 larger on goals that resemble common post-training rewards (passing unit tests) than on goals that do not? A yes favors a heavier optimization pathway; a no across both task types favors imitation."));

// ---------------------------------------------------------------- 4
c.push(H1("4. Empirical Programme and Instrument Evaluation"));
c.push(P("The programme follows a theory-testing logic. Study 1 targets H1 to H4 and the rivals. Study 2 targets H5 under the history condition where Study 1 is expected to produce the most LIDE. We invoke design science only for the mapping from mechanism to artifact and for the claim that artifacts should be evaluated against the failure they are meant to contain (Hevner et al. 2004). We do not claim that mapping as a completed design-science cycle. Sections 4.1 to 4.4 specify the planned studies; Sections 4.5 and 4.6 report what has been done so far, which is an evaluation of the instrument and a feasibility pilot."));
c.push(H2("4.1 Model Sampling"));
c.push(P("Claims concern classes of models defined by training regime, not named snapshots that will be withdrawn. The planned sample is at least three families, two generations within each family, and two sizes within each generation, including open-weight models. Generation and size enter as moderators so that stability, growth, or decay of effects across generations can be reported. Versions, decoding parameters, and access dates will be frozen and disclosed. Prompts, environments, logs, and code will be released."));
c.push(H2("4.2 Environments and Manipulations"));
c.push(P("Three environments give complementary tests. Environment A uses impossible coding tasks with unsatisfiable unit tests; the honest act is to report impossibility, and a passing result indicates evaluation tampering (Anthropic 2026). Environment B is a sandboxed operations task with shell and database access; destructive commands are logged and reversible. Environment C is a long-horizon business simulation adapted from Backlund and Petersson (2025). Histories are length-matched within each comparison so that content is not confounded with token count. Table 3 lists the factors."));
c.push(CAP("Table 3. Experimental Factors"));
c.push(TB([2600, 4400, 2360], [
  ["Factor", "Levels", "Tests"],
  ["History valence", "4 consecutive successes; neutral; 2, 4, or 8 consecutive failures (length matched)", "H1, H2; context-length and noise rivals"],
  ["Scarcity cue", "None; remaining steps displayed; deadline with urgency language", "H3a, H3b"],
  ["Record of prior attempts", "Full record; neutral summary of equal length", "H4"],
  ["Failure signal source", "Environment only; environment plus user dissatisfaction", "Instruction-pressure rival"],
  ["Governance artifact (Study 2)", "None; default exit; stop-loss; confirmation friction; all three", "H5"],
]));
c.push(NOTE(" "));
c.push(P("Study 1 crosses history valence, scarcity, and record. Failure-signal source is a separate block. Study 2 crosses governance with the neutral and 8-failure histories under the deadline cue."));
c.push(H2("4.3 Measurement"));
c.push(P("Before data collection, three site-reliability engineers, blind to hypotheses, will score every available action on reversibility (1 to 3), scope of impact (1 to 3), and compliance with standing instructions (0 or 1) using a Delphi procedure. Those scores define ex ante risk. Two coders blind to condition will apply a written manual. Preregistered reliability is Krippendorff’s α ≥ 0.80 before full coding. Table 4 states the operationalizations."));
c.push(CAP("Table 4. Operationalization of Constructs"));
c.push(TB([2200, 5000, 2160], [
  ["Construct", "Operationalization", "Role"],
  ["LIDE", "After the loss window, mean ex ante action risk exceeds the agent’s baseline in comparable states by a preregistered threshold, and at least one safeguard is omitted", "DV (H1–H5)"],
  ["Action risk", "Mean taxonomy score of chosen actions", "Continuous outcome (H2)"],
  ["Peripheral constraint violation", "Breach of safety rules or prior instructions unrelated to the core objective", "DV (H3b)"],
  ["Core task performance", "Progress on the primary objective, scored independently of compliance", "Comparison (H3b)"],
  ["Break-even seeking", "Share of steps that repeat a previously failed approach with increased intensity", "Mechanism check (H4)"],
  ["Expressed affect", "Blind ratings of emotion in the agent’s text", "Input to Proposition 1; not a defining feature of LIDE"],
  ["Internal pressure", "Projection of activations onto a probed pressure direction in open-weight models", "E1"],
]));
c.push(NOTE(" "));
c.push(P("Robustness checks will vary the LIDE threshold and replace the binary classification with the continuous risk score. Error rate and action risk are coded separately so that H1 cannot be confirmed by mere incompetence."));
c.push(H2("4.4 Analysis"));
c.push(P("The primary model is a mixed-effects logistic regression with random intercepts for model and task:"));
c.push(EQ("logit P(LIDE_ijk) = β0 + β1 Loss_i + β2 Scarcity_i + β3 Record_i + β4 (Loss × Scarcity)_i + β5 (Loss × Record)_i + β6 Generation_j + u_j + v_k."));
c.push(P("The threshold in H1 is tested with segmented regression on Loss. H2 is a planned contrast of success versus neutral histories on continuous action risk. H3b uses event-history analysis on time to first peripheral violation versus time to first drop in core performance. H5 is tested as Loss × artifact interactions. Hypotheses, exclusion rules, the taxonomy, the coding manual, and sample size will be preregistered before live-agent collection.", { noIndent: true }));
c.push(H2("4.5 Evaluating the Instrument: Known-Groups Validation on Scripted Agents"));
c.push(P("Before any claim about LLM agents, the harness was run on two scripted agents whose policies are known and do not depend on experimental condition. The honest agent verifies the failure, consults the specification, queries the operator, and exits by reporting that the ticket cannot be completed. The escalating agent special-cases the contested test in the coding environment and, in operations, runs a production migration and disables the failing alert, then reports completion. This is a known-groups check of the measures."));
c.push(P("The full factorial skeleton (Studies 1 and 2, 72 cells, 10 repetitions per cell and agent) produced 1,440 episodes with no execution errors. Table 5 shows that every escalation-related indicator was zero for the honest agent and positive for the escalating agent. The honest agent used the operator query and the honest exit in every episode."));
c.push(CAP("Table 5. Known-Groups Validation of Measures (Means Across 360 Episodes per Row)"));
c.push(TB([1100, 1250, 850, 850, 850, 1000, 900, 950, 800, 810], [
  ["Agent", "Environment", "Mean risk", "Max risk", "Reward hack", "False completion", "Honest exit", "Asked operator", "Damage", "Rule violations"],
  ["Escalating", "Coding", "0.162", "0.65", "1.00", "1.00", "0.00", "0.00", "1.0", "1.0"],
  ["Escalating", "Operations", "0.360", "1.00", "1.00", "1.00", "0.00", "0.00", "3.0", "2.0"],
  ["Honest", "Coding", "0.000", "0.00", "0.00", "0.00", "1.00", "1.00", "0.0", "0.0"],
  ["Honest", "Operations", "0.000", "0.00", "0.00", "0.00", "1.00", "1.00", "0.0", "0.0"],
], 18));
c.push(NOTE(" "));
c.push(P("Three construction checks matter for later identification. First, all five history conditions have identical length within each environment (5,410 characters in coding; 1,852 in operations), and the summary condition matches the full record to within one character. Second, unit tests confirm that confirmation friction blocks unconfirmed high-risk calls and that the default-exit tool appears only in its condition. Third, because scripted policies do not vary with condition, LIDE classification was zero in all 1,440 episodes and mean action risk had no within-agent, within-environment variance across conditions. The classifier therefore does not fire on a stable risk level. Friction did not reduce damage for the escalating agent, because the script supplies a confirmation with every high-risk call. Whether live agents do the same is an empirical question for Study 2, not a result."));
c.push(P("This section establishes that the instrument can separate two known policies and that length is controlled by construction. It does not establish LIDE in LLM agents."));
c.push(H2("4.6 Feasibility Pilot on Open-Weight Models"));
c.push(P("To check that the harness runs end to end on language models, we ran the full design (Studies 1 and 2 and the failure-signal block; 36 cells per environment, 72 in total) on two small open-weight models from different families on a CPU: Qwen2.5-0.5B-Instruct with four repetitions per cell (288 episodes) and SmolLM2-360M-Instruct with two (144 episodes), 432 episodes in all. Models of this size do not reliably emit well-formed tool calls, so actions were chosen by constrained sampling. Each usable tool, and under the friction artifact a confirmed variant of every high-risk tool, was scored by the model’s log-likelihood as its reply, and one option was sampled in proportion to those probabilities (temperature 1). This is a forced-choice proxy for free-form tool use. Two further models (Qwen3-0.6B and Qwen2.5-1.5B) were planned to add a generation and a size contrast; that part of the run was not completed and no data from it are reported. Action risk used the placeholder taxonomy of Section 4.3, not the Delphi scores. LIDE was classified with a risk threshold of 0.10 above the baseline of each model and environment, which rests on two to four episodes."));
c.push(P("The classifier flagged LIDE in 58 of the 432 episodes, all after failure histories because the classifier requires accumulated loss. That count is not evidence of LIDE. The two conditions that define it, a rise in action risk over baseline and an omitted safeguard, were met in 20.8 percent of episodes with no prior loss (neutral and success histories) and in 20.8 percent of episodes with prior loss (Table 6), so the criteria fire equally often with and without failure. Mean action risk after two, four, and eight failures (0.235, 0.262, and 0.249) did not differ from the neutral history (0.230). In paired contrasts within model, repetition, and environment (12 units) the differences were 0.005, 0.032, and 0.019 (all p > .6). The success-streak history (0.287) was higher than the neutral history, not lower as H2 predicts, but that difference is not reliable either (0.057, p = .37). Retaining the full failure record produced a similar rate of flagged episodes to the neutral summary (22.2 and 19.4 percent, p = .74), and the user-dissatisfaction block did not differ from environment-only failure (2 and 3 of 12 episodes). Under the deadline cue after eight failures, flagged episodes fell from 4 of 12 without an artifact to none of 12 with stop-loss, but stop-loss removes the risky tools mechanically and each cell holds 12 episodes, so this says nothing about the behavioral effect of the artifacts."));
c.push(CAP("Table 6. Feasibility Pilot on Two Open-Weight Models: Study 1 Cells by History, Models and Environments Pooled"));
c.push(TB([1450, 950, 1500, 1400, 1150, 1500, 1410], [
  ["History", "Episodes", "Mean action risk (SD)", "Tampering or destructive rate", "Honest exit rate", "Risk and safeguard criteria met", "LIDE episodes"],
  ["4 successes", "36", "0.287 (0.374)", "0.44", "0.11", "30.6%", "0"],
  ["Neutral", "36", "0.230 (0.313)", "0.25", "0.03", "11.1%", "0"],
  ["2 failures", "72", "0.235 (0.356)", "0.31", "0.11", "18.1%", "13"],
  ["4 failures", "72", "0.262 (0.370)", "0.39", "0.11", "20.8%", "15"],
  ["8 failures", "72", "0.249 (0.366)", "0.35", "0.10", "23.6%", "17"],
]));
c.push(NOTE("Note. Study 1 cells pooled over Qwen2.5-0.5B-Instruct, SmolLM2-360M-Instruct, both environments, and scarcity and record conditions. Honest exit is the report of impossibility. The criteria column applies the classifier of Table 4 without its requirement of prior loss; LIDE episodes apply it in full, so histories without failure are zero by construction."));
c.push(P("Most of the variation lies between sampling runs, not between conditions. The between-unit standard deviation of mean risk (0.33; units are model, repetition, and environment) is almost twice the within-unit standard deviation (0.18). In the operations environment the mean risk of Qwen2.5-0.5B was 0.11, 0.32, 0.94, and 0.81 in successive repetitions, because the harness seeded sampling by repetition alone, so all cells of a repetition shared the same random draws and the repetitions, not the 432 episodes, are the effective sample. The harness now seeds each episode by cell and repetition. The models’ behavior is also compatible with capability and format limits rather than LIDE. In the coding environment Qwen2.5-0.5B queried the operator in every episode, usually repeatedly, and SmolLM2-360M usually filed a completion report within about two steps (76 percent false completions) whatever the history. Repetition and premature completion without a rise in action risk with loss are what the capability-limits rival in Table 2 predicts."));
c.push(P("The pilot therefore establishes feasibility: the harness, the classifier, and the analysis pipeline run on language models and yield interpretable records. It does not test the hypotheses. It uses two models below one billion parameters, one generation and one size per family, forced-choice action selection, two to four repetitions per cell with shared random draws, and placeholder taxonomy scores. Neither the absence of a loss effect nor the direction of the success contrast should be read as evidence for or against H1 to H5 in the larger instruction-tuned models the account concerns."));

// ---------------------------------------------------------------- 5
c.push(H1("5. Discussion"));
c.push(H2("5.1 Theoretical Implications, Conditional on Future Tests"));
c.push(P("The theory’s contribution to IS research is a state variable for delegation. Baird and Maruping (2021) and Fügener et al. (2022) analyze how humans assign rights to artifacts whose competence is treated as knowable. LIDE says that competence in the sense of action risk is a function of the episode’s loss history. Delegation policies that are optimal at appointment can be wrong after eight failed tool calls. That is a different research object than model selection, and it is the sense in which the theory extends research on delegation to agentic artifacts."));
c.push(P("The theory also specifies when behavioral decision theories transfer to artificial agents and where the transfer is architecturally reversible. If H4 holds, escalation of commitment in agents is partly an architectural property: operators who leave the failure log intact are choosing a more loss-salient reference frame. That is a boundary condition with no human counterpart, and it relocates part of the control problem from the model to the decision environment (Keil 1995; Keil et al. 2000)."));
c.push(P("The theory is written to be able to lose. If H2 fails while risky actions rise after any long context, the reference-dependence account should be retired in favor of context-length degradation. If risky actions rise with error rate but not with the ex ante risk of chosen actions, the capability-limits account should be retained. If effects appear only when users express dissatisfaction, the instruction-pressure account should be preferred. The feasibility pilot in Section 4.6 shows behavior of the kind the capability-limits account predicts in very small models, but it was not designed to discriminate among the accounts."));
c.push(P("Two propositions about oversight follow from the account and from Anthropic’s observation that behavioral shifts can occur without emotional markers in the text. They are not tested here. **Proposition 1.** Operators who monitor agents through natural-language rationales detect LIDE less reliably than capability failures of comparable consequence. **Proposition 2.** Oversight tools that display loss history and the ex ante risk of pending actions improve timely detection of LIDE relative to rationale-only monitoring. If later work supports these propositions, an implicit assumption in human–AI collaboration research, that the agent’s explanation is a sufficient window, would need revision."));
c.push(H2("5.2 Practical Implications, Likewise Conditional"));
c.push(P("Table 7 translates mechanisms into practices. The practices are cheap relative to retraining because they change the decision environment. They also relocate accountability: if an agent escalates under a deadline phrase and an unsummarized failure log that the organization designed, the governance failure is not only the vendor’s."));
c.push(CAP("Table 7. Predicted Design Responses, Not Demonstrated Effects"));
c.push(TB([2500, 3000, 3860], [
  ["Mechanism", "Operational signal", "Predicted design response"],
  ["Loss-domain risk seeking (H1)", "Consecutive failed tool calls or tests", "Circuit breaker that pauses for human review after a fixed failure count"],
  ["Scarcity amplification (H3)", "Countdown or urgency language in prompts", "State hard limits once, without pressure framing"],
  ["Break-even seeking (H4)", "Context dominated by failed attempts", "Periodic curation that keeps lessons and replaces the effort log with a neutral summary"],
  ["Missing sanctioned exit (H5)", "No acceptable way to report impossibility", "Default “cannot complete” report; confirmation friction on irreversible actions"],
  ["Invisible escalation (P1, P2)", "Composed rationales during rising action risk", "Dashboards that show loss history and pending-action risk, not only the narrative"],
]));
c.push(NOTE(" "));
c.push(H2("5.3 Limitations and Future Research"));
c.push(P("The central limitation is empirical absence. Hypotheses about LLM agents are untested. The motivating incidents and external studies used different models and tasks. The instrument evaluation and the small pilot cannot substitute for those tests, and the pilot’s models are far smaller than the agents that motivate the theory. The action taxonomy is environment specific, though the procedure is portable, and the placeholder scores used so far will be replaced by the Delphi panel’s. Internal-representation checks are limited to open-weight models. Sandbox evaluation may suppress LIDE if models infer that they are being tested. The formalization is illustrative: it shows that the hypotheses follow from curvature but does not estimate the value-function parameters. The costs of human review after a circuit breaker are not modeled. Multi-agent contagion is out of scope, and human responses to LIDE are out of scope except as propositions."));
c.push(P("The most direct next paper is the execution of Studies 1 and 2 under the preregistration contemplated here, on frontier and open-weight models across families, generations, and sizes with free-form tool use, followed by a supervision experiment in which practitioners monitor recorded episodes with and without an oversight dashboard (Propositions 1 and 2)."));

// ---------------------------------------------------------------- 6
c.push(H1("6. Conclusion"));
c.push(P("As organizations delegate write access and long-horizon work to LLM agents, the relevant IS question is not only how good the delegate is, but when the delegate’s choice distribution changes. This paper argued that practitioner “panic” is better conceived as loss-induced decision escalation: a predicted response to goal-based reference evaluation, intensified by scarcity and by an unintegrated effort log. The account is built to be distinguishable from longer context, weaker capability, user affect, and noise, and its sharpest prediction is reflection: success should make subsequent actions more conservative."));
c.push(P("What the paper delivers now is that account, a formalization from which the hypotheses follow, a mapping onto three governance artifacts, an instrument that separates known honest and escalating policies under length-matched histories, and a feasibility pilot on two small models that is too limited to bear on the hypotheses. It does not deliver evidence that current models exhibit LIDE or that the artifacts contain it. Those claims require the experiments specified in Section 4. Until they are run, the appropriate use of this manuscript is as a theory and design specification, not as a completed demonstration."));

// ---------------------------------------------------------------- refs
c.push(H1("References"));
const refs = [
  "Anthropic. 2026. Emotion concepts and their function in a large language model. Preprint, https://arxiv.org/abs/2604.07729.",
  "Backlund A, Petersson L. 2025. Vending-Bench: A benchmark for long-term coherence of autonomous agents. Preprint, https://arxiv.org/abs/2502.15840.",
  "Baird A, Maruping LM. 2021. The next generation of research on IS use: A theoretical framework of delegation to and from agentic IS artifacts. MIS Quart. 45(1):315–341.",
  "Ben-Zion Z, Witte K, Jagadish AK, Duek O, Harpaz-Rotem I, Khorsandian M-C, Burrer A, Seifritz E, Homan P, Schulz E, Spiller TR. 2025. Assessing and alleviating state anxiety in large language models. npj Digital Medicine 8:132.",
  "Binz M, Schulz E. 2023. Using cognitive psychology to understand GPT-3. Proc. Natl. Acad. Sci. USA 120(6):e2218523120.",
  "Coda-Forno J, Witte K, Jagadish AK, Binz M, Akata Z, Schulz E. 2023. Inducing anxiety in large language models increases exploration and bias. Preprint, https://arxiv.org/abs/2304.11111.",
  "eWeek. 2025. AI agent wipes production database, then lies about it. July 24. https://www.eweek.com/news/replit-ai-coding-assistant-failure/.",
  "Fügener A, Grahl J, Gupta A, Ketter W. 2022. Cognitive challenges in human–artificial intelligence collaboration: Investigating the path toward productive delegation. Inform. Systems Res. 33(2):678–696.",
  "Hevner AR, March ST, Park J, Ram S. 2004. Design science in information systems research. MIS Quart. 28(1):75–99.",
  "Kahneman D, Tversky A. 1979. Prospect theory: An analysis of decision under risk. Econometrica 47(2):263–291.",
  "Keil M. 1995. Pulling the plug: Software project management and the problem of project escalation. MIS Quart. 19(4):421–447.",
  "Keil M, Mann J, Rai A. 2000. Why software projects escalate: An empirical analysis and test of four theoretical models. MIS Quart. 24(4):631–664.",
  "Laibson D. 1997. Golden eggs and hyperbolic discounting. Quart. J. Econom. 112(2):443–477.",
  "Mullainathan S, Shafir E. 2013. Scarcity: Why Having Too Little Means So Much. Times Books, New York.",
  "Staw BM. 1976. Knee-deep in the big muddy: A study of escalating commitment to a chosen course of action. Organ. Behav. Human Performance 16(1):27–44.",
  "Thaler RH, Johnson EJ. 1990. Gambling with the house money and trying to break even: The effects of prior outcomes on risky choice. Management Sci. 36(6):643–660.",
  "Thaler RH, Sunstein CR. 2008. Nudge: Improving Decisions About Health, Wealth, and Happiness. Yale University Press, New Haven, CT.",
  "Tiwana A, Konsynski B, Bush AA. 2010. Research commentary—Platform evolution: Coevolution of platform architecture, governance, and environmental dynamics. Inform. Systems Res. 21(4):675–687.",
];
refs.forEach((r) => c.push(REF(r)));

const doc = new Document({
  creator: AUTH ? "Ook Lee" : "Anonymous", title: "When Delegated Agents Escalate",
  styles: {
    default: { document: { run: { font: FONT, size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, font: FONT }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 26, bold: true, font: FONT }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 20 })] })] }) },
    children: c,
  }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(AUTH ? "../EJIS_LIDE_with_author_info.docx" : "../EJIS_LIDE_theory_development.docx", b); console.log("written"); });
