"""Run the whole analysis locally on weekly XML samples; prints a small markdown report to paste into the chat.

    python analyze_weeks.py --baseline week_210408.tsv.gz --weeks week_260108.tsv.gz week_260409.tsv.gz week_261008.tsv.gz \
        --rewrites rewrites_slim.jsonl.gz --out weeks_results.md

Needs: numpy, scipy (pip install numpy scipy). Files needed in the same folder: build_chunks.py, mixture.py,
textnorm.py (all in the repository's pilot folder).
Human model p comes from the baseline week (pre-ChatGPT, same XML source as the later weeks); the machine model q
from draft+expand rewrites (train split). Calibration and thresholds use held-out baseline documents.
"""
import argparse, collections, csv, gzip, hashlib, io, json, random, re, sys
import numpy as np
import scipy.sparse as sp
from build_chunks import chunks_of, open_tsv
from mixture import alpha_from_ll, EPS
from textnorm import normalize

csv.field_size_limit(sys.maxsize)
TOKEN = re.compile(r"[a-z]{3,}")
DETECTABLE = {"draft", "expand"}


def load_week(path, prng):
    docs = []
    for row in csv.DictReader(open_tsv(path), delimiter="\t"):
        cs = [c for c in chunks_of(normalize(row["description_text"]), 1100, 500) if len(c.split()) <= 1650]
        if not cs:
            continue
        ctry = [c for c in row.get("applicant_countries", "").split(";") if c]
        group = "non-US" if any(c != "US" for c in ctry) else "US"
        docs.append({"id": row["pgpub_id"], "filed": row.get("filing_date", ""), "group": group, "text": prng.choice(cs)})
    return docs


def split_train(key):
    return int(hashlib.md5(("q" + key).encode()).hexdigest(), 16) % 1000 < 500


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True); ap.add_argument("--weeks", nargs="+", required=True)
    ap.add_argument("--rewrites", required=True); ap.add_argument("--out", default="weeks_results.md")
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--vocab", type=int, default=6000)
    ap.add_argument("--boot", type=int, default=200); ap.add_argument("--clean-vocab", type=int, default=15)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed); prng = random.Random(a.seed)

    ai = [json.loads(l) for l in gzip.open(a.rewrites, "rt")]
    ai = [r for r in ai if r.get("output_clean") and r["prompt_type"] in DETECTABLE]
    base = load_week(a.baseline, prng); prng.shuffle(base)
    nb = len(base)
    weeks = {p: load_week(p, random.Random(a.seed)) for p in a.weeks}
    print("baseline docs", nb, "| weeks:", {p.split('_')[-1].split('.')[0]: len(d) for p, d in weeks.items()}, "| AI docs", len(ai), flush=True)

    texts = [d["text"] for d in base] + [d["text"] for ds in weeks.values() for d in ds] + [r["output_clean"] for r in ai]
    df = collections.Counter(); df_ai = collections.Counter()
    for t in texts:
        df.update(set(TOKEN.findall(t.lower())))
    for r in ai:
        df_ai.update(set(TOKEN.findall(r["output_clean"].lower())))
    ranked = [w for w, c in df.most_common(a.vocab * 3) if c >= 25 and df_ai[w] >= a.clean_vocab][: a.vocab]
    vocab = {w: i for i, w in enumerate(ranked)}; V = len(vocab)

    def matrix(ts):
        r, c = [], []
        for i, t in enumerate(ts):
            for w in set(TOKEN.findall(t.lower())):
                j = vocab.get(w)
                if j is not None:
                    r.append(i); c.append(j)
        return sp.csr_matrix((np.ones(len(r), dtype=np.float32), (r, c)), shape=(len(ts), V))

    def fit(X, s=1.0):
        return np.clip((np.asarray(X.sum(axis=0)).ravel() + s) / (X.shape[0] + 2 * s), EPS, 1 - EPS)

    def ll(X, p):
        w = np.log(p) - np.log1p(-p)
        return np.asarray(X @ w).ravel() + np.log1p(-p).sum()

    Xai = matrix([r["output_clean"] for r in ai]); Xb = matrix([d["text"] for d in base])
    gen = np.array([r["model"] for r in ai]); train = np.array([split_train(r["chunk_id"]) for r in ai])
    q = np.mean([fit(Xai[(gen == g) & train]) for g in sorted(set(gen))], axis=0)
    p_full = fit(Xb)
    # baseline documents are scored with a model that never saw them (5-fold cross-fitting)
    folds = np.arange(nb) % 5; lp_b = np.zeros(nb); lq_b = ll(Xb, q)
    for k in range(5):
        tr = np.where(folds != k)[0]; te = np.where(folds == k)[0]
        lp_b[te] = ll(Xb[te], fit(Xb[tr]))
    lpa, lqa = ll(Xai, p_full), ll(Xai, q); test_ai = np.where(~train)[0]
    grp_b = np.array([d["group"] for d in base])

    out = io.StringIO()
    def emit(s=""):
        print(s, flush=True); out.write(s + "\n")

    emit("# Weekly XML analysis (cross-fitted baseline, within-group comparisons)\n")
    emit(f"Baseline {a.baseline}: {nb} docs (US {int((grp_b=='US').sum())}, non-US {int((grp_b=='non-US').sum())}), scored by 5-fold cross-fitting. Machine docs {len(ai)} (draft+expand). Vocabulary {V}.\n")

    grid = [0, .02, .05, .1, .15, .2, .3, .4, .5, .7, 1.0]; n = 400; mh = []
    for s_ in grid:
        k = int(round(n * s_)); est = []
        for _ in range(15):
            h = rng.integers(0, nb, n - k); ai_i = rng.choice(test_ai, k)
            est.append(alpha_from_ll(np.concatenate([lp_b[h], lpa[ai_i]]), np.concatenate([lq_b[h], lqa[ai_i]])))
        mh.append(np.mean(est))
    mh = np.maximum.accumulate(np.array(mh)); cal = lambda x: float(np.interp(x, mh, grid))
    emit("Calibration (true share -> alpha-hat): " + ", ".join(f"{g:.2f}->{m:.3f}" for g, m in zip(grid, mh)) + "\n")

    def boot(lp, lq, idx, B):
        return [alpha_from_ll(lp[j], lq[j]) for j in (rng.choice(idx, len(idx)) for _ in range(B))]

    emit("## A. Baseline (pre-ChatGPT) alpha-hat by applicant group, all documents cross-fitted\n")
    emit("| group | docs | alpha-hat (95% CI) | 99th pct of alpha-hat in 100-doc groups |\n|---|---|---|---|")
    base_idx = {}
    for g in ["US", "non-US", "all"]:
        idx = np.where((grp_b == g) | (g == "all"))[0]; base_idx[g] = idx
        if len(idx) < 30:
            emit(f"| {g} | {len(idx)} | too few | |"); continue
        bs = boot(lp_b, lq_b, idx, a.boot); lo, hi = np.quantile(bs, [.025, .975])
        g100 = [alpha_from_ll(lp_b[j], lq_b[j]) for j in (rng.choice(idx, 100) for _ in range(300))]
        emit(f"| {g} | {len(idx)} | {alpha_from_ll(lp_b[idx], lq_b[idx]):.3f} ({lo:.3f}–{hi:.3f}) | {np.quantile(g100, .99):.3f} |")

    detail = {}
    emit("\n## B. Each 2026 week versus the same-group baseline (alpha-hat, difference with 95% CI, calibrated share)\n")
    emit("| week | group | docs | alpha-hat (95% CI) | baseline alpha-hat | difference (95% CI) | calibrated share |\n|---|---|---|---|---|---|---|")
    for path, ds in weeks.items():
        X = matrix([d["text"] for d in ds]); lp, lq = ll(X, p_full), ll(X, q); tag = path.split("_")[-1].split(".")[0]
        detail[tag] = (ds, lp, lq); grp = np.array([d["group"] for d in ds])
        for g in ["all", "US", "non-US"]:
            widx = np.where((grp == g) | (g == "all"))[0]; bidx = base_idx[g]
            if len(widx) < 30 or len(bidx) < 30:
                continue
            ah = alpha_from_ll(lp[widx], lq[widx]); bh = alpha_from_ll(lp_b[bidx], lq_b[bidx])
            bw = boot(lp, lq, widx, a.boot); bb = boot(lp_b, lq_b, bidx, a.boot)
            lo, hi = np.quantile(bw, [.025, .975]); dlo, dhi = np.quantile(np.array(bw) - np.array(bb), [.025, .975])
            emit(f"| {tag} | {g} | {len(widx)} | {ah:.3f} ({lo:.3f}–{hi:.3f}) | {bh:.3f} | {ah - bh:+.3f} ({dlo:+.3f} to {dhi:+.3f}) | {cal(ah):.3f} |")

    emit("\n## C. By filing quarter within each publication week (alpha-hat; at least 60 docs; mixes US and non-US)\n")
    emit("| week | filing quarter | docs | alpha-hat | calibrated share |\n|---|---|---|---|---|")
    for tag, (ds, lp, lq) in detail.items():
        qs = collections.defaultdict(list)
        for i, d in enumerate(ds):
            y, m = d["filed"][:4], int(d["filed"][4:6] or 0)
            if y and m:
                qs[f"{y}Q{(m - 1) // 3 + 1}"].append(i)
        for k in sorted(qs):
            if len(qs[k]) >= 60:
                idx = np.array(qs[k]); ah = alpha_from_ll(lp[idx], lq[idx])
                emit(f"| {tag} | {k} | {len(idx)} | {ah:.3f} | {cal(ah):.3f} |")
    open(a.out, "w", encoding="utf-8").write(out.getvalue())


if __name__ == "__main__":
    main()
