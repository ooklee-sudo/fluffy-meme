"""Typeset a preview PDF of ijds_manuscript.tex without the INFORMS class files.

The informs4 class and informs2014 bibliography style are distributed by INFORMS and are not installed here, so this
script swaps in the article class with stand-ins for the INFORMS front-matter macros and a natbib author-year style.
The layout is therefore not the journal's; the text, equations, tables and references are the same.

Usage:  python make_ijds_preview.py      (needs pdflatex and bibtex; writes ijds_manuscript_preview.pdf)
"""
import os
import shutil
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

SHIM = r"""\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{setspace}\onehalfspacing
\newcommand{\OneAndAHalfSpacedXI}{}
\newcommand{\TheoremsNumberedThrough}{}
\newcommand{\EquationsNumberedThrough}{}
\newcommand{\MANUSCRIPTNO}[1]{}
\newcommand{\RUNAUTHOR}[1]{}
\newcommand{\RUNTITLE}[1]{}
\newcommand{\TITLE}[1]{\title{#1}}
\newcommand{\ARTICLEAUTHORS}[1]{#1}
\newcommand{\AUTHOR}[1]{\def\theauthorname{#1}}
\newcommand{\AFF}[1]{\author{\theauthorname\\ \small #1}}
\newcommand{\EMAIL}[1]{#1}
\newcommand{\ABSTRACT}[1]{\gdef\theabstract{#1}}
\newcommand{\KEYWORDS}[1]{\gdef\thekeywords{#1}}
\newcommand{\HISTORY}[1]{}
\let\oldmaketitle\maketitle
\renewcommand{\maketitle}{\oldmaketitle\begin{abstract}\theabstract\par\smallskip\noindent\textit{Key words:} \thekeywords\end{abstract}}
\newenvironment{APPENDICES}{\appendix}{}
\newcommand{\ACKNOWLEDGMENT}[1]{\section*{Acknowledgments}#1}
\newtheorem{proposition}{Proposition}
"""


def main():
    src = open(os.path.join(HERE, "ijds_manuscript.tex"), encoding="utf-8").read()
    start = src.index("\\usepackage{natbib}")
    body = SHIM + src[start:]
    body = body.replace("\\makeatletter\n\\@ifundefined{proposition}{\\newtheorem{proposition}{Proposition}}{}\n\\makeatother\n", "")
    body = body.replace("\\bibliographystyle{informs2014}", "\\bibliographystyle{plainnat}")
    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td, "p.tex"), "w", encoding="utf-8").write(body)
        shutil.copy(os.path.join(HERE, "ijds_refs.bib"), td)
        run = lambda *c: subprocess.run(c, cwd=td, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        run("pdflatex", "-interaction=nonstopmode", "p.tex")
        run("bibtex", "p")
        run("pdflatex", "-interaction=nonstopmode", "p.tex")
        r = run("pdflatex", "-interaction=nonstopmode", "p.tex")
        warn = [l for l in r.stdout.splitlines() if "undefined" in l.lower() or l.startswith("!")]
        print("\n".join(warn[:20]) or "no undefined references or errors")
        shutil.copy(os.path.join(td, "p.pdf"), os.path.join(HERE, "ijds_manuscript_preview.pdf"))
    print("saved ijds_manuscript_preview.pdf")


if __name__ == "__main__":
    main()
