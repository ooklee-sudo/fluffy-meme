# IEEE Transactions on Reliability: submission package

| File | Use |
| --- | --- |
| `manuscript.pdf` | Main manuscript (IEEEtran journal format, 12 pages as compiled here) |
| `manuscript_IEEE_TR.docx` | The same manuscript in the IEEE Word template (built by `../word/build_docx.py`) |
| `source/manuscript.tex`, `source/figs/` | LaTeX source and figures (upload if the system asks for source files) |
| `cover_letter.pdf`, `cover_letter.tex` | Cover letter; fill in the date |
| `supplementary.zip` | Code, per-seed results, pilot results, figures for the measurement study |
| `author_biography.md` | Template; the author must complete it |
| `suggested_reviewers.md` | Candidates only; verify before use |

## Before you upload (author must do these)
1. **Check the generative-AI disclosure.** The Acknowledgment now says that an AI assistant
   (Claude, Anthropic) was used to edit and restructure the language and to write and run
   the experiment and analysis code, and that the author reviewed all AI-generated content
   and takes responsibility. Only you can confirm this is accurate. If AI was also used for
   the original draft or for other parts, extend the statement; IEEE may ask for the tool
   version and how it was used.
2. **Fill the placeholders** in `manuscript.tex`: manuscript received/revised dates in
   the author footnote, and the DOI of the deposited code and data in Data Availability.
   Deposit `supplementary.zip` contents in a public archive (Zenodo or similar) first.
3. **Review the author-specific statements**: funding (currently "no specific grant"),
   CRediT, competing interests.
4. **Previous submission.** The paper was desk-rejected by another journal before
   review. The cover letter says it is not under consideration elsewhere, which is
   true. Some journals ask about prior submissions in the form; answer truthfully.
5. **Verify the reference list.** Six IEEE Transactions on Reliability papers were added to
   the introduction (Nakagawa and Yasui 1987; Liu and Huang 2010; Rafiee, Feng, and Coit
   2015; Bao, Sun, and Trivedi 2005; Grottke et al. 2006; Ning et al. 2016). Their titles,
   authors, volumes, pages, and dates were checked against Crossref, but I did not read
   the full papers, so check that the one-line descriptions in the introduction match them.
   The other entries were carried over from the earlier draft and were not checked,
   in particular Arts et al. (2025), Williams et al. (2026), and the arXiv entries.
6. **Check the journal's current Information for Authors** for abstract length (the
   abstract here is 220 words), page limit and overlength charges, index terms (IEEE
   taxonomy), and figure requirements.
7. Complete the biography and photo (needed at acceptance, not at submission).

## Known limitations to be aware of (all stated in Section IX of the paper)
* One 70M model, synthetic drift, two maintenance epochs per seed, no closed-loop
  validation of the scheduling policy.
* Repair settings were fixed on one pilot seed and fitted the repaired facts unevenly
  on the reported seeds (mean fit 0.65 for the edit, 0.85 for full fine-tuning).
* The localized edit needs a replay constraint, and its cost advantage over full
  fine-tuning depends on the cost accounting.

## Rebuild
`cd source && pdflatex manuscript && pdflatex manuscript` (needs IEEEtran, in
texlive-publishers). Experiments: see `supplementary/code_and_results/README.md`.

## Word version
`manuscript_IEEE_TR.docx` uses the IEEE template styles. Equations are Word equations;
they were checked by schema validation and by converting them back to LaTeX, but the
build environment could not draw them, so open the file in Word and look at every
equation and table once. The page header still contains the template line
"REPLACE THIS LINE WITH YOUR MANUSCRIPT ID NUMBER"; replace it with the ID the system
assigns, or delete the text. Manuscript dates in the first-page footnote are placeholders.
