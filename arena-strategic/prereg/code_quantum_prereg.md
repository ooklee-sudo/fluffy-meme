# Preregistration: quantum-cognition signatures in LLM code review

Written and committed before any data were collected.

## Materials and models
- The 120 HumanEval programs of the code-judgment study (`code_items.json`; 60 correct, 60 one-token
  mutants verified to fail the official tests).
- Models: qwen/qwen3.7-flash, anthropic/claude-haiku-5.5, meta-llama/llama-4-scout, deepseek/deepseek-v3.2;
  temperature 1.0, reasoning off, max 5 tokens; two repetitions per item and cell with distinct seeds.
- System prompt: an experienced Python code reviewer.

## E1 Sure-thing principle / disjunction effect (single questions, separate conversations)
Conditions: tests PASSED, tests FAILED, test results UNKNOWN; question: approve merging this pull request?
Answer labels A/B counterbalanced (M1: A = Yes; M2: A = No). Measure P(approve) per condition.
Violation of the law of total probability: P(U) below min(P(P), P(F)) or above max(P(P), P(F)), judged by a
95% item-bootstrap CI (2,000 resamples) that excludes the interval [min, max] side. Item-level sure-thing
violations (approve under P and F, not under U) are reported descriptively.

## E2 Interference (total probability)
Direct: approve merging? Indirect: first "Does this code contain a bug?", then approve merging? (one conversation).
Labels counterbalanced as in E1. Interference = P_direct(approve) - P_indirect(approve), two-sided test by
95% item-bootstrap CI; classical probability (with the first answer as a measurement that does not disturb)
predicts 0.

## E3 Conjunction fallacy (forced choice)
"Which is more probable? (A) ... (B) ...", options: "This code contains a bug." vs "This code contains a bug in a
comparison, arithmetic, or boolean operator." Option order counterbalanced. Fallacy rate = share choosing the
conjunction; reported with 95% item-bootstrap CI; any rate above 0 is a violation of probability theory
(descriptive; not unique to quantum accounts).

## Reporting rules
- All analyses per model, per label mapping and pooled (equal weights), and split by correct / buggy code.
- Degeneracy: a cell with P(approve) < .05 or > .95 in every condition is flagged; E1/E2 verdicts in such cells
  are reported but marked uninformative.
- Interpretation rule: E1 or E2 violations show non-classical (context-dependent) probability judgments that
  quantum models can describe; they do not show that quantum theory causes the behavior. E3 is consistent
  with both quantum and heuristic (representativeness) accounts.
