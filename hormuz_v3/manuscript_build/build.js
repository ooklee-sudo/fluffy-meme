// Build the MISQ-format manuscript from content.txt + tables.json + figure PNGs.
// usage: node build.js <dir with content.txt, tables.json, image*.png> <out.docx>
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType,
  AlignmentType, BorderStyle, Footer, PageNumber, PageBreak, HeadingLevel, LineRuleType,
} = require('docx');

const dir = process.argv[2];
const out = process.argv[3];
const lines = fs.readFileSync(path.join(dir, 'content.txt'), 'utf8').split('\n');
const tables = JSON.parse(fs.readFileSync(path.join(dir, 'tables.json'), 'utf8'));

const FONT = 'Times New Roman';
const DOUBLE = { line: 480, lineRule: LineRuleType.AUTO, before: 0, after: 0 };
const SINGLE = { line: 240, lineRule: LineRuleType.AUTO, before: 0, after: 0 };
const TEXT_W = 9360; // 6.5 in

// *italic* markup -> runs
function runs(text, opts = {}) {
  const parts = text.split(/(\*[^*]+\*)/g).filter(s => s.length);
  return parts.map(p => p.startsWith('*') && p.endsWith('*')
    ? new TextRun({ text: p.slice(1, -1), italics: !opts.italics, bold: opts.bold, size: opts.size, font: FONT })
    : new TextRun({ text: p, italics: opts.italics, bold: opts.bold, size: opts.size, font: FONT }));
}

const body = [];
const para = (text, o = {}) => body.push(new Paragraph({
  children: runs(text, o.run || {}), spacing: o.spacing || DOUBLE, alignment: o.align,
  indent: o.indent, heading: o.heading, keepNext: o.keepNext, pageBreakBefore: o.pageBreakBefore,
}));

function addTable(key) {
  const t = tables[key];
  if (!t) throw new Error('missing table ' + key);
  const rows = t.rows;
  const ncol = rows[0].length;
  // column widths proportional to content length, with a floor
  const len = Array(ncol).fill(0);
  rows.forEach(r => r.forEach((c, i) => { len[i] = Math.max(len[i], Math.min(c.length, 60)); }));
  const raw = len.map(l => Math.max(l, 8));
  const sum = raw.reduce((a, b) => a + b, 0);
  const widths = raw.map(w => Math.floor(TEXT_W * w / sum));
  widths[ncol - 1] += TEXT_W - widths.reduce((a, b) => a + b, 0);
  const small = ncol >= 7 ? 16 : 18;
  body.push(new Paragraph({ children: runs(t.title, { bold: true, size: 22 }), spacing: { ...SINGLE, before: 240, after: 120 }, keepNext: true, alignment: AlignmentType.CENTER }));
  const none = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
  const line = { style: BorderStyle.SINGLE, size: 6, color: '000000' };
  const trs = rows.map((r, ri) => {
    const isHead = ri === 0;
    const isPanel = r.slice(1).every(c => c === '') && ncol > 1;
    const last = ri === rows.length - 1;
    if (isPanel) {
      return new TableRow({ children: [new TableCell({
        columnSpan: ncol, width: { size: TEXT_W, type: WidthType.DXA },
        borders: { top: none, bottom: none, left: none, right: none },
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        children: [new Paragraph({ children: runs(r[0], { italics: true, size: small }), spacing: SINGLE })],
      })] });
    }
    return new TableRow({
      tableHeader: isHead, cantSplit: true,
      children: r.map((c, ci) => new TableCell({
        width: { size: widths[ci], type: WidthType.DXA },
        borders: { top: isHead ? line : none, bottom: (isHead || last) ? line : none, left: none, right: none },
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        children: [new Paragraph({ children: runs(c, { bold: isHead, size: small }), spacing: SINGLE, alignment: ci === 0 ? AlignmentType.LEFT : AlignmentType.CENTER })],
      })),
    });
  });
  body.push(new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: widths, rows: trs }));
  if (t.note) body.push(new Paragraph({ children: [new TextRun({ text: 'Note: ', italics: true, size: 18, font: FONT }), ...runs(t.note, { size: 18 })], spacing: { ...SINGLE, before: 80, after: 240 } }));
  else body.push(new Paragraph({ children: [], spacing: { ...SINGLE, after: 240 } }));
}

function addFigure(spec) {
  const [file, title, note] = spec.split('|').map(s => s.trim());
  const buf = fs.readFileSync(path.join(dir, file));
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20); // PNG IHDR
  const W = 600, H = Math.round(W * h / w);
  body.push(new Paragraph({ children: [new ImageRun({ type: 'png', data: buf, transformation: { width: W, height: H }, altText: { title, description: title, name: file } })], alignment: AlignmentType.CENTER, spacing: { ...SINGLE, before: 240 }, keepNext: true }));
  body.push(new Paragraph({ children: runs(title, { bold: true, size: 22 }), alignment: AlignmentType.CENTER, spacing: { ...SINGLE, before: 120, after: note ? 60 : 240 }, keepNext: !!note }));
  if (note) body.push(new Paragraph({ children: [new TextRun({ text: 'Note: ', italics: true, size: 18, font: FONT }), ...runs(note, { size: 18 })], alignment: AlignmentType.CENTER, spacing: { ...SINGLE, after: 240 } }));
}

let pendingBreak = false;
for (const raw of lines) {
  const l = raw.trimEnd();
  if (!l) continue;
  const pb = pendingBreak; pendingBreak = false;
  if (l.startsWith('@TITLE ')) para(l.slice(7), { run: { bold: true, size: 28 }, align: AlignmentType.CENTER, spacing: { ...DOUBLE, after: 240 } });
  else if (l.startsWith('@H1 ')) para(l.slice(4), { run: { bold: true }, align: AlignmentType.CENTER, heading: HeadingLevel.HEADING_1, keepNext: true, pageBreakBefore: pb, spacing: { ...DOUBLE, before: 240 } });
  else if (l.startsWith('@H2 ')) para(l.slice(4), { run: { bold: true }, heading: HeadingLevel.HEADING_2, keepNext: true });
  else if (l.startsWith('@NOINDENT ')) para(l.slice(10));
  else if (l.startsWith('@EQ ')) para(l.slice(4), { align: AlignmentType.CENTER });
  else if (l.startsWith('@REF ')) para(l.slice(5), { indent: { left: 720, hanging: 720 } });
  else if (l.startsWith('@TABLE ')) addTable(l.slice(7).trim());
  else if (l.startsWith('@FIG ')) addFigure(l.slice(5));
  else if (l === '@PAGEBREAK') pendingBreak = true;
  else if (l.startsWith('@')) throw new Error('unknown directive ' + l);
  else para(l, { indent: { firstLine: 720 }, pageBreakBefore: pb });
}

const doc = new Document({
  creator: '', title: 'Manuscript',
  styles: {
    default: { document: { run: { font: FONT, size: 24 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FONT, size: 24, bold: true, color: '000000' }, paragraph: { outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FONT, size: 24, bold: true, color: '000000' }, paragraph: { outlineLevel: 1 } },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 24 })] })] }) },
    children: body,
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(out, b); console.log('wrote', out, body.length, 'blocks'); });
