const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, AlignmentType } = require("docx");
const F = "Times New Roman";
const P = (t, o = {}) => new Paragraph({ alignment: o.c ? AlignmentType.CENTER : AlignmentType.LEFT, spacing: { after: o.after ?? 160, line: 276 }, children: [new TextRun({ text: t, font: F, size: o.size || 24, bold: o.b, italics: o.i })] });
const doc = new Document({ sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } }, children: [
  P("Title page", { b: true, size: 26, after: 240 }),
  P("When Delegated Agents Escalate: Loss-Induced Decision Escalation and the Governance of Agentic Information Systems", { b: true, size: 28, after: 240 }),
  P("Author", { b: true, after: 60 }),
  P("Ook Lee", { after: 40 }),
  P("Department of Information Systems, Hanyang University, Seoul, Korea", { after: 40 }),
  P("E-mail: ooklee@hanyang.ac.kr", { after: 240 }),
  P("Corresponding author", { b: true, after: 60 }),
  P("Ook Lee, ooklee@hanyang.ac.kr", { after: 240 }),
  P("Article genre", { b: true, after: 60 }),
  P("Theory development", { after: 240 }),
  P("Keywords", { b: true, after: 60 }),
  P("agentic information systems; delegation; large language models; prospect theory; escalation of commitment; human oversight; IT governance", { after: 240 }),
] }] });
Packer.toBuffer(doc).then((b) => { fs.writeFileSync("../EJIS_title_page.docx", b); console.log("ok"); });
