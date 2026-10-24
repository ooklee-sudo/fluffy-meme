# Replication package

Paper: *Do Influencers Pay? Limited Attention, Engagement Elasticity, and Simulation-Based Pre-Tests for Seeding Decisions* (anonymized for review).

This package contains (i) the event-driven simulator, (ii) the scripts that run every simulation experiment and build Tables 2–6 and Figures 1–2, (iii) the synthetic-data validation of the estimator (Online Appendix B, Table B.1), and (iv) the script that estimates the engagement elasticity on SAGraph (Section 6, Table 7). All outputs used in the paper are in `results/`.

## Contents
| Path | What it does | Paper |
|---|---|---|
| `code/simulator.py` | Rule-based agent simulator: preferential-attachment follower graph, five personas, inhomogeneous-Poisson intensity with decaying stimuli (thinning), rule-based urge function, exposure rule with engagement elasticity β, four schedulers, seed plans | Sections 3–4, Online Appendix A |
| `code/run_experiments.py` | Runs the experiments (paired replications) and stores per-run adoption times in `results/runs/*.json.gz` | Section 5 |
| `code/analyze.py` | Tables 2–6, dominance checks, Eq. (2) check, Figures 1–2 (`results/tables_simulation.md`, `results/summary.json`, `results/figures/`) | Section 5 |
| `code/validate_estimator.py` | Synthetic-data recovery of β and of the daily profile (`results/tableB1_validation.csv`) | Online Appendix B |
| `code/sagraph_elasticity.py` | PPML and zero-truncated Poisson estimates of β on SAGraph (`results/table7_estimates.csv`) | Section 6 |
| `run_all.sh` | Runs everything | |

## Requirements
Python ≥ 3.10; `pip install -r requirements.txt`. The simulations take about 30 minutes on 4 cores (about 7 s per run; 810 runs). The SAGraph estimation takes about 2 minutes and needs 8 GB of memory.

## Data
SAGraph (Zhang et al., 2025; CC-BY 4.0): https://github.com/xiaoqzhwhu/SAGraph (data folder on Google Drive: `https://drive.google.com/drive/folders/1_JkyudTJcrrduKx8_G87PocSVSISUZK-`). Download, e.g.,
```python
import gdown; gdown.download_folder(id="1_JkyudTJcrrduKx8_G87PocSVSISUZK-", output="sagraph")
```
and pass the folder to `run_all.sh` or `sagraph_elasticity.py --data-dir`. The raw data are not redistributed here. `results/sagraph_posts.csv.gz` contains the derived post-level table (product, anonymized author id, followers, counts) used for estimation, with no text.

## How to reproduce
```bash
pip install -r requirements.txt
bash run_all.sh /path/to/sagraph          # or: bash run_all.sh   (skips SAGraph)
```
Scripts skip simulation files that already exist, so `analyze.py` can be re-run on the shipped `results/runs/`. Randomness: replication *r* of both plans uses world seed *r* (network, personas, interests) and the Python generator seeded from *r*; the distributed seed set uses a generator seeded with 10,000 + *r*; bootstrap intervals use a fixed seed. Results are reproducible on the same Python and NumPy versions; across versions, random streams for `numpy` generators are stable, but floating-point details may change the last digit.

## Implementation notes and assumptions
Parameters not fixed by the paper's text are listed here and in Online Appendix A:
- Accounts without followers cost one follower-equivalent when seeds are priced, so that the equal-link budget buys a finite number of ordinary accounts.
- Likes create no items and no notifications; adoption is the first comment or retweet of campaign content by an agent that is not a seed.
- The comment/retweet target is drawn from the agent's feed (40 most recent items, excluding its own) with probability proportional to its interest in the topic times exp(−age/2 h); if the feed is empty the agent posts.
- Volume matching for the alternative schedulers multiplies baseline rates by the ratio of total events under the event-driven and circadian-only schedulers in pilot runs without a campaign (`results/volume_multiplier.json`).
- Circadian profile: 0.12 + evening Gaussian at the chronotype (sd 2.2 h) + 0.45 × midday Gaussian at 12.5 h (sd 1.8 h), normalized to mean one, at 15-minute resolution.
- SAGraph: a post is a unique pair of author and post text; the reported author counts are author–campaign pairs; standard errors are clustered by author within campaign.
- Synthetic validation: the paper fixes the structure but not the random-effect scales; the values used are constants at the top of `validate_estimator.py`.
