@echo off
rem Fable 5.1, remaining conditions: 6 and 12 turns left, appended to the 3-turns-left log so that one file holds all three conditions.
rem 2 conditions x 3 frames x 16 wordings x 30 episodes = 2,880 calls, about $70 (range $45-150). Safe to rerun: --resume skips finished episodes.
if not defined ANTHROPIC_API_KEY echo ANTHROPIC_API_KEY is not set. Run:  set ANTHROPIC_API_KEY=your_key  & exit /b 1
if not exist wordings.json echo wordings.json not found in this folder & exit /b 1
if not exist results\w16_fable_t3.jsonl echo results\w16_fable_t3.jsonl not found: the 3-turns-left run must be in this folder first & exit /b 1
python run_experiment.py --policy anthropic:claude-fable-5-1 --wordings wordings.json --variants all --episodes 30 --temps 0.7 --fails 0 --start-ts 6 0 --first-only --workers 4 --resume --out results\w16_fable_t3.jsonl
python wording16.py results\w16_fable_t3.jsonl --md results\w16_fable_all.md
