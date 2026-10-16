"""Optional real-LLM backend (not executed in the offline simulation).

Usage sketch:
    llm = AnthropicLLM(model="claude-sonnet-5-5")
    y = llm.direct_counts(personas)           # condition A
    spec = llm.describe_distribution(persona) # condition C: {"mean": .., "dispersion_k": ..}
Set ANTHROPIC_API_KEY. Run a 1,000-persona pilot first to check cost.
"""
import json
import re


def persona_text(seg, treat):
    kind = {0: "an occasional", 1: "a regular", 2: "a frequent"}[seg]
    promo = "received a 15% discount coupon this month" if treat else "received no promotion this month"
    return f"You are {kind} online grocery shopper who {promo}."


class AnthropicLLM:
    def __init__(self, model="claude-sonnet-5-5", temperature=1.0):
        import anthropic  # lazy import
        self.client, self.model, self.t = anthropic.Anthropic(), model, temperature

    def _ask(self, prompt):
        r = self.client.messages.create(model=self.model, max_tokens=200, temperature=self.t,
                                        messages=[{"role": "user", "content": prompt}])
        return r.content[0].text

    def direct_count(self, seg, treat):
        txt = self._ask(persona_text(seg, treat) + " How many separate orders do you place in the next 4 weeks? "
                        "Answer with a single non-negative integer only.")
        m = re.search(r"\d+", txt)
        return int(m.group()) if m else None

    def describe_distribution(self, seg, treat):
        txt = self._ask(persona_text(seg, treat) + " Across 1,000 shoppers like you, describe the number of orders in "
                        'the next 4 weeks as JSON: {"mean": float, "variance": float, "share_zero": float}.')
        return json.loads(re.search(r"\{.*\}", txt, re.S).group())
