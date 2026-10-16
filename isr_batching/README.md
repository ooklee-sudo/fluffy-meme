# Batched-number pipeline for the ISR manuscript

| Manuscript item | Script |
|---|---|
| 5.2 alpha, beta, M, prefill, Assumption S check | `measure_tau.py` (GPU + vLLM) |
| 6.2 flat vs. schedule, Fig. 1/4 tolls and waiting/slowdown split | `quasi_static.py`, `run_all.py` (`results.csv`, `*_baseline.json`) |
| 6.3 Table 2 (quadratic vs. exact recovery, Cor. 9(a) bound) | `run_all.py` |
| 6.5 robustness grid | `run_all.py` |
| 6.7 implied c0/V, ratio-2 schedules | `run_all.py` (`sec67.json`) |
| Table B5 | `run_all.py` (`tableB5_check.csv`) |
| 6.1 Table 1 capacity under real/Poisson/bootstrap arrivals | `capacity_sim.py` |
| 6.4 Table 3, 6.6 Table 4 (exact Markov chain, simulated equilibrium demand) | **not included** |

Run order: `measure_tau.py` -> `run_all.py --M <M_kv> --b <beta/alpha> --profile <Azure 2024 csv>` -> `capacity_sim.py`.
Tests: `PYTHONPATH=. python3 test_quasi_static.py && PYTHONPATH=. python3 test_sim.py`.

Verified here: closed-form d, toll, waiting/slowdown split equal brute-force birth-death; B.1 values (toll 132.0); tolls increase
with load (Prop. 1); slowdown toll = 0 for b = 0; simulator matches Table B4. Table B5 beta=0 row reproduced
(flat loss 3.0%, two-level recovery 80%).

Assumptions to state in the paper: (i) "unpriced demand = r x capacity" is coded as Lambda_k = r*mubar*profile_k/mean(profile) (reproduces the manuscript's dedicated-server 14.7% / 4.6% / 44.1%); Table B5 uses profile/max (`norm="max"`);
(ii) single engine == c engines with random routing (percent losses invariant); balanced (JSQ) routing needs the
Assumption-S check of Sec. 5.4 -- test with `Engine`-level toll monotonicity or the simulator.
