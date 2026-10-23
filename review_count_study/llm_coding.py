"""LLM coding stage with on-disk JSONL cache (resumable), retries, schema validation, and a mock backend.

Backends:
  anthropic : real coding via the Anthropic Messages API (needs ANTHROPIC_API_KEY)
  mock      : deterministic keyword coder for tests / demo (NOT for research use)
Cache key = hash(backend model, prompt variant, text), so re-runs only code new rows.
"""
import hashlib
import json
import re
import time
from pathlib import Path

import pandas as pd

import prompts

DEFAULT_MODEL = "claude-haiku-5-5"


def _key(model, variant, text):
    return hashlib.sha256(f"{model}|{variant}|{text}".encode()).hexdigest()


def _parse_json(s):
    s = s.strip()
    m = re.search(r"\{.*\}", s, re.S)
    if not m:
        raise ValueError("no JSON object in response")
    return json.loads(m.group(0))


class AnthropicCoder:
    def __init__(self, model=DEFAULT_MODEL, variant="base"):
        import anthropic  # imported lazily so mock/demo runs without the SDK
        self.client = anthropic.Anthropic()
        self.model, self.variant = model, variant
        self.system = prompts.SYSTEM_PROMPT if variant == "base" else prompts.SYSTEM_PROMPT_VARIANT

    def code(self, text):
        resp = self.client.messages.create(
            model=self.model, max_tokens=400, temperature=0, system=self.system,
            messages=[{"role": "user", "content": prompts.user_message(text)}])
        return prompts.validate(_parse_json(resp.content[0].text))


class MockCoder:
    """Keyword heuristics that recover the demo generator's traits. Offline testing only."""
    variant = "base"

    def __init__(self, measurement_error=True):
        """measurement_error=False yields the 'true' codes (used to simulate human labels in the demo);
        True adds extra coding error on top, mimicking an imperfect LLM."""
        self.measurement_error = measurement_error
        self.model = "mock-v2" if measurement_error else "mock_truth-v2"  # bump when coding logic changes (cache key)

    def code(self, text):
        out = self._truth(text)
        if self.measurement_error:
            h = int(hashlib.md5(("err" + text).encode()).hexdigest(), 16)
            for i, f in enumerate(prompts.SCORE_FIELDS):
                hi = 3 if f == "argument_balance" else 5
                if (h >> (5 * i)) % 3 == 0:  # ~1/3 of scores off by one
                    out[f] = max(1, min(hi, out[f] + ((h >> (5 * i + 2)) % 2) * 2 - 1))
            for i, f in enumerate(prompts.BINARY_FIELDS):
                if (h >> (40 + 3 * i)) % 8 == 0:  # ~12% binary misclassification
                    out[f] = 1 - out[f]
        return out

    def _truth(self, text):
        t = text.lower()
        neg = any(w in t for w in ("awful", "bad", "not happy", "disappointed"))
        spec = bool(re.search(r"\d", t))
        both = "on the plus side" in t
        emo = "!!!" in t
        h = int(hashlib.md5(t.encode()).hexdigest(), 16)  # deterministic coding "noise"
        j = lambda k: (h >> (4 * k)) % 3 - 1  # in {-1,0,1}
        c = lambda v, lo, hi: max(lo, min(hi, v))
        return dict(
            valid=bool(t.strip()), sentiment=c((1 if neg else 5) + (j(0) if j(1) else 0) * (1 if neg else -1), 1, 5),
            emotional_intensity=c((5 if emo else 2) + j(2), 1, 5),
            specificity=c((5 if spec else 2) + j(3), 1, 5), informativeness=c((4 if (spec or both) else 2) + j(4), 1, 5),
            argument_balance=3 if both else 1, narrative=int("first we" in t),
            explicit_recommendation=int("recommend" in t), comparison=int("compared to" in t),
            dominant_emotion=["anger", "sadness", "none"][h % 3] if neg else (["joy", "surprise", "none"][h % 3] if not emo else "joy"), evidence="")


def code_reviews(df, coder, cache_path, max_retries=3, sleep=1.0, log_every=200):
    cache_path = Path(cache_path)
    cache = {}
    if cache_path.exists():
        for line in cache_path.read_text().splitlines():
            r = json.loads(line)
            cache[r["key"]] = r["coding"]
    n_new = 0
    with cache_path.open("a") as f:
        for text in df["text"].fillna("").tolist():
            k = _key(coder.model, coder.variant, text)
            if k in cache:
                continue
            coding = None
            for attempt in range(max_retries):
                try:
                    coding = coder.code(text)
                    break
                except Exception as e:  # malformed JSON, API errors, rate limits
                    time.sleep(sleep * 2 ** attempt)
                    err = e
            if coding is None:
                coding = {"error": str(err)}
            cache[k] = coding
            f.write(json.dumps({"key": k, "coding": coding}) + "\n")
            f.flush()
            n_new += 1
            if n_new % log_every == 0:
                print(f"  coded {n_new} new reviews")
    rows = [cache[_key(coder.model, coder.variant, t)] for t in df["text"].fillna("")]
    out = pd.DataFrame(rows).drop(columns=["evidence"], errors="ignore")
    out.index = df.index
    return pd.concat([df, out], axis=1)
