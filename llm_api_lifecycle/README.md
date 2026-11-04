# Replication package: "Managing LLM Maintenance Uncertainty: A Real Options View of Cloud API Lifecycles"

Ook Lee, Hanyang University (ooklee@hanyang.ac.kr)

This package contains the data, code, and reference outputs needed to reproduce every table, simulation result, and figure in the manuscript.

## Quick start

Requires Python 3.9 or later.

```bash
pip install -r requirements.txt
cd sim
python reproduce.py
```

`reproduce.py` runs all steps in order and writes outputs to `results/`. It takes under a minute on a laptop. All random draws use fixed seeds, so the outputs match the reference files in `results/` exactly.

## What reproduces what

| Manuscript item | Script (in `sim/`) | Output (in `results/`) |
| --- | --- | --- |
| Check against the analytical break-even (1 − φ)KΛ and θ values (sidebar) | `verify.py` | printed |
| Table 1: lifetimes (Kaplan–Meier, censored) and notice by vendor | `table_life.py` | `table_life.csv` |
| Table 2: savings and break-even premium by vendor and price scenario | `run_all.py` | `results_scenarios.csv` |
| Notice policy: Anthropic lifetimes under Anthropic vs Bedrock notice; Gemini previews | `run_notice.py` | `results_notice.csv` |
| Early switching: NPV rule vs option threshold | `run_switch.py` | `results_switch.csv` |
| Figure 1 | `fig1.py` | `fig1_framework.png` |

## Contents

| Path | Description |
| --- | --- |
| `data/gemini_lifecycle.csv` | Gemini API models: release, announcement and shutdown dates, replacements (103 rows) |
| `data/openai_lifecycle.csv` | OpenAI API models (150 rows) |
| `data/other_lifecycle.csv` | Anthropic API, AWS Bedrock, Azure OpenAI, Azure AI Foundry, Vertex AI (486 rows) |
| `data/openai_prices.csv`, `data/anthropic_prices.csv` | Predecessor and successor list prices |
| `data/gemini_quality.md` | Gemini blended prices, Arena scores, and quality-matched replacement ratios |
| `data/cases.md` | Notes and quotations from the two industry migration reports |
| `data/*_notes.md` | Collection method, definitions, and known gaps for each source |
| `sim/sim.py` | 36-month lifecycle simulation (rigid, flex, flex + NPV, flex + threshold) |
| `sim/km.py`, `sim/samplers.py` | Kaplan–Meier estimation; Weibull fit to censored lifetimes used for sampling |
| `sim/data.py` | Vendor subsets used in the analysis |
| `verify/live/` | Row-by-row checks of the data against live official pages (669 checks) |
| `verify/wayback/` | Checks of the Gemini data against archived Google pages, and scripts to rerun them |
| `results/` | Reference outputs |

## Data

Lifecycle data were retrieved from vendor pages on 4 November 2026 (Google Gemini API deprecations, release notes and pricing; OpenAI deprecations; Anthropic model deprecations; AWS Bedrock model lifecycle; Azure and Vertex AI lifecycle pages). Each CSV row records its sources in `announce_source`, `release_source` and `notes`. Column definitions:

- `release_date`: first public availability on the platform.
- `announce_date`: first publication of a day-level shutdown date (Bedrock: the Legacy date). `announce_date_lower`, where given, is the last date on which the shutdown date was known not to be published.
- `shutdown_date` and `shutdown_status`: `retired` (on or before 2026-11-04), `scheduled`, `redirected` (endpoint routed to a newer model), or `none`.

Vendor pages revise dates and replacement names over time. `verify/` documents the checks made and their results; remaining gaps are listed in `verify/wayback/SUMMARY.md` and the `*_notes.md` files.

## Model settings

Settings are in the function signature of `simulate()` in `sim/sim.py`: 36-month horizon, 10% annual discount rate, labor at USD 91.5 per hour, migration effort triangular (2, 4, 10) person-weeks, flexibility premium 6 person-weeks, effort factor φ = 0.5, 50% surcharge when notice is shorter than the migration takes, USD 2,000 per day of outage, 1 billion tokens per month at USD 1.25 per million, and monthly price volatility 10%. Price-ratio sets are defined at the top of `sim/run_all.py` and `sim/run_switch.py`.

## Provenance

Data collection, verification, and code were prepared with the assistance of an AI system (Claude, Anthropic) under the author's direction. All values used in the analysis were checked against primary sources as documented in `verify/`.
