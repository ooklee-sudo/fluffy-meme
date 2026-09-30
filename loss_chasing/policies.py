"""Decision makers: benchmark policies (Sec 6.4), synthetic agents for pipeline tests, and LLM backends."""
from __future__ import annotations
import json, math, re
import numpy as np
from env import ACTIONS, TABLE1, SKIPS
from frames import SYSTEM


class Policy:
    name = "policy"
    def act(self, env, frame, prompt, order, temperature, rng):  # -> (action, reason, parse_fail)
        raise NotImplementedError


class Greedy(Policy):
    name = "greedy_ev"
    def act(self, env, *a, **k):
        return max(ACTIONS, key=env.ev), "max EV", False

class Always(Policy):
    def __init__(self, action):
        self.action, self.name = action, f"always_{action}"
    def act(self, *a, **k):
        return self.action, "fixed", False


class SyntheticProspect(Policy):
    """SYNTHETIC agent for smoke-testing the pipeline ONLY. Its parameters are made up;
    its output must never be reported as an empirical result."""
    name = "synthetic_prospect"
    def __init__(self, loss_bias=1.0, streak_bias=0.4, noise=1.0):
        self.lb, self.sb, self.noise = loss_bias, streak_bias, noise
    def act(self, env, frame, prompt, order, temperature, rng):
        temp = max(temperature, 0.05) * self.noise
        bonus = (self.lb if frame == "loss" else 0.0) + self.sb * env.fail_streak
        u = np.array([env.ev(a) + (bonus * TABLE1[a][4] if a != "rollback" else 0) for a in ACTIONS])
        p = np.exp((u - u.max()) / temp); p /= p.sum()
        return ACTIONS[rng.choice(len(ACTIONS), p=p)], "synthetic", False


# ---------------------------------------------------------------- LLM backends
def parse_action(text):
    """JSON-only output; anything unparsable -> ('hold', flagged)."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if m:
        try:
            o = json.loads(m.group(0))
            if o.get("action") in ACTIONS:
                return o["action"], str(o.get("reason", ""))[:300], False
        except Exception:
            pass
    return "hold", "PARSE_FAIL", True


PREFILL = '{"action": "'   # local models: force the JSON-only format (keeps parsing strict)


class LLM(Policy):
    def __init__(self, backend, model, rational_prime=False, max_tokens=200):
        self.backend, self.model, self.max_tokens = backend, model, max_tokens
        self.name = f"{backend}:{model}" + ("+rational" if rational_prime else "")
        self.system = SYSTEM + (" Act as a rational investor and maximize expected value." if rational_prime else "")
        if backend == "anthropic":
            import anthropic; self.c = anthropic.Anthropic()
        elif backend == "openai":                      # any OpenAI-compatible endpoint (OPENAI_BASE_URL)
            import openai; self.c = openai.OpenAI()
        elif backend == "hfapi":                       # Hugging Face Inference API (needs HF_TOKEN)
            from huggingface_hub import InferenceClient; self.c = InferenceClient(model=model)
        elif backend == "hf":                          # local transformers model (CPU/GPU/MPS)
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.torch = torch
            self.tok = AutoTokenizer.from_pretrained(model)
            self.m = AutoModelForCausalLM.from_pretrained(model, torch_dtype=torch.float32).eval()
        else:
            raise ValueError(backend)

    def _local(self, prompt, temperature):
        msgs = [{"role": "system", "content": self.system}, {"role": "user", "content": prompt}]
        text = self.tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False) + PREFILL
        ids = self.tok(text, return_tensors="pt", add_special_tokens=False)
        kw = dict(do_sample=True, temperature=temperature) if temperature > 0 else dict(do_sample=False)
        with self.torch.no_grad():
            out = self.m.generate(**ids, max_new_tokens=self.max_tokens, pad_token_id=self.tok.eos_token_id, **kw)
        return PREFILL + self.tok.decode(out[0, ids["input_ids"].shape[1]:], skip_special_tokens=True)

    def act(self, env, frame, prompt, order, temperature, rng):
        for attempt in range(4):
            try:
                if self.backend == "hf":
                    text = self._local(prompt, temperature)
                elif self.backend == "hfapi":
                    r = self.c.chat_completion(messages=[{"role": "system", "content": self.system},
                        {"role": "user", "content": prompt}], max_tokens=self.max_tokens, temperature=max(temperature, 0.01))
                    text = r.choices[0].message.content
                elif self.backend == "anthropic":
                    r = self.c.messages.create(model=self.model, max_tokens=self.max_tokens, temperature=temperature,
                                               system=self.system, messages=[{"role": "user", "content": prompt}])
                    text = "".join(b.text for b in r.content if b.type == "text")
                else:
                    r = self.c.chat.completions.create(model=self.model, max_tokens=self.max_tokens,
                        temperature=temperature, messages=[{"role": "system", "content": self.system},
                                                           {"role": "user", "content": prompt}])
                    text = r.choices[0].message.content
                return parse_action(text)
            except Exception as e:
                import sys, time
                print(f"[API error, attempt {attempt + 1}/4] {type(e).__name__}: {str(e)[:200]}", file=sys.stderr, flush=True)
                if type(e).__name__ in ("AuthenticationError", "PermissionDeniedError", "NotFoundError", "BadRequestError"):
                    raise SystemExit("Fatal API error (check key, billing, model name). Stopping so no bad data is written.")
                time.sleep(2 ** attempt)
        self.fails = getattr(self, "fails", 0) + 1
        if self.fails >= 5:
            raise SystemExit("5 calls failed after retries. Stopping so no bad data is written.")
        return "hold", "API_ERROR", True


def make_policy(spec, rational_prime=False):
    if spec == "greedy": return Greedy()
    if spec.startswith("always:"): return Always(spec.split(":", 1)[1])
    if spec == "synthetic": return SyntheticProspect()
    backend, model = spec.split(":", 1)
    return LLM(backend, model, rational_prime)
