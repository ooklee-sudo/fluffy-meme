# Submission package: IEEE Transactions on Artificial Intelligence

Submission site: https://ieee.atyponrex.com/journal/tai-ieee  (double-anonymous review)

## Files to upload

| File | Upload as | Notes |
|---|---|---|
| `manuscript.pdf` | Main manuscript (two-column IEEE PDF) | 7 pages; no author, affiliation, contact, funding or external link. |
| `figures/Fig1_decomposition.pdf`, `figures/Fig2_reasoning.pdf` (PNG copies at 300 dpi) | Figures, one file each | Also embedded in the PDF. |
| `supplementary_material.pdf` | Supplementary material | Proofs, item bank, prompts, models, full results, robustness, added experiments (Appendices A to H). Anonymous. |
| `S1_replication_code.zip` | Supplementary material (code and data) | Item bank, generator, audit, runner, analysis, results, README. Anonymous. |
| `S2_raw_model_outputs.zip` | Supplementary material (data) | Raw model outputs: 176,400 main-run calls, 45,600 added calls, 1,450 pilot calls. Unzip inside `replication_code/` of S1 (it adds only `raw/`). |
| `manuscript_source.tex` | Only if the site asks for source files | Needs `figs/` from the repository (`deference/paper/`) and IEEEtran. |


## Entered in the web form (not in any file)

- **Manuscript type:** Original Research Regular Manuscript (10 pages normal limit; this paper has 7).
- **Title** (13 words; limit 15): Deference or Noise? A Baseline-Corrected Protocol for Auditing Stance Sensitivity in LLM Reviewers
- **Running head:** Deference or Noise? (19 characters; limit 25)
- **Keywords (3 to 6, chosen from the site's list):** the paper's own index terms are: Large language models, sycophancy, evaluation methodology, reliability, AI-assisted decision making, benchmark.. Pick the closest entries from the dropdown.
- **Authors, affiliation, e-mail, ORCID (required for every author), funding:** enter here only; they must not appear in any uploaded file.

## Abstract (234 words; limit 250)

Organizations increasingly ask language models to review a decision after a requester has already stated a preference. Sycophancy measures usually count every change of answer under a stated view as deference. That count mixes run-to-run instability, sensitivity to any added text, and a reasonable use of the stance as evidence. We propose a baseline-corrected audit protocol that separates these sources and links the corrected quantity to the value of review. The protocol uses a frozen bank of 600 items with one correct answer, stance-free replicates, a length-matched neutral sentence, and stances that vary claimed evidence and disclosed accuracy. Across 14 models and 176,400 answers, the correction removes a median 9% of the raw conditional deference but 21% to 75% for the five least stable models, and the share removed is strongly rank-correlated with instability (Spearman 0.90). Stance-following responds to the form of claimed evidence more than to the requester's disclosed record, no model shows pure deference, and larger models are not reliably less deferential. Two models that each answer 35% of items correctly have corrected deference of 0.06 and 0.67. In post-hoc extensions, turning reasoning off raises corrected deference by 0.34 to 0.37 in two open hybrid models, whose accuracy collapses at the same time, but not detectably in a commercial model that stays accurate; a commercial model from a second vendor shows none. Rankings of AI reviewers by accuracy alone can therefore mislead.

## Impact statement (142 words; required 100 to 150)

Many organizations now let AI systems double-check decisions that a manager, clerk or engineer has already leaned toward. The check is worthless if the AI simply agrees with whoever asks. Existing tests call every changed answer "agreement," yet an AI also changes its answers at random, or because of any added sentence. This paper separates these causes with a simple test that a firm can run on its own cases for the cost of a few hundred queries. Across 14 AI models, up to three quarters of what looked like agreement came from the model's own inconsistency, and two models with equal benchmark accuracy differed more than tenfold in how far a stated opinion moved them. Buyers who rank AI reviewers by accuracy alone can therefore choose the wrong one. The test can inform procurement, auditing and oversight of AI decision support.

## AI-use disclosure (IEEE policy)

The manuscript's Acknowledgments section discloses that AI-generated text was used in drafting and editing and cites the AI system as reference [AI coding assistant]. Keep that section and the reference.

## Checks done on the files

- Abstract, impact statement, title and running head are within the stated limits.
- No author name, affiliation, e-mail, funding source or external link in `manuscript.pdf`, `supplementary_material.pdf`, or the two zip files; PDF metadata has no author field. (The only person-name match is a co-author of a cited paper.)
- The zip files were unpacked in a clean directory and the analyses re-run from the raw outputs.

## Before you submit

1. Read the impact statement and the acknowledgments once more; they are yours to approve.
2. Check the reference list and the in-text citations against the originals. Six of the 14 references were verified online; the others were taken from the original manuscript or from memory.
3. If you share the code with reviewers through a repository, use an anonymous one; the guidelines ask for no links that reveal the authors.
