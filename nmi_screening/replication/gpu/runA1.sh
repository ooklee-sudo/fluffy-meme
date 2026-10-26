set -x
cd /workspace/in
pip install -q "transformers==4.46.3" accelerate pandas scikit-learn 2>&1 | tail -2
python3 gpu_baselines.py --data pod_A1.jsonl --out /workspace/out/pod_A1_scores.csv --max-tokens 1024
touch /workspace/out/DONE_A1
