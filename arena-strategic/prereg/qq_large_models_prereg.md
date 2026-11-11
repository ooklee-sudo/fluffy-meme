# Preregistration addendum: Study 2R with larger and reasoning models

Written and committed before any data were collected. Motivated by the concern that results from three
small models may not hold for larger or reasoning models.

- Models: deepseek/deepseek-v3.2 (reasoning off), qwen/qwen3-235b-a22b-2507 (reasoning off), and
  deepseek/deepseek-v3.2 with reasoning enabled (max 3,000 tokens; only the final answer is parsed and
  appended to the conversation).
- Design identical to Study 2R (prereg/qq_counterbalanced_prereg.md): five item pairs, letter labels in
  two counterbalanced mappings, simulated US-adult respondents, temperature 1.0, but 150 respondents per
  item x order x mapping x model (9,000 interviews).
- Analysis identical to Study 2R: mapping-specific q, equal-weight pooled q, two-sided test at 5 percent,
  label robustness, comparison with the human benchmark (Wang et al. 2014, Table 1) on yes-shares and
  order-effect signs.
- Primary question: does any of these models reproduce the human QQ pattern (equality holds for
  Clinton-Gore and White-Black, fails for Rose-Jackson) in both label mappings?
