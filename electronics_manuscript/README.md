# MDPI *Electronics* manuscript

Converted from the TMIS submission (TMIS-09-2026-0123) to the MDPI *Electronics* format.

| File | What it is |
| --- | --- |
| `manuscript.tex` | LaTeX source using the official MDPI class (`Definitions/`) |
| `manuscript.pdf` | Compiled PDF |
| `manuscript.docx` | Word version (built from the LaTeX by `make_docx.py`) |
| `fig1.png` | Figure 1 |

References are numbered in order of first citation, in MDPI (ACS-style) format.

## Rebuild

```bash
pdflatex manuscript && pdflatex manuscript   # PDF (run twice for numbering)
python3 make_docx.py                          # Word file; needs pandoc and the .aux from the PDF build
```
