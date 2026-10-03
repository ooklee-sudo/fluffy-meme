@echo off
rem Notice length and flexibility, identified within repositories (Cox stratified by repository, clustered errors). Needs results\history_enriched.jsonl from run_enrich.bat.
python analyze_notice.py results\history_enriched.jsonl --md results\notice_summary.md
echo.
echo Done. Paste results\notice_summary.md
