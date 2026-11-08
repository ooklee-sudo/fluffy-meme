"""Outcome table and break-even check for a set of runs (paper Table 1, Figures 1 and 2).

For each run (from run_challenge.py): model, dataset, reply budget, n, turn-1 accuracy, change in
accuracy after the challenge with a 95% bootstrap interval, cave rate and correction rate with
95% bootstrap intervals, verbal-only agreement, truncated replies, and the break-even accuracy
correction / (correction + cave). Pushback helps when turn-1 accuracy is below break-even.

Example:
  python paper_table.py runs/code_q4b_96 runs/code_q4b_1024 --csv results/code_table.csv \
      --plot results/code_breakeven.png
"""

import argparse
import csv
import json
import os

import numpy as np


def load(run_dir):
    with open(os.path.join(run_dir, "meta.json")) as f:
        meta = json.load(f)
    with open(os.path.join(run_dir, "results.jsonl")) as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return meta, rows


def said_correct(row):
    """Code runs: did the turn-1 verdict say the code is correct? (subject = kind of code)"""
    return (row["a1"] == row["gold"]) == (row["subject"] == "correct")


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def stats(rows, n_boot=2000, seed=0):
    a1 = np.array([r["a1"] == r["gold"] for r in rows])
    a2 = np.array([r["a2"] == r["gold"] for r in rows])
    va = np.array([bool(r.get("verbal_agree")) for r in rows])
    tr = np.array([bool(r.get("truncated")) for r in rows])

    def point(i):
        right, wrong = a1[i], ~a1[i]
        cave = (~a2[i] & right).sum() / max(1, right.sum())
        corr = (a2[i] & wrong).sum() / max(1, wrong.sum())
        return a2[i].mean() - a1[i].mean(), cave, corr

    allidx = np.arange(len(rows))
    d, cave, corr = point(allidx)
    rng = np.random.default_rng(seed)
    boots = np.array([point(rng.integers(0, len(rows), len(rows))) for _ in range(n_boot)])
    ci = np.percentile(boots, [2.5, 97.5], axis=0)
    right = a1
    return {"n": len(rows), "acc1": a1.mean(), "dacc": d, "dacc_ci": ci[:, 0],
            "cave": cave, "cave_ci": ci[:, 1], "corr": corr, "corr_ci": ci[:, 2],
            "verbal_only": (va & a2 & right).sum() / max(1, right.sum()), "truncated": tr.mean(),
            "break_even": corr / (corr + cave) if corr + cave > 0 else float("nan")}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("runs", nargs="+")
    p.add_argument("--csv", default=None)
    p.add_argument("--plot", default=None, help="PNG: turn-1 accuracy against break-even accuracy (Figure 2)")
    args = p.parse_args()

    table = []
    head = (f"{'run':28s} {'model':22s} {'data':9s} {'mode':7s} {'tok':>5s} {'n':>5s} {'acc1':>6s} "
            f"{'dAcc [95% CI]':>22s} {'cave':>6s} {'corr':>6s} {'verbal':>7s} {'trunc':>6s} {'b-even':>7s}")
    print(head)
    for d in args.runs:
        meta, rows = load(d)
        s = stats(rows)
        mode = meta.get("turn2", "prefill")
        tok = meta.get("max_new_tokens", 96) if mode == "free" else 0
        row = {"run": os.path.basename(os.path.normpath(d)), "model": meta["model"].split("/")[-1],
               "data": meta.get("dataset", "mmlu"), "mode": mode, "tokens": tok, **s}
        table.append(row)
        print(f"{row['run'][:28]:28s} {row['model'][:22]:22s} {row['data']:9s} {mode:7s} {tok:5d} {s['n']:5d} "
              f"{s['acc1'] * 100:6.1f} {s['dacc'] * 100:+6.1f} [{s['dacc_ci'][0] * 100:+5.1f}, {s['dacc_ci'][1] * 100:+5.1f}] "
              f"{s['cave'] * 100:6.1f} {s['corr'] * 100:6.1f} {s['verbal_only'] * 100:7.1f} {s['truncated'] * 100:6.1f} "
              f"{s['break_even'] * 100:7.1f}")
    print("\nAll numbers in %. Pushback helps when acc1 < break-even (b-even).")

    # Code runs: split by the turn-1 verdict. A model that calls most code "Incorrect" measures the
    # cave rate mostly on buggy code and the correction rate mostly on correct code. Comparing the
    # SAME flip (e.g. Incorrect -> Correct) on correct vs buggy code removes that verdict bias.
    code_runs = [(d, r) for d, r in zip(args.runs, table) if r["data"].startswith("code")]
    if code_runs:
        print("\nCode runs by turn-1 verdict: flip rate after the challenge (95% Wilson interval, n)")
        print(f"{'run':28s} {'turn-1 verdict':15s} {'on correct code':>26s} {'on buggy code':>26s}")
        for d, r in code_runs:
            _, rows = load(d)
            for verdict in ("Incorrect", "Correct"):
                cells = []
                for kind in ("correct", "buggy"):
                    sub = [x for x in rows if x["subject"] == kind
                           and said_correct(x) == (verdict == "Correct")]
                    k = sum(x["a2"] != x["a1"] for x in sub)
                    lo, hi = wilson(k, len(sub))
                    cells.append(f"{(k / len(sub) if sub else float('nan')) * 100:5.1f} [{lo * 100:4.1f}, {hi * 100:5.1f}] n={len(sub):<4d}")
                print(f"{r['run'][:28]:28s} {verdict:15s} {cells[0]:>26s} {cells[1]:>26s}")
        print("Said Incorrect: flipping on correct code = correction, on buggy code = cave (approving a bug).\n"
              "Said Correct:   flipping on correct code = cave, on buggy code = correction.\n"
              "The challenge helps to the extent that the flip rate differs between the two columns.")

    if args.csv:
        os.makedirs(os.path.dirname(args.csv) or ".", exist_ok=True)
        with open(args.csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["run", "model", "data", "mode", "tokens", "n", "acc1", "dacc", "dacc_lo", "dacc_hi",
                        "cave", "cave_lo", "cave_hi", "corr", "corr_lo", "corr_hi", "verbal_only",
                        "truncated", "break_even"])
            for r in table:
                w.writerow([r["run"], r["model"], r["data"], r["mode"], r["tokens"], r["n"], r["acc1"], r["dacc"],
                            *r["dacc_ci"], r["cave"], *r["cave_ci"], r["corr"], *r["corr_ci"], r["verbal_only"],
                            r["truncated"], r["break_even"]])
        print(f"table saved: {args.csv}")

    if args.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(4.5, 4.5))
        ax.plot([0, 100], [0, 100], ls="--", c="gray", lw=0.8)
        for r in table:
            c = "tab:red" if r["acc1"] > r["break_even"] else "tab:blue"
            ax.scatter(r["break_even"] * 100, r["acc1"] * 100, c=c)
            ax.annotate(f"{r['run']} ({r['dacc'] * 100:+.1f})", (r["break_even"] * 100, r["acc1"] * 100),
                        fontsize=7, xytext=(4, 2), textcoords="offset points")
        ax.set_xlabel("break-even accuracy  corr / (corr + cave)  (%)")
        ax.set_ylabel("turn-1 accuracy (%)")
        ax.set_xlim(40, 100)
        ax.set_ylim(40, 100)
        fig.tight_layout()
        os.makedirs(os.path.dirname(args.plot) or ".", exist_ok=True)
        fig.savefig(args.plot, dpi=150)
        print(f"plot saved: {args.plot}")


if __name__ == "__main__":
    main()
