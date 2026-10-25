# ISR Submission Compliance Checklist and Self-Assessment

Based on the ISR Submission Guidelines supplied by the author. Status: **Ready** / **To do** / **Decision needed**.

## A. Manuscript requirements
| Requirement | Status | Notes |
|---|---|---|
| Type: Research Article ("pure theory" or "applies existing theory" are allowed; strong grounding in theory) | Ready | Classified as a theory article with empirical illustration; stated in Section 1 ("Article type and audience"). |
| Intended audience stated prominently | Ready | Added to Section 1. |
| Length: at most 32 pages of text and 38 pages in all (references, appendices, tables, figures); proofs may go to an online appendix | Ready, with room | Built as 11 pt, double-spaced, 1-inch margins (`build_submission.py`): **23 pages in all, 19 before the references** (after the literature review was expanded). About 13 pages of text and 15 in total are free. See "Use of the page budget" below. |
| Format: double-spaced, at least 11 pt, 1-inch margins | Ready for review; **To do** for final | The submission PDF must follow the INFORMS LaTeX style files (Author Portal). Conversion not yet done. |
| Double-anonymous review: no author names, institutions, acknowledgments; neutral self-citation | Ready in the blinded build; **To do** at submission | The build removes the author line and replaces file paths with "replication package (anonymized for review)". Before upload: check PDF metadata, file names, and that no repository, user name or institutional URL appears. |
| Mathematical notation: numbered equations flush right, no more complex than necessary | **To do** | Key equations are currently unnumbered displayed or inline text; number them in the LaTeX conversion and keep proofs short (move long proofs to the e-companion). |
| Abstract of at most 300 words | Ready | 251 words. |
| Keywords describing theoretical and methodological orientation, chosen from the ScholarOne list | **To do** | Current keywords are free text; map them to the ScholarOne list when submitting. |
| References alphabetical, INFORMS style, in-text (Author Year) | **Partly done; To do** | Each entry was checked against web sources (`reference_verification.md`); an incorrect author list (Xia et al. 2023) was fixed and unconfirmed volumes or pages were omitted. **Still compare every entry with the originals, and complete the omitted volume/page details.** |
| Footnotes numbered | Ready | None used. |
| Figures: color converts to black and white in print | **Decision needed** | Figure 1 uses a perceptual colormap that remains legible in grayscale; consider a grayscale-safe version. |

## B. Cover letter and policies
| Requirement | Status | Notes |
|---|---|---|
| Contribution statement under 500 words in the cover letter (papers without it do not move forward) | Ready | Draft in `contribution_statement.md` (492 words including headings). |
| Paper provenance: disclose overlap with other work, prior submission, and working-paper posting | **To do** | Confirm no overlap or prior submission; disclose any preprint posting. |
| Data provenance: certify the right to use public data; upload permission documentation if required | **To do** | See `data_provenance.md`: two GitHub repositories (RepairBench, SWE-bench submissions) had no license file; contact the maintainers and record the reply before submitting. Also check the terms of the model API and the three model licenses. |
| Ethics: no human-subject data | Ready | The behavioral experiment was removed and has not been run. |
| ORCID for the submitting author | **To do** | Required in ScholarOne Step 3. |
| Funding statement | **To do** | Step 5. |

## C. ScholarOne steps that need the author's decisions
- Step 1: manuscript type (Research Article) and **two preferred Senior Editors**; running header.
- Step 4: **five preferred reviewers (at least two ERB members)**, two Associate Editors, two Senior Editors, without conflicts of interest (same institution, major professor or student, co-authors in the last four years).
- ISR has **no reject-and-resubmit option**, and rejected manuscripts cannot be resubmitted to ISR. Submit only when the paper is ready; consider the pre-submission editing services on the Author Portal and a colleague read.

## D. After acceptance (prepare later)
Practice- and policy-oriented abstract of at most 200 words ("Research Spotlights"), 75-word author biographies, copyright transfer form, editorial checklist, optional media form; online appendix (e-companion) as PDF; final Word or LaTeX files.

## E. Self-assessment against ISR's evaluation criteria
| Criterion | Assessment | Main risk and what would strengthen it |
|---|---|---|
| Phenomenon of salient interest to IS | Moderate to strong | AI-assisted maintenance and pay-per-use AI services sit in IT sourcing, governance and human–AI work design. Connect explicitly to IS concerns beyond software engineering. |
| Robust connections to the literature and relevant theories | **Moderate, improved** | Section 2 now covers IT contracting (ISR and Management Science papers), agency and multitask incentives, human–AI collaboration, pricing of information goods, and states the theoretical positioning and testable implications. **Gap:** no peer-reviewed IS paper on usage-based or outcome-based pricing of IT services was found in our searches; search ISR, MISQ, Management Science directly before submission.
| Theoretical model appropriate and compelling | Moderate | Tractable and general in the heterogeneity distribution, but assumes conditionally independent attempts, binary verification, symmetric vendors, and linear pay-per-use contracts; several results are numerical. |
| Empirical methods appropriate, valid, well executed | Moderate | Public benchmark data validate the premises; costs are calibrated from public sources but not measured on a firm, and the verification cost v is a judgement. A field study would raise this. |
| Analyses done competently | Moderate to strong | Proofs and numerical checks agree; many results come from simulation grids. |
| Results interesting | Moderate to strong | The incentive rent of sequential search and the role of differentiation are the most distinctive. |
| Conclusions compelling | Moderate | The welfare advantage of success fees holds when H/v is at least about 30 and weakens when each attempt needs manual review (Section 5.4). State this scope in the abstract and conclusion. |

## F. Use of the page budget
The compact manuscript uses 15 of 32 text pages. ISR articles are usually fuller. Candidate additions, in order of value for the criteria above: (1) done: an IS-grounded literature review and theory positioning (Section 2, about 1,000 words); remaining: a direct search for pricing papers; (2) the intuition and a worked example for the incentive rent; (3) the private-quality and competition results with their full tables; (4) proof sketches in the text and full proofs in the e-companion; (5) a robustness subsection (the earlier extended version contains these analyses). Do not exceed 32 text pages.
