#!/bin/bash
# Main sampling run: 8 models x 157 tasks x 20 samples, hard cap $10, then execution.
cd "$(dirname "$0")"
MODELS="meta-llama/llama-3.1-8b-instruct mistralai/mistral-small-3.2-24b-instruct qwen/qwen3-coder-30b-a3b-instruct openai/gpt-4o-mini anthropic/claude-haiku-5.5 meta-llama/llama-3.2-3b-instruct mistralai/ministral-3b-2512 qwen/qwen-2.5-7b-instruct"
python3 generate.py --models $MODELS --tasks 157 --samples 20 --budget 10.0 --workers 32 --out data/samples.jsonl
python3 execute.py --samples data/samples.jsonl --out data/results.jsonl --workers 4
