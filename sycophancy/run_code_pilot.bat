@echo off
rem Code sycophancy pilot: runs every pushback condition one after another, then compares them.
rem   run_code_pilot.bat          all 290 items per condition
rem   run_code_pilot.bat 40       quick test with 40 items (separate output folders)
rem Logs go to logs\, results to runs\. Rerunning skips items that are already done.

set MODEL=Qwen/Qwen3-4B
set TAG=code_q4b
set NARG=
set SUF=
if not "%1"=="" (
  set NARG=--n %1
  set SUF=_n%1
)
if not exist logs mkdir logs

rem Most important first: neutral control, doubt, evidence, then the track-record series.
for %%c in (recheck doubt evidence track50 track20 track80 authority) do (
  echo [%time%] %%c
  python code_challenge.py --model %MODEL% --challenge %%c %NARG% --out runs\%TAG%_%%c%SUF% > logs\%TAG%_%%c%SUF%.txt 2>&1
)

python code_challenge_compare.py runs\%TAG%_recheck%SUF% runs\%TAG%_doubt%SUF% runs\%TAG%_evidence%SUF% runs\%TAG%_track20%SUF% runs\%TAG%_track50%SUF% runs\%TAG%_track80%SUF% runs\%TAG%_authority%SUF% > logs\%TAG%_summary%SUF%.txt
type logs\%TAG%_summary%SUF%.txt
