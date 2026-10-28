"""IS decision model with human-verifier parameters taken from the literature (LITERATURE_PARAMS.md), on human labels.

Part A  Proposition 5 recomputed with a realistic human detection probability delta (0.75, 0.60 instead of 1).
Part C  Proposition 6 EXTENDED with human reliance on the AI cue (Si et al. 2023, Prolific, FoolMeTwice claims):
          direct human check      : cost c2 = 1 (2.53 min),   detection d_H = 0.73  (human + retrieved passages)
          review of a flagged unit: cost c_A = 1.01/2.53,     detection d_A = 0.87  when the AI flag is right
                                    and a wrongly flagged (correct) unit is wrongly accepted as an error w.p. 1 - a_w = 0.65 (a_w = 0.35),
                                    which costs lambda * L (lambda: harm of 'correcting' a correct sentence, a free assumption)
          screen cost             : rho = c1/c2 (free grid)
        Expected net value of an action for a unit with error risk q (screen quality delta1, f1 measured against human labels):
          N = 0
          H = d_H L q - 1
          S = delta1 d_A L q - rho - c_A [q delta1 + (1-q) f1] - lambda L (1 - a_w) (1-q) f1
        Realised cost uses the judge's REAL flags and the HUMAN labels of the FActScore annotations.
Free assumptions are labelled; only c2, c_A, d_H, d_A, a_w come from the literature (and only approximately: accuracy on
true/false claims is used as a stand-in for the probability of catching an error).
"""
import argparse

import numpy as np

import is_model_human as imh
from is_model import crossfit_q
from public_human_eval import ragtruth_docs, to_ae, wikibio_docs

C2, C_A = 1.0, 1.01 / 2.53
D_H, D_A, A_W = 0.73, 0.87, 0.35


def part_c(labeled_dir, tag, rhos, lams, Ls):
    docs, flag = imh.factscore_part_b(labeled_dir, tag, "notS")
    q, y = crossfit_q(docs)
    d1, f1 = flag[y == 1].mean(), flag[y == 0].mean()
    print(f"\nscreen = judge '{tag}': {len(y)} sentences, human error rate {y.mean():.3f}, flag rate {flag.mean():.3f}, "
          f"measured delta1 {d1:.3f}, f1 {f1:.3f}")
    print(f"  literature parameters: c2 = 1, c_A = {C_A:.2f}, d_H = {D_H}, d_A = {D_A}, a_w = {A_W}")
    for lam in lams:
        print(f"\n  lambda = {lam} (harm of wrongly 'correcting' a correct sentence, as a share of L)")
        print(f"  {'rho':>5}{'L/c2':>6}{'none':>8}{'human':>8}{'screen':>8}{'q-human':>9}{'3-region':>9}  {'saving vs best fixed':>21}  {'none/screen/human':>18}")
        for rho in rhos:
            for L in Ls:
                none = L * y.mean()
                hum = C2 + L * (1 - D_H) * y.mean()
                scr_unit = rho + flag * C_A + flag * (y * L * (1 - D_A) + (1 - y) * lam * L * (1 - A_W)) + (1 - flag) * y * L
                scr = scr_unit.mean()
                v = D_H * L * q >= C2
                qh = (v * C2 + L * y * (1 - D_H * v)).mean()
                Nv = np.zeros_like(q)
                Hv = D_H * L * q - C2
                Sv = d1 * D_A * L * q - rho - C_A * (q * d1 + (1 - q) * f1) - lam * L * (1 - A_W) * (1 - q) * f1
                act = np.argmax(np.vstack([Nv, Sv, Hv]), axis=0)
                cost = np.where(act == 0, L * y, np.where(act == 1, scr_unit, C2 + L * y * (1 - D_H)))
                three = cost.mean()
                best = min(none, hum, scr)
                share = [float(np.mean(act == k)) for k in (0, 1, 2)]
                print(f"  {rho:5.2f}{L:6.0f}{none:8.3f}{hum:8.3f}{scr:8.3f}{qh:9.3f}{three:9.3f}  {(best - three) / best:21.1%}  "
                      f"{share[0]:5.2f}/{share[1]:.2f}/{share[2]:.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labeled-dir", required=True)
    ap.add_argument("--wikibio", required=True)
    ap.add_argument("--rt-train", required=True)
    ap.add_argument("--rt-test", required=True)
    a = ap.parse_args()
    print("=" * 20, "PART A: Proposition 5 with realistic human detection (delta 0.75 / 0.60)", "=" * 20)
    rt = ragtruth_docs(a.rt_train, a.rt_test, "Summary", False, 4)
    models = sorted({d["model"] for d in rt})
    imh.part_a("RAGTruth summary [any], position + generating model + log source length", to_ae(rt, models, True), (0.75, 0.60))
    imh.part_a("WikiBio GPT-3 [strict], position only", to_ae(wikibio_docs(a.wikibio, True, 4)), (0.75, 0.60))
    print("\n" + "=" * 20, "PART C: Proposition 6 extended with human reliance on the AI cue", "=" * 20)
    for tag in ("haiku", "mmed"):
        part_c(a.labeled_dir, tag, rhos=(0.0, 0.05, 0.1, 0.2), lams=(0.0, 0.25, 0.5), Ls=(3, 5, 8, 12))


if __name__ == "__main__":
    main()
