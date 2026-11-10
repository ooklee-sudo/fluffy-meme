#!/bin/bash
# Confirmatory study (paper_isr/CONFIRMATORY_PLAN.md) on the API models, new items code_new@v1.
# Start only after paper_isr/predictions_open.md is committed.
#   bash run_confirm_api.sh            all six API models (three exploratory, three new)
#   bash run_confirm_api.sh api_haiku  one model (tag from the list below)
set -u
declare -A MODELS=(
  [api_haiku]=anthropic/claude-haiku-5.5
  [api_luna]=openai/gpt-6-luna
  [api_deepseek]=deepseek/deepseek-v4.1-flash
  [api_minimax]=minimax/minimax-m3.1-flash
  [api_mimo]=xiaomi/mimo-v2.6-flash
  [api_glm]=z-ai/glm-5.3-flashx
)
TAGS=("${@:-${!MODELS[@]}}")
mkdir -p logs
for tag in "${TAGS[@]}"; do
  m=${MODELS[$tag]}
  t=confirm_${tag#api_}
  for c in recheck doubt track20 track50 track80 authority evidence; do
    python api_challenge.py --model "$m" --tag "$t" --dataset code_new@v1 --challenge "$c" >> "logs/${t}.txt" 2>&1
  done
  python api_challenge.py --model "$m" --tag "$t" --dataset code_new@v1 --challenge evidence --tool >> "logs/${t}.txt" 2>&1
  for k in 4 1 0.25; do
    for c in recheck track50 authority; do
      python api_challenge.py --model "$m" --tag "$t" --dataset code_new@v1 --challenge "$c" --cost "$k" >> "logs/${t}.txt" 2>&1
    done
  done
  echo "$tag done"
done
