"""Validate the group-level LLM-share estimator on real patent text.

    python validate_detector.py --desc desc_2021_sample.tsv.gz --rewrites rewrites_slim.jsonl.gz --out validation.md

Human text : 2021 applications that are NOT sources of any rewrite, one random ~1,100-word chunk each,
             split into reference (fits p), null (calibrates thresholds), and test sets.
Machine text: normalized rewrites; source chunks are split into train (fits q) and test.
Every document passes through textnorm.normalize, so no formatting artifact separates the classes.
"""
import argparse, collections, csv, gzip, hashlib, io, json, random, re, sys, zipfile
import numpy as np
import scipy.sparse as sp
from build_chunks import chunks_of, open_tsv
from mixture import alpha_from_ll, EPS
from textnorm import normalize

csv.field_size_limit(sys.maxsize)
TOKEN = re.compile(r"[a-z]{3,}")


def load_human(path, exclude_ids, rng, max_words=1650):
    docs = []
    for row in csv.DictReader(open_tsv(path), delimiter="\t"):
        if row["pgpub_id"] in exclude_ids:
            continue
        cs = [c for c in chunks_of(normalize(row["description_text"]), 1100, 500) if len(c.split()) <= max_words]
        if cs:
            docs.append(rng.choice(cs))
    return docs


def split_bool(key, frac, salt):
    h = int(hashlib.md5((salt + key).encode()).hexdigest(), 16) % 1000
    return h < frac * 1000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desc", required=True); ap.add_argument("--rewrites", required=True)
    ap.add_argument("--out", default="validation.md"); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--vocab", type=int, default=6000)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed); prng = random.Random(a.seed)

    ai = [json.loads(l) for l in gzip.open(a.rewrites, "rt")]
    ai = [r for r in ai if r.get("output_clean")]
    human = load_human(a.desc, {r["chunk_id"] for r in ai}, prng)
    prng.shuffle(human)
    nh = len(human)
    h_ref, h_null, h_test = human[: nh // 2], human[nh // 2: 3 * nh // 4], human[3 * nh // 4:]
    print(f"human chunks {nh} (ref {len(h_ref)}, null {len(h_null)}, test {len(h_test)}); AI rewrites {len(ai)}")

    # vocabulary: most frequent words by document frequency over all documents
    all_texts = human + [r["output_clean"] for r in ai]
    df = collections.Counter()
    for t in all_texts:
        df.update(set(TOKEN.findall(t.lower())))
    vocab = {w: i for i, (w, c) in enumerate(df.most_common(a.vocab)) if c >= 25}
    V = len(vocab); print("vocabulary", V)

    def matrix(texts):
        rows, cols = [], []
        for i, t in enumerate(texts):
            for w in set(TOKEN.findall(t.lower())):
                j = vocab.get(w)
                if j is not None:
                    rows.append(i); cols.append(j)
        return sp.csr_matrix((np.ones(len(rows), dtype=np.float32), (rows, cols)), shape=(len(texts), V))

    Xh = {k: matrix(v) for k, v in {"ref": h_ref, "null": h_null, "test": h_test}.items()}
    Xa = matrix([r["output_clean"] for r in ai])
    gen = np.array([r["model"] for r in ai]); prompt = np.array([r["prompt_type"] for r in ai])
    train = np.array([split_bool(r["chunk_id"], 0.5, "q") for r in ai])
    gens = sorted(set(gen))

    def fit(X, smooth=1.0):
        n = X.shape[0]
        return np.clip((np.asarray(X.sum(axis=0)).ravel() + smooth) / (n + 2 * smooth), EPS, 1 - EPS)

    def loglik(X, p):
        w = np.log(p) - np.log1p(-p)
        return np.asarray(X @ w).ravel() + np.log1p(-p).sum()

    p = fit(Xh["ref"])
    def q_from(mask_gens):  # equal weight per generator, trained on train chunks only
        return np.mean([fit(Xa[(gen == g) & train]) for g in mask_gens], axis=0)
    q_all = q_from(gens)

    LP = {k: loglik(X, p) for k, X in Xh.items()}
    def ai_ll(q): return loglik(Xa, p), loglik(Xa, q)
    lp_ai, lq_ai = ai_ll(q_all)
    lq_h = {k: loglik(X, q_all) for k, X in Xh.items()}

    out = io.StringIO()
    def emit(s=""):
        print(s); out.write(s + "\n")

    emit("# Detector validation on real patent text\n")
    emit(f"Human chunks: {nh} (reference {len(h_ref)}, null {len(h_null)}, test {len(h_test)}). Machine rewrites: {len(ai)} "
         f"({', '.join(f'{g.split(chr(47))[-1]} {int((gen==g).sum())}' for g in gens)}). Vocabulary {V} words. Seed {a.seed}.\n")

    # A. false-positive rate with count-conditional null threshold
    emit("## A. False-positive rate on human-only groups\n")
    emit("| group size | threshold (99th pct of null) | FPR on test | mean alpha-hat |\n|---|---|---|---|")
    thr = {}
    for n in [5, 20, 100, 400]:
        nulls = [alpha_from_ll(LP["null"][idx], lq_h["null"][idx]) for idx in (rng.integers(0, len(h_null), n) for _ in range(300))]
        thr[n] = float(np.quantile(nulls, 0.99))
        tests = [alpha_from_ll(LP["test"][idx], lq_h["test"][idx]) for idx in (rng.integers(0, len(h_test), n) for _ in range(300))]
        emit(f"| {n} | {thr[n]:.3f} | {np.mean(np.array(tests) > thr[n]):.3f} | {np.mean(tests):.3f} |")

    # B. recovery of known mixtures, all generators pooled with equal weight
    test_idx = {g: np.where((gen == g) & ~train)[0] for g in gens}
    def group(n, frac, gs, per_gen=None):
        k = int(round(n * frac))
        h = rng.integers(0, len(h_test), n - k)
        ai_ids = np.concatenate([rng.choice(test_idx[rng.choice(gs)], 1) for _ in range(k)]) if k else np.array([], int)
        lp = np.concatenate([LP["test"][h], lp_ai[ai_ids]]); lq = np.concatenate([lq_h["test"][h], lq_ai[ai_ids]])
        return lp, lq
    emit("\n## B. Recovery of known AI shares (all generators, held-out source chunks)\n")
    emit("| true share | n=100 mean (sd) | n=400 mean (sd) | detected above threshold, n=100 |\n|---|---|---|---|")
    for frac in [0.0, 0.02, 0.05, 0.10, 0.25, 0.50]:
        r100 = [alpha_from_ll(*group(100, frac, gens)) for _ in range(60)]
        r400 = [alpha_from_ll(*group(400, frac, gens)) for _ in range(40)]
        emit(f"| {frac:.2f} | {np.mean(r100):.3f} ({np.std(r100):.3f}) | {np.mean(r400):.3f} ({np.std(r400):.3f}) | {np.mean(np.array(r100) > thr[100]):.2f} |")

    # C. leave-one-generator-out
    emit("\n## C. Leave-one-generator-out (q trained without the held-out model; groups of 200, 25% held-out AI)\n")
    emit("| held-out generator | pure-AI group alpha-hat (n=50) | 25% mix alpha-hat (sd) | | in-training reference (25% mix) |\n|---|---|---|---|---|")
    for g in gens:
        others = [x for x in gens if x != g]
        q_lo = q_from(others)
        lp_a, lq_a = loglik(Xa, p), loglik(Xa, q_lo)
        lq_ht = loglik(Xh["test"], q_lo)
        def mix(n, frac, lqa, lqh):
            k = int(round(n * frac)); h = rng.integers(0, len(h_test), n - k); ids = rng.choice(test_idx[g], k)
            return np.concatenate([LP["test"][h], lp_a[ids]]), np.concatenate([lqh[h], lqa[ids]])
        pure = np.mean([alpha_from_ll(*mix(50, 1.0, lq_a, lq_ht)) for _ in range(30)])
        mixed = [alpha_from_ll(*mix(200, 0.25, lq_a, lq_ht)) for _ in range(30)]
        lq_in, lq_hin = loglik(Xa, q_all), lq_h["test"]
        ref = np.mean([alpha_from_ll(*mix(200, 0.25, lq_in, lq_hin)) for _ in range(30)])
        emit(f"| {g} | {pure:.3f} | {np.mean(mixed):.3f} ({np.std(mixed):.3f}) | | {ref:.3f} |")

    # D. by prompt type (pure AI groups, all-generator q)
    emit("\n## D. Pure-AI groups by prompt type (n=50, held-out chunks)\n")
    emit("| prompt | alpha-hat mean | fraction above n=20 threshold (groups of 20) |\n|---|---|---|")
    for pt in sorted(set(prompt)):
        ids = np.where((prompt == pt) & ~train)[0]
        est = [alpha_from_ll(lp_ai[i], lq_ai[i]) for i in (rng.choice(ids, 50) for _ in range(30))]
        det = [alpha_from_ll(lp_ai[i], lq_ai[i]) > thr[20] for i in (rng.choice(ids, 20) for _ in range(60))]
        emit(f"| {pt} | {np.mean(est):.3f} | {np.mean(det):.2f} |")
    open(a.out, "w").write(out.getvalue())


if __name__ == "__main__":
    main()
