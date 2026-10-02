@echo off
rem Second pass on the finished history run: adds flexibility level, activity and relaxed-migration variables, then the full analysis.
rem Needs results\history2.jsonl from run_history.bat. Re-clones only the ~154 repositories that are in it. No token needed (public clones).
python mine_by_history.py --enrich results\history2.jsonl --out results\history_enriched.jsonl
python analyze_history.py results\history_enriched.jsonl --md results\history3_summary.md
echo.
echo Done. Paste results\history3_summary.md (sections "Sensitivity analyses").
