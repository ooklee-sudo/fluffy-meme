"""Decision-theoretic illustration (MODEL.md section 8) recomputed on HUMAN labels.

Part A (Proposition 5): per sentence, human check costs c = 1, detects an error w.p. delta, an undetected error costs L.
  Risk q_t is cross-fitted (5-fold over documents) from features a verifier knows for free; realised cost uses the human label y.
  Rule: verify iff delta * L * q >= 1.  Baselines: verify nothing / verify everything.  Closed form V = min(sum a+, sum a-).
Part B (Proposition 6): a cheap automatic screen (the LLM judge, cost rho = c1/c2) flags sentences; flagged ones go to the
  human (cost 1, perfect detection). The screen's quality (delta1 = P(flag | error), f1 = P(flag | no error)) is MEASURED
  against the human labels on the FActScore annotations, and its real flags are used to compute realised costs.
  Policies: none / all-human / screen-then-human for all / q-targeted human only / the three-region rule of Prop. 6
  (action = argmax of N(q)=0, H(q)=L q-1, S(q)=delta1 L q - rho - [q delta1 + (1-q) f1]).
"""
import argparse
import os

import numpy as np

import alloc_eval as ae
from human_validation import SOURCES, human_units, judge_units, pairs
from is_model import crossfit_q
from public_human_eval import ragtruth_docs, to_ae, wikibio_docs

RATIOS = [1.5, 2, 3, 5, 8, 12, 20, 40, 80]


def part_a(name, docs, delta_list=(1.0, 0.8)):
    q, y = crossfit_q(docs)
    print(f"\n{name}: {len(y)} sentences, human error rate {y.mean():.3f}, mean cross-fitted q {q.mean():.3f}, "
          f"q 5-95% {np.percentile(q, 5):.3f}-{np.percentile(q, 95):.3f}")
    for delta in delta_list:
        print(f"  delta = {delta}")
        print(f"  {'L/c':>5}{'none':>8}{'all':>8}{'targeted':>10}{'verified':>10}{'saving vs best baseline':>26}{'closed-form V':>15}")
        for L in RATIOS:
            none = L * y.mean()
            allv = 1.0 + L * (1 - delta) * y.mean()
            v = delta * L * q >= 1.0
            tgt = (v.mean() + L * (y * (1 - delta * v)).mean())
            best = min(none, allv)
            aa = delta * L * q - 1.0
            V = min(aa[aa > 0].sum(), -aa[aa < 0].sum()) / len(y)
            sav = (best - tgt) / best if best > 0 else 0.0
            print(f"  {L:5.1f}{none:8.3f}{allv:8.3f}{tgt:10.3f}{v.mean():10.2f}{sav:25.1%}{V:15.3f}")


def factscore_part_b(labeled_dir, judge_tag, event):
    """Aligned (human y, judge flag, features) per document over the FActScore annotations."""
    hdir = os.path.join(ae.DATA, "human")
    docs, flags = [], []
    for si, src in enumerate(SOURCES):
        hum = human_units(labeled_dir, src)
        jud = judge_units(os.path.join(hdir, f"labsH_{judge_tag}_{src}.jsonl"))
        rows = pairs(hum, jud, event)
        by = {}
        for t, i, h, j in rows:
            by.setdefault(t, []).append((i, h, j))
        for t, lst in by.items():
            lst.sort()
            n = len(lst)
            if n < 4:
                continue
            rank = np.arange(1, n + 1)
            pos = (rank - 0.5) / n
            X = np.column_stack([np.ones(n), (rank == 1).astype(float), pos - 0.5, (pos - 0.5) ** 2,
                                 np.full(n, float(src == "ChatGPT")), np.full(n, float(src == "PerplexityAI"))])
            docs.append({"title": src + "::" + t, "y": np.array([h for _, h, _ in lst]), "X": X, "c": np.ones(n)})
            flags.append(np.array([j for _, _, j in lst]))
    return docs, np.concatenate(flags)


def part_b(labeled_dir, judge_tag, event, rhos=(0.05, 0.1, 0.2, 0.3), Ls=(2, 3, 5, 8, 12, 20)):
    docs, flag = factscore_part_b(labeled_dir, judge_tag, event)
    q, y = crossfit_q(docs)
    assert len(flag) == len(y)
    d1 = flag[y == 1].mean(); f1 = flag[y == 0].mean()
    print(f"\nFActScore human labels, screen = judge '{judge_tag}' (event {event}): {len(y)} sentences, human error rate {y.mean():.3f}, "
          f"screen flag rate {flag.mean():.3f}")
    print(f"  measured screen quality: delta1 = {d1:.3f}, f1 = {f1:.3f}, discrimination delta1 - f1 = {d1 - f1:.3f}")
    print(f"  {'rho=c1/c2':>9}{'L/c2':>6}{'none':>8}{'human-all':>10}{'screen-all':>11}{'q-targeted':>11}{'3-region':>9}  {'saving vs best fixed':>21}  {'share none/screen/human':>24}")
    for rho in rhos:
        for L in Ls:
            none = L * y.mean()
            human_all = 1.0
            screen_all = rho + flag.mean() + L * (y * (1 - flag)).mean()
            tgt_v = L * q >= 1.0
            q_tgt = tgt_v.mean() + L * (y * (1 - tgt_v)).mean()
            Nv = np.zeros_like(q)
            Hv = L * q - 1.0
            Sv = d1 * L * q - rho - (q * d1 + (1 - q) * f1)
            act = np.argmax(np.vstack([Nv, Sv, Hv]), axis=0)  # 0 none, 1 screen, 2 human
            cost = np.where(act == 0, L * y, np.where(act == 1, rho + flag + L * y * (1 - flag), 1.0))
            three = cost.mean()
            best_fixed = min(none, human_all, screen_all)
            share = [float(np.mean(act == k)) for k in (0, 1, 2)]
            print(f"  {rho:9.2f}{L:6.0f}{none:8.3f}{human_all:10.3f}{screen_all:11.3f}{q_tgt:11.3f}{three:9.3f}  {(best_fixed - three) / best_fixed:21.1%}  "
                  f"{share[0]:7.2f}/{share[1]:.2f}/{share[2]:.2f}")
    # Proposition 6 condition at a reference point
    for L in (3, 5, 8):
        qh = 1.0 / L
        print(f"  Prop. 6 screening threshold at L/c2 = {L} (delta2 = 1, q_h = {qh:.2f}): screening pays only if c1/c2 < {(d1 - f1) * (1 - qh):.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labeled-dir", required=True, help="FActScore data/labeled folder")
    ap.add_argument("--wikibio", required=True)
    ap.add_argument("--rt-train", required=True)
    ap.add_argument("--rt-test", required=True)
    a = ap.parse_args()
    print("=" * 30, "PART A: value of targeting (Proposition 5), human labels", "=" * 30)
    for strict in (False, True):
        tag = "strict" if strict else "any"
        part_a(f"WikiBio GPT-3 [{tag}], position only", to_ae(wikibio_docs(a.wikibio, strict, 4)))
        rt = ragtruth_docs(a.rt_train, a.rt_test, "Summary", strict, 4)
        models = sorted({d["model"] for d in rt})
        part_a(f"RAGTruth summary [{tag}], position + generating model + log source length", to_ae(rt, models, True))
        part_a(f"RAGTruth summary [{tag}], position only", to_ae(rt))
    print("\n" + "=" * 30, "PART B: automatic screen + human (Proposition 6), FActScore human labels", "=" * 30)
    for tag in ("haiku", "mmed"):
        part_b(a.labeled_dir, tag, "notS")


if __name__ == "__main__":
    main()
