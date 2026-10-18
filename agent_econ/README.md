# agent_econ: executable LLM-agent world for the power-concentration study

- `world.py` – scarce tasks, energy transfers, access promises, elections (plurality / approval / ranked-choice), binding vs advisory allocation, optional public record, survival vs neutral framing.
- `metrics.py` – outcomes computed only from logged events (Gini, holder spells, exclusion spells, vote-for-access exchanges, promise honor rate).
- `llm.py` – OpenRouter client; every call is added to `results/spend.json`; calls stop at `AE_BUDGET_USD` (default 45).
- `run_world.py` – one world; `run_pilot.py` – pilot grid.

Needs `OPENROUTER_API_KEY` in the environment. Never commit keys.

`--models scripted` runs rule-based placeholder agents to test the pipeline. Their output is marked `"evidence": false` and must not be reported as results.
