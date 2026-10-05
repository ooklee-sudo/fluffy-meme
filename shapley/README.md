# Pricing Forgetting — exact-Shapley pipeline

`games.py` exact Shapley / LOO / dual game / sequential estimator (+ `test_games.py`: Prop. 1, Prop. 2, duplicate-player checks).
`sim.py`, `run.py` CPU-scale **stand-in** for the TOFU design (NOT an LLM): a small MLP memorizes synthetic author facts
(paraphrase = input noise) beside a shared "general" task; fixed epochs; all 2^10 coalitions retrained, GA unlearning
from the full model at 6 intensities, sequential-permutation unlearning, seed-noise check, relearning attack.
`analyze.py` computes phi(v), LOO, phi(v_hat), phi(eps), rho/kappa, order dependence, P1/P3 -> `out/*_analysis.json`.

    python3 run.py --n 10 --kind base  --out out/base.npz
    python3 run.py --n 10 --kind manip --seed 1 --out out/manip.npz   # groups 0,1 duplicates; replication k in {1,2,4,8}
    python3 analyze.py out/base.npz out/manip.npz

To go to a real LLM, replace `retrain`/`unlearn_all` in `run.py` with TOFU fine-tuning / OpenUnlearning calls that fill the same
tables `U[mask, n+1]` and `Uh[strength, mask, n+1]`; `analyze.py` is unchanged.
