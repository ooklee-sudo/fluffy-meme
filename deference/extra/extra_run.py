"""Post-main-run additions (E3-mini reasoning on/off, E2 other-vendor tier). Not part of the frozen main run.

Reuses the frozen bank, prompts, system prompt, temperature and parser from run/main_run.py unchanged (imported, not copied).
Every call records the reasoning setting, provider, returned model and token usage.

  python extra/extra_run.py sample                       write extra/sample300.json (stratified, fixed seed)
  python extra/extra_run.py plan                         calls per condition
  python extra/extra_run.py run OUT.jsonl --go [--conditions A,B] [--limit N] [--per-cell N] [--workers 16]
  python extra/extra_run.py export OUT.jsonl OUT.csv     analysis.py input; condition label becomes the model label
"""
import argparse
import concurrent.futures as cf
import csv
import hashlib
import importlib.util
import json
import os
import random
import threading
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BANKDIR = os.path.join(ROOT, "bank", "out")
_spec = importlib.util.spec_from_file_location("main_run", os.path.join(ROOT, "run", "main_run.py"))
M = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(M)

SEED_SAMPLE, SEED_ORDER = 2026102301, 20261023
CAP = 2048  # both conditions of every pair use the long-form limit and the long-form parser
E3_CHANNELS = {("N", ""): 3, ("NEU", ""): 1, ("ST_AGAINST", "pref"): 1, ("ST_AGAINST", "weak"): 1,
               ("ST_AGAINST", "strong"): 1, ("ST_AGAINST", "disclaimer"): 1, ("ACC", "20"): 1, ("ACC", "50"): 1, ("ACC", "80"): 1}
FULL = "full"  # all 21 channels of the main run

# label: (OpenRouter id, family, size_rank, reasoning param: None = not sent, True/False = reasoning.enabled, channel set, item set)
CONDITIONS = {}
# Open hybrids were chosen from a pilot (extra/PILOT.md): Qwen3.5-9B/27B truncate at 2,048 tokens with reasoning on (91% / 9%)
for lab, mid, fam, rank, items in (("Haiku4.5", "anthropic/claude-haiku-4.5", "Claude", 1, "s300"),
                                   ("Qwen3.6-27B", "qwen/qwen3.6-27b", "Qwen3.6", 1, "all"),
                                   ("Qwen3.8-27B", "qwen/qwen3.8-27b", "Qwen3.8", 1, "all")):
    for mode in (False, True):
        CONDITIONS[f"{lab}|{'on' if mode else 'off'}"] = (mid, fam, rank, mode, E3_CHANNELS, items)
# Other-vendor large tier: reasoning cannot be disabled on this endpoint, so it is run once with the endpoint default.
CONDITIONS["Gemini3.1-Pro|default"] = ("google/gemini-3.1-pro-preview", "Gemini", 1, None, FULL, "all")


def sample300(bank):
    """Stratified sample: 50 per domain, tiers proportional to 34/33/33, fixed seed."""
    rnd = random.Random(SEED_SAMPLE); out = []
    by = defaultdict(list)
    for it in bank.values():
        by[(it["domain"], it["tier"])].append(it["item_id"])
    for dom in sorted({d for d, _ in by}):
        tiers = sorted(t for d, t in by if d == dom)
        quota = {t: 17 for t in tiers}; quota[rnd.choice(tiers)] = 16  # 17+17+16 = 50, which tier gets 16 is random
        for t in tiers:
            out += rnd.sample(sorted(by[(dom, t)]), quota[t])
    return sorted(out)


def load_sample():
    return json.load(open(os.path.join(HERE, "sample300.json")))["item_ids"]


def jobs_for(prompts, conds):
    s300 = set(load_sample()) if any(CONDITIONS[c][5] == "s300" for c in conds) else set()
    jobs = []
    for c in conds:
        _, _, _, _, chans, items = CONDITIONS[c]
        for p in prompts:
            if items == "s300" and p["item_id"] not in s300:
                continue
            if chans == FULL:
                reps = M.N_REPS if p["channel"] == "N" else 1
            elif (p["channel"], p["level"]) in chans and p["rot"] == 0:
                reps = chans[(p["channel"], p["level"])]
            else:
                continue
            jobs += [(c, p, r) for r in range(reps)]
    return jobs


def jkey(c, p, rep):
    return f'{c}|{p["item_id"]}|{p["channel"]}|{p["level"]}|{p["rot"]}|{rep}'


def call(mid, text, reasoning):
    body = {"model": mid, "messages": [{"role": "system", "content": M.SYSTEM}, {"role": "user", "content": text}],
            "max_tokens": CAP, "temperature": M.TEMPERATURE}
    if reasoning is not None:
        body["reasoning"] = {"enabled": reasoning}
    last = None
    for attempt in range(5):
        try:
            req = urllib.request.Request(M.URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=240) as r:
                j = json.load(r)
            ch = (j.get("choices") or [{}])[0]; msg = ch.get("message") or {}; u = j.get("usage") or {}
            return dict(raw=msg.get("content") or "", served_by=j.get("provider"), returned_model=j.get("model"), finish_reason=ch.get("finish_reason"),
                        reasoning_present=bool(msg.get("reasoning") or msg.get("reasoning_details")),
                        reasoning_tokens=(u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
                        completion_tokens=u.get("completion_tokens"), prompt_tokens=u.get("prompt_tokens"), cost=u.get("cost"), error=None)
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: " + e.read()[:200].decode(errors="ignore")
            if e.code in (400, 401, 403, 404):
                break
        except Exception as e:  # noqa: BLE001
            last = str(e)[:200]
        time.sleep(2 ** (attempt + 1))
    return dict(raw="", served_by=None, returned_model=None, finish_reason=None, reasoning_present=None, reasoning_tokens=None,
                completion_tokens=None, prompt_tokens=None, cost=None, error=last)


def cmd_sample(a):
    bank = {i["item_id"]: i for i in json.load(open(os.path.join(BANKDIR, "bank.json")))}
    ids = sample300(bank)
    cnt = Counter((bank[i]["domain"], bank[i]["tier"]) for i in ids)
    json.dump(dict(seed=SEED_SAMPLE, n=len(ids), item_ids=ids), open(os.path.join(HERE, "sample300.json"), "w"), indent=1)
    print(len(ids), "items;", dict(Counter(bank[i]["domain"] for i in ids)), "per domain; tiers", dict(Counter(bank[i]["tier"] for i in ids)))


def cmd_plan(a):
    man, bank, prompts = M.load_bank(BANKDIR)
    for c in CONDITIONS:
        print(f"{c:28s} {len(jobs_for(prompts, [c])):6d} calls  reasoning={CONDITIONS[c][3]}  items={CONDITIONS[c][5]}")
    print("total", len(jobs_for(prompts, list(CONDITIONS))))


def cmd_run(a):
    man, bank, prompts = M.load_bank(BANKDIR)
    conds = a.conditions.split(",") if a.conditions else list(CONDITIONS)
    jobs = jobs_for(prompts, conds)
    random.Random(SEED_ORDER).shuffle(jobs)
    if a.per_cell:  # pilot: first N jobs per condition after the fixed shuffle
        seen = Counter(); keep = []
        for j in jobs:
            if seen[j[0]] < a.per_cell:
                keep.append(j); seen[j[0]] += 1
        jobs = keep
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
    f = open(a.out, "a")

    def work(job):
        c, p, rep = job
        mid, fam, rank, reasoning, _, _ = CONDITIONS[c]
        res = call(mid, p["text"], reasoning)
        L, br = M.parse(res["raw"], True)
        row = dict(key=jkey(c, p, rep), model=c, base_model=c.split("|")[0], family=fam, size_rank=rank, reasoning_setting=reasoning,
                   item_id=p["item_id"], domain=bank[p["item_id"]]["domain"], tier=bank[p["item_id"]]["tier"], channel=p["channel"], level=p["level"],
                   rot=p["rot"], rep=rep, letter=L, parser_branch=br, role=p["roles"][L] if L else "missing", max_tokens=CAP,
                   temperature_sent=True, ts=int(time.time()), **res)
        with lock:
            f.write(json.dumps(row) + "\n"); f.flush(); n_done[0] += 1
            if n_done[0] % 500 == 0:
                print(n_done[0], "/", len(jobs), flush=True)

    with cf.ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(work, jobs))
    f.close(); print("done")


def cmd_export(a):
    rows = [json.loads(l) for l in open(a.results)]
    cols = ["model", "family", "size_rank", "item_id", "domain", "tier", "channel", "level", "rep", "role"]
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols)
        for r in rows:
            w.writerow([r[c] for c in cols])
    print(len(rows), "rows ->", a.out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sample"); sub.add_parser("plan")
    s = sub.add_parser("run"); s.add_argument("out"); s.add_argument("--go", action="store_true"); s.add_argument("--conditions")
    s.add_argument("--limit", type=int); s.add_argument("--per-cell", type=int); s.add_argument("--workers", type=int, default=16)
    s.add_argument("--retry-errors", action="store_true")
    s = sub.add_parser("export"); s.add_argument("results"); s.add_argument("out")
    a = ap.parse_args()
    {"sample": cmd_sample, "plan": cmd_plan, "run": cmd_run, "export": cmd_export}[a.cmd](a)
