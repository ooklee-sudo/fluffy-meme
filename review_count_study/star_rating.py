"""LLM star-rating inference (Winter et al. 2026-style): predict the star rating the author gave from the text alone.
Reuses the cached/concurrent coding loop in llm_coding.code_reviews; the result column is `stars_llm` (1-5)."""
import json
import re

import llm_coding

STAR_SYSTEM = ("You read one online product review and infer the star rating (1 to 5, integers) its author gave, "
               "based only on the review text. 1 = very dissatisfied, 5 = very satisfied. "
               'Respond with ONLY a JSON object like {"stars_llm": 4}, no other text.')


def parse_stars(out):
    """JSON {"stars_llm"/"stars"/"rating": n} if present, otherwise the single digit 1-5 in a free-form reply."""
    try:
        obj = llm_coding._parse_json(out)
        for k in ("stars_llm", "stars", "rating", "star_rating"):
            if k in obj:
                v = int(round(float(obj[k])))
                if 1 <= v <= 5:
                    return v
    except (ValueError, TypeError):
        pass
    m = re.search(r"(?<![\d.])([1-5])\s*(?:/|out of)\s*5\b", out)
    if m:
        return int(m.group(1))
    digits = set(re.findall(r"(?<![\d.])([1-5])(?![\d.]|\s*(?:out of|/)\s*[6-9])", out))
    if len(digits) == 1:  # ambiguous replies (several different digits) are rejected, not guessed
        return int(digits.pop())
    raise ValueError(f"cannot parse a unique 1-5 rating from {out[:80]!r}")


class StarCoder(llm_coding.OpenRouterCoder):
    """Star inference. Default prompt is ours (STAR_SYSTEM). For the replication of Winter et al. (2026) pass
    system=<their system prompt verbatim>, tag='orig', temperature=0.2, raw_user=True so the review text is sent
    unwrapped. tag separates the on-disk cache from other prompts."""

    def __init__(self, model="anthropic/claude-haiku-5.5", system=None, tag="stars", temperature=0.0, raw_user=False):
        super().__init__(model, tag)
        self.system = system or STAR_SYSTEM
        self.temperature, self.raw_user = temperature, raw_user

    def code(self, text):
        return {"stars_llm": parse_stars(self._call(text, max_tokens=60))}
