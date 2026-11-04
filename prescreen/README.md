# Synthetic pre-screening of A/B tests (Upworthy)

Decision-model extension for "When Can Platforms Trust Synthetic Agents?".

- `prep.py` — builds headline-only tests from the public Upworthy confirmatory packages (OSF jd64p) and empirical-Bayes "true" CTRs.
- `twin.py` — asks LLM twins (no-persona prompt from study C2) for click probabilities via OpenRouter.
- `sim.py` — simulates policies at fixed traffic budgets: A test all, B twin keeps top half, C random half, D twin only, E twin as prior.
- `analytic.py` — stylized model: crossover budget N*(rho) below which pre-screening beats testing all arms.
- `report.py` — figure and table.

```bash
curl -L https://osf.io/download/vy8mj/ -o confirmatory.csv
python prep.py confirmatory.csv arms.csv
python twin.py arms.csv twin.jsonl 500 3 anthropic/claude-haiku-5.5,openai/gpt-6-luna,google/gemini-3.7-flash,deepseek/deepseek-v4.1-flash
python sim.py arms.csv twin.jsonl sim_results.json
python report.py sim_results.json .
```
