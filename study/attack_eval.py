"""Feature-aware (white-box) evasion test of the count-based screen.
The attacker edits the first ~2,300 tokens of each MACHINE paper so that five easily editable events (parentheses, square brackets,
semicolons, quotation marks, discourse markers) move a fraction e of the way from the paper's own count to the HUMAN mean count, with
the insertions clustered in two of the four windows (as human text clusters). Passives and nominalizations are NOT edited, so this is a
LOWER bound on what an adaptive attacker can do. Detector: clustering features, trained on human + the other two generators (clean text),
cross-validated by source paper; the attacked texts are only scored, never trained on. Metrics: AUC and share detected at 5% FPR."""
import json, re, io, contextlib, runpy, zlib, numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import features as F
with contextlib.redirect_stdout(io.StringIO()):
    ns = runpy.run_path("newmodel.py", run_name="lib")
doc_feats, FAM, H, fold, build = ns["doc_feats"], ns["FAM"], ns["H"], ns["fold"], ns["build"]
load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
human = load("data/human.jsonl")
TEXT = {g: {r["human_id"]: r["text"] for r in load(f"data/synthetic/{g}.jsonl")} for g in ("gpt4o", "claude", "llama")}
clean = {g: ns["build"](list({r["human_id"]: r for r in load(f"data/synthetic/{g}.jsonl")}.values()), "human_id") for g in TEXT}
EV = ["parentheses", "brackets", "semicolons", "quotes", "markers"]
hum_mean = {e: float(np.mean([F.counts(r["text"]).mean(0)[F.NAMES.index(e)] for r in human[:200] if len(F.TOK.findall(r["text"])) >= 2000])) for e in EV}
SLICE = 2300; SCALE = SLICE / 500
MARK = set(w for w in F.MARKERS if " " not in w)

def count(s, e): return F.FEATURES[e](s)
def attack(text, e, rng):
    toks = F.TOK.findall(text)[:SLICE]
    if e == 0: return " ".join(toks)
    hot = rng.choice(4, 2, replace=False); span = SLICE // 4
    def pos(k):                                    # clustered insertion sites: 80% inside two hot windows
        out = []
        for _ in range(k):
            w = rng.choice(hot) if rng.rand() < .8 else rng.randint(4)
            out.append(min(SLICE - 1, w * span + rng.randint(span)))
        return out
    for ev in EV:
        s = " ".join(toks); cur = count(s, ev); delta = int(round(e * (hum_mean[ev] * SCALE - cur)))
        if delta == 0: continue
        if delta > 0:
            for i in pos(delta):
                if i >= len(toks): continue
                if ev == "brackets": toks[i] += " [%d]" % rng.randint(1, 40)
                elif ev == "parentheses": toks[i] += " (%d)" % rng.randint(1, 30)
                elif ev == "quotes": toks[i] = '"' + toks[i].strip('"') + '"'
                elif ev == "semicolons":
                    j = next((j for j in range(i, min(len(toks), i + 80)) if toks[j].endswith(",")), None)
                    if j is not None: toks[j] = toks[j][:-1] + ";"
                elif ev == "markers": toks[i] += " However,"
        else:
            k = -delta; idx = [j for j, t in enumerate(toks) if (("(" in t) if ev == "parentheses" else ("[" in t) if ev == "brackets" else (";" in t) if ev == "semicolons"
                              else ('"' in t or "“" in t) if ev == "quotes" else t.strip(",.").lower() in MARK)]
            for j in rng.permutation(idx)[:k]:
                if ev == "parentheses": toks[j] = toks[j].replace("(", "", 1)
                elif ev == "brackets": toks[j] = toks[j].replace("[", "", 1)
                elif ev == "semicolons": toks[j] = toks[j].replace(";", ",", 1)
                elif ev == "quotes": toks[j] = re.sub(r'["“”]', "", toks[j])
                else: toks[j] = ""
    return " ".join(t for t in toks if t)

LEVELS = (0.0, 0.25, 0.5, 0.75, 1.0)
def evaluate(g, levels=LEVELS, fam=None):
    others = [t for t in clean if t != g]; fam = fam or FAM["NEW: rates+(a,b)"]
    res = {e: ([], []) for e in levels}; hs = []
    attacked = {e: {} for e in levels}
    for e in levels:
        rng0 = np.random.RandomState(int(e * 100) + 7)
        for pid, text in TEXT[g].items():
            f = doc_feats(attack(text, e, np.random.RandomState(zlib.crc32(f'{pid}|{e}'.encode()))))
            if f is not None: attacked[e][pid] = f
    out = {e: [] for e in levels}; hsc, ysc = [], {e: [] for e in levels}
    for k in range(5):
        tr = [(fam(f), 0) for gid, f in H if fold[gid] != k]
        for t in others: tr += [(fam(f), 1) for gid, f in clean[t] if fold.get(gid, -1) != k]
        X = np.array([x for x, _ in tr]); y = np.array([c for _, c in tr]); mu, sd = X.mean(0), X.std(0) + 1e-9
        w = np.array([1.0 if c == 0 else len(H) / max(1, sum(len(clean[t]) for t in others)) for c in y])
        clf = LogisticRegression(max_iter=4000).fit((X - mu) / sd, y, sample_weight=w)
        P = lambda L: clf.predict_proba((np.array(L) - mu) / sd)[:, 1]
        hsc += list(P([fam(f) for gid, f in H if fold[gid] == k]))
        for e in levels: ysc[e] += list(P([fam(attacked[e][pid]) for pid in attacked[e] if fold.get(pid, -1) == k]))
    thr = np.quantile(hsc, 0.95); rows = {}
    for e in levels:
        y = np.r_[np.zeros(len(hsc)), np.ones(len(ysc[e]))]; s = np.r_[hsc, ysc[e]]
        rows[e] = (roc_auc_score(y, s), float((np.array(ysc[e]) > thr).mean()))
    return rows

if __name__ == "__main__":
    print("human mean count per 500 tokens (targets):", {k: round(v, 2) for k, v in hum_mean.items()})
    allr = {}
    for g in ("gpt4o", "claude", "llama"):
        allr[g] = evaluate(g)
    print(f"\n{'target':8s}" + "".join(f"  e={e:<4}  AUC / det@5%FPR   " for e in LEVELS))
    for g, r in allr.items():
        print(f"{g:8s}" + "".join(f"  {r[e][0]:.3f} / {r[e][1]:.2f}        " for e in LEVELS))
    mix = {e: (np.mean([allr[g][e][0] for g in allr]), np.mean([allr[g][e][1] for g in allr])) for e in LEVELS}
    print(f"{'mixture':8s}" + "".join(f"  {mix[e][0]:.3f} / {mix[e][1]:.2f}        " for e in LEVELS))
    json.dump({g: {str(e): v for e, v in r.items()} for g, r in allr.items()}, open("results_attack.json", "w"))
