# Replication package: "Reach Before Price"

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
