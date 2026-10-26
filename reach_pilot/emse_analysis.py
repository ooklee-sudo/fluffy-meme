"""Numbers and figures for the EMSE manuscript: mutation reach (7 modules) and real-fault reach (87 BugsInPy faults)."""
import json, glob, os
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.optimize import brentq
H = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(0)
MODELS = [("anthropic/claude-haiku-5.5", "Claude Haiku 5.5"), ("anthropic/claude-sonnet-5.5", "Claude Sonnet 5.5"), ("deepseek/deepseek-v4.1-flash", "DeepSeek V4.1 Flash")]
h = lambda x: 0.0 if x <= 1 else 1 - (1 + np.log(x)) / x
kbar = lambda A: np.inf if A >= 1 else (np.nan if A <= 0 else brentq(lambda k: h(k) - A, 1 + 1e-9, 1e12))
out = {}
# ---------- mutation
mods = [json.load(open(p)) for p in sorted(glob.glob(f"{H}/study/results_snapshot/*.py.json"))]
rows = []
for d in mods:
    hm = np.array(d["human"], bool); r = dict(module=d["module"], project=d["repo"], n=len(hm), human=hm.mean())
    for m, ml in MODELS:
        at = d["models"][m]["attempts"]; K = np.array([a["killed"] for a in at], bool)
        r[f"{ml}|K1"] = K[:1].any(0).mean(); r[f"{ml}|K8"] = K.any(0).mean(); r[f"{ml}|only"] = (K.any(0) & ~hm).mean(); r[f"{ml}|valid1"] = at[0]["n_pass"]
    rows.append(r)
M = pd.DataFrame(rows); M.to_csv(f"{H}/emse_mutation_modules.csv", index=False)
big = [d for d in mods if len(d["human"]) >= 30]
def mut_A(m, K, idx):
    rs = []
    for i in idx:
        d = big[i]; hm = np.array(d["human"], bool); t = np.array([a["killed"] for a in d["models"][m]["attempts"][:K]], bool).any(0); mask = hm | t
        if hm[mask].sum(): rs.append(t[mask].mean() / hm[mask].mean())
    return np.mean(rs)
curves = {}
for m, ml in MODELS:
    cur = []
    for K in range(1, 9):
        a = mut_A(m, K, range(len(big))); bs = [mut_A(m, K, rng.integers(0, len(big), len(big))) for _ in range(1500)]
        cur.append((K, a, np.percentile(bs, 2.5), np.percentile(bs, 97.5)))
    curves[ml] = cur
out["mutation"] = {ml: [dict(K=k, A=round(a, 3), lo=round(l, 3), hi=round(u, 3)) for k, a, l, u in c] for ml, c in curves.items()}
out["mutation_modules"] = len(big)
# complementarity: share of mutants killed by the LLM (K=8) but not by the existing tests, among mutants killed by either
comp = {}
for m, ml in MODELS:
    v = []
    for d in big:
        hm = np.array(d["human"], bool); t = np.array([a["killed"] for a in d["models"][m]["attempts"]], bool).any(0); mask = hm | t; v.append((t & ~hm)[mask].mean())
    comp[ml] = round(float(np.mean(v)), 3)
out["mutation_llm_only_share"] = comp
# ---------- real faults
bugs = [json.load(open(p)) for p in sorted(glob.glob(f"{H}/bugsinpy/results_snapshot/*_*.json")) if "spend" not in p and "valid" not in p]
projects = sorted({b["bug"].split("/")[0] for b in bugs})
def det(b, m, k): return any(x["detected"] for x in b["models"][m]["attempts"][:k])
def clus_ci(vals_by_proj, B=3000):
    ps = list(vals_by_proj); bs = []
    for _ in range(B):
        pick = rng.choice(ps, len(ps)); v = np.concatenate([vals_by_proj[p][rng.integers(0, len(vals_by_proj[p]), len(vals_by_proj[p]))] for p in pick]); bs.append(v.mean())
    return np.percentile(bs, 2.5), np.percentile(bs, 97.5)
rf = {}
for m, ml in MODELS + [("any", "Any of the three")]:
    cur = []
    for K in range(1, 7):
        f = (lambda b: any(det(b, mm, K) for mm, _ in MODELS)) if m == "any" else (lambda b: det(b, m, K))
        by = {p: np.array([f(b) for b in bugs if b["bug"].startswith(p + "/")], float) for p in projects}
        allv = np.concatenate(list(by.values())); lo, hi = clus_ci(by); cur.append(dict(K=K, A=round(allv.mean(), 3), lo=round(lo, 3), hi=round(hi, 3)))
    rf[ml] = cur
out["real_faults"] = rf; out["n_bugs"] = len(bugs); out["projects"] = {p: sum(b["bug"].startswith(p + "/") for b in bugs) for p in projects}
out["per_project_any_K6"] = {p: round(np.mean([any(det(b, m, 6) for m, _ in MODELS) for b in bugs if b["bug"].startswith(p + "/")]), 2) for p in projects}
# test validity: share of attempts with no runnable test, and share with tests failing on the buggy version
va = {}
for m, ml in MODELS:
    at = [x for b in bugs for x in b["models"][m]["attempts"]]
    va[ml] = dict(attempts=len(at), no_tests=round(np.mean([x["n_tests"] == 0 for x in at]), 3), any_fail_buggy=round(np.mean([x["n_fail_buggy"] > 0 for x in at]), 3), detected=round(np.mean([x["detected"] for x in at]), 3))
out["validity"] = va
out["kbar"] = {ml: (lambda A: "inf" if np.isinf(kbar(A)) else round(kbar(A), 2))(rf[ml][-1]["A"]) for _, ml in MODELS}
json.dump(out, open(f"{H}/emse_results.json", "w"), indent=1)
# ---------- figure
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.6))
cols = {"Claude Haiku 5.5": "#2a6f97", "Claude Sonnet 5.5": "#6fa8c7", "DeepSeek V4.1 Flash": "#e07a5f", "Any of the three": "#333333"}
for ml, c in curves.items():
    a1.plot([x[0] for x in c], [x[1] for x in c], marker="o", ms=3, color=cols[ml], label=ml); a1.fill_between([x[0] for x in c], [x[2] for x in c], [x[3] for x in c], color=cols[ml], alpha=0.12)
a1.axhline(1, color="k", lw=0.7, ls="--"); a1.set_xlabel("Attempts K"); a1.set_ylabel("Reach relative to existing tests"); a1.set_title("a  Mutants (7 modules)", loc="left", fontsize=9); a1.legend(fontsize=7, frameon=False); a1.set_ylim(0, 1.6)
for ml, c in rf.items():
    a2.plot([x["K"] for x in c], [x["A"] for x in c], marker="o", ms=3, color=cols[ml], label=ml, ls="--" if ml.startswith("Any") else "-")
    a2.fill_between([x["K"] for x in c], [x["lo"] for x in c], [x["hi"] for x in c], color=cols[ml], alpha=0.1)
a2.axhline(1, color="k", lw=0.7, ls="--"); a2.set_xlabel("Attempts K"); a2.set_ylabel("Share of real faults revealed"); a2.set_title("b  Real faults (87 BugsInPy bugs)", loc="left", fontsize=9); a2.legend(fontsize=7, frameon=False); a2.set_ylim(0, 1.05)
fig.tight_layout(); fig.savefig(f"{H}/emse_fig_reach.png", dpi=200)
print(json.dumps({k: out[k] for k in ("mutation_modules", "mutation_llm_only_share", "n_bugs", "projects", "per_project_any_K6", "validity", "kbar")}, indent=0))
print({ml: (c[0], c[-1]) for ml, c in out["mutation"].items()}); print({ml: (c[0], c[-1]) for ml, c in rf.items()})
