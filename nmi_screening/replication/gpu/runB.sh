set -x
cd /workspace/in
for t in gpt4o claude llama deepseek econ; do python3 ext_train_score.py --model roberta --train train_$t.jsonl --test test_$t.jsonl --out /workspace/out/rb_$t.csv; done
touch /workspace/out/DONE_B
