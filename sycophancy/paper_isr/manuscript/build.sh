#!/bin/bash
# Build the ISR submission files (US Letter, 1-inch margins, double-spaced, page numbers):
#   manuscript.docx                 main text with author line (for internal review)
#   manuscript_complete.docx        complete text with title page (ISR version a)
#   manuscript_anonymous.docx       main text for double-anonymous review (no author, no date line)
#   online_appendix_anonymous.docx  online appendix (proofs, estimation details, prompts, field data)
cd "$(dirname "$0")"
F="-f markdown+tex_math_dollars+pipe_tables --reference-doc=ref.docx --resource-path=."
pandoc main.md -o manuscript.docx $F
pandoc title_page.md main.md -o manuscript_complete.docx $F -M author= -M date=
pandoc main.md -o manuscript_anonymous.docx $F -M author= -M date=
pandoc appendix.md -o online_appendix_anonymous.docx $F -M title="Online Appendix: When Should an AI Reviewer Back Down? Pushback, Verification, and Deference in AI-Assisted Code Review"
python3 setpage.py manuscript.docx manuscript_complete.docx manuscript_anonymous.docx online_appendix_anonymous.docx
pandoc cover_letter.md -o cover_letter.docx --reference-doc=ref.docx
python3 setpage.py cover_letter.docx
for f in manuscript.docx manuscript_complete.docx manuscript_anonymous.docx online_appendix_anonymous.docx cover_letter.docx; do zip -d "$f" "*/" >/dev/null 2>&1 || true; done
