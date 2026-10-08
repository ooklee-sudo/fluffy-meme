"""PRE-SPECIFIED: cascade (screen gates the judge) before and after the hybrid attack. Same rules as judge_cascade.py:
screen scores all documents, the top share q of the pool is sent to the Gemini judge, final score = judge score (ties broken by screen);
metric = share of machine papers flagged when at most 5% of ALL human papers are flagged; pools with 10% machine papers (300 bootstrap pools).
Screen = clustering detector trained without the target and without Llama (the rewriter); all texts scored from the judged 2,000-token excerpts.
Usage: python3 judge_attack_cascade.py clean h1"""
import sys, math, numpy as np
from scipy.stats import rankdata
levels = sys.argv[1:]; sys.argv = sys.argv[:1]
import judge_attack_fusion as J
QS = (0.1, 0.2, 0.3, 0.5, 1.0)
def system(y, P, Gm, q):
    n = len(y); sent = np.argsort(-P)[: math.ceil(q * n)]; rP = (rankdata(P) - 1) / max(1, n - 1)
    final = Gm[sent] + 1e-3 * rP[sent]; is_h = y[sent] == 0; n_h = int((y == 0).sum()); k = math.floor(0.05 * n_h)
    hs = np.sort(final[is_h])[::-1]; thr = -np.inf if len(hs) <= k else hs[k]
    return float(((final > thr) & (y[sent] == 1)).sum() / max(1, (y == 1).sum()))
def pools(y, P, Gm, B=300, prev=0.10, seed=11):
    r = np.random.RandomState(seed); h, m = np.where(y == 0)[0], np.where(y == 1)[0]; n_m = round(len(h) * prev / (1 - prev)); out = {q: [] for q in QS}
    for _ in range(B):
        idx = np.concatenate([r.choice(h, len(h)), r.choice(m, n_m)])
        for q in QS: out[q].append(system(y[idx], P[idx], Gm[idx], q))
    return {q: (np.mean(v), *np.percentile(v, [2.5, 97.5])) for q, v in out.items()}
res = {}
for level in levels:
    T, G = J.texts(level), J.gem(level)
    for g in ("gpt4o", "claude", "llama"):
        mach = {i: J.doc_feats(t) for i, t in T.items() if J.key[i]["source"] == g}; S = J.screen_scores(g, mach)
        ids_m = [i for i in mach if mach[i] is not None and i in S and G.get(i) is not None]; ids_h = [i for i in J.hum_ids if i in S]
        ids = ids_h + ids_m; y = np.array([0] * len(ids_h) + [1] * len(ids_m)); P = np.array([S[i] for i in ids])
        Gm = np.array([J.GEM["clean"][i] if i in set(ids_h) else G[i] for i in ids], float)
        res[(level, g)] = pools(y, P, Gm)
print("Share of machine papers detected at <=5% FPR; pools with 10% machine papers; q = share of documents sent to the judge")
print(f"{'target':8s}{'q':>6s}" + "".join(f"{lv:>22s}" for lv in levels))
for g in ("gpt4o", "claude", "llama"):
    for q in QS:
        print(f"{g:8s}{q:6.0%}" + "".join(f"{res[(lv, g)][q][0]:12.2f} [{res[(lv, g)][q][1]:.2f},{res[(lv, g)][q][2]:.2f}]" for lv in levels))
