# Build scripts for the ISR v4 submission files

Regenerate the Word files (needs Node and `npm install` in this folder, which installs `docx`):

    npm install
    node lc2.js ../ISR_manuscript_v4.docx ../ISR_online_appendix_v4.docx     (manuscript and online appendix)
    node cover2.js ../ISR_cover_letter_v4.docx                               (cover letter)
    python title_page.py                                                     (title page; run in this folder, writes ISR_title_page_v4.docx; needs python-docx)

- `lib.js` holds the document styles and helpers; `fig/` the two figures; `prompts.json` the prompt texts quoted in Appendix A.
- `lc2.js` reads the wordings from `../../wordings.json` (absolute path in the script: change the line `const WD = ...` if the repository is elsewhere).
- Checked on the day of submission: the body XML (`word/document.xml`) of the manuscript, appendix and cover letter produced by these scripts is byte-identical to the submitted v4 files. The title page was not re-checked.
- Edit the text in `lc2.js` / `cover2.js`, not in the .docx, so that the two stay in step.
