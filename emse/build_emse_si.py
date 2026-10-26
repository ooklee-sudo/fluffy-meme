"""EMSE supplementary material: per-module mutation table, per-project and per-bug real-fault tables, prompts, procedures."""
import sys, json, glob, re
sys.path.insert(0, "/home/user/fluffy-meme/isr_submission/manuscript_build")
from docbuild import *
import pandas as pd, numpy as np
R = json.load(open("../reach_pilot/emse_results.json")); M = pd.read_csv("../reach_pilot/emse_mutation_modules.csv")
MS = [("anthropic/claude-haiku-5.5", "Claude Haiku 5.5"), ("anthropic/claude-sonnet-5.5", "Claude Sonnet 5.5"), ("deepseek/deepseek-v4.1-flash", "DeepSeek V4.1 Flash")]
SH = {"Claude Haiku 5.5": "Haiku", "Claude Sonnet 5.5": "Sonnet", "DeepSeek V4.1 Flash": "DeepSeek"}
bugs = [json.load(open(p)) for p in sorted(glob.glob("../reach_pilot/bugsinpy/results_snapshot/*_*.json")) if "spend" not in p and "valid" not in p]
f2 = lambda x: f"{x:.2f}"
d = new_doc(spacing=1.15, running="Supplementary material")
TITLE(d, "Supplementary material", size=15)
P(d, "Mutants overstate what LLM-written unit tests can find: reach on mutants and on real faults  ·  Ook Lee", indent=False, align="center", size=10, italic=True, after=8)
P(d, "Contents: S1 Per-module mutation results · S2 Reach on mutants by number of attempts · S3 Per-project real-fault results · S4 Per-bug results · S5 Prompts · S6 Procedures, environment and cost.", indent=False, size=9, after=6)
# S1
H1(d, "S1 Per-module mutation results")
rows = [["Project", "Module", "Mutants", "Existing tests kill"] + [f"{SH[ml]} K=1 / K=8" for _, ml in MS] + ["In main analysis"]]
for r in M.sort_values(["project", "module"]).itertuples():
    rd = r._asdict()
    rows.append([r.project, r.module, str(r.n), f2(r.human)] + [f"{rd[f'_{5 + 4*i}']:.2f} / {rd[f'_{6 + 4*i}']:.2f}" if False else "" for i in range(3)] + ["yes" if r.n >= 30 else "no (< 30 mutants)"])
# fill model columns explicitly (namedtuple renames columns with '|')
for i, r in enumerate(M.sort_values(["project", "module"]).to_dict("records"), 1):
    for j, (_, ml) in enumerate(MS):
        rows[i][4 + j] = f"{r[f'{ml}|K1']:.2f} / {r[f'{ml}|K8']:.2f}"
TABLE(d, "**Table S1 Mutants and kill rates per module.** Kill rate = share of all mutants killed. Modules with fewer than 30 mutants are shown but excluded from the reach estimates in the main text.", rows, widths=[0.9, 1.6, 0.6, 0.8, 0.9, 0.9, 0.9, 0.9], size=7.5)
rows = [["Module"] + [f"{SH[ml]}: LLM-only share" for _, ml in MS]]
for r in M[M.n >= 30].sort_values("module").to_dict("records"):
    rows.append([r["module"]] + [f"{r[f'{ml}|only']:.2f}" for _, ml in MS])
TABLE(d, "**Table S2 Mutants killed only by the LLM tests (K = 8)**, as a share of all mutants of the module.", rows, widths=[2.0, 1.4, 1.4, 1.4], size=8)
# S2
H1(d, "S2 Reach on mutants by number of attempts")
rows = [["K"] + [ml for _, ml in MS]]
for K in range(1, 9):
    rows.append([str(K)] + [(lambda x: f"{x['A']:.2f} ({x['lo']:.2f}–{x['hi']:.2f})")(next(y for y in R["mutation"][ml] if y["K"] == K)) for _, ml in MS])
TABLE(d, "**Table S3 Reach on mutants relative to the existing tests** (module-level ratio among mutants killed by either side, averaged over 7 modules; 95% intervals from 1,500 module resamples).", rows, widths=[0.5, 1.9, 1.9, 1.9], size=8.5)
# S3
H1(d, "S3 Per-project real-fault results")
projects = sorted({b["bug"].split("/")[0] for b in bugs}, key=lambda p: -sum(b["bug"].startswith(p + "/") for b in bugs))
det = lambda b, m, k: any(x["detected"] for x in b["models"][m]["attempts"][:k])
rows = [["Project", "Faults"] + [f"{SH[ml]} K=1 / K=6" for _, ml in MS] + ["Any model K=6"]]
for p in projects:
    B = [b for b in bugs if b["bug"].startswith(p + "/")]
    rows.append([p, str(len(B))] + [f"{np.mean([det(b, m, 1) for b in B]):.2f} / {np.mean([det(b, m, 6) for b in B]):.2f}" for m, _ in MS] + [f"{np.mean([any(det(b, m, 6) for m, _ in MS) for b in B]):.2f}"])
rows.append(["All", str(len(bugs))] + [f"{np.mean([det(b, m, 1) for b in bugs]):.2f} / {np.mean([det(b, m, 6) for b in bugs]):.2f}" for m, _ in MS] + [f"{np.mean([any(det(b, m, 6) for m, _ in MS) for b in bugs]):.2f}"])
TABLE(d, "**Table S4 Share of real faults revealed, by project.**", rows, widths=[1.1, 0.6, 1.2, 1.2, 1.2, 1.0], size=8)
vb = json.load(open("../reach_pilot/bugsinpy/results_snapshot/valid_bugs.json"))
tried = {}
for k, v in vb.items():
    p = k.split("/")[0]; tried.setdefault(p, [0, 0]); tried[p][0] += 1; tried[p][1] += bool(v["valid"])
rows = [["Project", "Bugs tried", "Valid (fails on faulty, passes on fixed)"]] + [[p, str(t), str(v)] for p, (t, v) in sorted(tried.items(), key=lambda x: -x[1][1])]
TABLE(d, "**Table S5 Validation of BugsInPy bugs.** A bug is valid if the developer's fault-revealing test fails on the faulty and passes on the fixed version in our environment. Invalid bugs mostly failed to install with their pinned dependencies or did not reproduce the failure.", rows, widths=[1.5, 1.0, 2.6], size=8.5)
# S4
H1(d, "S4 Per-bug results")
rows = [["Bug"] + [f"{SH[ml]}: attempts revealing (of 6)" for _, ml in MS]]
for b in sorted(bugs, key=lambda b: (b["bug"].split("/")[0], int(b["bug"].split("/")[1]))):
    rows.append([b["bug"]] + [str(sum(x["detected"] for x in b["models"][m]["attempts"][:6])) for m, _ in MS])
TABLE(d, "**Table S6 Number of the six attempts that revealed the fault, per bug and model.**", rows, widths=[1.6, 1.6, 1.6, 1.6], size=7)
# S5 prompts
H1(d, "S5 Prompts")
src = open("../reach_pilot/study/mutation_study.py").read(); src2 = open("../reach_pilot/bugsinpy/bip_study.py").read()
def grab(s, start):
    i = s.index(start); j = s.index("```python", i); seg = s[i:j]
    return re.sub(r'"\s*\n\s*f?"', "", seg).replace('prompt = (f"', "").replace("\\n", " ").strip()
P(d, "**Mutation study** (one call per attempt; `{modname}` is the module's import path, followed by the module source in a python code block):", indent=False, size=9)
P(d, grab(src, 'prompt = (f"Below is the source'), indent=False, size=9, italic=True)
P(d, "**Real-fault study** (one call per attempt; followed by the non-test files changed by the fix, in their faulty state, each prefixed by '# file: <path>' and truncated to 40,000 characters):", indent=False, size=9)
P(d, grab(src2, 'prompt = (f"Below are source files'), indent=False, size=9, italic=True)
P(d, "Code was extracted from the first python code block of the answer. Models were called at their default temperature with up to 16,000 output tokens.", indent=False, size=9)
# S6
H1(d, "S6 Procedures, environment and cost")
P(d, "**Mutants.** Operators: arithmetic operator replacement, comparison operator replacement, Boolean operator replacement, constant replacement and negation removal on the module's AST; at most 150 mutants per module, sampled with a fixed seed. Generated tests that failed on the original module were discarded; a mutant is killed if a retained test fails or errors on it (with a timeout). Passing tests are identified from JUnit XML; the affected kill vectors of an earlier harness that parsed console output (humanize; 5 of 24 attempts on boltons/strutils) were recomputed from the stored generated tests (recompute_kills.py).", indent=False, size=9)
P(d, "**Real faults.** Each bug was checked out from a bare clone of the project at the faulty commit; the fixed version was obtained by applying the BugsInPy patch. Each project ran in its own virtual environment with the Python version recorded by BugsInPy (3.8 where older versions were unavailable) and setuptools < 60. A generated test reveals the fault if it fails on the faulty and passes on the fixed version; failures caused by import or collection errors are not counted. Test files that hung were stopped by a timeout and counted as producing no usable test.", indent=False, size=9)
P(d, "**Statistics.** Mutation reach: module-level ratios averaged across modules; 95% percentile intervals from 1,500 resamples of modules. Real-fault reach: share of faults revealed; 95% percentile intervals from 3,000 two-stage resamples (projects, then bugs within projects).", indent=False, size=9)
P(d, "**Cost.** API spending was about US$28 for the real-fault study (87 bugs × 3 models × 6 attempts) and is recorded with the mutation study's ledger in the replication package.", indent=False, size=9)
d.save("EMSE_Supplementary.docx"); print("ok")
