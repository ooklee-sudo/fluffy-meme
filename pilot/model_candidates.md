# Model candidates and training-data cutoffs (checked 2026-10-30)

Regime is defined against the tag-volume break found in `volume_v3.json`: supply is normal through 2022H2 and collapses from 2023H1.

| Model | OpenRouter id | Stated cutoff | Source | Regime |
|---|---|---|---|---|
| GPT-3.5 Turbo (family) | `openai/gpt-3.5-turbo-0613`, `-16k` | Sep 2021 | OpenAI model page (family level; the 0613 snapshot is not listed there) | pre |
| Llama 2 | not on OpenRouter | Sep 2022 pretraining (tuning data to Jul 2023) | Meta model card | pre (self-host only) |
| Llama 3 8B | not on OpenRouter | Mar 2023 | Meta model card | transition |
| Llama 3 70B | not on OpenRouter | Dec 2023 | Meta model card | transition |
| Llama 3.1 / 3.2 / 3.3 | `meta-llama/llama-3.1-8b-instruct`, `-70b`, `llama-3.3-70b-instruct` | Dec 2023 | Meta model cards (3.3 states Dec 2023) | transition |
| GPT-4o | `openai/gpt-4o-2024-05-13` | Oct 2023 | OpenAI model page | transition |
| GPT-4.1 | `openai/gpt-4.1` | Jun 2024 | OpenAI model page | post |
| Phi-4 | `microsoft/phi-4` | Jun 2024 and earlier | HF model card | post |
| Gemma 3 | `google/gemma-3-27b-it` | Aug 2024 | Google model card | post |
| Llama 4 | `meta-llama/llama-4-scout`, `-maverick` | Aug 2024 | Meta model card | post |

## Not usable until a source is found
- `openai/gpt-4`: the OpenAI page lists "Dec 2023" for `gpt-4`, but GPT-4 was released 2023-03-14, so that date cannot describe the original snapshot. It is the current alias. The snapshot cutoff is unverified.
- Qwen 2.5 / Qwen3, DeepSeek-V3, Mistral 7B v0.3, Gemma 2: official model cards state no cutoff. Third-party aggregators disagree (e.g. Qwen2.5 Dec 2023 vs May 2024).
- Claude models: not checked.

## Consequence for the design
The pre-ChatGPT control group is thin. Only the GPT-3.5 family is verifiably pre-ChatGPT on OpenRouter, and Llama 2 (the strongest open pre-ChatGPT model) must be self-hosted. Llama 3.x and GPT-4o saw only the first year of the decline, so they are a transition group, not a clean post group.
