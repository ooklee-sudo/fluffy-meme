@echo off
rem Screening run for one small model: 3 turns left, 3 frames x 16 wordings x 30 episodes = 1,440 first choices.
rem usage:  run_small_screen.bat openai:MODEL_NAME TAG        e.g.  run_small_screen.bat openai:gpt-4.1-nano gpt41nano
rem OpenAI:   set OPENAI_API_KEY=your_key
rem Gemini:   set OPENAI_API_KEY=your_gemini_key   and   set OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
rem Others (OpenRouter, Together, ...):  set OPENAI_API_KEY=their_key   and   set OPENAI_BASE_URL=their OpenAI-compatible URL
if "%~2"=="" echo usage: run_small_screen.bat openai:MODEL_NAME TAG & exit /b 1
if not defined OPENAI_API_KEY echo OPENAI_API_KEY is not set. Run:  set OPENAI_API_KEY=your_key  & exit /b 1
if not exist wordings.json echo wordings.json not found in this folder & exit /b 1
python -m pip install --quiet openai
python run_experiment.py --policy %1 --wordings wordings.json --variants all --episodes 30 --temps 0.7 --fails 0 --start-ts 9 --first-only --workers 4 --resume --out results\w16_%2_t3.jsonl
python wording16.py results\w16_%2_t3.jsonl --md results\w16_%2_t3.md
python check_log.py results\w16_%2_t3.jsonl
