"""Build the anonymized Word manuscript from ../manuscript_emse.md.
Steps: strip author/journal lines and Declarations (moved to the title page), caption tables,
convert with pandoc using a Times New Roman / double-spaced reference docx, then add continuous
line numbers and a centered page-number footer."""
import re, subprocess, zipfile, shutil, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "..", "manuscript_emse.md"), encoding="utf8").read()

# --- 1. anonymized markdown ---------------------------------------------------------------
src = re.sub(r"\*\*Journal:\*\*.*?\n\n\*\*Authors:\*\*.*?\n\n", "", src, flags=re.S)
a = src.index("## Declarations"); b = src.index("## References")
src = src[:a] + src[b:]
src = src.replace("Table 1: Eligible repositories", "Table: Table 1. Eligible repositories")

GREEK = {"\\gamma": "γ", "\\lambda": "λ", "\\tau": "τ", "\\mu": "μ", "\\beta": "β"}
SUB = {"_0": "₀", "_t": "ₜ"}
def math_to_text(m):
    t = m.group(1).replace("{,}", ",").replace("\\bar X", "X\u0304")
    for k, v in GREEK.items(): t = t.replace(k, v)
    for k, v in SUB.items(): t = t.replace(k, v)
    t = t.replace("^2", "²")
    t = re.sub(r"(^|[=(\s])-(?=\d)", lambda mm: mm.group(1) + "\u2212", t)
    t = re.sub(r"([A-Za-zα-ωX\u0304]+[₀ₜ²]*)", lambda mm: "*" + mm.group(1) + "*" if re.match(r"[A-Za-zα-ω]", mm.group(1)) else mm.group(1), t)
    return t
src = re.sub(r"\$([^$]+)\$", math_to_text, src)
# move table caption above its table (pandoc places 'Table:' captions after; docx shows above)
src = src.replace("## References\n\n", "## References\n\n::: {custom-style=\"Bibliography\"}\n\n") .rstrip() + "\n\n:::\n"
open(os.path.join(HERE, "manuscript_blind.md"), "w", encoding="utf8").write(src)

# --- 2. reference docx ----------------------------------------------------------------------
ref = os.path.join(HERE, "ref.docx")
open(ref, "wb").write(subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"], capture_output=True, check=True).stdout)
zin = zipfile.ZipFile(ref); files = {n: zin.read(n) for n in zin.namelist()}; zin.close()
st = files["word/styles.xml"].decode("utf8")
TNR = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman" />'
st = re.sub(r'(<w:docDefaults>.*?<w:rPrDefault>\s*<w:rPr>\s*)<w:rFonts [^>]*/>', r'\1' + TNR, st, flags=re.S)
st = st.replace('<w:spacing w:after="200" />', '<w:spacing w:after="0" />', 1)
def sty(sid, fn):
    global st
    m = re.search(r'<w:style [^>]*w:styleId="%s".*?</w:style>' % sid, st, re.S)
    st = st[:m.start()] + fn(m.group(0)) + st[m.end():]
sty("BodyText", lambda s: s.replace('<w:spacing w:before="180" w:after="180" />', '<w:spacing w:before="0" w:after="0" w:line="480" w:lineRule="auto" /><w:ind w:firstLine="720" />'))
sty("Compact", lambda s: s.replace('<w:spacing w:before="36" w:after="36" />', '<w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto" /><w:ind w:firstLine="0" />'))
def heading(size, extra=""):
    def f(s):
        s = re.sub(r'<w:rFonts [^>]*/>', TNR, s)
        s = re.sub(r'<w:color [^>]*/>', '<w:color w:val="000000" />', s)
        s = re.sub(r'<w:sz w:val="\d+" />', '<w:sz w:val="%d" />' % size, s); s = re.sub(r'<w:szCs w:val="\d+" />', '<w:szCs w:val="%d" />' % size, s)
        s = re.sub(r'<w:spacing [^>]*/>', '<w:spacing w:before="360" w:after="120" />', s)
        return s.replace('<w:bCs />', '<w:bCs />' + extra, 1) if extra else s
    return f
sty("Heading1", heading(28)); sty("Heading2", heading(24)); sty("Heading3", heading(24, "<w:i /><w:iCs />"))
def title(s):
    s = re.sub(r'<w:rFonts [^>]*/>', TNR, s); s = re.sub(r'<w:color [^>]*/>', '<w:color w:val="000000" />', s)
    s = re.sub(r'<w:sz w:val="\d+" />', '<w:sz w:val="32" />', s); s = re.sub(r'<w:szCs w:val="\d+" />', '<w:szCs w:val="32" />', s)
    return re.sub(r'<w:spacing [^>]*/>', '<w:spacing w:before="0" w:after="360" />', s)
sty("Title", title)
sty("Bibliography", lambda s: re.sub(r'<w:pPr>.*?</w:pPr>', '', s, flags=re.S).replace('</w:style>', '') .replace('<w:qFormat />', '<w:qFormat /><w:pPr><w:spacing w:before="0" w:after="120" w:line="240" w:lineRule="auto" /><w:ind w:left="720" w:hanging="720" /></w:pPr>', 1) + '</w:style>')
for sid in ("Abstract", "AbstractTitle", "TableCaption", "Caption"):
    sty(sid, lambda s: re.sub(r'<w:color [^>]*/>', '<w:color w:val="000000" />', re.sub(r'<w:rFonts [^>]*/>', TNR, s)))
sty("Table", lambda s: s.replace("<w:tblPr>", '<w:tblPr><w:tblBorders><w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/><w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="BBBBBB"/></w:tblBorders>', 1).replace("</w:tblPr>", "</w:tblPr><w:rPr><w:sz w:val=\"20\"/><w:szCs w:val=\"20\"/></w:rPr>", 1))
files["word/styles.xml"] = st.encode("utf8")
zout = zipfile.ZipFile(ref, "w", zipfile.ZIP_DEFLATED)
for n, d in files.items(): zout.writestr(n, d)
zout.close()

# --- 3. pandoc, then line numbers + page-number footer ----------------------------------------
out = os.path.join(HERE, "Manuscript_blinded.docx")
subprocess.run(["pandoc", os.path.join(HERE, "manuscript_blind.md"), "-o", out, "--reference-doc", ref], check=True)
zin = zipfile.ZipFile(out); files = {n: zin.read(n) for n in zin.namelist()}; zin.close()
doc = files["word/document.xml"].decode("utf8")
NEW_SECT = ('<w:sectPr><w:footerReference w:type="default" r:id="rIdFooter1"/><w:pgSz w:w="11906" w:h="16838"/>'
            '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>'
            '<w:lnNumType w:countBy="1" w:restart="continuous"/></w:sectPr>')
doc, n = re.subn(r"<w:sectPr\s*/>|<w:sectPr[^>]*>.*?</w:sectPr>", NEW_SECT, doc, count=1, flags=re.S); assert n == 1
if 'xmlns:r=' not in doc[:600]: doc = doc.replace("<w:document ", '<w:document xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" ', 1)
files["word/document.xml"] = doc.encode("utf8")
files["word/footer1.xml"] = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:p><w:pPr><w:suppressLineNumbers/><w:jc w:val="center"/></w:pPr><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>').encode("utf8")
rels = files["word/_rels/document.xml.rels"].decode("utf8").replace("</Relationships>", '<Relationship Id="rIdFooter1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/></Relationships>')
files["word/_rels/document.xml.rels"] = rels.encode("utf8")
ct = files["[Content_Types].xml"].decode("utf8").replace("</Types>", '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/></Types>')
files["[Content_Types].xml"] = ct.encode("utf8")
zout = zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED)
for n in ["[Content_Types].xml"] + [n for n in files if n != "[Content_Types].xml"]: zout.writestr(n, files[n])
zout.close(); os.remove(ref); print("built", out)
