"""Recompute LLM kill vectors from the stored generated test files (no new LLM calls) with exact test ids, for modules whose ids were truncated."""
import json, os, random, re, shlex, sys
sys.argv = [sys.argv[0]] + sys.argv[1:]
import mutation_study as S
targets = {"src/humanize/number.py": "humanize", "src/humanize/filesize.py": "humanize", "boltons/strutils.py": "boltons"}
tests = {m: t for tg in json.load(open("targets.json")) for m, t in tg["modules"]}
only = sys.argv[1:] or list(targets)
for mod in only:
    name = targets[mod]; path = f"{S.RES}/{S.key(name, mod)}.json"; st = json.load(open(path))
    R = S.Runner(name, mod, tests[mod]); ms = S.make_mutants(R.orig); random.Random(0).shuffle(ms); ms = ms[:150]
    assert len(ms) == st["n_mutants"], (len(ms), st["n_mutants"])
    for model, M in st["models"].items():
        for k, at in enumerate(M["attempts"]):
            fn = f"test_llm_{re.sub(r'[^a-z0-9]', '', mod.lower())}_{re.sub(r'[^a-z0-9]', '', model.split('/')[-1])}_{k}.py"
            if not os.path.exists(f"{R.base}/{R.tdir}/{fn}"): print("missing", fn); continue
            R.add_test_file(fn, open(f"{R.base}/{R.tdir}/{fn}").read())
            ids, _ = R.passing_ids(fn)
            at["n_pass"] = len(ids); at["killed"] = R.kills(ms, " ".join(shlex.quote(i) for i in ids)) if ids else [False] * len(ms)
            json.dump(st, open(path, "w"))
            print(mod, model.split("/")[-1], k, len(ids), round(sum(at["killed"]) / len(ms), 3), flush=True)
