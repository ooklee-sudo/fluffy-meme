"""Multi-module, multi-model mutation study of tool reach vs the human baseline (existing tests).

For each target module:  mutants (cap per module) -> human kill vector (existing tests) ->
for each model and attempt k: LLM writes pytest tests from the module source -> keep tests that pass on the original ->
kill vector. Results are stored per (module, model) in work/results/*.json and a running spend ledger enforces a hard cap.

python3 mutation_study.py run --models anthropic/claude-haiku-5.5,deepseek/deepseek-v4.1-flash,anthropic/claude-sonnet-5.5 \
        --k 8 --max-mutants 150 --cap-usd 150 [--only toolz/itertoolz.py]
python3 mutation_study.py report
Resumable: finished (module, model, attempt) triples are skipped. Spend is logged in work/spend.json.
"""
import argparse, json, os, re, shutil, shlex, sys, subprocess, random, urllib.request, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mut"))
from mutation_pilot import make_mutants, clean_code          # operators and code extraction are shared with the pilot

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, "work"); RES = os.path.join(W, "results"); LEDGER = os.path.join(W, "spend.json")
os.makedirs(RES, exist_ok=True)


def sh(c, cwd=None, t=900):
    r = subprocess.run(c, shell=True, cwd=cwd, capture_output=True, text=True, timeout=t); return r.returncode, r.stdout + r.stderr


def spend():
    return json.load(open(LEDGER))["total"] if os.path.exists(LEDGER) else 0.0


def add_spend(x, tag):
    d = json.load(open(LEDGER)) if os.path.exists(LEDGER) else {"total": 0.0, "by": {}}
    d["total"] += x; d["by"][tag] = d["by"].get(tag, 0.0) + x
    json.dump(d, open(LEDGER, "w"), indent=1)


def chat(model, prompt, cap):
    for attempt in range(3):
        if spend() >= cap:
            raise SystemExit(f"spend cap reached: ${spend():.2f}")
        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 16000,
                             "reasoning": {"effort": "low"}, "temperature": 0.8}).encode(),
            headers={"Content-Type": "application/json",
                     **({"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]} if os.environ.get("OPENROUTER_API_KEY") else {})})
        try:
            j = json.load(urllib.request.urlopen(req, timeout=900))
        except Exception as e:
            print("   api error:", str(e)[:80]); time.sleep(5 * (attempt + 1)); continue
        add_spend(j.get("usage", {}).get("cost") or 0.0, model)
        text = j["choices"][0]["message"].get("content")
        if text:
            return text
        print("   empty content, finish_reason=", j["choices"][0].get("finish_reason"))
    return ""


class Runner:
    """Persistent per-worker copies of a repo so mutants can be swapped in quickly."""
    def __init__(self, name, mod, test, workers=4):
        self.d = f"{W}/{name}"; self.base = f"{self.d}/repo"; self.mod, self.test = mod, test
        self.tdir = os.path.dirname(test); self.workers = workers
        self.py = f"{self.d}/venv/bin/python"; self.orig = open(f"{self.base}/{mod}").read()
        self.copies = []
        for w in range(workers):
            p = f"{self.d}/copy_{os.getpid()}_{w}"
            if os.path.exists(p): shutil.rmtree(p)
            shutil.copytree(self.base, p); self.copies.append(p)

    def pytest(self, cwd, args, timeout=60):
        try:
            env = dict(os.environ, PYTHONPATH=f"{cwd}/src:{cwd}")   # src-layout repos must import the mutated copy, not the editable install
            r = subprocess.run(f"{self.py} -m pytest -x -q --no-header --color=no -p no:cacheprovider {args}", shell=True, cwd=cwd,
                               capture_output=True, text=True, timeout=timeout, env=env); return r.returncode
        except subprocess.TimeoutExpired:
            return 124

    def kills(self, mutants, target_args):
        out = [None] * len(mutants)
        def worker(w):
            p = self.copies[w]
            for i in range(w, len(mutants), self.workers):
                open(f"{p}/{self.mod}", "w").write(mutants[i][1]); out[i] = self.pytest(p, target_args) != 0
            open(f"{p}/{self.mod}", "w").write(self.orig)
        with ThreadPoolExecutor(self.workers) as ex: list(ex.map(worker, range(self.workers)))
        return out

    def add_test_file(self, fn, code):
        for p in [self.base] + self.copies:
            open(f"{p}/{self.tdir}/{fn}", "w").write(code)

    def passing_ids(self, fn):
        """Exact node ids of tests that pass on the original module, read from JUnit XML (ids may contain spaces)."""
        import xml.etree.ElementTree as ET
        env = dict(os.environ, PYTHONPATH=f"{self.base}/src:{self.base}"); x = f"{self.d}/junit_{os.getpid()}.xml"
        try:
            r = subprocess.run(f"{self.py} -m pytest -q --no-header --color=no -p no:cacheprovider --tb=no --junitxml={x} {self.tdir}/{fn}", shell=True,
                               cwd=self.base, capture_output=True, text=True, timeout=300, env=env)
        except subprocess.TimeoutExpired:      # a generated test hangs (e.g. an infinite generator): the attempt counts as having no usable tests
            return [], "timeout"
        ids = []
        try:
            for tc in ET.parse(x).getroot().iter("testcase"):
                if not any(c.tag in ("failure", "error", "skipped") for c in tc):
                    cls = tc.get("classname", ""); parts = cls.split(".")
                    path = f"{self.tdir}/{fn}"; inner = [p for p in parts if p and p not in (self.tdir.replace("/", ".").split(".") + [fn[:-3]])]
                    ids.append("::".join([path] + inner + [tc.get("name")]))
        except Exception: pass
        return ids, r.stdout[-300:]


def key(name, mod): return f"{name}__{mod.replace('/', '_')}"


def run(a):
    models = a.models.split(",")
    si, sn = (int(x) for x in a.shard.split("/"))
    flat = [(tg, m) for tg in json.load(open(a.targets)) for m in tg["modules"]]
    for idx, (tg, (mod, test)) in enumerate(flat):
        if True:
            if idx % sn != si: continue
            if a.only and a.only != mod: continue
            if not os.path.exists(f"{W}/{tg['name']}/venv"):
                print("skip (not set up):", tg["name"]); continue
            k_ = key(tg["name"], mod); path = f"{RES}/{k_}.json"
            st = json.load(open(path)) if os.path.exists(path) else {"module": mod, "repo": tg["name"], "models": {}}
            R = Runner(tg["name"], mod, test)
            src = R.orig
            ms = make_mutants(src); random.Random(0).shuffle(ms); ms = ms[: a.max_mutants]
            if "human" not in st:
                st["human"] = R.kills(ms, test); st["n_mutants"] = len(ms)
                print(f"{tg['name']}/{mod}: {len(ms)} mutants, human kill {sum(st['human'])/len(ms):.3f}", flush=True)
                json.dump(st, open(path, "w"))
            modname = re.sub(r"^src/", "", mod)[:-3].replace("/", ".")
            if modname.endswith(".__init__"): modname = modname[:-9]
            prompt = (f"Below is the source of the Python module `{modname}`. Write a thorough pytest test file for it. Test the "
                      f"behaviour of its public functions, including edge cases. Import from `{modname}`. Keep it under 250 lines. "
                      f"Output only one python code block.\n\n```python\n{src}\n```")
            for model in models:
                M = st["models"].setdefault(model, {"attempts": []})
                for k in range(len(M["attempts"]), a.k):
                    text = chat(model, prompt, a.cap_usd)
                    fn = f"test_llm_{re.sub(r'[^a-z0-9]', '', mod.lower())}_{re.sub(r'[^a-z0-9]', '', model.split('/')[-1])}_{k}.py"
                    code = clean_code(text) if text else ""
                    R.add_test_file(fn, code)
                    ids, tail = R.passing_ids(fn) if code else ([], "")
                    killed = R.kills(ms, " ".join(shlex.quote(i) for i in ids)) if ids else [False] * len(ms)
                    M["attempts"].append({"n_pass": len(ids), "killed": killed})
                    json.dump(st, open(path, "w"))
                    print(f"  {model} k={k}: {len(ids)} tests pass, kill {sum(killed)/len(ms):.3f}; spend ${spend():.2f}", flush=True)


def report(a):
    import numpy as np, glob, csv
    rows = []; rng = np.random.default_rng(0)
    data = [json.load(open(p)) for p in sorted(glob.glob(f"{RES}/*.json"))]
    models = sorted({m for d in data for m in d["models"]})
    print(f"{len(data)} modules; total spend ${spend():.2f}")
    for m in models:
        for Kmax in range(1, a.k + 1):
            H, T = [], []
            for d in data:
                at = d["models"].get(m, {}).get("attempts", [])
                if len(at) < Kmax or "human" not in d: continue
                h = np.array(d["human"], bool); t = np.any([np.array(x["killed"], bool) for x in at[:Kmax]], axis=0)
                H.append(h); T.append(t)
            if not H: continue
            # module-level ratio, then average across modules (each module counts once); bootstrap over modules
            def ratio(idx, either):
                num = den = 0
                rs = []
                for i in idx:
                    h, t = H[i], T[i]; mask = (h | t) if either else np.ones(len(h), bool)
                    if h[mask].sum() > 0: rs.append(t[mask].mean() / h[mask].mean())
                return np.mean(rs)
            n = len(H); idx = np.arange(n)
            for either in (False, True):
                est = ratio(idx, either); bs = [ratio(rng.integers(0, n, n), either) for _ in range(2000)]
                rows.append(dict(model=m, K=Kmax, denominator="killed by either side" if either else "all mutants", modules=n,
                                 A=round(est, 3), lo=round(np.percentile(bs, 2.5), 3), hi=round(np.percentile(bs, 97.5), 3)))
    for r in rows: print(r)
    with open(os.path.join(HERE, "study_summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run"); r.add_argument("--targets", default=os.path.join(HERE, "targets.json"))
    r.add_argument("--models", default="anthropic/claude-haiku-5.5"); r.add_argument("--k", type=int, default=8)
    r.add_argument("--max-mutants", type=int, default=150); r.add_argument("--cap-usd", type=float, default=150.0)
    r.add_argument("--only", default=""); r.add_argument("--shard", default="0/1", help="i/n: run every n-th module")
    p = sp.add_parser("report"); p.add_argument("--k", type=int, default=8)
    a = ap.parse_args(); {"run": run, "report": report}[a.cmd](a)
