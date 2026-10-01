@echo off
rem Dominance-visible variant: Haiku 4.5, 5 frames x 16 wordings x 30 episodes = 2,400 calls (about $2), 3 turns left, expected quality change stated in every option.
if not defined ANTHROPIC_API_KEY echo ANTHROPIC_API_KEY is not set. Run:  set ANTHROPIC_API_KEY=your_key  & exit /b 1
if not exist wordings.json echo wordings.json not found in this folder & exit /b 1
python run_experiment.py --policy anthropic:claude-haiku-4-5-20251001 --wordings wordings.json --extra-frames --variants all --episodes 30 --temps 0.7 --fails 0 --start-ts 9 --first-only --workers 4 --resume --reveal-ev --out results\reveal_haiku.jsonl
python compare_reveal.py results\g2x2_haiku.jsonl results\reveal_haiku.jsonl --md results\reveal_haiku.md
