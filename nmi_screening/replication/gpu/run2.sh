set -x
rm -f /workspace/out/DONE2
cd /workspace/in
python3 gpu_baselines.py --data attacked_docs.jsonl --out /workspace/out/attacked_binoculars.csv --max-tokens 1024
python3 score_attacked_supervised.py --model roberta --train docs.jsonl --attacked attacked_docs.jsonl --sample judge_sample.csv --out /workspace/out/attack_roberta_results.csv
touch /workspace/out/DONE2
