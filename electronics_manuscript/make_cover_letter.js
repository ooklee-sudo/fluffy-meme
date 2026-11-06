const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, AlignmentType, LevelFormat } = require('docx');

const FONT = 'Times New Roman';
// **bold** and *italic* segments -> runs
function runs(text) {
  return text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/).filter(Boolean).map(s =>
    s.startsWith('**') ? new TextRun({ text: s.slice(2, -2), bold: true })
      : s.startsWith('*') ? new TextRun({ text: s.slice(1, -1), italics: true }) : new TextRun(s));
}
const J = AlignmentType.JUSTIFIED;
const para = (t, opts = {}) => new Paragraph({ children: runs(t), spacing: { after: 160 }, alignment: J, ...opts });
const lines = (arr, after) => arr.map((t, i) => new Paragraph({ children: runs(t), keepNext: i < arr.length - 1, spacing: { after: i === arr.length - 1 ? after : 0 } }));
const item = (ref, t, last) => new Paragraph({ children: runs(t), numbering: { reference: ref, level: 0 }, spacing: { after: last ? 160 : 80 }, alignment: J });

const results = [
  '**A scheduling rule.** The optimal update interval grows only with the square root of the update cost, so a tenfold rise in cost justifies an interval about three times longer. Update mechanisms that forget less should be run more often, not less.',
  '**When to wait.** Solving the scheduling problem numerically shows that the optimal scheduler waits while a drift event is likely to arrive soon and updates when it is not. When drift arrives in clusters, this cuts cost by 9–11% across five settings of update cost and drift rate, and adjusting in the wrong direction costs more than ignoring timing altogether.',
  '**Testable conditions.** The optimal policy escalates from knowledge editing to fine-tuning to full retraining under conditions that can be measured for each mechanism. A case study on the public Pythia-70M model shows how: retrieval absorbs drift in proportion to its coverage (61% at 60% coverage), and an unreplayed low-rank adapter fails the conditions by doing worse than no update at all.',
];
const confirms = [
  'the manuscript is original, has not been published previously, and is not under consideration for publication elsewhere;',
  'both authors have approved the submitted version and agree to its submission;',
  'the research received no external funding, and the authors declare no conflicts of interest;',
  'the data and code supporting the case study are available from the corresponding author upon reasonable request;',
  '[Generative AI: state the tool and purpose if used beyond grammar and formatting, or delete this line.]',
];

const children = [
  new Paragraph({ children: [new TextRun('6 November 2026')], spacing: { after: 160 } }),
  ...lines(['Editorial Office', '*Electronics*', 'MDPI, Basel, Switzerland'], 160),
  para('Dear Editors of *Electronics*,'),
  para('On behalf of my co-author, Hannah Park, I am pleased to submit our manuscript “Mathematical Modeling of Large Language Model Maintenance: A Stochastic Optimal-Control Framework for Retraining Scheduling, Knowledge Retention, and Alignment Preservation” for consideration as an Article in the Artificial Intelligence section of *Electronics*.'),
  para('Deployed large language models (LLMs) lose accuracy as the world drifts away from their training data, yet most teams still update them on a fixed calendar. The manuscript treats a deployed LLM as a deteriorating system and uses condition-based maintenance theory to decide when, how, and how much to update it, accounting jointly for staleness, update-induced forgetting, and compute cost.'),
  para('Three results make the work useful to practitioners:', { spacing: { after: 120 }, keepNext: true }),
  ...results.map((t, i) => item('numbers', t, i === results.length - 1)),
  para('The manuscript states openly which building blocks are classical, such as the economic-order-quantity form and monotone-policy arguments, and sets out what is new at the end of the Introduction.'),
  para('The work fits *Electronics* because it addresses an engineering problem in operating AI systems and turns the analysis into design rules for LLM operations: update schedulers, release gates on forgetting, and monitoring (Section 9). The numerical results are reproducible on a standard CPU, where each scheduling problem solves in seconds.'),
  para('We confirm that:', { spacing: { after: 120 }, keepNext: true }),
  ...confirms.map((t, i) => item('bullets', t, i === confirms.length - 1)),
  para('We would be glad to suggest potential reviewers if that would help the editorial process. Thank you for considering this manuscript; we look forward to hearing from you.'),
  new Paragraph({ children: [new TextRun('Sincerely,')], spacing: { after: 240 } }),
  ...lines(['Ook Lee (corresponding author), on behalf of both authors (Ook Lee and Hannah Park)', 'Department of Information Systems, Hanyang University', 'Seoul 04763, Republic of Korea; ooklee@hanyang.ac.kr'], 0),
];

const lvl = (format, text) => [{ level: 0, format, text, alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 567, hanging: 340 } } } }];
const doc = new Document({
  creator: 'Ook Lee and Hannah Park',
  title: 'Cover Letter',
  styles: { default: { document: { run: { font: FONT, size: 22 } } } },
  numbering: { config: [
    { reference: 'bullets', levels: lvl(LevelFormat.BULLET, '•') },
    { reference: 'numbers', levels: lvl(LevelFormat.DECIMAL, '%1.') },
  ] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1020, bottom: 1020, left: 1304, right: 1304 } } }, children }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(process.argv[2], b); console.log('ok'); });
