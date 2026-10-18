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
    nb = len(base); b_ref, b_null, b_test = base[: int(.4 * nb)], base[int(.4 * nb): int(.7 * nb)], base[int(.7 * nb):]
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

    Xai = matrix([r["output_clean"] for r in ai])
    gen = np.array([r["model"] for r in ai]); train = np.array([split_train(r["chunk_id"]) for r in ai])
    p = fit(matrix([d["text"] for d in b_ref]))
    q = np.mean([fit(Xai[(gen == g) & train]) for g in sorted(set(gen))], axis=0)
    lpa, lqa = ll(Xai, p), ll(Xai, q); test_ai = np.where(~train)[0]
    def doc_ll(ds):
        X = matrix([d["text"] for d in ds]); return ll(X, p), ll(X, q)
    lp_null, lq_null = doc_ll(b_null); lp_test, lq_test = doc_ll(b_test)

    out = io.StringIO()
    def emit(s=""):
        print(s, flush=True); out.write(s + "\n")

    emit("# Weekly XML analysis\n")
    emit(f"Baseline {a.baseline}: {nb} docs (p fit on {len(b_ref)}, null {len(b_null)}, test {len(b_test)}). Machine docs {len(ai)} (draft+expand). Vocabulary {V}.\n")

    # calibration from synthetic mixtures of held-out baseline humans and held-out machine documents
    lp_h = np.concatenate([lp_null, lp_test]); lq_h = np.concatenate([lq_null, lq_test])
    grid = [0, .02, .05, .1, .15, .2, .3, .4, .5, .7, 1.0]; n = 400; mh = []
    for s in grid:
        k = int(round(n * s)); est = []
        for _ in range(15):
            h = rng.integers(0, len(lp_h), n - k); ai_i = rng.choice(test_ai, k)
            est.append(alpha_from_ll(np.concatenate([lp_h[h], lpa[ai_i]]), np.concatenate([lq_h[h], lqa[ai_i]])))
        mh.append(np.mean(est))
    mh = np.maximum.accumulate(np.array(mh)); cal = lambda x: float(np.interp(x, mh, grid))
    emit("Calibration (true share -> alpha-hat): " + ", ".join(f"{g:.2f}->{m:.3f}" for g, m in zip(grid, mh)) + "\n")

    # A. false positives in the baseline, by applicant group
    emit("## A. Baseline (pre-ChatGPT) false positives by applicant group\n")
    emit("| group | docs (test) | alpha-hat, all test docs | FPR at 99th-pct threshold, groups of 100 |\n|---|---|---|---|")
    n_grp = 100
    nulls = [alpha_from_ll(lp_null[i], lq_null[i]) for i in (rng.integers(0, len(b_null), n_grp) for _ in range(300))]
    thr = float(np.quantile(nulls, 0.99))
    for g in ["US", "non-US", "all"]:
        idx = np.array([i for i, d in enumerate(b_test) if g == "all" or d["group"] == g])
        if len(idx) < 30:
            emit(f"| {g} | {len(idx)} | too few | |"); continue
        fp = np.mean([alpha_from_ll(lp_test[j], lq_test[j]) > thr for j in (rng.choice(idx, n_grp) for _ in range(300))])
        emit(f"| {g} | {len(idx)} | {alpha_from_ll(lp_test[idx], lq_test[idx]):.3f} | {fp:.3f} |")
    emit(f"\nThreshold (99th percentile of baseline null, groups of {n_grp}): {thr:.3f}\n")

    # B. each week
    emit("## B. LLM-drafted share by week\n")
    emit("| week | docs | alpha-hat (95% CI) | calibrated share (95% CI) | US-only | non-US |\n|---|---|---|---|---|---|")
    detail = {}
    for path, ds in weeks.items():
        lp, lq = doc_ll(ds); tag = path.split("_")[-1].split(".")[0]
        est = lambda idx: alpha_from_ll(lp[idx], lq[idx])
        allidx = np.arange(len(ds)); ah = est(allidx)
        bs = [est(rng.integers(0, len(ds), len(ds))) for _ in range(a.boot)]; lo, hi = np.quantile(bs, [.025, .975])
        us = np.array([i for i, d in enumerate(ds) if d["group"] == "US"]); nu = np.array([i for i, d in enumerate(ds) if d["group"] == "non-US"])
        emit(f"| {tag} | {len(ds)} | {ah:.3f} ({lo:.3f}–{hi:.3f}) | {cal(ah):.3f} ({cal(lo):.3f}–{cal(hi):.3f}) | {est(us):.3f} (n={len(us)}) | {est(nu):.3f} (n={len(nu)}) |")
        detail[tag] = (ds, lp, lq)

    # C. by filing quarter within each week
    emit("\n## C. By filing quarter within each publication week (alpha-hat; groups with at least 60 docs)\n")
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
    open(a.out, "w").write(out.getvalue())


if __name__ == "__main__":
    main()
