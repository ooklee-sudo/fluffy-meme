@echo off
rem Study 1b, Addendum 3 (see STUDY1B_PREREG.md): aligned-stance channel for the 14 main models, then the value-of-review analysis.
rem Run AFTER run_hard.bat (it adds to results\study1b.jsonl). Needs OPENROUTER_API_KEY and ANTHROPIC_API_KEY set in this window (never paste them into chat), then cls. Safe to rerun: it resumes.
set PYTHONUTF8=1
set STUDY1_BANK=hard
python audit_hard.py || goto :eof
python run.py --models models_hard.json --only claude-haiku claude-sonnet claude-opus claude-fable qwen2.5-7b qwen2.5-72b llama3.1-8b llama3.1-70b gemma3-4b gemma3-12b gemma3-27b ministral-3b ministral-8b ministral-14b --channels aligned --out results\study1b.jsonl --workers 4 --resume || goto :eof
python analyze_aligned.py results\study1b.jsonl --md results\analysis_1b_aligned.md
python analyze_aligned.py results\study1b.jsonl --drop-failed --md results\analysis_1b_aligned_dropfailed.md
python analyze_aligned.py results\study1b.jsonl --exclude-domain 6 --md results\analysis_1b_aligned_no_d6.md
echo.
echo Done. Paste results\analysis_1b_aligned.md, results\analysis_1b_aligned_dropfailed.md, results\analysis_1b_aligned_no_d6.md
