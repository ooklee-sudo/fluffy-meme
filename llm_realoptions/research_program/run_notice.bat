@echo off
rem Notice length, flexibility and the timing of migration around the shutdown. Needs results\history_enriched.jsonl from run_enrich.bat.
python analyze_notice.py results\history_enriched.jsonl --md results\notice_summary.md
echo.
echo Done. Paste results\notice_summary.md
