"""Estimate the share of LLM-drafted text in pre-grant publications by year (and publication quartile).

    python estimate_prevalence.py --human desc_2021_sample.tsv.gz --rewrites rewrites_slim.jsonl.gz \
        --years 2021=desc_2021_sample.tsv.gz 2024=desc_2024_sample.tsv.gz 2025=desc_2025_sample.tsv.gz --out prevalence.md

p (human word model) is fit on half of the 2021 human chunks; q (LLM word model) on 'draft' and 'expand'
rewrites only, because LLM-polished human text is not detectable (see validation_results.md).
Raw alpha-hat is mapped to a calibrated share through a curve built from known synthetic mixtures.
Time within a year is approximated by the serial number in pgpub_id (publication order).
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


def load_docs(path, rng, exclude=frozenset(), max_words=1650):
    out = []
    for row in csv.DictReader(open_tsv(path), delimiter="\t"):
        if row["pgpub_id"] in exclude:
            continue
        cs = [c for c in chunks_of(normalize(row["description_text"]), 1100, 500) if len(c.split()) <= max_words]
        if cs:
            out.append((row["pgpub_id"], rng.choice(cs)))
    return out


def split_train(key):
    return int(hashlib.md5(("q" + key).encode()).hexdigest(), 16) % 1000 < 500


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--human", required=True); ap.add_argument("--rewrites", required=True)
    ap.add_argument("--years", nargs="+", required=True, help="YEAR=path ...")
    ap.add_argument("--out", default="prevalence.md"); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--vocab", type=int, default=6000); ap.add_argument("--boot", type=int, default=200)
    ap.add_argument("--clean-vocab", type=int, default=0, help="keep only words found in at least N machine documents (drops human-only parsing artifacts such as 'infig')")
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed); prng = random.Random(a.seed)

    ai = [json.loads(l) for l in gzip.open(a.rewrites, "rt")]
    ai = [r for r in ai if r.get("output_clean") and r["prompt_type"] in DETECTABLE]
    src = {r["chunk_id"] for r in ai}
    h21 = load_docs(a.human, prng, exclude=src); prng.shuffle(h21)
    nh = len(h21); h_ref = [t for _, t in h21[: nh // 2]]; h_held = h21[nh // 2:]
    years = {}
    for spec in a.years:
        y, path = spec.split("=", 1)
        years[y] = load_docs(path, random.Random(a.seed)) if y != "2021" else h_held
    print("docs:", {y: len(d) for y, d in years.items()}, "human ref", len(h_ref), "AI", len(ai))

    texts = h_ref + [t for d in years.values() for _, t in d] + [r["output_clean"] for r in ai]
    df = collections.Counter()
    for t in texts:
        df.update(set(TOKEN.findall(t.lower())))
    df_ai = collections.Counter()
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

    def ll(X, p, cols=None):
        if cols is not None:
            X, p = X[:, cols], p[cols]
        w = np.log(p) - np.log1p(-p)
        return np.asarray(X @ w).ravel() + np.log1p(-p).sum()

    Xref, Xai = matrix(h_ref), matrix([r["output_clean"] for r in ai])
    gen = np.array([r["model"] for r in ai]); train = np.array([split_train(r["chunk_id"]) for r in ai])
    gens = sorted(set(gen))
    p = fit(Xref); q = np.mean([fit(Xai[(gen == g) & train]) for g in gens], axis=0)
    Xy = {y: matrix([t for _, t in d]) for y, d in years.items()}

    def pipeline(cols, tag):
        lpy = {y: ll(X, p, cols) for y, X in Xy.items()}; lqy = {y: ll(X, q, cols) for y, X in Xy.items()}
        lpa, lqa = ll(Xai, p, cols), ll(Xai, q, cols)
        test_ai = np.where(~train)[0]
        # calibration: known mixtures of held-out 2021 humans (not used for p) and held-out AI docs
        lp_h, lq_h = lpy["2021"], lqy["2021"]
        grid = [0, .02, .05, .1, .15, .2, .3, .4, .5, .7, 1.0]; n = 600; mean_hat = []
        for s in grid:
            k = int(round(n * s)); est = []
            for _ in range(15):
                h = rng.integers(0, len(lp_h), n - k); ai_i = rng.choice(test_ai, k)
                est.append(alpha_from_ll(np.concatenate([lp_h[h], lpa[ai_i]]), np.concatenate([lq_h[h], lqa[ai_i]])))
            mean_hat.append(np.mean(est))
        mh = np.maximum.accumulate(np.array(mean_hat))
        cal = lambda x: float(np.interp(x, mh, grid))
        res = {}
        for y, d in years.items():
            lp, lq = lpy[y], lqy[y]; ids = [i for i, _ in d]
            def est(idx): return alpha_from_ll(lp[idx], lq[idx])
            allidx = np.arange(len(d)); a_hat = est(allidx)
            bs = [est(rng.integers(0, len(d), len(d))) for _ in range(a.boot)]
            lo, hi = np.quantile(bs, [.025, .975])
            serial = np.array([int(i[4:]) for i in ids]); qb = np.digitize(serial, np.quantile(serial, [.25, .5, .75]))
            qs = [est(np.where(qb == k)[0]) for k in range(4)]
            res[y] = (len(d), a_hat, lo, hi, cal(a_hat), cal(lo), cal(hi), qs)
        return res, grid, mh

    out = io.StringIO()
    def emit(s=""):
        print(s); out.write(s + "\n")

    emit("# Share of LLM-drafted text in pre-grant publications, by year\n")
    emit(f"Human model p: {len(h_ref)} chunks from 2021. LLM model q: draft+expand rewrites ({len(ai)}), equal weight over {len(gens)} generators, train split only. Vocabulary {V}. One ~1,100-word chunk per application; ~3,000 applications per year (random sample of the year's long-text file).\n")
    res, grid, mh = pipeline(None, "full")
    emit("## All 6,000 words\n")
    emit("| year | docs | alpha-hat (95% CI) | calibrated share (95% CI) | by publication quartile (alpha-hat Q1..Q4) |\n|---|---|---|---|---|")
    for y in sorted(res):
        n, ah, lo, hi, c, cl, ch, qs = res[y]
        emit(f"| {y} | {n} | {ah:.3f} ({lo:.3f}–{hi:.3f}) | {c:.3f} ({cl:.3f}–{ch:.3f}) | {' / '.join(f'{x:.3f}' for x in qs)} |")
    emit("\nCalibration curve (true share -> mean alpha-hat in 600-doc mixtures): " + ", ".join(f"{g:.2f}->{m:.3f}" for g, m in zip(grid, mh)))

    fw = np.arange(min(300, V))   # most frequent words by document frequency: style words, little topical content
    res2, _, _ = pipeline(fw, "function")
    emit("\n## Robustness: only the 300 most frequent words (mostly function words, less affected by topic drift)\n")
    emit("| year | alpha-hat (95% CI) | calibrated share |\n|---|---|---|")
    for y in sorted(res2):
        n, ah, lo, hi, c, cl, ch, qs = res2[y]
        emit(f"| {y} | {ah:.3f} ({lo:.3f}–{hi:.3f}) | {c:.3f} ({cl:.3f}–{ch:.3f}) |")

    # which words drive the detector
    inv = {i: w for w, i in vocab.items()}
    lr = np.log(q / (1 - q)) - np.log(p / (1 - p))
    top = np.argsort(-lr)[:25]; bot = np.argsort(lr)[:25]
    emit("\n## Words that most separate LLM text from human text (log odds ratio of occurrence)\n")
    emit("LLM-overused: " + ", ".join(f"{inv[i]} ({lr[i]:.1f})" for i in top))
    emit("Human-overused: " + ", ".join(f"{inv[i]} ({lr[i]:.1f})" for i in bot))
    open(a.out, "w").write(out.getvalue())


if __name__ == "__main__":
    main()
