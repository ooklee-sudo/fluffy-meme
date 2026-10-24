#!/bin/bash
# Execute the samples already collected while sampling continues, then execute the remainder.
cd "$(dirname "$0")"
cp data/samples.jsonl data/samples_part1.jsonl
python3 execute.py --samples data/samples_part1.jsonl --out data/results.jsonl --workers 3 &
P1=$!
while pgrep -f "python3 generate.py" > /dev/null; do sleep 20; done
wait $P1
python3 execute.py --samples data/samples.jsonl --out data/results.jsonl --workers 4
echo ALL_DONE
