@echo off
rem Many-wording study for anthropic:claude-opus-5-5. Safe to run again: --resume continues an interrupted run.
if not defined ANTHROPIC_API_KEY echo ANTHROPIC_API_KEY is not set. Run:  set ANTHROPIC_API_KEY=your_key  & exit /b 1
if not exist wordings.json echo wordings.json not found in this folder & exit /b 1
python run_experiment.py --policy anthropic:claude-opus-5-5 --wordings wordings.json --variants all --episodes 30 --temps 0.7 --fails 0 --start-ts 9 6 0 --first-only --workers 4 --resume --out results\w16_opus.jsonl
python wording16.py results\w16_opus.jsonl --md results\w16_opus.md
