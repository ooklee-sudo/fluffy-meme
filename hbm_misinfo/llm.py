"""Thin wrapper around any OpenAI-compatible chat endpoint.

Works with a local server on an 8 GB GPU (Ollama, llama.cpp server, vLLM)
or with a hosted gateway such as OpenRouter. Configure with environment
variables:

    LLM_BASE_URL   default http://localhost:11434/v1   (Ollama)
    LLM_MODEL      default qwen2.5:7b-instruct
    LLM_API_KEY    default "local" (ignored by local servers)
    LLM_EXTRA_BODY optional JSON merged into each request, e.g. '{"reasoning": {"enabled": false}}'
                   for OpenRouter, to switch off a model's thinking mode
"""
from __future__ import annotations

import json
import os
import re
import time

from openai import OpenAI

BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
MODEL = os.environ.get("LLM_MODEL", "qwen2.5:7b-instruct")
API_KEY = os.environ.get("LLM_API_KEY", "local")
EXTRA_BODY = json.loads(os.environ.get("LLM_EXTRA_BODY", "{}"))

_client = None


def client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=120)
    return _client


def _extract_json(text: str):
    """Return the first JSON object in a model reply (tolerates code fences and preambles)."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        raise ValueError("no JSON object in reply")
    return json.loads(m.group(0))


def chat_json(system: str, user: str, temperature: float = 0.0, max_tokens: int = 1500,
              retries: int = 3, seed: int | None = 0) -> dict:
    """Ask for a JSON object; retry on transport errors or unparsable output."""
    last_err = None
    for attempt in range(retries):
        try:
            kwargs = dict(model=MODEL, temperature=temperature, max_tokens=max_tokens,
                          messages=[{"role": "system", "content": system},
                                    {"role": "user", "content": user}])
            if seed is not None:
                kwargs["seed"] = seed
            if EXTRA_BODY:
                kwargs["extra_body"] = EXTRA_BODY
            resp = client().chat.completions.create(**kwargs)
            choice = resp.choices[0]
            if not choice.message.content and choice.finish_reason == "length":
                raise ValueError("empty reply cut off by max_tokens (model may be spending tokens on hidden reasoning)")
            return _extract_json(choice.message.content or "")
        except Exception as e:  # noqa: BLE001 - surface the last error after retries
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"LLM call failed after {retries} attempts: {last_err}")
