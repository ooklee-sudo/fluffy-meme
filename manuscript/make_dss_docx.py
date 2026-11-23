"""Word version of dss_manuscript.tex (elsarticle) for reading and editing, via the converter in make_ijds_docx.py.

Usage:  python make_dss_docx.py      (needs pandoc; writes dss_manuscript.docx)
"""
import os
import re
import subprocess
import tempfile

import make_ijds_docx as M

HERE = os.path.dirname(os.path.abspath(__file__))


def to_informs_macros(src):
    """Rewrite the elsarticle front matter and appendix markup into the macros make_ijds_docx understands."""
    fm = src[src.index("\\begin{frontmatter}"):src.index("\\end{frontmatter}")]
    title = M.macro_arg(fm, "title")
    author = re.sub(r"\\corref\{[^}]*\}", "", fm[fm.index("\\author[") :].split("]", 1)[1].split("\n")[0]).strip()[1:-1]
    c = fm.index("{", fm.index("\\cortext["))
    email = fm[c + 1:M.find_close(fm, c)].replace("Corresponding author. ", "")
    aff = fm[fm.index("\\address["):].split("]", 1)[1].split("\n")[0].strip()[1:-1]
    abstract = fm[fm.index("\\begin{abstract}") + 16:fm.index("\\end{abstract}")].strip()
    kw = fm[fm.index("\\begin{keyword}") + 15:fm.index("\\end{keyword}")].strip().replace(" \\sep ", "; ")
    body = src[src.index("\\end{frontmatter}") + len("\\end{frontmatter}"):]
    body = body.replace("\\appendix", "\\begin{APPENDICES}").replace("\\bibliographystyle", "\\end{APPENDICES}\n\\bibliographystyle")
    body = re.sub(r"\\begin\{adjustbox\}\{[^}]*\}\n?|\n?\\end\{adjustbox\}", "", body)
    body = body.replace("\\todo{", "\\pending{")
    return (f"\\TITLE{{{title}}}\n\\AUTHOR{{{author}}}\n\\AFF{{{aff}, {email}}}\n\\ABSTRACT{{{abstract}}}\n"
            f"\\KEYWORDS{{{kw}}}\n\\maketitle\n{body}")


def main():
    src = open(os.path.join(HERE, "dss_manuscript.tex"), encoding="utf-8").read()
    bib = M.parse_bib(os.path.join(HERE, "dss_refs.bib"))
    body, refs = M.convert(to_informs_macros(src), bib)
    refs_tex = re.sub(r"\*([^*]+)\*", r"\\emph{\1}", refs).replace("&", "\\&")
    out = os.path.join(HERE, "dss_manuscript.docx")
    with tempfile.TemporaryDirectory() as td:
        bt = os.path.join(td, "body.tex")
        open(bt, "w", encoding="utf-8").write("\\documentclass{article}\\begin{document}\n" + body
                                              + "\n\\section*{References}\n\n" + refs_tex + "\n\\end{document}\n")
        subprocess.run(["pandoc", bt, "-f", "latex", "-o", out], check=True)
    print("saved", out)


if __name__ == "__main__":
    main()
