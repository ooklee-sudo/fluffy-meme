# Revision study: effective decision temperature (T_eff)

Code and results for the revision of "Is the Sampling Temperature the Agent's Decision State?".
This folder is independent of the real-options code in the repository root.
Everything runs on CPU with HF Transformers in fp32 (no GPU, no quantisation).

| File | Purpose |
| --- | --- |
| `teff_core.py` | Task definitions, prompt wordings (P0-P2, C0-C2), model wrapper with prefix KV cache, estimators (T_eff MLE, profile-likelihood interval, distributional T_eff, bootstrap) |
| `run_study.py` | Stages `probe`, `matched` (clean/pressure/contamination cells, three references), `grid` (full attractor-length grid), `refcmp` (same-history / gold-repaired / de-duplicated references) |
| `free_gen.py` | Full-vocabulary free generation with a planted attractor |
| `se_nli.py` | Entailment-clustered semantic entropy (DeBERTa-large MNLI) on the free-generation completions |
| `sim_identification.py` | Simulations S1-S4 (scale confound, interval properties, saturation, stylised peak condition) |
| `runtime_bench.py` | Cost of fitting T_eff |
| `analyze.py` | Aggregates `results/*.json` into `results/summary.json` |
| `build_revision.py`, `edit_docx.py`, `build_response.py` | Write the revised manuscript and the response letter into `manuscript/` |
| `run_all.sh`, `run_refcmp.sh` | Drivers used for the runs |

Models: Qwen/Qwen2.5-0.5B-Instruct, Qwen/Qwen2.5-1.5B-Instruct, unsloth/Llama-3.2-1B-Instruct (ungated mirror),
HuggingFaceTB/SmolLM2-1.7B-Instruct. Seeds are hashes of the cell definition.

```bash
pip install torch transformers scipy sentencepiece python-docx
python run_study.py probe   --model Qwen/Qwen2.5-0.5B-Instruct
python run_study.py matched --model Qwen/Qwen2.5-0.5B-Instruct --n 40 --variants
python run_study.py grid    --model Qwen/Qwen2.5-0.5B-Instruct --n 20 --tasks alphabet,months,planets --temps 0.15,0.8,1.5,2.5,4.0
python run_study.py refcmp  --model Qwen/Qwen2.5-0.5B-Instruct --n 40
python free_gen.py --model Qwen/Qwen2.5-1.5B-Instruct --n 20 && python se_nli.py results/free_Qwen2.5-1.5B-Instruct.json
python sim_identification.py && python runtime_bench.py && python analyze.py
python build_revision.py ORIGINAL.docx manuscript   # see __main__ block / build() for arguments
```

Not included: the scripts of Stages A and B of the original submission, and any run of the 3B / 7B models of the main text.
