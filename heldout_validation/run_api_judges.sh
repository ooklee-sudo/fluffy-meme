#!/bin/bash
cd "$(dirname "$0")"
for g in qwen0.5b smollm360m qwen1.5b; do
  python3 judge_api.py --gen $g --model meta-llama/llama-3.3-70b-instruct --name llama70b
  python3 judge_api.py --gen $g --model google/gemma-3-27b-it --name gemma27b
done
echo APIDONE
