# Prompt-format robustness of tag-level accuracy (30 tags, 1,185 common questions; cost $9.81)

Formats: F1 system-role prompt, F2 user message with instruction, F3 bare question. Rubric R1, judge gpt-4.1-mini.

| Model | Level F1/F2/F3 | Tag-level SD | Split-half reliability (different questions) | Cross-format Pearson (same questions) |
|---|---|---|---|---|
| GPT-3.5 | 56.3 / 50.7 / 49.7% | 0.095-0.107 | 0.48 / 0.66 / 0.51 | 0.67-0.73 |
| Llama 3.1 8B | 22.3 / 22.6 / 22.5% | 0.073-0.079 | 0.41 / 0.15 / 0.11 | 0.73-0.77 |

Cross-format correlations are computed on the same questions, so they include shared question difficulty. The split-half reliability (disjoint questions) is the better measure of how much of the tag-level accuracy generalizes beyond the sampled questions: moderate for GPT-3.5, low for Llama.

GPT-4o minus GPT-3.5 tag-level delta (19 tags, 399 questions): mean -7.7 pp under F1, +1.4 pp under F2; correlation of the delta across formats: Pearson -0.03, Spearman -0.14. The change-in-accuracy treatment is not stable across prompt formats.
