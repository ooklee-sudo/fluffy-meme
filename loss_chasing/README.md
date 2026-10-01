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

## Resuming, summarizing
- `run_experiment.py ... --resume --out <log>` continues an interrupted run (skips episodes already in the log; refuses to append to a non-empty log without `--resume`).
- `python summarize.py data/*.jsonl` builds the cross-model table (`SUMMARY.md`). `data/` holds the Qwen and SmolLM2 logs.
- `analyze.py` reports H1 as NOT TESTABLE when nobody ever skips, and H2 both as registered (raw risk index) and as an exploratory excess-risk + skip criterion.

## Wording robustness
`run_experiment.py ... --variants 0 1 2 3` runs the registered headline (0) and three paraphrases that carry the same facts; `python wording.py <log> --fails 0` reports the frame effect per wording and with wording fixed effects. First choices depend only on the prompt and on sampling, so each cell is repeated draws on one wording: without variants a "frame" effect is the effect of one sentence.

## Many-wording study (frame effect over independently generated paraphrases)
```bash
# 1. A model writes paraphrases from a fixed instruction; candidates are checked mechanically; the first 15 valid ones are kept
python make_wordings.py --model claude-sonnet-5-5 --n 15 --out wordings.json
# 2. Run any model on all 16 wordings (index 0 = registered) in two conditions (3 turns left, 12 turns left), 20 episodes per cell
python run_experiment.py --policy anthropic:claude-opus-5-5 --wordings wordings.json --variants all --episodes 20 \
    --temps 0.7 --fails 0 --start-ts 9 0 --first-only --workers 4 --out results/w16_opus.jsonl
# 3. Frame effect with wording as the unit of replication (cluster bootstrap over wordings, variance shares)
python wording16.py results/w16_opus.jsonl --md results/w16_opus.md
```
Models that reject `temperature` (Opus 5.x, Fable, Sonnet 5.x) run with default sampling and log `temperature_applied=false`; the console prints token and estimated cost totals after every cell (display only, nothing stops the run).
