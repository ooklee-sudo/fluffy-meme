#!/usr/bin/env bash
# Reproduces every table and figure. About 30 minutes on 4 cores for the simulations; a few minutes for SAGraph.
# Usage: bash run_all.sh /path/to/sagraph_data   (folder with <product>_profile.graph.anon / _interaction.graph.anon)
set -euo pipefail
SAG="${1:-}"
cd "$(dirname "$0")/code"
python run_experiments.py --out ../results          # Section 5 (writes results/runs/*.json.gz; skips files that exist)
python analyze.py --results ../results              # Tables 2-6, Figures 1-2, summary.json
python validate_estimator.py --out ../results       # Online Appendix B, Table B.1
if [ -n "$SAG" ]; then
  python sagraph_elasticity.py --data-dir "$SAG" --out ../results   # Section 6, Table 7
else
  echo "Skipping SAGraph (pass the data folder as the first argument; see README)."
fi
