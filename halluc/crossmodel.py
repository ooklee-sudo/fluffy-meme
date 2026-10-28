"""One comparable row per (task, generator model): does the pilot's picture replicate?

Columns
  rate      sentence-level error rate (bio: contradicted; summ: not supported by the source article)
  lead/rest error rate of the lead sentence vs. all later sentences
  q1..q5    rate over position quintiles of the non-lead sentences (early -> late): shows the late rebound
  Fano5     observed Fano of 5-sentence windows / independent-intensity null (position + rarity); excess = shared latent difficulty
  tau       document-level SD of the random intercept (logit scale), fitted by marginal likelihood (alloc_eval.fit)
  rarity    fitted rarity coefficient (negative = rarer entities err more)
  st-un     out-of-sample gain of the model-based static policy over uniform allocation at 10% / 30% budget
            (per-document budgets, unit cost) with a bootstrap CI over documents
  lead@10   share of errors caught by verifying only the lead sentence at 10% budget
  ad-st     adaptive minus static at 30% / 50% pooled budget (delta = 1)
"""
import argparse
import os

import numpy as np

import alloc_eval as ae
from analyze import fano, fano_null, fit as glm_fit, to_frame
from analyze_sent import sentence_docs
from common import DATA, read_jsonl


def row(path, event):
    raw = read_jsonl(path)
    df = to_frame(sentence_docs(raw, "all", event), strict=True)
    rate = df.y.mean()
    lead = df[df.t == 1].y.mean()
    rest = df[df.t > 1]
    q = [rest[(rest.t / rest.n > a) & (rest.t / rest.n <= b)].y.mean() for a, b in zip((0, .2, .4, .6, .8), (.2, .4, .6, .8, 1.0))]
    m = glm_fit(df, ["lt", "lsl_c"])
    import statsmodels.api as sm
    prob = m.predict(sm.add_constant(df[["lt", "lsl_c"]])).values
    rng = np.random.default_rng(0)
    obs, nl = fano(df, 5), fano_null(df, 5, prob, 100, rng)

    docs = ae.load(path, "unit", event)
    gam, tau = ae.fit(docs)
    rg = np.random.default_rng(0)
    fold = np.zeros(len(docs), int)
    fold[rg.permutation(len(docs))] = np.arange(len(docs)) % 5
    res = {}
    for phi in (0.1, 0.3):
        agg = {k: np.zeros(len(docs)) for k in ("uniform", "lead", "tail", "static")}
        tot = np.zeros(len(docs))
        for f in range(5):
            te = np.where(fold == f)[0]
            gf, tf = ae.fit([docs[i] for i in np.where(fold != f)[0]])
            c, t = ae.eval_within([docs[i] for i in te], gf, tf, phi)
            for k in agg:
                agg[k][te] = c[k]
            tot[te] = t
        lo, hi = ae.boot(agg["static"], agg["uniform"], tot, B=1000)
        res[phi] = ((agg["static"].sum() - agg["uniform"].sum()) / tot.sum(), lo, hi, agg["lead"].sum() / tot.sum())
    ad = {}
    for phi in (0.3, 0.5):
        agg = {k: np.zeros(len(docs)) for k in ("uniform", "static", "adaptive")}
        tot = np.zeros(len(docs))
        for f in range(5):
            te = np.where(fold == f)[0]
            gf, tf = ae.fit([docs[i] for i in np.where(fold != f)[0]])
            c, t = ae.eval_pooled([docs[i] for i in te], gf, tf, phi, 1.0, np.random.default_rng(f))
            for k in agg:
                agg[k][te] = c[k]
            tot[te] = t
        lo, hi = ae.boot(agg["adaptive"], agg["static"], tot, B=1000)
        ad[phi] = ((agg["adaptive"].sum() - agg["static"].sum()) / tot.sum(), lo, hi)
    return dict(docs=len(docs), rate=rate, lead=lead, rest=rest.y.mean(), q=q, fano=(obs, nl.mean()), tau=tau,
                rarity=gam[4], st10=res[0.1], st30=res[0.3], ad30=ad[0.3], ad50=ad[0.5])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True, help="task:event:path, e.g. bio:C:data/labs_x.jsonl or summ:notS:data/labs_summ_x.jsonl")
    a = ap.parse_args()
    print(f"{'task/model':<34}{'docs':>5}{'rate':>6}{'lead':>6}{'rest':>6}  {'q1..q5 (non-lead, early->late)':<32}{'Fano5 obs/null':>15}{'tau':>5}{'rarity':>7}  {'static-uniform @10%':<24}{'@30%':<22}{'lead@10':>8}  {'adaptive-static @30%':<24}{'@50%':<22}")
    for spec in a.runs:
        task, event, path = spec.split(":", 2)
        r = row(path, event)
        name = f"{task}/{os.path.basename(path).replace('labs_', '').replace('summ_', '').replace('.jsonl', '')}"
        s10, s30, a30, a50 = r["st10"], r["st30"], r["ad30"], r["ad50"]
        print(f"{name:<34}{r['docs']:>5}{r['rate']:6.2f}{r['lead']:6.2f}{r['rest']:6.2f}  {' '.join(f'{x:.2f}' for x in r['q']):<32}"
              f"{r['fano'][0]:7.2f}/{r['fano'][1]:<7.2f}{r['tau']:5.2f}{r['rarity']:+7.2f}  "
              f"{s10[0]:+.3f} [{s10[1]:+.3f},{s10[2]:+.3f}]  {s30[0]:+.3f} [{s30[1]:+.3f},{s30[2]:+.3f}]  {s10[3]:8.3f}  "
              f"{a30[0]:+.3f} [{a30[1]:+.3f},{a30[2]:+.3f}]  {a50[0]:+.3f} [{a50[1]:+.3f},{a50[2]:+.3f}]", flush=True)


if __name__ == "__main__":
    main()
