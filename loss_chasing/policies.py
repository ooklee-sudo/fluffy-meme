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


class LLM(Policy):
    def __init__(self, backend, model, rational_prime=False, max_tokens=200):
        self.backend, self.model, self.max_tokens = backend, model, max_tokens
        self.name = f"{backend}:{model}" + ("+rational" if rational_prime else "")
        self.system = SYSTEM + (" Act as a rational investor and maximize expected value." if rational_prime else "")
        if backend == "anthropic":
            import anthropic; self.c = anthropic.Anthropic()
        elif backend == "openai":                      # any OpenAI-compatible endpoint (OPENAI_BASE_URL)
            import openai; self.c = openai.OpenAI()
        else:
            raise ValueError(backend)

    def act(self, env, frame, prompt, order, temperature, rng):
        for attempt in range(4):
            try:
                if self.backend == "anthropic":
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
                import time; time.sleep(2 ** attempt)
        return "hold", "API_ERROR", True


def make_policy(spec, rational_prime=False):
    if spec == "greedy": return Greedy()
    if spec.startswith("always:"): return Always(spec.split(":", 1)[1])
    if spec == "synthetic": return SyntheticProspect()
    backend, model = spec.split(":", 1)
    return LLM(backend, model, rational_prime)
