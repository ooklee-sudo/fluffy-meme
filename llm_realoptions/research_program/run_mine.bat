@echo off
rem Mines public GitHub repositories for how long they take to remove retired OpenAI model identifiers.
rem Before running, in this same window:  set GITHUB_TOKEN=your_token   (a classic or fine-grained token with public-read access)
if "%GITHUB_TOKEN%"=="" (
  echo GITHUB_TOKEN is not set. Type:  set GITHUB_TOKEN=your_token   and run this file again.
  exit /b 1
)
python -m pip install --quiet requests pandas
if not exist results mkdir results
python mine_migrations.py --default-set --max-hits 30 --out results\migrations.jsonl
echo.
python -c "import pandas as pd; d=pd.read_json('results/migrations.jsonl', lines=True); print(len(d),'files'); print(d.groupby('model').agg(files=('repo','size'), censored=('censored','mean'), median_lag=('lag_days','median')).round(2))"
