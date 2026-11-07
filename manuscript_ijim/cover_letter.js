// Cover letter for the IJIM submission. Run: node cover_letter.js -> LIDE_IJIM_cover_letter.docx
const fs = require("fs");
const path = require("path");
const { Document, Packer, Paragraph, TextRun, AlignmentType } = require("docx");

const FONT = "Times New Roman";
const P = (text, o = {}) => new Paragraph({
  alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { after: o.after ?? 160, line: 264 },
  indent: o.indent,
  children: (Array.isArray(text) ? text : [text]).map(t =>
    typeof t === "string" ? new TextRun({ text: t, font: FONT, size: 23 }) : new TextRun({ font: FONT, size: 23, ...t })),
});

const body = [
  P("November 7, 2026", { align: AlignmentType.RIGHT }),
  P("The Editors", { after: 0, align: AlignmentType.LEFT }),
  P("International Journal of Information Management", { align: AlignmentType.LEFT }),
  P("Dear Editors,"),
  P(["I am pleased to submit the manuscript ",
     { text: "“When delegated AI agents fail: Accumulated loss, evaluation gaming, and the information management of agentic systems”", italics: true },
     " for consideration as a Research Article in the ",
     { text: "International Journal of Information Management", italics: true }, "."]),
  P("Organizations increasingly delegate operational work to AI agents built on large language models, and they decide what those agents see: how much of the session history remains in context, how test and monitoring systems report failures, and how explicitly the rules are written. The manuscript argues that these are information management decisions with direct consequences for how agents behave once things go wrong. Drawing on escalation of commitment and reference-dependent evaluation, I develop a theory of loss-induced decision escalation, in which accumulated failure against an assigned goal makes an agent more willing to game the evaluation it is judged by, and I test it in five experiments comprising 3,360 episodes with 13 models from seven developers."),
  P("The results show that two failed attempts raised evaluation gaming roughly tenfold in a substantial class of current models, that the loss itself rather than the information failure carries drives the effect, and that agents accumulating their own failures show the same pattern. The effect was contained by diagnostic failure feedback and disappeared when every route to gaming was explicitly prohibited, in which case failure increased help-seeking instead. Susceptibility differed sharply across models: five of six frontier models never gamed the evaluation. Two predictions of the theory were not supported, and the manuscript reports and interprets these results rather than setting them aside."),
  P("I believe the paper fits the journal’s aims in three respects. First, it extends information systems theory on delegation to agentic artifacts by showing that an agent’s decision quality is a state that the organization’s own information shapes, not only a fixed property assessed at the time of delegation. Second, it addresses the governance of an emerging technology with evidence that translates into concrete information management practices: loss stress testing before granting write access, diagnostic failure reporting, explicit prohibitions in agent-facing rules, early circuit breakers, and specification-based review. Third, it contributes a reusable evaluation instrument that organizations and researchers can apply to their own tasks."),
  P("In line with the journal’s Open Data policy, the complete episode-level data, the experimental harness, and scripts that reproduce every table and statistic are provided in a replication package. For double-anonymized review, the package is shared through an anonymized link, which is given in the manuscript and in the data availability statement; it will be deposited with a persistent identifier upon acceptance."),
  P("As required by the journal’s policy, the manuscript includes a declaration of the use of generative AI and AI-assisted technologies. I used Claude (Anthropic) to help implement the experimental software and analysis scripts, to run and check the analyses, and to draft and edit portions of the text. I reviewed, verified, and revised all of this material and take full responsibility for the content. The language models evaluated in the studies are the objects of the research and were not used to prepare the manuscript."),
  P("This manuscript is original, has not been published previously, and is not under consideration for publication elsewhere. I am the sole author and have approved the submission. I have no competing interests to declare, and the research received no specific funding. The title page, highlights, figures, and supplementary material are uploaded as separate files, and suggested reviewers are entered in the submission system."),
  P("Thank you for considering this manuscript. I look forward to hearing from you."),
  P("Sincerely,", { after: 360, align: AlignmentType.LEFT }),
  P("Ook Lee", { after: 0, align: AlignmentType.LEFT }),
  P("Department of Information Systems", { after: 0, align: AlignmentType.LEFT }),
  P("Hanyang University", { after: 0, align: AlignmentType.LEFT }),
  P("222 Wangsimni-ro, Seongdong-gu, Seoul 04763, Republic of Korea", { after: 0, align: AlignmentType.LEFT }),
  P("ooklee@hanyang.ac.kr", { after: 0, align: AlignmentType.LEFT }),
];

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 23 } } } },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 },
    margin: { top: 1300, bottom: 1200, left: 1440, right: 1440 } } }, children: body }],
});
Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(path.join(__dirname, "LIDE_IJIM_cover_letter.docx"), b);
  console.log("ok");
});
