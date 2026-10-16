"""Bootstrap confidence intervals for the pilot grid (no API calls).

  python analyze_runs.py --runs runs --boot 2000

Reads runs/*/raw_counts.csv and config.json. Resamples customers within each (model, anchor, condition)
cell, pooling temperatures for models that accept temperature (the grid showed no systematic temperature
effect; pass --by-temp to keep them apart). A trailing * marks a CI that excludes the reference value
(retail: Retail II NB mean 0.49, alpha 3.05; grocery: Complete Journey histogram).
"""
import argparse, glob, json, os
import numpy as np, pandas as pd

import run_pilot as rp

REF = {}  # filled from the runs' scenario (retail: parametric NB; grocery: Complete Journey histogram)


def stats_of(x):
    m, v = x.mean(), x.var(ddof=1)
    return dict(mean=m, var_mean=v / m if m > 0 else np.nan, zero=(x == 0).mean(),
                alpha=(v - m) / m**2 if m > 0 else np.nan)


def boot(x, B, rng):
    out = {k: [] for k in REF}
    n = len(x)
    for _ in range(B):
        s = stats_of(x[rng.integers(0, n, n)])
        for k in out:
            out[k].append(s[k])
    return {k: np.nanpercentile(v, [2.5, 97.5]) if np.isfinite(v).any() else (np.nan, np.nan) for k, v in out.items()}


def fmt(k, est, ci):
    if not np.isfinite(est):
        return "n/a"
    star = "*" if np.isfinite(ci[0]) and not (ci[0] <= REF[k] <= ci[1]) else ""
    return f"{est:.2f} [{ci[0]:.2f},{ci[1]:.2f}]{star}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--by-temp", action="store_true")
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    frames = []
    for d in sorted(glob.glob(os.path.join(a.runs, "*"))):
        f, c = os.path.join(d, "raw_counts.csv"), os.path.join(d, "config.json")
        if not (os.path.exists(f) and os.path.exists(c)):
            continue
        cfg = json.load(open(c))
        REF.update(rp.ref_stats(rp.get_scenario(cfg.get("scenario", "retail"))))
        df = pd.read_csv(f)
        df["model"], df["anchor"], df["temp"] = cfg["model"], bool(cfg["anchor"]), cfg["temp"]
        frames.append(df)
    if not frames:
        raise SystemExit(f"no finished runs in {a.runs}")
    df = pd.concat(frames)
    df = df[df.cond != "real(ref)"]
    keys = ["model", "anchor", "cond"] + (["temp"] if a.by_temp else [])
    rows, fail = [], []
    for k, g in df.groupby(keys):
        x = g["count"].dropna().astype(float).values
        rec = dict(zip(keys, k))
        rec["n"] = len(x)
        rec["parse_fail"] = round(1 - len(x) / len(g), 3)
        if len(x) < 20:
            rows.append(rec); continue
        est, ci = stats_of(x), boot(x, a.boot, rng)
        for m in REF:
            rec[m] = fmt(m, est[m], ci[m])
        rows.append(rec)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(a.runs, "ci_summary.csv"), index=False)
    print(f"reference: mean {REF['mean']:.2f}, var/mean {REF['var_mean']:.2f}, zero {REF['zero']:.2f}, alpha {REF['alpha']:.2f}")
    print("estimate [95% bootstrap CI]; * = CI excludes the reference\n")
    print(out.to_string(index=False))
    print(f"\nsaved {os.path.join(a.runs, 'ci_summary.csv')}")


if __name__ == "__main__":
    main()
