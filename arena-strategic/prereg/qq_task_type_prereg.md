# Preregistration: Does QQ conformity in LLM judgments depend on task type?

Written and committed before any data for this study were collected.

## Hypothesis

H1. LLM yes/no judgments about **content presented in the prompt** (stimulus-based, S) violate the
QQ equality less often than judgments that rest on **stored knowledge or trained policy** about
people, groups, institutions and policies (knowledge/policy-based, K).

## Design

- Evaluators: qwen/qwen3.7-flash, anthropic/claude-haiku-5.5, meta-llama/llama-4-scout
  (temperature 1.0, reasoning off, max 5 tokens).
- Respondents: random US-adult personas (age, gender, race, region, education, party), generated
  by the same function and seed scheme for both task types.
- Items: 12 S items and 12 K items (listed in `src/qq_task_type.py`, fixed before running).
  - S: a real AI-assistant answer from the Arena 140k release (English, 400-1,200 characters,
    no model/company names) shown to the respondent, followed by two yes/no questions about it.
    Six question pairs, each used for two stimuli.
  - K: two yes/no questions about public figures, groups, institutions or policies, no stimulus.
- Each respondent answers both questions in sequence in one conversation, in one of two orders.
  200 respondents per item x order x evaluator (28,800 interviews).

## Measures and decision rules

- Per item x evaluator cell: q = disagreement share (order AB) - disagreement share (order BA);
  z = q / SE with SE = sqrt(dA(1-dA)/nA + dB(1-dB)/nB).
- **Violation** = two-sided p < 0.05 for q = 0.
- **Degenerate** cells are excluded from the primary test and reported separately: a cell is
  degenerate if either question's yes-share, when asked first, is below 0.05 or above 0.95.
- **Primary test**: logistic regression of violation (0/1) on task type (K vs S) with evaluator fixed
  effects, standard errors clustered by item; one-sided test of H1 at alpha = 0.05 (K > S).
  Fisher's exact test on the pooled 2x2 table is reported as a check.
- **Secondary**: mean z^2 by task type (under QQ, E[z^2] = 1), Mann-Whitney test; share of cells
  with a significant order effect (chi-square on the 2x4 table, p < 0.05) by task type.
- Results are reported whatever their direction. No items are added or dropped after data collection
  except by the degeneracy rule above.
