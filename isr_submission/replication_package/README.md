# Replication package: "Reach Before Price" (version 2)

Code and derived data for the manuscript and Online Appendix. All numerical results in the paper are illustrations
at the parameters of Table 2 of the manuscript (a=20, b=0.12, B=1.6, c0=0.8, k=0.1, A0=0.5, ln kappa ~ N(ln 4.8, 0.9^2)).
They are not calibrated to any market.

## Layout
- `code/` all scripts (flat; run from this directory so that local imports work)
- `data/` derived tables used in the paper (CSV)
- `figures/` Figures 1-5 (PNG) and `fig_cache.npz` (cached profit curve)
- `requirements.txt`, `download_data.sh`, `LICENSE`

## Environment
Python 3.13 (3.11+ should work). `pip install -r requirements.txt`. PyMC/ArviZ and pymongo are needed only for the
estimation-machinery and Jira-extraction scripts. No GPU needed.

## Quick check (1-3 minutes)
    cd code
    python3 reproduce_key_numbers.py
Recomputes Table 1, the closed forms at parity (Pi*(1)=5.7729, right derivative 13.195, theta-hat=46.18), the entry
threshold, conditions (Q) and (Q'), and the A=0.9 / A=1.0 linear-price profits, and prints OK/MISMATCH for each.

## Figures (3-6 minutes; faster with the cache)
    cd code && python3 make_figures.py          # writes ../figures/fig1..fig5

## Where each result comes from
| Result | Script |
|---|---|
| Adoption set, profit, price, menus | vendor_model.py, vendor_menu.py (LP bound), vendor_menu_det.py (MILP menu) |
| Kink and bunching (Props 7-8) | kink_asymptotics.py (`python3 kink_asymptotics.py`) |
| Investment jump, subsidy (Props 6, 9) | vendor_investment.py, vendor_investment_policy.py |
| Liability, duopoly, signaling | vendor_strategic.py, vendor_signaling.py, vendor_signaling_complexity.py |
| Duopoly race, learning, private reach | vendor_dynamics.py (`race`, `learn`, `private`; coarse grid) |
| NHPP regression layer (simulation only) | nhpp_llm_econ.py, coverage_check.py (60 replicates, ~hours), sensitivity.py |
| Public-data analyses | jira_extract_bugs.py, jira_nhpp.py, swe_agent_curve.py, swe_beta_model.py, pilot_cursor_package.py, cursor_adoption_by_popularity.py, collect_issue_labels_gql.py |

## Public raw data
Not redistributed. `download_data.sh` lists sources (Zenodo, Hugging Face). The Jira extraction streams a ~56 GB
MongoDB dump and takes roughly 6-10 minutes plus download time. `collect_issue_labels_gql.py` needs a GitHub token in the
environment variable `GITHUB_TOKEN`. **Never put a token in a file or commit it.**
The derived results (`data/*.csv`) are included so that the paper's tables can be checked without the large downloads.

## Known limits
- Grid-based calculations (vendor_menu*.py, vendor_dynamics.py) are sensitive to grid size; magnitudes move by a few percent, orderings do not.
- The global maximum behind Proposition 8 and theta_low = 27.58 are numerical.
- Social threshold theta_s = 65.09 depends on the reach cap 1.3 chosen in make_figures.py.

## Version 2: empirical reach of LLM-written unit tests (EMSE manuscript)
Folder `empirical/` (added in version 2). Needs network access to the model gateway (OpenRouter; set `OPENROUTER_API_KEY`), git, and
Python 3.8-3.13 virtual environments created by the scripts. No GPU.

| Part | Scripts | Results |
|---|---|---|
| Mutation study (11 modules of toolz, boltons, humanize, cachetools, more-itertools; 7 with >= 30 mutants analysed) | `empirical/mutation/mutation_study.py` (operators in `mutation_pilot.py`, targets in `targets.json`) | `empirical/mutation/results/*.json` (per module: human kill vector, and per model and attempt the number of passing tests and the kill vector) |
| Harness check and fix | `check_ids.py` (finds truncated test ids), `recompute_kills.py` (recomputes kill vectors from the stored generated tests, no new LLM calls) | see Note below |
| Real faults (BugsInPy) | `empirical/bugsinpy/bip_lib.py`, `bip_validate.py`, `bip_study.py`, `bip_calibrate.py` | `empirical/bugsinpy/results/*.json` (per bug and model: six attempts with test counts, failures on the faulty version and detection), `valid_bugs.json` |
| Tables and figure of the EMSE manuscript | `empirical/emse_analysis.py` | `empirical/emse_results.json`, `emse_mutation_modules.csv`, `emse_fig_reach.png` |

Run order: `python3 bip_validate.py --projects ...` then `python3 bip_study.py run --models <comma list> --k 6 [--shard i/n]`, then
`python3 emse_analysis.py`. The mutation study: `python3 mutation_study.py run --models <comma list> --k 8 --max-mutants 150`.

Note (harness correction). The first harness read the names of passing tests from pytest's console output. Names containing
spaces were truncated, and one project forces coloured output; in both cases the follow-up run failed to collect the test and every
mutant was counted as killed (or, with colour, every generated test was discarded). This affected humanize (both modules) and 5 of
24 attempts on boltons/strutils. The harness now reads exact test ids from JUnit XML; the affected kill vectors were recomputed from
the stored generated tests with `recompute_kills.py`. All other modules were unaffected (`check_ids.py`).
