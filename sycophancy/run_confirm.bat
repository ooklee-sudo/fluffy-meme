@echo off
rem Confirmatory study (paper_isr/CONFIRMATORY_PLAN.md) on an open model, new items code_new@v1.
rem Start only after paper_isr/predictions_open.md is committed.
rem   run_confirm.bat 4b       Qwen3-4B (batch 4)
rem   run_confirm.bat 8b       Qwen3-8B (batch 2)
rem   run_confirm.bat olmo     OLMo-2 7B Instruct (batch 1, new model)
rem   run_confirm.bat 4b 20    quick test with 20 items (not part of the study)
rem 17 runs: recheck, doubt, track20/50/80, authority, evidence, evidence + tool,
rem and K = 4, 1, 1/4 with recheck, track50, authority. Hidden states are not saved.
rem Results go to runs\confirm_<tag>_<condition>. Rerunning skips items already done.
rem Analysis: the doubt run is named _doubt, so run fit_reviewer.py and policy_sim.py WITHOUT --prefix-style open.

if "%1"=="4b" (
  set MODEL=Qwen/Qwen3-4B
  set TAG=confirm_q4b
  set BS=4
) else if "%1"=="8b" (
  set MODEL=Qwen/Qwen3-8B
  set TAG=confirm_q8b
  set BS=2
) else if "%1"=="olmo" (
  set MODEL=allenai/OLMo-2-1124-7B-Instruct
  set TAG=confirm_olmo7b
  set BS=1
) else (
  echo usage: run_confirm.bat 4b ^| 8b ^| olmo [N]
  goto end
)
set N=382
set SUF=
if not "%2"=="" (
  set N=%2
  set SUF=_n%2
)
set DATA=code_new@v1
if not exist logs mkdir logs

for %%c in (recheck doubt track50 authority evidence track20 track80) do (
  echo %%c
  python code_challenge.py --model %MODEL% --dataset %DATA% --challenge %%c --no-hidden --n %N% --bs %BS% --out runs\%TAG%%SUF%_%%c > logs\%TAG%%SUF%_%%c.txt 2>&1
)
echo evidence + tool
python code_challenge.py --model %MODEL% --dataset %DATA% --challenge evidence --tool --no-hidden --n %N% --bs %BS% --out runs\%TAG%%SUF%_evidence_tool > logs\%TAG%%SUF%_evidence_tool.txt 2>&1
for %%k in (4 1 0.25) do (
  for %%c in (recheck track50 authority) do (
    echo cost %%k %%c
    python code_challenge.py --model %MODEL% --dataset %DATA% --challenge %%c --cost %%k --no-hidden --n %N% --bs %BS% --out runs\%TAG%%SUF%_cost%%k_%%c > logs\%TAG%%SUF%_cost%%k_%%c.txt 2>&1
  )
)
echo done
:end
