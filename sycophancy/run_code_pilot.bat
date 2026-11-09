@echo off
rem Study 2 objection conditions on code (same protocol as run_code_paper.bat 4b; only the pushback differs).
rem The doubt condition is the main run runs\code_q4b_1024, so it is not repeated here.
rem   run_code_pilot.bat          382 items per condition (the first 382 of the main run), ~7 hours each
rem   run_code_pilot.bat 40       quick test with 40 items (separate output folders)
rem Logs go to logs\, results to runs\. Rerunning skips items that are already done.

set MODEL=Qwen/Qwen3-4B
set TAG=code_q4b
set N=382
set SUF=
if not "%1"=="" (
  set N=%1
  set SUF=_n%1
)
if not exist logs mkdir logs

rem Most important first: neutral control (H2a, H5a), evidence (H3, H5c), then the track-record series (H2b).
for %%c in (recheck evidence track50 track20 track80 authority) do (
  echo [%time%] %%c
  python code_challenge.py --model %MODEL% --challenge %%c --n %N% --out runs\%TAG%_%%c%SUF% > logs\%TAG%_%%c%SUF%.txt 2>&1
)

set RUNS=runs\code_q4b_1024
for %%c in (recheck evidence track20 track50 track80 authority) do (
  if exist runs\%TAG%_%%c%SUF%\results.jsonl call set RUNS=%%RUNS%% runs\%TAG%_%%c%SUF%
)
python code_challenge_compare.py %RUNS% > logs\%TAG%_conditions%SUF%.txt
type logs\%TAG%_conditions%SUF%.txt
