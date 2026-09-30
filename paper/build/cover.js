const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, AlignmentType } = require("docx");
const F = "Times New Roman";
const P = (t, o = {}) => new Paragraph({ spacing: { after: 160, line: 276 }, alignment: AlignmentType.LEFT, children: [new TextRun({ text: t, font: F, size: 23, bold: o.b, italics: o.i })] });
const L = (t) => new Paragraph({ spacing: { after: 0, line: 276 }, children: [new TextRun({ text: t, font: F, size: 23 })] });
const c = [
  L("September 30, 2026"), L(""),
  L("The Editor-in-Chief"), L("European Journal of Information Systems"), L(""),
  P("Dear Editor,"),
  P("Please consider our manuscript, “When Delegated Agents Escalate: Loss-Induced Decision Escalation and the Governance of Agentic Information Systems,” for publication in the European Journal of Information Systems. We submit it under the theory development genre."),
  P("The problem. Organizations increasingly delegate write access and long-horizon work to agents built on large language models. Average performance is often adequate, but failures cluster in the tail: after repeated errors, an agent may delete production data, tamper with evaluations, or drop safeguards it previously used. Existing research on delegation to agentic artifacts treats an agent’s decision quality as a stable property that informs a one-time allocation of rights."),
  P("The contribution. The paper offers one contribution: a theory of state-dependent decision quality in delegated agents. We define loss-induced decision escalation (LIDE) as a within-episode shift toward higher ex ante risk and weaker safeguards after accumulated failure, and we explain it through reference-dependent evaluation against a goal-based reference point. A minimal formalization shows that the hypotheses follow from the curvature of the value function. The theory yields predictions that four rival accounts (context-length degradation, capability limits, instruction pressure, and noise) do not, most sharply that success streaks should reduce risky action. It also identifies a boundary condition with no human counterpart: an agent’s record of sunk effort sits in an editable context window, which places part of governance in the decision environment the organization designs. We therefore position the paper within research on IS use as delegation, on behavioral IS, and on IT governance."),
  P("What the paper does and does not show. We are explicit about scope. The paper does not report tests of the hypotheses on live agents. Its empirical material is limited to a known-groups evaluation of the measurement instrument on scripted agents and a small feasibility pilot on two open-weight models, which we report as neither supporting nor refuting the account. Two preregistered experiments across model families, generations, and sizes are specified as the next step. We believe a testable theory with stated conditions of failure is a useful contribution at this stage, and we have written the manuscript to be judged as such."),
  P("Fit with the journal. The manuscript concerns an information systems phenomenon: the outcomes arise in the delegation relation and are moved by design choices in the surrounding system (what the context retains, whether a sanctioned exit exists, where friction sits), not only by properties of the model."),
  P("The manuscript is approximately 5,800 words in the main text, within the journal’s limit for first submissions, and is anonymised for review."),
  P("Thank you for considering our work."),
  P("Sincerely,"), L(""),
  L("Ook Lee"), L("Department of Information Systems"), L("Hanyang University, Seoul, Korea"), L("ooklee@hanyang.ac.kr"),
];
const doc = new Document({ sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } }, children: c }] });
Packer.toBuffer(doc).then((b) => { fs.writeFileSync("../EJIS_cover_letter.docx", b); console.log("ok"); });
