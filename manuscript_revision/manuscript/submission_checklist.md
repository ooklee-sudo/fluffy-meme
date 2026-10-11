# Before submitting `manuscript_misq.docx`

The Word file (`manuscript_misq.docx`) is double-spaced Times New Roman 12, with equations as native Word equations. Open it in Word to check the equations and tables; the preview I could run here cannot display Word equations. The Markdown source (`manuscript_misq.md`) is what the file was built from.

## Must verify against the journal's current instructions
- Abstract length, total word limit, reference style, and whether the manuscript must be anonymized in the file properties and the title page (this draft has no author names).
- The journal's policy on use of generative AI in preparing a manuscript, and any disclosure statement it requires. I drafted this text with an AI assistant; if the policy asks for disclosure, include it.
- Article type. The draft is written as a Research Article. If you submit as a theory-led essay, the empirical section can be shortened.

## Citations to complete
- Dell'Acqua et al. (2026): volume, issue and pages were not confirmed; the search showed an Organization Science listing (37(2)) and an earlier working paper.
- Muennighoff et al. (2023), OctoPack: the full author list is abbreviated.
- Liu et al. (2026) and Mujahid and Imran (2026) are preprints; check whether they have since been published.
- Peng et al. (2023) and METR (2025) are cited as working papers/reports.
- Every other reference was copied from your original manuscript's reference list; entries I added were checked on public pages, but check them again before submission.

## Statements that depend on material I have not seen
- "Proofs of Results 4 and 8 are in the Online Appendix", and the claim that sign results of the strategic extension hold more generally (Online Appendix): these refer to your original appendix. Make sure those proofs are complete.
- Section 4 uses the formalization I wrote (utility, game, equilibrium). Read it as your own model and confirm each step.

## Empirical claims to reproduce before submission
- Every number in Section 5 comes from the scripts in `../empirical/` and `../empirical/satd/` and the outputs saved beside them. Rerun them if the data sources are refreshed.
- Section 5.5 describes an experiment that has not been run; the manuscript says so. Keep that wording unless the experiment is completed.
- The data sources have their own terms (AIDev: CC BY 4.0; CommitPackFT: MIT; GH Archive). Cite them in the data statement and check whether the journal requires a data-availability statement.

## Not in the file
- Title page with author details and acknowledgments (for the non-anonymized version), funding and conflict-of-interest statements, and the Online Appendix.

# Management Science version (`manuscript_ms.docx`)

Same content as the other version, with these differences: the front line names Management Science (Department of Information Systems); the audience sentence in the Introduction addresses economics and management readers as well as information systems; Data and Code Availability, Funding and Conflict of Interest sections are added before the references (the last two are placeholders); and page numbers are in the footer. The reference style is the INFORMS style that your original manuscript already used.

Check in the journal's current instructions:
- Its data and code disclosure requirements, and whether the code and data must be deposited at submission or only on acceptance. The statement in the file promises a public deposit; add the repository and DOI once it exists.
- Abstract and length limits, and whether proofs should go in an electronic companion instead of Appendix A.
- The department and the type of paper it expects. Papers that rest on assumed behavioral parameters will be read for the novelty of the economic insight, so the argument that frame shift is a structural claim (Section 3.1) deserves the most attention before submission.
