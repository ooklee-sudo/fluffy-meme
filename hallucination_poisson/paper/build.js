const fs = require('fs');
const { d, P, H1, H2, run } = require('./lib');
const { Document, Packer, Paragraph, AlignmentType, Footer, PageNumber, TextRun } = d;
const { intro, related, model, cascade } = require('./theory');
const { method } = require('./method');
const { results } = require('./results');
const { discussion, conclusion, references } = require('./tail');

const title = 'Operational Readiness for LLM Hallucinations: A Counting-Process Capacity Model and Measured Evidence on Guardrail Cascades';
const abstract = [
  H1('Abstract'),
  P('Organisations that deploy large language models (LLMs) must decide how much human triage capacity to hold in reserve and how many automated guardrail layers to place in front of the model. Practice relies on two rules of thumb: staff for the average incident load, and stack guardrails whose combined benefit is computed under independence. We model critical hallucinations as a (possibly over-dispersed, non-homogeneous) counting process, size capacity at a quantile of the daily count, and treat the multiplicative guardrail formula as the independence special case of Fréchet-type bounds. We show analytically that over-dispersion inflates required capacity by roughly the square root of the dispersion index, that positive association between layers makes the independence formula a lower bound on residual risk, and that, because capacity is integer-valued, total cost is not unimodal in the number of layers; an earlier claim that three layers are structurally optimal does not follow from the cost model. We then evaluate the integrated pipeline on measured outputs of three open LLMs answering 900 SQuAD 2.0 questions through three executed guardrail layers (rules, an extractive-QA classifier, an LLM judge) with measured latency and failures, with user traffic simulated as a non-homogeneous arrival process. A single validated classifier cut required capacity by 80-95%; a routed judge added a modest, model-dependent gain at about triple the latency. The independence formula understated the share of hallucinations passing a two-layer cascade by a factor of 1.6-2.6 (2.7-4.6 with routing), a classifier with chance-level discrimination appeared beneficial only because it blocked almost everything, and with mild burstiness (daily-rate CV 0.3) a Poisson-sized capacity plan was exceeded on about 25% of days instead of 5%. Arrival times are simulated, models are small, and the task is extractive QA, so the numbers do not transfer to production; the method and its diagnostics do.'),
  new Paragraph({ children: [run('Keywords: ', { bold: true }), run('LLM operations, hallucination, guardrails, capacity planning, Poisson process, over-dispersion, design science')], spacing: { after: 200 } }),
];
const frontNote = new Paragraph({ children: [run('Working draft. Revised from an earlier analytical-only draft; see Section 3.4 for corrections. Code and data: hallucination_poisson/ in the accompanying repository.', { italics: true, size: 18 })], spacing: { after: 160 } });

const doc = new Document({
  creator: 'Author', title,
  styles: { default: { document: { run: { font: 'Times New Roman', size: 22 } } } },
  numbering: { config: [{ reference: 'bul', levels: [{ level: 0, format: d.LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: 'Times New Roman', size: 18 })] })] }) },
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: [run(title, { bold: true, size: 30 })] }),
      frontNote, ...abstract, ...intro, ...related, ...model, ...cascade, ...method, ...results, ...discussion, ...conclusion, ...references,
    ],
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync('../runs/LLM_Hallucination_Poisson_Framework_Revised.docx', b); console.log('written', b.length); });
