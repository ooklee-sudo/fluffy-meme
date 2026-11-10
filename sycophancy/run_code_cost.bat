@echo off
rem Cost-framing test on an open model (the decisive test of the ambiguity-averse reviewer model).
rem One sentence on the cost of the two errors is appended to the system prompt; turn 1 is re-read under it.
rem   run_code_cost.bat 4b       Qwen3-4B (batch 4)
rem   run_code_cost.bat 8b       Qwen3-8B (batch 2)
rem   run_code_cost.bat 4b 40    quick test with 40 items
rem Stated cost ratio K = 4, 1, 1/4 (approving a bug costs K times as much as rejecting correct code),
rem each with re-check, track record 50% and senior engineer: 9 runs. Hidden states are not saved.
rem Logs go to logs\, results to runs\<tag>_cost<K>_<condition>. Rerunning skips items already done.
rem Afterwards: python fit_reviewer.py --prefix-style open runs\code_q4b   (4b; 8b without --prefix-style)

if "%1"=="4b" (
  set MODEL=Qwen/Qwen3-4B
  set TAG=code_q4b
  set BS=4
) else if "%1"=="8b" (
  set MODEL=Qwen/Qwen3-8B
  set TAG=code_q8b
  set BS=2
) else (
  echo usage: run_code_cost.bat 4b ^| 8b [N]
  goto end
)
set N=382
set SUF=
if not "%2"=="" (
  set N=%2
  set SUF=_n%2
)
if not exist logs mkdir logs

for %%k in (4 1 0.25) do (
  for %%c in (recheck track50 authority) do (
    echo cost %%k %%c
    python code_challenge.py --model %MODEL% --challenge %%c --cost %%k --no-hidden --n %N% --bs %BS% --out runs\%TAG%%SUF%_cost%%k_%%c > logs\%TAG%%SUF%_cost%%k_%%c.txt 2>&1
  )
)

python cost_framing_compare.py --tags %TAG%%SUF% --conditions track50 authority > logs\%TAG%%SUF%_cost.txt
type logs\%TAG%%SUF%_cost.txt
:end
