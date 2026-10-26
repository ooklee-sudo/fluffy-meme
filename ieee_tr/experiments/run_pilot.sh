#!/bin/bash
# Pilot on a held-out seed (100): sweep edit/LoRA learning rates, never touching the reporting seeds.
set -x
cd /workspace/exp
pip install -q "transformers>=4.56,<5" peft scipy matplotlib 2>&1 | tail -1
mkdir -p /workspace/out
(cd /workspace/out && python -m http.server 8000 >/dev/null 2>&1 &)
nvidia-smi > /workspace/out/gpu.txt
i=0
for cfg in "5e-4 2e-3" "1e-4 5e-4" "3e-5 2e-4" "1e-5 1e-4"; do
  set -- $cfg
  python seed_study.py --seeds 100 --edit-lr $1 --lora-lr $2 --base-cache /workspace/out/base_cache --out /workspace/out/pilot_$i >> /workspace/out/log.txt 2>&1
  i=$((i+1))
done
touch /workspace/out/DONE
sleep 36000
