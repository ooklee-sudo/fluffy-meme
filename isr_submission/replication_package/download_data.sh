#!/usr/bin/env bash
# Download the public raw data used in Section 7 / Online Appendix F. Nothing here is redistributed in this package.
set -euo pipefail
mkdir -p raw && cd raw
# Public Jira Dataset (Montgomery, Lueders, Maalej), CC-BY-4.0. About 5.8 GB. Zenodo DOI 10.5281/zenodo.5882881
echo "Public Jira Dataset: open https://zenodo.org/doi/10.5281/zenodo.5882881 and download the MongoDB dump (zip)."
# SWE-bench Verified (human difficulty labels) and a published single-run result, via Hugging Face
curl -L -o swebench_verified.parquet "https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified/resolve/main/data/test-00000-of-00001.parquet" || true
echo "Agent trajectories: https://huggingface.co/datasets/nebius/SWE-agent-trajectories (12 shards; the scripts read them via huggingface hub)."
echo "o1 run on SWE-bench Verified: https://huggingface.co/datasets/AlexCuadron/SWE-Bench-Verified-O1-reasoning-high-results"
echo "AI-coding-assistant adoption replication package: https://zenodo.org/records/18368661 (663 MB)."
echo "Issue labels: run  GITHUB_TOKEN=<your token> python3 ../code/collect_issue_labels_gql.py ../data/pilot_pass_repos.csv issue_labels.csv"
echo "(The token is read from the environment and must never be committed or shared.)"
