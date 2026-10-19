# agent_econ: executable LLM-agent world for the power-concentration study

- `world.py` – scarce tasks, energy transfers, access promises, elections (plurality / approval / ranked-choice), binding vs advisory allocation, optional public record, survival vs neutral framing.
- `metrics.py` – outcomes computed only from logged events (Gini, holder spells, exclusion spells, vote-for-access exchanges, promise honor rate).
- `llm.py` – OpenRouter client; every call is added to `results/spend.json`; calls stop at `AE_BUDGET_USD` (default 45).
- `run_world.py` – one world; `run_pilot.py` – pilot grid.

Needs `OPENROUTER_API_KEY` in the environment. Never commit keys.

`--models scripted` runs rule-based placeholder agents to test the pipeline. Their output is marked `"evidence": false` and must not be reported as results.

## Study 2 (prompt variation)

`run_study2.py` runs Study 2a-lite (random holder, no election) and the 2b baseline comparison. New `Config` options: `assign_office` (holder drawn uniformly every `term` days), `prompt` (`baseline` | `self_interest` | `collective_duty`) and `paraphrase` (0/1). `metrics.py` adds `holder_self_share`. The "stripped" prompt needs the prompt audit and is not implemented. Scripted runs test the pipeline only and are marked `"evidence": false`.

### Study 2a analysis
`python analysis/study2a_primary.py results/` (primary contrasts, Holm over four tests, paired sensitivity, OLS with paraphrase) and `python analysis/study2a_mechanism.py results/` (keyword manipulation check on message text; within-day conditional logit by prompt with a world bootstrap). Both need pandas, numpy, scipy and statsmodels. The manipulation check is a keyword count, not hand coding.
