# IEEE Transactions on Reliability: submission package

| File | Use |
| --- | --- |
| `manuscript.pdf` | Main manuscript (IEEEtran journal format, 12 pages as compiled here) |
| `source/manuscript.tex`, `source/figs/` | LaTeX source and figures (upload if the system asks for source files) |
| `cover_letter.pdf`, `cover_letter.tex` | Cover letter; fill in the date |
| `supplementary.zip` | Code, per-seed results, pilot results, figures for the measurement study |
| `author_biography.md` | Template; the author must complete it |
| `suggested_reviewers.md` | Candidates only; verify before use |

## Before you upload (author must do these)
1. **Disclose generative-AI use.** IEEE requires that substantive use of AI tools for
   text, figures, or code be disclosed, normally in the Acknowledgment. The manuscript
   language, the experiment code, and the data analysis were produced with an AI
   assistant, so add a statement of the form: "The author used [tool] to assist with
   [language editing / code for the experiments] and reviewed and edited all output;
   the author takes full responsibility for the content." Check the current IEEE policy
   for exact wording. The manuscript does not contain this sentence yet.
2. **Fill the placeholders** in `manuscript.tex`: manuscript received/revised dates in
   the author footnote, and the DOI of the deposited code and data in Data Availability.
   Deposit `supplementary.zip` contents in a public archive (Zenodo or similar) first.
3. **Review the author-specific statements**: funding (currently "no specific grant"),
   CRediT, competing interests.
4. **Previous submission.** The paper was desk-rejected by another journal before
   review. The cover letter says it is not under consideration elsewhere, which is
   true. Some journals ask about prior submissions in the form; answer truthfully.
5. **Verify the reference list.** Entries were carried over from the earlier draft and
   not checked against the sources, in particular Arts et al. (2025), Williams et al.
   (2026), and the arXiv entries. Add recent IEEE Transactions on Reliability papers on
   imperfect maintenance or condition-based maintenance to the introduction and related
   work; editors expect the paper to connect to the journal's own literature.
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
