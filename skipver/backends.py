"""Model backends and response parsing.

openrouter : any model on OpenRouter (the aggregator used in Study 6; also
             reaches the Claude tiers used in Studies 1-5).
local      : Hugging Face model on CPU/GPU with the JSON pre-fill used for the
             open models in Study 1 (Appendix B).
mock       : fixed-probability policy, for testing the pipeline offline.
"""
from __future__ import annotations

import json
import os
import random
import re
import time
from dataclasses import dataclass, field

import requests

from env import ACTION_ORDER

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
PREFILL = '{"action": "'


class ClientError(RuntimeError):
    """A 4xx that retrying will not fix (bad parameter, unknown model)."""


@dataclass
class ModelSpec:
    name: str                       # short label used in logs and analysis
    model_id: str                   # backend model id
    backend: str = "openrouter"
    temperature: float | None = 0.7  # None = do not send (model default)
    reasoning: dict | None = None   # OpenRouter `reasoning` object, e.g. {"max_tokens": 2000}
    max_tokens: int = 400
    provider: dict | None = None    # OpenRouter provider routing, optional
    extra: dict = field(default_factory=dict)

    def label(self) -> dict:
        return {"model": self.name, "model_id": self.model_id,
                "temperature": self.temperature, "reasoning": self.reasoning}


@dataclass
class Reply:
    text: str
    reasoning_text: str = ""
    model_version: str = ""
    provider: str = ""
    usage: dict = field(default_factory=dict)
    temperature_applied: bool = False


# ---------------------------------------------------------------- parsing
_JSON_RE = re.compile(r"\{.*?\}", re.S)


def parse_action(text: str, allowed=ACTION_ORDER) -> tuple[str, str, bool]:
    """Return (action, reason, parse_fail). Failures map to hold (Section 4.3)."""
    if not text:
        return "hold", "", True
    cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    for cand in [cleaned] + _JSON_RE.findall(cleaned):
        try:
            obj = json.loads(cand)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(obj, dict):
            a = str(obj.get("action", "")).strip().lower()
            if a in allowed:
                return a, str(obj.get("reason", ""))[:500], False
    return "hold", "", True


# ---------------------------------------------------------------- backends
class OpenRouterBackend:
    def __init__(self, spec: ModelSpec, timeout: int = 120, max_retries: int = 5):
        self.spec, self.timeout, self.max_retries = spec, timeout, max_retries
        # The agent proxy injects the real key; a placeholder is enough here.
        self.key = os.environ.get("OPENROUTER_API_KEY", "sk-or-placeholder")
        self.session = requests.Session()

    def __call__(self, system: str, user: str) -> Reply:
        s = self.spec
        body = {"model": s.model_id, "max_tokens": s.max_tokens,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}], **s.extra}
        if s.temperature is not None:
            body["temperature"] = s.temperature
        if s.reasoning is not None:
            body["reasoning"] = s.reasoning
        if s.provider is not None:
            body["provider"] = s.provider
        last = None
        for attempt in range(self.max_retries):
            try:
                r = self.session.post(OPENROUTER_URL, json=body, timeout=self.timeout,
                                      headers={"Authorization": f"Bearer {self.key}"})
            except requests.RequestException as e:
                last = e
                time.sleep(2 ** attempt)
                continue
            if r.status_code in (429, 500, 502, 503, 504, 529):
                last = RuntimeError(f"{r.status_code}: {r.text[:200]}")
                time.sleep(2 ** attempt + random.random())
                continue
            try:
                d = r.json()
            except ValueError:
                last = RuntimeError(f"{r.status_code}: non-JSON body")
                time.sleep(2 ** attempt)
                continue
            if "error" in d:
                code = d["error"].get("code")
                if isinstance(code, int) and 400 <= code < 500 and code != 429:
                    raise ClientError(json.dumps(d["error"])[:500])
                last = RuntimeError(json.dumps(d["error"])[:300])
                time.sleep(2 ** attempt + random.random())
                continue
            if r.status_code >= 400:
                raise ClientError(f"{r.status_code}: {r.text[:300]}")
            msg = d["choices"][0]["message"]
            return Reply(text=msg.get("content") or "",
                         reasoning_text=msg.get("reasoning") or "",
                         model_version=d.get("model", ""),
                         provider=d.get("provider", ""),
                         usage=d.get("usage") or {},
                         temperature_applied=s.temperature is not None)
        raise RuntimeError(f"failed after {self.max_retries} attempts: {last}")


class LocalBackend:
    """Hugging Face chat model with the JSON pre-fill (Study 1 open models)."""

    def __init__(self, spec: ModelSpec):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        self.spec, self.torch = spec, torch
        self.tok = AutoTokenizer.from_pretrained(spec.model_id)
        self.model = AutoModelForCausalLM.from_pretrained(spec.model_id, torch_dtype=torch.float32)
        self.model.eval()

    def __call__(self, system: str, user: str) -> Reply:
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        prompt = self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True) + PREFILL
        ids = self.tok(prompt, return_tensors="pt")
        t = self.spec.temperature
        with self.torch.no_grad():
            out = self.model.generate(**ids, max_new_tokens=min(self.spec.max_tokens, 80),
                                      do_sample=bool(t), temperature=t or None,
                                      pad_token_id=self.tok.eos_token_id)
        gen = self.tok.decode(out[0, ids["input_ids"].shape[1]:], skip_special_tokens=True)
        text = PREFILL + gen
        # Close a truncated object so the parser can read the action.
        if "}" not in text:
            text = text + ('"}' if text.count('"') % 2 else "}")
        return Reply(text=text, model_version=self.spec.model_id, temperature_applied=bool(t))


class MockBackend:
    """Skips with probability p_skip (higher when the target is in the headline)."""

    def __init__(self, spec: ModelSpec):
        self.spec = spec
        self.p = spec.extra.get("p_skip", 0.2)

    def __call__(self, system: str, user: str) -> Reply:
        head = user.splitlines()[0].lower()
        p = self.p * (2.0 if "target" in head else 0.5)
        a = random.choice(["narrow_skip", "wide_skip"]) if random.random() < p else "narrow_patch"
        return Reply(text=json.dumps({"action": a, "reason": "mock"}), model_version="mock")


def make_backend(spec: ModelSpec):
    return {"openrouter": OpenRouterBackend, "local": LocalBackend,
            "mock": MockBackend}[spec.backend](spec)
