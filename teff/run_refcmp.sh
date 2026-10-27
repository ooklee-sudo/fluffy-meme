#!/bin/bash
# Reference-construction comparison (same history / gold-repaired / de-duplicated).
cd "$(dirname "$0")"
while pgrep -f "run_all.sh" >/dev/null; do sleep 30; done
for M in Qwen/Qwen2.5-0.5B-Instruct Qwen/Qwen2.5-1.5B-Instruct unsloth/Llama-3.2-1B-Instruct HuggingFaceTB/SmolLM2-1.7B-Instruct; do
  python3 run_study.py refcmp --model $M --n 40
done
