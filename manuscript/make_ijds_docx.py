"""Convert ijds_manuscript.tex (INFORMS informs4 class) into a Word file with pandoc, for reading and editing.

Citations become INFORMS author-year text, cross-references become numbers, the bibliography is formatted from
ijds_refs.bib, and \\pending{...} notes are kept in brackets.  The LaTeX file remains the source of truth.

Usage:  python make_ijds_docx.py [ijds_manuscript.tex] [ijds_manuscript.docx]
Requires: pandoc.
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def find_close(s, i):
    """Index of the brace that closes the one opening at s[i]."""
    d = 0
    for k in range(i, len(s)):
        if s[k] == "{" and s[k - 1] != "\\":
            d += 1
        elif s[k] == "}" and s[k - 1] != "\\":
            d -= 1
            if d == 0:
                return k
    raise ValueError("unbalanced braces")


def macro_arg(s, name):
    i = s.index("\\" + name + "{") + len(name) + 1
    return s[i + 1:find_close(s, i)]


def strip_macro(s, name, repl=lambda arg: arg):
    out, i = [], 0
    pat = "\\" + name + "{"
    while True:
        j = s.find(pat, i)
        if j < 0:
            out.append(s[i:])
            return "".join(out)
        out.append(s[i:j])
        c = find_close(s, j + len(pat) - 1)
        out.append(repl(s[j + len(pat):c]))
        i = c + 1


# ------------------------------------------------------------------ bibliography
def parse_bib(path):
    txt = open(path, encoding="utf-8").read()
    entries = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),", txt):
        start = m.end()
        end = find_close(txt, txt.index("{", m.start()))
        body = txt[start:end]
        fields = {}
        for f in re.finditer(r"(\w+)\s*=\s*\{", body):
            c = find_close(body, f.end() - 1)
            fields[f.group(1).lower()] = body[f.end():c]
        fields["type"] = m.group(1).lower()
        entries[m.group(2).strip()] = fields
    return entries


def detex(s):
    s = re.sub(r"\\['`^\"~=.vu]\{?(\w)\}?", r"\1", s)  # accents -> base letter
    s = s.replace("{\\v{Z}}", "Z").replace("\\&", "&").replace("--", "–")
    return s.replace("{", "").replace("}", "")


def authors(e):
    names = [a.strip() for a in e["author"].split(" and ")]
    return names


def last(name):
    name = detex(name)
    return name.split(",")[0].strip() if "," in name else name.split()[-1]


def cite_name(e):
    a = authors(e)
    if a[-1] == "others" or len(a) > 2:
        return f"{last(a[0])} et al."
    if len(a) == 2:
        return f"{last(a[0])} and {last(a[1])}"
    return last(a[0])


def ref_entry(e):
    def person(n):
        n = detex(n)
        if "," in n:
            l, f = [x.strip() for x in n.split(",", 1)]
            ini = "".join(p[0] for p in re.split(r"[\s.-]+", f) if p)
            return f"{l} {ini}"
        return n
    a = authors(e)
    names = ", ".join(person(n) for n in a if n != "others") + (", et al." if a[-1] == "others" else "")
    t, y = detex(e.get("title", "")), e.get("year", "")
    if e["type"] == "article":
        tail = f"*{detex(e['journal'])}* {e.get('volume', '')}"
        if e.get("number"):
            tail += f"({e['number']})"
        if e.get("pages"):
            tail += f":{detex(e['pages'])}"
        return f"{names} ({y}) {t}. {tail}."
    if e["type"] == "book":
        ed = f", {e['edition']} ed." if e.get("edition") else ""
        return f"{names} ({y}) *{t}*{ed} ({detex(e.get('publisher', ''))}, {e.get('address', '')})."
    if e["type"] == "inproceedings":
        pg = f", {detex(e['pages'])}" if e.get("pages") else ""
        return f"{names} ({y}) {t}. *{detex(e['booktitle'])}*{pg}."
    return f"{names} ({y}) {t}. arXiv:{e.get('eprint', '')}."


# ------------------------------------------------------------------ conversion
def convert(src, bib):
    pre, body = src.split("\\maketitle", 1)
    title = macro_arg(pre, "TITLE")
    author = macro_arg(pre, "AUTHOR")
    aff = re.sub(r"\\EMAIL\{([^}]*)\}", r"\1", macro_arg(pre, "AFF"))
    abstract = macro_arg(pre, "ABSTRACT")
    keywords = macro_arg(pre, "KEYWORDS")
    body = body[: body.index("\\bibliographystyle")]
    ack = macro_arg(body, "ACKNOWLEDGMENT") if "\\ACKNOWLEDGMENT{" in body else ""
    body = strip_macro(body, "ACKNOWLEDGMENT", lambda a: "")
    body = re.sub(r"(?m)^%.*\n", "", body)

    # numbering of sections (main + appendix), tables, propositions, equations
    labels, sec, app, tab, prop, eq = {}, 0, 0, 0, 0, 0
    in_app = False
    for m in re.finditer(r"\\begin\{APPENDICES\}|\\section\{|\\subsection\{|\\begin\{table\}|"
                         r"\\begin\{proposition\}|\\begin\{equation\}", body):
        tok, pos = m.group(), m.start()
        after = body[pos:pos + 400]
        lab = re.search(r"\\label\{([^}]+)\}", after)
        if tok == "\\begin{APPENDICES}":
            in_app = True
        elif tok == "\\section{":
            if in_app:
                app += 1
                num = chr(64 + app)
            else:
                sec += 1
                num = str(sec)
            sub = 0
            if lab and lab.start() < after.index("}") + 40:
                labels[lab.group(1)] = num
            cur = num
        elif tok == "\\subsection{":
            sub += 1
            if lab and lab.start() < after.index("}") + 40:
                labels[lab.group(1)] = f"{cur}.{sub}"
        elif tok == "\\begin{table}":
            tab += 1
            e = body.index("\\end{table}", pos)
            for l in re.findall(r"\\label\{([^}]+)\}", body[pos:e]):
                labels[l] = str(tab)
        elif tok == "\\begin{proposition}":
            prop += 1
            if lab:
                labels[lab.group(1)] = str(prop)
        else:
            eq += 1
            e = body.index("\\end{equation}", pos)
            for l in re.findall(r"\\label\{([^}]+)\}", body[pos:e]):
                labels[l] = f"({eq})"

    # headings: numbered text, appendices lettered
    out, i, sec, app, in_app = [], 0, 0, 0, False
    for m in re.finditer(r"\\begin\{APPENDICES\}|\\end\{APPENDICES\}|\\section\{|\\subsection\{", body):
        out.append(body[i:m.start()])
        tok = m.group()
        if tok == "\\begin{APPENDICES}":
            in_app, i = True, m.end()
            continue
        if tok == "\\end{APPENDICES}":
            i = m.end()
            continue
        c = find_close(body, m.end() - 1)
        ttl = body[m.end():c]
        if tok == "\\section{":
            if in_app:
                app += 1
                out.append(f"\\section*{{Appendix {chr(64 + app)}. {ttl}}}")
            else:
                sec += 1
                sub = 0
                out.append(f"\\section*{{{sec}. {ttl}}}")
        else:
            sub += 1
            out.append(f"\\subsection*{{{sec}.{sub} {ttl}}}")
        i = c + 1
    out.append(body[i:])
    body = "".join(out)

    # propositions -> bold run-in paragraphs
    n = [0]

    def prop_sub(m):
        n[0] += 1
        name = f" ({m.group(1)})" if m.group(1) else ""
        return f"\\textbf{{Proposition {n[0]}{name}.}} \\emph{{"
    body = re.sub(r"\\begin\{proposition\}(?:\[([^\]]*)\])?\s*(?:\\label\{[^}]+\})?", prop_sub, body)
    body = body.replace("\\end{proposition}", "}")

    # citations
    def cites(keys):
        return [bib[k.strip()] for k in keys.split(",")]

    def p_sub(m):
        pre_note = m.group(1) or ""
        items = "; ".join(f"{cite_name(e)} {e['year']}" for e in cites(m.group(3)))
        return f"({pre_note + ' ' if pre_note else ''}{items})"
    body = re.sub(r"\\citep(?:\[([^\]]*)\])?(?:\[([^\]]*)\])?\{([^}]+)\}", p_sub, body)
    body = re.sub(r"\\citet\{([^}]+)\}",
                  lambda m: "; ".join(f"{cite_name(e)} ({e['year']})" for e in cites(m.group(1))), body)
    body = re.sub(r"\\citealt\{([^}]+)\}",
                  lambda m: "; ".join(f"{cite_name(e)} {e['year']}" for e in cites(m.group(1))), body)
    used = []
    for m in re.finditer(r"\\cite\w*(?:\[[^\]]*\])*\{([^}]+)\}", src):
        for k in m.group(1).split(","):
            if k.strip() not in used:
                used.append(k.strip())

    # references and labels
    body = re.sub(r"\\(?:eq)?ref\{([^}]+)\}", lambda m: labels.get(m.group(1), "??"), body)
    body = re.sub(r"\\label\{[^}]+\}", "", body)
    body = strip_macro(body, "pending", lambda a: f"[PENDING: {a}]")
    body = body.replace("\\E", "\\mathbb{E}").replace("\\small\n", "\n").replace("\\smallskip\\footnotesize", "")
    body = re.sub(r"\\begin\{table\}\[[^\]]*\]", r"\\begin{table}", body)
    body = re.sub(r"\\cmidrule(\([^)]*\))?\{[^}]*\}", "", body)

    refs = sorted(used, key=lambda k: (last(authors(bib[k])[0]).lower(), bib[k]["year"]))
    ref_md = "\n\n".join(ref_entry(bib[k]) for k in refs)
    front = (f"\\begin{{center}}\\textbf{{{title}}}\\end{{center}}\n\n\\begin{{center}}{author}\\\\ {aff}\\end{{center}}\n\n"
             f"\\textbf{{Abstract.}} {abstract}\n\n\\textbf{{Key words:}} {keywords}\n\n")
    tail = f"\\section*{{Acknowledgments}}\n{ack}\n\n" if ack else ""
    return front + body + tail, ref_md


def textify(src):
    """In Word, signed numbers and footnote marks read better as plain text than as equations."""
    src = re.sub(r"\$([+-])(\d[\d.]*)\$", lambda m: ("\u2212" if m.group(1) == "-" else "+") + m.group(2), src)
    for mark, ch in (("\\dagger", "\u2020"), ("\\ddagger", "\u2021"), ("\\ast", "*")):
        src = src.replace("$^" + mark + "$", "\\textsuperscript{" + ch + "}")
    return src.replace("$<0$", "<0")


def anonymize(src):
    """Review copy: no author, affiliation or repository owner."""
    src = re.sub(r"\\AUTHOR\{[^}]*\}", r"\\AUTHOR{[Author name withheld for review]}", src)
    i = src.index("\\AFF{") + 4
    src = src[:i] + "{Affiliation withheld for review}" + src[find_close(src, i) + 1:]
    src = re.sub(r"https://github\.com/[^\s)]+( \(branch [^)]*\))?", "[repository link withheld for review]", src)
    src = src.replace("the author used Claude", "the author(s) used Claude").replace("The author reviewed", "The author(s) reviewed")
    return src


def main(*argv):
    anon = "--anon" in argv
    rest = [a for a in argv if a != "--anon"]
    tex = rest[0] if rest else os.path.join(HERE, "ijds_manuscript.tex")
    out = rest[1] if len(rest) > 1 else os.path.join(HERE, "ijds_manuscript_anonymized.docx" if anon else "ijds_manuscript.docx")
    src = textify(open(tex, encoding="utf-8").read())
    if anon:
        src = anonymize(src)
    bib = parse_bib(os.path.join(HERE, "ijds_refs.bib"))
    body, refs = convert(src, bib)
    refs_tex = re.sub(r"\*([^*]+)\*", r"\\emph{\1}", refs).replace("&", "\\&")
    with tempfile.TemporaryDirectory() as td:
        bt = os.path.join(td, "body.tex")
        open(bt, "w", encoding="utf-8").write("\\documentclass{article}\\begin{document}\n" + body
                                              + "\n\\section*{References}\n\n" + refs_tex + "\n\\end{document}\n")
        subprocess.run(["pandoc", bt, "-f", "latex", "--reference-doc", os.path.join(HERE, "submission_reference.docx"),
                        "-o", out], check=True)
    import make_dss_docx
    make_dss_docx.polish(out)  # title block, table widths and spacing, schema order
    if anon:  # file properties must not identify the author either
        from docx import Document
        d = Document(out)
        d.core_properties.author = d.core_properties.last_modified_by = ""
        d.save(out)
    print("saved", out)


if __name__ == "__main__":
    main(*sys.argv[1:])
