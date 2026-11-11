#!/bin/bash
# Build the Word manuscript: main text + appendix, equations as Word equations.
cd "$(dirname "$0")"
pandoc main.md appendix.md -o manuscript.docx --reference-doc=ref.docx --resource-path=. -f markdown+tex_math_dollars+pipe_tables
