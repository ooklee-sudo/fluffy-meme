@echo off
rem Staged expansion of the study (more models, more seeds, demographic personas).
rem Usage (from the llm-count-study folder, with OPENROUTER_API_KEY set):  run_expansion.bat 1
rem Every stage is resumable: finished configurations are skipped when you run it again.
rem   stage 1: demographic personas, the 3 original models, seed 0                 (~8,400 calls)
rem   stage 2: 5 additional models, seed 0, all four experiments                   (~78,000 calls)
rem   stage 3: the 3 original models, seeds 1 and 2, all four experiments          (~94,000 calls)
rem   stage 4: 5 additional models, seeds 1 and 2, all four experiments            (~156,000 calls)
rem   stage 5: prompt-wording robustness (third-person and survey wordings), 4 models, seed 0, retail + grocery + email (~150,000 calls)
rem Check cost first:  python estimate_cost.py --models <list> --seeds <k>
set OLD=openai/gpt-4o-mini,meta-llama/llama-3.3-70b-instruct,anthropic/claude-haiku-5.5
set NEW=anthropic/claude-sonnet-5,openai/gpt-5.6-terra,deepseek/deepseek-v4-pro-0813,google/gemini-3.1-flash-lite,mistralai/mistral-large-4-0
set W=16
if "%1"=="1" goto s1
if "%1"=="2" goto s2
if "%1"=="3" goto s3
if "%1"=="4" goto s4
if "%1"=="5" goto s5
echo usage: run_expansion.bat 1 ^| 2 ^| 3 ^| 4 ^| 5
goto end

:s1
python run_all.py --n 200 --workers %W% --scenario grocery --personas demographic --temps 0.7 --models %OLD% --runs runs_grocery_demo
python analyze_ci.py --runs runs_grocery_demo
goto end

:s2
python run_all.py --n 200 --workers %W% --scenario retail --temps 0.7 --models %NEW% --runs runs
python run_all.py --n 200 --workers %W% --scenario grocery --temps 0.7 --models %NEW% --runs runs_grocery
python run_all.py --n 200 --workers %W% --scenario grocery --personas demographic --temps 0.7 --models %NEW% --runs runs_grocery_demo
python run_hillstrom.py --n 300 --workers %W% --models %NEW% --runs runs_hillstrom
goto end

:s3
python run_all.py --n 200 --workers %W% --scenario retail --temps 0.7 --seeds 1,2 --models %OLD% --runs runs
python run_all.py --n 200 --workers %W% --scenario grocery --temps 0.7 --seeds 1,2 --models %OLD% --runs runs_grocery
python run_all.py --n 200 --workers %W% --scenario grocery --personas demographic --temps 0.7 --seeds 1,2 --models %OLD% --runs runs_grocery_demo
python run_hillstrom.py --n 300 --workers %W% --seeds 1,2 --models %OLD% --runs runs_hillstrom
goto end

:s4
python run_all.py --n 200 --workers %W% --scenario retail --temps 0.7 --seeds 1,2 --models %NEW% --runs runs
python run_all.py --n 200 --workers %W% --scenario grocery --temps 0.7 --seeds 1,2 --models %NEW% --runs runs_grocery
python run_all.py --n 200 --workers %W% --scenario grocery --personas demographic --temps 0.7 --seeds 1,2 --models %NEW% --runs runs_grocery_demo
python run_hillstrom.py --n 300 --workers %W% --seeds 1,2 --models %NEW% --runs runs_hillstrom
goto end

:s5
set WM=openai/gpt-4o-mini,meta-llama/llama-3.3-70b-instruct,anthropic/claude-haiku-5.5,anthropic/claude-sonnet-5
for %%V in (third survey) do (
  python run_all.py --n 200 --workers %W% --scenario retail --temps 0.7 --wording %%V --models %WM% --runs runs_w_%%V
  python run_all.py --n 200 --workers %W% --scenario grocery --temps 0.7 --wording %%V --models %WM% --runs runs_grocery_w_%%V
  python run_hillstrom.py --n 300 --workers %W% --wording %%V --models %WM% --runs runs_hillstrom_w_%%V
)
goto end

:end
echo.
echo to summarize: python analyze_ci.py --runs runs_w_third  (and runs_w_survey, runs_grocery_w_third, runs_grocery_w_survey) ; python hillstrom_rd.py --runs runs_hillstrom_w_third --data hillstrom.csv
echo main runs: python analyze_ci.py --runs runs  /  runs_grocery  /  runs_grocery_demo   and   python hillstrom_rd.py --runs runs_hillstrom --data hillstrom.csv
