#!/usr/bin/env python3
"""Build the IEEE Transactions Word version of manuscript.tex from the IEEE Word template.

    python build_docx.py TEMPLATE.docx ../manuscript.tex OUT.docx

The LaTeX source is converted with a small purpose-built converter (it handles only the
constructs used in manuscript.tex).  Math is converted to Word equations (OMML) with pandoc.
Template styles (Title, Abstract, IndexTerms, Heading 1/2, Text, Equation, Figure Caption,
Table Title) are used unchanged.
"""
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from xml.sax.saxutils import escape

TEMPLATE, TEX, OUT = sys.argv[1:4]
FIGDIR = os.path.join(os.path.dirname(os.path.abspath(TEX)), "figs")

src = open(TEX, encoding="utf8").read()
body = src[src.index("\\maketitle") + len("\\maketitle"):src.index("\\end{document}")]

# --------------------------------------------------------------------------
# bibliography: order by first citation (IEEE convention)
# --------------------------------------------------------------------------
bib_block = re.search(r"\\begin\{thebibliography\}\{\d+\}(.*?)\\end\{thebibliography\}", body, re.S)
bib_items = {}
for m in re.finditer(r"\\bibitem\{([^}]+)\}\s*(.*?)(?=\\bibitem|\Z)", bib_block.group(1), re.S):
    bib_items[m.group(1)] = " ".join(m.group(2).split())
main_text = body.replace(bib_block.group(0), "")
cite_order = []
for m in re.finditer(r"\\cite(?:\[[^\]]*\])?\{([^}]+)\}", main_text):
    for k in m.group(1).split(","):
        k = k.strip()
        if k not in cite_order:
            cite_order.append(k)
assert set(cite_order) == set(bib_items), set(bib_items) ^ set(cite_order)
cnum = {k: i + 1 for i, k in enumerate(cite_order)}

# --------------------------------------------------------------------------
# counters and labels
# --------------------------------------------------------------------------
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
labels = {}
sec = sub = fig = tab = eq = asm = prop = 0
appendix = False
last = {}
tok = re.compile(r"\\(section\*?|subsection|appendices)\b(?:\{)?|\\begin\{(figure|table\*?|equation|multline|assumption|proposition)\}|\\label\{([^}]+)\}")
for m in tok.finditer(main_text):
    if m.group(1) == "section":
        sec += 1; sub = 0
        last["sec"] = ("Appendix " + "ABCDEFG"[sec - 1]) if appendix else ROMAN[sec - 1]
    elif m.group(1) == "subsection":
        sub += 1
        last["sec"] = f"{ROMAN[sec - 1]}-{'ABCDEFGH'[sub - 1]}"
    elif m.group(1) == "appendices":
        appendix = True; sec = 0
    elif m.group(2):
        e = m.group(2)
        if e == "figure": fig += 1; last["fig"] = str(fig)
        elif e.startswith("table"): tab += 1; last["tab"] = ROMAN[tab - 1]
        elif e in ("equation", "multline"): eq += 1; last["eq"] = str(eq)
        elif e == "assumption": asm += 1; last["as"] = str(asm)
        elif e == "proposition": prop += 1; last["prop"] = str(prop)
    elif m.group(3):
        k = m.group(3)
        labels[k] = last[k.split(":")[0]]

# --------------------------------------------------------------------------
# math
# --------------------------------------------------------------------------
MACROS = {r"\E": r"\mathbb{E}", r"\eps": r"\varepsilon"}
math_list = []


def prep_math(m):
    m = re.sub(r"\\label\{[^}]*\}", "", m)
    for a, b in MACROS.items():
        m = re.sub(re.escape(a) + r"(?![A-Za-z])", lambda _: b, m)
    m = re.sub(r"\\begin\{multline\}(.*?)\\end\{multline\}", lambda x: r"\begin{gathered}" + x.group(1) + r"\end{gathered}", m, flags=re.S)
    m = m.replace(r"\ ", " ").replace(r"\!", "")
    m = re.sub(r"\\tfrac", r"\\frac", m)
    return " ".join(m.split())


omml_cache = {}


def collect_math(expr):
    e = prep_math(expr)
    if e not in math_list:
        math_list.append(e)
    return e


# --------------------------------------------------------------------------
# inline text -> runs
# --------------------------------------------------------------------------
def rpr(b=False, i=False, sup=False, sz=None, caps=False):
    p = ""
    if b: p += "<w:b/><w:bCs/>"
    if i: p += "<w:i/><w:iCs/>"
    if sup: p += '<w:vertAlign w:val="superscript"/>'
    if sz: p += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    return f"<w:rPr>{p}</w:rPr>" if p else ""


def run(text, **kw):
    if text == "":
        return ""
    return f'<w:r>{rpr(**kw)}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def fmt_cites(keys):
    nums = sorted(set(cnum[k.strip()] for k in keys.split(",")))
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        if j - i >= 2:
            out.append(f"[{nums[i]}]\u2013[{nums[j]}]")
        else:
            out += [f"[{n}]" for n in nums[i:j + 1]]
        i = j + 1
    return ", ".join(out)


def read_group(s, i):
    """s[i] == '{' -> (content, index after the closing brace)."""
    assert s[i] == "{", s[i:i + 30]
    depth, j = 0, i
    while True:
        if s[j] == "{": depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1


SIMPLE = {r"\%": "%", r"\&": "&", r"\_": "_", r"\$": "$", r"\{": "{", r"\}": "}", "~": "\u00a0",
          r"\,": "\u2009", "---": "\u2014", "--": "\u2013", "``": "\u201c", "''": "\u201d",
          r"\ldots": "\u2026", r"\textquotesingle": "'", r"\@": ""}


def plain_number(expr):
    e = expr.replace("\\to", "\u2192").replace("\\times", "\u00d7").replace("-", "\u2212")
    e = e.replace("\\,", "\u2009").replace("\\!", "")
    return e if re.fullmatch(r"[0-9.+\u2212\u2192\u00d7 \u2009]+", e) else None


def inline(s, b=False, i=False, sz=None):
    """LaTeX text -> list of run XML strings (math becomes a placeholder tuple)."""
    out = []
    pos, buf = 0, ""

    def flush():
        nonlocal buf
        if buf:
            out.append(run(buf, b=b, i=i, sz=sz))
            buf = ""

    n = len(s)
    while pos < n:
        c = s[pos]
        if c == "$":
            end = pos + 1
            while s[end] != "$" or s[end - 1] == "\\":
                end += 1
            expr = s[pos + 1:end]
            plain = plain_number(expr)
            if plain is not None:   # purely numeric math is set as ordinary text
                buf += plain
            else:
                flush()
                out.append(("math", collect_math(expr), sz))
            pos = end + 1
            continue
        if c == "\\":
            m = re.match(r"\\([A-Za-z]+)", s[pos:])
            if m:
                name = m.group(1)
                after = pos + 1 + len(name)
                if name in ("emph", "textit"):
                    g, nx = read_group(s, after); flush(); out += inline(g, b=b, i=not i, sz=sz); pos = nx; continue
                if name == "textbf":
                    g, nx = read_group(s, after); flush(); out += inline(g, b=True, i=i, sz=sz); pos = nx; continue
                if name == "cite":
                    opt = ""
                    if s[after] == "[":
                        close = s.index("]", after)
                        opt = s[after + 1:close].replace("~", "\u00a0")
                        after = close + 1
                    g, nx = read_group(s, after)
                    cs = fmt_cites(g)
                    buf += cs[:-1] + ", " + opt + "]" if opt else cs
                    pos = nx; continue
                if name in ("ref", "eqref"):
                    g, nx = read_group(s, after)
                    v = labels[g]
                    buf += f"({v})" if name == "eqref" else v
                    pos = nx; continue
                if name == "IEEEPARstart":
                    g1, nx = read_group(s, after); g2, nx = read_group(s, nx)
                    buf += g1 + g2; pos = nx; continue
                if name == "label":
                    _, nx = read_group(s, after); pos = nx; continue
                if name in ("hfill", "noindent"):
                    pos = after; continue
                if name == "ldots":
                    buf += "\u2026"; pos = after; continue
                if name == "item":
                    pos = after; continue
                raise ValueError("unhandled macro \\" + name + " in: " + s[max(0, pos - 40):pos + 40])
            two = s[pos:pos + 2]
            if two in SIMPLE:
                buf += SIMPLE[two]; pos += 2; continue
            if two == "\\\\":
                flush(); out.append("<w:r><w:br/></w:r>"); pos += 2; continue
            if two == "\\ ":
                buf += " "; pos += 2; continue
            raise ValueError("unhandled escape: " + s[pos:pos + 20])
        for k in ("---", "--", "``", "''"):
            if s.startswith(k, pos):
                buf += SIMPLE[k]; pos += len(k); break
        else:
            if c == "~":
                buf += "\u00a0"
            elif c == "{" or c == "}":
                pass
            else:
                buf += c
            pos += 1
    flush()
    return out


# --------------------------------------------------------------------------
# paragraph / table / figure XML
# --------------------------------------------------------------------------
def render_runs(items):
    xml = ""
    for it in items:
        if isinstance(it, tuple):
            xml += f"@@MATH{math_list.index(it[1])}@@"
        else:
            xml += it
    return xml


def para(style, items, ppr_extra="", text_first=False):
    st = f'<w:pStyle w:val="{style}"/>' if style else ""
    return f"<w:p><w:pPr>{st}{ppr_extra}</w:pPr>{render_runs(items) if not isinstance(items, str) else items}</w:p>"


def text_para(s, style="Text", ppr_extra="", **kw):
    return para(style, inline(s, **kw), ppr_extra)


def png_size(path):
    with open(path, "rb") as f:
        d = f.read(32)
    return struct.unpack(">II", d[16:24])


media = []   # (file name in word/media, source path, rId)
next_rid = [100]


def figure_xml(name, caption_tex, number):
    path = os.path.join(FIGDIR, os.path.basename(name))
    w, h = png_size(path)
    rid = f"rId{next_rid[0]}"; next_rid[0] += 1
    fname = f"fig{number}.png"
    media.append((fname, path, rid))
    cx = int(3.3 * 914400); cy = int(cx * h / w)
    drawing = (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
               f'<wp:docPr id="{200 + number}" name="Figure {number}"/><wp:cNvGraphicFramePr/>'
               f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
               f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{200 + number}" name="{fname}"/><pic:cNvPicPr/></pic:nvPicPr>'
               f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
               f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
               f'</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')
    pic = f'<w:p><w:pPr><w:keepNext/><w:spacing w:before="60" w:after="40"/><w:jc w:val="center"/></w:pPr>{drawing}</w:p>'
    cap = para("FigureCaption", [run(f"Fig. {number}.", b=True, sz=16), run("\u2002", sz=16)] + inline(caption_tex, sz=16),
               '<w:spacing w:after="120"/>')
    return pic + cap


def table_xml(env_body, number, drop=(), fsz=15, widths=None, left_all=False, extra_note=""):
    cap = re.search(r"\\caption\{(.*?)\}\\label", env_body, re.S).group(1)
    tab_m = re.search(r"\\begin\{tabular\}\{[^\n]*\}(.*?)\\end\{tabular\}", env_body, re.S)
    rows = []
    for r in re.split(r"\\\\(?:\[[^\]]*\])?", tab_m.group(1)):
        r = r.replace("\\toprule", "").replace("\\midrule", "").replace("\\bottomrule", "").strip()
        if not r:
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)&", r)]
        rows.append([c for j, c in enumerate(cells) if j not in drop])
    ncol = len(rows[0])
    if widths is None:
        widths = [5040 // ncol] * ncol
    scale = 5040 / sum(widths)
    widths = [int(w * scale) for w in widths]
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    trs = ""
    for ri, row in enumerate(rows):
        tcs = ""
        for ci, cell in enumerate(row):
            top = '<w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>' if ri == 0 else ""
            bot = ""
            if ri == 0: bot = '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
            if ri == len(rows) - 1: bot = '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
            jc = "left" if (ci == 0 or left_all) else "center"
            cp = para(None, inline(cell, b=(ri == 0), sz=fsz),
                      f'<w:spacing w:before="20" w:after="20"/><w:jc w:val="{jc}"/>')
            tcs += f'<w:tc><w:tcPr><w:tcW w:w="{widths[ci]}" w:type="dxa"/><w:tcBorders>{top}{bot}</w:tcBorders><w:tcMar><w:left w:w="40" w:type="dxa"/><w:right w:w="40" w:type="dxa"/></w:tcMar></w:tcPr>{cp}</w:tc>'
        trs += f"<w:tr><w:trPr><w:cantSplit/></w:trPr>{tcs}</w:tr>"
    tbl = (f'<w:tbl><w:tblPr><w:tblW w:w="5040" w:type="dxa"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/></w:tblPr>'
           f'<w:tblGrid>{grid}</w:tblGrid>{trs}</w:tbl>')
    title = para("TableTitle", [run(f"TABLE {ROMAN[number - 1]}", sz=16)], '<w:keepNext/><w:spacing w:before="120"/>')
    title2 = para("TableTitle", inline(cap, sz=16), '<w:keepNext/><w:spacing w:after="60"/>')
    note = ""
    pm = re.search(r"\\parbox\{[^}]*\}\{(.*)\}\s*\\end", env_body, re.S)
    if pm:
        note = para("FigureCaption", inline(" ".join(pm.group(1).replace("\\footnotesize", "").split()) + extra_note, sz=14), '<w:spacing w:before="40" w:after="120"/>')
    else:
        note = '<w:p><w:pPr><w:spacing w:after="80"/></w:pPr></w:p>'
    return title + title2 + tbl + note


def equation_xml(eq_tex, number):
    e = collect_math(eq_tex)
    idx = math_list.index(e)
    tabs = '<w:tabs><w:tab w:val="clear" w:pos="5040"/><w:tab w:val="center" w:pos="2520"/><w:tab w:val="right" w:pos="5040"/></w:tabs>'
    return (f'<w:p><w:pPr><w:pStyle w:val="Equation"/>{tabs}<w:spacing w:before="60" w:after="60"/></w:pPr>'
            f'<w:r><w:tab/></w:r>@@MATH{idx}@@<w:r><w:tab/><w:t>({number})</w:t></w:r></w:p>')


# --------------------------------------------------------------------------
# main conversion loop
# --------------------------------------------------------------------------
blocks = []
abstract_tex = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", src, re.S).group(1).strip()
keywords_tex = re.search(r"\\begin\{IEEEkeywords\}(.*?)\\end\{IEEEkeywords\}", src, re.S).group(1).strip()

text = main_text
text = re.sub(r"\\begin\{abstract\}.*?\\end\{abstract\}", "", text, flags=re.S)
text = re.sub(r"\\begin\{IEEEkeywords\}.*?\\end\{IEEEkeywords\}", "", text, flags=re.S)
text = re.sub(r"\\appendices", "", text)
text = text.replace("\\%", "@@PCT@@")
text = re.sub(r"%[^\n]*", "", text)
text = text.replace("@@PCT@@", "\\%")

# tokenise into top-level chunks
chunks = re.split(r"(\\begin\{(?:figure|table\*?|equation|multline|assumption|proposition|enumerate)\}.*?\\end\{(?:figure|table\*?|equation|multline|assumption|proposition|enumerate)\})", text, flags=re.S)
sec_no = sub_no = 0
fig_no = tab_no = eq_no = 0
in_appendix = False
seen_appendix_marker = "Proof of Proposition"
out = []


def handle_prose(chunk):
    global sec_no, sub_no, in_appendix
    for piece in re.split(r"\n\s*\n", chunk):
        piece = piece.strip()
        if not piece:
            continue
        # headings may be glued to following paragraph text
        while True:
            m0 = re.match(r"\\(section\*?|subsection)(?=\{)", piece)
            if not m0:
                break
            title, endpos = read_group(piece, m0.end())
            ml = re.match(r"(?:\\label\{[^}]*\})?\s*", piece[endpos:])
            kind = m0.group(1)
            class _M:  # minimal stand-in for the previous match object
                @staticmethod
                def end():
                    return endpos + ml.end()
            m = _M
            if kind == "section":
                sec_no += 1; sub_no = 0
                if in_appendix or title.startswith(seen_appendix_marker) or title == "Notation":
                    in_appendix = True
                    letter = "ABCDEFG"[sec_no_app()[0]]
                    head = f"Appendix {letter}: {title}"
                    out.append(para("Heading1", inline(head)))
                else:
                    out.append(para("Heading1", inline(f"{ROMAN[sec_no - 1]}. {title}")))
            elif kind == "section*":
                out.append(para("Heading1", inline(title)))
            else:
                sub_no += 1
                out.append(para("Heading2", inline(f"{'ABCDEFGH'[sub_no - 1]}. {title}"), '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr><w:ind w:left="0" w:firstLine="0"/>'))
            piece = piece[m.end():].strip()
        if piece:
            out.append(text_para(" ".join(piece.split())))


app_counter = [-1]


def sec_no_app():
    app_counter[0] += 1
    return (app_counter[0],)


assump = prop_n = 0
for ch in chunks:
    if not ch.strip():
        continue
    m = re.match(r"\\begin\{(figure|table\*?|equation|multline|assumption|proposition|enumerate)\}(.*)\\end\{.*\}$", ch, re.S)
    if not m:
        handle_prose(ch)
        continue
    env, inner = m.group(1), m.group(2)
    if env == "figure":
        fig_no += 1
        name = re.search(r"\\includegraphics\[[^\]]*\]\{([^}]+)\}", inner).group(1)
        cap = re.search(r"\\caption\{(.*)\}\\label", inner, re.S).group(1)
        out.append(figure_xml(name, " ".join(cap.split()), fig_no))
    elif env.startswith("table"):
        tab_no += 1
        if "tab:gap" in inner:
            out.append(table_xml(inner, tab_no, fsz=14, widths=[900, 1250, 1500, 1390], left_all=True))
        elif "tab:sqrt" in inner:
            out.append(table_xml(inner, tab_no, fsz=13, widths=[560, 480, 600, 600, 640, 520, 560, 640]))
        elif "tab:mech" in inner:
            inner = inner.replace("Trainable subset", "Trainable subset")
            out.append(table_xml(inner, tab_no, drop=(1,), fsz=14, widths=[1150, 500, 500, 1100, 1000, 790], extra_note=" Trainable subsets: edit, MLP block of one layer; LoRA, low-rank adapters on all layers; full fine-tune, all parameters."))
        else:
            out.append(table_xml(inner, tab_no, fsz=14, widths=[1500, 3540], left_all=True))
    elif env in ("equation", "multline"):
        eq_no += 1
        body_eq = inner.strip()
        if env == "multline":
            body_eq = r"\begin{gathered}" + body_eq + r"\end{gathered}"
        out.append(equation_xml(body_eq, eq_no))
    elif env == "assumption":
        assump += 1
        mm = re.match(r"\s*\[(.*?)\](?:\\label\{[^}]*\})?\s*(.*)", inner, re.S)
        label = f"Assumption {assump}"
        if mm:
            label += f" ({mm.group(1)})"
        out.append(para("Text", [run(label + ". ", b=True, i=True)] + inline(" ".join(mm.group(2).split()) if mm else " ".join(inner.split()))))
    elif env == "proposition":
        prop_n += 1
        mm = re.match(r"\s*\[(.*?)\](?:\\label\{[^}]*\})?\s*(.*)", inner, re.S)
        out.append(para("Text", [run(f"Proposition {prop_n} ({mm.group(1)}). ", b=True, i=True)] + inline(" ".join(mm.group(2).split()))))
    elif env == "enumerate":
        for k, it in enumerate(re.split(r"\\item", inner)[1:], 1):
            runs = [run(f"{k})\t")] + inline(" ".join(it.split()))
            out.append(para("Text", runs, '<w:tabs><w:tab w:val="left" w:pos="360"/></w:tabs><w:ind w:left="360" w:hanging="360" w:firstLine="0"/>'))

# bibliography
refs_xml = para("ReferenceHead", [run("References")], '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>')
for k in cite_order:
    refs_xml += para("References", [run(f"[{cnum[k]}]\t", sz=16)] + inline(bib_items[k], sz=16),
                     '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr><w:tabs><w:tab w:val="left" w:pos="360"/></w:tabs><w:ind w:left="360" w:hanging="360"/>')

# front matter pieces
abs_runs = [run("Abstract", b=True, i=True, sz=18), run("\u2014", b=True, sz=18)] + inline(" ".join(abstract_tex.split()), b=True, sz=18)
kw_runs = [run("Index Terms", b=True, i=True, sz=18), run("\u2014", b=True, sz=18)] + inline(" ".join(keywords_tex.split()), b=True, sz=18)
title_tex = re.search(r"\\title\{(.*?)\}\s*\\author", src, re.S).group(1)
title_text = " ".join(title_tex.replace("\\\\", " ").split())

# --------------------------------------------------------------------------
# math -> OMML through pandoc
# --------------------------------------------------------------------------
tmp = tempfile.mkdtemp()
md = "\n\n".join(f"MKS{i}MKE ${e}$ MKX{i}MKX" for i, e in enumerate(math_list))
open(os.path.join(tmp, "m.md"), "w", encoding="utf8").write(md)
subprocess.run(["pandoc", os.path.join(tmp, "m.md"), "-f", "markdown+tex_math_dollars", "-o", os.path.join(tmp, "m.docx")], check=True)
with zipfile.ZipFile(os.path.join(tmp, "m.docx")) as z:
    mdoc = z.read("word/document.xml").decode("utf8")
paras = re.findall(r"<w:p>.*?</w:p>|<w:p [^>]*>.*?</w:p>", mdoc, re.S)
omml = {}
for p in paras:
    mi = re.search(r"MKS(\d+)MKE", p)
    if mi:
        idx = int(mi.group(1))
        found = re.findall(r"<m:oMath>.*?</m:oMath>", p, re.S)
        omml[idx] = found[0] if found else None
bad = [math_list[i] for i in range(len(math_list)) if omml.get(i) is None]
if bad:
    print("WARNING: math not converted (shown as text):", bad)


def fix_omml(x):
    """Reorder pandoc's OMML children into the order required by the schema."""
    def reorder(m, order):
        inner = m.group(2)
        parts = re.findall(r"<m:(\w+)(?: [^>]*)?(?:/>|>.*?</m:\1>)", inner, re.S)
        items = re.findall(r"(<m:(\w+)(?: [^>]*)?(?:/>|>.*?</m:\2>))", inner, re.S)
        items.sort(key=lambda t: order.index(t[1]) if t[1] in order else len(order))
        return m.group(1) + "".join(t[0] for t in items) + m.group(3)
    x = re.sub(r"(<m:dPr>)(.*?)(</m:dPr>)", lambda m: reorder(m, ["begChr", "sepChr", "endChr", "grow", "shp", "ctrlPr"]), x, flags=re.S)
    x = re.sub(r"(<m:rPr>)(.*?)(</m:rPr>)", lambda m: reorder(m, ["lit", "nor", "scr", "sty", "brk", "aln"]), x, flags=re.S)
    x = x.replace('<m:nor /><m:sty m:val="p" />', "<m:nor />")
    x = re.sub(r"(<m:mcPr>)(.*?)(</m:mcPr>)", lambda m: reorder(m, ["count", "mcJc"]), x, flags=re.S)
    return x


def math_xml(i):
    if omml.get(i):
        return fix_omml(omml[i])
    return run(math_list[i], i=True)


# --------------------------------------------------------------------------
# assemble document.xml from the template
# --------------------------------------------------------------------------
work = tempfile.mkdtemp()
with zipfile.ZipFile(TEMPLATE) as z:
    z.extractall(work)
doc = open(os.path.join(work, "word/document.xml"), encoding="utf8").read()
head_end = doc.index("<w:body>") + len("<w:body>")
sect_last = re.findall(r"<w:sectPr [^>]*>(?:(?!<w:sectPr).)*?</w:sectPr>", doc, re.S)[-1]
sect_first = re.findall(r"<w:sectPr [^>]*>(?:(?!<w:sectPr).)*?</w:sectPr>", doc, re.S)[0]
fn_ref_para = re.search(r'<w:p [^>]*><w:pPr><w:pStyle w:val="Text"/><w:ind w:firstLine="0"/>.*?<w:footnoteReference w:customMarkFollows="1" w:id="1"/>.*?</w:p>', doc, re.S).group(0)

front = (
    f'<w:p><w:pPr><w:pStyle w:val="Title"/><w:framePr w:w="0" w:hSpace="0" w:vSpace="0" w:wrap="auto" w:vAnchor="margin" w:hAnchor="text" w:xAlign="left" w:yAlign="inline"/></w:pPr>{run(title_text)}</w:p>'
    '<w:p><w:pPr><w:spacing w:line="252" w:lineRule="auto"/><w:jc w:val="both"/><w:rPr><w:sz w:val="18"/></w:rPr></w:pPr></w:p>'
    '<w:p><w:pPr><w:jc w:val="center"/><w:rPr><w:sz w:val="22"/></w:rPr></w:pPr>' + run("Ook Lee", sz=22) + "</w:p>"
    '<w:p><w:pPr><w:spacing w:after="320"/><w:ind w:firstLine="202"/><w:jc w:val="both"/></w:pPr></w:p>'
    f'<w:p><w:pPr><w:spacing w:before="20" w:after="320"/><w:ind w:firstLine="202"/><w:jc w:val="both"/>{sect_first}</w:pPr></w:p>'
    + fn_ref_para
    + para("Abstract", abs_runs)
    + para("IndexTerms", kw_runs, '<w:spacing w:after="120"/>')
)
sect_first_clean = sect_first
body_xml = front + "".join(out) + refs_xml + sect_last
body_xml = re.sub(r"@@MATH(\d+)@@", lambda m: math_xml(int(m.group(1))), body_xml)
# nothing of the template body survives except the section properties and footnote reference
new_doc = doc[:head_end] + body_xml + "</w:body></w:document>"
open(os.path.join(work, "word/document.xml"), "w", encoding="utf8").write(new_doc)

# footnote 1: dates, correspondence, affiliation
fn = open(os.path.join(work, "word/footnotes.xml"), encoding="utf8").read()
fi = fn.index('<w:footnote w:id="1"')
fj = fn.index("</w:footnote>", fi) + len("</w:footnote>")


def fnp(t, it=False):
    return ('<w:p><w:pPr><w:keepLines/><w:ind w:firstLine="202"/><w:jc w:val="both"/></w:pPr>'
            f'<w:r><w:rPr>{"<w:i/>" if it else ""}<w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr><w:t xml:space="preserve">{escape(t)}</w:t></w:r></w:p>')


foot = ('<w:footnote w:id="1">' + fnp("Manuscript received XX XX, 2026; revised XX XX, 2026. This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors. (Corresponding author: Ook Lee.)")
        + fnp("The author is with the Department of Information System, Hanyang University, Seoul 04763, Republic of Korea (e-mail: ooklee@hanyang.ac.kr).") + "</w:footnote>")
fn = fn[:fi] + foot + fn[fj:]
open(os.path.join(work, "word/footnotes.xml"), "w", encoding="utf8").write(fn)

# relationships: drop template images/ole/hyperlinks, add figures
rels = open(os.path.join(work, "word/_rels/document.xml.rels"), encoding="utf8").read()
rels = re.sub(r'<Relationship [^>]*Type="[^"]*/(?:image|oleObject|hyperlink)"[^>]*/>', "", rels)
add = "".join(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{fn_}"/>' for fn_, _, rid in media)
rels = rels.replace("</Relationships>", add + "</Relationships>")
open(os.path.join(work, "word/_rels/document.xml.rels"), "w", encoding="utf8").write(rels)
shutil.rmtree(os.path.join(work, "word/embeddings"), ignore_errors=True)
for f in os.listdir(os.path.join(work, "word/media")):
    os.remove(os.path.join(work, "word/media", f))
for fn_, path, _ in media:
    shutil.copy(path, os.path.join(work, "word/media", fn_))
ct = open(os.path.join(work, "[Content_Types].xml"), encoding="utf8").read()
if 'Extension="png"' not in ct:
    ct = ct.replace("<Default ", '<Default Extension="png" ContentType="image/png"/><Default ', 1)
ct = re.sub(r'<Override [^>]*embeddings[^>]*/>', "", ct)
open(os.path.join(work, "[Content_Types].xml"), "w", encoding="utf8").write(ct)

if os.path.exists(OUT):
    os.remove(OUT)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    ctp = os.path.join(work, "[Content_Types].xml")
    z.write(ctp, "[Content_Types].xml")
    for root, _, files in os.walk(work):
        for f in files:
            full = os.path.join(root, f)
            arc = os.path.relpath(full, work)
            if arc != "[Content_Types].xml":
                z.write(full, arc)
print("wrote", OUT, "| math expressions:", len(math_list), "| figures:", len(media), "| refs:", len(cite_order))
