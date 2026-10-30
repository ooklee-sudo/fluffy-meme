# Recency-gap pilot (24 tags x 16 q per half-year block; score 2-30, accepted answer)

Gap G = accuracy on old block - accuracy on recent block (same prompt, T=0, judge gpt-4.1-mini).

Same questions (2022H1 vs 2024H1):
| Model | Cutoff | 2022H1 | 2024H1 | Gap (pp, se) |
|---|---|---|---|---|
| GPT-3.5 (control) | Sep 2021 | 53.2% | 43.7% | +9.5 (3.6) |
| Llama 3.1 8B | Dec 2023 | 20.5% | 13.8% | +6.7 (2.8) |
| GPT-4.1 | Jun 2024 | 54.8% | 44.8% | +10.0 (3.6) |
| Gemma 3 27B | Aug 2024 | 39.9% | 27.9% | +12.0 (3.4) |
| Llama 4 Scout | Aug 2024 | 39.6% | 26.8% | +12.8 (3.5) |

Each model on its own blocks (last half-year before cutoff vs two years earlier): GPT-3.5 +1.4, Llama 3.1 8B +7.7, GPT-4.1 +10.0, Gemma 3 +12.0, Llama 4 +13.6. This rising pattern disappears once all models face the same questions: the 2024H1 questions are simply harder for every model, including a model that cannot know them.

Difference in gaps vs the GPT-3.5 control: Llama 3.1 -2.8, GPT-4.1 +0.5, Gemma 3 +2.5, Llama 4 +3.3 pp (se about 5, all |z| < 1).
Tag-level (24 tags): corr(log question decline, post-minus-control gap) = -0.07.
Llama 3.1 8B control run was 16 jobs short of complete when analyzed.
