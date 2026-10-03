# ISR submission record

Journal: *Information Systems Research* (INFORMS), double-anonymous review.
Manuscript: "When Do LLM Operators Skip Verification? Goal Visibility, Reasoning, and Framing in an Automated Maintenance Environment"
Submission date: **TO FILL IN (date the ScholarOne submission was completed)**
Manuscript ID assigned by the system: **TO FILL IN**
Handling Senior Editor / Associate Editor nominated, if any: **TO FILL IN**

## Files in this repository that correspond to the submission

These are the repository versions, all generated from the scripts below. If the uploaded files were edited afterwards in Word (page layout, metadata, anonymisation), the uploaded copies are the ones of record; keep them with this note.

| File | Bytes | SHA-256 (first 16) | Last commit touching it |
|---|---|---|---|
| ISR_manuscript_v4.docx | 227,992 | b0c89eadd7651a17 | 358b41c |
| ISR_online_appendix_v4.docx | 21,192 | 524bbd614b8f3cce | 358b41c |
| ISR_cover_letter_v4.docx | 12,501 | 090dd6194d4a608e | f289df6 |
| ISR_title_page_v4.docx | 37,557 | 88e5b4b4d7424fa9 | 505d86b |

Git tag `isr-submission-v4` marks commit 505d86b, which contains all four files as listed.
Earlier versions (v1 to v3) remain in this folder and are not part of the submission.

## State of the work at submission

- Main text 32 pages; 37 pages including references and tables (author's measurement in Word). Abstract 299 words (limit 300).
- Study 6 (small-model screening of seven models) is in Section 10; Tables F1 to F3 are in Appendix F. GPT-5-nano and Qwen3-14B are reported as excluded invalid runs (parse failures above 5%), not as floors; they were not rerun.
- Screening rule for Study 6, committed before the runs: pass if pooled skip is at least 5% at 3 turns left (1,440 first choices); every candidate run is reported.
- The 16-wording expansion was not run on small open models; the manuscript states this and why. The partial output of the stopped open-model run was not analysed.
- Wording set: `loss_chasing/wordings.json`, SHA-256 prefix d90e7efc164b816b (16 wordings per frame).
- The scale and deference study (MISQ) is not cited or mentioned in the manuscript or cover letter.

## Do not change while under review

- Do not add analyses or runs that depart from the pre-committed Study 6 rule; they would be hard to explain in a revision.
- Do not post a preprint without checking the current ISR policy on double-anonymous review.
- Revision work should start from tag `isr-submission-v4`.

## Generators

The scripts that produced the four files are in `build/` (see `build/README.md`). The manuscript, appendix and cover-letter scripts were rerun and reproduce the submitted v4 files' body XML byte for byte; the title-page script (`build/title_page.py`) was not re-checked.
