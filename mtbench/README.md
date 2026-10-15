# MT-Bench judge vs human check

`mt_bench_ledger.py` compares the GPT-4 pairwise judge (J) with expert human majority votes (G) on
`lmsys/mt_bench_human_judgments` (CC-BY-4.0). Download the two parquet files from the Hugging Face
dataset, then `python mt_bench_ledger.py human.parquet gpt4.parquet results.json` (needs pandas, pyarrow).
Results of the run are in `results.json`. Canary classes = reasoning, math, coding (verifiable answers).

`mt_bench_bestofn.py` selects, among n randomly drawn candidate answers (n = 2..6), the one GPT-4 prefers,
and scores it against a random incumbent from the same set using the human votes. Output: `bestofn_results.json`.
Caveat: draws reuse the same ~1,200 human-judged pairs, so evaluations are not independent.
