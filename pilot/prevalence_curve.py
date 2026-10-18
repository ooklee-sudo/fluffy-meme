"""Share of LLM-drafted-like text over time, by applicant group, firm size and technology section.

    python prevalence_curve.py --baseline week_210408.tsv.gz week_211007.tsv.gz week_220407.tsv.gz week_221006.tsv.gz \
        --weeks week_230406.tsv.gz ... --rewrites rewrites_slim.jsonl.gz --out curve.md [--strata group_cpc]

Baseline weeks are pre-ChatGPT publications. They are scored out-of-fold (5-fold cross-fitting), so they also appear
in the curve as placebo points. Each document is compared with the human model of its own stratum (US/non-US, optionally
x CPC section), so changes in the mix of applicants or technologies do not masquerade as AI use.
Writes curve.md and curve.csv (UTF-8).
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


def week_tag(path):
    m = re.search(r"week_(\d{6})", path)
    return m.group(1) if m else path


def load(path, prng):
    docs = []
    for row in csv.DictReader(open_tsv(path), delimiter="\t"):
        cs = [c for c in chunks_of(normalize(row["description_text"]), 1100, 500) if len(c.split()) <= 1650]
        if not cs:
            continue
        ctry = [c for c in row.get("applicant_countries", "").split(";") if c]
        cnt = int(row.get("org_week_count") or 0)
        docs.append({"week": week_tag(path), "filed": row.get("filing_date", ""), "text": prng.choice(cs),
                     "group": "non-US" if any(c != "US" for c in ctry) else "US",
                     "cpc": (row.get("cpc_section") or row.get("cpc_main", "")[:1] or "?"),
                     "size": "individual" if cnt == 0 else ("large (>=10/wk)" if cnt >= 10 else "small (<10/wk)")})
    return docs


def split_train(key):
    return int(hashlib.md5(("q" + key).encode()).hexdigest(), 16) % 1000 < 500


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", nargs="+", required=True); ap.add_argument("--weeks", nargs="*", default=[])
    ap.add_argument("--rewrites", required=True); ap.add_argument("--out", default="curve.md")
    ap.add_argument("--strata", choices=["group", "group_cpc"], default="group")
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--vocab", type=int, default=6000)
    ap.add_argument("--boot", type=int, default=100); ap.add_argument("--clean-vocab", type=int, default=15)
    ap.add_argument("--min-stratum", type=int, default=150)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed); prng = random.Random(a.seed)

    ai = [json.loads(l) for l in gzip.open(a.rewrites, "rt")]
    ai = [r for r in ai if r.get("output_clean") and r["prompt_type"] in DETECTABLE]
    base = [d for p in a.baseline for d in load(p, random.Random(a.seed))]
    later = [d for p in a.weeks for d in load(p, random.Random(a.seed))]
    for d in base + later:
        d["stratum"] = d["group"] if a.strata == "group" else f"{d['group']}|{d['cpc']}"
    print("baseline docs", len(base), "| later docs", len(later), "| AI docs", len(ai), flush=True)

    df = collections.Counter(); df_ai = collections.Counter()
    for t in [d["text"] for d in base + later] + [r["output_clean"] for r in ai]:
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

    Xai = matrix([r["output_clean"] for r in ai]); Xb = matrix([d["text"] for d in base]); Xl = matrix([d["text"] for d in later])
    gen = np.array([r["model"] for r in ai]); train = np.array([split_train(r["chunk_id"]) for r in ai])
    q = np.mean([fit(Xai[(gen == g) & train]) for g in sorted(set(gen))], axis=0)
    nb = len(base); strat_b = np.array([d["stratum"] for d in base]); grp_b = np.array([d["group"] for d in base])

    def p_models(idx):
        """human word model per stratum from baseline rows idx, with fallback to the applicant-group model"""
        gm = {g: fit(Xb[idx[grp_b[idx] == g]]) for g in ("US", "non-US") if (grp_b[idx] == g).sum() >= 30}
        pm = {}
        for s_ in set(strat_b):
            rows = idx[strat_b[idx] == s_]
            pm[s_] = fit(Xb[rows]) if len(rows) >= a.min_stratum else gm.get(s_.split("|")[0], fit(Xb[idx]))
        return pm

    def score(X, strata, pm):
        lp = np.zeros(X.shape[0]); default = next(iter(pm.values()))
        for s_ in set(strata):
            rows = np.where(strata == s_)[0]
            lp[rows] = ll(X[rows], pm.get(s_, pm.get(s_.split("|")[0], default)))
        return lp

    folds = np.arange(nb) % 5; lp_b = np.zeros(nb); lq_b = ll(Xb, q)
    for k in range(5):
        tr = np.where(folds != k)[0]; te = np.where(folds == k)[0]
        lp_b[te] = score(Xb[te], strat_b[te], p_models(tr))
    pm_full = p_models(np.arange(nb))
    strat_l = np.array([d["stratum"] for d in later])
    lp_l = score(Xl, strat_l, pm_full) if later else np.array([]); lq_l = ll(Xl, q) if later else np.array([])
    lpa = ll(Xai, next(iter(pm_full.values()))); lqa = ll(Xai, q); test_ai = np.where(~train)[0]

    grid = [0, .02, .05, .1, .15, .2, .3, .4, .5, .7, 1.0]; n = 400; mh = []
    for s_ in grid:
        k = int(round(n * s_)); est = []
        for _ in range(15):
            h = rng.integers(0, nb, n - k); ai_i = rng.choice(test_ai, k)
            est.append(alpha_from_ll(np.concatenate([lp_b[h], lpa[ai_i]]), np.concatenate([lq_b[h], lqa[ai_i]])))
        mh.append(np.mean(est))
    mh = np.maximum.accumulate(np.array(mh)); cal = lambda x: float(np.interp(x, mh, grid))

    rows_all = [("baseline-oof", d, lp_b[i], lq_b[i]) for i, d in enumerate(base)] + \
               [("later", d, lp_l[i], lq_l[i]) for i, d in enumerate(later)]
    by_week = collections.defaultdict(list)
    for kind, d, lp, lq in rows_all:
        by_week[d["week"]].append((d, lp, lq))

    def est_of(items, B=0):
        lp = np.array([x[1] for x in items]); lq = np.array([x[2] for x in items])
        ah = alpha_from_ll(lp, lq)
        if not B:
            return ah, None, None
        bs = [alpha_from_ll(lp[j], lq[j]) for j in (rng.integers(0, len(lp), len(lp)) for _ in range(B))]
        lo, hi = np.quantile(bs, [.025, .975]); return ah, lo, hi

    out, csvrows = io.StringIO(), []
    def emit(s=""):
        print(s, flush=True); out.write(s + "\n")

    emit(f"# LLM-drafted-like share by publication week (strata: {a.strata})\n")
    emit(f"Baseline weeks (pre-ChatGPT, out-of-fold): {', '.join(week_tag(p) for p in a.baseline)}; later weeks: {', '.join(week_tag(p) for p in a.weeks) or '-'}. "
         f"Documents: {nb} baseline, {len(later)} later. Machine documents {len(ai)}. Vocabulary {V}.\n")
    emit("Calibration (true share -> alpha-hat): " + ", ".join(f"{g:.2f}->{m:.3f}" for g, m in zip(grid, mh)) + "\n")
    emit("| week | kind | docs | alpha-hat (95% CI) | calibrated share | US | non-US | large firms | small firms |\n|---|---|---|---|---|---|---|---|---|")
    for wk in sorted(by_week):
        items = by_week[wk]; kind = "baseline (placebo)" if wk in {week_tag(p) for p in a.baseline} else "post"
        ah, lo, hi = est_of(items, a.boot)
        sub = {}
        for name, f in (("US", lambda d: d["group"] == "US"), ("non-US", lambda d: d["group"] == "non-US"),
                        ("large", lambda d: d["size"].startswith("large")), ("small", lambda d: d["size"].startswith("small"))):
            it = [x for x in items if f(x[0])]
            sub[name] = f"{est_of(it)[0]:.3f} (n={len(it)})" if len(it) >= 60 else "n<60"
        emit(f"| {wk} | {kind} | {len(items)} | {ah:.3f} ({lo:.3f}–{hi:.3f}) | {cal(ah):.3f} | {sub['US']} | {sub['non-US']} | {sub['large']} | {sub['small']} |")
        csvrows.append([wk, kind, len(items), round(ah, 4), round(lo, 4), round(hi, 4), round(cal(ah), 4)])

    emit("\n## By CPC section, pooled over post weeks versus pooled baseline (alpha-hat; at least 60 docs)\n")
    emit("| CPC section | baseline docs | baseline alpha-hat | post docs | post alpha-hat | difference |\n|---|---|---|---|---|---|")
    for sec in sorted({d["cpc"] for d in base + later}):
        ib = [x for x in rows_all if x[0] == "baseline-oof" and x[1]["cpc"] == sec]
        il = [x for x in rows_all if x[0] == "later" and x[1]["cpc"] == sec]
        if len(ib) >= 60 and len(il) >= 60:
            bh = est_of([(x[1], x[2], x[3]) for x in ib])[0]; lh = est_of([(x[1], x[2], x[3]) for x in il])[0]
            emit(f"| {sec} | {len(ib)} | {bh:.3f} | {len(il)} | {lh:.3f} | {lh - bh:+.3f} |")
    open(a.out, "w", encoding="utf-8").write(out.getvalue())
    with open(a.out.replace(".md", ".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["week", "kind", "docs", "alpha_hat", "ci_lo", "ci_hi", "calibrated_share"]); w.writerows(csvrows)


if __name__ == "__main__":
    main()
