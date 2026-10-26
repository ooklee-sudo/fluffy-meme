set -x
cd /workspace/in
python3 gpu_baselines.py --data pod_A2.jsonl --out /workspace/out/pod_A2_scores.csv --max-tokens 1024
touch /workspace/out/DONE_A2
