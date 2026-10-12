@echo off
rem Run from this folder. Set the token first in the same window:  set GITHUB_TOKEN=ghp_xxxxx
chcp 65001 >nul
if "%GITHUB_TOKEN%"=="" (
  echo GITHUB_TOKEN is not set. Run:  set GITHUB_TOKEN=ghp_xxxxx
  exit /b 1
)
python -m pip install requests pandas numpy scipy
python collect.py
if errorlevel 1 exit /b 1
python analyze.py --end-week 2026-10-05
echo.
echo Done. Upload the results folder (or results\results.md).
pause
