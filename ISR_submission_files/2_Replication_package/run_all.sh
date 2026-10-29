#!/usr/bin/env bash
# Reproduce every table and figure that does not require model training (about 6 minutes on a laptop CPU).
# Usage: bash run_all.sh        (run from this directory)
set -euo pipefail
mkdir -p results figures
python code/release_intensity.py   | tee results/table3_release_intensity.txt
python code/policy_regions.py      | tee results/table4_policy_regions.txt
python code/monopoly_duopoly.py    | tee results/tables5_7_duopoly.txt
python code/arrival_robustness.py  | tee results/table6_arrival_robustness.txt
python code/vendor_sensitivity.py --out results/sensitivity.json --plot figures/fig5_sensitivity.png | tee results/appendix_F_sensitivity.txt
python code/make_figures.py
for d in seeds_gpu seeds_large_gpu tasks_small_gpu tasks_large_gpu; do python code/aggregate_seeds.py results/$d > results/aggregate_$d.txt; done
python code/analysis_all.py        | tee results/table_C3_all_tasks.txt
python code/check_against_paper.py | tee results/check_against_paper.txt
