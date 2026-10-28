#!/bin/bash
# External-validity runs: other models on the biography task, and a source-grounded summarisation task.
# Usage: bash run_ext.sh   (idempotent: generate.py / label_sent.py skip finished items)
cd "$(dirname "$0")"
chain() {  # chain <task> <model>
  task=$1; model=$2; short=${model##*/}
  pre=gen_; [ "$task" = summ ] && pre=gen_summ_
  python3 -u generate.py --model "$model" --task "$task" --workers 6 \
    && python3 -u label_sent.py --gen "data/${pre}${short}.jsonl" --workers 6
}
for m in mistralai/mistral-small-3.2-24b-instruct meta-llama/llama-4-scout google/gemma-3-12b-it mistralai/mistral-large-2512; do
  chain bio "$m" > "data/ext_bio_${m##*/}.log" 2>&1 &
done
for m in google/gemma-3-27b-it mistralai/mistral-small-3.2-24b-instruct meta-llama/llama-4-scout; do
  chain summ "$m" > "data/ext_summ_${m##*/}.log" 2>&1 &
done
wait
