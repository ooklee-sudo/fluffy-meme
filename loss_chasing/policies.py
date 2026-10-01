"""Decision makers: benchmark policies (Sec 6.4), synthetic agents for pipeline tests, and LLM backends."""
from __future__ import annotations
import inspect, json, math, re, threading
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
# Newer Claude models reject temperature/top_p/top_k (400) and always think, so thinking tokens count against max_tokens.
NO_SAMPLING = ("claude-opus-5", "claude-opus-4-8", "claude-opus-4-7", "claude-fable", "claude-mythos", "claude-sonnet-5")
PRICES = {"claude-opus-5-5": (4.0, 20.0), "claude-fable-5-1": (10.0, 50.0), "claude-sonnet-5-5": (2.0, 10.0),
          "claude-haiku-4-5": (1.0, 5.0)}   # USD per 1M tokens (input, output); check the current price list


class LLM(Policy):
    def __init__(self, backend, model, rational_prime=False, max_tokens=200, thinking_budget=None):
        self.backend, self.model, self.max_tokens = backend, model, max_tokens
        self.thinking_budget = thinking_budget
        self.name = f"{backend}:{model}" + (f"+think{thinking_budget}" if thinking_budget else "") + ("+rational" if rational_prime else "")
        self.system = SYSTEM + (" Act as a rational investor and maximize expected value." if rational_prime else "")
        self.controls_temperature = not (backend == "anthropic" and model.startswith(NO_SAMPLING))
        if not self.controls_temperature:
            self.max_tokens = max(self.max_tokens, 4000)
        if thinking_budget:                      # extended thinking on a model that allows it off by default (e.g. Haiku 4.5); temperature must stay default
            self.controls_temperature = False
            self.max_tokens = thinking_budget + 2000
        self.tok_in = self.tok_out = self.n_calls = 0
        self._lock, self._tl = threading.Lock(), threading.local()
        if backend == "anthropic":
            import anthropic; self.c = anthropic.Anthropic(timeout=60.0, max_retries=2)  # fail fast instead of hanging for minutes
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

    @property
    def last_usage(self):
        return getattr(self._tl, "usage", None)

    def cost_line(self):
        if not self.n_calls:
            return ""
        pin, pout = next((v for k, v in PRICES.items() if self.model.startswith(k)), (None, None))
        usd = f", est. ${(self.tok_in * pin + self.tok_out * pout) / 1e6:.2f}" if pin is not None else ""
        return f"  [{self.n_calls} calls, {self.tok_in} in / {self.tok_out} out tokens{usd}]"

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
                    kw = dict(model=self.model, max_tokens=self.max_tokens, system=self.system,
                              messages=[{"role": "user", "content": prompt}])
                    if self.thinking_budget:
                        kw["thinking"] = {"type": "enabled", "budget_tokens": self.thinking_budget}
                    # newer SDKs dropped the `temperature` keyword; send it in the raw request body instead
                    if not self.controls_temperature:
                        pass                      # these models reject sampling parameters: default sampling is used
                    elif "temperature" in inspect.signature(self.c.messages.create).parameters:
                        kw["temperature"] = temperature
                    else:
                        kw["extra_body"] = {"temperature": temperature}
                    r = self.c.messages.create(**kw)
                    u = getattr(r, "usage", None)
                    if u is not None:
                        self._tl.usage = (u.input_tokens, u.output_tokens)
                        with self._lock:
                            self.tok_in += u.input_tokens; self.tok_out += u.output_tokens; self.n_calls += 1
                    if getattr(r, "stop_reason", None) == "refusal":
                        return "hold", "REFUSAL", True
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
                if isinstance(e, (TypeError, AttributeError, NameError)) or type(e).__name__ in ("AuthenticationError", "PermissionDeniedError", "NotFoundError", "BadRequestError"):
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
    budget = None
    if "+think" in model:                      # e.g. anthropic:claude-haiku-4-5-20251001+think2000
        model, budget = model.split("+think"); budget = int(budget)
    return LLM(backend, model, rational_prime, thinking_budget=budget)
