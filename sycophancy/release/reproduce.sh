#!/usr/bin/env bash
# Every command used for the paper, in order. Run from this folder.
# Each command is resumable; rerun it after an interruption.
set -e

# ---------------------------------------------------------------------------
# 1. Challenge runs with short replies
# ---------------------------------------------------------------------------
python run_challenge.py --model Qwen/Qwen3-1.7B --n 2000 --max-new-tokens 96 --out runs/q17b_doubt
python run_challenge.py --model Qwen/Qwen3-4B   --n 2000 --max-new-tokens 96 --out runs/q4b_doubt
python run_challenge.py --model Qwen/Qwen3-4B   --n 2000 --max-new-tokens 96 --system firm --no-hidden --out runs/q4b_doubt_firm
python run_challenge.py --model Qwen/Qwen3-8B   --n 2000 --max-new-tokens 96 --bs 4 --out runs/q8b_doubt
python run_challenge.py --model allenai/OLMo-2-1124-7B-Instruct --n 2000 --max-new-tokens 256 --bs 4 --out runs/olmo7b_doubt
python run_challenge.py --model Qwen/Qwen3-4B   --n 500  --max-new-tokens 256 --no-hidden --out runs/q4b_doubt_256
python run_challenge.py --model Qwen/Qwen3-4B   --dataset arc --n 1000 --max-new-tokens 96 --bs 16 --no-hidden --out runs/q4b_arc_96

# ---------------------------------------------------------------------------
# 2. Challenge runs with full replies (1,024 tokens)
# ---------------------------------------------------------------------------
python run_challenge.py --model Qwen/Qwen3-4B   --n 1000 --max-new-tokens 1024 --bs 4 --out runs/q4b_v2
python run_challenge.py --model Qwen/Qwen3-8B   --n 1000 --max-new-tokens 1024 --bs 2 --out runs/q8b_v2
python run_challenge.py --model allenai/OLMo-2-1124-7B-Instruct --n 500 --max-new-tokens 1024 --bs 1 --out runs/olmo7b_v2
python run_challenge.py --model Qwen/Qwen3-4B   --dataset arc --n 1000 --max-new-tokens 1024 --bs 4 --out runs/q4b_arc
python run_challenge.py --model allenai/OLMo-2-1124-7B-Instruct --dataset arc --n 500 --max-new-tokens 1024 --bs 1 --out runs/olmo7b_arc

# ---------------------------------------------------------------------------
# 3. Steering and gating (answers read without a reply unless noted)
# ---------------------------------------------------------------------------
python steer.py runs/q4b_doubt --model Qwen/Qwen3-4B --turn2 prefill --layers 18,24,28 --alphas=-4,2,4,8 --n-test 1000 --out results/screen_q4b
python steer.py runs/q4b_doubt --model Qwen/Qwen3-4B --turn2 prefill --layers 18 --alphas=2,4,8 --n-test 1000 --direction targeted --out results/screen_q4b_targeted
python steer.py runs/q4b_doubt --model Qwen/Qwen3-4B --turn2 prefill --layers 18 --alphas=2,4,8 --n-test 1000 --direction combined --out results/screen_q4b_combined
python steer.py runs/q4b_doubt --model Qwen/Qwen3-4B --turn2 prefill --layers 18 --alphas=-4,2,4,8 --n-test 1000 --gate --out results/gate_q4b
python steer.py runs/q8b_doubt --model Qwen/Qwen3-8B --turn2 prefill --layers 14,18,22 --alphas=-4,2,4,8 --n-test 1000 --bs 8 --gate --out results/gate_q8b
python steer.py runs/olmo7b_doubt --model allenai/OLMo-2-1124-7B-Instruct --turn2 prefill --layers 12,16,20 --alphas=-4,2,4,8 --n-test 1000 --bs 8 --gate --out results/gate_olmo
# OLMo-2 7B with free 256-token replies (prefilled replies show no answer changes for this model)
python steer.py runs/olmo7b_doubt --model allenai/OLMo-2-1124-7B-Instruct --layers 16 --alphas=-4,8 --n-test 300 --bs 4 --gate --out results/steer_olmo_free

# ---------------------------------------------------------------------------
# 4. Probes and shared-signal test (CPU)
# ---------------------------------------------------------------------------
for run in q4b_doubt olmo7b_doubt q4b_v2 olmo7b_v2; do
  python analyze.py runs/$run --no-plot
done
for run in q4b_doubt q4b_v2 q8b_doubt q8b_v2 olmo7b_doubt olmo7b_v2; do
  python geometry.py runs/$run --layer-step 4
done

# ---------------------------------------------------------------------------
# 5. Tables and figures
# ---------------------------------------------------------------------------
python make_figures.py
