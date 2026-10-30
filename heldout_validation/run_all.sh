#!/bin/bash
# Sequential on purpose: latency (2 s timeout) must not be disturbed by concurrent jobs.
cd "$(dirname "$0")"
for g in qwen0.5b smollm360m qwen1.5b; do python3 run_heldout.py gen --gen $g --n 1000; done
for j in qwen1.5b smollm1.7b; do for g in qwen0.5b smollm360m qwen1.5b; do python3 run_heldout.py judge --gen $g --judge $j; done; done
echo ALLDONE
