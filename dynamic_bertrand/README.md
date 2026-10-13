# Dynamic Bertrand–Edgeworth model of LLM inference capacity

Code and results for the manuscript `LLM_Capacity_Bertrand_ISR.docx`.

| File | What it does |
| --- | --- |
| `bertrand_mpe.py` | Logit Markov perfect equilibrium of a capacity-constrained Bertrand game (price × capacity action, Rust/Ericson–Pakes state). `solve_decoupled()` uses the pricing/capacity separation (Prop. 1); `solve_mpe()` is the slower reference solver that gives the same equilibrium to 5 decimals. Also solves the joint-profit benchmark and the market-share contest. `python bertrand_mpe.py` (~2 min). |
| `sensitivity.py` | 20 scenarios × 4 starting points, equilibrium-selection runs, numerical checks of Props. 2–3. Writes `results/sens2/` and `results/sens2_summary.json` (~1 h on 4 cores). |
| `make_sens_tables.py` | Collapses the scenario files into `results/sens2_rows.json` and `results/sensitivity_capacity.png`. |
| `equilibria_states.py` | State-level behaviour in the two base-scenario equilibria (`results/equilibria_states.json`). |
| `alternating.py`, `price_game.py` | Dynamic price competition with alternating moves (Maskin–Tirole): prices are state variables. `price_game.py` solves the fixed-capacity game by Newton continuation in ρ and writes `results/price_game.json`; `alternating.py` is the joint price + capacity game (value iteration, Newton continuation). |
| `joint_dynamic.py`, `joint_dynamic_starts.py`, `joint_dynamic_sens.py`, `make_price_figs.py` | Joint-game runs (ρ = 3, 2, 1.7), multi-start check, 17-scenario comparison with simultaneous pricing, Edgeworth-cycle figure. |
| `theory_checks.py` | Exhaustive enumeration of pure Markov profiles in the two-price alternating game; verifies Propositions 4 and 5 (`python theory_checks.py verify` → `results/theory_checks.json`). |
| `timing_experiment.py` | Controlled timing experiment: simultaneous vs staggered/synchronized capacity vs committed prices (C0, C1, C1s, C2) → `results/timing_experiment.json` (~4 min on 4 cores). |
| `empirical/` | Exploratory empirical check of the repricing prediction (manuscript Section 8.3) and the design for a real test. `DESIGN.md` (Korean) is the plan; `build_price_panel.py` rebuilds the LiteLLM price panel from git history (needs a blobless clone of BerriAI/litellm); `analyze_repricing.py` runs the host-type regressions; `collect_openrouter.py` appends a daily snapshot of host-level prices and uptime (run it once a day); `analyze_snapshots.py` analyses that panel after 28 days. |
| `LLM_Capacity_Bertrand_ISR.docx` | Manuscript, ISR-style format. |

```bash
pip install numpy matplotlib
python bertrand_mpe.py
python sensitivity.py --workers 4 && python make_sens_tables.py
python equilibria_states.py
```

Notes: in the baseline model the pricing stage is static (prices are not state variables), so it has no Edgeworth cycles; Section 7 of the manuscript adds the alternating-move version, solved only for moderate payoff noise (ρ ≥ 1.7 jointly, ρ ≥ 0.1 at fixed capacities, one case excepted). Parameters are illustrative, not estimated; only the price floor/ceiling ratio is set from public data. The base scenario has two equilibria; results depend on the starting point (see manuscript Section 6). Three of 80 sensitivity runs did not meet the convergence tolerance (listed in Table 4 of the manuscript).
