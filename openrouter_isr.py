"""Migration breakage vs. integration depth across consecutive API model versions (OpenRouter).

Follow-up to Section 8.1 of "Updating AI Platforms": a developer app of integration depth d
(0 = plain Q&A ... 3 = strict multi-rule pipeline) is tuned on version v_k and then run, unchanged,
on v_{k+1}. We measure per depth:
  strict accuracy, content accuracy (facts right, format ignored), format-failure rate,
  and regression rate = P(strict-correct on old & strict-wrong on new)  (migration-cost proxy).
Prediction (P3 / Prop. 6): regression and format failures rise with depth, while content accuracy does not.

    export OPENROUTER_API_KEY=...
    python openrouter_isr.py --n 40                 # default chains
    python openrouter_isr.py --mock                 # no network, pipeline check
"""
import argparse, concurrent.futures as cf, hashlib, json, os, random, re, sys, time
from pathlib import Path
import requests

CHAINS = {  # oldest -> newest
    "gemini-flash": ["google/gemini-3.6-flash", "google/gemini-3.7-flash", "google/gemini-3.8-flash"],
    "deepseek": ["deepseek/deepseek-chat-v3-0324", "deepseek/deepseek-chat-v3.1", "deepseek/deepseek-v3.2"],
    "llama": ["meta-llama/llama-3.1-70b-instruct", "meta-llama/llama-3.3-70b-instruct"],
}
LABELS = ["refund", "exchange", "complaint", "inquiry"]
NAMES = ["Aria", "Bo", "Chen", "Dara", "Eli", "Fay", "Gus", "Hana", "Ivo", "Jun"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
DEPTHS = [0, 1, 2, 3]


def make_items(n, seed):
    rng = random.Random(seed)
    items = []
    for i in range(n):
        oid = "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(2)) + str(rng.randint(1000, 9999))
        qty, price = rng.randint(2, 9), round(rng.uniform(5, 99), 2)
        m, d, y = rng.randint(1, 12), rng.randint(1, 28), rng.choice([2024, 2025])
        label = rng.choice(LABELS)
        intent = {"refund": "I want my money back for this order.",
                  "exchange": "Please swap it for a different size.",
                  "complaint": "This is the third time it arrived broken and I am furious.",
                  "inquiry": "Could you tell me when it will ship?"}[label]
        text = (f"Hi, this is {rng.choice(NAMES)}. Order {oid} placed on {MONTHS[m-1]} {d}, {y}: "
                f"{qty} units at ${price:.2f} each. {intent}")
        items.append(dict(id=i, text=text, oid=oid, total=round(qty * price, 2), date=f"{y}-{m:02d}-{d:02d}",
                          label=label, qty=qty))
    return items


def prompt(item, depth):
    t = item["text"]
    if depth == 0:
        return None, f"{t}\n\nWhat is the total price of the order?"
    if depth == 1:
        return None, f"{t}\n\nReply with only the total price as a number with two decimals, nothing else."
    if depth == 2:
        return None, (f"{t}\n\nReturn a JSON object with exactly the keys \"order_id\", \"total\" (number), "
                      f"\"label\" (one of {LABELS}). Output only JSON, no code fences.")
    sysmsg = ("You are a ticket parser inside a billing pipeline. Output EXACTLY one line, no other text:\n"
              "TICKET|<ORDER_ID uppercase>|<DATE ISO yyyy-mm-dd>|<TOTAL with exactly 2 decimals, no currency symbol>|"
              f"<LABEL lowercase one of {','.join(LABELS)}>|<QTY integer>\n"
              "Never add explanations, quotes, markdown or trailing spaces.")
    return sysmsg, t


NUM = re.compile(r"-?\d[\d,]*\.?\d*")


def nums(s):
    return [float(x.replace(",", "")) for x in NUM.findall(s) if x.replace(",", "").replace(".", "").isdigit()]


def grade(item, depth, out):
    """returns (strict_ok, content_ok)"""
    out = out or ""
    tot = item["total"]
    close = lambda v: abs(v - tot) < 0.015
    if depth == 0:
        c = any(close(v) for v in nums(out))
        return c, c
    if depth == 1:
        c = any(close(v) for v in nums(out))
        return bool(re.fullmatch(r"\d+\.\d{2}", out.strip())) and close(float(out.strip())), c
    if depth == 2:
        try:
            j = json.loads(out.strip())
            strict = (set(j) == {"order_id", "total", "label"} and j["order_id"] == item["oid"]
                      and isinstance(j["total"], (int, float)) and close(j["total"]) and j["label"] == item["label"])
            return strict, strict
        except Exception:
            c = item["oid"] in out and any(close(v) for v in nums(out)) and item["label"] in out.lower()
            return False, c
    exp = f"TICKET|{item['oid']}|{item['date']}|{item['total']:.2f}|{item['label']}|{item['qty']}"
    c = all(x in out for x in [item["oid"], item["date"], f"{item['total']:.2f}", item["label"]])
    return out == exp, c


class Client:
    def __init__(self, cache, mock):
        self.cache, self.mock = Path(cache), mock
        self.cache.mkdir(parents=True, exist_ok=True)
        self.key = os.environ.get("OPENROUTER_API_KEY")
        if not mock and not self.key:
            sys.exit("OPENROUTER_API_KEY not set (use --mock for a dry run)")
        self.cost = 0.0

    def __call__(self, model, sysmsg, user, max_tokens):
        h = hashlib.sha1(json.dumps([model, sysmsg, user, max_tokens]).encode()).hexdigest()
        f = self.cache / f"{h}.json"
        if f.exists():
            return json.loads(f.read_text())["text"]
        if self.mock:
            return self.mock_reply(model, sysmsg, user)
        msgs = ([{"role": "system", "content": sysmsg}] if sysmsg else []) + [{"role": "user", "content": user}]
        body = dict(model=model, messages=msgs, temperature=0, max_tokens=max_tokens, usage={"include": True})
        for a in range(5):
            try:
                r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, timeout=120,
                                  headers={"Authorization": f"Bearer {self.key}"})
                if r.status_code in (429, 500, 502, 503, 504):
                    raise RuntimeError(r.status_code)
                r.raise_for_status()
                j = r.json()
                text = j["choices"][0]["message"].get("content") or ""
                self.cost += (j.get("usage") or {}).get("cost", 0) or 0
                f.write_text(json.dumps(dict(text=text, model=j.get("model"), id=j.get("id"))))
                return text
            except Exception as e:
                if a == 4:
                    print(f"  fail {model}: {e}", file=sys.stderr)
                    return None
                time.sleep(2 ** a)

    @staticmethod
    def mock_reply(model, sysmsg, user):  # deterministic fake: newer "versions" are chattier at high depth
        m = hash(model) % 7
        oid = re.search(r"Order (\w+)", user).group(1)
        total = None
        q = re.search(r"(\d+) units at \$([\d.]+)", user)
        total = int(q.group(1)) * float(q.group(2))
        lab = next(l for l, k in [("refund", "money back"), ("exchange", "swap"), ("complaint", "furious"),
                                  ("inquiry", "ship")] if k in user)
        if sysmsg:
            return f"TICKET|{oid}|2024-01-01|{total:.2f}|{lab}|{q.group(1)}" + (" " if m % 2 else "")
        if "JSON" in user:
            return ("```json\n" if m % 3 == 0 else "") + json.dumps(dict(order_id=oid, total=total, label=lab))
        return f"The total is ${total:.2f}." if "only" not in user or m % 2 else f"{total:.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chains", nargs="*", default=list(CHAINS))
    ap.add_argument("--models", nargs="*", help="custom chain, oldest->newest (overrides --chains)")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--max-tokens", type=int, default=400)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--out", default="results/openrouter_isr.json")
    a = ap.parse_args()
    chains = {"custom": a.models} if a.models else {k: CHAINS[k] for k in a.chains}
    items = make_items(a.n, a.seed)
    cl = Client("results/or_cache", a.mock)
    res = {}
    for cname, models in chains.items():
        per = {}
        for m in models:
            jobs = [(it, d) for d in DEPTHS for it in items]
            def run(j):
                it, d = j
                s, u = prompt(it, d)
                return grade(it, d, cl(m, s, u, a.max_tokens))
            with cf.ThreadPoolExecutor(1 if a.mock else a.workers) as ex:
                r = list(ex.map(run, jobs))
            per[m] = {d: [r[k] for k, (_, dd) in enumerate(jobs) if dd == d] for d in DEPTHS}
            print(f"{m}: " + " ".join(f"d{d}={sum(x[0] for x in per[m][d])/a.n:.2f}" for d in DEPTHS), flush=True)
        out = dict(models=models, models_stats={}, transitions=[])
        for m in models:
            out["models_stats"][m] = {d: dict(strict=sum(x[0] for x in per[m][d]) / a.n,
                                              content=sum(x[1] for x in per[m][d]) / a.n,
                                              format_fail=sum((not x[0]) and x[1] for x in per[m][d]) / a.n)
                                      for d in DEPTHS}
        for o, nw in zip(models, models[1:]):
            t = {}
            for d in DEPTHS:
                po, pn = per[o][d], per[nw][d]
                reg = sum(x[0] and not y[0] for x, y in zip(po, pn)) / a.n
                fix = sum(y[0] and not x[0] for x, y in zip(po, pn)) / a.n
                creg = sum(x[1] and not y[1] for x, y in zip(po, pn)) / a.n
                t[d] = dict(regression=reg, fix=fix, content_regression=creg)
            out["transitions"].append(dict(old=o, new=nw, by_depth=t))
        res[cname] = out
        print(f"\n[{cname}] regression rate (strict) by depth")
        for tr in out["transitions"]:
            print(f"  {tr['old']} -> {tr['new']}: " + " ".join(
                f"d{d}={tr['by_depth'][d]['regression']:.2f}(content {tr['by_depth'][d]['content_regression']:.2f})"
                for d in DEPTHS))
    Path(a.out).parent.mkdir(exist_ok=True)
    Path(a.out).write_text(json.dumps(dict(args=vars(a), results=res), indent=1))
    print(f"\nsaved {a.out}; spend ${cl.cost:.4f}")


if __name__ == "__main__":
    main()
