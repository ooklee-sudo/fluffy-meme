# LLM API lifecycles as real options (IEEE IT Professional manuscript)

Data, simulation code, and results for "Managing LLM Maintenance Uncertainty: A Real Options View of Cloud API Lifecycles."

## Contents

| Path | What it is |
| --- | --- |
| `data/gemini_lifecycle.csv` | Gemini API models: release, announcement, and shutdown dates (103 rows) |
| `data/openai_lifecycle.csv`, `data/openai_prices.csv` | OpenAI API models (150 rows) and predecessor/successor price pairs |
| `data/other_lifecycle.csv`, `data/anthropic_prices.csv` | Anthropic API, AWS Bedrock, Azure, Vertex AI (486 rows) and Anthropic price pairs |
| `data/gemini_quality.md` | Gemini blended prices, Arena and GPQA scores, quality-matched replacement ratios |
| `data/cases.md` | Notes and quotes from the two industry migration reports (Tursio, Verint) |
| `data/*_notes.md` | Collection method, definitions, and known gaps for each source |
| `sim/sim.py` | 36-month chatbot lifecycle simulation (rigid, flex, flex + NPV, flex + threshold) |
| `sim/km.py`, `sim/samplers.py` | Kaplan–Meier estimates with censoring; Weibull fit used to draw lifetimes |
| `sim/table_life.py` | Table 1 (lifetimes and notice by vendor) |
| `sim/run_all.py` | Table 2 (savings and break-even premium by vendor and price scenario) |
| `sim/run_switch.py` | Early-switching comparison (NPV rule vs. option threshold) |
| `sim/verify.py` | Checks the simulation against the analytical break-even (1 − φ)KΛ and the θ values |
| `sim/fig1.py` | Figure 1 |
| `results/` | Outputs of the scripts above |
| `manuscript/` | Manuscript (.docx) |

All web data were retrieved on 2026-11-04. Lifecycle pages change and rewrite replacement names over time; see the notes files for caveats.

## Run

```bash
pip install numpy pandas scipy matplotlib
cd sim
python verify.py
python table_life.py
python run_all.py
python run_switch.py
```
