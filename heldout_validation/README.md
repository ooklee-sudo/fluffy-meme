# Replication package

Code and outputs for the held-out replication (Section 5.7), the real-arrival analysis (Section 5.5, WildChat),
and the numerical checks of the tables and propositions (Section 3) of

> *Safety Stock for Machine Error: Standby Labour, Screening Depth and Correlated Risk in LLM Services*

## What is and is not included
| Included | Not included |
|---|---|
| Pre-registered configuration (`PREREG.md`) and every deviation from it (`DEVIATIONS.md`) | Public datasets (SQuAD 2.0, WildChat-1M, BurstGPT, ticket logs, court-case database); `download_data.sh` fetches the first two |
| Pipeline for the 1,000-question replication: generation, L1, L2, local and API judges | The pipeline of the first 300-question evaluation (Sections 5.1-5.4) **[authors: add or delete this line]** |
| Per-question outputs of all generators and judges (`results/*.jsonl`) | Model weights (downloaded from Hugging Face) |
| Analysis scripts and their outputs (`results/analysis_*`, `wildchat_arrivals.json`, `table5.json`, `cost_by_judge.txt`) | |
| Scripts that recompute Tables 1-4, 6, 7 and check Propositions 4 and 5 | |

## Quick check without any model or download (about one minute)
```bash
pip install numpy scipy
python check_tables.py                 # recomputes Tables 1-4, 6, 7; checks Propositions 4(b), 4(c), 5(b); prints ALL CHECKS PASSED
python econ_dependence.py              # Table 5 -> results/table5.json
python analyze_heldout.py qwen1.5b     # Table 12 columns for the local judge, from the stored outputs
python analyze_heldout.py llama70b
python analyze_heldout.py gemma27b
python cost_heldout.py llama70b        # paired daily-cost effect of adding the routed judge
```

## Full replication
```bash
pip install -r requirements.txt
./download_data.sh
./run_all.sh                           # 3 generators x 1,000 questions, then the two local judges; about 5 to 6 hours on 4 CPU cores
export OPENROUTER_API_KEY=...          # only needed outside an environment that supplies credentials
./run_api_judges.sh                    # Llama-3.3-70B and Gemma-3-27B through OpenRouter; about 10 minutes, under 1 USD
python wildchat_arrivals.py            # downloads about 3 GB, deletes each shard after reading the timestamps
python analyze_heldout.py <judge> [credit]
```

## Mapping to the manuscript
| Script | Output | Manuscript |
|---|---|---|
| `check_tables.py`, `econ_dependence.py` | console, `results/table5.json` | Tables 1-7 (Section 3), Propositions 4-5 |
| `run_heldout.py` (`gen`, `judge`), `judge_api.py` | `results/gen_*.jsonl`, `results/judge_*.jsonl` | Section 5.7 |
| `analyze_heldout.py` | `results/analysis_<judge>[_credit].json/.md` | Table 12 and Section 5.7 text |
| `cost_heldout.py` | `results/cost_by_judge.txt` | Section 5.7, daily saving from the routed judge |
| `wildchat_arrivals.py` | `results/wildchat_arrivals.json` | Section 5.5 (WildChat paragraph), Appendix B |

## Things that can differ on another machine
* **Latency and the 2 s timeout.** Judge calls on the local CPU take 1.7-2.5 s, so which calls count as failures depends on the hardware. The classification of the verdicts does not.
* **Greedy decoding** is deterministic for a given library version and hardware, but small numerical differences can change a few answers.
* **API judges** use temperature 0, but hosted models can change; the stored outputs are the ones used in the manuscript.
* **Seeds.** Question sample: `random.Random(20261030)`; bootstrap and simulations: seed 0.
* The original 300-question sample (seed 0) could not be reproduced, so overlap with the 1,000-question sample cannot be excluded (about 3% expected).

## Licences of the inputs
SQuAD 2.0: CC BY-SA 4.0. WildChat-1M: ODC-BY. Model licences are those of the Hugging Face releases. The per-question outputs here contain SQuAD passages and questions and therefore carry the SQuAD licence. Code licence: **[choose, e.g. MIT]**.
