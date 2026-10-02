@echo off
rem Full run for a small model that passed the screen (see SMALL_MODELS_PLAN.md): adds 6 and 12 turns left to the screening file.
rem usage:  run_small_full.bat openai:MODEL_NAME TAG   (same TAG as in the screen; same environment variables)
if "%~2"=="" echo usage: run_small_full.bat openai:MODEL_NAME TAG & exit /b 1
if not defined OPENAI_API_KEY echo OPENAI_API_KEY is not set. Run:  set OPENAI_API_KEY=your_key  & exit /b 1
python run_experiment.py --policy %1 --wordings wordings.json --variants all --episodes 30 --temps 0.7 --fails 0 --start-ts 6 0 --first-only --workers 4 --resume --out results\w16_%2_t3.jsonl
python wording16.py results\w16_%2_t3.jsonl --md results\w16_%2_all.md
python check_log.py results\w16_%2_t3.jsonl
