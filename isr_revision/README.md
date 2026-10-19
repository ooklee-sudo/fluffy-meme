# ISR manuscript revision kit

| file | content |
|---|---|
| `ISR_manuscript_draft_3.docx` | draft 2 with the "Working draft" note removed and the figure alt text no longer duplicating the captions |
| `1_theory_reframing.md` | mechanism-based replacement for Section 2 (post-hoc propositions P1'-P5' with falsification conditions) |
| `2_robustness_design.md` | preregistered confirmatory design (402 worlds in three blocks) |
| `analysis/analyze_worlds.py` | factorial models with robust SEs, Holm/BH correction, candidacy GEE, win-given-standing conditional logit |
| `analysis/mechanism.py` | conditional logit of allocation rules (rotation, need, self-allocation, reciprocity) with a random-draw placebo |
| `3_results_real_data.md` | results from the real logs (144 + 24 worlds) and what they imply for the manuscript |
| `convert_logs.py` | converts `agent_econ/results` event logs into the three tables below |
| `analysis/capability.py` | Flash vs Pro: candidacy and win-given-standing |
| `results_real/` | aggregate outputs of the analysis on the real logs (raw logs are not committed) |
| `make_synthetic.py` | synthetic logs with planted effects, used only to test the pipeline |

## Input schema (replace `data_synthetic/` with the real event-log extracts)

- `worlds.csv`: `world_id, seed, authority, rule, population, rent, n_elections, n_nocand, n_contested, gini, reelect, transfers`
- `elections.csv`: one row per agent per election: `world_id, election_id, agent_id, family, capability, stood, won, energy_rank_before, held_before`
- `allocations.csv`: one row per agent per task slot: `world_id, day, slot, agent_id, holder_id (-1 if vacant), binding_active, received, cum_tasks_before, energy_before, gifted_holder_before` (add `rent` to split by rent level)

```
python convert_logs.py /path/to/agent_econ/results data_real   # real logs -> data_real/main, data_real/h2
python make_synthetic.py data_synthetic
python analysis/analyze_worlds.py data_synthetic    # about 2 min
python analysis/mechanism.py data_synthetic
```

Needs `numpy pandas scipy statsmodels`. The synthetic data contain no information about the paper's results.
