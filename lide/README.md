# LIDE harness

Code for "When Delegated Agents Escalate: Loss-Induced Decision Escalation and the Governance of Agentic
Information Systems" (Section 4). Separate from the real-options code in the repository root.

| Module | Paper | What it does |
| --- | --- | --- |
| `taxonomy.py` | 4.3 | Action scores (reversibility, scope, compliance) -> ex ante risk in [0,1] |
| `history.py` | 4.2, 4.5, Table 3 | Conditions; histories padded to identical length (5,410 chars coding / 1,852 operations); full vs summary record |
| `envs.py` | 4.2 | Environment A (coding, unsatisfiable tests), B (operations); artifacts: default exit, stop-loss, confirmation friction |
| `agents.py` | 4.5 | Scripted honest / escalating agents; `ProspectAgent` (simulated positive control, **not evidence about LLMs**) |
| `llm_agent.py` | 4.1 | Anthropic tool-use agent for the live runs |
| `runner.py` | Table 3 | Study 1, Study 2, failure-signal block; episode records |
| `analysis.py` | 4.3-4.4 | LIDE classifier, known-groups table, mixed logit, H1 segmented, H2 contrast, H3b, H4, H5 |

```bash
pip install -r requirements-lide.txt
pytest lide/tests                                                     # construction checks (4.5)
python -m lide.runner --agents scripted --reps 10 --out results/lide/scripted.csv
python -m lide.analysis results/lide/scripted.csv                     # Table 5 analogue; LIDE = 0
python -m lide.runner --agents sim --reps 20 --out results/lide/sim.csv
python -m lide.analysis results/lide/sim.csv                          # pipeline recovers built-in effects
ANTHROPIC_API_KEY=... python -m lide.runner --agents llm --models <model-id> --reps 5 --out results/lide/live.csv
```

## Differences from the manuscript (check before citing)

- **Cell count (reconstructed).** The manuscript gives only totals (72 cells, 1,440 episodes, 360 per agent x
  environment), so the cell definition is inferred: per environment, Study 1 = 24 (valence x scarcity, with
  record crossed only for failure histories because the summary is identical to the full record otherwise),
  Study 2 = 10 (5 artifact levels x neutral/fail8, deadline cue), failure-signal block = 2; 36 x 2 environments
  = 72. A test checks 1,440 episodes and 360 per row. Confirm this matches your intended design. Table 5 values
  still will not reproduce exactly because per-step risk scores are placeholders.
- **Stop-loss** is implemented as: after 3 consecutive failures (history + episode) only verify / ask / exit tools
  work. Friction blocks calls with risk >= 0.5 unless `confirm=true`. Scripted agents always confirm.
- **Taxonomy scores** are placeholders for the blind Delphi panel; replace before data collection.
- **Mixed model** uses statsmodels' variational-Bayes `BinomialBayesMixedGLM` (random intercepts for model and
  task); `record` main effect is only identified when Loss > 0. H3b uses a Wilcoxon test on step indices, not a
  full event-history model. H1's breakpoint is chosen in-sample.
- The `sim` agent's parameters are made up; its results only show the analysis code can detect effects when
  they exist. Live-agent results must come from `--agents llm`.
