# Preregistration: Study 3, free-text review of realistic pull requests

Written and committed before any data were collected. Purpose: test whether the interference and
sure-thing effects of Study 2 hold for longer pull requests, free-text reviews, a lower temperature,
and larger and reasoning models.

## Materials
- 60 pull requests, each adding a module of three functions drawn from the 120 HumanEval programs of
  Studies 1 and 2 (`code_items.json`), with a title and one-line description. 30 "clean" PRs contain three
  correct functions; 30 "defective" PRs contain two correct functions and one verified one-token mutant.
  Construction is fixed by `src/build_prs.py` (seed 2027) before data collection.

## Models
qwen/qwen3.7-flash, anthropic/claude-haiku-5.5, meta-llama/llama-4-scout, deepseek/deepseek-v3.2 (reasoning off),
deepseek/deepseek-v3.2 (reasoning on). Temperature 0.7; max 700 output tokens (3,000 with reasoning);
two repetitions per PR and condition with distinct seeds.

## Conditions (each a separate conversation)
- DIRECT: review the PR in free text and end with "DECISION: APPROVE" or "DECISION: REQUEST CHANGES".
- BUGFIRST: first asked "Before your review, list any bugs you can find in this pull request."; then the
  DIRECT instruction in the same conversation.
- CI_PASS / CI_FAIL / CI_UNKNOWN: the DIRECT instruction preceded by the CI status (all tests passed /
  one test failed / CI still running, result unknown).
The decision is parsed from the last DECISION line; reviews without a parsable decision are unanswered.

## Hypotheses and tests (per model, 95% bootstrap CI over PRs, 2,000 resamples)
- H4' (interference): P(approve | DIRECT) - P(approve | BUGFIRST) != 0.
- H3' (total probability): P(approve | CI_UNKNOWN) outside [min, max] of CI_PASS and CI_FAIL.
- Also reported: approval by clean vs defective PRs; whether the free-text review names the defective
  function (detection), by condition; elicitation-variance decomposition as in the Study 2 analysis.
Results are reported whatever their direction.
