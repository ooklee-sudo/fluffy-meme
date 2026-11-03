# Small set of real statutory amendments (UK), version 1

27 verified amendment records from two UK Acts, built by comparing the text in force immediately before each amendment with the current text on legislation.gov.uk (retrieved 2026-11-03). Each record carries the site's own amendment note (instrument and commencement date).

Contains public sector information published on legislation.gov.uk (Crown copyright), which the site makes available under the Open Government Licence v3.0. Check the site's terms before redistributing the quoted text. This is research data, not legal advice.

## Contents of `real_amendments_v1.json`

| Cluster | Provisions | Change | Commencement | Instrument (from the site's note) |
|---|---|---|---|---|
| `ERA_time_limit_3_to_6_months` | Employment Rights Act 1996, ss. 11, 23, 34, 48, 51, 54, 57, 60, 63, 70, 111, 188 (12 provisions) | time limit for presenting a complaint: "three" -> "six" months | 2026-10-01 | Employment Rights Act 2025 (c. 36), s. 159(3), Sch. 12; S.I. 2026/954 |
| `ERA_money_limits_2026` | Employment Rights Act 1996, ss. 31, 186, 227 (3 provisions) | £39 -> £41 (s. 31); £719 -> £751 (ss. 186, 227) | 2026-04-06 | The Employment Rights (Increase of Limits) Order 2026 (S.I. 2026/310) |
| `CA2006_size_thresholds_2025` | Companies Act 2006, ss. 382, 383, 465, 466 (12 values) | size thresholds (turnover, balance sheet; net and gross), e.g. £10.2m -> £15m, £5.1m -> £7.5m | 2025-04-06 | The Companies (Accounts and Reports) (Amendment and Transitional Provision) Regulations 2024 (S.I. 2024/1303) |

Each record: `act`, `section`, `title`, `cluster`, `kind`, `old` (value in force just before), `new`, `old_enacted` (value in the 1996/2006 text, kept only for reference), `before_date`, `text_before`, `text_after` (about 22 words of statutory text around the change), `source_url`, `amending_notes`.

### Dependency structure present in the data

- **One change, many provisions.** The three-to-six-months change appears in 12 separate provisions made by one amending schedule: a real analogue of consequential amendments.
- **Net and gross thresholds.** In ss. 383 and 466 each "gross" threshold is about 1.2 times the "net" one before and after the amendment (10.2 -> 12.2, 5.1 -> 6.1, 36 -> 43.2, 18 -> 21.6, then 15 -> 18, 7.5 -> 9, 54 -> 64, 27 -> 32; the new gross values are rounded). This is an observed relationship in the text, not a rule asserted by the Act.

## How it was built

1. `crawl.py <act> <first> <last>`: fetches the enacted and current text of each section and lists sections in which a number or spelled-out number changed.
2. `build_dataset.py`: keeps changes of periods and amounts (cross-reference renumbering is filtered out), attaches section titles and the site's amendment notes.
3. `make_v1.py`: replaces the enacted text by the text in force the day before commencement, so that `old` is the value actually replaced by the amendment (the enacted value is often several amendments older).

Ranges scanned: Employment Rights Act 1996 ss. 1-235; Companies Act 2006 ss. 380-480; Housing Act 1988 ss. 1-45; Insolvency Act 1986 ss. 1-130. The last two produced only renumbering changes, no period or amount amendments. Raw crawler output and cached pages are not included (`.gitignore`).

## Limits (read before using)

- Only 3 clusters from 2 Acts; the ranges scanned were chosen by hand, so this is not a sample of UK legislation.
- Text comes from an automated diff and may include table-cell or sub-clause fragments; the quotations in `text_before` and `text_after` were not manually proofread, and values for each cluster were checked only against the site's amendment notes.
- "Current" means the latest revised version shown by the site on the retrieval date. Extent (England and Wales, Scotland, Northern Ireland), prospective provisions and savings or transitional rules were not examined.
- The 2026 amendments postdate the training data of most language models; that is why they are useful for tests, and also why they cannot be cross-checked against model knowledge.
