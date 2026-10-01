@echo off
rem Valence x goal-salience study for anthropic:claude-sonnet-5-5: 5 frames x 16 wordings x 30 episodes, 3 turns left, with and without the target in the facts line.
if not defined ANTHROPIC_API_KEY echo ANTHROPIC_API_KEY is not set. Run:  set ANTHROPIC_API_KEY=your_key  & exit /b 1
if not exist wordings.json echo wordings.json not found in this folder & exit /b 1
python run_experiment.py --policy anthropic:claude-sonnet-5-5 --wordings wordings.json --extra-frames --variants all --episodes 30 --temps 0.7 --fails 0 --start-ts 9 --first-only --workers 4 --resume --out results\g2x2_sonnet.jsonl
python run_experiment.py --policy anthropic:claude-sonnet-5-5 --wordings wordings.json --extra-frames --variants all --episodes 30 --temps 0.7 --fails 0 --start-ts 9 --first-only --workers 4 --resume --hide-target --out results\g2x2_hide_sonnet.jsonl
python goal2x2.py results\g2x2_sonnet.jsonl results\g2x2_hide_sonnet.jsonl --md results\g2x2_sonnet.md
