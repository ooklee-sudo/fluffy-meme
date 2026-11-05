"""Convert main.tex (acmart) to a Word manuscript, main.docx.

Pandoc cannot read the acmart front matter or resolve LaTeX numbering, so this script
writes a simplified copy (build_word.tex) in which section, equation, table, figure,
definition, proposition, and theorem numbers are spelled out to match the PDF, then
runs pandoc with citeproc and applies manuscript formatting with python-docx.

Run after compiling main.tex with latexmk, so that main.aux holds the label numbers.
"""
import re
import subprocess

from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.shared import Pt, RGBColor

SRC, TMP, OUT = "main.tex", "build_word.tex", "main.docx"

labels = dict(re.findall(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", open("main.aux").read()))
s = open(SRC).read()

# ---------------------------------------------------------------- front matter
title = re.search(r"\\title\[[^\]]*\]\{(.+?)\}\n", s).group(1)
abstract = re.search(r"\\begin\{abstract\}(.+?)\\end\{abstract\}", s, re.S).group(1).strip()
ccs = re.findall(r"\\ccsdesc\[\d+\]\{(.+?)\}", s)
keywords = re.search(r"\\keywords\{(.+?)\}", s).group(1)
body = s[s.index("\\maketitle") + len("\\maketitle"):s.index("\\end{document}")]

ccs_text = "; ".join(c.replace("~", " $\\rightarrow$ ") for c in ccs)
front = (
    "\\noindent Ook Lee, Hanyang University, Seoul, Republic of Korea "
    "(ooklee@hanyang.ac.kr; ORCID 0000-0003-4361-7927)\n\n"
    "\\section*{Abstract}\n" + abstract + "\n\n"
    "\\noindent\\textbf{CCS Concepts:} " + ccs_text + "\n\n"
    "\\noindent\\textbf{Additional Key Words and Phrases:} " + keywords + "\n\n"
)

# ---------------------------------------------------------------- numbering
# Sections and subsections: write the numbers into the headings.
out, sec, sub, appendix = [], 0, 0, False
for line in body.split("\n"):
    if line.strip() == "\\appendix":
        appendix, sec = True, 0
        continue
    m = re.match(r"\\(sub)?section\{(.+?)\}(\\label\{[^}]+\})?\s*$", line)
    if m:
        if m.group(1):
            sub += 1
            num = f"{chr(64 + sec) if appendix else sec}.{sub}"
            line = f"\\subsection*{{{num} {m.group(2)}}}"
        else:
            sec, sub = sec + 1, 0
            num = chr(64 + sec) if appendix else str(sec)
            line = f"\\section*{{{num} {m.group(2)}}}"
    out.append(line)
body = "\n".join(out)

# Cross-references.
body = re.sub(r"\\ref\{([^}]+)\}", lambda m: labels.get(m.group(1), "??"), body)

# Display equations: numbered ones get the number written next to them.
def eq(m):
    inner = m.group(1)
    lab = re.search(r"\\label\{([^}]+)\}", inner)
    inner = re.sub(r"\\label\{[^}]+\}", "", inner).strip()
    num = labels[lab.group(1)] if lab else None
    tag = re.search(r"\\tag\{([^}]+)\}", inner)
    if tag:
        num, inner = tag.group(1), re.sub(r"\\tag\{[^}]+\}", "", inner).strip()
    return f"\\[ {inner} \\qquad ({num}) \\]" if num else f"\\[ {inner} \\]"

body = re.sub(r"\\begin\{equation\}(.+?)\\end\{equation\}", eq, body, flags=re.S)
body = re.sub(r"\\begin\{equation\*\}(.+?)\\end\{equation\*\}", lambda m: f"\\[ {m.group(1).strip()} \\]", body, flags=re.S)

# Definitions, propositions, and appendix results as run-in bold labels.
counters = {"construct": 0, "proposition": 0, "C": 0}
names = {"construct": "Definition", "proposition": "Proposition", "lemma": "Lemma",
         "theorem": "Theorem", "corollary": "Corollary"}

def thm(m):
    env, opt, inner = m.group(1), m.group(2), m.group(3)
    inner = re.sub(r"\\label\{[^}]+\}", "", inner).strip()
    if env in ("lemma", "theorem", "corollary"):
        counters["C"] += 1
        num = f"C.{counters['C']}"
    else:
        counters[env] += 1
        num = str(counters[env])
    head = f"{names[env]} {num}" + (f" ({opt})" if opt else "") + "."
    return f"\n\\noindent\\textbf{{{head}}} \\emph{{{inner}}}\n"

body = re.sub(r"\\begin\{(construct|proposition|lemma|theorem|corollary)\}(?:\[([^\]]*)\])?(.+?)\\end\{\1\}",
              thm, body, flags=re.S)
body = re.sub(r"\\begin\{proof\}(.+?)\\end\{proof\}",
              lambda m: f"\n\\noindent\\emph{{Proof.}} {m.group(1).strip()} $\\blacksquare$\n", body, flags=re.S)

# Run-in paragraph headings, as in the PDF.
body = re.sub(r"\\paragraph\{([^}]*)\}", r"\\noindent\\textbf{\1.}", body)

# Table and figure captions with their numbers; notes become ordinary paragraphs.
def cap(kind):
    def f(m):
        inner = m.group(1)
        lab = re.search(r"\\label\{([^}]+)\}", m.group(0))
        num = labels.get(lab.group(1), "") if lab else ""
        return f"\\caption{{{kind} {num}. {inner}}}"
    return f

body = re.sub(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}(\\label\{tab:[^}]+\})", cap("Table"), body)
body = re.sub(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}(\\label\{fig:[^}]+\})", cap("Figure"), body)
body = re.sub(r"\\par\\smallskip\\footnotesize\s*", r"\\par ", body)
body = re.sub(r"\\Description\{[^}]*\}", "", body)
body = body.replace("\\small\n", "")

# Tables: drop partial rules and turn simple numeric math into plain text.
body = re.sub(r"\\cmidrule(\([a-z]+\))?\{[^}]*\}", "", body)

def plain_cells(m):
    t = m.group(0)
    def num(mm):
        x = mm.group(1)
        if re.fullmatch(r"[-+0-9.,\s\[\]<]*", x):
            return x.replace("-", "\u2212")
        return mm.group(0)
    return re.sub(r"\$([^$]*)\$", num, t)

body = re.sub(r"\\begin\{tabular\}.+?\\end\{tabular\}", plain_cells, body, flags=re.S)

# Simple inline math becomes plain text (italic letters, sub/superscripts), so that it
# shows in any viewer; anything more complex stays as a Word equation.
GREEK = {"sigma": "σ", "pi": "π", "nu": "ν", "xi": "ξ", "zeta": "ζ", "rho": "ρ", "beta": "β",
         "theta": "θ", "kappa": "κ", "psi": "ψ", "delta": "δ", "tau": "τ", "omega": "ω",
         "mu": "μ", "gamma": "γ", "lambda": "λ", "varepsilon": "ε", "eta": "η",
         "Delta": "Δ", "Gamma": "Γ", "Omega": "Ω", "Pi": "Π"}
OPS = {"le": "≤", "ge": "≥", "approx": "≈", "ldots": "…", "to": "→", "in": "∈", "infty": "∞",
       "mid": "|", "times": "×", "cdot": "·"}

def atom(tok):
    if tok.startswith("\\"):
        name = tok[1:]
        if name in GREEK:
            return "\\textit{" + GREEK[name] + "}"
        return OPS[name]
    if tok.isalpha():
        if tok in ("max", "min", "ln", "exp", "log", "iff", "FB"):
            return tok
        return "\\textit{" + tok + "}"
    return tok.replace("-", "\u2212")

REL = {"=", "<", ">", "≤", "≥", "≈", "→", "∈", "×", "|"}

def to_text(x):
    toks = re.findall(r"\\[A-Za-z]+|[_^](?:\{[^{}]*\}|\\[A-Za-z]+|.)|[A-Za-z]+|\d*\.?\d+|\S", x)
    out, prev = [], None   # prev: kind of previous piece ("op", "open", "val")
    for t in toks:
        if t[0] in "_^" and len(t) > 1:
            arg = t[1:]
            if arg.startswith("{"):
                arg = arg[1:-1]
            inner = "".join(atom(a) for a in re.findall(r"\\[A-Za-z]+|[A-Za-z]+|\d+|\S", arg))
            out.append(("\\textsubscript{" if t[0] == "_" else "\\textsuperscript{") + inner + "}")
            prev = "val"
            continue
        a = atom(t)
        if a in REL:
            out.append(" " + a + " ")
            prev = "op"
        elif a in ("+", "\u2212"):
            if prev in (None, "op", "open"):
                out.append(a)
            else:
                out.append(" " + a + " ")
                prev = "op"
                continue
            prev = "op"
        elif a == ",":
            out.append(", ")
            prev = "op"
        elif a in ("(", "["):
            out.append(a)
            prev = "open"
        else:
            out.append(a)
            prev = "val"
    txt = "".join(out)
    return re.sub(r"\s+", " ", txt).strip()

def inline(m):
    x = m.group(1)
    cmds = set(re.findall(r"\\([A-Za-z]+)", x))
    if cmds - set(GREEK) - set(OPS) or "{" in x.replace("_{", "").replace("^{", ""):
        return m.group(0)
    if re.search(r"[_^][_^]", x):
        return m.group(0)
    try:
        return to_text(x)
    except KeyError:
        return m.group(0)

body = re.sub(r"(?<!\\)\$([^$]+)\$", inline, body)

# Bibliography is produced by citeproc.
body = re.sub(r"\\bibliographystyle\{[^}]+\}\s*\\bibliography\{[^}]+\}",
              lambda m: "\\section*{References}\n\n::: {#refs}\n:::\n", body)
refs_marker = "\\section*{References}"
appendix_start = body.find("\\section*{A ")
# Keep references before the appendices, as in the PDF.

doc = ("\\documentclass{article}\n\\usepackage{amsmath}\n\\usepackage{graphicx}\n\\usepackage{natbib}\n"
       f"\\title{{{title}}}\n\\begin{{document}}\n\\maketitle\n" + front + body + "\n\\end{document}\n")
doc = doc.replace("::: {#refs}\n:::", "\\hypertarget{refs}{}")
open(TMP, "w").write(doc)

subprocess.run(["pandoc", TMP, "-f", "latex", "-o", OUT, "--citeproc",
                "--bibliography=references.bib", "--resource-path=.",
                "-M", "link-citations=false", "-M", "reference-section-title=References"],
               check=True)

# ---------------------------------------------------------------- formatting
d = Document(OUT)
for st in d.styles:
    try:
        if st.type == 1:
            st.font.name = "Times New Roman"
            st.font.color.rgb = RGBColor(0, 0, 0)
            if not st.name.startswith(("Heading", "Title")):
                st.font.size = Pt(12)
    except Exception:
        pass
for p in d.paragraphs:
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE
# Tables span the text width with single-spaced cells.
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
for t in d.tables:
    pr = t._tbl.tblPr
    w = pr.find(qn("w:tblW"))
    if w is None:
        w = OxmlElement("w:tblW")
        pr.append(w)
    w.set(qn("w:type"), "pct")
    w.set(qn("w:w"), "5000")
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "autofit")
    pr.append(layout)
    for row in t.rows:
        for cell in row.cells:
            for cp in cell.paragraphs:
                cp.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                for r in cp.runs:
                    r.font.size = Pt(10)
d.save(OUT)
print("wrote", OUT)
