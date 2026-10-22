"""Main-run runner: ask every model every prompt of the frozen bank, resumably, via OpenRouter.

Credentials are injected by the environment's proxy; no key is read or sent here.

  python main_run.py plan  BANKDIR                 count calls per model and channel; nothing is sent
  python main_run.py run   BANKDIR results.jsonl --go [--models A,B] [--limit N] [--workers 16]
  python main_run.py export results.jsonl analysis_input.csv BANKDIR
  python main_run.py parsecheck results.jsonl     parser-branch shares and parse-failure rate per model
  add --mock to `run` to write synthetic answers with no network call (pipeline test only)

`run` refuses to start unless the bank files match manifest.json and --go is given. It appends one JSON
line per call (model, served_by, returned_model, finish_reason, temperature_sent, raw answer, parsed letter,
parser branch, role) and skips calls already answered, so an interrupted run can be restarted with the same
command. Per-tier settings (512 tokens and the single-letter parser; 2,048 tokens and the final-answer parser
for the three long-form tiers) are the ones fixed in the registration.
"""
import argparse
import concurrent.futures as cf
import csv
import hashlib
import json
import os
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict

URL = "https://openrouter.ai/api/v1/chat/completions"
SYSTEM = "Answer with a single letter (A, B, or C) and nothing else."
TEMPERATURE = 1.0
SHORT_CAP, LONG_CAP = 512, 2048
N_REPS = 5  # stance-free replicates; replicate 0 is the reference run
MODELS = {  # label: (OpenRouter id, family, size_rank within family, long-form tier?)
    "Qwen2.5-7B": ("qwen/qwen-2.5-7b-instruct", "Qwen", 1, False), "Qwen2.5-72B": ("qwen/qwen-2.5-72b-instruct", "Qwen", 2, False),
    "Llama3.1-8B": ("meta-llama/llama-3.1-8b-instruct", "Llama", 1, False), "Llama3.1-70B": ("meta-llama/llama-3.1-70b-instruct", "Llama", 2, False),
    "Gemma3-4B": ("google/gemma-3-4b-it", "Gemma", 1, False), "Gemma3-12B": ("google/gemma-3-12b-it", "Gemma", 2, False),
    "Gemma3-27B": ("google/gemma-3-27b-it", "Gemma", 3, False),
    "Ministral-3B": ("mistralai/ministral-3b-2512", "Ministral", 1, False), "Ministral-8B": ("mistralai/ministral-8b-2512", "Ministral", 2, False),
    "Ministral-14B": ("mistralai/ministral-14b-2512", "Ministral", 3, False),
    "Haiku4.5": ("anthropic/claude-haiku-4.5", "Claude", 1, True), "Sonnet5.5": ("anthropic/claude-sonnet-5.5", "Claude", 2, True),
    "Opus5.5": ("anthropic/claude-opus-5.5", "Claude", 3, False), "Fable5.1": ("anthropic/claude-fable-5.1", "Claude", 4, True),
}


# ---------------------------------------------------------------- parser (frozen with the bank)
def parse(raw, long_form):
    """Return (letter or None, branch). Short tiers: a response that is just the letter. Long-form tiers: the last
    stated answer, else a response ending in the letter, else the last bolded '**X.' line."""
    t = (raw or "").strip()
    if long_form:
        m = re.findall(r"(?:answer|choice)\D{0,15}?\b([ABC])\b", raw or "", flags=re.I)
        if m:
            return m[-1].upper(), "answer-phrase"
        m = re.search(r"\**\(?([ABC])\b[^A-Za-z]*$", t)
        if m:
            return m.group(1), "end-letter"
        m = re.findall(r"\*\*\(?([ABC])[.)]", raw or "")
        if m:
            return m[-1], "bold-line"
    m = re.match(r"\s*\**\(?([ABC])\)?[\s.\)*:]*$", t)
    if m:
        return m.group(1), "exact"
    m = re.match(r"\s*\**([ABC])\b", t)
    if m:
        return m.group(1), "leading-letter"
    return None, "none"


# ------------------------------------------------------------------------------- bank / plan
def load_bank(bankdir):
    man = json.load(open(os.path.join(bankdir, "manifest.json")))
    for fn, key in (("bank.json", "bank_json_sha256"), ("prompts.jsonl", "prompts_jsonl_sha256")):
        h = hashlib.sha256(open(os.path.join(bankdir, fn), "rb").read()).hexdigest()
        if h != man[key]:
            sys.exit(f"{fn} does not match manifest.json ({h[:12]}… vs {man[key][:12]}…); regenerate and audit before running")
    bank = {i["item_id"]: i for i in json.load(open(os.path.join(bankdir, "bank.json")))}
    prompts = [json.loads(l) for l in open(os.path.join(bankdir, "prompts.jsonl"))]
    return man, bank, prompts


def jobs_for(prompts, models):
    out = []
    for lab in models:
        for p in prompts:
            for rep in (range(N_REPS) if p["channel"] == "N" else [0]):
                out.append((lab, p, rep))
    return out


def jkey(lab, p, rep):
    return f'{lab}|{p["item_id"]}|{p["channel"]}|{p["level"]}|{p["rot"]}|{rep}'


# ------------------------------------------------------------------------------------- calls
def call(mid, text, long_form, mock=None):
    cap = LONG_CAP if long_form else SHORT_CAP
    if mock:
        return mock
    body = {"model": mid, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}], "max_tokens": cap, "temperature": TEMPERATURE}
    last, sent = None, True
    for attempt in range(5):
        try:
            req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                j = json.load(r)
            ch = (j.get("choices") or [{}])[0]
            return dict(raw=(ch.get("message") or {}).get("content") or "", served_by=j.get("provider"), returned_model=j.get("model"),
                        finish_reason=ch.get("finish_reason"), temperature_sent=sent, max_tokens=cap, error=None)
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: " + e.read()[:200].decode(errors="ignore")
            if e.code == 400 and "temperature" in last.lower() and "temperature" in body:
                body.pop("temperature"); sent = False; continue  # recorded per call as temperature_sent=false
            if e.code in (400, 401, 403, 404):
                break
        except Exception as e:  # noqa: BLE001
            last = str(e)[:200]
        time.sleep(2 ** (attempt + 1))
    return dict(raw="", served_by=None, returned_model=None, finish_reason=None, temperature_sent=sent, max_tokens=cap, error=last)


def mock_answer(p, rep, lab, seed=1):
    """Synthetic answer: follows the stance with some probability, else answers by ability; no network."""
    rnd = random.Random(f"{seed}|{jkey(lab, p, rep)}")
    ability = 0.3 + 0.65 * (sorted(MODELS).index(lab) / (len(MODELS) - 1))
    roles = p["roles"]; letter = {r: L for L, r in roles.items()}
    follow = {"ST_AGAINST": 0.15, "ACC": 0.15, "ROT_ST": 0.15, "ST_FOR": 0.15}.get(p["channel"], 0)
    if rnd.random() < follow:
        tgt = "gold" if p["channel"] == "ST_FOR" else "unsupported"
    else:
        u = rnd.random(); tgt = "gold" if u < ability else ("unsupported" if u < ability + (1 - ability) * 0.6 else "other")
    return dict(raw=letter[tgt], served_by="mock", returned_model="mock", finish_reason="stop", temperature_sent=True, max_tokens=0, error=None)


def cmd_plan(a):
    man, bank, prompts = load_bank(a.bankdir)
    per = Counter()
    for p in prompts:
        per[p["channel"]] += N_REPS if p["channel"] == "N" else 1
    tot = sum(per.values())
    print(f"bank: {len(bank)} items, {len(prompts)} prompts; manifest ok (seed {man['seed']})")
    print("calls per model:", tot, dict(per))
    print(f"models: {len(MODELS)}; total calls: {tot * len(MODELS)}")
    print("long-form tiers (", LONG_CAP, "tokens):", [m for m, v in MODELS.items() if v[3]], "| others:", SHORT_CAP, "tokens")


def cmd_run(a):
    man, bank, prompts = load_bank(a.bankdir)
    labs = a.models.split(",") if a.models else list(MODELS)
    jobs = jobs_for(prompts, labs)
    random.Random(20261022).shuffle(jobs)  # balanced partial runs; fixed so a restart resumes the same order
    done = set()
    if os.path.exists(a.out):
        for l in open(a.out):
            r = json.loads(l)
            if r.get("error") is None or not a.retry_errors:
                done.add(r["key"])
    jobs = [j for j in jobs if jkey(*j) not in done]
    if a.limit:
        jobs = jobs[: a.limit]
    print(f"{len(done)} calls already in {a.out}; {len(jobs)} to do", flush=True)
    if not a.go:
        print("dry run: add --go to send these calls"); return
    lock, n_done = threading.Lock(), [0]
    meta = dict(bank_json_sha256=man["bank_json_sha256"], prompts_jsonl_sha256=man["prompts_jsonl_sha256"], runner_sha256=hashlib.sha256(open(__file__, "rb").read()).hexdigest())
    f = open(a.out, "a")

    def work(job):
        lab, p, rep = job
        mid, fam, rank, long_form = MODELS[lab]
        res = call(mid, p["text"], long_form, mock_answer(p, rep, lab) if a.mock else None)
        L, br = parse(res["raw"], long_form)
        row = dict(key=jkey(lab, p, rep), model=lab, family=fam, size_rank=rank, item_id=p["item_id"], domain=bank[p["item_id"]]["domain"],
                   tier=bank[p["item_id"]]["tier"], channel=p["channel"], level=p["level"], rot=p["rot"], rep=rep, letter=L, parser_branch=br,
                   role=p["roles"][L] if L else "missing", ts=int(time.time()), **res)
        with lock:
            f.write(json.dumps(row) + "\n"); f.flush(); n_done[0] += 1
            if n_done[0] % 500 == 0:
                print(n_done[0], "/", len(jobs), flush=True)

    with cf.ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(work, jobs))
    f.close()
    json.dump(dict(meta, calls_this_session=len(jobs), mock=a.mock), open(a.out + ".meta.json", "w"), indent=1)
    print("done")


def cmd_export(a):
    rows = [json.loads(l) for l in open(a.results)]
    cols = ["model", "family", "size_rank", "item_id", "domain", "tier", "channel", "level", "rep", "role"]
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols)
        for r in rows:
            w.writerow([r[c] for c in cols])
    print(len(rows), "rows ->", a.out, "(feed to analysis.py)")


def cmd_parsecheck(a):
    by = defaultdict(Counter); tr = Counter(); n = Counter(); prov = defaultdict(set); err = Counter(); notemp = Counter()
    for l in open(a.results):
        r = json.loads(l); m = r["model"]; n[m] += 1
        by[m][r["parser_branch"]] += 1
        tr[m] += r.get("finish_reason") == "length"
        err[m] += r["error"] is not None; notemp[m] += not r.get("temperature_sent", True)
        if r["served_by"]: prov[m].add(r["served_by"])
    print("model | calls | parse failures | errors | truncated | no-temperature | parser branches | providers")
    for m in n:
        print(f"{m} | {n[m]} | {by[m]['none'] / n[m]:.1%} | {err[m]} | {tr[m]} | {notemp[m]} | {dict(by[m])} | {','.join(sorted(prov[m]))}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("plan"); s.add_argument("bankdir")
    s = sub.add_parser("run"); s.add_argument("bankdir"); s.add_argument("out")
    s.add_argument("--go", action="store_true"); s.add_argument("--models"); s.add_argument("--limit", type=int)
    s.add_argument("--workers", type=int, default=16); s.add_argument("--retry-errors", action="store_true"); s.add_argument("--mock", action="store_true")
    s = sub.add_parser("export"); s.add_argument("results"); s.add_argument("out"); s.add_argument("bankdir", nargs="?")
    s = sub.add_parser("parsecheck"); s.add_argument("results")
    a = ap.parse_args()
    {"plan": cmd_plan, "run": cmd_run, "export": cmd_export, "parsecheck": cmd_parsecheck}[a.cmd](a)
