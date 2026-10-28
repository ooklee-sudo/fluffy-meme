#!/bin/bash
# Launch (or resume) the three model runs in the background (threads; one process per model).
cd "$(dirname "$0")"; source tau2-bench/.venv/bin/activate
declare -A W=([llama8b]=24 [llama70b]=24 [deepseek]=12)
for m in llama8b llama70b deepseek; do
  if ! pgrep -f "^python inject_run.py $m" >/dev/null; then
    nohup python inject_run.py $m --workers ${W[$m]} --cap 150 >> logs_$m.out 2>> logs_$m.err &
  fi
done
