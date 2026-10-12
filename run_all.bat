@echo off
rem Runs every analysis with 999 bootstrap draws, in the right order, and collects all output in one file.
rem Put this file, analyze.py, spec_c.py, rq123.py, extra_analyses.py, section52.py, repo_relevance.csv, events.csv and data\ in one folder.
rem Usage: run_all.bat 2026-10-05        (the argument is the last week; default 2026-10-05)
rem Takes one to a few hours. Keep the computer awake and do not close this window.
setlocal
set END=%1
if "%END%"=="" set END=2026-10-05
set B=999
if not exist results mkdir results
set ALL=results\all_output.txt
echo ==== started %DATE% %TIME% (end week %END%, boot %B%) ==== > %ALL%

echo [1/4] spec_c.py ...
echo. >> %ALL% & echo ===== spec_c.py ===== >> %ALL%
python spec_c.py --end-week %END% --boot %B% >> %ALL% 2>&1

echo [2/4] rq123.py ...
echo. >> %ALL% & echo ===== rq123.py ===== >> %ALL%
python rq123.py --end-week %END% --boot %B% >> %ALL% 2>&1

echo [3/4] extra_analyses.py ...
echo. >> %ALL% & echo ===== extra_analyses.py ===== >> %ALL%
python extra_analyses.py --end-week %END% --boot %B% >> %ALL% 2>&1

echo [4/4] section52.py ...
echo. >> %ALL% & echo ===== section52.py ===== >> %ALL%
python section52.py --end-week %END% --boot %B% >> %ALL% 2>&1

echo. >> %ALL% & echo ==== finished %DATE% %TIME% ==== >> %ALL%
echo.
echo Done. Open results\all_output.txt, copy everything and paste it into the conversation.
endlocal
