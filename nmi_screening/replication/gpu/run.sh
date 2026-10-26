set -x
rm -f /workspace/out/DONE
cd /workspace/in
# transformers 5.x requires a newer PyTorch than the image's 2.4.1, so pin 4.x
pip install -q "transformers==4.46.3" accelerate pandas scikit-learn 2>&1 | tail -2
python3 gpu_baselines.py --data docs.jsonl --out /workspace/out/scores_binoculars.csv --max-tokens 1024
python3 supervised_baselines.py --data docs.jsonl --model tfidf --out /workspace/out/tfidf_scores.csv
python3 supervised_baselines.py --data docs.jsonl --model roberta --out /workspace/out/roberta_scores.csv
touch /workspace/out/DONE
