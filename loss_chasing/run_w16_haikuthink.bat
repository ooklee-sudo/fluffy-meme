@echo off
rem Control: Haiku 4.5 WITH extended thinking (budget 2000), 3 turns left, 16 wordings x 3 frames x 30 episodes = 1440 calls.
if not defined ANTHROPIC_API_KEY echo ANTHROPIC_API_KEY is not set. Run:  set ANTHROPIC_API_KEY=your_key  & exit /b 1
if not exist wordings.json echo wordings.json not found in this folder & exit /b 1
python run_experiment.py --policy anthropic:claude-haiku-4-5-20251001+think2000 --wordings wordings.json --variants all --episodes 30 --temps 0.7 --fails 0 --start-ts 9 --first-only --workers 4 --resume --out results\w16_haikuthink.jsonl
python wording16.py results\w16_haikuthink.jsonl --md results\w16_haikuthink.md
