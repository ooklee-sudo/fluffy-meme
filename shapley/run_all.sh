#!/usr/bin/env bash
# Whole pipeline, K processes sharing one GPU (the step is launch-overhead bound, so this scales ~linearly).
# usage: bash run_all.sh N OUTDIR [K=4] [extra llm_run.py flags...]     e.g.  bash run_all.sh 4 out_llm 4 --perms 20
# Resumable: rerun the same command after an interruption. Logs in OUTDIR/logs.
set -euo pipefail
N=$1; OUT=$2; K=${3:-4}; shift 3 || shift $#
EXTRA=("$@")
export OMP_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
mkdir -p "$OUT/logs"
trap 'pkill -P $$ 2>/dev/null || true' EXIT   # a failed shard must not leave the others running as orphans
par() {  # par CMD : run CMD in K shards in parallel, wait for all
  local cmd=$1 pids=()
  for ((i = 0; i < K; i++)); do
    python llm_run.py "$cmd" --n "$N" --out "$OUT" --shard "$i/$K" "${EXTRA[@]}" > "$OUT/logs/${cmd}_$i.log" 2>&1 & pids+=($!)
  done
  for p in "${pids[@]}"; do wait "$p"; done; echo "$cmd done $(date +%T)"
}
par retrain
par unlearn
for cmd in noise seq attack; do
  python llm_run.py "$cmd" --n "$N" --out "$OUT" "${EXTRA[@]}" > "$OUT/logs/$cmd.log" 2>&1 & 
done
wait; echo "noise/seq/attack done $(date +%T)"
python llm_run.py assemble --n "$N" --out "$OUT" "${EXTRA[@]}" > "$OUT/logs/assemble.log" 2>&1
python analyze.py "$OUT/tofu.npz" > "$OUT/analysis.txt"; echo "wrote $OUT/analysis.txt and ${OUT}/tofu_analysis.json"
