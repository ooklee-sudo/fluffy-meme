"""Sensitivity of the 'screen, then review the flagged' result to the two literature values it rests on:
review cost of a flagged unit c_A (Si et al.: 1.01 min vs 2.53 min for a direct check -> 0.40) and the human detection
d_A when the AI cue is right (0.87).  Everything else as in is_model_literature.py (d_H = 0.73, a_w = 0.35).
Saving = (best policy WITHOUT the screen - screen-then-review for all) / best policy without the screen,
where 'without the screen' = min(verify nothing, direct human check for all, risk-targeted direct check)."""
import argparse

import numpy as np

import is_model_human as imh
from is_model import crossfit_q
from is_model_literature import A_W, D_H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labeled-dir", required=True)
    ap.add_argument("--tag", default="haiku")
    a = ap.parse_args()
    docs, flag = imh.factscore_part_b(a.labeled_dir, a.tag, "notS")
    q, y = crossfit_q(docs)
    print(f"screen = {a.tag}: {len(y)} sentences, human error rate {y.mean():.3f}, flag rate {flag.mean():.3f}; d_H = {D_H}, a_w = {A_W}")
    print("saving of 'screen all, human reviews the flagged' over the best policy without a screen (rho = 0.10, lambda = 0.25)")
    print(f"{'c_A':>6}{'d_A':>6}" + "".join(f"{'L/c2=' + str(L):>10}" for L in (3, 5, 8, 12, 20)))
    for cA in (0.40, 0.70, 1.00, 1.30):
        for dA in (0.87, 0.73, 0.60):
            row = []
            for L in (3, 5, 8, 12, 20):
                none = L * y.mean()
                hum = 1.0 + L * (1 - D_H) * y.mean()
                v = D_H * L * q >= 1.0
                qh = (v * 1.0 + L * y * (1 - D_H * v)).mean()
                scr = (0.10 + flag * cA + flag * (y * L * (1 - dA) + (1 - y) * 0.25 * L * (1 - A_W)) + (1 - flag) * y * L).mean()
                best = min(none, hum, qh)
                row.append((best - scr) / best)
            print(f"{cA:6.2f}{dA:6.2f}" + "".join(f"{r:10.1%}" for r in row))


if __name__ == "__main__":
    main()
