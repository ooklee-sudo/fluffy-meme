# Detector validation on real patent text

Human chunks: 2366 (reference 1183, null 591, test 592). Machine rewrites: 7423 (claude-opus-5.5 597, deepseek-v4.1-flash 1491, gemini-3.8-flash 1500, llama-4-maverick 1500, mistral-small-2603 235, gpt-6.1-sol 600, qwen3.8-flash 1500). Vocabulary 6000 words. Seed 0.

## A. False-positive rate on human-only groups

| group size | threshold (99th pct of null) | FPR on test | mean alpha-hat |
|---|---|---|---|
| 5 | 0.381 | 0.033 | 0.054 |
| 20 | 0.198 | 0.017 | 0.051 |
| 100 | 0.098 | 0.010 | 0.050 |
| 400 | 0.070 | 0.033 | 0.049 |

## B. Recovery of known AI shares (all generators, held-out source chunks)

| true share | n=100 mean (sd) | n=400 mean (sd) | detected above threshold, n=100 |
|---|---|---|---|
| 0.00 | 0.046 (0.022) | 0.050 (0.012) | 0.05 |
| 0.02 | 0.064 (0.026) | 0.064 (0.012) | 0.12 |
| 0.05 | 0.079 (0.025) | 0.080 (0.011) | 0.18 |
| 0.10 | 0.106 (0.027) | 0.109 (0.010) | 0.67 |
| 0.25 | 0.201 (0.030) | 0.200 (0.014) | 1.00 |
| 0.50 | 0.339 (0.038) | 0.347 (0.014) | 1.00 |

## C. Leave-one-generator-out (q trained without the held-out model; groups of 200, 25% held-out AI)

| held-out generator | pure-AI group alpha-hat (n=50) | 25% mix alpha-hat (sd) | | in-training reference (25% mix) |
|---|---|---|---|---|
| anthropic/claude-opus-5.5 | 0.565 | 0.171 (0.018) | | 0.184 |
| deepseek/deepseek-v4.1-flash | 0.543 | 0.168 (0.021) | | 0.188 |
| google/gemini-3.8-flash | 0.577 | 0.186 (0.017) | | 0.185 |
| meta-llama/llama-4-maverick | 0.649 | 0.195 (0.023) | | 0.200 |
| mistralai/mistral-small-2603 | 0.703 | 0.212 (0.021) | | 0.212 |
| openai/gpt-6.1-sol | 0.574 | 0.173 (0.021) | | 0.210 |
| qwen/qwen3.8-flash | 0.701 | 0.222 (0.016) | | 0.207 |

## D. Pure-AI groups by prompt type (n=50, held-out chunks)

| prompt | alpha-hat mean | fraction above n=20 threshold (groups of 20) |
|---|---|---|
| draft | 0.925 | 1.00 |
| expand | 0.933 | 1.00 |
| polish | 0.068 | 0.05 |
