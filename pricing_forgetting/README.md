# Code for "Pricing Forgetting" (Shapley-based data valuation and audit design for compensated unlearning)

| File | Paper section | Runs on | What it does |
| --- | --- | --- | --- |
| `shapley.py` | 3–5 | – | Exact Shapley/Banzhaf/leave-one-out, contribution & deletion games, replication & merging, residual game, sequential estimator, audit formulas |
| `theory_checks.py` (`test_theory.py`) | Props 1–8, P5, P6 | CPU, seconds | Verifies every proposition and worked example on random games (19 checks) |
| `tofu_experiment.py` | 6 | GPU (CPU for `--tiny`) | Exact retraining of all 2⁴ coalitions on TOFU authors; unlearning (set-function and sequential); relearning attack |
| `analyze.py` | 6.4, Tables 1–2 | CPU | φ, LOO, ε(∅)=ρ−κ, L1 norms, sequential distances, P5 check, sign-change point, plot |

## Run

```bash
pip install -r requirements.txt
python theory_checks.py                     # propositions; exits non-zero on failure
python tofu_experiment.py --tiny            # plumbing test in ~20 s (random tiny model, synthetic data)
python analyze.py --dir results/pf_tiny

# the paper's experiment (Qwen2.5-0.5B, full fine-tuning; GPU with >=24GB recommended)
python tofu_experiment.py --model Qwen/Qwen2.5-0.5B
python analyze.py --dir results/pf
```

Stages (`--stages retrain,noise,unlearn`) write JSON into `--out` and are skipped when their output exists (`--force` to redo). `retrain` also saves the full (`N`) and empty (`{}`) checkpoints in `<out>/ckpt/`; they are gitignored.

## Setup details (Section 6.1 / 6.3)

- 200 TOFU authors × 20 QA, shuffled with `--data-seed`: 4 groups of 10 authors, D0 = 100 other authors. `U = author component + general component` (real-authors and world-facts averaged), score = mean of exp(mean answer-token log-prob).
- Retraining: 5 epochs, AdamW lr 2e-5, batch 32, one run per coalition; `noise` repeats {}, {0,1,2}, N with 5 seeds.
- Unlearning from the full model: AdamW lr 1e-6, batch 16, grad-clip 1.0, strength *s* = steps per removed group, grid 8,12,16,20,24,32. The set-function estimate removes N∖T in one run of s·|N∖T| steps (one run per T is evaluated at every s). The sequential estimate removes groups one at a time along `--n-orders` removal orders (`6`, or `all` = 24 for the exact P5 check); orders share prefixes so U~ is a true function of the prefix.
- Relearning attack at T = {}: fine-tune 5 steps (lr 2e-5, batch 32) on a random 10 % of the forgotten pairs, evaluate on the other 90 %.

## Items the paper lists as not yet done, now implemented

| Item | How |
| --- | --- |
| Other unlearning methods | `--method gd` (gradient difference), `--method npo` (`--npo-beta`) |
| Relearning control (retrained model + same attack) | printed as "relearning control" and stored as `relearn_control` |
| P5: sequential identity with all 24 orders, Prop. 5 bound, order-gap lower bound | `--n-orders all`; `analyze.py` prints the check |
| P6: replication gain | printed by `analyze.py` (Prop. 2 formula on the measured game); algebra verified in `theory_checks.py` |
| P1: redundant contributors | `--redundant 1:0` gives group 1 the same author facts as group 0 |
| P3: hard-to-forget data | `--dup 1,2,4,8` duplicates each group's training examples k times; `analyze.py` reports the slope of φ̂ᵢ−φᵢ on k |

Use a different `--out` for each manipulation, e.g. `--redundant 1:0 --out results/pf_p1`.

## Notes

- ρ and κ: ρ(T) = (1/n) Σ_{j∉T}(Û_j − U_j) and κ(T) = −[(1/n) Σ_{j∈T}(Û_j − U_j) + (Û_gen − U_gen)], so ε = ρ − κ holds exactly; at T = {} ρ is the mean excess on the forgotten groups.
- Shapley sums and ε(∅) use U (author + general). The L1 norms and the sequential-vs-set comparison use the author component, as in Section 6.4.
- Not reproduced here: the numbers in the paper's Tables 1–2 come from a GPU run; this environment only ran the `--tiny` smoke test and the theory checks.
