#!/bin/bash
# Pilot round 3 on held-out seed 100: localized edit with larger replay; full and LoRA fixed from round 2.
cd /workspace/exp
pip install -q "transformers>=4.56,<5" peft scipy matplotlib 2>&1 | tail -1
mkdir -p /workspace/out
(cd /workspace/out && python -m http.server 8000 >/dev/null 2>&1 &)
nvidia-smi > /workspace/out/gpu.txt
i=0
for cfg in "5e-4 15 3" "1e-3 15 3" "5e-4 15 10" "1e-3 15 10" "1e-3 30 10" "1e-3 15 30" "1e-3 30 30" "2e-3 30 30"; do
  set -- $cfg
  python seed_study.py --seeds 100 --edit-lr $1 --edit-epochs $2 --edit-replay $3 --full-lr 3e-4 --full-epochs 8 --lora-lr 2e-3 \
    --base-cache /workspace/out/base_cache --out /workspace/out/pilot3_$i >> /workspace/out/log.txt 2>&1
  i=$((i+1))
done
touch /workspace/out/DONE
sleep 36000
