# MT-Bench judge vs human check

`mt_bench_ledger.py` compares the GPT-4 pairwise judge (J) with expert human majority votes (G) on
`lmsys/mt_bench_human_judgments` (CC-BY-4.0). Download the two parquet files from the Hugging Face
dataset, then `python mt_bench_ledger.py human.parquet gpt4.parquet results.json` (needs pandas, pyarrow).
Results of the run are in `results.json`. Canary classes = reasoning, math, coding (verifiable answers).
