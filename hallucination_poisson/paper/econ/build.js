const fs = require('fs');
const { d, P, run } = require('../misq/lib');
const { Document, Packer, Paragraph, AlignmentType, Footer, PageNumber, TextRun, PageBreak } = d;
const { intro, related, model } = require('./e1');
const { method, results } = require('../misq/s2');
const { findings2, sup } = require('../misq/s3');
const { abstractText, discussion, conclusion, appendix, appendixEnd, REFS } = require('./e4');
const title = 'Safety Stock for Machine Error: Standby Labour, Screening Depth and Correlated Risk in LLM Services';
console.log('abstract words:', abstractText.split(/\s+/).length);
const pb = () => new Paragraph({ children: [new PageBreak()] });
const front = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 360, line: 360 }, children: [run(title, { bold: true, size: 32 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 }, children: [run('Manuscript for double-blind review', { italics: true, size: 22 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [run('Abstract', { bold: true })] }),
  P(abstractText, { indent: { firstLine: 0 } }),
  new Paragraph({ spacing: { before: 200, line: 360 }, children: [run('Keywords: ', { bold: true }), run('LLM operations, hallucination, safety stock, newsvendor, factor substitution, correlated risk, over-dispersion')] }),
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
Packer.toBuffer(doc).then(b => { fs.writeFileSync('../ECON_Manuscript.docx', b); console.log('written', b.length); });
