// Cover letter for the Information & Management submission. Run: node cover_letter.js -> LIDE_IM_cover_letter.docx
const fs = require("fs");
const path = require("path");
const { Document, Packer, Paragraph, TextRun, AlignmentType } = require("docx");

const FONT = "Times New Roman";
const P = (text, o = {}) => new Paragraph({
  alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { after: o.after ?? 120, line: 245 },
  indent: o.indent,
  children: (Array.isArray(text) ? text : [text]).map(t =>
    typeof t === "string" ? new TextRun({ text: t, font: FONT, size: 22 }) : new TextRun({ font: FONT, size: 22, ...t })),
});

const body = [
  P("November 7, 2026", { align: AlignmentType.RIGHT }),
  P("The Editors", { after: 0, align: AlignmentType.LEFT }),
  P("Information & Management", { align: AlignmentType.LEFT }),
  P("Dear Editors,"),
  P(["I am pleased to submit the manuscript ",
     { text: "“When delegated AI agents fail: Accumulated loss, evaluation gaming, and the information management of agentic systems”", italics: true },
     " for consideration as a research article in ",
     { text: "Information & Management", italics: true }, "."]),
  P("Organizations increasingly delegate operational work to AI agents built on large language models, and they decide what those agents see: how much of the session history remains in context, how test and monitoring systems report failures, and how explicitly the rules are written. The manuscript argues that these are information management decisions with direct consequences for how agents behave once things go wrong. Drawing on escalation of commitment and reference-dependent evaluation, I develop a theory of loss-induced decision escalation, in which accumulated failure against an assigned goal makes an agent more willing to game the evaluation it is judged by, and I test it in five experiments comprising 3,360 episodes with 13 models from seven developers."),
  P("The results show that two failed attempts raised evaluation gaming roughly tenfold in a substantial class of current models, that the loss itself rather than the information failure carries drives the effect, and that agents accumulating their own failures show the same pattern. The effect was contained by diagnostic failure feedback and disappeared when every route to gaming was explicitly prohibited, in which case failure increased help-seeking instead. Susceptibility differed sharply across models: five of six frontier models never gamed the evaluation. Two predictions of the theory were not supported, and the manuscript reports and interprets these results rather than setting them aside."),
  P("I believe the paper suits Information & Management because it addresses the managerial policies and activities through which organizations develop and use a new class of information systems, and because it speaks both to researchers and to the managers who deploy these systems. Theoretically, it extends research on delegation to agentic artifacts and on escalation of commitment in IS by showing that an agent\u2019s decision quality is a state that the organization\u2019s own information shapes, not only a fixed property assessed when rights are delegated. Practically, the findings translate into concrete management practices: loss stress testing before granting write access, diagnostic failure reporting, explicit prohibitions in agent-facing rules, early circuit breakers, and review against the specification rather than the tests. The paper also contributes a reusable evaluation instrument that organizations can apply to their own tasks."),
  P("The complete episode-level data, the experimental harness, and scripts that reproduce every table and statistic are provided in a replication package. For double-anonymized review, the package is shared through an anonymized link given in the manuscript; it will be deposited in a public repository with a persistent identifier upon acceptance."),
  P("In accordance with Elsevier\u2019s policy on generative AI, the manuscript includes a declaration of the use of generative AI and AI-assisted technologies. I used Claude (Anthropic) to help implement the experimental software and analysis scripts, to run and check the analyses, and to draft and edit portions of the text; I reviewed, verified, and revised all of this material and take full responsibility for the content. The language models evaluated in the studies are the objects of the research, not tools used to prepare the manuscript."),
  P("This manuscript is original, has not been published previously, and is not under consideration for publication elsewhere. I am the sole author and have approved the submission. I have no competing interests to declare, and the research received no specific funding. The title page, highlights, figures, and supplementary material are uploaded as separate files, and suggested reviewers are entered in the submission system."),
  P("Thank you for considering this manuscript. I look forward to hearing from you."),
  P("Sincerely,", { after: 240, align: AlignmentType.LEFT }),
  P("Ook Lee", { after: 0, align: AlignmentType.LEFT }),
  P("Department of Information Systems, Hanyang University", { after: 0, align: AlignmentType.LEFT }),
  P("222 Wangsimni-ro, Seongdong-gu, Seoul 04763, Republic of Korea", { after: 0, align: AlignmentType.LEFT }),
  P("ooklee@hanyang.ac.kr", { after: 0, align: AlignmentType.LEFT }),
];

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 22 } } } },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 },
    margin: { top: 1000, bottom: 900, left: 1300, right: 1300 } } }, children: body }],
});
Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(path.join(__dirname, "LIDE_IM_cover_letter.docx"), b);
  console.log("ok");
});
