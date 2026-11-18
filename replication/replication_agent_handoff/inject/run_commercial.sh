#!/bin/bash
# Launch (or resume) the tau2-bench runs for the two commercial models (two repetitions, as for DeepSeek-V3.1).
cd "$(dirname "$0")"; source tau2-bench/.venv/bin/activate
for m in gpt61terra sonnet55; do
  if ! pgrep -f "^python inject_run.py $m" >/dev/null; then
    nohup python inject_run.py $m --reps 2 --workers 16 --cap 400 >> logs_$m.out 2>> logs_$m.err &
  fi
done
