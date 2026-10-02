@echo off
rem Study 4 design (valence x goal visibility, 5 frames x 16 wordings x 30 episodes, 3 turns left) for ONE small model that passed the screen.
rem Runs the design with the target in the facts line and with the target hidden (4,800 first choices in all).
rem usage:  run_small_g2x2.bat PROVIDER MODEL TAG      e.g.  run_small_g2x2.bat openrouter google/gemini-2.5-flash-lite gem25fl
if "%~3"=="" echo usage: run_small_g2x2.bat PROVIDER MODEL TAG & exit /b 1
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
python run_experiment.py --policy openai:%~2 --wordings wordings.json --extra-frames --variants all --episodes 30 --temps 0.7 --fails 0 --start-ts 9 --first-only --workers 4 --resume --out results\g2x2_%~3.jsonl
python run_experiment.py --policy openai:%~2 --wordings wordings.json --extra-frames --variants all --episodes 30 --temps 0.7 --fails 0 --start-ts 9 --first-only --workers 4 --resume --hide-target --out results\g2x2_hide_%~3.jsonl
python goal2x2.py results\g2x2_%~3.jsonl results\g2x2_hide_%~3.jsonl --md results\g2x2_%~3.md
python check_log.py results\g2x2_%~3.jsonl
python check_log.py results\g2x2_hide_%~3.jsonl
