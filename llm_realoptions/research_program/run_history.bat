@echo off
rem Time to migration from git history (no survivorship bias). Needs git and python on the PATH.
rem usage:  run_history.bat [MAX_REPOS]      (default 500; a run can be extended later by calling it again with a larger number)
rem Step 1 (once): in this window  set GITHUB_TOKEN=your_token   then this file builds the repository frame (results\repos2.jsonl).
set MAXREPOS=%1
if "%MAXREPOS%"=="" set MAXREPOS=500
if not exist results mkdir results
if not exist results\repos2.jsonl (
  if "%GITHUB_TOKEN%"=="" (
    echo GITHUB_TOKEN is not set. Type:  set GITHUB_TOKEN=your_token   and run this file again.
    exit /b 1
  )
  python -m pip install --quiet requests pandas
  python mine_by_history.py --find-repos --out results\repos2.jsonl
)
python mine_by_history.py --repos results\repos2.jsonl --out results\history2.jsonl --default-set --max-repos %MAXREPOS%
python analyze_history.py results\history2.jsonl --md results\history2_summary.md
