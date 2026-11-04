# Practitioner cases for LLM API retirement / migration (compiled 2026-11-04)

Sources were read in full from the arXiv PDFs, downloaded 2026-11-04 and converted with pdftotext.
Page numbers are PDF pages, checked with a per-page text search.
Quotes are verbatim. The only change is rejoining words that pdftotext hyphenated at line breaks.
Original typos are kept and marked [sic].

---------------------------------------------------------------------
## Paper 1. Casey, Roberts, Sim, Beaver (2026), arXiv:2604.27082v1

**Verification:** Confirmed.
- arXiv metadata title: "When Your LLM Reaches End-of-Life: A Framework for Confident Model Migration in Production Systems".
- Authors: Emma Casey, David Roberts, David Sim, Ian Beaver.
- Submitted 29 Apr 2026 (v1 only), cs.AI, 12 pp.
- Affiliation: "Verint Systems Inc, Melville, NY, USA" (p.1).
- The user's title differs only in capitalisation. There is no author or title mismatch.
- No venue is listed on arXiv, so treat it as a preprint, not peer-reviewed.

### Company and domain
- Company: Verint Systems (from the affiliation). The paper itself says "our company" (p.1).
- "Our company currently offers over a dozen enterprise products using LLMs for various features." (p.1, §1)
- Hosting: "Often the LLMs used are proprietary or too large to self-host and are instead hosted by third parties such as Azure, Amazon Web Services, or Google Cloud Platform." (p.1, §1)
  - The hosting platform for the case system is NOT stated explicitly.
  - Indirect hint only: the paper used "Amazon Bedrock's Prompt Management suite" (p.5, §7) and candidates include AWS Nova. Do not assert Bedrock.

### System and scale
- "This system averages 5.3M chats per month across 6 global regions, supports multiple languages, and has been in commercial usage for over two years primarily supporting contact center agents during customer interactions for dozens of enterprise companies." (p.1, §1)
- "The system requiring migration is a question-answering service shared across several customer-support products. Given a user query and a ranked set of source texts, it returns a natural-language answer with citations." (p.2, §3)
- Output format: "The model is required to return a structured XML response, including a flag indicating when it cannot answer the question, enabling a clean "I don't know" (IDK) output." (p.2, §3)
- Constraints: "Maintaining output quality for current enterprise customers, ensuring adequate speed across deployed geographic regions, and not substantially increasing LLM cost are the primary constraints of model choice." (p.1, §1)

### Models migrated, and dates
- From: "as its underlying LLM—Claude 3 Haiku—approaches end-of-life, we must migrate to an alternative model without degrading performance." (p.2, §3)
- Candidates: "Gemma 3 (27B), Anthropic Claude 4.5 Haiku and 3.5 Sonnet, AWS Nova Micro, Lite, Lite 2 and Pro; OpenAI GPT-OSS 20B and 120B, Qwen3-32B and 235B" (p.3, §5)
- To: "we select Nova 2 Lite in situations where file processing is needed, and Qwen3-32B with reasoning disabled as the primary LLM to migrate this system to." (p.5, §6.4)
- Expected outcome: "This choice offers a quality of service that will be equal to or better than the current system while offering full regional coverage at reduced financial cost and response time improvement." (p.5, §6.4)
  - The wording "will be" is a projection. The paper reports no post-deployment results.
- **No dates are given.** The paper states no deprecation notice date, retirement date, migration start or end date, or go-live date.
- Migration frequency: "This proprietary LLM deprecation and migration cycle has been happening roughly every 12 months and impacts every product built on the deprecated model, meaning a target model must be identified and migrated to for all impacted products before the LLM is removed from the hosting platform." (p.1, §1)
- Window pressure: "an inefficient and time-consuming manual process is prohibitively expensive given the short migration windows, frequency of migrations, and breadth of impacted products." (p.1, §1). The length of the window is not quantified.

### Elapsed time, team size and effort
- **None reported.** The paper gives no elapsed time, person-hours, team size, or dollar cost.
- Human labelling: "A group of three assessors judged these collaboratively and without access to the metrics' judgments on them." (p.4, §5.1)
- Appendix C adds: "we had three separate developers mark a series of LLM responses." (p.9, App. C)
- Effort is a stated goal but is not measured: "our goal is to minimize the time spent experimenting with alternative prompts in order to reduce both migration cost and overall timeline." (p.2–3, §3)
- Reuse lever: "The manual evaluation only needs to be done once for a given test set, and can then be reused for other metrics and models." (p.3, §4.1)
- Multi-model outcome: "To cover all regional requirements, more than one LLM may need to be supported." (p.3, §4 step 6). This is the multi-sourcing / portfolio angle.

### Evaluation approach
- Framework steps 1–6 (p.3, §4):
  1. Vetted candidates
  2. Eliminate models that fail the output schema
  3. Count IDK responses and compare correctness with the baseline
  4. Eliminate models with significant increases in IDK rate or latency, or decreases in correctness
  5. Style check, and prompt fixes if needed
  6. Choose a subset covering regions and modality, on price and quality
- Test sets: "We evaluated against 200 examples from the HotpotQA test set, 200 from the SQuAD test set, and 51 samples from an internal test set representing natural language questions about a set of customer-service-style documents." (p.3–4, §5.1)
- Manual calibration sample: "we randomly selected 66 HotpotQA examples, 55 from the internal test set and 25 from SQuAD to evaluate manually to assess the metrics." (p.4, §5.1). That is 146 examples labelled by hand.
  - SQuAD was later discarded "as we had found insufficient true-negatives to effectively calibrate the metrics." (p.4, §6.1)
- Metrics: RAGAS correctness, faithfulness and relevance, plus their own llm_correctness and new_correctness. The judge prompts "were run against Claude 4 Sonnet." (p.4, §5.2)
  - Best metric: "new_correctness was the metric most closely aligned with actual correctness on both test sets" (p.4, §6.1)
  - Table 1 (p.4): TPR 0.905 and FPR 0.375 on basic; TPR 0.883 and FPR 0.100 on hotpot.
- Statistics: confusion matrices, then Beta posteriors for TPR and FPR ("uninformative Bayesian priors"), then Monte Carlo sampling, then a normal approximation justified by Bernstein–von Mises, giving 90% CIs on the correctness difference (App. A, pp.7–8).
- Style checks use a substring match for phrases such as "according to" (p.3, §4.2).
- Latency: median response time (Table 5, p.10).

### Cost figures
- **No currency figures.** Table 3 (p.6) gives only relative "Price Tier" values:
  - Claude 3 Haiku: Middle
  - Claude 4.5 Haiku: High
  - Nova Pro: High
  - Nova 2 Lite: Middle
  - Qwen3-32B: Low
  - Qwen3-235B: Middle
- Table 3 also gives regional availability outside the USA.
- Candidates were also filtered on "operating cost limits" (p.2, §3).
- Some candidates were rejected because "they required excessive dedicated hosting costs to maintain data residency in non-USA regions." (p.3, §5)
- No evaluation, labelling or token costs are reported.

### What reduced effort
- Qualitative only, and nothing is quantified.
  - Calibrated automated metrics replace large-scale manual review.
  - Labelling is reusable across models.
  - The baseline prompt carried over unchanged.
- "Based on this data, the baseline prompt generalizes surprisingly well across models." (p.5, §7.1)
- "Experiments with manual, automated, and machine-learned prompt adaptation showed no statistically significant improvements over the baseline prompt" (p.6, §9)
- "the framework offers an efficient and principled method for enterprise LLM migration, providing dependable quality assurance while limiting evaluation cost." (p.6, §9)

### Failures and regressions
- "The second step of our framework eliminated both OpenAI GPT-OSS models as they were unable to consistently generate output following the XML schema required by the product." (p.4, §6)
  - Qwen3-32B had the same schema problem: "quickly resolved by adding examples of correctly formatted output to the prompt" (p.4, §6)
- Nova Micro, Nova Lite and Gemma 3 27B were eliminated because their correctness CIs included negative values (p.4, §6.2).
- Claude 3.5 Sonnet was eliminated on latency: "1.73s and 1.89s median response times ... compared to 1.19s and 1.06s for the baseline" (p.4, §6.3)
- Qwen3-32B reasoning mode "increasing bad style occurrences from 2.1% to 7.5% on the basic test set" (p.4, §6.3)
- DSPy/MIPROv2 prompts "substantially increased IDK rates" on the basic set, and the gains did not replicate on HotpotQA (p.5, §7.1).
- Correctness of the selected models versus Claude 3 Haiku, from Table 2 (p.5), mean difference in percentage points with 90% CI:

  | Model | basic | hotpot |
  |---|---|---|
  | Nova 2 Lite | +4.85 [0.173, 10.1] | +4.75 [0.692, 9.04] |
  | Qwen3-32B (no reasoning) | +9.79 [4.16, 16.17] | +6.39 [2.66, 10.29] |

### Lessons stated by the authors
- "reliable model selection requires aligned evaluation metrics rather than blind reliance on standard QA benchmarks." (p.6, §9)
- Calibration "identified substantial variability in their accuracy, with only new_correctness consistently matching human judgment." (p.6, §9)
- Future work: "Integrating our comparison framework into a continuous evaluation system would allow monitoring of drift, assessment of vendor updates and efficient evaluation of candidate models" (p.6, §8)
- Also future work: "enable faster migrations to new LLMs in the future" (p.6, §8)
- Limitations (p.6, §10):
  - Only two test sets
  - English only
  - "relatively small test sets"
  - A single judge model

### Use for the real-options model
- **Migration frequency:** about 1 per 12 months per model ("roughly every 12 months", p.1). The burden multiplies across "over a dozen enterprise products".
- **φ and person-weeks:** cannot be estimated from this paper, which has no time or effort data.
- **Proxy for flexibility value:** the baseline prompt transferred without change. The reusable labelled set (146 examples, labelled once) and the automated metric are the main effort levers.
- **Multi-model / switching option:** the result was a two-model portfolio chosen for regional coverage.

---------------------------------------------------------------------
## Paper 2. Tripathi, Nema, Halder, Qiao, Jindal (2025), arXiv:2507.05573v1

**Verification:** Confirmed.
- Title: "Prompt Migration: Stabilizing GenAI Applications with Evolving Large Language Models".
- Authors: Shivani Tripathi, Pushpanjali Nema, Aditya Halder, Shi Qiao, Alekh Jindal.
- Submitted 8 Jul 2025 (v1 only), cs.DB, 9 pp.
- Affiliation: "Tursio Inc." (p.1).
- No venue is listed on arXiv, so treat it as a preprint, not peer-reviewed.

### Company, domain and scale
- Tursio enterprise search: natural language turned into SQL-operator trees over SQL Server, Azure SQL, Fabric, Snowflake, Databricks, BigQuery, Teradata and Cassandra (p.3, §2.3).
- "Tursio was originally built on GPT-4-32k in 2023" (p.3, §2.3)
- "Over the years, Tursio has been deployed to over 100 instances running thousands of queries per day. Each query triggers an analysis with 33 LLM calls on average, including calls to basic foundational model, broader foundational model, and reasoning model. Together, these calls have a footprint of roughly 6,000 input tokens and 1,000 output tokens per query. Likewise, the training process incurs over 1,000 LLM calls per run." (p.3, §2.3)
- Number of users: not stated.

### Models, notice and deprecation dates
- "Later, on June 6th, 2024, GPT-4-32k was deprecated with a shutdown date of June 6th, 2025 (i.e., a window of one year). Tursio migrated to GPT-4.5-preview, which was in turn deprecated on April 14th, 2025, with a shutdown date of July 14th, 2025 (i.e., a window of just three months). Currently, Tursio runs on GPT-4.1" (p.1, §1)
- Path: GPT-4-32k → GPT-4.5-preview → GPT-4.1. These are OpenAI models; whether they were served through the Azure OpenAI or OpenAI API is not stated.
- Notice windows stated: 12 months, then 3 months.
- The paper does NOT give the dates when Tursio itself switched models.

### Elapsed time and effort (the key quantitative claim)
- "At Tursio, our first migration effort last [sic] couple of months end-to-end, but the above structured framework reduces it down to a couple of weeks." (p.7, §4.4)
  - Imprecise wording: "couple of months" and "couple of weeks".
  - No person-count, FTE or hours are given.
  - Read literally, about 2 months against about 2 weeks implies roughly a 4x reduction in elapsed time, i.e. φ ≈ 0.75 effort saved. This is our inference, not the authors'.
  - It is calendar time, not person-time.
  - It also conflates learning effects (first versus later migration) with the framework, so it is not a clean measurement of flexibility.
- Team: only "We thank the Tursio engineering and products teams for deligently [sic] handling LLM migrations" (p.9, Acknowledgments). There is no size.
- "Migration effort. Even though we came up with a representative migration testbed, the migration effort is still significant. Moreover, newer models require more structured and verbose prompts, that grew from a few lines to a page in our migration effort. All this requires careful thinking and inspection from the developers, as well as tooling to cope up with the mushrooming models." (p.8, §5)
- Testbed cost: "Crafting meaningful queries that have good coverage requires good understanding of the underlying dataset, which is a time-taking process." It "still requires manual inspection for sanity and meaningfulness." (p.7, §4.3)

### Evaluation approach
- An existing regression suite ("a large test suite", p.3, §3.1). Its size is not stated.
- Pass rates, Table 1 (p.3):

  | Model | Tests passed |
  |---|---|
  | GPT-4-32k | 100% |
  | GPT-4.1 | 98% |
  | GPT-4.5-preview | 97.3% |

- "Using new prompts with GPT-4.1 resulted in 100% tests results, i.e., full correction of the earlier issues with both precision and consistency." (p.6, §4.2)
- Migration testbed: "We have derived 110 questions from hundreds of production workloads processed by Tursio into the migration testbed." (p.7, §4.3). The questions are split into easy, moderate and hard tiers.
- Process (p.7, §4.4): a loop of run testbed → fix failing prompts using the vendor prompting guide → rerun → regression tests.
- No statistical method is used (pass/fail only), and there is no repeated sampling or CI.

### Cost figures
- No dollar, evaluation, labelling or token-cost figures are given.
- The token footprint per query (about 6k in, 1k out, 33 calls) is the only basis for a cost estimate, and that requires assumed prices.

### Failures and regressions (pp.3–4, §3.2)
- Common to both new models:
  - Missing ORDER BY / GROUP BY
  - Non-existent column names
  - Semantic misreads (TIMES_LATE)
  - Missing inferred filters
- GPT-4.1 only:
  - Needs more explicit prompts
  - Misses implicit ORDER BY for "over time" and "last three months"
  - Mixes up column names and values
- GPT-4.5-preview: "faced all the above issues" plus:
  - "Incorrect output formats, leading to internal parser errors"
  - Free-text info messages
  - Redundant ORDER BY
- "...leading to inconsistencies in the application behavior and breaking the CI/CD pipelines." (p.3, §3.1)

### Lessons stated by the authors (p.8, §5)
- Flexible versus structured prompting: GPT-4.1 and 4.5 need explicit, structured prompts.
- Example format matters: XML is better than JSON or plain text.
- Migration effort is still significant.
- Prompt lifecycle management.
- The testbed "decouples model exploration and evaluation from application development" (AI engineers versus application engineers).
- "Prompt management skills".
- "LLMs are getting smarter in some ways, but dumber in others."
- Future work: use LLMs to automate the prompt-rewrite steps (p.7, §4.4).

### Accuracy caveats inside the paper
- p.4, §3.3 states "GPT-4's context window is limited to 2k to 8k tokens". This is inaccurate for GPT-4-32k (32k), the model they used. Avoid citing it.
- p.9: "more than 30% of this paper has been generated with the help of LLMs".
- The paper is an informal "war story" (the authors' own term, p.1).

### Use for the real-options model
- **Notice windows:** 12 months and 3 months (OpenAI). This is direct evidence of shrinking or variable notice periods.
- **Frequency:** two forced migrations between June 2024 and July 2025.
- **φ:** the only usable number is the elapsed-time ratio of about 2 months to about 2 weeks. It is calendar time, the "couple" wording is imprecise, and the before/after comparison is not controlled.
  - If used, present it as "order-of-magnitude consistent with φ ≥ 0.5", not as a point estimate.
- **Person-weeks:** cannot be derived because there is no headcount.

---------------------------------------------------------------------
## Search for other documented enterprise cases (about 15 minutes)

**Result: no solid first-party enterprise case with concrete effort or cost numbers was found.** Candidates that were checked and rejected:

1. tianpan.co, "The Model Deprecation Cliff" (2026-04-13): https://tianpan.co/blog/2026-04-13-the-model-deprecation-cliff
   - Claims a healthcare provider moving from Gemini 1.5 to 2.5 Flash "consumed over 400 engineering hours" and that token use rose 5x.
   - **No source is cited.** A search found no primary source.
   - The same post misquotes Tursio's pass rates as 95.1% and 97.3% (the paper says 98% and 97.3%).
   - Not usable.
2. AWS ML Blog, "Improve Amazon Nova migration performance with data-aware prompt optimization": https://aws.amazon.com/blogs/machine-learning/improve-amazon-nova-migration-performance-with-data-aware-prompt-optimization/
   - This is the reference cited by Casey et al.
   - Vendor demo on the public XSum data, migrating Claude 3 Haiku to Nova Lite. As reported by the search tool (not re-verified on the page), accuracy went from 77.75% to 83.25% on 80 samples.
   - Not an enterprise case, and it has no effort figures.
3. Thematic, "The Upgrade Trap" (Jan 2026): https://getthematic.com/insights/llm-upgrade-trap
   - First-party, but it gives no models, numbers or effort.
4. Xu & Wu, arXiv:2608.17719 (Aug 2026), "What Aggregate Scores Miss: Measuring Item-Level Regressions in Commercial LLM API Migrations".
   - Benchmark study on public items, with no enterprise effort data.
   - Possibly useful as a citation that aggregate gains hide item-level regressions: up to 8.3% of items reliably regress on edges with net gains.
   - Abstract only was checked.
5. Others were dev.to and personal posts ("an afternoon plus a day of eval") and vendor or opinion posts (ibl.ai, Vertesia, softwareseni, callsphere). They are anecdotal or unsourced. Not usable.
