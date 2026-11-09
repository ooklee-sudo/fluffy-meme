@echo off
rem H4: does cheaper verification reduce caving to false evidence?
rem Same as the evidence condition of run_code_pilot.bat, but the model may run the code under review
rem (up to 3 calls of the function with literal arguments; nothing else the model writes is executed).
rem Run this after run_code_pilot.bat has finished (do not edit or pull while a batch file is running).
rem   run_code_tool.bat        382 items
rem   run_code_tool.bat 20     quick test with 20 items

set N=382
set SUF=
if not "%1"=="" (
  set N=%1
  set SUF=_n%1
)
if not exist logs mkdir logs
python code_challenge.py --model Qwen/Qwen3-4B --challenge evidence --tool --n %N% --out runs\code_q4b_evidence_tool%SUF% > logs\code_q4b_evidence_tool%SUF%.txt 2>&1
python code_challenge_compare.py runs\code_q4b_1024 runs\code_q4b_recheck runs\code_q4b_evidence runs\code_q4b_evidence_tool%SUF% > logs\code_q4b_tool_compare%SUF%.txt
type logs\code_q4b_tool_compare%SUF%.txt
