"""Fill the MISQE manuscript template (unpacked in un/) with content_misqe.py; output in out/."""
import os, re, shutil, sys
from lxml import etree
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import content_misqe as C

SRC, OUT = f"{HERE}/un", f"{HERE}/out"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
shutil.rmtree(OUT, ignore_errors=True)
shutil.copytree(SRC, OUT)

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

fn_ids, fn_xml = {}, []

def footnote(key):
    if key not in fn_ids:
        fid = len(fn_ids) + 1
        fn_ids[key] = fid
        fn_xml.append(f'<w:footnote w:id="{fid}"><w:p><w:pPr><w:pStyle w:val="FootnoteMISQE"/></w:pPr>'
                      f'<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr><w:footnoteRef/></w:r>'
                      f'{runs(" " + C.FOOTNOTES[key], allow_fn=False)}</w:p></w:footnote>')
    return (f'<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/><w:vertAlign w:val="superscript"/></w:rPr>'
            f'<w:footnoteReference w:id="{fn_ids[key]}"/></w:r>')

def runs(text, rpr="", allow_fn=True):
    out = []
    for tok in re.split(r"(\[\[fn:\w+\]\]|\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if not tok:
            continue
        if tok.startswith("[[fn:"):
            assert allow_fn
            out.append(footnote(tok[5:-2]))
            continue
        r = rpr
        if tok.startswith("**"):
            tok, r = tok[2:-2], "<w:b/>" + r
        elif tok.startswith("*"):
            tok, r = tok[1:-1], "<w:i/>" + r
        out.append(f'<w:r>{"<w:rPr>" + r + "</w:rPr>" if r else ""}<w:t xml:space="preserve">{esc(tok)}</w:t></w:r>')
    return "".join(out)

def p(style, inner, ppr=""):
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{ppr}</w:pPr>{inner}</w:p>'

def bullet(text):
    return p("BulletlistMISQE", runs(text))

def lead_bullet(lead, text):
    return p("BulletlistMISQE", runs(f"*{lead}*") + runs(": " + text))

PAGE_BREAK = '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
CELL_RPR = '<w:rFonts w:ascii="Cambria" w:hAnsi="Cambria"/><w:sz w:val="19"/><w:szCs w:val="19"/>'

def table(key):
    t = C.TABLES[key]
    ws = t["widths"]
    def cell(text, w, head):
        style = "TableHeadingMISQE" if head else "Normal"
        ppr = '' if head else '<w:spacing w:before="40" w:after="40" w:line="240" w:lineRule="auto"/>'
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/></w:tcPr>'
                f'{p(style, runs(text, ("<w:b/>" if head else "") + CELL_RPR), ppr)}</w:tc>')
    rows = ['<w:tr><w:trPr><w:tblHeader/></w:trPr>' + "".join(cell(h, w, True) for h, w in zip(t["header"], ws)) + "</w:tr>"]
    rows += ["<w:tr>" + "".join(cell(c, w, False) for c, w in zip(r, ws)) + "</w:tr>" for r in t["rows"]]
    if t["note"]:
        rows.append(f'<w:tr><w:tc><w:tcPr><w:tcW w:w="{sum(ws)}" w:type="dxa"/><w:gridSpan w:val="{len(ws)}"/></w:tcPr>'
                    f'{p("Normal", runs(t["note"], CELL_RPR.replace("19", "17")), "<w:spacing w:before=\"40\" w:after=\"40\" w:line=\"240\" w:lineRule=\"auto\"/>")}</w:tc></w:tr>')
    tbl = (f'<w:tbl><w:tblPr><w:tblStyle w:val="SimpleTwoColumnMISQE1"/><w:tblW w:w="{sum(ws)}" w:type="dxa"/>'
           f'<w:tblLayout w:type="fixed"/><w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
           f'<w:tblGrid>{"".join(f"<w:gridCol w:w=\"{x}\"/>" for x in ws)}</w:tblGrid>{"".join(rows)}</w:tbl>')
    return [p("TableFigureCaptionMISQE", runs(t["caption"]), "<w:keepNext/>"), tbl, p("BodyMISQE", "", '<w:spacing w:after="0"/>')]

EMU = 914400
def figure(key):
    f = C.FIGURES[key]
    shutil.copy(os.path.join(HERE, f["image"]), f"{OUT}/word/media/image2.png")
    cx, cy = int(f["width_in"] * EMU), int(f["height_in"] * EMU)
    drawing = (f'<w:r><w:rPr><w:noProof/></w:rPr><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0" '
               f'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">'
               f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="201" name="Figure 1"/>'
               f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
               f'<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
               f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
               f'<pic:nvPicPr><pic:cNvPr id="201" name="figure1.png"/><pic:cNvPicPr/></pic:nvPicPr>'
               f'<pic:blipFill><a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="rId9"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
               f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
               f'</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')
    return [p("TableFigureCaptionMISQE", runs(f["caption"]), "<w:keepNext/>"),
            p("BodyMISQE", drawing, '<w:keepNext/><w:ind w:firstLine="0"/><w:jc w:val="center"/>')]

def body_blocks(items):
    xml = []
    for kind, val in items:
        if kind == "H1":
            xml.append(p("L1HeadingMISQE", runs(val)))
        elif kind == "H2":
            xml.append(p("L2HeadingMISQE", runs(val)))
        elif kind == "P":
            xml.append(p("BodyMISQE", runs(val)))
        elif kind == "B":
            xml += [lead_bullet(a, b) for a, b in val]
        elif kind == "T":
            xml += table(val)
        elif kind == "F":
            xml += figure(val)
    return xml

B = C.BRIEFING
xml = [p("ArticleTitleMISQE", runs("Executive Briefing: " + C.TITLE)),
       p("L2HeadingMISQE", runs("The Key Problem"))]
xml += [bullet(x) for x in B["problem"]]
xml += [p("L2HeadingMISQE", runs("Key Insights")), p("BodyMISQE", runs(B["basis"]), '<w:ind w:firstLine="0"/>')]
xml += [bullet(x) for x in B["insights"]]
xml += [p("L2HeadingMISQE", runs("What Executives Should Do"))]
xml += [bullet(x) for x in B["do"]]
xml.append(PAGE_BREAK)
xml += [p("ArticleTitleMISQE", runs(C.TITLE)), p("SummaryParagraphMISQE", runs(C.SUMMARY)),
        p("AuthorNameMISQE", runs("Keywords")), p("AuthorAffiliationMISQE", runs(C.KEYWORDS))]
xml += body_blocks(C.BODY)
xml.append(p("L1HeadingMISQE", runs("Appendix: About the Research")))
xml += body_blocks(C.APPENDIX)
xml.append(p("L1HeadingMISQE", runs("Question-and-Answer Section for Answer Engines")))
for q, a in C.QA:
    xml += [p("L2HeadingMISQE", runs(q)), p("BodyMISQE", runs(a))]

# ---- document.xml: replace the body, keep the final section properties ----
path = f"{OUT}/word/document.xml"
tree = etree.parse(path)
body = tree.getroot().find("w:body", NS)
sect = body[-1]
for k in list(body)[:-1]:
    body.remove(k)
for x in xml:
    for el in etree.fromstring(f'<x xmlns:w="{W}">{x}</x>'):
        sect.addprevious(el)
tree.write(path, xml_declaration=True, encoding="UTF-8", standalone=True)

# ---- footnotes.xml: keep separators, replace notes ----
fpath = f"{OUT}/word/footnotes.xml"
s = open(fpath, encoding="utf-8").read()
start = s.index('<w:footnote w:id="1"')
end = s.rindex("</w:footnotes>")
s = s[:start] + "".join(fn_xml) + s[end:]
open(fpath, "w", encoding="utf-8").write(s)
print("ok, footnotes:", len(fn_ids))
