# Handoff: where the project stands (2026-10-19)

Project: "Does Generative AI Help Inventors Innovate?" (target: Information Systems Research).
Branch: `ccr-b3faa909-a8e15y` of `ooklee-sudo/fluffy-meme`. Start a new session on this branch and read this file, `pilot/PILOT_PLAN.md`, and `pilot/validation_results.md`.

## Done
- Proposal v2 (`GenAI_Inventor_Proposal_v2.docx`) and a pre-results ISR manuscript draft (`GenAI_Inventor_ISR_Manuscript_Draft.docx`). Results sections are placeholders; no numbers were invented.
- Pilot code in `pilot/`: chunk extraction, OpenRouter rewrite generation (budget-capped, resumable), text normalization, group-level mixture estimator, detector validation, summaries. All have offline tests.
- Machine reference corpus: 7,423 rewrites (≈$67) from six complete generators (llama-4-maverick, qwen3.8-flash, deepseek-v4.1-flash, gemini-3.8-flash, gpt-6.1-sol, claude-opus-5.5) plus 235 from mistral-small (mistral was rate-limited and left out).
- Detector validation on real 2021 text: see `validation_results.md`. Key finding: LLM-drafted/expanded text is detected (alpha-hat ≈ 0.93); LLM-polished human text is not (≈ 0.07, same as the human baseline).

## Files that are NOT in the repo (kept on the user's computer, Downloads\...\pilot)
`rewrites.jsonl` (full raw outputs and manifest), `rewrites_slim.jsonl.gz` (15.9 MB, normalized text), `chunks.jsonl`, `desc_2021_sample.tsv.gz`, `brf_2021_sample.tsv.gz`. A new session must have these re-uploaded; session upload folders do not persist.

## Latest result (prevalence by year)
Detectable LLM-drafted share: 2021 baseline alpha-hat 0.02; 2024 ≈ 0%; 2025 ≈ 0.8% (CI 0.1–1.5%), with a suggestive uptick in the last quarter of 2025 (≈2–3%). Details in `prevalence_results.md`. Gate (a) is not met on data through 2025; the project needs later data (2026 publications) or a reframing.

## Raw XML plan (in progress)
Download weekly files from https://data.uspto.gov/bulkdata/datasets/appxml (see PILOT_PLAN.md for the list of weeks), run `peek_xml.py` on one to verify the structure, then `xml_to_tsv.py` per week.

## Weekly XML result (ipa261008)
No agent/law-firm element in application publications (0%); 94% organizational applicants; 55% non-US applicants; filing date and CPC always present. See PILOT_PLAN.md.

## Latest result
Within-group, 2026 weeks exceed the 2021 baseline (all nine differences positive, CIs exclude 0): pooled calibrated share ≈3–6%, US ≈6–9.5%, non-US ≈1–2%. See weeks_results_v1.md and PILOT_PLAN.md for cautions (single baseline week, no CPC control, group-level noise).

## Next steps
0. (Done) 2024 and 2025 samples analyzed. The 2025 long-text file is listed on page 1 of the portal (newest files first).
1. Download and sample `pg_detail_desc_text_{2019,2023,2024,2025}` from the USPTO Open Data Portal (`pvpgpubtxt`; login + API key), shrink with `pilot/sample_tsv.py --n 3000`, upload the four `desc_*_sample.tsv.gz` files.
2. Estimate the LLM-drafted share by year/quarter (RQ1 prevalence) and check the 2019/2021 placebo. This is gate criterion (a). Interpret by publication year (18-month lag; data end 2025-09-30).
3. Calibrate alpha-hat to true share (attenuation seen at high shares) and enlarge the null sample (FPR was 3.3% at n=400).
4. Gate criteria still open: (b) non-U.S./machine-translated false positives (needs applicant country), (c) agent/law-firm field availability in the application data.
5. Decide whether to add a seventh generator (mistral replacement, ≈$1) or leave as is.
6. If the gate passes, build the drafting-unit panel and run the DID design from the proposal; fill the [RESULTS] sections of the manuscript.

## Housekeeping
- The OpenRouter key was pasted into the chat twice: delete it at https://openrouter.ai/keys and create a new key with a spending limit. Also replace it wherever else it is used.
- Never paste keys into chat; set `OPENROUTER_API_KEY` as an environment variable.
- Remaining OpenRouter credit was about $95–100 after the rewrite run.
- `--budget` in `rewrite_corpus.py` is cumulative over the output file.
