#!/usr/bin/env bash
# Reproduces the WildChat snapshot-design analysis (RQ3). Needs ~5 GB disk, internet, pip install -r requirements.txt
set -euo pipefail
export DATA=${DATA:-$PWD/data}; mkdir -p "$DATA"
for i in $(seq 0 13); do n=$(printf %05d $i)
  [ -f "$DATA/s$i.parquet" ] || curl -sSL -o "$DATA/s$i.parquet" "https://huggingface.co/datasets/allenai/WildChat-1M/resolve/main/data/train-$n-of-00014.parquet"
  python3 -I extract.py "$DATA/s$i.parquet" "$DATA/f$i.parquet"
done
python3 -I build_all.py "$DATA"
DATA="$DATA" python3 -I fig3_data.py
python3 -I design.py  | tee results.txt
python3 -I placebo.py | tee placebo_results.txt
