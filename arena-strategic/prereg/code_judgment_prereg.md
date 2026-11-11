# Preregistration: Do LLMs lean toward judging code wrong, and is the pattern quantum-like?

Written and committed before any data for this study were collected.

## Materials

120 HumanEval problems, each used once (`code_items.json`): 60 canonical solutions that pass the
official tests ("correct") and 60 one-token mutants that fail them ("buggy"), built by
`src/build_code_items.py` (operator, comparison, boolean and min/max swaps).

## Evaluators

qwen/qwen3.7-flash, anthropic/claude-haiku-5.5, meta-llama/llama-4-scout; temperature 1.0,
reasoning off, max 5 tokens. System prompt: an experienced code reviewer, answer Yes or No only.

## Study A: bias and framing (single question)

Each item x evaluator is asked, in separate conversations, 5 times each:
- F1 "Is this code correct?"  (judged wrong = No)
- F2 "Does this code contain a bug?"  (judged wrong = Yes)

H1 (bias toward "wrong"). Signal detection with "bug present" as signal: hit = judged wrong on buggy
code, false alarm = judged wrong on correct code. Criterion c = -(z(H) + z(FA))/2, with a log-linear
correction (add 0.5 to counts). H1 predicts c < 0 (liberal toward "wrong"). Test per evaluator and
framing; 95% CI by bootstrap over items (2,000 resamples). Also reported: false-alarm rate, miss rate, d'.

H2 (framing). The share judged wrong is higher under F2 than under F1, for correct and for buggy code.
Test: per evaluator, paired by item, one-sided bootstrap over items at alpha = 0.05.

## Study B: question order and the QQ equality (exploratory, two-sided)

In one conversation each item is asked Q = "Is this code correct?" and R = "Is this code well
written and easy to read?" in order QR or RQ, 4 times per order per item per evaluator.
Per evaluator (pooled over items) and per evaluator x label: order effects (chi-square on the 2x4
pattern table) and q = disagreement share (QR) - disagreement share (RQ), with a two-sided z test and a
TOST equivalence test at +/-0.05 (90% CI by item bootstrap).

## Interpretation rule (fixed in advance)

A bias toward "wrong" (H1) or a framing effect (H2) is NOT evidence for quantum theory, because a
quantum model can fit any marginal. Only Study B bears on quantum-like structure, and even a QQ result
consistent with the equality would show that a quantum model *describes* the judgments, not that
quantum theory *causes* them. LLMs run on classical hardware.
