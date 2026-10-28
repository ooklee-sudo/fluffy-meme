#!/bin/bash
# Launch (or resume) the three model runs in the background.
cd "$(dirname "$0")"; source tau2-bench/.venv/bin/activate
for m in llama8b llama70b deepseek; do
  if ! pgrep -f "^python inject_run.py $m" >/dev/null; then
    nohup python inject_run.py $m --workers 20 --cap 150 > logs_$m.out 2> logs_$m.err &
  fi
done
