"""Plot and tabulate a physical-error-rate sweep of decoder logical error rates.

Inputs (either):
  --log  FILE   text log with lines like  "eval d=5 p=0.005: NN 0.0281  MWPM 0.0413  BPOSD 0.0355  BPOSD* 0.0383"
  --json FILE   results JSON; the table is found automatically (see find_table). If the structure is not
                recognised the script prints it so the parser can be adjusted (--key a.b selects a subtree).

Outputs (in --out-dir): psweep.png (log-scale plot with 95% Wilson intervals), psweep.csv, psweep.md
(table incl. relative reduction of the reference decoder vs every other decoder and a ~2-sigma flag).

  python qec_tools/plot_psweep.py --log run.log --n 20000 --ref NN --out-dir results/figs
  python qec_tools/plot_psweep.py --json results/c_large_psweep.json --n 20000

Notes: the intervals assume independent shots (binomial). The ~2-sigma flag compares two rates as if they came
from independent samples; if the decoders were evaluated on the SAME shots a paired test would be tighter.
"""
import argparse
import csv
import json
import math
import os
import re
import sys

LINE = re.compile(r"eval\s+(?:d=(\d+)\s+)?p=([0-9.]+(?:e-?\d+)?)\s*:\s*(.*)", re.I)
PAIR = re.compile(r"([A-Za-z][A-Za-z0-9_+*\-]*)\s+([0-9]*\.?[0-9]+(?:e-?\d+)?)")
SKIP_KEYS = {"p", "d", "n", "shots", "rounds", "seed", "n_shots", "distance", "eval_n", "n_eval", "physical_p"}
VALUE_KEYS = ("ler", "rate", "logical_error_rate", "err", "error", "value", "mean", "fail_rate")


def parse_log(path):
    table = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = LINE.search(line)
            if not m:
                continue
            p = float(m.group(2))
            table.setdefault(p, {}).update({k: float(v) for k, v in PAIR.findall(m.group(3))})
    return table


def _num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, dict):
        for k in VALUE_KEYS:
            if k in v and isinstance(v[k], (int, float)):
                return float(v[k])
    return None


def _floatkey(k):
    try:
        return float(k)
    except (TypeError, ValueError):
        return None


def find_table(obj):
    """Return {p: {decoder: rate}} from common layouts, searching recursively; None if not found."""
    # layout A: {"0.005": {"NN": .., "MWPM": ..}, ...}
    if isinstance(obj, dict) and obj and all(_floatkey(k) is not None for k in obj) and \
            all(isinstance(v, dict) for v in obj.values()):
        t = {float(k): {d: _num(x) for d, x in v.items() if _num(x) is not None and d not in SKIP_KEYS}
             for k, v in obj.items()}
        if any(t.values()):
            return t
    # layout B: [{"p": 0.005, "NN": .., "MWPM": ..}, ...]
    if isinstance(obj, list) and obj and all(isinstance(r, dict) for r in obj):
        t = {}
        for r in obj:
            pk = next((k for k in ("p", "eval_p", "physical_p", "physical_error_rate") if _num(r.get(k)) is not None), None)
            if pk is None:
                t = {}
                break
            t[float(r[pk])] = {d: _num(x) for d, x in r.items() if d != pk and d not in SKIP_KEYS and _num(x) is not None}
        if t and any(t.values()):
            return t
    # layout C: {"p": [..], "NN": [..], "MWPM": [..]}
    if isinstance(obj, dict) and isinstance(obj.get("p"), list):
        ps = obj["p"]
        t = {float(p): {} for p in ps}
        for k, v in obj.items():
            if k in SKIP_KEYS or not isinstance(v, list) or len(v) != len(ps):
                continue
            for p, x in zip(ps, v):
                if _num(x) is not None:
                    t[float(p)][k] = _num(x)
        if any(t.values()):
            return t
    # recurse
    children = obj.values() if isinstance(obj, dict) else obj if isinstance(obj, list) else []
    for c in children:
        if isinstance(c, (dict, list)):
            r = find_table(c)
            if r:
                return r
    return None


def describe(obj, depth=0, maxdepth=3):
    pad = "  " * depth
    if isinstance(obj, dict):
        for k, v in list(obj.items())[:15]:
            print(f"{pad}{k!r}: {type(v).__name__}" + (f" (len {len(v)})" if isinstance(v, (list, dict)) else f" = {v!r}"[:60]))
            if depth < maxdepth and isinstance(v, (dict, list)):
                describe(v, depth + 1, maxdepth)
    elif isinstance(obj, list) and obj:
        print(f"{pad}[0]: {type(obj[0]).__name__}")
        if depth < maxdepth and isinstance(obj[0], (dict, list)):
            describe(obj[0], depth + 1, maxdepth)


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log")
    ap.add_argument("--json")
    ap.add_argument("--key", help="dot path to the subtree of the JSON that holds the sweep")
    ap.add_argument("--n", type=int, default=20000, help="shots per p (for error bars)")
    ap.add_argument("--ref", default="NN", help="reference decoder for relative reductions")
    ap.add_argument("--out-dir", default="results/figs")
    ap.add_argument("--title", default="Logical error rate vs physical error rate")
    a = ap.parse_args()

    if bool(a.log) == bool(a.json):
        sys.exit("give exactly one of --log or --json")
    if a.log:
        table = parse_log(a.log)
    else:
        with open(a.json, encoding="utf-8") as f:
            obj = json.load(f)
        for part in (a.key.split(".") if a.key else []):
            obj = obj[int(part)] if isinstance(obj, list) else obj[part]
        table = find_table(obj)
        if not table:
            print("Could not find a {p: {decoder: rate}} table in the JSON. Structure (first levels):")
            describe(obj)
            sys.exit(1)
    table = {p: v for p, v in table.items() if v}
    if not table:
        sys.exit("no data parsed")
    ps = sorted(table)
    decs = []
    for p in ps:
        for d in table[p]:
            if d not in decs:
                decs.append(d)
    if a.ref not in decs:
        sys.exit(f"reference decoder {a.ref!r} not in {decs}")
    os.makedirs(a.out_dir, exist_ok=True)

    # ---- CSV
    with open(os.path.join(a.out_dir, "psweep.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["p", "n_shots"] + decs)
        for p in ps:
            w.writerow([p, a.n] + [table[p].get(d, "") for d in decs])

    # ---- Markdown table
    others = [d for d in decs if d != a.ref]
    lines = [f"Logical error rate (n = {a.n} shots per p; 95% Wilson intervals in the plot).", "",
             "| p | " + " | ".join(decs) + " |", "| --- | " + " | ".join("---" for _ in decs) + " |"]
    for p in ps:
        lines.append(f"| {p:g} | " + " | ".join(f"{table[p][d]:.4f}" if d in table[p] else "-" for d in decs) + " |")
    lines += ["", f"Relative reduction of {a.ref} vs each decoder, (other - {a.ref}) / other. "
                  "`*` = difference larger than ~2 standard errors (unpaired binomial approximation).", "",
              "| p | " + " | ".join(others) + " |", "| --- | " + " | ".join("---" for _ in others) + " |"]
    for p in ps:
        row = []
        r = table[p].get(a.ref)
        for d in others:
            o = table[p].get(d)
            if r is None or o is None or o == 0:
                row.append("-")
                continue
            se = math.sqrt(r * (1 - r) / a.n + o * (1 - o) / a.n)
            row.append(f"{(o - r) / o * 100:+.0f}%" + ("*" if abs(o - r) > 2 * se else ""))
        lines.append(f"| {p:g} | " + " | ".join(row) + " |")
    with open(os.path.join(a.out_dir, "psweep.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

    # ---- Plot
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    markers = "osv^Dp<>"
    for i, d in enumerate(decs):
        xs = [p for p in ps if d in table[p]]
        ys = [table[p][d] for p in xs]
        err = [[], []]
        for y in ys:
            lo, hi = wilson(round(y * a.n), a.n)
            err[0].append(max(y - lo, 0.0))
            err[1].append(max(hi - y, 0.0))
        ref = d == a.ref
        ax.errorbar(xs, ys, yerr=err, marker=markers[i % len(markers)], ms=6 if not ref else 8,
                    lw=2.4 if ref else 1.4, ls="--" if d.endswith("*") else "-", capsize=3, label=d,
                    zorder=5 if ref else 3)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(ps)
    ax.set_xticklabels([f"{p:g}" for p in ps])
    ax.minorticks_off()
    lo_, hi_ = ax.get_ylim()
    yt = [v for v in (0.001, 0.002, 0.003, 0.005, 0.007, 0.01, 0.02, 0.03, 0.05, 0.07, 0.1, 0.2, 0.3, 0.5)
          if lo_ * 0.95 <= v <= hi_ * 1.05]
    if len(yt) >= 2:
        ax.set_yticks(yt)
        ax.set_yticklabels([f"{v:g}" for v in yt])
    ax.set_xlabel("physical error rate p")
    ax.set_ylabel("logical error rate")
    ax.set_title(a.title)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    out = os.path.join(a.out_dir, "psweep.png")
    fig.savefig(out, dpi=160)
    print("wrote", out, "psweep.csv", "psweep.md")


if __name__ == "__main__":
    main()
