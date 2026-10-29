#!/usr/bin/env bash
# Re-run the model-pair experiments (Section 3.3, Appendix C). These need a GPU (about 50 min for the five small pairs on one
# RTX 4090, about 100 min for the five larger pairs on an H200) and internet access to download the public checkpoints and data.
# The per-seed results of our runs are already in results/ so this script is only needed to repeat them.
# Wall-clock cost ratios C_A/C_N are only meaningful on CPU: add --preset cpu behaviour by running without a GPU.
set -euo pipefail
cd "$(dirname "$0")/code"
pip install -r ../requirements.txt
# GSM8K, small pairs and larger pairs, seeds 0-4
python run_seeds.py --fp32 --seeds 0 1 2 3 4 --outdir ../results/seeds_gpu
python run_seeds.py --large --fp32 --seeds 0 1 2 3 4 --outdir ../results/seeds_large_gpu
# DialogSum and text-to-SQL: small pairs (five seeds), two larger pairs (three seeds)
for task in dialogsum sql; do
  python run_seeds.py --fp32 --task $task --seeds 0 1 2 3 4 --outdir ../results/tasks_small_gpu
  python run_seeds.py --large --fp32 --task $task --only "pythia-1.4b +70k" "qwen2.5-1.5b" --seeds 0 1 2 --outdir ../results/tasks_large_gpu
done
# CPU cost ratios (C_A/C_N) for the 160M pairs, seed 0 (about 30 min per pair):
#   python run_seeds.py --seeds 0 --only "pythia-160m" --outdir ../results/seeds_cpu
