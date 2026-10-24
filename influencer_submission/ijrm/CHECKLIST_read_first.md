# IJRM submission checklist (based on the journal's Guide for Authors you pasted)

## Files
| File | Upload as |
|---|---|
| `manuscript_ijrm.docx` | Anonymized manuscript (title, abstract, keywords, text, AI declaration, references, tables, and Appendices A and B in one file; page numbers added) |
| `title_page.docx` | Separate title page (author details, acknowledgments, competing interests, funding, CRediT) |
| `highlights_ijrm.docx` | Highlights (file name includes "highlights"; 5 bullets, each at most 85 characters) |
| `cover_letter.docx` | Cover letter (about 300 words) |
| Figures 1 and 2 | Separate files named Figure_1, Figure_2 (not yet inserted; the text has placeholders) |
| Code and data archive | Deposit in a repository and give the link (IJRM requires this or a statement of why not) |

## How this version meets the guide
- Length: at most 50 pages including everything. My build (double-spaced text, tables single-spaced, no figures) is about 35 pages with appendices; two figures will add a few pages. Check the final Word page count.
- Abstract about 147 words (limit 250); 6 keywords (limit 6); highlights 3 to 5 bullets within 85 characters.
- Double anonymized: no author names, acknowledgments, or funding in the manuscript. Make sure the code archive is also anonymized (no names in file properties, README, or commit history).
- Cover letter: short, no funding, declarations, or reviewer suggestions (the guide says these are requested separately). It states the fit with the journal's aims and the novelty.
- Equations use exp(...) instead of powers of e and are numbered; tables are editable text with captions and notes below.
- Inclusive language: gendered pronouns removed.
- Reference style: IJRM accepts any consistent style at submission and applies APA 7 after acceptance, so the INFORMS-style list was kept. Check that the in-text citations and list match.
- Generative-AI declaration: a section with the required title is placed before the reference list. I drafted it with Claude (Anthropic) as the tool used to restructure and edit the text; **you must confirm and edit it** to match what you actually did and take responsibility for the content.

## Authors must complete
- [ ] Author details, affiliations, corresponding author address, acknowledgments, funding, CRediT statement (title page)
- [ ] Competing-interests declarations tool and uploaded Word file
- [ ] Figures 1 and 2 as separate files
- [ ] Repository link for code and results; dataset citation for SAGraph
- [ ] Submission-declaration questions (not published, not under consideration elsewhere): answer truthfully
- [ ] Optional: Associate Editor or ERB suggestions in the cover letter
- [ ] Verify arXiv ids and 2026 preprints in the reference list (copied from the earlier manuscript, not re-verified)

## Fit risk (read this)
The Aims and Scope say that "replications and minor methodological or theoretical improvements will generally not be publishable" and that the editors favor research that is novel and path-breaking. The paper is positioned as identifying a new source of error in a fast-growing practice, not as an incremental fix. The likely reviewer objections are the uncalibrated rule-based simulator, the descriptive (non-causal) elasticity, and the small simulated network; the Discussion states these limits, and you should consider adding the recommended robustness checks before submitting.
