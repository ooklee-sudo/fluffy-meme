# Running the published-detector baselines on RunPod

1. Create a pod with a PyTorch template and a GPU with at least 40 GB (the default pair, Falcon-7B and Falcon-7B-instruct, is about 28 GB in bfloat16). A 24 GB card works with `--observer`/`--performer` set to smaller models that share a tokenizer.
2. Upload `gpu_baselines.py` and the document file `docs.jsonl` (one JSON object per line with `id`, `label`, `generator`, `text`; use the same first-2,000-token excerpt as the screens).
3. In the pod: `pip install transformers accelerate pandas` (PyTorch is in the template), then
   `python3 gpu_baselines.py --data docs.jsonl --out scores.csv`
4. Download `scores.csv` and place it in `data/` of the repository. The analysis step reads it.
5. Stop the pod when done. Do not put API keys, tokens or passwords in any file in this repository.

Smoke test without a GPU (checks the code path only; the scores are not meaningful):
`python3 gpu_baselines.py --data docs.jsonl --observer gpt2 --performer distilgpt2 --max-tokens 256 --limit 10`
