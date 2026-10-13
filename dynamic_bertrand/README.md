# Dynamic Bertrand version of the LLM capacity-competition MPE model

- `bertrand_mpe.py` – logit Markov perfect equilibrium of a capacity-constrained Bertrand game
  (price × capacity action, Rust/Ericson–Pakes state). Also solves a joint-profit cartel and the
  original market-share contest as benchmarks. `python bertrand_mpe.py` (~6 min on CPU; numpy,
  matplotlib for the figures; `--sweep` adds a rho × marginal-cost sensitivity run, not yet run).
- `LLM_MPE_Dynamic_Bertrand.docx` – the revised manuscript.
- `results/` – `dynamic_bertrand.json`, `price_by_state.png`, `benchmarks.png`.

Results are for one parameterisation and one selected equilibrium; see Section 5 of the manuscript.
