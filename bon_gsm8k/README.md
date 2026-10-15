# Best-of-N under an LLM judge (GSM8K, deterministic gold)

Windows cmd:

    pip install numpy pandas pyarrow
    set OPENROUTER_API_KEY=sk-or-...
    python bon_gsm8k.py --n-questions 20 --k 8 --max-usd 0.5     (small trial first)
    python bon_gsm8k.py --n-questions 200 --k 32 --max-usd 3     (full run)

`python bon_gsm8k.py --mock` runs an offline self-test with synthetic data. Output goes to `bon_out/`
(`gens.jsonl`, `judges.jsonl` caches, `results.json`); rerunning resumes from the cache.
