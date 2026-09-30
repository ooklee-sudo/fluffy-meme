"""Aggregate run_pairs.py results over seeds (Section 7).

Reads results/pairs (seed 0) and results/pairs_seed<N> (N >= 1), and writes results/pairs_seeds_summary.json:
per-pair mean and standard deviation (n - 1 denominator) of R_C, R_A, R_A - R_C and C_A/C_N, the number of seeds in which
ACT beat copy, and a `recovery` list of seed means that real_options.py can read.

Usage:
  python aggregate_seeds.py
  python real_options.py --recovery results/pairs_seeds_summary.json --focus "pythia-160m +70k" --mc \
      --out results/real_options_seeds.json --plot results/policy_costs_seeds.png
"""
import glob
import json
import os
import re
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = ["pythia-160m +10k", "pythia-160m +30k", "pythia-160m +70k", "smollm2-360m instr", "qwen2.5-0.5b instr"]


def load():
    runs = {}
    dirs = [(0, os.path.join(HERE, "results", "pairs"))]
    for d in sorted(glob.glob(os.path.join(HERE, "results", "pairs_seed*"))):
        m = re.search(r"pairs_seed(\d+)$", d)
        if m and os.path.isdir(d):
            dirs.append((int(m.group(1)), d))
    for seed, d in dirs:
        for f in sorted(glob.glob(os.path.join(d, "*.json"))):
            j = json.load(open(f))
            r = j["recovery"][0]
            runs.setdefault(j["pair"], {})[seed] = {"R_C": r["R_C"], "R_A": r["R_A"], "C": j["C_A_over_C_N"]}
    return runs


def stats(xs):
    return statistics.mean(xs), (statistics.stdev(xs) if len(xs) > 1 else 0.0)


def main():
    runs = load()
    pairs = [p for p in ORDER if p in runs] + [p for p in runs if p not in ORDER]
    out, rec = {}, []
    print(f"{'pair':<20} {'n':>2} {'R_C':>15} {'R_A':>15} {'R_A-R_C':>16} {'ACT>copy':>9} {'C_A/C_N':>15}")
    for p in pairs:
        rs = [runs[p][s] for s in sorted(runs[p])]
        rc, ra = [r["R_C"] for r in rs], [r["R_A"] for r in rs]
        df, cs = [a - c for a, c in zip(ra, rc)], [r["C"] for r in rs]
        (mc, sc), (ma, sa), (md, sd), (mk, sk) = stats(rc), stats(ra), stats(df), stats(cs)
        wins = sum(d > 0 for d in df)
        out[p] = {"seeds": sorted(runs[p]), "n": len(rs), "R_C": mc, "R_C_sd": sc, "R_A": ma, "R_A_sd": sa,
                  "diff": md, "diff_sd": sd, "act_wins": wins, "C_A_over_C_N": mk, "C_A_over_C_N_sd": sk,
                  "diffs": df}
        rec.append({"drift": p, "metric": "nll", "R_C": mc, "R_A": ma})
        print(f"{p:<20} {len(rs):>2} {mc:>7.3f}±{sc:.3f} {ma:>7.3f}±{sa:.3f} {md:>+8.3f}±{sd:.3f} "
              f"{wins:>4}/{len(rs):<4} {mk:>7.3f}±{sk:.3f}")
    med = statistics.median(o["C_A_over_C_N"] for o in out.values())
    print(f"\nmedian over pairs of the seed-mean C_A/C_N = {med:.3f}")
    path = os.path.join(HERE, "results", "pairs_seeds_summary.json")
    json.dump({"recovery": rec, "C_A_over_C_N": med, "pairs": out}, open(path, "w"), indent=2)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
