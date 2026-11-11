# Preregistration: Do LLM judgments follow the QQ equality when the model hallucinates?

Written and committed before any data for this study were collected.

## Hypothesis

H1. Yes/no judgments about **nonexistent entities** (F; any yes/no answer is by definition a
hallucination) violate the QQ equality less often than matched judgments about **real entities** (R).

Rationale: quantum models describe judgments that are constructed when elicited; answers about entities
the model cannot know are constructed rather than retrieved.

## Design

- 12 fictional items, each mirrored one to one by a real item asking the same two questions about a real
  entity of the same kind (6 well known, 6 less well known). Listed in `src/qq_hallucination.py`.
- Evaluators: qwen/qwen3.7-flash, anthropic/claude-haiku-5.5, meta-llama/llama-4-scout; temperature 1.0,
  reasoning off, max 5 tokens, distinct seed per repetition. System prompt: answer Yes or No only.
- Each trial asks both questions in one conversation, in order AB or BA; 200 trials per item x order x
  evaluator (28,800 trials).
- Knowledge check: in separate conversations, "Do you know <entity>?" 20 times per item x evaluator.

## Measures and decision rules (same as the task-type preregistration)

- Hallucination rate = share of F trials in which both questions received Yes/No answers.
- Per item x evaluator cell, using answered trials only: q, z, two-sided p; violation = p < 0.05.
- Degenerate cells (either question's yes-share when asked first < 0.05 or > 0.95) are excluded from the
  primary test and reported. Cells with fewer than 30 answered trials per order are also excluded.
- Primary test: Fisher's exact test, one-sided, violation rate R > F, alpha = 0.05 (chosen over the
  logistic model used before because that model failed by complete separation). Secondary: mean z^2 by
  type, Mann-Whitney one-sided; logistic regression with evaluator fixed effects if estimable.
- Results are reported whatever their direction. A QQ-consistent result would show that a quantum model
  describes hallucinated judgments, not that hallucination is a quantum phenomenon.
