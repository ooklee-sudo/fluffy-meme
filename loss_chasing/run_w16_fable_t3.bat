@echo off
rem Fable 5.1, 3 turns left only (the condition where Haiku skips): 3 frames x 16 wordings x 30 episodes = 1,440 calls, about $16 (range $10-$40; Fable reasons by default and rejects temperature).
if not defined ANTHROPIC_API_KEY echo ANTHROPIC_API_KEY is not set. Run:  set ANTHROPIC_API_KEY=your_key  & exit /b 1
if not exist wordings.json echo wordings.json not found in this folder & exit /b 1
python run_experiment.py --policy anthropic:claude-fable-5-1 --wordings wordings.json --variants all --episodes 30 --temps 0.7 --fails 0 --start-ts 9 --first-only --workers 4 --resume --out results\w16_fable_t3.jsonl
python wording16.py results\w16_fable_t3.jsonl --md results\w16_fable_t3.md
