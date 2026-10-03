@echo off
rem Study 1b, Addenda 1 and 2 (see STUDY1B_PREREG.md). Run AFTER run_hard.bat. Needs OPENROUTER_API_KEY and ANTHROPIC_API_KEY set in this window (never paste them into chat), then cls.
rem Safe to rerun: it resumes. Wording robustness for the 14 main models (system prompt variants 1 and 2, stance set B), then 9 further models on the registered wording.
set PYTHONUTF8=1
set STUDY1_BANK=hard
python audit_hard.py || goto :eof
python check_models.py models_hard_ext.json || goto :eof
set MAIN=claude-haiku claude-sonnet claude-opus claude-fable qwen2.5-7b qwen2.5-72b llama3.1-8b llama3.1-70b gemma3-4b gemma3-12b gemma3-27b ministral-3b ministral-8b ministral-14b
python run.py --models models_hard.json --only %MAIN% --system-variant 1 --out results\study1b.jsonl --workers 4 --resume || goto :eof
python run.py --models models_hard.json --only %MAIN% --system-variant 2 --out results\study1b.jsonl --workers 4 --resume || goto :eof
python run.py --models models_hard.json --only %MAIN% --social-set B --out results\study1b.jsonl --workers 4 --resume || goto :eof
python run.py --models models_hard_ext.json --all --out results\study1b.jsonl --workers 4 --resume || goto :eof
python analyze.py results\study1b.jsonl --primary Qwen2.5 Llama3.1 Gemma3 Ministral --md results\analysis_1b_open_robust.md
python analyze.py results\study1b.jsonl --primary Qwen2.5 Llama3.1 Gemma3 Ministral Cohere-Command OpenAI-4.1 Amazon-Nova --md results\analysis_1b_eight_families.md
echo.
echo Done. Paste results\analysis_1b_open_robust.md and results\analysis_1b_eight_families.md
