@echo off
rem Screens the candidate small models fixed in SMALL_MODELS_PLAN.md, all through OpenRouter with ONE key.
rem Before running, in this window:  set OPENROUTER_API_KEY=your_key      (never paste the key into a chat)
if not defined OPENROUTER_API_KEY echo OPENROUTER_API_KEY is not set & exit /b 1
call run_small.bat openrouter openai/gpt-5-nano gpt5nano
call run_small.bat openrouter google/gemini-2.5-flash-lite gem25fl
call run_small.bat openrouter google/gemini-3.1-flash-lite gem31fl
call run_small.bat openrouter mistralai/ministral-8b-2512 ministral8b
call run_small.bat openrouter meta-llama/llama-3.1-8b-instruct llama31_8b
call run_small.bat openrouter google/gemma-3-12b-it gemma3_12b
call run_small.bat openrouter qwen/qwen3-14b qwen3_14b
python screen_report.py results\w16_gpt5nano.jsonl results\w16_gem25fl.jsonl results\w16_gem31fl.jsonl results\w16_ministral8b.jsonl results\w16_llama31_8b.jsonl results\w16_gemma3_12b.jsonl results\w16_qwen3_14b.jsonl
