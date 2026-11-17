# Replication materials

**Consistent but Not Valid: How LLM Labels Bias Class-Specific Estimates** (Letter, *Political Analysis*)

## Status of this package

| Output | Script | Runs now? |
|---|---|---|
| Figure 1 | `code/make_figure1.py` | Yes. Uses the published estimates in SI Table S2 |
| SI Table S4 | `code/table_s4_hypergeometric.py` | Yes. Exact hypergeometric computation |
| Check of Table 2 and SI Table S3 | `code/check_decomposition.py` | Yes. Recomputes equations (1) and (2) from the published cell counts and means |
| Table 1 Panel B, SI Table S2, Table 2, SI Table S3 from raw data | `code/analysis.py` | Needs `data/posts.csv` and `data/events.csv` (see `data/README.md`). `--demo` runs it on synthetic data |
| Tick-level sample construction, placebos, pre-post drift, robustness (SI S6) | — | **Not included.** Add the original code |
| Correction simulation: naive, human-only, PPI, DSL (SI S5) | — | **Not included.** Add the original code |
| LLM labelling runs (SI S1) | — | **Not included.** Add prompts, raw outputs, and run scripts |

Before depositing in the Political Analysis Dataverse, add the missing code and the data files listed in `data/README.md`, and run every script from a clean copy.

## Requirements

Python 3.11 or later.

```bash
pip install -r requirements.txt
```

## Running

From the `code/` folder:

```bash
python make_figure1.py
python table_s4_hypergeometric.py
python check_decomposition.py
python analysis.py --demo
```

Once the data files are in place:

```bash
python analysis.py
```

All outputs are written to `output/`.

## What each script does

- **`make_figure1.py`** draws Figure 1: class means by label set (panels A and B) and the human-minus-model escalation difference with day-clustered 95% confidence intervals (panel C).
- **`table_s4_hypergeometric.py`** computes how many of the 10 human escalation events (and 32 de-escalation events) a random validated subset of 19, 38, 57, 76, or 96 posts contains.
- **`check_decomposition.py`** recomputes the model-label mean (equation 1) and every term of equation (2) from the published cell counts and means, and checks them against the published values to within rounding.
- **`analysis.py`** computes, from post- and event-level data: Cohen's κ with bootstrap intervals, Gwet's AC1, and precision and recall by class (Table 1, Panel B); class means, medians, and Wilcoxon tests by label set, and the human-minus-model escalation difference with a day-clustered bootstrap (10,000 resamples) (SI Table S2); and the misclassification decomposition (Table 2 and SI Table S3).

## Notes

- `analysis.py` is written to reproduce the published definitions. It has been tested only on synthetic data, so confirm that it reproduces the published numbers on the real data before depositing.
- Random seeds are fixed (`SEED = 20261014` in `analysis.py`). Bootstrap intervals will differ slightly from the published ones unless the original resampling code and seed are used.
