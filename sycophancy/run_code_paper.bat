@echo off
rem Same study as the paper ("Room to Reconsider"), on code review instead of MMLU/ARC.
rem Data: data\code_humaneval.jsonl + data\code_mbpp.jsonl (764 items: half correct code, half one-bug mutants).
rem
rem   run_code_paper.bat check   turn-1 verdict bias of each question wording (python code_prompt_check.py)
rem   run_code_paper.bat test    quick check: Qwen3-4B, 40 items, 96 tokens (a few minutes)
rem   run_code_paper.bat 4b      Qwen3-4B: 1024 and 96 tokens, firm prompt, tables, probes, shared signal
rem   run_code_paper.bat steer   Qwen3-4B steering screen (prefill) with gates, layers 18/24/28
rem   run_code_paper.bat 8b      Qwen3-8B: 1024 and 96 tokens + analysis
rem   run_code_paper.bat olmo    OLMo-2-7B: 1024 and 256 tokens + analysis
rem   run_code_paper.bat table   table and figures for every run that exists
rem Runs resume where they stopped. Logs: logs\, runs: runs\, tables and figures: results\.

rem DATA may name a question wording, e.g. code_all@v3 (see syco.CODE_PROMPTS and the check step)
set DATA=code_all
set N=764
if not exist logs mkdir logs
if not exist results mkdir results
if "%1"=="" goto usage
goto %1

:check
python code_prompt_check.py --model Qwen/Qwen3-4B > logs\code_prompt_check.txt 2>&1
type logs\code_prompt_check.txt
goto end

:test
python run_challenge.py --model Qwen/Qwen3-4B --dataset %DATA% --n 40 --max-new-tokens 96 --bs 8 --out runs\code_test > logs\code_test.txt 2>&1
python paper_table.py runs\code_test
goto end

:4b
python run_challenge.py --model Qwen/Qwen3-4B --dataset %DATA% --n %N% --max-new-tokens 1024 --bs 4 --out runs\code_q4b_1024 > logs\code_q4b_1024.txt 2>&1
python run_challenge.py --model Qwen/Qwen3-4B --dataset %DATA% --n %N% --max-new-tokens 96 --bs 8 --out runs\code_q4b_96 > logs\code_q4b_96.txt 2>&1
python run_challenge.py --model Qwen/Qwen3-4B --dataset %DATA% --n %N% --max-new-tokens 96 --bs 8 --system firm --no-hidden --out runs\code_q4b_96_firm > logs\code_q4b_96_firm.txt 2>&1
python run_challenge.py --model Qwen/Qwen3-4B --dataset %DATA% --n %N% --turn2 prefill --bs 8 --no-hidden --out runs\code_q4b_prefill > logs\code_q4b_prefill.txt 2>&1
python analyze.py runs\code_q4b_1024 > logs\analyze_code_q4b_1024.txt 2>&1
python analyze.py runs\code_q4b_96 > logs\analyze_code_q4b_96.txt 2>&1
python geometry.py runs\code_q4b_96 --layer-step 4 > logs\tr_code_q4b_96.txt 2>&1
python geometry.py runs\code_q4b_1024 --layer-step 4 > logs\tr_code_q4b_1024.txt 2>&1
goto table

:steer
python steer.py runs\code_q4b_96 --model Qwen/Qwen3-4B --turn2 prefill --layers 18,24,28 --alphas=-4,2,4,8 --n-test 382 --bs 8 --gate --firm-run runs\code_q4b_96_firm --out results\code_steer_q4b > logs\code_steer_q4b.txt 2>&1
goto end

:8b
python run_challenge.py --model Qwen/Qwen3-8B --dataset %DATA% --n %N% --max-new-tokens 1024 --bs 2 --out runs\code_q8b_1024 > logs\code_q8b_1024.txt 2>&1
python run_challenge.py --model Qwen/Qwen3-8B --dataset %DATA% --n %N% --max-new-tokens 96 --bs 4 --out runs\code_q8b_96 > logs\code_q8b_96.txt 2>&1
python analyze.py runs\code_q8b_1024 > logs\analyze_code_q8b_1024.txt 2>&1
python analyze.py runs\code_q8b_96 > logs\analyze_code_q8b_96.txt 2>&1
python geometry.py runs\code_q8b_96 --layer-step 4 > logs\tr_code_q8b_96.txt 2>&1
python geometry.py runs\code_q8b_1024 --layer-step 4 > logs\tr_code_q8b_1024.txt 2>&1
goto table

:olmo
python run_challenge.py --model allenai/OLMo-2-1124-7B-Instruct --dataset %DATA% --n %N% --max-new-tokens 1024 --bs 1 --out runs\code_olmo7b_1024 > logs\code_olmo7b_1024.txt 2>&1
python run_challenge.py --model allenai/OLMo-2-1124-7B-Instruct --dataset %DATA% --n %N% --max-new-tokens 256 --bs 2 --out runs\code_olmo7b_256 > logs\code_olmo7b_256.txt 2>&1
python analyze.py runs\code_olmo7b_1024 > logs\analyze_code_olmo7b_1024.txt 2>&1
python analyze.py runs\code_olmo7b_256 > logs\analyze_code_olmo7b_256.txt 2>&1
python geometry.py runs\code_olmo7b_256 --layer-step 4 > logs\tr_code_olmo7b_256.txt 2>&1
python geometry.py runs\code_olmo7b_1024 --layer-step 4 > logs\tr_code_olmo7b_1024.txt 2>&1
goto table

:table
set RUNS=
for %%r in (code_q4b_96 code_q4b_1024 code_q4b_96_firm code_q4b_prefill code_q8b_96 code_q8b_1024 code_olmo7b_256 code_olmo7b_1024) do (
  if exist runs\%%r\results.jsonl call set RUNS=%%RUNS%% runs\%%r
)
python paper_table.py %RUNS% --csv results\code_table.csv --plot results\code_breakeven.png > logs\code_table.txt 2>&1
type logs\code_table.txt
goto end

:usage
echo usage: run_code_paper.bat check ^| test ^| 4b ^| steer ^| 8b ^| olmo ^| table
:end
