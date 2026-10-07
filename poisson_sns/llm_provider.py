"""Optional real-LLM intensity provider (proposal section 4 prompt).  Not used in the
reported results (no API key in the run environment).  Usage:

    from sim import Sim, CachedProvider
    from llm_provider import LLMIntensity
    Sim(provider=CachedProvider(LLMIntensity()), ...)

CachedProvider discretises the state, so #API calls is bounded by the number of
distinct states (a few thousand), not by the number of exposures.
"""
import json
import re

from sim import prompt_for


class LLMIntensity:
    name = "llm"

    def __init__(self, model="claude-haiku-4-5-20251001"):
        import anthropic
        self.client, self.model = anthropic.Anthropic(), model

    def __call__(self, persona, hour, emotion, rel_count, rel_bucket, notif):
        msg = self.client.messages.create(
            model=self.model, max_tokens=120, temperature=0,
            messages=[{"role": "user", "content": prompt_for(persona, hour, emotion, rel_count, notif)}])
        txt = msg.content[0].text
        try:
            j = json.loads(re.search(r"\{.*\}", txt, re.S).group(0))
            return min(5.0, max(0.0, float(j["intensity"]))), j.get("reason", "")
        except Exception:
            return 1.0, "parse-failure-default"
