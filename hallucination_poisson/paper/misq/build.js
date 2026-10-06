const fs = require('fs');
const { d, P, PN, H1, run } = require('./lib');
const { Document, Packer, Paragraph, AlignmentType, Footer, PageNumber, TextRun, PageBreak } = d;
const { intro, related, model } = require('./s1');
const { method, results } = require('./s2');
const { findings2, sup } = require('./s3');
const { discussion, conclusion, appendix, REFS, appendixEnd } = require('./s4');
const S = require('../../runs/summary.json');
const R3 = ['qwen05', 'smol360', 'qwen15'];
const rg = (a, dd = 0) => { const lo = Math.min(...a).toFixed(dd), hi = Math.max(...a).toFixed(dd); return lo === hi ? lo : `${lo} to ${hi}`; };
const cfgk = (r, c) => S[r].sla500.configs.find(x => x.config === c);
const red = R3.map(r => 100 * (1 - cfgk(r, 'L2').k_star / cfgk(r, 'none').k_star));
const fb = R3.map(r => 100 * S[r].false_block_share_of_good.L2);
const none3 = R3.map(r => 100 * S[r].burst.poisson_checks.none.p_exceed_k_star_observed), none44 = R3.map(r => 100 * S[r].burst044.poisson_checks.none.p_exceed_k_star_observed);

const title = 'Operational Readiness for LLM Hallucinations: A Capacity Model for Human Triage and Guardrail Cascades';
const abstract = `Organisations that place large language models (LLMs) in front of customers must decide how many people to keep on standby for hallucinations that get through, and how many guardrail layers to put ahead of them. Practice often sizes the team at the mean incident load and credits each layer with its stand-alone catch rate, as if layers failed independently. We propose a capacity-planning artifact that sets standby capacity at a quantile of the daily count of human-handled incidents, corrects it for over-dispersion, bounds a cascade's residual rate without assuming independence, and models failure classes with different counting processes. We evaluate it on the outputs of three small open models passed through three guardrail layers, with simulated arrivals and public traces of an LLM service, provider incidents, company tickets and court-case hallucinations. One task-specific verifier cut required capacity by ${rg(red)}% but blocked ${rg(fb)}% of correct answers; a routed LLM judge did not demonstrably pay for itself. Mild day-to-day variation in demand sufficed for Poisson-sized plans to be exceeded on ${rg([...none3, ...none44])}% of days without guardrails. Arrivals are simulated and no operator log of hallucinations is public, so the numbers illustrate the method rather than predict production.`;
console.log('abstract words:', abstract.split(/\s+/).length);
const pb = () => new Paragraph({ children: [new PageBreak()] });
const front = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 360, line: 360 }, children: [run(title, { bold: true, size: 32 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 }, children: [run('Manuscript for double-blind review', { italics: true, size: 22 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [run('Abstract', { bold: true })] }),
  P(abstract, { indent: { firstLine: 0 } }),
  new Paragraph({ spacing: { before: 200, line: 360 }, children: [run('Keywords: ', { bold: true }), run('LLM operations, hallucination, guardrails, capacity planning, over-dispersion, counting processes, design science')] }),
  pb(),
];
const doc = new Document({
  creator: 'Anonymous', title,
  styles: { default: { document: { run: { font: 'Times New Roman', size: 24 } } } },
  numbering: { config: [{ reference: 'bul', levels: [{ level: 0, format: d.LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: 'Times New Roman', size: 22 })] })] }) },
    children: [...front, ...intro, ...related, ...model, ...method, ...results, ...findings2, ...discussion, ...conclusion, pb(), ...REFS, pb(), ...appendix, ...sup.C1, ...sup.C2, ...sup.C3, ...appendixEnd],
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync('../MISQ_Manuscript.docx', b); console.log('written', b.length); });
