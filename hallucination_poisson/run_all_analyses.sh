#!/bin/sh
# Re-run every analysis used in the paper (needs runs/{qwen05,smol360,qwen15}/records.jsonl).
cd "$(dirname "$0")"
for r in qwen05 smol360 qwen15; do
  python run_experiment.py analyze --run runs/$r --daily-queries 200 --days 90 --sla-ms 100 --tag _sla100 > runs/$r/analysis_sla100.txt 2>&1
  python run_experiment.py analyze --run runs/$r --daily-queries 200 --days 90 --sla-ms 500 --tag _sla500 --c-false-block 1 --c-residual 100 > runs/$r/analysis_sla500.txt 2>&1
  python run_experiment.py analyze --run runs/$r --daily-queries 200 --days 90 --sla-ms 500 --burst-cv 0.3 --tag _burst > runs/$r/analysis_burst.txt 2>&1
  python run_experiment.py analyze --run runs/$r --daily-queries 200 --days 90 --sla-ms 500 --burst-cv 0.44 --profile-file runs/real_data.json --tag _burst044 > runs/$r/analysis_burst044.txt 2>&1
done
python paper_tables.py > runs/paper_tables.txt
python summarize.py > runs/summary.txt
