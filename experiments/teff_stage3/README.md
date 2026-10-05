# Stage 3: Qwen2.5-3B-Instruct, alphabet continuation with a planted attractor

- `lib.py` loads the model (bf16, CPU) and returns next-letter logits over the 26 candidate tokens.
- `run.py` runs the first sweep (`results_qwen3b.json`): attractor strength m in {0,2,3,4,6}, pressure/contamination cells, no-feedback control.
- `run2.py` with `EXTRA=1 OUT=results_extra.json` runs the 100-trajectory sweep over T in 0.15..5.0 used for Tables 7 and 8.
- Teff is the maximum-likelihood T on a log grid (0.02..20). It is not identified when the clean reference is saturated, and the estimate then sits at 0.02.

## Stage 4: Qwen2.5-7B-Instruct (Q8_0 GGUF, llama.cpp)

- `lib7.py` and `run7.py` run the same task with `llama-cpp-python`; results are in `results_qwen7b.json`.
- Needs `bartowski/Qwen2.5-7B-Instruct-GGUF` (`Qwen2.5-7B-Instruct-Q8_0.gguf`) and the Qwen2.5-7B-Instruct tokenizer.
