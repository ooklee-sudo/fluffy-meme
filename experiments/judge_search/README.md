# GSM8K judge-search experiments (TMIS manuscript, Section 7.2)

Re-run of the best-of-N and judge-guided rewriting experiments with full per-question raw data,
so that exact statistical tests can be reported.

| File | What it is |
| --- | --- |
| `run_gsm8k.py` | Runs both experiments through OpenRouter and appends every result to `results/*.jsonl` (resumable) |
| `analyze.py` | Computes Tables 4 and 5: bootstrap intervals over questions, paired t-tests (df = n - 1), exact McNemar tests |
| `results/bon_raw.jsonl` | 200 questions x 32 policy samples, each with its strong-judge score, correctness, and length |
| `results/rewrite_init.jsonl` | Round-0 answer per question, shared by both judges and both arms |
| `results/rewrite_raw.jsonl` | One record per (question, judge, arm) with the full 6-round history |
| `results/summary.json` | Output of `analyze.py` |

## Design

- 200 questions sampled from the GSM8K test set with seed 20261105; gold is exact match on the final number.
- Policy and optimizer: `meta-llama/llama-3.1-8b-instruct`, temperature 1.
- Judges (temperature 0, reference-free 1-10 score): strong `openai/gpt-4o-mini`, weak `meta-llama/llama-3.2-3b-instruct`.
- OpenRouter provider routing sorted by throughput; the provider of each call is logged.
- Best-of-N: for each N in {1, 2, 4, 8, 16, 32}, the expected accuracy of the highest-judge answer among
  N candidates drawn at random without replacement from the 32 (2,000 draws per question, ties broken at random).
- Rewriting: 6 rounds x 4 rewrites. Optimize arm keeps the best-scoring rewrite if it does not lower the
  score; control arm keeps one rewrite at random. Both arms start from the same round-0 answer.

## Run

```bash
pip install requests numpy scipy
python run_gsm8k.py bon
python run_gsm8k.py rewrite
python analyze.py
```

`OPENROUTER_API_KEY` must be set (in the original run it was injected by a proxy).
