@echo off
rem Study 1, Claude ladder (Haiku, Sonnet, Opus, Fable). Needs ANTHROPIC_API_KEY set in this window first. Safe to rerun: it resumes.
set PYTHONUTF8=1
python audit.py || goto :eof
if not exist results mkdir results
python run.py --models models.json --only claude-haiku claude-sonnet claude-opus claude-fable --out results\study1_claude.jsonl --workers 4 --resume || goto :eof
python analyze.py results\study1_claude.jsonl --primary Claude --md results\analysis_claude.md
