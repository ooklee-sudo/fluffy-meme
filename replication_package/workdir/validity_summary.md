# Validity check of the tag-accuracy metric (80 questions, ~20 tags; cost about $3.9)

Grading rubrics on regenerated answers (user-message-only prompt):
| Model | n | R1 original (same core solution, key part) | R2 relaxed (any valid solution, full answer, gpt-4.1 judge) | avg length (chars) |
|---|---|---|---|---|
| GPT-3.5 | 80 | 43.8% | 96.2% | 3284 |
| GPT-4o | 80 | 55.0% | 85.0% | 2339 |
| GPT-4 | 30 | 60.0% | 86.7% | 3342 |

R2 saturates and ranks GPT-3.5 highest (an LLM judge accepts long confident answers): not usable as ground truth.

Prompt-format sensitivity under R1, same 80 questions:
| Model | user-message prompt | system-role prompt | earlier large run (system-role) |
|---|---|---|---|
| GPT-3.5 | 43.8% | 55.0% | 56.2% |
| GPT-4o | 55.0% | 52.5% | 53.8% |

Item-level agreement between two runs with the same prompt (T=0): 84% (GPT-3.5), 89% (GPT-4o).

Conclusions: GPT-3.5's accuracy moves by about 11 pp with prompt format (more than the whole GPT-4o vs GPT-3.5 gap and about 3x the tag-level signal SD of 0.04); the earlier "GPT-4o below GPT-3.5" came from this format effect. A change-in-accuracy treatment built on this metric is not reliable without a fixed, preregistered protocol and robustness checks across prompts.
