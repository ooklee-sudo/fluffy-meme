"""Build manuscript.docx from manuscript.tex.

Run pdflatex twice first so manuscript.aux holds the final numbers; this
script copies citation, equation, table, figure and section numbers from it,
so the Word file matches the PDF exactly.

Usage: python3 make_docx.py
"""
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEX = HERE / "manuscript.tex"
AUX = HERE / "manuscript.aux"
BUILD = HERE / "build_docx"
OUT = HERE / "manuscript.docx"


def group(s, i):
    """Return (content, end) of the balanced {...} group starting at s[i] == '{'."""
    assert s[i] == "{", s[i:i + 30]
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    raise ValueError("unbalanced braces")


def macro_arg(s, name):
    i = s.index("\\" + name + "{") + len(name) + 1
    return group(s, i)[0]


def replace_macro(s, name, fn):
    """Replace every \\name{arg} with fn(arg)."""
    out, i = [], 0
    pat = "\\" + name + "{"
    while True:
        j = s.find(pat, i)
        if j < 0:
            out.append(s[i:])
            return "".join(out)
        arg, end = group(s, j + len(pat) - 1)
        out.append(s[i:j])
        out.append(fn(arg))
        i = end


# ---------------------------------------------------------------- numbers
aux = AUX.read_text()
labels = {m.group(1): m.group(2) for m in re.finditer(r"\\newlabel\{([^}]*)\}\{\{([^}]*)\}", aux)}
bibnum = {m.group(1): int(m.group(2)) for m in re.finditer(r"\\bibcite\{([^}]*)\}\{\{(\d+)\}", aux)}


def cite(arg):
    nums = sorted(bibnum[k.strip()] for k in arg.split(","))
    parts, run = [], [nums[0]]
    for n in nums[1:]:
        if n == run[-1] + 1:
            run.append(n)
        else:
            parts.append(run)
            run = [n]
    parts.append(run)
    txt = []
    for r in parts:
        if len(r) >= 3:
            txt.append(f"{r[0]}--{r[-1]}")
        else:
            txt.extend(str(x) for x in r)
    return "[" + ",".join(txt) + "]"


src = TEX.read_text()
preamble_macros = "\n".join(l for l in src.splitlines() if l.startswith("\\newcommand"))

# ---------------------------------------------------------------- front matter
title = macro_arg(src, "Title")
author = macro_arg(src, "Author")
address = re.search(r"\\address\[1\]\{(.*)\}", src).group(1)
corres = macro_arg(src, "corres")
abstract = macro_arg(src, "abstract")
keywords = macro_arg(src, "keyword")

body = src[src.index("\\begin{document}") + len("\\begin{document}"):src.index("\\vspace{6pt}")]
back = src[src.index("\\vspace{6pt}"):src.index("\\begin{adjustwidth}{-\\extralength}")]
bib = src[src.index("\\begin{thebibliography}"):src.index("\\end{thebibliography}")]

# drop comments
body = re.sub(r"(?<!\\)%.*", "", body)
back = re.sub(r"(?<!\\)%.*", "", back)
bib = re.sub(r"(?<!\\)%.*", "", bib)

# ---------------------------------------------------------------- equations
EQ_NUMBERS = []  # display-equation numbers in document order; written next to each equation in postprocess()


def number_equations(s):
    def eq(m):
        inner = m.group(1)
        lab = re.search(r"\\label\{([^}]*)\}", inner).group(1)
        inner = re.sub(r"\\label\{[^}]*\}", "", inner).strip()
        EQ_NUMBERS.append(labels[lab])
        return f"\\[ {inner} \\]"
    return re.sub(r"\\begin\{equation\}(.*?)\\end\{equation\}", eq, s, flags=re.S)


body = number_equations(body)
body = body.replace("\\Bigl(", "\\left(").replace("\\Bigr)", "\\right)")
body = body.replace("\\operatorname*{argmin}_{\\D}", "\\mathop{\\mathrm{arg\\,min}}_{\\D}")

# ---------------------------------------------------------------- proposition / proof
def prop(m):
    name, lab, text = m.group(1), m.group(2), m.group(3).strip()
    return f"\\textbf{{Proposition {labels[lab]}}} ({name}). \\textit{{{text}}}"


body = re.sub(r"\\begin\{Proposition\}\[([^\]]*)\]\\label\{([^}]*)\}(.*?)\\end\{Proposition\}", prop, body, flags=re.S)
body = body.replace("\\begin{proof}", "\\textit{Proof.} ").replace("\\end{proof}", " $\\square$")

# ---------------------------------------------------------------- sections (MDPI numbering "1." / "1.1.")
sec = sub = 0


def heading(m):
    global sec, sub
    kind, text = m.group(1), m.group(2)
    if kind == "section":
        sec += 1
        sub = 0
        return f"\\section*{{{sec}. {text}}}"
    sub += 1
    return f"\\subsection*{{{sec}.{sub}. {text}}}"


body = re.sub(r"\\(section|subsection)\{(.*)\}(\\label\{[^}]*\})?", heading, body)

# ---------------------------------------------------------------- tables
TABLE_WIDTHS = []  # column-width fractions per table, applied to the Word tables in postprocess()


def table(m):
    t = m.group(0)
    note = ""
    nm = re.search(r"\\noindent\{\\footnotesize\{(.*)\}\}", t, flags=re.S)
    if nm:
        note = "\n\n\\noindent " + nm.group(1).strip() + "\n"
        t = t.replace(nm.group(0), "")
    lab = re.search(r"\\label\{([^}]*)\}", t).group(1)
    t = re.sub(r"\\label\{[^}]*\}", "", t)
    t = t.replace("\\caption{", f"\\caption{{\\textbf{{Table {labels[lab]}.}} ", 1)
    spec = re.search(r"\\begin\{tabularx\}\{\\textwidth\}\{([^\n]*?)\}\n", t)
    # column widths as fractions of the text width: p{..cm} as given, l = 0.2, X-type (L/C/R) share the rest
    cols = re.findall(r"p\{([\d.]+)cm\}|([LCRlcr])", spec.group(1))
    fixed = sum(float(p) / 15.9 if p else (0.2 if k in "lcr" else 0) for p, k in cols)
    nflex = sum(1 for p, k in cols if not p and k in "LCR")
    widths = [float(p) / 15.9 if p else (0.2 if k in "lcr" else (1 - fixed) / nflex) for p, k in cols]
    TABLE_WIDTHS.append(widths)
    colspec = "".join(f"p{{{w:.3f}\\textwidth}}" for w in widths)
    t = t.replace(spec.group(0), "\\begin{tabular}{" + colspec + "}\n")
    t = t.replace("\\end{tabularx}", "\\end{tabular}").replace("\\small", "")
    t = re.sub(r"\\boldmath\{(\$[^$]*\$)\}", r"\1", t)
    first = t.index("\\midrule") + len("\\midrule")
    t = t[:first] + t[first:].replace("\\midrule", "")
    return t + note


body = re.sub(r"\\begin\{table\}\[H\].*?\\end\{table\}", table, body, flags=re.S)

# ---------------------------------------------------------------- figures
def figure(m):
    f = m.group(0)
    lab = re.search(r"\\label\{([^}]*)\}", f).group(1)
    f = re.sub(r"\\label\{[^}]*\}", "", f)
    f = f.replace("\\caption{", f"\\caption{{\\textbf{{Figure {labels[lab]}.}} ", 1)
    return f.replace("[width=10.5 cm]{fig1}", "[width=10.5cm]{fig1.png}")


body = re.sub(r"\\begin\{figure\}\[H\].*?\\end\{figure\}", figure, body, flags=re.S)

# ---------------------------------------------------------------- refs and cites
def resolve(s):
    s = replace_macro(s, "cite", cite)
    s = replace_macro(s, "eqref", lambda k: f"({labels[k]})")
    s = replace_macro(s, "ref", lambda k: labels[k])
    return s


body = resolve(body)
back = resolve(back)

# ---------------------------------------------------------------- back matter
pieces = []
for macro, head in [("funding", "Funding"), ("institutionalreview", "Institutional Review Board Statement"),
                    ("informedconsent", "Informed Consent Statement"), ("dataavailability", "Data Availability Statement"),
                    ("conflictsofinterest", "Conflicts of Interest")]:
    if "\\" + macro + "{" in back:
        pieces.append(f"\\noindent\\textbf{{{head}:}} {macro_arg(back, macro)}\n")
abbr = re.search(r"\\begin\{tabular\}\{@\{\}ll\}(.*?)\\end\{tabular\}", back, flags=re.S).group(1)
pieces.append("\\noindent\\textbf{Abbreviations}\n\n\\noindent The following abbreviations are used in this manuscript:\n\n"
              "\\begin{tabular}{ll}" + abbr + "\\end{tabular}\n")

# ---------------------------------------------------------------- bibliography
items = re.split(r"\\bibitem\[[^\]]*\]\{[^}]*\}", bib)[1:]
refs = "\n".join(f"\\item {it.strip()}" for it in items)

doc = f"""\\documentclass{{article}}
\\usepackage{{amsmath,amssymb,graphicx,booktabs}}
{preamble_macros}
\\begin{{document}}

\\noindent\\textit{{Article}}

\\noindent\\textbf{{{title}}}

\\noindent\\textbf{{{author}}}

\\noindent {address}

\\noindent {corres}

\\noindent\\textbf{{Abstract:}} {abstract}

\\noindent\\textbf{{Keywords:}} {keywords}

{body}

{chr(10).join(pieces)}

\\section*{{References}}
\\begin{{enumerate}}
{refs}
\\end{{enumerate}}
\\end{{document}}
"""

# ---------------------------------------------------------------- MDPI-like styles
FONT = '<w:rFonts w:ascii="Palatino Linotype" w:hAnsi="Palatino Linotype" w:eastAsia="Palatino Linotype" w:cs="Times New Roman"/>'


def set_style(styles, sid, ppr, rpr):
    """Replace pPr/rPr of style sid."""
    m = re.search(r'(<w:style [^>]*w:styleId="%s">)(.*?)(</w:style>)' % sid, styles, flags=re.S)
    inner = re.sub(r"<w:pPr>.*?</w:pPr>|<w:rPr>.*?</w:rPr>", "", m.group(2), flags=re.S)
    return styles[:m.start()] + m.group(1) + inner + f"<w:pPr>{ppr}</w:pPr><w:rPr>{rpr}</w:rPr>" + m.group(3) + styles[m.end():]


def build_reference(path):
    default = subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"],
                             check=True, capture_output=True).stdout
    tmp = BUILD / "default_reference.docx"
    tmp.write_bytes(default)
    with zipfile.ZipFile(tmp) as z:
        files = {n: z.read(n) for n in z.namelist()}
    s = files["word/styles.xml"].decode()
    s = re.sub(r"<w:rPrDefault>.*?</w:rPrDefault>",
               f'<w:rPrDefault><w:rPr>{FONT}<w:sz w:val="20"/><w:szCs w:val="20"/>'
               '<w:lang w:val="en-US" w:eastAsia="en-US" w:bidi="ar-SA"/></w:rPr></w:rPrDefault>', s, flags=re.S)
    s = re.sub(r"<w:pPrDefault>.*?</w:pPrDefault>",
               '<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="260" w:lineRule="atLeast"/></w:pPr></w:pPrDefault>',
               s, flags=re.S)
    body_p = '<w:spacing w:before="0" w:after="0" w:line="260" w:lineRule="atLeast"/><w:ind w:firstLine="425"/><w:jc w:val="both"/>'
    s = set_style(s, "BodyText", body_p, "")
    s = set_style(s, "FirstParagraph", body_p, "")
    s = set_style(s, "Compact", '<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:firstLine="0"/><w:jc w:val="left"/>',
                  '<w:sz w:val="18"/><w:szCs w:val="18"/>')
    s = set_style(s, "Title", '<w:keepNext/><w:spacing w:before="120" w:after="240" w:line="360" w:lineRule="atLeast"/><w:jc w:val="left"/>',
                  f'{FONT}<w:b/><w:bCs/><w:color w:val="000000"/><w:sz w:val="36"/><w:szCs w:val="36"/>')
    s = set_style(s, "Author", '<w:keepNext/><w:spacing w:before="0" w:after="240"/><w:jc w:val="left"/>',
                  f'{FONT}<w:b/><w:bCs/><w:sz w:val="20"/>')
    s = set_style(s, "Heading1", '<w:keepNext/><w:keepLines/><w:spacing w:before="240" w:after="60" w:line="260" w:lineRule="atLeast"/><w:outlineLvl w:val="0"/>',
                  f'{FONT}<w:b/><w:bCs/><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/>')
    s = set_style(s, "Heading2", '<w:keepNext/><w:keepLines/><w:spacing w:before="120" w:after="60" w:line="260" w:lineRule="atLeast"/><w:outlineLvl w:val="1"/>',
                  f'{FONT}<w:i/><w:iCs/><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/>')
    cap_p = '<w:spacing w:before="120" w:after="120" w:line="228" w:lineRule="atLeast"/><w:jc w:val="both"/>'
    s = set_style(s, "Caption", cap_p, '<w:sz w:val="18"/><w:szCs w:val="18"/>')
    s = set_style(s, "TableCaption", '<w:keepNext/>' + cap_p, '<w:sz w:val="18"/><w:szCs w:val="18"/>')
    s = set_style(s, "ImageCaption", cap_p, '<w:sz w:val="18"/><w:szCs w:val="18"/>')
    s = set_style(s, "CaptionedFigure", '<w:keepNext/><w:spacing w:before="120"/><w:jc w:val="center"/>', "")
    s = set_style(s, "Figure", '<w:keepNext/><w:jc w:val="center"/>', "")
    # three-line tables: rule above and below the table, and under the header row
    s = s.replace('<w:tblInd w:w="0" w:type="dxa" />',
                  '<w:tblInd w:w="0" w:type="dxa" /><w:tblBorders><w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
                  '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/></w:tblBorders>', 1)
    # header-row rule: pandoc already defines one; put it in schema order (tcBorders before vAlign)
    s = re.sub(r"(<w:vAlign [^>]*/>)(\s*)(<w:tcBorders>.*?</w:tcBorders>)", r"\3\2\1", s, flags=re.S)
    s = re.sub(r"(<w:color [^>]*/>)>", r"\1", s)  # stray ">" in pandoc's default styles
    files["word/styles.xml"] = sort_ppr(s).encode()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in files.items():
            z.writestr(n, data)


TEXT_WIDTH = 11906 - 2 * 1531  # A4 width minus left/right margins, in DXA

# A4, MDPI-like margins, continuous line numbers (as in MDPI's submission template)
SECTPR = ('<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
          '<w:pgMar w:top="1417" w:right="1531" w:bottom="1077" w:left="1531" w:header="1020" w:footer="850" w:gutter="0"/>'
          '<w:lnNumType w:countBy="1" w:distance="284" w:restart="continuous"/><w:cols w:space="425"/></w:sectPr>')


PPR_ORDER = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr",
             "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
             "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd", "snapToGrid",
             "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc", "textDirection",
             "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange"]


def sort_ppr(xml):
    """Put the children of every <w:pPr> into the order the OOXML schema requires."""
    def fix(m):
        kids = re.findall(r"<w:(\w+)\b(?:[^<>]*/>|[^<>]*>.*?</w:\1>)", m.group(1), flags=re.S)
        parts = [k.group(0) for k in re.finditer(r"<w:(\w+)\b(?:[^<>]*/>|[^<>]*>.*?</w:\1>)", m.group(1), flags=re.S)]
        if len(kids) != len(parts) or any(k not in PPR_ORDER for k in kids):
            return m.group(0)
        parts.sort(key=lambda s: PPR_ORDER.index(re.match(r"<w:(\w+)", s).group(1)))
        return "<w:pPr>" + "".join(parts) + "</w:pPr>"
    return re.sub(r"<w:pPr>(.*?)</w:pPr>", fix, xml, flags=re.S)


def postprocess(path):
    with zipfile.ZipFile(path) as z:
        files = {n: z.read(n) for n in z.namelist() if not n.endswith("/")}
    d = files["word/document.xml"].decode()
    d = re.sub(r"<w:sectPr\b.*?</w:sectPr>", "", d, flags=re.S)
    d = re.sub(r"<w:sectPr ?/>", "", d)
    d = d.replace("</w:body>", SECTPR + "</w:body>")
    # front matter (everything before the first section heading): no indents; title and author styles
    cut = d.index('<w:pStyle w:val="Heading1"')
    head, rest = d[:cut], d[cut:]
    paras = re.findall(r"<w:p>.*?</w:p>|<w:p .*?</w:p>", head, flags=re.S)
    for i, p in enumerate(paras):
        new = re.sub(r'<w:pStyle w:val="(FirstParagraph|BodyText)" ?/>', '<w:pStyle w:val="BodyText"/><w:spacing w:after="160"/><w:ind w:firstLine="0"/>', p)
        if i == 1:
            new = re.sub(r'<w:pStyle w:val="[^"]*" ?/>.*?(?=</w:pPr>)', '<w:pStyle w:val="Title"/>', p, flags=re.S)
        if i == 2:
            new = re.sub(r'<w:pStyle w:val="[^"]*" ?/>.*?(?=</w:pPr>)', '<w:pStyle w:val="Author"/>', p, flags=re.S)
        head = head.replace(p, new, 1)
    d = head + rest
    # paragraphs written with \noindent in the source (back matter, table notes) start with bold labels; keep them flush left
    d = re.sub(r'(<w:pStyle w:val="(?:FirstParagraph|BodyText)" ?/>)(</w:pPr>\s*<w:r>\s*<w:rPr>\s*<w:b(?:Cs)? ?/>)',
               r'\1<w:ind w:firstLine="0"/>\2', d)
    # table widths: full text width, with the column fractions from the LaTeX source
    tables = re.findall(r"<w:tbl>.*?</w:tbl>", d, flags=re.S)
    for tbl, fracs in zip(tables, TABLE_WIDTHS):
        cols = [round(f * TEXT_WIDTH) for f in fracs]
        new = re.sub(r'<w:tblW [^>]*/>', f'<w:tblW w:type="dxa" w:w="{sum(cols)}"/>', tbl, count=1)
        new = re.sub(r"<w:tblGrid>.*?</w:tblGrid>",
                     "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{c}"/>' for c in cols) + "</w:tblGrid>", new, flags=re.S)

        def row(m):
            cells = iter(cols)
            return re.sub(r"<w:tcPr ?/>", lambda _: f'<w:tcPr><w:tcW w:w="{next(cells)}" w:type="dxa"/></w:tcPr>', m.group(0))
        new = re.sub(r"<w:tr>.*?</w:tr>", row, new, flags=re.S)
        d = d.replace(tbl, new, 1)
    # abbreviations list (last table, after the paper's tables): no rules
    if len(tables) > len(TABLE_WIDTHS):
        abbr_tbl = re.findall(r"<w:tbl>.*?</w:tbl>", d, flags=re.S)[len(TABLE_WIDTHS)]
        nil = "".join(f'<w:{b} w:val="nil"/>' for b in ("top", "left", "bottom", "right", "insideH", "insideV"))
        new = re.sub(r'<w:tblLook [^>]*/>', f'<w:tblBorders>{nil}</w:tblBorders><w:tblLook w:firstRow="0" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="1" w:noVBand="1" w:val="0000"/>', abbr_tbl, count=1)
        d = d.replace(abbr_tbl, new, 1)
    # table cells: compact 9 pt style, no first-line indent
    d = re.sub(r"<w:tbl>.*?</w:tbl>",
               lambda m: re.sub(r'<w:pStyle w:val="(?:FirstParagraph|BodyText)" ?/>', '<w:pStyle w:val="Compact"/>', m.group(0)),
               d, flags=re.S)
    # numbered display equations: borderless row, equation centered (display style) and "(n)" flush right
    eqs = re.findall(r'<w:p><w:pPr><w:pStyle w:val="BodyText" ?/></w:pPr>(<m:oMathPara>.*?</m:oMathPara>)</w:p>', d, flags=re.S)
    assert len(eqs) == len(EQ_NUMBERS), (len(eqs), len(EQ_NUMBERS))
    num_w = 850
    nil = "".join(f'<w:{b} w:val="nil"/>' for b in ("top", "left", "bottom", "right", "insideH", "insideV"))
    for math, n in zip(eqs, EQ_NUMBERS):
        cell_p = '<w:pPr><w:pStyle w:val="BodyText"/><w:spacing w:before="60" w:after="60"/><w:ind w:firstLine="0"/><w:jc w:val="%s"/></w:pPr>'
        row = (f'<w:tbl><w:tblPr><w:tblW w:type="dxa" w:w="{TEXT_WIDTH}"/><w:tblBorders>{nil}</w:tblBorders>'
               '<w:tblLayout w:type="fixed"/><w:tblLook w:firstRow="0" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="1" w:noVBand="1" w:val="0000"/></w:tblPr>'
               f'<w:tblGrid><w:gridCol w:w="{TEXT_WIDTH - num_w}"/><w:gridCol w:w="{num_w}"/></w:tblGrid><w:tr>'
               f'<w:tc><w:tcPr><w:tcW w:w="{TEXT_WIDTH - num_w}" w:type="dxa"/><w:tcBorders>{nil}</w:tcBorders><w:vAlign w:val="center"/></w:tcPr>'
               f'<w:p>{cell_p % "center"}{math}</w:p></w:tc>'
               f'<w:tc><w:tcPr><w:tcW w:w="{num_w}" w:type="dxa"/><w:tcBorders>{nil}</w:tcBorders><w:vAlign w:val="center"/></w:tcPr>'
               f'<w:p>{cell_p % "right"}<w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:t>({n})</w:t></w:r></w:p></w:tc></w:tr></w:tbl>')
        d = d.replace(f'<w:p><w:pPr><w:pStyle w:val="BodyText" /></w:pPr>{math}</w:p>', row, 1)
    # schema order fixes for pandoc output: table jc before tblLook; delimiter sepChr before endChr
    d = re.sub(r"(<w:tblW [^>]*/>)((?:(?!</w:tblPr>).)*?)(<w:jc [^>]*/>)", r"\1\3\2", d, flags=re.S)
    d = re.sub(r"(<m:endChr [^>]*/>)(<m:sepChr [^>]*/>)", r"\2\1", d)
    d = re.sub(r"(<m:sty [^>]*/>)(<m:scr [^>]*/>)", r"\2\1", d)
    d = re.sub(r"(<m:nor ?/>)<m:sty [^>]*/>", r"\1", d)  # nor and sty are alternatives
    d = re.sub(r"(<m:mcJc [^>]*/>)(<m:count [^>]*/>)", r"\2\1", d)
    d = sort_ppr(d)
    num = files["word/numbering.xml"].decode()
    num = re.sub(r'(<w:nsid w:val=")([0-9A-Fa-f]+)(")', lambda m: m.group(1) + m.group(2).zfill(8)[-8:] + m.group(3), num)
    files["word/numbering.xml"] = num.encode()
    # settings.xml: pandoc writes top-level elements out of schema order
    order = ["zoom", "embedSystemFonts", "proofState", "stylePaneFormatFilter", "doNotTrackMoves", "defaultTabStop",
             "drawingGridHorizontalSpacing", "drawingGridVerticalSpacing", "displayHorizontalDrawingGridEvery",
             "displayVerticalDrawingGridEvery", "characterSpacingControl", "savePreviewPicture", "footnotePr",
             "endnotePr", "compat", "rsids", "mathPr", "themeFontLang", "clrSchemeMapping", "decimalSymbol", "listSeparator"]
    st = files["word/settings.xml"].decode()
    open_tag = re.search(r"<w:settings[^>]*>", st)
    inner = st[open_tag.end():st.rindex("</w:settings>")]
    elems = [m.group(0) for m in re.finditer(r"<(w|m):(\w+)\b(?:[^<>]*/>|[^<>]*>.*?</\1:\2>)", inner, flags=re.S)]
    names = [re.match(r"<\w+:(\w+)", e).group(1) for e in elems]
    if all(n in order for n in names):
        elems.sort(key=lambda e: order.index(re.match(r"<\w+:(\w+)", e).group(1)))
        st = st[:open_tag.end()] + "".join(elems) + "</w:settings>"
        files["word/settings.xml"] = st.encode()
    files["word/document.xml"] = d.encode()
    ct = files["[Content_Types].xml"].decode()
    if 'Extension="png"' not in ct:
        ct = ct.replace("<Default Extension=\"xml\"", '<Default Extension="png" ContentType="image/png" /><Default Extension="xml"', 1)
        files["[Content_Types].xml"] = ct.encode()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in files.items():
            z.writestr(n, data)


BUILD.mkdir(exist_ok=True)
(BUILD / "pandoc_input.tex").write_text(doc)
shutil.copy(HERE / "fig1.png", BUILD / "fig1.png")
ref = BUILD / "mdpi_reference.docx"
build_reference(ref)
subprocess.run(["pandoc", "pandoc_input.tex", "-f", "latex", "-t", "docx",
                "--reference-doc", str(ref), "-o", str(OUT)],
               cwd=BUILD, check=True)
postprocess(OUT)
print("wrote", OUT)
