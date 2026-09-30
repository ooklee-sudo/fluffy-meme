# Loss-chasing evaluation harness

Implements the protocol *Loss Chasing in LLM Maintenance Decisions* (state machine §4, frames §4.4,
grid §5, outcomes/analysis §6, log schema App. B). No human subjects; **the paper reports no results and neither does this repo**.

```bash
pip install numpy scipy pandas            # + anthropic / openai / huggingface_hub (hfapi:) / torch+transformers (hf: local)
cd loss_chasing
# 1. pipeline smoke test (SYNTHETIC agent, not evidence of anything)
python run_experiment.py --policy synthetic --policy greedy --policy always:narrow_patch --policy always:hold \
    --episodes 50 --out results/smoke.jsonl
python analyze.py results/smoke.jsonl
# 2. real run (primary test only = 1 call/episode; drop --first-only for full 12-turn episodes)
export ANTHROPIC_API_KEY=...
python run_experiment.py --policy anthropic:claude-haiku-4-5-20251001 --episodes 100 --first-only --out results/haiku.jsonl
python analyze.py results/haiku.jsonl
```
Options: `--rational-prime` (correction condition), `--p-scale/--d-scale 0.8|1.2` (±20% sensitivity), `--early-stop`,
`analyze.py --drop-parse-fail`. Parse failures map to `hold` and are flagged (`parse_fail`).

Note: computing EVs from Table 1 gives `wide_skip = 0.35*3 − 0.65*5 = −2.20`, not the −1.80 quoted in §4.1 (the other five match).
The code uses Table 1's parameters; skipping is dominated either way.

## Hugging Face backends
```bash
# local model on CPU/GPU (downloads from the Hub; set HF_TOKEN for gated models)
python run_experiment.py --policy hf:Qwen/Qwen2.5-0.5B-Instruct --episodes 100 --first-only --out results/qwen.jsonl
# Hugging Face Inference API (HF_TOKEN required)
python run_experiment.py --policy hfapi:meta-llama/Llama-3.1-8B-Instruct --episodes 100 --first-only --out results/llama.jsonl
```
Local models get `{"action": "` pre-filled so small models stay in the JSON-only format; parsing remains strict.
