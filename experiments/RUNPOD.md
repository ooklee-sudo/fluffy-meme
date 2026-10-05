# Running the experiments on RunPod

`unlearn_audit_exp.py` reproduces the TOFU/Qwen2.5-0.5B experiment of the paper (exact retraining of all 16 coalitions,
gradient-ascent unlearning, six sequential orders, relearning attack) and adds what the revised manuscript needs:
the **retrained-model relearning control**, the **P8 concealment arm**, and the **duplication arm** (P3/P7).
It was smoke-tested on CPU with a tiny random model (`--tiny`); it has **not** been run on the real model yet.
Timings below are rough guesses, not measurements.

## 1. Pod
- GPU: 1x A100 40/80GB or RTX 4090/L40S 24GB. Full fine-tuning of 0.5B in fp32 + AdamW needs about 8-10GB plus activations.
- Template: a PyTorch template (CUDA 12.x). Volume: 30GB mounted at `/workspace` (outputs and `full.pt` ~2GB per run).
- Network: needs Hugging Face access to `Qwen/Qwen2.5-0.5B` and the public `locuslab/TOFU` dataset (no token needed for either).

## 2. Setup
```bash
cd /workspace
git clone https://github.com/ooklee-sudo/fluffy-meme.git && cd fluffy-meme
git checkout claude/practical-edison-oxooao
pip install -q transformers datasets numpy
python experiments/unlearn_audit_exp.py --tiny --stage all     # 20 s sanity check on the pod
```

## 3. Runs (use tmux or nohup; each stage saves JSON incrementally and the script can be re-run per stage)
```bash
# A. main replication + control (retrain 16 coalitions, unlearn at 6 strengths, relearning attack, retrained control)
nohup python experiments/unlearn_audit_exp.py --stage all --out /workspace/results/main > main.log 2>&1 &

# B. P3/P7: duplication arm (re-trains everything with group g repeated k_g times)
nohup python experiments/unlearn_audit_exp.py --stage all --dup 1 2 4 8 --out /workspace/results/dup > dup.log 2>&1 &

# C. more seeds for intervals (change --seed and --out; five seeds recommended)
for s in 1 2 3 4; do python experiments/unlearn_audit_exp.py --stage all --seed $s --out /workspace/results/main_s$s; done

# D. summary tables
python experiments/unlearn_audit_exp.py --stage analyze --out /workspace/results/main
```
`--stage conceal` (P8) can be re-run alone after `retrain` has produced `full.pt`; e.g. extra budgets:
`--stage conceal --budgets 0 1 2 4 8 16 --conceal-strengths 12 16 20 24`.

## 4. What to check before trusting numbers
1. **Learning-rate calibration.** The paper chose unlearning lr 1e-6 so the sign of eps(empty) changes inside the s-grid.
   If the sign change is outside 8-32 steps per group, adjust `--lr-unlearn` or `--strengths` (as in the paper's calibration).
2. **Replication of the original numbers.** Original runs used a single training template. Default here trains on four
   templates (needed so that a secret, held-out format exists for P8). To replicate the original exactly use
   `--train-templates 0`; expect small differences either way.
3. **Retrained control.** `retrain.json -> control_relearn` is the relearning attack on the model retrained without any group.
   Compare it with `unlearn.json -> relearn_empty`; only the excess over the control is residual knowledge.
4. **Seeds.** Single-seed groups are statistically tied (paper: seed sd 0.0004-0.0014), so ranks are not identified.
   Use `--dup` for asymmetric contributors.

## 5. Mapping to the manuscript (Section 6.5)
| Prediction | Output | Reading |
|---|---|---|
| P2 | `unlearn.json` + `analyze` table (eps, rho, kappa) | aggregate bias = -eps(empty) |
| P4 | `relearn_empty` vs `control_relearn` | residual knowledge net of generic fast relearning |
| P5 | rerun with `--all-orders` | aggregate identity with all 24 orders |
| P7 | `--dup 1 2 4 8`, per-group phi(eps) in `analyze` | bias and protection cost rising with k |
| P8 | `conceal.json` (`gap`, post-relearn secret) | gap rises with budget b and saturates |
| P9 | not an LLM experiment: simulate from measured retrain/shard compute | threshold z >= g0 - Lambda |

## 6. Bringing results back
```bash
cd /workspace/fluffy-meme && git checkout -b results-runpod && mkdir -p results/pf && cp -r /workspace/results/*/*.json results/pf/ 2>/dev/null
tar czf /workspace/pf_results.tgz -C /workspace results   # or download via runpodctl / the web UI
```
Do not commit `full.pt` (about 2GB). Send the JSON files (or tell me where they are) and I will update Section 6 and the abstract with measured numbers.
