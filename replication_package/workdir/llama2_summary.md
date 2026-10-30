# Llama 2 (pretraining cutoff Sep 2022) on v2 questions, 50 tags x ~40 q (2019-2022, score 3-20)

Served with vLLM on RunPod (A100 80GB), weights from the NousResearch mirrors, T=0, 1024 max tokens, same judge (gpt-4.1-mini) as run_v2.py. Deduplicated to 1,966 unique questions per model.

| Model | Accuracy | Cross-tag SD | Sampling-noise SD | Signal SD |
|---|---|---|---|---|
| Llama 2 13B chat | 0.123 | 0.078 | 0.052 | 0.057 |
| Llama 2 7B chat | 0.094 | 0.058 | 0.047 | 0.035 |

- Tag-level accuracy correlates 0.61 between 13B and 7B (permutation p < 0.001): the tag pattern is real and replicates.
- Same questions, other models (earlier partial run, 19 tags): gpt-3.5 0.555, gpt-4 0.579 (n=195), gpt-4o 0.464 (n=399), llama-3.1-8b 0.242. Per-tag correlation of Llama 2 13B with gpt-3.5 0.52, with llama-3.1-8b 0.70, with gpt-4o and gpt-4 about 0 (small n).
- Floor effect: several tags are at 0. A weak control model leaves little room to observe a gap, which limits power for the recency-gap design.
- Pod deleted after the run. About 4.5 h of idle billing was lost when background jobs stopped while the session was idle.
