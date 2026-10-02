@echo off
rem Screening run for ONE small model (3 turns left, 3 frames x 16 wordings x 30 episodes = 1,440 first choices; see SMALL_MODELS_PLAN.md).
rem usage:  run_small.bat PROVIDER MODEL TAG [full]
rem   PROVIDER = openai | gemini | openrouter        MODEL = exact model id from list_models.py        TAG = short name for the output files
rem   add "full" as the 4th argument for models that passed the screen: adds 6 and 12 turns left to the same file
rem keys (set in this window, never in chat):  OPENAI_API_KEY | GEMINI_API_KEY | OPENROUTER_API_KEY
if "%~3"=="" echo usage: run_small.bat PROVIDER MODEL TAG [full] & exit /b 1
if not exist wordings.json echo wordings.json not found in this folder & exit /b 1
if /i "%~1"=="openai" (
  if not defined OPENAI_API_KEY echo OPENAI_API_KEY is not set & exit /b 1
  set OPENAI_BASE_URL=https://api.openai.com/v1
) else if /i "%~1"=="gemini" (
  if not defined GEMINI_API_KEY echo GEMINI_API_KEY is not set & exit /b 1
  set OPENAI_API_KEY=%GEMINI_API_KEY%
  set OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
) else if /i "%~1"=="openrouter" (
  if not defined OPENROUTER_API_KEY echo OPENROUTER_API_KEY is not set & exit /b 1
  set OPENAI_API_KEY=%OPENROUTER_API_KEY%
  set OPENAI_BASE_URL=https://openrouter.ai/api/v1
) else (
  echo PROVIDER must be openai, gemini or openrouter & exit /b 1
)
python -m pip install --quiet openai
set TS=9
if /i "%~4"=="full" set TS=9 6 0
python run_experiment.py --policy openai:%~2 --wordings wordings.json --variants all --episodes 30 --temps 0.7 --fails 0 --start-ts %TS% --first-only --workers 4 --resume --out results\w16_%~3.jsonl
python wording16.py results\w16_%~3.jsonl --md results\w16_%~3.md
python check_log.py results\w16_%~3.jsonl
