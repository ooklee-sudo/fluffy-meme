"""LLM star-rating inference (Winter et al. 2026-style): predict the star rating the author gave from the text alone.
Reuses the cached/concurrent coding loop in llm_coding.code_reviews; the result column is `stars_llm` (1-5)."""
import json

import llm_coding

STAR_SYSTEM = ("You read one online product review and infer the star rating (1 to 5, integers) its author gave, "
               "based only on the review text. 1 = very dissatisfied, 5 = very satisfied. "
               'Respond with ONLY a JSON object like {"stars_llm": 4}, no other text.')


class StarCoder(llm_coding.OpenRouterCoder):
    def __init__(self, model="anthropic/claude-haiku-5.5"):
        super().__init__(model, "stars")
        self.system = STAR_SYSTEM

    def code(self, text):
        out = self._call(text, max_tokens=60)
        obj = llm_coding._parse_json(out)
        v = obj.get("stars_llm")
        if isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= 5:
            raise ValueError(f"bad stars_llm {v!r}")
        return {"stars_llm": v}
