# Original star-inference system prompt (Winter, Zacharias & Hartwig 2026)

Source: Web Appendix 7 (GUIDE-LLM), Items B.3, C.1, C.2 of the supplementary material to
Winter et al. (2026), *Marketing Letters* 37:30, https://doi.org/10.1007/s11002-026-09824-7 (CC BY 4.0).

The supplementary lists the system prompt as three separate strings:
1. "You are a classifier. Your job is to tell me the star rating of a product review."
2. "Treat every prompt as if it were a review."
3. "Answer only with the corresponding number between 1 and 5."

How the three strings were combined into `system_prompt` (separator) is not shown; we join them with single
spaces (`winter2026_system_prompt.txt`). The user message is the raw review text. Settings: temperature 0.2,
one completion, stateless calls (original: OpenAI API; ours: other LLMs via OpenRouter).
