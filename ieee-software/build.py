"""Fill the IEEE CS magazine template (unpacked in tpl/un) with content.py; write tpl/out/ then zip."""
import copy, re, shutil, os, sys
from lxml import etree
sys.path.insert(0, os.path.dirname(__file__))
import content as C

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = f"{HERE}/tpl/un"
OUT = f"{HERE}/tpl/out"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
q = lambda t: f"{{{W}}}{t}"

shutil.rmtree(OUT, ignore_errors=True)
shutil.copytree(SRC, OUT)

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def runs(text, base_rpr=""):
    """Inline markup -> w:r XML. ^x^ superscript, **x** bold, *x* italic."""
    out = []
    for tok in re.split(r"(\^[^^]+\^|\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if not tok:
            continue
        rpr = base_rpr
        if tok.startswith("^"):
            tok, rpr = tok[1:-1], rpr + '<w:vertAlign w:val="superscript"/>'
        elif tok.startswith("**"):
            tok, rpr = tok[2:-2], '<w:b/>' + rpr
        elif tok.startswith("*"):
            tok, rpr = tok[1:-1], '<w:i/>' + rpr
        out.append(f'<w:r>{"<w:rPr>" + rpr + "</w:rPr>" if rpr else ""}<w:t xml:space="preserve">{esc(tok)}</w:t></w:r>')
    return "".join(out)

def p(style, inner, ppr_extra=""):
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{ppr_extra}</w:pPr>{inner}</w:p>'

H2_PPR = '<w:spacing w:before="240"/><w:rPr><w:b w:val="0"/><w:bCs w:val="0"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr>'
H2_RPR = '<w:b w:val="0"/><w:bCs w:val="0"/><w:sz w:val="24"/><w:szCs w:val="24"/>'

def bullet(lead, text, sep="—"):
    return p("ListParagraph", runs(f"*{lead}*") + runs(sep + text),
             '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="6"/></w:numPr><w:ind w:left="360"/>')

PG = '<w:pgSz w:w="11232" w:h="15408"/><w:pgMar w:top="1040" w:right="1040" w:bottom="1080" w:left="1040" w:header="600" w:footer="660" w:gutter="0"/>'
def sect_break(cols2):
    cols = '<w:cols w:num="2" w:space="280"/>' if cols2 else '<w:cols w:space="280"/>'
    return f'<w:p><w:pPr><w:pStyle w:val="Para"/><w:spacing w:after="0" w:line="120" w:lineRule="exact"/><w:ind w:firstLine="0"/><w:sectPr><w:type w:val="continuous"/>{PG}{cols}<w:docGrid w:linePitch="299"/></w:sectPr></w:pPr></w:p>'

TF = '<w:rFonts w:ascii="Helvetica-Light" w:hAnsi="Helvetica-Light"/><w:sz w:val="16"/><w:szCs w:val="16"/>'
def cell(text, w, head=False):
    rpr = TF + ("<w:b/>" if head else "")
    shade = '<w:shd w:val="clear" w:color="auto" w:fill="DBE5F1"/>' if head else ""
    return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shade}</w:tcPr>'
            f'<w:p><w:pPr><w:pStyle w:val="TableParagraph"/><w:spacing w:before="20" w:after="20" w:line="200" w:lineRule="exact"/><w:ind w:left="60" w:right="60"/></w:pPr>'
            f'{runs(text, rpr)}</w:p></w:tc>')

def table(key, num):
    t = C.TABLES[key]
    ws = t["widths"]
    border = "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="000000"/>' for s in ["top", "left", "bottom", "right", "insideH", "insideV"])
    xml = [p("AuthorBio", f'<w:r><w:rPr><w:color w:val="0070C0"/></w:rPr><w:t xml:space="preserve">TABLE {num}</w:t></w:r>' + runs(". " + t["caption"]),
             '<w:keepNext/><w:spacing w:before="200" w:after="60"/>')]
    xml.append(f'<w:tbl><w:tblPr><w:tblW w:w="{sum(ws)}" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>{border}</w:tblBorders>'
               f'<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar><w:tblLook w:val="01E0"/></w:tblPr>'
               f'<w:tblGrid>{"".join(f"<w:gridCol w:w=\"{x}\"/>" for x in ws)}</w:tblGrid>')
    xml.append('<w:tr><w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>' + "".join(cell(h, w, True) for h, w in zip(t["header"], ws)) + "</w:tr>")
    for r in t["rows"]:
        xml.append('<w:tr><w:trPr><w:cantSplit/></w:trPr>' + "".join(cell(c, w) for c, w in zip(r, ws)) + "</w:tr>")
    xml.append("</w:tbl>")
    start = 1
    xml[start:] = ["".join(xml[start:start + len(t["rows"]) + 3])] + xml[start + len(t["rows"]) + 3:]
    for letter, note in t["notes"]:
        xml.append(p("ParaContinue", f'<w:r><w:rPr><w:position w:val="6"/><w:sz w:val="12"/></w:rPr><w:t>{letter}</w:t></w:r>' + runs(note, '<w:sz w:val="16"/>'),
                     '<w:spacing w:before="40" w:after="0"/>'))
    if not t["notes"]:
        xml.append(p("ParaContinue", "", '<w:spacing w:after="0"/>'))
    return xml

EMU = 914400
def figure(key, num):
    f = C.FIGURES[key]
    shutil.copy(os.path.join(HERE, f["image"]), f"{OUT}/word/media/image2.png")
    cx, cy = int(f["width_in"] * EMU), int(f["height_in"] * EMU)
    drawing = (f'<w:r><w:rPr><w:noProof/></w:rPr><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0" '
               f'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">'
               f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{100 + num}" name="Figure {num}"/>'
               f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
               f'<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
               f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
               f'<pic:nvPicPr><pic:cNvPr id="{100 + num}" name="figure{num}.png"/><pic:cNvPicPr/></pic:nvPicPr>'
               f'<pic:blipFill><a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="rId21"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
               f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
               f'</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')
    return [p("Para", drawing, '<w:keepNext/><w:spacing w:before="160" w:after="60"/><w:ind w:firstLine="0"/><w:jc w:val="center"/>'),
            p("FigureCaption", f'<w:r><w:rPr><w:color w:val="0070C0"/></w:rPr><w:t xml:space="preserve">FIGURE {num}</w:t></w:r>' + runs(". " + f["caption"]),
              '<w:spacing w:after="160"/>')]

# ---- document.xml ----
path = f"{OUT}/word/document.xml"
tree = etree.parse(path)
body = tree.getroot().find("w:body", NS)
kids = list(body)

def set_text_runs(par, xml_runs, keep_first_run=False):
    """Replace all runs of a paragraph (optionally keeping the first run, e.g. pictures)."""
    rs = [c for c in par if c.tag in (q("r"), q("hyperlink"), q("bookmarkStart"), q("bookmarkEnd"))]
    for r in rs[1 if keep_first_run else 0:]:
        par.remove(r)
    frag = etree.fromstring(f'<x xmlns:w="{W}">{xml_runs}</x>')
    for r in frag:
        par.append(r)

# 0: title paragraph (pictures in first run, title text in second)
title_p = kids[0]
title_runs = title_p.findall("w:r", NS)
title_runs[-1].find("w:t", NS).text = C.TITLE
for t in title_p.iter(q("t")):
    if "Article Type" in (t.text or ""):
        t.text = "           " + C.ARTICLE_TYPE
# authors: block 4 holds a picture + sectPr; put the single author there and drop blocks 2-3
set_text_runs(kids[4], runs(C.AUTHOR + ", ") + runs(C.AFFIL, '<w:b w:val="0"/><w:bCs/><w:i/><w:iCs/>'), keep_first_run=True)
body.remove(kids[2]); body.remove(kids[3])
# 6: abstract
AB = '<w:rFonts w:ascii="Helvetica-Black" w:hAnsi="Helvetica-Black"/><w:b/>{}<w:sz w:val="20"/><w:szCs w:val="20"/>'
set_text_runs(kids[6], runs("Abstract", AB.format("<w:i/>")) + runs("—", AB.format("")) + runs(C.ABSTRACT, AB.format("<w:i/>")))
# 7: empty spacer -> actionable insights (single-column region before the body section break)
ins = [p("Para", runs("Actionable insights for practitioners", '<w:rFonts w:ascii="Helvetica-Black" w:hAnsi="Helvetica-Black"/><w:b/><w:sz w:val="20"/>'),
         '<w:keepNext/><w:spacing w:before="200" w:after="60"/><w:ind w:firstLine="0"/>')]
ins += [bullet(a, b + ("" if b.endswith(".") else ".")) for a, b in C.INSIGHTS]
anchor = kids[7]
for x in ins:
    anchor.addprevious(etree.fromstring(f'<x xmlns:w="{W}">{x}</x>')[0])
body.remove(anchor)

# 9: first body paragraph with drop-cap image + copyright footnote reference
first = kids[9]
fr = [r for r in first.findall("w:r", NS) if r.find("w:footnoteReference", NS) is not None][0]
drop = first.findall("w:r", NS)[0]
for r in first.findall("w:r", NS):
    first.remove(r)
first.append(drop)
for r in etree.fromstring(f'<x xmlns:w="{W}">{runs(C.INTRO_FIRST)}</x>'):
    first.append(r)
first.append(fr)

# remove template body blocks 10 .. before final sectPr
for k in kids[10:-1]:
    body.remove(k)
final_sect = kids[-1]

xml = []
tnum = {"T1": 1, "T2": 2}
for kind, val in C.BODY:
    if kind == "P":
        xml.append(p("Para", runs(val)))
    elif kind == "H1":
        xml.append(p("Heading1", runs(val)))
    elif kind == "H2":
        xml.append(p("Heading2", runs(val, H2_RPR), H2_PPR))
    elif kind == "L":
        xml += [bullet(a, b) for a, b in val]
    elif kind == "T":
        xml.append(sect_break(cols2=True))
        xml += table(val, tnum[val])
        xml.append(sect_break(cols2=False))
    elif kind == "F":
        xml += figure(val, 1)
xml.append(p("AckHead", runs("ACKNOWLEDGMENTS")))
xml.append(p("Para", runs(C.ACK)))
xml.append(p("ReferenceHead", runs("REFERENCES")))
for i, r in enumerate(C.REFS, 1):
    xml.append(p("Bibentry", f'<w:r><w:t>{i}.</w:t><w:tab/></w:r>' + runs(r)))
xml.append(p("AuthorBio", runs("**" + C.BIO_NAME + "**") + runs(C.BIO), '<w:spacing w:before="240" w:after="0" w:line="240" w:lineRule="auto"/>'))

for x in xml:
    for el in etree.fromstring(f'<x xmlns:w="{W}">{x}</x>'):
        final_sect.addprevious(el)
tree.write(path, xml_declaration=True, encoding="UTF-8", standalone=True)

# ---- headers / footers ----
def sub(fname, old, new):
    f = f"{OUT}/word/{fname}"
    s = open(f, encoding="utf-8").read()
    assert old in s, (fname, old)
    open(f, "w", encoding="utf-8").write(s.replace(old, new))
sub("header1.xml", "THEME/FEATURE/DEPARTMENT", "FEATURE")
sub("header2.xml", ">HEAD<", f">{C.RUNNING_HEAD}<")
for f in ["footer1.xml", "footer2.xml"]:
    sub(f, "Publication Title", "IEEE Software")
sub("footer3.xml", "Publication Name", "IEEE Software")
print("ok")

# ---- stretch the title banner for a three-line title (+52pt) ----
f = f"{OUT}/word/document.xml"
s = open(f, encoding="utf-8").read()
for old, new in [("margin-top:-11.65pt;width:558.75pt;height:46.15pt", "margin-top:-11.65pt;width:558.75pt;height:178pt"),
                 ("margin-top:62.25pt;width:468pt;height:15pt", "margin-top:114.25pt;width:468pt;height:15pt"),
                 ("margin-top:27.75pt;width:50.25pt;height:117pt", "margin-top:27.75pt;width:50.25pt;height:169pt"),
                 ("margin-top:-57.75pt;width:50.25pt;height:202.5pt", "margin-top:-57.75pt;width:50.25pt;height:254.5pt")]:
    assert old in s, old
    s = s.replace(old, new)
# send banner shapes behind the text so the longer title stays visible
for z in ["251658752", "251659776", "251656704", "251655680", "251657728", "251660800", "251653632"]:
    s = s.replace(f"z-index:{z};", f"z-index:-{z};")
open(f, "w", encoding="utf-8").write(s)
print("banner ok")
