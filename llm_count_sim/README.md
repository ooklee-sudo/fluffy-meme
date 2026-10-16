# LLM synthetic customers vs. real count distributions

Research code and plan for testing whether LLM-simulated customers reproduce real purchase-count distributions (Poisson / negative binomial / zero-inflated).

| File | Role |
| --- | --- |
| `docs/research_plan.md` | Research questions, hypotheses, design, preliminary results |
| `count_metrics.py` | Dispersion, zero share, distances, Cameron–Trivedi test, Poisson/NB/ZIP AIC, IRR |
| `synthetic_customers.py` | Ground-truth generator and conditions A–D (MockLLM stand-in) |
| `evaluate.py` | Real-vs-synthetic comparison pipeline |
| `run_simulation.py` | Offline simulation, writes `results/` tables and figures |
| `real_data_profile.py` | Profiles real count distributions (UCI Online Retail II, CDNOW) → `results/real_profile.csv` |
| `llm_client.py` | Optional real-LLM backend (Anthropic API), not run offline |

```bash
pip install numpy scipy pandas statsmodels matplotlib
python run_simulation.py --n 5000 --reps 20
python run_simulation.py --preset retail2   # calibrated to Online Retail II
python real_data_profile.py --retail2 online_retail_II.xlsx --cdnow CDNOW_sample.txt
```

`MockLLM` encodes assumed failure modes; results from it validate the pipeline, not any real model.
