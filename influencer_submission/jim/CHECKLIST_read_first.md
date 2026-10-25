# Journal of Interactive Marketing (AMA journals) submission checklist

Source: SAGE/AMA submission guidelines for JIM (checked 25 Oct 2026 from the SAGE PDF and the AMA guidelines pages). Submit through the JIM ScholarOne site linked on https://www.ama.org/submission-guidelines-american-marketing-association-journals/ (choose "New Submission").

## Files to upload
| File | Upload as |
|---|---|
| `manuscript_jim.docx` | Main document (page 1: title, abstract, keywords; text from page 2; references on their own page; tables and figures in the text) |
| `title_page.docx` | Title page (author details, acknowledgments with the AI statement, statements and declarations) |
| `Web_Appendix.pdf` | Web Appendix (single PDF; page numbers start at 1; contains the required disclosure) |
| `cover_letter.docx` | Cover letter |
| `figures/Figure_1.pdf`, `Figure_2.pdf` (and PNG) | Keep for acceptance (the AMA asks for editable originals then); the figures are already embedded in the main document |

## How the files meet the AMA rules (verified against the guidelines)
- 12-point Times New Roman, double-spaced text (tables may be single-spaced), 1-inch margins, no page numbers or headers/footers in the main document; 38 pages including references, tables, and figures (limit 50; the Web Appendix does not count).
- Title 14 words (limit 25); abstract 182 words, third person (limit 200); 7 keywords (limit 8).
- Headings unnumbered (centered bold; bold italic; italic), at most three levels; no "Section N" cross-references; equations numbered in parentheses and cited as "Equation 1".
- In-text citations use author-year without commas, semicolon-separated and alphabetical; up to three authors named. The reference list is in AMA style with full first names, alphabetical.
- Tables placed in the text with takeaway titles, notes labeled "Notes:", and standard errors for the estimates; inference for simulation output uses SEs and bootstrap confidence intervals.
- Figures embedded in the text in grayscale (Arial-metric font), axes labeled with headline-style capitalization, legends in sentence case, error bars explained in the notes.
- Web Appendix tables are numbered W1 to W3; sections labeled "Web Appendix A/B/C", each starting on a new page.
- Double-anonymized: no author names in the main document or Web Appendix; document properties have no author name.
- Generative-AI use is identified in the main document (Experiments and Results, Setup) and in the acknowledgments on the title page.

## What you must do
- [ ] Title page: author details, funding, conflicts of interest, ethics wording, repository link, acknowledgments. Confirm the AI statement is accurate.
- [ ] Upload an anonymized copy of `influencer_replication/` (code and results) and give its link on the title page (not in the main document). Remove author names from the files and commit history.
- [ ] Answer the submission system's questions about prior or concurrent submission truthfully; withdraw anything under review elsewhere first.
- [ ] Check the full first names in the reference list: they were taken from Crossref and arXiv records; nine entries were completed manually from my knowledge (Bakshy et al., Gilbert, Hadar and Russell, Horton, Simon, Zhao et al., Park et al., Kempe et al., Brand et al.). Also check the journal titles and page ranges against the AMA reference examples.
- [ ] Read the AMA Research Transparency Policy and Policy for Reporting Results: exact p-values are required throughout. The simulation analysis reports SEs and bootstrap intervals instead of p-values; SAGraph z statistics are far beyond conventional thresholds (reported as p < .001 in the note). Add p-values to Tables 6 and 7 if the editors ask.
- [ ] The journal asks for decimals without a leading zero for quantities that cannot exceed 1 (applied to P(C > D)); elasticity values can exceed 1 and keep the zero.

## Substantive points to know before submitting
- All simulation numbers come from the shipped code (`influencer_replication/run_all.sh`). The earlier numbers in previous drafts came from code that no longer exists. Compared with those drafts, the reversal points are higher (about 0.3 for discounted reach and downside risk, 0.4 to 0.5 for final reach) and concentrated seeding leads from the first hour.
- For final reach the margin between the estimate and the reversal range is small for the largest accounts (0.57 [0.49, 0.65]) and one campaign (0.52), and a bias of about 0.16 would remove it; the paper says so.
- Fit risk: JIM publishes research on interactive and social media marketing; the paper is simulation-centered with a descriptive empirical estimate. Reviewers are likely to ask for calibration of the simulator and for a causal handle on the elasticity.
