# Submission checklist (read first)

## Files in this package
| File | Purpose |
|---|---|
| `title_page.docx` | Separate title page with authors and declarations (upload as title page, not to reviewers) |
| `manuscript_blinded.docx` | Blinded manuscript (no author information); 3 tables embedded |
| `online_appendix.docx` | Web (online) appendix |
| `cover_letter.docx` | Cover letter |
| `replication_package.zip` | Code, prompts, IDs, LLM outputs, human validation labels, README |

## You must complete before submitting (nothing here was invented for you)
- [ ] Author names, affiliations, ORCID, corresponding author e-mail (title page, cover letter)
- [ ] Funding, conflicts of interest, ethics/IRB status, author contributions, acknowledgments
- [ ] Repository link (anonymized for review, permanent after acceptance) in manuscript, title page, online appendix, README
- [ ] Online appendix: confirm whether the coders completed the qualification quiz and how independence was ensured
- [ ] Confirm the generative-AI statement matches your actual use and the journal's current policy
- [ ] Decide whether the replication package may include the optional merged analysis table (it contains Amazon rating and vote counts; the dataset's license terms are not stated on its page)
- [ ] Optional: suggested reviewers
- [ ] English language check by a native speaker or editing service

## Verify against the journal before submitting
- Current Replication Corner limits (4,000 words incl. abstract/text/references; at most 3 tables or figures; web appendix 2,000 words), regular-article limit (5,000), abstract limit (150), and whether the Corner still exists: https://link.springer.com/journal/11002/submission-guidelines (I could not open this page; limits come from search results).
- Whether the journal wants a separate declarations section inside the manuscript, line numbers, or double spacing.
- Whether the review is double-blind (the manuscript is already free of author information).

## Known limitations stated in the manuscript (do not remove)
Not preregistered (pilot first); product labels are LLM-generated and validated on 100 products only; goods-classification decision rules were set after the calibration round; category-level coding in the main specification; our LLMs differ from those used in the original; experiment not replicated.

## Pending analysis (not yet in the manuscript)
A misclassification sensitivity analysis for the product-level labels (EM; `misclass_sensitivity.py`) was still running when this package was built. If you want to include it, add it as an online-appendix section and one sentence in the Results; the package script already contains the method.

## Checked in this package
- Abstract 125 words (limit 150); main text with references about 2,960 words (limit 4,000 by search-result guidance); 3 tables.
- All reference details were checked against Crossref (volume, issue, pages, DOI); the Kübler et al. and WZH page numbers match.
- All numbers in the manuscript were compared with the analysis logs and CSV outputs.
