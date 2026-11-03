# Submission notes for AI_and_Law_manuscript.docx

## What was written, and what is still yours to complete
- Declarations: funding, competing interests, author contributions and the data/code DOI are placeholders. The existing Zenodo deposit covers only the first experiment; deposit the scripts and results in `followup/` again and insert the new DOI.
- Title page, cover letter and author details are not in this file.
- AI-use statement: Springer Nature requires documented use of a large language model (outside plain copy-editing) in the Methods section or a suitable alternative part, and does not accept an LLM as an author. A draft statement is in the Declarations; confirm or correct it, and add a sentence to Section 5 if the journal asks for it there. Check the live policy before submitting.

## Format assumptions (not confirmed against the journal page)
The journal's instructions page could not be opened from here (login redirect). The file follows common Springer Nature conventions: numbered headings, abstract under 250 words (247), 4-6 keywords (6), author-year references in a Springer-like style, declarations at the end, tables with captions above and figures with captions below. Check the live instructions for: reference style, whether the review is blind, abstract and keyword rules, figure file format, and article type and length.

## References: what was and was not checked in this work
Checked during this work (existence and venue): Cohen et al. 2024 (TACL 12:283-298); Zhong et al. 2023 (EMNLP, pp. 15686-15702); Moffatt v. Air Canada 2024 BCCRT 149; the two Australian OPC guidance notes (URLs as listed).
Written from memory and NOT checked: every other reference, including page numbers and author lists (Alchourron et al. 1985; De Cao et al. 2021; Dhingra et al. 2022; French 1999; Hu et al. 2022; Kirkpatrick et al. 2017; Lazaridou et al. 2021; Meng et al. 2022, 2023; Mitchell et al. 2022; Palmirani and Vitali 2011; Rolnick et al. 2019; Wang et al. 2024; Yang et al. 2024; Yao et al. 2023; Zheng et al. 2023). Verify each against the publisher record before submission, and correct or remove any that do not match.

## Facts in the text that depend on the data files
All tables are generated from `followup/results/*.json` by `paper/build_manuscript.py`; figures by `paper/make_figures.py`. The 70M figure and table use `resA/B/C.json` (some cells have two seeds). Statements about the 1.5B and 3B runs refer to one seed.

## Points a reviewer is likely to raise
27 amended provisions from two Acts; one model family; forced-choice evaluation; editors run without tuning and with reduced MEMIT/ROME statistics; the currency expression was written after the first experiments; extracted passages not proofread exhaustively. The Limitations section says so; do not weaken it.

## Revision after the critique (this version)
- Legal mapping corrected: saving/transitional provisions preserve old law for earlier cases and do not protect unamended text; retention constraints are presented as a technical device with no drafting counterpart (Table 1, Sections 2.1, 7.4). Point-in-time validity added as Section 7.5 and as a limitation.
- Added: RAG and in-context diagnosis (Section 6.6, Table 9; base vs launch models), expanded "Why update weights?" (7.2), Section 2.4 on retrieval and legal QA, hard-alternative control metric and change in control margin (Tables 6–7).
- Claims softened: formula is an accounting identity; listing and arithmetic non-propagation are credited to Zhong et al. 2023 and Cohen et al. 2024.
- Controls: 66 curated (24 removed, criteria in `real_law/curate_controls.py`); "not proofread" statement replaced.
- "Alchórron" corrected to "Alchourrón".
- Experiments complete: MEMIT/ROME re-run with corrected subject spans and 10,000 covariance samples (3 seeds); real-amendment fine-tuning has 3 seeds (`results/reallaw_v2.json`, merged with `reallaw_v2_s3.json`).
- Still open: (1) Declarations placeholders and deposit update (add the new scripts, `real_law/real_fact_bank_v2.json`, `results/`); (2) verify references added in this version: Governatori et al. 2005 (title and pages), Palmirani and Brighi 2006 (pages), Magesh et al. 2025 (issue and pages), Dahl et al. 2024, Lewis et al. 2020, and check the descriptions of what Dahl and Magesh found; (3) the analysis scripts `analyze_*.py` still read the old result files.
