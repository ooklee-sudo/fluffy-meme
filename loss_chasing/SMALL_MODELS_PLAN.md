# Small-model replication: plan fixed before any run

Purpose. In the Loss Chasing manuscript the evidence for what is associated with skipping comes from one model that skips (Claude Haiku 4.5). This plan adds small fast models from other vendors, run with the same environment, the same 16 wordings, the same prompts and the same analysis scripts (`wording16.py`, `goal2x2.py`).

## Candidate models (check availability and exact names on the vendor's model list before running)
- One small tier of the OpenAI family (a nano or mini tier that is currently offered). Note that earlier small models are being retired (the OpenAI table lists gpt-4.1-nano for 2026-10-23), so choose a model that will still be available during review.
- One small tier of the Google Gemini family (a Flash-Lite tier), through the OpenAI-compatible endpoint `https://generativelanguage.googleapis.com/v1beta/openai/` with a Google API key.
- One or two small open-weight instruct models (about 7 to 14 billion parameters, for example a Llama, Mistral, or Qwen model) through an OpenAI-compatible hosting service such as OpenRouter or Together.

## Candidates fixed before the runs (all through OpenRouter with one key; ids checked on the OpenRouter list of 2 October 2026)
1. openai/gpt-5-nano (reasons by default)
2. google/gemini-2.5-flash-lite
3. google/gemini-3.1-flash-lite
4. mistralai/ministral-8b-2512
5. meta-llama/llama-3.1-8b-instruct
6. google/gemma-3-12b-it
7. qwen/qwen3-14b
The list is not changed after the first run. gpt-4.1-nano is excluded because its retirement is announced for 2026-10-23. `run_small_all.bat` runs all seven in this order and `screen_report.py` prints the screening table.

## Screening rule (stated before the runs)
1. Run every candidate at three turns left: 3 frames x 16 wordings x 30 episodes = 1,440 first choices, temperature 0.7 (reasoning models use their default sampling and are flagged).
2. A model passes the screen if the pooled test-skip rate over the 1,440 first choices is at least 5%, so that frame contrasts can be estimated.
3. Passing models are also run at 6 and 12 turns left (`run_small_full.bat`) and in the Study 4 design (goal visibility and valence, `goal2x2.py`).
3a. A run in which more than 5% of first choices are parse failures or refusals is invalid and is not a floor result: its file is deleted and the model is rerun after the cause is fixed (for example a reasoning model that spent its output budget before answering), or it is excluded and the exclusion is reported. The first run of openai/gpt-5-nano was invalid in this sense (1,440 of 1,440 parse failures; the output budget of 200 tokens was used by hidden reasoning) and was rerun after the runner raised the budget automatically.
4. All candidates that were run are reported, including those that did not pass the screen; a model is not dropped or replaced after its results are seen. Parse failures and refusals are reported for every model (`check_log.py`).
5. The analysis is the one used for Haiku 4.5: wording-level cluster bootstrap, 95% intervals with a 99.6% multiplicity check, variance shares, and the same contrasts (loss minus gain, neutral minus gain; for Study 4 the registered and the goal contrasts).
6. The commit that holds this file is the time-stamped record that the plan preceded the runs.

## Cost
About 1,440 calls with roughly 900 input and 50 output tokens each, which is on the order of USD 0.1 to 1 per model for small tiers (check current prices; models that reason by default produce more output tokens and cost more).

## How the results would enter the paper
A new section after Study 5: "Replication in small models from other vendors." If one or more models skip and show the same ordering (loss below gain, goal visibility raising skipping), the generality concern is reduced; if all are at floor, we report that the environment does not elicit skipping in them, as for the larger Claude models. Either result goes in.

## Record of a decision after the runs (2 October 2026)
The first runs of openai/gpt-5-nano and qwen/qwen3-14b were invalid under rule 3a (1,440 and 1,276 parse failures; the 200-token output budget was used by hidden reasoning). The runner was fixed to raise the budget automatically, but the two models were not rerun, by the authors' decision. Under rule 3a they are excluded and the exclusion is reported in the manuscript (Table 10 and Appendices C and D). Their invalid logs are kept in the replication package and are not analyzed.
