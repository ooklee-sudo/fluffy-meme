#!/bin/bash
# Robustness: frontier reasoning models with reasoning switched on (medium effort), original items,
# the eight core conditions. Same protocol and items as the exploratory API runs.
#   bash run_reasoning_api.sh             both models
#   bash run_reasoning_api.sh r_sonnet55  one model
set -u
declare -A MODELS=([r_sonnet55]=anthropic/claude-sonnet-5.5 [r_gpt61sol]=openai/gpt-6.1-sol)
TAGS=("${@:-${!MODELS[@]}}")
mkdir -p logs
for tag in "${TAGS[@]}"; do
  m=${MODELS[$tag]}
  for c in recheck doubt track20 track50 track80 authority evidence; do
    python api_challenge.py --model "$m" --tag "api_$tag" --challenge "$c" --reasoning-effort medium >> "logs/api_$tag.txt" 2>&1
  done
  python api_challenge.py --model "$m" --tag "api_$tag" --challenge evidence --tool --reasoning-effort medium >> "logs/api_$tag.txt" 2>&1
  echo "$tag done"
done
