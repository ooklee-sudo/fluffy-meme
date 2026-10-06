"""LLM backends. A backend spec is "<kind>:<model>":

  hf:Qwen/Qwen2.5-0.5B-Instruct      local Hugging Face model (CPU or GPU)
  anthropic:<model-id>               Anthropic API   (ANTHROPIC_API_KEY)
  openai:<model-id>                  OpenAI-compatible API (OPENAI_API_KEY, optional OPENAI_BASE_URL -> vLLM/Ollama)
  mock                               deterministic fake model, for smoke tests only
"""
import os
import random
import re


class Backend:
    spec = "?"

    def generate(self, user, system=None, max_tokens=64, temperature=0.0):
        raise NotImplementedError


class HFBackend(Backend):
    def __init__(self, model_id):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.spec = f"hf:{model_id}"
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_id)
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=dtype)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device).eval()
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token

    def generate(self, user, system=None, max_tokens=64, temperature=0.0):
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
        if getattr(self.tok, "chat_template", None):
            text = self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        else:  # base model without a chat template
            text = (system + "\n\n" if system else "") + user + "\nAnswer:"
        ids = self.tok(text, return_tensors="pt", add_special_tokens=False).to(self.device)
        kw = dict(max_new_tokens=max_tokens, pad_token_id=self.tok.pad_token_id)
        if temperature > 0:
            kw.update(do_sample=True, temperature=temperature, top_p=0.95)
        else:
            kw.update(do_sample=False)
        with self.torch.no_grad():
            out = self.model.generate(**ids, **kw)
        return self.tok.decode(out[0, ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()


class AnthropicBackend(Backend):
    def __init__(self, model_id):
        import anthropic

        self.spec = f"anthropic:{model_id}"
        self.client = anthropic.Anthropic()
        self.model = model_id

    def generate(self, user, system=None, max_tokens=64, temperature=0.0):
        kw = dict(model=self.model, max_tokens=max_tokens, messages=[{"role": "user", "content": user}])
        if system:
            kw["system"] = system
        try:
            r = self.client.messages.create(temperature=temperature, **kw)
        except Exception as e:  # some models reject sampling parameters
            if "temperature" not in str(e):
                raise
            r = self.client.messages.create(**kw)
        return "".join(b.text for b in r.content if getattr(b, "type", "") == "text").strip()


class OpenAIBackend(Backend):
    def __init__(self, model_id):
        from openai import OpenAI

        self.spec = f"openai:{model_id}"
        self.client = OpenAI()  # honours OPENAI_API_KEY / OPENAI_BASE_URL
        self.model = model_id

    def generate(self, user, system=None, max_tokens=64, temperature=0.0):
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
        r = self.client.chat.completions.create(
            model=self.model, messages=msgs, max_tokens=max_tokens, temperature=temperature)
        return (r.choices[0].message.content or "").strip()


class MockBackend(Backend):
    """Fake model so the whole pipeline can be exercised offline. NOT a real experiment."""
    spec = "mock"

    def __init__(self, seed=0):
        self.rng = random.Random(seed)

    def generate(self, user, system=None, max_tokens=64, temperature=0.0):
        if "Reply SUPPORTED or UNSUPPORTED" in (system or "") + user:  # judge role
            ans = re.search(r"Answer: (.*)", user)
            ctx = re.search(r"Passage: (.*?)\nQuestion:", user, re.S)
            a, c = (ans.group(1).strip().lower() if ans else ""), (ctx.group(1).lower() if ctx else "")
            ok = bool(a) and a in c
            return "SUPPORTED" if (ok if self.rng.random() < 0.9 else not ok) else "UNSUPPORTED"
        ctx = re.search(r"Passage: (.*?)\nQuestion:", user, re.S)
        words = re.findall(r"[A-Z][a-z]+|\d+", ctx.group(1)) if ctx else []
        r = self.rng.random()
        if r < 0.15:
            return "UNANSWERABLE"
        if r < 0.55 or not words:
            return self.rng.choice(["1987", "Paris", "Napoleon", "42", "Berlin"])
        return self.rng.choice(words)


def make_backend(spec):
    kind, _, model = spec.partition(":")
    if kind == "hf":
        return HFBackend(model)
    if kind == "anthropic":
        return AnthropicBackend(model)
    if kind == "openai":
        return OpenAIBackend(model)
    if kind == "mock":
        return MockBackend()
    raise ValueError(f"unknown backend spec: {spec!r}")
