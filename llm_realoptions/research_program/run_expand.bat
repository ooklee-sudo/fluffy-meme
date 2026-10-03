@echo off
rem Second frame aimed at provider-agnostic-layer users (litellm, langchain, llama-index, vercel ai, ...), larger repositories allowed (800 MB).
rem Needs: set GITHUB_TOKEN=your_token in this window (only for the repository search). Resumable: run again to continue after an interruption.
rem Steps: build frame -> mine history -> enrich -> merge with the first frame -> both analyses on the merged data.
if not exist results mkdir results
if not exist results\repos3.jsonl (
  if "%GITHUB_TOKEN%"=="" (
    echo GITHUB_TOKEN is not set. Type:  set GITHUB_TOKEN=your_token   and run this file again.
    exit /b 1
  )
  python mine_by_history.py --find-repos-layer --exclude results\repos2.jsonl --out results\repos3.jsonl
)
python mine_by_history.py --repos results\repos3.jsonl --out results\history3.jsonl --default-set --max-mb 800
python mine_by_history.py --enrich results\history3.jsonl --out results\history3_enriched.jsonl
python merge_history.py results\history_all.jsonl results\history_enriched.jsonl results\history3_enriched.jsonl
python analyze_history.py results\history_all.jsonl --md results\all_summary.md
python analyze_notice.py results\history_all.jsonl --md results\notice_all_summary.md
echo.
echo Done. Paste results\all_summary.md (sections H1 and Sensitivity) and results\notice_all_summary.md
