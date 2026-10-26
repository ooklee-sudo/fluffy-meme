#!/bin/bash
# Main run: seeds 0-9 with the settings fixed from the pilot (passed in as $EXTRA_ARGS).
cd /workspace/exp
pip install -q "transformers>=4.56,<5" peft scipy matplotlib 2>&1 | tail -1
mkdir -p /workspace/out
(cd /workspace/out && python -m http.server 8000 >/dev/null 2>&1 &)
python seed_study.py --seeds ${SEEDS:-0-9} $EXTRA_ARGS --out /workspace/out/results_seeds >> /workspace/out/log.txt 2>&1
python aggregate.py /workspace/out/results_seeds --figdir /workspace/out/figs_seeds > /workspace/out/aggregate.txt 2>&1
touch /workspace/out/DONE
sleep 36000
