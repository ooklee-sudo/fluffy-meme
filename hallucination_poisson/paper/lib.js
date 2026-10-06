const d = require('docx');
const { Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType, ImageRun } = d;
const FONT = 'Times New Roman';
const run = (t, o = {}) => new TextRun({ text: t, font: FONT, size: 22, ...o });
// inline markup: *italic* and **bold**
function runs(text) {
  const out = []; const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g; let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(run(text.slice(last, m.index)));
    const s = m[0];
    if (s.startsWith('**')) out.push(run(s.slice(2, -2), { bold: true })); else out.push(run(s.slice(1, -1), { italics: true }));
    last = m.index + s.length;
  }
  if (last < text.length) out.push(run(text.slice(last)));
  return out;
}
const P = (t, o = {}) => new Paragraph({ children: runs(t), spacing: { after: 120, line: 300 }, alignment: AlignmentType.JUSTIFIED, ...o });
const H1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 280, after: 120 }, children: [run(t, { bold: true, size: 26 })] });
const H2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 100 }, children: [run(t, { bold: true, italics: true, size: 23 })] });
const EQ = t => new Paragraph({ children: [run(t, { italics: true })], alignment: AlignmentType.CENTER, spacing: { before: 80, after: 120 } });
const BOX = (label, t) => new Paragraph({ children: [run(label + ' ', { bold: true }), ...runs(t)], spacing: { after: 120, line: 300 }, indent: { left: 360, right: 360 }, alignment: AlignmentType.JUSTIFIED,
  border: { left: { style: BorderStyle.SINGLE, size: 12, color: '888888', space: 8 } } });
const BUL = t => new Paragraph({ children: runs(t), numbering: { reference: 'bul', level: 0 }, spacing: { after: 60, line: 288 } });
function table(caption, header, rows, widths, note) {
  const total = widths.reduce((a, b) => a + b, 0);
  const b = { style: BorderStyle.SINGLE, size: 4, color: 'AAAAAA' };
  const borders = { top: b, bottom: b, left: b, right: b };
  const cell = (t, w, hdr) => new TableCell({ width: { size: w, type: WidthType.DXA }, borders,
    shading: hdr ? { fill: 'E8E8E8', type: ShadingType.CLEAR, color: 'auto' } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [run(String(t), { size: 18, bold: hdr })] })] });
  const out = [new Paragraph({ children: [run(caption, { bold: true, size: 20 })], spacing: { before: 160, after: 60 }, keepNext: true }),
    new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths,
      rows: [new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, widths[i], true)) }),
        ...rows.map(r => new TableRow({ children: r.map((c, i) => cell(c, widths[i], false)) }))] })];
  if (note) out.push(new Paragraph({ children: [run(note, { size: 18, italics: true })], spacing: { before: 40, after: 160 } }));
  else out.push(new Paragraph({ children: [], spacing: { after: 120 } }));
  return out;
}
const fs = require('fs');
const IMG = (path, w, h, caption) => [new Paragraph({ alignment: AlignmentType.CENTER, children: [new ImageRun({ type: 'png', data: fs.readFileSync(path), transformation: { width: w, height: h }, altText: { title: caption, description: caption, name: caption } })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [run(caption, { size: 18, italics: true })], spacing: { after: 160 } })];
module.exports = { d, run, runs, P, H1, H2, EQ, BOX, BUL, table, IMG, FONT };
