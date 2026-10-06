// MISQ-style helpers: 12-pt Times New Roman, double-spaced body, single-spaced tables and references.
const d = require('docx');
const fs = require('fs');
const { Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType, ImageRun, TabStopType } = d;
const FONT = 'Times New Roman';
const fix = t => t.replace(/k\*/g, 'k∗');
const run = (t, o = {}) => new TextRun({ text: t, font: FONT, size: 24, ...o });
function runs(text, o = {}) {
  text = fix(text);
  const out = []; const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g; let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(run(text.slice(last, m.index), o));
    const s = m[0];
    if (s.startsWith('**')) out.push(run(s.slice(2, -2), { ...o, bold: true })); else out.push(run(s.slice(1, -1), { ...o, italics: true }));
    last = m.index + s.length;
  }
  if (last < text.length) out.push(run(text.slice(last), o));
  return out;
}
const P = (t, o = {}) => new Paragraph({ children: runs(t), spacing: { line: 480, after: 0 }, indent: { firstLine: 720 }, alignment: AlignmentType.LEFT, ...o });
const PN = (t, o = {}) => P(t, { indent: { firstLine: 0 }, ...o });           // paragraph without first-line indent
const H1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, keepNext: true, spacing: { before: 360, after: 120, line: 360 }, children: [run(t, { bold: true, color: '000000' })] });
const H2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, spacing: { before: 240, after: 60, line: 360 }, children: [run(t, { bold: true, italics: true, color: '000000' })] });
const H3 = t => new Paragraph({ keepNext: true, spacing: { before: 120, after: 0, line: 360 }, children: [run(t, { italics: true })] });
// numbered display equation: centred formula, number flush right
const EQ = (t, n) => new Paragraph({ spacing: { before: 120, after: 120, line: 360 }, tabStops: [{ type: TabStopType.CENTER, position: 4680 }, { type: TabStopType.RIGHT, position: 9360 }],
  children: [run('\t'), run(fix(t), { italics: true }), run(n ? `\t(${n})` : '')] });
// proposition / definition box, 1.5 spacing, set off by a rule on the left
const BOX = (label, t) => new Paragraph({ children: [run(label + ' ', { bold: true }), ...runs(t)], spacing: { before: 120, after: 160, line: 360 }, indent: { left: 360, right: 360 }, alignment: AlignmentType.LEFT,
  border: { left: { style: BorderStyle.SINGLE, size: 12, color: '888888', space: 8 } } });
const BUL = t => new Paragraph({ children: runs(t), numbering: { reference: 'bul', level: 0 }, spacing: { after: 60, line: 360 } });
function table(caption, header, rows, widths, note) {
  const total = widths.reduce((a, b) => a + b, 0);
  const b = { style: BorderStyle.SINGLE, size: 4, color: 'AAAAAA' };
  const borders = { top: b, bottom: b, left: b, right: b };
  const cell = (t, w, hdr) => new TableCell({ width: { size: w, type: WidthType.DXA }, borders,
    shading: hdr ? { fill: 'E8E8E8', type: ShadingType.CLEAR, color: 'auto' } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [run(fix(String(t)), { size: 18, bold: hdr })] })] });
  const out = [new Paragraph({ children: [run(fix(caption), { bold: true, size: 22 })], spacing: { before: 240, after: 80, line: 276 }, keepNext: true }),
    new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths,
      rows: [new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, widths[i], true)) }),
        ...rows.map(r => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, widths[i], false)) }))] })];
  out.push(new Paragraph({ children: note ? [run(fix(note), { size: 18, italics: true })] : [], spacing: { before: 60, after: 240, line: 240 } }));
  return out;
}
const IMG = (path, w, h, caption) => [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200 }, children: [new ImageRun({ type: 'png', data: fs.readFileSync(path), transformation: { width: w, height: h }, altText: { title: caption, description: caption, name: caption } })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [run(fix(caption), { size: 20, bold: true })], spacing: { before: 60, after: 240, line: 276 } })];
module.exports = { d, run, runs, P, PN, H1, H2, H3, EQ, BOX, BUL, table, IMG, FONT, fix };
