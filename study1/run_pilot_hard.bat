@echo off
rem Study 1b pilot (96 queries per model, 4 models) and the pre-registered gate. Needs two keys set in THIS window first (never paste them into chat):
rem   set ANTHROPIC_API_KEY=...    set OPENROUTER_API_KEY=...      then  cls
rem Safe to rerun: it resumes. Pilot data are never used in the main analysis.
set PYTHONUTF8=1
python check_models.py models_hard.json || goto :eof
python items_hard.py --pilot || goto :eof
set STUDY1_BANK=pilot
if not exist results mkdir results
python run.py --models models_hard.json --only claude-haiku qwen2.5-7b llama3.1-8b llama3.1-70b --out results\pilot_hard.jsonl --workers 4 --resume || goto :eof
python audit_hard.py --pilot-gate results\pilot_hard.jsonl
