# Poisson-SNS (re-implementation from the manuscript)

Re-implemented from the manuscript text because the original code could not be located.
Numbers will not match the manuscript exactly; replace the manuscript's results with these.

| File | Purpose |
| --- | --- |
| `sim.py` | Event-driven simulator: IPP thinning, personas (Table 1), platform rules, oracles, alternative networks |
| `analysis.py` | Study 1 metrics (r, TV, chi2, KS, reply delays), Hawkes MLE branching ratio |
| `study1.py` | Scheduler comparison (IPP vs HPP vs polling) -> `results_study1.json` |
| `study2.py` | Seeding experiment; `--oracle surrogate|coarse|llm:<table.json>` (Studies 2 and 3) |
| `sensitivity.py` | One-at-a-time sensitivity (kappa, S_max, p_view, network) -> `results_sensitivity.json` |
| `build_llm_table.py` | Rates the 1,600 coarse states with the Anthropic API (needs `ANTHROPIC_API_KEY`) |

Run: `pip install numpy scipy anthropic`, then `python study1.py`, `python study2.py --reps 40`, `python sensitivity.py`.

## Choices not specified in the manuscript (assumptions)
- Daily profile: floor 0.12 + evening Gaussian (sd 2.2 h) + midday Gaussian at 12.5 h (weight 0.45, sd 1.8 h), normalized to mean one.
- Emotions: excited/angry/happy/indifferent, resampled at each oracle call with probabilities .20/.15/.30/.35.
- Relevance level from the agent's Dirichlet interest weight: low < 0.10 <= medium < 0.30 <= high.
- Surrogate oracle coefficients (`surrogate_core`), and the coarse surrogate evaluated at bin representatives.
- Replies/retweets pick feed items with recency weight exp(-age/2 h); this was added to bring reply delays near the manuscript's, it is not in the manuscript.
- Study 1 references are stylized assumptions (piecewise-linear bimodal profile; log-normal delay, median 0.5 h, sigma 1.2, truncated at 48 h).
- Campaign: injected at 18:00 of day 1 (after an 18 h warm-up); outcomes counted over the following 48 h. The distributed pool excludes only the three seeded influencers.
