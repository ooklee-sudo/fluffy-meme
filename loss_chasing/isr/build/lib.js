// Shared helpers: ISR-style manuscript formatting (US Letter, 1" margins, Times New Roman 12 pt, double-spaced).
const D = require('docx');
const { Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType, BorderStyle,
        Footer, PageNumber, HeadingLevel } = D;

const FONT = 'Times New Roman';
const SIZE = 24;            // 12 pt (half-points)
const DOUBLE = 480;         // double spacing (240 = single)

// *italic* and **bold** inline markup
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), font: FONT, size: SIZE, ...base }));
    const t = m[0];
    if (t.startsWith('**')) out.push(new TextRun({ text: t.slice(2, -2), bold: true, font: FONT, size: SIZE, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, font: FONT, size: SIZE, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), font: FONT, size: SIZE, ...base }));
  return out;
}

const body = (t, o = {}) => new Paragraph({
  children: runs(t),
  spacing: { line: DOUBLE, before: 0, after: 0 },
  indent: o.noIndent ? undefined : { firstLine: 720 },
  alignment: o.align || AlignmentType.LEFT,
  keepNext: o.keepNext,
});
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, keepNext: true,
  children: [new TextRun({ text: t, bold: true, font: FONT, size: SIZE })], spacing: { line: DOUBLE, before: 0, after: 0 } });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true,
  children: [new TextRun({ text: t, bold: true, italics: true, font: FONT, size: SIZE })], spacing: { line: DOUBLE, before: 0, after: 0 } });
const center = (t, o = {}) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { line: DOUBLE, before: 0, after: 0 },
  children: runs(t, o.bold ? { bold: true } : {}), keepNext: o.keepNext });
const pageBreak = () => new Paragraph({ children: [new D.PageBreak()] });

// caption sits above the table, single-spaced block inside the table region
const caption = (t) => new Paragraph({ keepNext: true, spacing: { line: DOUBLE, before: 0, after: 0 }, children: runs(t, {}) });
const note = (t) => new Paragraph({ spacing: { line: 240, before: 60, after: 240 }, children: runs(t, { size: 20 }) });

function table(header, rows, widths, opts = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const b = { style: BorderStyle.SINGLE, size: 4, color: '000000' };
  const none = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
  const cell = (txt, w, head, align) => new TableCell({
    width: { size: w, type: WidthType.DXA },
    borders: { top: head ? b : none, bottom: head ? b : none, left: none, right: none },
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    shading: { type: ShadingType.CLEAR, fill: 'FFFFFF', color: 'auto' },
    children: [new Paragraph({ alignment: align, spacing: { line: 240, before: 0, after: 0 },
      children: runs(String(txt), { size: 20, bold: head || undefined }) })],
  });
  const all = [header, ...rows];
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: all.map((r, ri) => new TableRow({ tableHeader: ri === 0, cantSplit: true,
      children: r.map((c, ci) => cell(c, widths[ci], ri === 0, ci === 0 ? AlignmentType.LEFT : (opts.center === false ? AlignmentType.LEFT : AlignmentType.CENTER))) })),
  });
}

const footer = () => new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
  children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: SIZE })] })] });

const pageProps = { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } };

function makeDoc(children, extra = {}) {
  return new D.Document({
    creator: '', title: extra.title || '', description: '',
    styles: { default: { document: { run: { font: FONT, size: SIZE } } },
      paragraphStyles: [
        { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { font: FONT, size: SIZE, bold: true }, paragraph: { spacing: { line: DOUBLE }, outlineLevel: 0 } },
        { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { font: FONT, size: SIZE, bold: true, italics: true }, paragraph: { spacing: { line: DOUBLE }, outlineLevel: 1 } } ] },
    sections: [{ properties: pageProps, footers: { default: footer() }, children }],
  });
}

module.exports = { D, body, h1, h2, center, pageBreak, caption, note, table, makeDoc, runs, FONT, SIZE, DOUBLE };
