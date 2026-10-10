# P4 exploratory test across seven public repositories

Extends p4_pilot_aider/ (Aider only). Outcome: self-admitted debt (SATD) markers in added Python comment lines.
Predictor: LLM-assisted commit. P4 predicts fewer markers per unit of detected debt; rational acceleration predicts none.

## Sample
- Aider-AI/aider: LLM = author name contains "(aider)" (window from 2024-06-18).
- Six repos where commits carry a Claude co-author / "Generated with Claude Code" trailer (window from 2025-01-01):
  BerriAI/litellm, mlflow/mlflow, pydantic/pydantic-ai, PrefectHQ/fastmcp, simonw/datasette, crewAIInc/crewAI.
  Chosen from ten screened repos (screen.sh): the other four had 12-49 marked commits (python-sdk, marimo, langchain, llama_index).
- Authors kept: >= 8 marked and >= 8 unmarked .py-touching commits (agent accounts such as "Copilot"/"Claude" excluded).
  22,176 commits, 43 authors, 4,811 LLM-marked. litellm limited to its 12,000 most recent qualifying commits.
- Debt introduced = increase in ruff warnings (C901, PLR09xx, PLR2004, SIM, ERA001, B; noqa ignored) parent -> child.

## Results (Poisson; controls: debt, log added lines, author FE, repo-quarter FE; SE clustered by author)
| | Strict (584 events) | Broad (910 events) |
|---|---|---|
| Pooled IRR | 0.48 [0.24, 0.96] | 0.40 [0.23, 0.69] |
| + comment-lines control | 0.51 [0.27, 0.98] | 0.42 [0.25, 0.71] |
| Excluding Aider | 0.66 [0.44, 1.01] | 0.60 [0.43, 0.84] |
| Random-effects average, 6 repos | 0.47 [0.23, 0.97] (I2 69%) | 0.46 [0.29, 0.72] (I2 57%) |

Per repo: below 1 in five of six repos with enough events; mlflow ~1.0 (1.04 / 1.02); crewAI has too few events.

## Caveats
Disclosed AI use only (undisclosed use biases toward zero); team or tool conventions may discourage TODOs;
task selection into LLM use not random; ruff is a proxy; broad marker list was defined after seeing counts;
not preregistered; heterogeneity is substantial.

## Reproduce
screen.sh (blobless bare clones + counts) -> full bare clones into /home/user/full -> runall.sh/pipeline.py
(per-repo CSVs) -> analysis_multi.py (needs the Aider extraction in p4_pilot_aider: extract3.py, lint.py).
pooled_pseudonymized.csv is the pooled commit-level dataset (author names and e-mails replaced by hashed ids).
