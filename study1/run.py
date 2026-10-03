"""Collect completions: 120 stems x 2 channels per model, deterministic decoding, one completion per query.

usage:
  python run.py --models models.json --only qwen2.5-7b qwen2.5-32b --out results/study1.jsonl
  python run.py --models models.json --all --resume --out results/study1.jsonl
Backends (set per model in models.json):
  hf         local transformers, official chat template, greedy decoding (do_sample=False), fixed dtype
  openai     any OpenAI-compatible endpoint (vLLM, Together, OpenRouter, HF router, OpenAI): needs base_url / key env var
  anthropic  Anthropic API; Claude models that reject temperature are called without it and this is recorded
Keys are read from environment variables only (never from files or the command line).
Item order is interleaved by a hash of stem ids, identical for every model. --cut applies the pre-registered reduction:
drop Domain 3, keep the first 16 stems of each other domain.
"""
import argparse, hashlib, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
from bank import build, render, MANIFEST_FILE
from prompts import SYSTEMS, parse


def query_order(items, cut, channels=("normative", "social")):
    if cut:
        keep = {}
        items = [i for i in items if i["domain"] != 3]
        out = []
        for i in items:
            keep[i["domain"]] = keep.get(i["domain"], 0) + 1
            if keep[i["domain"]] <= 16:
                out.append(i)
        items = out
    qs = [(i, ch) for i in items for ch in channels]
    return sorted(qs, key=lambda q: hashlib.sha256(f"{q[0]['stem_id']}|{q[1]}".encode()).hexdigest())


class HF:
    def __init__(self, spec):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        dt = {"float32": torch.float32, "bfloat16": torch.bfloat16, "float16": torch.float16}[spec.get("dtype", "bfloat16")]
        self.tok = AutoTokenizer.from_pretrained(spec["model"], revision=spec.get("revision"))
        self.m = AutoModelForCausalLM.from_pretrained(spec["model"], revision=spec.get("revision"), torch_dtype=dt, device_map=spec.get("device_map"))
        self.m.eval(); self.torch = torch; self.spec = spec
        self.revision = getattr(self.m.config, "_commit_hash", None)

    def __call__(self, system, user, max_new):
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        kw = dict(enable_thinking=self.spec["thinking"]) if "enable_thinking" in self.spec.get("template_kwargs", []) else {}
        ids = self.tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt", return_dict=True, **kw)
        ids = {k: v.to(self.m.device) for k, v in ids.items()}
        with self.torch.no_grad():
            out = self.m.generate(**ids, max_new_tokens=max_new, do_sample=False, temperature=None, top_p=None, top_k=None,
                                  pad_token_id=self.tok.eos_token_id)
        gen = out[0][ids["input_ids"].shape[1]:]
        finish = "length" if len(gen) >= max_new else "stop"
        return self.tok.decode(gen, skip_special_tokens=True), finish, int(ids["input_ids"].shape[1]), int(len(gen)), True


class OpenAICompat:
    def __init__(self, spec):
        from openai import OpenAI
        key = os.environ.get(spec.get("key_env", "OPENAI_API_KEY"))
        if not key:
            sys.exit(f"set the environment variable {spec.get('key_env', 'OPENAI_API_KEY')} first (do not paste keys into chat or files)")
        self.c = OpenAI(api_key=key, base_url=spec.get("base_url"), timeout=120.0, max_retries=3)
        self.spec = spec; self.revision = spec["model"]

    def __call__(self, system, user, max_new):
        kw = {"max_tokens": max_new} if not self.spec.get("max_completion_tokens") else {"max_completion_tokens": max_new}
        applied = True
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        for attempt in range(7):                       # upstream rate limits (429) are temporary: wait and retry before counting a call as failed
            try:
                try:
                    r = self.c.chat.completions.create(model=self.spec["model"], temperature=0, top_p=1, messages=msgs, **kw)
                except Exception as e:                 # some endpoints reject temperature 0: use the lowest permitted value and record it
                    if "temperature" not in str(e).lower():
                        raise
                    applied = False
                    r = self.c.chat.completions.create(model=self.spec["model"], messages=msgs, **kw)
                break
            except Exception as e:
                if attempt < 6 and ("429" in str(e) or "rate" in repr(e).lower()):
                    time.sleep(min(15 * 2 ** attempt, 240)); continue
                raise
        ch = r.choices[0]
        return ch.message.content or "", ch.finish_reason, r.usage.prompt_tokens, r.usage.completion_tokens, applied


class Anthropic:
    NO_SAMPLING = ("claude-opus-5", "claude-opus-4-8", "claude-opus-4-7", "claude-fable", "claude-mythos", "claude-sonnet-5")

    def __init__(self, spec):
        import anthropic
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("set ANTHROPIC_API_KEY in this window first (do not paste keys into chat or files)")
        self.c = anthropic.Anthropic(timeout=120.0, max_retries=3)
        self.spec = spec; self.revision = spec["model"]
        self.sampling_ok = not spec["model"].startswith(self.NO_SAMPLING)

    def __call__(self, system, user, max_new):
        kw = dict(model=self.spec["model"], max_tokens=max(max_new, 2048 if not self.sampling_ok else max_new), system=system,
                  messages=[{"role": "user", "content": user}])
        if self.sampling_ok:
            kw["extra_body"] = {"temperature": 0}
        r = self.c.messages.create(**kw)
        text = "".join(b.text for b in r.content if b.type == "text")
        return text, r.stop_reason, r.usage.input_tokens, r.usage.output_tokens, self.sampling_ok


def make_backend(spec):
    return {"hf": HF, "openai": OpenAICompat, "anthropic": Anthropic}[spec["backend"]](spec)


def done_keys(path):
    keys = set()
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            try:
                r = json.loads(line)
                if str(r.get("finish_reason", "")).startswith("error:"):
                    continue                           # a failed API call is not an answer: query it again on resume
                keys.add((r["model_key"], r["stem_id"], r["channel"], r.get("system_variant", 0), r.get("social_set", "A")))
            except (json.JSONDecodeError, KeyError):
                pass
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="models.json"); ap.add_argument("--only", nargs="*", default=[]); ap.add_argument("--all", action="store_true")
    ap.add_argument("--out", default="results/study1.jsonl"); ap.add_argument("--resume", action="store_true")
    ap.add_argument("--max-new", type=int, default=512, help="maximum new tokens (pre-registered: 512)")
    ap.add_argument("--cut", action="store_true", help="pre-registered reduction: drop Domain 3, 16 stems per remaining domain")
    ap.add_argument("--system-variant", type=int, default=0, choices=[0, 1, 2], help="0 = registered system prompt; 1, 2 = robustness wordings")
    ap.add_argument("--social-set", default="A", choices=["A", "B"], help="A = registered stance sentences; B = robustness wordings")
    ap.add_argument("--limit", type=int, default=0, help="debug: only the first N queries")
    ap.add_argument("--channels", nargs="+", default=["normative", "social"], choices=["normative", "social", "aligned"], help="aligned = stance that supports the gold action (Study 1b, Addendum 3; hard bank only)")
    ap.add_argument("--workers", type=int, default=4, help="parallel API calls (api backends only)")
    a = ap.parse_args()
    specs = json.load(open(a.models, encoding="utf-8"))["models"]
    chosen = [s for s in specs if a.all or s["key"] in a.only]
    if not chosen:
        sys.exit("no models selected: use --only KEY ... or --all (keys: " + ", ".join(s["key"] for s in specs) + ")")
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    if os.path.exists(a.out) and os.path.getsize(a.out) and not a.resume:
        sys.exit(f"{a.out} is not empty: pass --resume to continue it, or choose another --out")
    if os.path.exists(a.out) and os.path.getsize(a.out) and not open(a.out, "rb").read().endswith(b"\n"):
        open(a.out, "ab").write(b"\n")                  # a torn last line from an interrupted run
    man = json.load(open(MANIFEST_FILE, encoding="utf-8"))
    qs = query_order(build(), a.cut, tuple(a.channels))
    if a.limit:
        qs = qs[:a.limit]
    done = done_keys(a.out)
    for spec in chosen:
        todo = [q for q in qs if (spec["key"], q[0]["stem_id"], q[1], a.system_variant, a.social_set) not in done]
        print(f"[{spec['key']}] {len(todo)} queries to run ({len(qs) - len(todo)} already done)", flush=True)
        if not todo:
            continue
        be = make_backend(spec)
        max_new = spec.get("max_new_tokens", a.max_new)
        if max_new != a.max_new:
            print(f"  note: max_new_tokens={max_new} for this model (deviation from 512; report it)", flush=True)
        fails = {"n": 0}

        def one(q):
            item, ch = q
            t0 = time.time()
            try:
                text, finish, tin, tout, applied = be(SYSTEMS[a.system_variant], render(item, ch, a.social_set), max_new)
            except Exception as e:
                if any(w in repr(e).lower() for w in ("auth", "permission", "notfound", "not_found", "badrequest", "invalid")):
                    print("FATAL API error:", repr(e)[:300]); os._exit(2)
                fails["n"] += 1
                if fails["n"] >= 5:
                    print("5 failed calls, last error:", repr(e)[:300]); os._exit(2)
                text, finish, tin, tout, applied = "", "error:" + type(e).__name__, 0, 0, None
            letter, conf = parse(text)
            return dict(model_key=spec["key"], family=spec["family"], tier=spec["tier"], thinking=bool(spec.get("thinking", False)),
                        size_b=spec.get("size_b"), panel=spec.get("panel", "open"), model_id=spec["model"], revision=getattr(be, "revision", None),
                        stem_id=item["stem_id"], domain=item["domain"], channel=ch, system_variant=a.system_variant, social_set=a.social_set, letter=letter, confidence=conf,
                        parse_fail=letter is None, finish_reason=finish, tokens_in=tin, tokens_out=tout, temperature_applied=applied,
                        seconds=round(time.time() - t0, 2), items_sha=man["items_sha256"][:12], completion=text)

        workers = a.workers if spec["backend"] != "hf" else 1
        n = 0
        with open(a.out, "a", encoding="utf-8") as f, ThreadPoolExecutor(workers) as ex:
            for row in ex.map(one, todo):
                f.write(json.dumps(row, ensure_ascii=False) + "\n"); f.flush(); n += 1
                if n % 20 == 0 or n == len(todo):
                    print(f"  {n}/{len(todo)}", flush=True)
        del be


if __name__ == "__main__":
    main()
