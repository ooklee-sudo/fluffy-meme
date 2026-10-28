#!/bin/bash
# Launch (or resume) the three model runs in the background (threads; one process per model).
cd "$(dirname "$0")"; source tau2-bench/.venv/bin/activate
declare -A W=([llama8b]=24 [llama70b]=24 [deepseek]=20)
for m in llama8b llama70b deepseek; do
  if ! pgrep -f "^python inject_run.py $m" >/dev/null; then
    R=3; [ $m = deepseek ] && R=2
    nohup python inject_run.py $m --reps $R --workers ${W[$m]} --cap 350 >> logs_$m.out 2>> logs_$m.err &
  fi
done
