set -x
pkill -f gpu_baselines.py; sleep 2
cd /workspace/in
pip install -q hf_transfer "huggingface_hub[cli]<0.27" 2>&1 | tail -1
rm -f /root/.cache/huggingface/hub/models--tiiuae--falcon-7b-instruct/blobs/*.incomplete
for t in 1 2 3; do HF_HUB_ENABLE_HF_TRANSFER=1 timeout 900 huggingface-cli download tiiuae/falcon-7b-instruct --quiet && break; echo retry $t; done
du -sh /root/.cache/huggingface/hub/*
python3 gpu_baselines.py --data pod_A1.jsonl --out /workspace/out/pod_A1_scores.csv --max-tokens 1024
touch /workspace/out/DONE_A1
python3 gpu_baselines.py --data pod_A2.jsonl --out /workspace/out/pod_A2_scores.csv --max-tokens 1024
touch /workspace/out/DONE_A2
