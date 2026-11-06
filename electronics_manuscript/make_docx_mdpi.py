"""Build manuscript_mdpi.docx: the manuscript set in MDPI's official Electronics Word template.

Uses make_docx.py's LaTeX preprocessing (numbers resolved from manuscript.aux), converts the
body with pandoc, then maps every block onto the template's own MDPI_* styles and places it
inside Definitions/electronics-template.dot, keeping the template's front-page layout,
headers, footers, page setup and numbering.

Run pdflatex twice first (for manuscript.aux), then: python3 make_docx_mdpi.py
"""
import html
import re
import shutil
import subprocess
import zipfile

import make_docx as M

HERE = M.HERE
BUILD = HERE / "build_mdpi"
OUT = HERE / "manuscript_mdpi.docx"
TEMPLATE = HERE / "Definitions" / "electronics-template.dot"
TABLE_W, TABLE_IND = 7857, 2608          # template: tables and equations sit in the 7857-dxa text column
EQ_W, EQ_NUM_W = 7428, 431

TNOTE, THEOREM, PROOF, BACK, NOIND = "\u27e6TNOTE\u27e7", "\u27e6THM\u27e7", "\u27e6PRF\u27e7", "\u27e6BACK\u27e7", "\u27e6NOIND\u27e7"


def esc(s):
    return html.escape(s, quote=False)


def latex_to_text(s):
    return subprocess.run(["pandoc", "-f", "latex", "-t", "plain", "--wrap=none"], input=s,
                          capture_output=True, text=True, check=True).stdout.strip()


# ---------------------------------------------------------------- pandoc input with sentinels
body = M.body.replace("\\noindent ", "\\noindent " + TNOTE)
body = body.replace("\\textbf{Proposition", THEOREM + "\\textbf{Proposition")
body = body.replace("\\textit{Proof.} ", PROOF + "\\textbf{Proof.} ")
back = []
for piece in M.pieces:
    if piece.startswith("\\noindent\\textbf{Abbreviations}"):
        piece = piece.replace("\\noindent\\textbf{Abbreviations}", "\\section*{Abbreviations}")
        piece = piece.replace("\\noindent The following", NOIND + "The following")
    else:
        piece = piece.replace("\\noindent\\textbf{", BACK + "\\textbf{", 1)
    back.append(piece)
doc = f"""\\documentclass{{article}}
\\usepackage{{amsmath,amssymb,graphicx,booktabs}}
{M.preamble_macros}
\\begin{{document}}
{body}

{chr(10).join(back)}

\\section*{{References}}
\\begin{{enumerate}}
{M.refs}
\\end{{enumerate}}
\\end{{document}}
"""

# column alignment per table, from the tabularx specs (same order as make_docx.TABLE_WIDTHS)
SPECS = re.findall(r"\\begin\{tabularx\}\{\\textwidth\}\{([^\n]*?)\}\n", M.src)
ALIGN = [["center" if k in "Cc" else "right" if k in "Rr" else "left"
          for p, k in re.findall(r"p\{([\d.]+)cm\}|([LCRlcr])", spec)] for spec in SPECS]
ALIGN = [[a if a else "left" for a in row] for row in ALIGN]
assert len(ALIGN) == len(M.TABLE_WIDTHS)


# ---------------------------------------------------------------- helpers on pandoc XML
def runs_of(p):
    """Paragraph content after its pPr (runs, math, hyperlinks, bookmarks)."""
    inner = re.sub(r"^<w:p>|^<w:p [^>]*>", "", p)[:-len("</w:p>")]
    return re.sub(r"^<w:pPr>.*?</w:pPr>", "", inner, flags=re.S)


def para(style, content, extra=""):
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{extra}</w:pPr>{content}</w:p>'


def text_of(x):
    return "".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", x))


def drop_sentinels(x):
    for s in (TNOTE, THEOREM, PROOF, BACK, NOIND):
        x = x.replace(s, "")
    return re.sub(r'<w:r><w:t xml:space="preserve"></w:t></w:r>|<w:r><w:t></w:t></w:r>', "", x)


def three_line_table(tbl, fracs, align):
    cols = [round(f * TABLE_W) for f in fracs]
    rows = re.findall(r"<w:tr>.*?</w:tr>|<w:tr .*?</w:tr>", tbl, flags=re.S)
    out = [f'<w:tbl><w:tblPr><w:bidiVisual w:val="0"/><w:tblW w:w="{sum(cols)}" w:type="dxa"/><w:tblInd w:w="{TABLE_IND}" w:type="dxa"/>'
           '<w:tblBorders><w:top w:val="single" w:sz="8" w:space="0" w:color="auto"/><w:bottom w:val="single" w:sz="8" w:space="0" w:color="auto"/></w:tblBorders>'
           '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="57" w:type="dxa"/><w:right w:w="57" w:type="dxa"/></w:tblCellMar>'
           '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
           "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{c}"/>' for c in cols) + "</w:tblGrid>"]
    for ri, row in enumerate(rows):
        cells = re.findall(r"<w:tc>.*?</w:tc>", row, flags=re.S)
        trpr = "<w:trPr><w:tblHeader/></w:trPr>" if ri == 0 else ""
        out.append(f"<w:tr>{trpr}")
        for ci, cell in enumerate(cells):
            border = '<w:tcBorders><w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/></w:tcBorders>' if ri == 0 else ""
            paras = re.findall(r"<w:p>.*?</w:p>|<w:p .*?</w:p>", cell, flags=re.S) or ["<w:p></w:p>"]
            jc = align[ci] if ri > 0 else ("center" if align[ci] == "center" else "left")
            ps = "".join(para("MDPI42tablebody", runs_of(p), f'<w:spacing w:line="240" w:lineRule="auto"/><w:jc w:val="{jc}"/>') for p in paras)
            out.append(f'<w:tc><w:tcPr><w:tcW w:w="{cols[ci]}" w:type="dxa"/>{border}<w:vAlign w:val="center"/></w:tcPr>{ps}</w:tc>')
        out.append("</w:tr>")
    return "".join(out) + "</w:tbl>"


def plain_table(tbl):
    """Abbreviations: two borderless columns in the text column."""
    rows = re.findall(r"<w:tr>.*?</w:tr>|<w:tr .*?</w:tr>", tbl, flags=re.S)
    cols = [1500, TABLE_W - 1500]
    out = [f'<w:tbl><w:tblPr><w:bidiVisual w:val="0"/><w:tblW w:w="{TABLE_W}" w:type="dxa"/><w:tblInd w:w="{TABLE_IND}" w:type="dxa"/>'
           '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar>'
           '<w:tblLook w:val="0000" w:firstRow="0" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="1" w:noVBand="1"/></w:tblPr>'
           "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{c}"/>' for c in cols) + "</w:tblGrid>"]
    for row in rows:
        cells = re.findall(r"<w:tc>.*?</w:tc>", row, flags=re.S)
        out.append("<w:tr>")
        for ci, cell in enumerate(cells):
            p = (re.findall(r"<w:p>.*?</w:p>|<w:p .*?</w:p>", cell, flags=re.S) or ["<w:p></w:p>"])[0]
            out.append(f'<w:tc><w:tcPr><w:tcW w:w="{cols[ci]}" w:type="dxa"/></w:tcPr>'
                       + para("MDPI42tablebody", runs_of(p), '<w:jc w:val="left"/>') + "</w:tc>")
        out.append("</w:tr>")
    return "".join(out) + "</w:tbl>"


def equation_table(math, number):
    return (f'<w:tbl><w:tblPr><w:bidiVisual w:val="0"/><w:tblW w:w="{EQ_W + EQ_NUM_W}" w:type="dxa"/><w:tblInd w:w="{TABLE_IND}" w:type="dxa"/>'
            '<w:tblCellMar><w:left w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar>'
            '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
            f'<w:tblGrid><w:gridCol w:w="{EQ_W}"/><w:gridCol w:w="{EQ_NUM_W}"/></w:tblGrid><w:tr>'
            f'<w:tc><w:tcPr><w:tcW w:w="{EQ_W}" w:type="dxa"/></w:tcPr>{para("MDPI39equation", math)}</w:tc>'
            f'<w:tc><w:tcPr><w:tcW w:w="{EQ_NUM_W}" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>'
            f'{para("MDPI3aequationnumber", f"<w:r><w:t>({number})</w:t></w:r>")}</w:tc></w:tr></w:tbl>')


# ---------------------------------------------------------------- convert the body
def convert_body(d, numbering):
    num_fmt = {}
    for m in re.finditer(r'<w:num w:numId="(\d+)"[^>]*>.*?<w:abstractNumId w:val="(\d+)"', numbering, flags=re.S):
        a = re.search(r'<w:abstractNum [^>]*w:abstractNumId="%s".*?<w:numFmt w:val="([^"]+)"' % m.group(2), numbering, flags=re.S)
        num_fmt[m.group(1)] = a.group(1) if a else "bullet"
    inner = d[d.index("<w:body>") + 8:d.rindex("<w:sectPr")]
    blocks = re.findall(r"<w:tbl>.*?</w:tbl>|<w:p>.*?</w:p>|<w:p .*?</w:p>|<w:p/>", inner, flags=re.S)
    out, eq_i, tbl_i = [], 0, 0
    prev, in_refs, abbr_next = None, False, False
    kinds = []
    for b in blocks:
        style = (re.search(r'<w:pStyle w:val="([^"]+)"', b) or [None, None])[1] if b.startswith("<w:p") else None
        if b.startswith("<w:tbl>"):
            kinds.append("tbl")
        elif "<m:oMathPara>" in b:
            kinds.append("eq")
        elif "<w:numPr>" in b:
            kinds.append("list")
        else:
            kinds.append(style or "p")
    for i, b in enumerate(blocks):
        k = kinds[i]
        nxt = kinds[i + 1] if i + 1 < len(kinds) else None
        if k == "tbl":
            if abbr_next:
                out.append(plain_table(b))
                abbr_next = False
            else:
                out.append(three_line_table(b, M.TABLE_WIDTHS[tbl_i], ALIGN[tbl_i]))
                tbl_i += 1
        elif k == "eq":
            math = re.search(r"<m:oMathPara>.*</m:oMathPara>", b, flags=re.S).group(0)
            out.append(equation_table(math, M.EQ_NUMBERS[eq_i]))
            eq_i += 1
        elif k == "Heading1":
            in_refs = text_of(b).strip() == "References"
            out.append(para("MDPI21heading1", runs_of(b)))
        elif k == "Heading2":
            out.append(para("MDPI22heading2", runs_of(b)))
        elif k == "list":
            nid = re.search(r'<w:numId w:val="(\d+)"', b).group(1)
            if in_refs:
                style = "MDPI81references"
            else:
                style = "MDPI38bullet" if num_fmt.get(nid, "bullet") == "bullet" else "MDPI37itemize"
            extra = '<w:spacing w:before="60"/>' if style != "MDPI81references" else ""
            out.append(para(style, runs_of(b), extra))
        elif k == "TableCaption":
            out.append(para("MDPI41tablecaption", runs_of(b)))
        elif k in ("CaptionedFigure", "Figure"):
            out.append(para("MDPI52figure", runs_of(b)))
        elif k == "ImageCaption":
            out.append(para("MDPI51figurecaption", runs_of(b)))
        elif b == "<w:p/>":
            continue
        else:
            t = text_of(b)
            c = runs_of(b)
            if TNOTE in t:
                out.append(para("MDPI43tablefooter", drop_sentinels(c)))
            elif THEOREM in t:
                out.append(para("MDPI82theorem", drop_sentinels(c), '<w:spacing w:before="240" w:after="240"/>'))
            elif PROOF in t:
                out.append(para("MDPI83proof", drop_sentinels(c), '<w:spacing w:before="240" w:after="240"/>'))
            elif BACK in t:
                out.append(para("MDPI62backmatter", drop_sentinels(c)))
            elif NOIND in t:
                out.append(para("MDPI32textnoindent", drop_sentinels(c), '<w:spacing w:after="240"/>'))
                abbr_next = True
            elif prev == "eq" and t[:1].islower():
                out.append(para("MDPI32textnoindent", c))
            elif nxt == "list" and prev != "list":
                out.append(para("MDPI35textbeforelist", c))
            elif prev == "list" and not in_refs:
                out.append(para("MDPI36textafterlist", c))
            else:
                out.append(para("MDPI31text", c))
        prev = k
    assert eq_i == len(M.EQ_NUMBERS) and tbl_i == len(M.TABLE_WIDTHS), (eq_i, tbl_i)
    return "".join(out)


# ---------------------------------------------------------------- front matter from the template
def front_matter(tblocks):
    def retext(p, runs):
        head = re.match(r"(<w:p[^>]*>(?:<w:pPr>.*?</w:pPr>)?)", p, flags=re.S).group(1)
        return head + runs + "</w:p>"
    r = lambda s, rpr="": f'<w:r>{rpr}<w:t xml:space="preserve">{esc(s)}</w:t></w:r>'
    title = latex_to_text(M.title)
    abstract = latex_to_text(M.abstract)
    keywords = latex_to_text(M.keywords)
    address = latex_to_text(M.address)
    corres = latex_to_text(M.corres)
    fm = [
        retext(tblocks[0], r("Article")),
        retext(tblocks[1], r(title)),
        retext(tblocks[2], r(latex_to_text(M.author))),
        tblocks[3],                                    # academic editor / history / citation / copyright box
        retext(tblocks[4], r(address)),
        retext(tblocks[6], r(corres)),
        tblocks[7],                                    # "Abstract" heading
        retext(tblocks[8], r(abstract)),
        retext(tblocks[9], r("Keywords: ", "<w:rPr><w:b/></w:rPr>") + r(keywords)),
        tblocks[10],                                   # rule under the keywords
    ]
    return "".join(fm)


# ---------------------------------------------------------------- assemble
def main():
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir()
    (BUILD / "pandoc_input.tex").write_text(doc)
    for png in HERE.glob("*.png"):
        shutil.copy(png, BUILD / png.name)
    subprocess.run(["pandoc", "pandoc_input.tex", "-f", "latex", "-t", "docx", "-o", "body.docx"], cwd=BUILD, check=True)
    with zipfile.ZipFile(BUILD / "body.docx") as z:
        pd = {n: z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(TEMPLATE) as z:
        files = {n: z.read(n) for n in z.namelist() if not n.endswith("/")}

    body_xml = convert_body(pd["word/document.xml"].decode(), pd["word/numbering.xml"].decode())
    # schema order fixes for pandoc's math output
    body_xml = re.sub(r"(<m:endChr [^>]*/>)(<m:sepChr [^>]*/>)", r"\2\1", body_xml)
    body_xml = re.sub(r"(<m:sty [^>]*/>)(<m:scr [^>]*/>)", r"\2\1", body_xml)
    body_xml = re.sub(r"(<m:nor ?/>)<m:sty [^>]*/>", r"\1", body_xml)
    body_xml = re.sub(r"(<m:mcJc [^>]*/>)(<m:count [^>]*/>)", r"\2\1", body_xml)

    # relationships used by the body (images, hyperlinks) -> new ids in the template package
    prel = pd["word/_rels/document.xml.rels"].decode()
    trel = files["word/_rels/document.xml.rels"].decode()
    new_rels = []
    for rid in sorted(set(re.findall(r'r:(?:embed|id)="([^"]+)"', body_xml)), key=len, reverse=True):
        rel = re.search(r'<Relationship [^>]*Id="%s"[^>]*/>' % re.escape(rid), prel).group(0)
        nid = "rIdB" + rid[3:]
        target = re.search(r'Target="([^"]+)"', rel).group(1)
        if "/image" in rel:
            name = "b_" + target.split("/")[-1]
            files["word/media/" + name] = pd["word/" + target]
            rel = rel.replace(f'Target="{target}"', f'Target="media/{name}"')
        new_rels.append(rel.replace(f'Id="{rid}"', f'Id="{nid}"'))
        body_xml = re.sub(r'(r:(?:embed|id)=")%s"' % re.escape(rid), r'\g<1>%s"' % nid, body_xml)
    files["word/_rels/document.xml.rels"] = trel.replace("</Relationships>", "".join(new_rels) + "</Relationships>").encode()

    td = files["word/document.xml"].decode()
    root_end = td.index(">", td.index("<w:document")) + 1
    root = td[:root_end]
    for pfx, uri in [("a", "http://schemas.openxmlformats.org/drawingml/2006/main"),
                     ("pic", "http://schemas.openxmlformats.org/drawingml/2006/picture"),
                     ("wp", "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"),
                     ("m", "http://schemas.openxmlformats.org/officeDocument/2006/math"),
                     ("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")]:
        if f"xmlns:{pfx}=" not in root:
            root = root[:-1] + f' xmlns:{pfx}="{uri}">'
    tbody = td[td.index("<w:body>") + 8:td.rindex("</w:body>")]
    tblocks = re.findall(r"<w:tbl>.*?</w:tbl>|<w:p [^>]*/>|<w:p [^>]*[^/]>.*?</w:p>|<w:p>.*?</w:p>|<w:sectPr.*?</w:sectPr>", tbody, flags=re.S)
    notes = next(b for b in tblocks if "MDPI63notes" in b)
    sectpr = tblocks[-1]
    assert sectpr.startswith("<w:sectPr")
    new_doc = root + "<w:body>" + front_matter(tblocks) + body_xml + notes + sectpr + "</w:body></w:document>"
    files["word/document.xml"] = new_doc.encode()

    ct = files["[Content_Types].xml"].decode()
    ct = ct.replace("wordprocessingml.template.main+xml", "wordprocessingml.document.main+xml")
    files["[Content_Types].xml"] = ct.encode()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in files.items():
            z.writestr(n, data)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
