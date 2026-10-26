"""Blind-testing study on real faults (BugsInPy). For each valid bug and model, K independent attempts:
the model sees only the buggy version of the source files that the fix touches (no issue text, no hint that a bug exists)
and writes pytest tests. Detection = a test fails on the buggy version (not an import/name error) and passes on the fixed version.
Reach A(K) = share of valid bugs detected within K attempts (the pool is faults humans found and fixed, so human reach is 1 by construction).

python3 bip_study.py run --models M1,M2 --k 6 --cap-usd 60 [--shard i/n]
python3 bip_study.py report --k 6
"""
import argparse, json, os, re, sys, time, urllib.request
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mut"))
from mutation_pilot import clean_code
import bip_lib as B

W = B.W; RES = f"{W}/study_results"; LEDGER = f"{W}/spend.json"; os.makedirs(RES, exist_ok=True)
VALID = os.path.join(B.HERE, "valid_bugs.json")


def spend(): return json.load(open(LEDGER))["total"] if os.path.exists(LEDGER) else 0.0
def add_spend(x, tag):
    d = json.load(open(LEDGER)) if os.path.exists(LEDGER) else {"total": 0.0, "by": {}}
    d["total"] += x; d["by"][tag] = d["by"].get(tag, 0.0) + x; json.dump(d, open(LEDGER, "w"), indent=1)


def chat(model, prompt, cap):
    for attempt in range(3):
        if spend() >= cap: raise SystemExit(f"spend cap reached: ${spend():.2f}")
        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 16000,
                             "reasoning": {"effort": "low"}, "temperature": 0.8}).encode(),
            headers={"Content-Type": "application/json", **({"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]} if os.environ.get("OPENROUTER_API_KEY") else {})})
        try: j = json.load(urllib.request.urlopen(req, timeout=900))
        except Exception as e: print("   api error:", str(e)[:80], flush=True); time.sleep(5 * (attempt + 1)); continue
        add_spend(j.get("usage", {}).get("cost") or 0.0, model)
        t = j["choices"][0]["message"].get("content")
        if t: return t
    return ""


def source_files(kv):
    files = re.findall(r"(?m)^diff --git a/(\S+) b/\S+", B.patch_text(kv))
    return [f for f in files if f.endswith(".py") and "test" not in f.lower()]


def judge(before, after):
    det = [t for t, (oc, exc) in before.items() if oc == "failed" and not exc.startswith(B.SUSPECT) and after.get(t, ("", ""))[0] == "passed"]
    return det


def run_bug(key, models, k, cap):
    project, bug = key.split("/"); path = f"{RES}/{project}_{bug}.json"
    st = json.load(open(path)) if os.path.exists(path) else {"bug": key, "models": {}}
    wt, py, kv = B.prepare(project, bug); B.revert(wt)
    srcs = source_files(kv)
    code = "\n\n".join(f"# file: {f}\n{open(f'{wt}/{f}').read()[:40000]}" for f in srcs if os.path.exists(f"{wt}/{f}"))
    if not code: return
    prompt = (f"Below are source files from the Python project `{project}`. Write a thorough pytest test file for them. Test the behaviour "
              f"of the public functions and classes, including edge cases. Use only absolute imports of the project's modules. Keep it under 250 lines. "
              f"Output only one python code block.\n\n```python\n{code}\n```")
    os.makedirs(f"{wt}/llm_tests", exist_ok=True)
    for model in models:
        M = st["models"].setdefault(model, {"attempts": []})
        for i in range(len(M["attempts"]), k):
            text = chat(model, prompt, cap); src = clean_code(text) if text else ""
            fn = f"llm_tests/test_llm_{re.sub(r'[^a-z0-9]', '', model.split('/')[-1])}_{i}.py"
            B.revert(wt); os.makedirs(f"{wt}/llm_tests", exist_ok=True); open(f"{wt}/{fn}", "w").write(src)
            before, _ = B.run_pytest_xml(wt, py, fn)
            ok, o = B.apply_fix(wt, kv, "fix"); after, _ = B.run_pytest_xml(wt, py, fn) if ok else ({}, "")
            B.revert(wt)
            det = judge(before, after) if ok else []
            M["attempts"].append({"n_tests": len(before), "n_fail_buggy": sum(v[0] == "failed" for v in before.values()),
                                  "detected": bool(det), "tests": det[:3]})
            json.dump(st, open(path, "w"))
            print(f"{key} {model.split('/')[-1]} k={i}: tests={len(before)} failing_on_buggy={M['attempts'][-1]['n_fail_buggy']} detected={bool(det)}; spend ${spend():.2f}", flush=True)


def run(a):
    valid = [k for k, v in json.load(open(VALID)).items() if v["valid"]]
    si, sn = (int(x) for x in a.shard.split("/"))
    for n, key in enumerate(valid):
        if n % sn != si or (a.only and a.only != key): continue
        try: run_bug(key, a.models.split(","), a.k, a.cap_usd)
        except SystemExit: raise
        except Exception as e: print(key, "ERROR", str(e)[:150], flush=True)


def report(a):
    import glob
    data = [json.load(open(p)) for p in sorted(glob.glob(f"{RES}/*.json"))]
    rng = np.random.default_rng(0); models = sorted({m for d in data for m in d["models"]})
    print(f"{len(data)} bugs with results; spend ${spend():.2f}")
    for m in models:
        for K in range(1, a.k + 1):
            D = [any(x["detected"] for x in d["models"][m]["attempts"][:K]) for d in data if m in d["models"] and len(d["models"][m]["attempts"]) >= K]
            if not D: continue
            D = np.array(D); n = len(D); bs = [D[rng.integers(0, n, n)].mean() for _ in range(2000)]
            print(f"{m:34s} K={K}: A = {D.mean():.2f} (95% CI {np.percentile(bs,2.5):.2f}-{np.percentile(bs,97.5):.2f}), n={n} bugs")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run"); r.add_argument("--models", default="anthropic/claude-haiku-5.5"); r.add_argument("--k", type=int, default=6)
    r.add_argument("--cap-usd", type=float, default=60.0); r.add_argument("--shard", default="0/1"); r.add_argument("--only", default="")
    p = sp.add_parser("report"); p.add_argument("--k", type=int, default=6)
    a = ap.parse_args(); {"run": run, "report": report}[a.cmd](a)
