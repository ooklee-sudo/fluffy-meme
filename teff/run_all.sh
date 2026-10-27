#!/bin/bash
# Sequential driver for the revision study (all models: HF transformers, fp32, CPU).
# Stage order: probe -> matched (+ prompt variants) -> grid -> free generation.
# Qwen2.5-0.5B probe and matched stages were launched by hand first:
#   python3 run_study.py probe   --model Qwen/Qwen2.5-0.5B-Instruct
#   python3 run_study.py matched --model Qwen/Qwen2.5-0.5B-Instruct --n 40 --variants
cd "$(dirname "$0")"
Q05=Qwen/Qwen2.5-0.5B-Instruct; Q15=Qwen/Qwen2.5-1.5B-Instruct
L1=unsloth/Llama-3.2-1B-Instruct; S17=HuggingFaceTB/SmolLM2-1.7B-Instruct
while pgrep -f "run_study.py matched --model Qwen/Qwen2.5-0.5B" >/dev/null; do sleep 20; done
for M in $Q15 $L1; do
  python3 run_study.py probe --model $M
  python3 run_study.py matched --model $M --n 40 --variants
done
python3 run_study.py probe --model $S17
python3 run_study.py matched --model $S17 --n 40
for M in $Q05 $Q15 $L1; do
  python3 run_study.py grid --model $M --n 20 --tasks alphabet,months,planets --temps 0.15,0.8,1.5,2.5,4.0
done
for M in $Q15 $L1; do
  python3 free_gen.py --model $M --n 20
  python3 se_nli.py results/free_$(basename $M).json
done
