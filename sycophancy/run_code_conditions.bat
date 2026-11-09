@echo off
rem Study 2 objection conditions for another open model (replication of the Qwen3-4B runs).
rem Same protocol as run_code_pilot.bat and run_code_tool.bat; doubt is run here too, on the same 382 items.
rem   run_code_conditions.bat 8b      Qwen3-8B (batch 2)
rem   run_code_conditions.bat olmo    OLMo-2-7B-Instruct (batch 1)
rem   run_code_conditions.bat 8b 40   quick test with 40 items
rem Order: recheck, doubt, evidence, evidence + execution tool, track50, authority, track20, track80.
rem Logs go to logs\, results to runs\. Rerunning skips items that are already done.

if "%1"=="8b" (
  set MODEL=Qwen/Qwen3-8B
  set TAG=code_q8b
  set BS=2
) else if "%1"=="olmo" (
  set MODEL=allenai/OLMo-2-1124-7B-Instruct
  set TAG=code_olmo7b
  set BS=1
) else (
  echo usage: run_code_conditions.bat 8b ^| olmo [N]
  goto end
)
set N=382
set SUF=
if not "%2"=="" (
  set N=%2
  set SUF=_n%2
)
if not exist logs mkdir logs

for %%c in (recheck doubt evidence) do (
  echo %%c
  python code_challenge.py --model %MODEL% --challenge %%c --n %N% --bs %BS% --out runs\%TAG%_%%c%SUF% > logs\%TAG%_%%c%SUF%.txt 2>&1
)
echo evidence + tool
python code_challenge.py --model %MODEL% --challenge evidence --tool --n %N% --bs %BS% --out runs\%TAG%_evidence_tool%SUF% > logs\%TAG%_evidence_tool%SUF%.txt 2>&1
for %%c in (track50 authority track20 track80) do (
  echo %%c
  python code_challenge.py --model %MODEL% --challenge %%c --n %N% --bs %BS% --out runs\%TAG%_%%c%SUF% > logs\%TAG%_%%c%SUF%.txt 2>&1
)

set RUNS=
for %%c in (doubt recheck evidence evidence_tool track20 track50 track80 authority) do (
  if exist runs\%TAG%_%%c%SUF%\results.jsonl call set RUNS=%%RUNS%% runs\%TAG%_%%c%SUF%
)
python code_challenge_compare.py %RUNS% > logs\%TAG%_conditions%SUF%.txt
type logs\%TAG%_conditions%SUF%.txt
:end
