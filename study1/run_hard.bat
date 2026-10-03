@echo off
rem Study 1b main run. Run ONLY after the pilot gate printed "GATE PASSED" and the bank files were committed (see STUDY1B_PREREG.md, section 8).
rem Needs ANTHROPIC_API_KEY and OPENROUTER_API_KEY set in this window first (never paste them into chat), then cls. Safe to rerun: it resumes.
set PYTHONUTF8=1
set STUDY1_BANK=hard
if not exist items_hard.jsonl ( echo items_hard.jsonl is missing: get the frozen bank files first & goto :eof )
python audit_hard.py || goto :eof
if not exist results mkdir results
python run.py --models models_hard.json --only claude-haiku claude-sonnet claude-opus claude-fable qwen2.5-7b qwen2.5-72b llama3.1-8b llama3.1-70b gemma3-4b gemma3-12b gemma3-27b ministral-3b ministral-8b ministral-14b --out results\study1b.jsonl --workers 4 --resume || goto :eof
python analyze.py results\study1b.jsonl --primary Qwen2.5 Llama3.1 Gemma3 Ministral --md results\analysis_1b_open.md
python analyze.py results\study1b.jsonl --primary Claude --md results\analysis_1b_claude.md
echo.
echo Done. Paste results\analysis_1b_open.md and results\analysis_1b_claude.md
