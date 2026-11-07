// Builds the anonymized JAIS review manuscript from manuscript.txt.
// Run: node build_docx.js   ->  LIDE_JAIS_manuscript.docx
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, BorderStyle, ImageRun, Footer, PageNumber, PageBreak, LineNumberRestartFormat, VerticalAlign,
} = require("docx");

const FONT = "Times New Roman";
const BODY = 24;        // 12 pt
const SMALL = 20;       // 10 pt for tables
const DOUBLE = 480;     // double spacing
const TEXT_W = 9360;    // 6.5 in at 1 in margins

const src = fs.readFileSync(path.join(__dirname, "manuscript.txt"), "utf8").split("\n");

// *italic* and **bold** inline markup
function runs(text, opt = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), font: FONT, size: opt.size || BODY, bold: opt.bold, italics: opt.italics }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), font: FONT, size: opt.size || BODY, bold: true, italics: opt.italics }));
    else out.push(new TextRun({ text: t.slice(1, -1), font: FONT, size: opt.size || BODY, italics: true, bold: opt.bold }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), font: FONT, size: opt.size || BODY, bold: opt.bold, italics: opt.italics }));
  return out;
}

const para = (text, o = {}) => new Paragraph({
  children: runs(text, o),
  alignment: o.align || AlignmentType.LEFT,
  spacing: { line: o.line || DOUBLE, before: o.before || 0, after: o.after || 0 },
  indent: o.indent,
  keepNext: o.keepNext,
});

const border = { style: BorderStyle.SINGLE, size: 2, color: "000000" }; // 1/4 pt
const borders = { top: border, bottom: border, left: border, right: border };

let tableNo = 0, figNo = 0;
const children = [];

function cell(text, width, o = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    borders,
    columnSpan: o.span,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({ children: runs(text, { size: SMALL, bold: o.bold, italics: o.italics }), spacing: { line: 240 } })],
  });
}

function buildTable(caption, rows, note) {
  tableNo += 1;
  children.push(para(`Table ${tableNo}. ${caption}`, { bold: true, align: AlignmentType.CENTER, before: 240, after: 60, line: 240, keepNext: true }));
  const ncol = rows[0].length;
  // width proportional to the longest text in each column, with a floor
  const lens = Array.from({ length: ncol }, (_, j) => Math.max(...rows.map(r => Math.min((r[j] || "").length, 60)), 4));
  const total = lens.reduce((a, b) => a + b, 0);
  // floor = room for the longest single word in the column, so no word breaks mid-way
  const floors = Array.from({ length: ncol }, (_, j) => Math.max(...rows.map(r => Math.max(...(r[j] || "").split(/\s+/).map(w => w.length)))) * 115 + 220);
  let widths = lens.map((l, j) => Math.max(floors[j], Math.round(TEXT_W * l / total)));
  const s = widths.reduce((a, b) => a + b, 0);
  widths = widths.map(w => Math.round(w * TEXT_W / s));
  widths[ncol - 1] += TEXT_W - widths.reduce((a, b) => a + b, 0);
  const trs = rows.map((r, i) => {
    const groupRow = i > 0 && r.slice(1).every(c => c === "");   // a subgroup label row
    if (groupRow) return new TableRow({ children: [cell(r[0], TEXT_W, { span: ncol, italics: true })] });
    return new TableRow({ tableHeader: i === 0, cantSplit: true, children: r.map((c, j) => cell(c, widths[j], { bold: i === 0 })) });
  });
  if (note) trs.push(new TableRow({ children: [cell(note, TEXT_W, { span: ncol })] }));
  children.push(new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: widths, rows: trs }));
  children.push(para("", { line: 240, after: 120 }));
}

function buildFigure(file, caption) {
  figNo += 1;
  const buf = fs.readFileSync(path.join(__dirname, file));
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);   // PNG header
  const outW = 600, outH = Math.round(outW * h / w);          // ~6.25 in wide at 96 dpi
  children.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 240, after: 0 },
    children: [new ImageRun({ type: "png", data: buf, transformation: { width: outW, height: outH },
      altText: { title: `Figure ${figNo}`, description: caption, name: `figure${figNo}` } })] }));
  const m = caption.match(/^(.*?)(\s*\((.*)\))?$/);
  const capRuns = [new TextRun({ text: `Figure ${figNo}. ${m[1]}`, font: FONT, size: BODY, bold: true })];
  if (m[3]) capRuns.push(new TextRun({ text: ` ${m[3]}`, font: FONT, size: SMALL }));
  children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { line: 240, before: 60, after: 240 }, children: capRuns }));
}

// ---- parse ----
let i = 0;
let inRefs = false;
let codeBuf = [];
const flushCode = () => {
  if (!codeBuf.length) return;
  codeBuf.forEach(l => children.push(new Paragraph({ spacing: { line: 240 }, indent: { left: 720 },
    children: [new TextRun({ text: l.length ? l : " ", font: "Courier New", size: SMALL })] })));
  children.push(para("", { line: 240, after: 120 }));
  codeBuf = [];
};

while (i < src.length) {
  const line = src[i];
  if (line.startsWith("CODE:")) { codeBuf.push(line.replace(/^CODE: ?/, "")); i++; continue; }
  flushCode();
  if (!line.trim()) { i++; continue; }

  if (line.startsWith("TITLE:")) {
    const t = line.slice(6).trim();
    children.push(para(t, { bold: true, align: AlignmentType.CENTER, size: 28, after: 240 }));
    children.push(para("[Author information removed for double-blind review]", { italics: true, align: AlignmentType.CENTER, after: 240 }));
  } else if (line.startsWith("ABSTRACT:")) {
    children.push(para("Abstract", { bold: true, align: AlignmentType.CENTER }));
    children.push(para(line.slice(9).trim(), { align: AlignmentType.JUSTIFIED }));
  } else if (line.startsWith("KEYWORDS:")) {
    children.push(new Paragraph({ spacing: { line: DOUBLE, before: 240 }, children: [
      new TextRun({ text: "Keywords: ", font: FONT, size: BODY, bold: true }),
      new TextRun({ text: line.slice(9).trim(), font: FONT, size: BODY })] }));
    children.push(new Paragraph({ children: [new PageBreak()] }));
  } else if (line.startsWith("# ")) {
    const t = line.slice(2).trim();
    inRefs = t === "References";
    const pageBreak = t === "References" || t.startsWith("Appendix");
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: pageBreak, children: [new TextRun({ text: t, font: FONT, size: BODY, bold: true })] }));
  } else if (line.startsWith("## ")) {
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: line.slice(3).trim(), font: FONT, size: BODY, bold: true })] }));
  } else if (line.startsWith("### ")) {
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text: line.slice(4).trim(), font: FONT, size: BODY, bold: true, italics: true })] }));
  } else if (line.startsWith("TABLE:")) {
    const caption = line.slice(6).trim();
    const rows = []; let note = null; i++;
    while (i < src.length && (src[i].startsWith("|") || src[i].startsWith("NOTE:"))) {
      if (src[i].startsWith("NOTE:")) note = src[i].slice(5).trim();
      else rows.push(src[i].split("|").slice(1, -1).map(c => c.trim()));
      i++;
    }
    buildTable(caption, rows, note);
    continue;
  } else if (line.startsWith("FIGURE:")) {
    const [file, caption] = line.slice(7).split("|").map(s => s.trim());
    buildFigure(file, caption);
  } else if (line.startsWith("EQ:")) {
    children.push(para(line.slice(3).trim(), { italics: true, align: AlignmentType.CENTER }));
  } else if (line.startsWith("QUOTE:")) {
    children.push(para(line.slice(6).trim(), { indent: { left: 720, right: 720 }, line: 360, after: 120 }));
  } else if (line.startsWith("REF:")) {
    children.push(para(line.slice(4).trim(), { indent: { left: 720, hanging: 720 } }));
  } else {
    children.push(para(line.trim(), { indent: { firstLine: 720 } }));
  }
  i++;
}
flushCode();

const doc = new Document({
  creator: "",
  title: "Manuscript",
  styles: {
    default: { document: { run: { font: FONT, size: BODY } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: BODY, bold: true }, paragraph: { spacing: { before: 240, after: 0, line: DOUBLE }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: BODY, bold: true }, paragraph: { spacing: { before: 120, after: 0, line: DOUBLE }, keepNext: true, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: BODY, bold: true, italics: true }, paragraph: { spacing: { before: 120, after: 0, line: DOUBLE }, keepNext: true, outlineLevel: 2 } },
    ],
  },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } },
    },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: BODY })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(path.join(__dirname, "LIDE_JAIS_manuscript.docx"), b);
  console.log(`ok: ${tableNo} tables, ${figNo} figures`);
});
