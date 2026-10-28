"""Judge-sensitivity analysis: how much do the conclusions depend on the single LLM judge?

Two judges label the same biographies/summaries with the same numbered-sentence procedure (label_sent.py):
  A = anthropic/claude-haiku-5.5 (full run), B = a second judge from another model family on a random document subset.
Reported, on the sentences both judges produced claims for:
  1. agreement on the sentence-level event (raw agreement, Cohen's kappa) and the claim label mix of each judge
  2. the headline quantities recomputed under each judge: error rate, lead vs later sentences, tau, and the out-of-sample
     gain of the model-based static policy over uniform allocation (5-fold, 10% / 30% budget)
  3. cross-judge evaluation: policy fitted on judge X's labels, scored against judge Y's labels (does the gain survive a
     different notion of 'error'?)
"""
import argparse
import os

import numpy as np

import alloc_eval as ae
from common import read_jsonl


def sent_events(path, event):
    out = {}
    for r in read_jsonl(path):
        by = {}
        for c in r["claims"]:
            by.setdefault(c["sent"], []).append(c["label"])
        out[r["title"]] = {s: (int(any(l != "S" for l in v)) if event == "notS" else int("C" in v)) for s, v in by.items()}
    return out


def claim_mix(path):
    from collections import Counter
    c = Counter(x["label"] for r in read_jsonl(path) for x in r["claims"])
    n = sum(c.values())
    return {k: round(c[k] / n, 3) for k in "SCN"}


def kappa(a, b):
    a, b = np.array(a), np.array(b)
    po = (a == b).mean()
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return po, (po - pe) / (1 - pe)


def gain(train, test, folds, phi, rng_seed=0):
    """Static-minus-uniform gain: policy fitted on `train` docs' labels, scored on `test` docs' labels (same units)."""
    rg = np.random.default_rng(rng_seed)
    fold = np.zeros(len(train), int)
    fold[rg.permutation(len(train))] = np.arange(len(train)) % folds
    agg = {k: np.zeros(len(train)) for k in ("uniform", "lead", "tail", "static")}
    tot = np.zeros(len(train))
    for f in range(folds):
        te = np.where(fold == f)[0]
        g, t = ae.fit([train[i] for i in np.where(fold != f)[0]])
        c, tt = ae.eval_within([test[i] for i in te], g, t, phi)
        for k in agg:
            agg[k][te] = c[k]
        tot[te] = tt
    lo, hi = ae.boot(agg["static"], agg["uniform"], tot, B=1000)
    return (agg["static"].sum() - agg["uniform"].sum()) / tot.sum(), lo, hi, agg["lead"].sum() / tot.sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="judge A labels (full run)")
    ap.add_argument("--b", required=True, help="judge B labels (subset)")
    ap.add_argument("--gen", required=True, help="generations, for content features")
    ap.add_argument("--event", choices=["C", "notS"], default="C")
    ap.add_argument("--content", action="store_true")
    ap.add_argument("--folds", type=int, default=5)
    a = ap.parse_args()

    ea, eb = sent_events(a.a, a.event), sent_events(a.b, a.event)
    keep = {t: set(ea[t]) & set(eb[t]) for t in eb if t in ea}
    va, vb = [], []
    for t, ids in keep.items():
        for s in ids:
            va.append(ea[t][s])
            vb.append(eb[t][s])
    po, kp = kappa(va, vb)
    print(f"{os.path.basename(a.a)} (A) vs {os.path.basename(a.b)} (B), event={a.event}")
    print(f"docs in B: {len(eb)}; shared units: {len(va)}; event rate A {np.mean(va):.3f}, B {np.mean(vb):.3f}")
    print(f"sentence-event agreement {po:.3f}, Cohen kappa {kp:.3f}; A-only {np.mean([x == 1 and y == 0 for x, y in zip(va, vb)]):.3f}, B-only {np.mean([x == 0 and y == 1 for x, y in zip(va, vb)]):.3f}")
    print("claim label mix A:", claim_mix(a.a), " B:", claim_mix(a.b))

    da = ae.load(a.a, "unit", a.event, a.content, keep, a.gen)
    db = ae.load(a.b, "unit", a.event, a.content, keep, a.gen)
    ta = {d["title"]: d for d in da}
    db = [d for d in db if d["title"] in ta]
    da = [ta[d["title"]] for d in db]
    assert all(len(x["y"]) == len(y["y"]) for x, y in zip(da, db))
    print(f"docs analysed: {len(da)}, units: {sum(len(d['y']) for d in da)}")
    for nm, ds in (("A", da), ("B", db)):
        ys = np.concatenate([d["y"] for d in ds])
        lead = np.mean([d["y"][0] for d in ds])
        rest = np.concatenate([d["y"][1:] for d in ds]).mean()
        g, tau = ae.fit(ds)
        print(f"judge {nm}: error rate {ys.mean():.3f}, lead {lead:.3f}, later {rest:.3f}, tau {tau:.2f}, lead coef {g[1]:+.2f}")
    print(f"\n{'policy fitted on -> scored on':<30}{'gain@10%':>10} {'95% CI':<18}{'gain@30%':>10} {'95% CI':<18}{'lead-only@10':>13}")
    for nm, tr, te in (("A -> A", da, da), ("B -> B", db, db), ("A -> B", da, db), ("B -> A", db, da)):
        g1 = gain(tr, te, a.folds, 0.1)
        g3 = gain(tr, te, a.folds, 0.3)
        print(f"{nm:<30}{g1[0]:+10.3f} [{g1[1]:+.3f},{g1[2]:+.3f}]  {g3[0]:+10.3f} [{g3[1]:+.3f},{g3[2]:+.3f}]  {g1[3]:13.3f}")


if __name__ == "__main__":
    main()
