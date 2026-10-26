#!/bin/bash
# Pilot round 2 on held-out seed 100: edit (with replay) and full fine-tune settings.
cd /workspace/exp
pip install -q "transformers>=4.56,<5" peft scipy matplotlib 2>&1 | tail -1
mkdir -p /workspace/out
(cd /workspace/out && python -m http.server 8000 >/dev/null 2>&1 &)
nvidia-smi > /workspace/out/gpu.txt
i=0
for cfg in "5e-4 15 1e-4 8" "1e-3 15 1e-4 16" "2e-3 15 1e-4 32" "5e-4 40 3e-4 8" "1e-3 40 3e-4 16" "2e-3 40 3e-4 32"; do
  set -- $cfg
  python seed_study.py --seeds 100 --edit-lr $1 --edit-epochs $2 --full-lr $3 --full-epochs $4 --lora-lr 2e-3 \
    --base-cache /workspace/out/base_cache --out /workspace/out/pilot2_$i >> /workspace/out/log.txt 2>&1
  i=$((i+1))
done
touch /workspace/out/DONE
sleep 36000
