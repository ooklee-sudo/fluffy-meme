# Data Provenance Table (ISR requires certification of the right to use data and publish results)

| Source | What is used | Terms found at retrieval | Status and action |
|---|---|---|---|
| RepairBench results, GitHub `ASSERT-KTH/repairbench` (commit e43cb67, 26 Oct 2025) | Counts of test-passing samples per bug and model; token usage. No patches are redistributed. | No LICENSE file in the repository; README asks users to cite the paper. | Aggregate statistics only. **Action: ask the maintainers for written permission or confirm terms before submission, and cite as requested.** |
| SWE-bench submissions, GitHub `SWE-bench/experiments` | Resolved lists per submission; pass@k and cost statements quoted from submission READMEs. | No LICENSE file at the repository root in the checkout used. | Aggregates and short quotations. **Action: confirm terms with the maintainers; cite each README's authors.** |
| HumanEvalPack (HumanEvalFix, Python), Hugging Face `bigcode/humanevalpack` | 164 bug-fixing tasks and their tests. | Dataset tag: MIT. | OK to use; cite the dataset paper. |
| Model samples for HumanEvalFix (Llama-3.2-3B-Instruct, Ministral-8B, Gemma-3-4B-it) via the OpenRouter API | Pass/fail and token counts only; generated code was not stored. | Terms of OpenRouter and of each model's license. | **Action: read the current terms of use of the API and of the three model licenses and record that the use is analysis of aggregate pass rates.** |
| OpenRouter public model list (prices per million tokens), accessed 25 Oct 2026 | List prices for cost calibration. | Public API listing. | Cite with access date; prices change. |
| BLS Occupational Outlook Handbook, software developers (May 2025 median pay $64.44 per hour; $135,980 per year) | Wage for H. | U.S. government data. | Read from bls.gov directly. |
| BLS Employer Costs for Employee Compensation, private industry (benefits 29.5% of compensation, June 2022) | Loaded-cost multiplier. | U.S. government data. | **Action: open the BLS release directly (retrieved only through a search summary) and update to the latest quarter.** |
| SWE-bench Verified time-to-fix annotation (as summarized by Epoch AI; METR's check) | Bucket shares 39%, 52%, 8%, 3 tasks. | Published web article and paper. | **Action: cite the primary annotation source (OpenAI's SWE-bench Verified release) and METR (arXiv:2503.14499).** |
| Published results (Brown et al. 2024; DeepSWE-Preview, Cortexa and other READMEs) | A few pass@k and cost numbers. | Published. | Cite precisely. |

No human-subject data are used or collected.
