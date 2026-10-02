@echo off
rem Time to migration from git history (no survivorship bias). Needs git and python on the PATH.
rem Step 1 (once): in this window  set GITHUB_TOKEN=your_token   then this file builds the repository frame.
if not exist results mkdir results
if not exist results\repos.jsonl (
  if "%GITHUB_TOKEN%"=="" (
    echo GITHUB_TOKEN is not set. Type:  set GITHUB_TOKEN=your_token   and run this file again.
    exit /b 1
  )
  python -m pip install --quiet requests pandas
  python mine_by_history.py --find-repos --out results\repos.jsonl
)
python mine_by_history.py --repos results\repos.jsonl --out results\history.jsonl --default-set --max-repos 400
python analyze_history.py results\history.jsonl --md results\history_summary.md
