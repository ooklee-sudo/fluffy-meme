# ISR submission checklist

**Source of the requirements.** The authors pasted the official ISR "Submission Guidelines" text on 2026-10-28; everything marked *(official)* comes from that text. The linked policy pages (general submission guidelines, authorship, copyright and plagiarism, ethical behavior, ORCID, rights and permissions), the INFORMS reference-style PDF, the mathematical-notation PDF, the LaTeX style files, and any policy on generative AI were not provided and have **not** been read. Items marked *(not checked)* must be checked by the authors.

## Requirements and how the review files meet them

| Requirement *(official)* | Status |
| --- | --- |
| Article type: Research Article (theoretical and/or empirical examination of a significant IS phenomenon, strong grounding in theory, intended audience stated prominently) | Prepared as a Research Article. The audience is stated at the end of the introduction. **Whether the theoretical grounding is "strong" enough for ISR is the main risk; see below.** |
| Length: at most 32 pages of text and 38 pages including everything | `ISR_manuscript.pdf` has 26 pages including references (LibreOffice rendering; recheck in the final software). Proofs and supplementary evidence are in `ISR_online_appendix` (3 pages). |
| Format: double-spaced (abstract, references, footnotes included), font at least 11 pt, one-inch margins | 12-pt Times New Roman, double spacing, one-inch margins. Tables are single-spaced at 11 pt. |
| Double-anonymous review: remove names, institutions, acknowledgments; write so that identity is not revealed; also submit text without the title page | No author information in `ISR_manuscript` or the online appendix; document properties are blank. Title page is separate (`TITLE_PAGE.md`). Re-check after edits, and do not link a non-anonymous repository. |
| Mathematical notation: expressions no more complex than necessary; numbered equations in parentheses, flush right | Equations are inline and unnumbered. Number the key equations (the probability model, the cost) if the authors prefer; the notation PDF has not been read. |
| Contribution statement in the cover letter, fewer than 500 words: (a) contribution to the literature, (b) influence on practice, policy, or society and the broader discourse. Papers without it do not move forward. | `COVER_LETTER.md`, 398 words. |
| Paper provenance and data provenance statements | Placeholders in the cover letter for the authors to complete. **Data provenance: licenses must be checked, especially the FActScore annotation release.** |
| Abstract of at most 300 words, understandable to general readers | 272 words. |
| Keywords beneath the abstract; chosen from the ScholarOne list | Keywords are beneath the abstract; **replace them with terms from the ScholarOne list at submission.** |
| References alphabetical; in-text citations as (Norman 1977) or Norman (1977), per INFORMS style | In-text citations use this form and the list is alphabetical. The entries follow the pattern seen in a published ISR article's reference list (`Surname Initials (Year) Title. Journal abbrev. Vol(Issue):pages`), supplied by the authors; the official INFORMS reference-style PDF was not read, so journal abbreviations may need adjustment. One entry (Fügener et al. 2022) was confirmed against that list. |
| Footnotes numbered; avoid when possible | None used. |
| Figures | None. |
| ScholarOne steps: type, title, running header, abstract, two preferred Senior Editors; keywords; all authors and institutions and the submitting author's ORCID iD; five preferred reviewers (at least two Editorial Review Board members), two preferred Associate Editors and two preferred Senior Editors, with no conflicts of interest; cover letter and funding; ethical certifications; upload files; review the generated PDF | Author tasks. None of these can be prepared from the repository. |

## Before submitting (authors must do)
1. Resolve every `[AUTHORS ...]` marker in the manuscript (nine remain), above all: verify every reference against its source and complete author lists and venues, and check the figures taken from Si et al. against the published tables.
2. Complete the cover letter's provenance, data-provenance, conflict-of-interest, funding, and ethics statements, and the title page.
3. Check the INFORMS policy on generative-AI use and disclose AI assistance as it requires. **This manuscript was prepared with substantial AI assistance.** The relevant policy page was not provided.
4. Read the manuscript critically as an author. The prose is a draft; the claims, caveats, and interpretation must be yours. In particular, check every number against `RESULTS.md` and `MODEL.md`.
5. Decide whether to run a human-verifier study (the predictions in Section 8.7 are testable) or to keep the current framing, in which the parameters of human verification come from the literature.

## Candid assessment against the journal's stated criteria
- *"Is the phenomenon of salient interest to the IS community?"* Plausibly yes (verification of AI-generated content).
- *"Are the connections to the literature and relevant theories robust?"* **Weak at present.** The IS literature is represented by a handful of references (human–AI collaboration, task–technology fit, costly state verification). A reviewer may find the grounding in IS theory thin. Strengthening Section 2 with a systematic reading of recent ISR and MIS Quarterly work on AI-assisted decision making and on IT governance is the most valuable remaining edit.
- *"Is the theoretical model appropriate and compelling?"* The analytical results use standard tools (knapsack-type thresholds, Schur-convexity, envelope arguments). Their value lies in the connection to the data, not in novelty of technique.
- *"Are the empirical methods appropriate, valid, and well-executed?"* The main evidence rests on public human annotations and offline evaluation. There is no experiment with human verifiers; the verifier parameters come from one published study with a different task.
- Whether this fits ISR's scope and bar cannot be judged from here. The guidelines say rejection decisions are generally final and a rejected paper cannot be resubmitted, so a conference or another venue first may be prudent.
