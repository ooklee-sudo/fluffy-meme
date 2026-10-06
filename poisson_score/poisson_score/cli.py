"""Usage:
  python -m poisson_score.cli score DIR_OR_FILES... -o scores.csv [--window 200]
  python -m poisson_score.cli pilot --human DIR --synthetic DIR [--window 200]
  python -m poisson_score.cli explain FILE        # signed per-family diagnostics
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

from .evaluate import auc, bootstrap_auc_ci, tpr_at_fpr
from .score import FAMILIES, NBReference, score_text


def _files(paths):
    out = []
    for p in map(Path, paths):
        out += sorted(p.rglob("*.txt")) if p.is_dir() else [p]
    return out


def _row(path, r, label=""):
    row = {"file": str(path), "label": label, "n_tokens": r.n_tokens,
           "n_windows": r.n_windows, "poisson_score": r.score, "nb_score": r.nb_score}
    for k in FAMILIES:
        f = r.families.get(k)
        row[f"H_{k}"] = f.hellinger if f else float("nan")
        row[f"ID_{k}"] = f.dispersion if f else float("nan")
        row[f"rate_{k}"] = f.rate if f else float("nan")
    return row


def _write(rows, out):
    w = csv.DictWriter(out, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="poisson_score")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("score"); s.add_argument("paths", nargs="+")
    s.add_argument("-o", "--out"); s.add_argument("--window", type=int, default=200)
    p = sub.add_parser("pilot"); p.add_argument("--human", required=True)
    p.add_argument("--synthetic", required=True); p.add_argument("--window", type=int, default=200)
    p.add_argument("-o", "--out")
    e = sub.add_parser("explain"); e.add_argument("file"); e.add_argument("--window", type=int, default=200)
    a = ap.parse_args(argv)

    if a.cmd == "score":
        rows = [_row(f, score_text(f.read_text(errors="ignore"), a.window)) for f in _files(a.paths)]
        _write(rows, open(a.out, "w", newline="") if a.out and a.out != "-" else sys.stdout)
    elif a.cmd == "explain":
        r = score_text(Path(a.file).read_text(errors="ignore"), a.window)
        print(f"tokens={r.n_tokens} windows={r.n_windows} Poisson-Score={r.score:.3f}")
        for k, f in r.families.items():
            d = "over-dispersed (clumped)" if f.dispersion > 1.2 else \
                "under-dispersed (too regular)" if f.dispersion < 0.8 else "close to Poisson"
            print(f"  {k}: rate/window={f.rate:.2f} ID={f.dispersion:.2f} H={f.hellinger:.3f} p={f.p_disp:.3f} -> {d}")
    else:
        hf, sf = _files([a.human]), _files([a.synthetic])
        ht = [f.read_text(errors="ignore") for f in hf]
        st = [f.read_text(errors="ignore") for f in sf]
        ref = NBReference().fit(ht, a.window)
        hr = [score_text(t, a.window, reference=ref) for t in ht]
        sr = [score_text(t, a.window, reference=ref) for t in st]
        if a.out:
            _write([_row(f, r, "human") for f, r in zip(hf, hr)] +
                   [_row(f, r, "synthetic") for f, r in zip(sf, sr)], open(a.out, "w", newline=""))
        for name, get in (("Poisson-Score", lambda r: r.score), ("NB-Score", lambda r: r.nb_score)):
            pos = np.array([get(r) for r in sr]); neg = np.array([get(r) for r in hr])
            lo, hi = bootstrap_auc_ci(pos, neg)
            print(f"{name}: AUC={auc(pos, neg):.3f} [{lo:.3f}, {hi:.3f}]  "
                  f"TPR@5%FPR={tpr_at_fpr(pos, neg, .05):.3f}")
        print("Signed dispersion (median ID) human vs synthetic:")
        for k in FAMILIES:
            h = np.nanmedian([r.families[k].dispersion for r in hr if r.families])
            s_ = np.nanmedian([r.families[k].dispersion for r in sr if r.families])
            print(f"  {k}: {h:.2f} vs {s_:.2f}")
        print("NOTE: in-sample NB reference; hold out documents for the real analysis.")


if __name__ == "__main__":
    main()
