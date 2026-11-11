#!/bin/bash
# Build the Word manuscript: main text + appendix, equations as Word equations.
#   manuscript.docx            with author and draft line
#   manuscript_anonymous.docx  for blind review (no author, no date line)
cd "$(dirname "$0")"
pandoc main.md appendix.md -o manuscript.docx --reference-doc=ref.docx --resource-path=. -f markdown+tex_math_dollars+pipe_tables
pandoc main.md appendix.md -o manuscript_anonymous.docx --reference-doc=ref.docx --resource-path=. -f markdown+tex_math_dollars+pipe_tables -M author= -M date=
for f in manuscript.docx manuscript_anonymous.docx; do zip -d "$f" "*/" >/dev/null 2>&1 || true; done
