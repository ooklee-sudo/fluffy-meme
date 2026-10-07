"""PRE-SPECIFIED cascade simulation: cheap Poisson screen first, Gemini judge only for the top-q share of the pool.
 Stage 1: Poisson NEW detector (trained on human + the other two generators, never the target) scores every document.
 Stage 2: the top q of the pool by that score (q in 10,20,30,50,100%) is sent to the Gemini judge; the rest cannot be flagged.
 Final score of sent documents:  C1 = Gemini score (ties broken by the screen rank);  C2 = mean of screen rank (in the pool)
   and Gemini rank (within the sent set).  Metric: share of machine papers flagged when at most 5% of ALL human papers are flagged.
 PRIMARY evaluation: pools with 10% machine papers (all human papers + resampled machine papers, 300 bootstrap pools).
 SECONDARY: pools as sampled (about one third machine).  Cost per 1,000 documents = q * 1000 * judge cost per document (US$0.0174 measured)."""
import sys, io, contextlib, runpy, math, numpy as np
from scipy.stats import rankdata
sys.argv = ["judge_eval.py", "gpt4o", "gemini"]
with contextlib.redirect_stdout(io.StringIO()):
    ns = runpy.run_path("judge_eval.py", run_name="lib")
key, J, GENS, poisson_scores = ns["key"], ns["J"], ns["GENS"], ns["poisson_scores"]
QS = (0.1, 0.2, 0.3, 0.5, 1.0); JUDGE_USD = 0.0174; JUDGE_SEC = 23.4

def system(y, P, Gm, q, rule):
    n = len(y); sent = np.argsort(-P)[: math.ceil(q * n)]
    rP = (rankdata(P) - 1) / max(1, n - 1)
    if rule == "C1": final = Gm[sent] + 1e-3 * rP[sent]
    else: final = (rP[sent] + (rankdata(Gm[sent]) - 1) / max(1, len(sent) - 1)) / 2
    is_h = (y[sent] == 0); n_h = int((y == 0).sum()); k = math.floor(0.05 * n_h)
    hs = np.sort(final[is_h])[::-1]
    thr = -np.inf if len(hs) <= k else hs[k]
    flagged = final > thr
    return float((flagged & (y[sent] == 1)).sum() / max(1, (y == 1).sum()))

def run(y, P, Gm, prevalence, B, seed):
    r = np.random.RandomState(seed); h = np.where(y == 0)[0]; m = np.where(y == 1)[0]
    n_m = len(m) if prevalence is None else round(len(h) * prevalence / (1 - prevalence))
    out = {(q, rule): [] for q in QS for rule in ("C1", "C2")}
    for _ in range(B):
        idx = np.concatenate([r.choice(h, len(h)), r.choice(m, n_m)])
        for q in QS:
            for rule in ("C1", "C2"): out[(q, rule)].append(system(y[idx], P[idx], Gm[idx], q, rule))
    return {k: (np.mean(v), *np.percentile(v, [2.5, 97.5])) for k, v in out.items()}

for label, prev in (("PRIMARY: 10% machine papers in the pool", 0.10), ("SECONDARY: pools as sampled (~1/3 machine)", None)):
    print(f"\n===== {label} =====")
    print(f"{'target':8s}{'q (share judged)':>18s}{'cost/1000 docs':>16s}{'hours/1000':>12s}{'C1: judge only':>26s}{'C2: fusion':>26s}")
    for g in GENS:
        ps = poisson_scores(g, [t for t in GENS if t != g], "NEW: rates+(a,b)")
        keep = [i for i, k in key.items() if k["source"] in ("human", g) and (k["source"], k["source_id"]) in ps
                and all(i in J[j] and J[j][i]["p_ai"] is not None for j in ("gpt4o", "gemini"))]
        y = np.array([0 if key[i]["source"] == "human" else 1 for i in keep])
        P = np.array([ps[(key[i]["source"], key[i]["source_id"])] for i in keep]); Gm = np.array([J["gemini"][i]["p_ai"] for i in keep], float)
        res = run(y, P, Gm, prev, 300, 11)
        for q in QS:
            c1, c2 = res[(q, "C1")], res[(q, "C2")]
            print(f"{g:8s}{q:18.0%}{q*1000*JUDGE_USD:15.1f}${q*1000*JUDGE_SEC/3600:12.1f}"
                  f"{f'{c1[0]:.2f} [{c1[1]:.2f},{c1[2]:.2f}]':>26s}{f'{c2[0]:.2f} [{c2[1]:.2f},{c2[2]:.2f}]':>26s}", flush=True)
