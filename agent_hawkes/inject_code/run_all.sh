#!/bin/bash
# Launch (or resume) the coding-agent fault-injection runs for the three models.
cd "$(dirname "$0")"
for m in llama8b llama70b deepseek; do
  if ! pgrep -f "^python3 code_inject.py $m" >/dev/null; then
    nohup python3 code_inject.py $m --reps 2 --workers 12 --cap 80 >> logs_$m.out 2>> logs_$m.err &
  fi
done
