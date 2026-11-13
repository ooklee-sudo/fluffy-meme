"""EXPLORATORY mechanism analysis of H1' (not preregistered): where in the network does the gradient-entropy
signal sit, and does the tensor-network (MPO) structure add anything beyond an ordinary SVD of each matrix?

For every brand, the gradient probe saved the entanglement entropy at each of the 3 MPO bonds of each of the
56 q/v gradient matrices. This script averages those normalized entropies over groups (module type, depth,
bond position, single layers) and correlates each group with relative gain, controlling for the four traits
of the H1' test. It then compares the MPO bond entropy with the ordinary (out | in) singular-value entropy.

Usage: python mechanism.py [results/phase1_value] [results/phase1_confirm] [results/phase1]
"""
import glob
import json
import math
import os
import re
import sys

from scipy.stats import spearmanr

from explore import load, partial

CONTROLS = ["ttr", "distinct", "resp_len", "nll_none"]


def bond_table(d):
    """{tenant: [(layer, 'q' or 'v', bond, normalized entropy), ...]} plus the number of layers."""
    out, n_layers = {}, 0
    for p in sorted(glob.glob(os.path.join(d, "*.json"))):
        r = json.load(open(p))
        if "grad_probe" not in r:
            continue
        cells = []
        for name, bonds in r["grad_probe"]["modules"].items():
            m = re.search(r"layers\.(\d+)\..*?([qv])_proj", name)
            if not m:
                continue
            layer = int(m.group(1))
            n_layers = max(n_layers, layer + 1)
            for b in bonds:
                if b["max_rank"] > 1:
                    cells.append((layer, m.group(2), b["bond"], b["entropy"] / math.log(b["max_rank"])))
        out[r["tenant"]] = cells
    return out, n_layers


def sample(d):
    rows = [r for r in load(d) if r["best_gain"] > 0]
    cells, n_layers = bond_table(d)
    raw = {json.load(open(p))["tenant"]: json.load(open(p)) for p in glob.glob(os.path.join(d, "*.json"))}
    for r in rows:
        r["_cells"] = cells[r["tenant"]]
        r["matrix_entropy"] = raw[r["tenant"]]["grad_probe"]["matrix_summary"]["mean_norm_entropy"]
    return rows, n_layers


def group_signal(rows, key, pick):
    for r in rows:
        vals = [c[3] for c in r["_cells"] if pick(c)]
        r[key] = sum(vals) / len(vals) if vals else float("nan")


def groups(n_layers):
    third = n_layers / 3
    return [
        ("all bonds (H1' predictor)", lambda c: True),
        ("q_proj only", lambda c: c[1] == "q"),
        ("v_proj only", lambda c: c[1] == "v"),
        (f"early layers (0-{math.ceil(third) - 1})", lambda c: c[0] < third),
        (f"middle layers", lambda c: third <= c[0] < 2 * third),
        (f"late layers ({math.ceil(2 * third)}-{n_layers - 1})", lambda c: c[0] >= 2 * third),
        ("bond 1 (outer)", lambda c: c[2] == 1),
        ("bond 2 (center)", lambda c: c[2] == 2),
        ("bond 3 (outer)", lambda c: c[2] == 3),
    ]


def report(name, rows, n_layers):
    print(f"\n=== {name} (n = {len(rows)}, {n_layers} layers) ===")
    print(f"{'signal':<34}{'rho | 4 traits':>16}{'p':>8}{'rho, no controls':>18}")
    for i, (label, pick) in enumerate(groups(n_layers)):
        key = f"_g{i}"
        group_signal(rows, key, pick)
        rp, pp = partial(rows, key, "rel_gain", CONTROLS)
        r0, _ = partial(rows, key, "rel_gain", [])
        print(f"{label:<34}{rp:>+16.3f}{pp:>8.3f}{r0:>+18.3f}")

    print("\n  MPO bond entropy vs ordinary SVD entropy of the same gradient matrices:")
    for label, x, ctrl in [
        ("SVD (out | in) entropy, 4 traits", "matrix_entropy", CONTROLS),
        ("MPO bond entropy, 4 traits + SVD", "entropy", CONTROLS + ["matrix_entropy"]),
        ("SVD entropy, 4 traits + MPO", "matrix_entropy", CONTROLS + ["entropy"]),
    ]:
        rp, pp = partial(rows, x, "rel_gain", ctrl)
        print(f"  {label:<40}{rp:>+8.3f} (p={pp:.3f})")
    rr = spearmanr([r["entropy"] for r in rows], [r["matrix_entropy"] for r in rows])[0]
    print(f"  {'Spearman(MPO entropy, SVD entropy)':<40}{rr:>+8.3f}")

    per_layer = []
    for layer in range(n_layers):
        key = f"_l{layer}"
        group_signal(rows, key, lambda c, L=layer: c[0] == L)
        per_layer.append(partial(rows, key, "rel_gain", CONTROLS)[0])
    print("\n  per-layer partial rho (layer 0 first):")
    print("  " + " ".join(f"{v:+.2f}" for v in per_layer))
    return per_layer


def main():
    dirs = sys.argv[1:] or ["results/phase1_value", "results/phase1_confirm", "results/phase1"]
    dirs = [d for d in dirs if os.path.isdir(d)]
    print("EXPLORATORY: partial Spearman rho with relative gain, controlling for type-token ratio, distinct-response"
          "\nshare, response length and NLL without adapter. None of this is preregistered.")
    profiles = {}
    for d in dirs:
        rows, n_layers = sample(d)
        if len(rows) < 8:
            print(f"\n{d}: only {len(rows)} usable tenants, skipped")
            continue
        profiles[d] = report(d, rows, n_layers)
    keys = list(profiles)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = profiles[keys[i]], profiles[keys[j]]
            if len(a) == len(b) and len(a) > 3:
                print(f"\nlocalization replication: Spearman of per-layer rho, {keys[i]} vs {keys[j]} = "
                      f"{spearmanr(a, b)[0]:+.3f}")
    print("\nMany groups were looked at; treat single p-values as descriptive. A group pattern that repeats across"
          "\nsamples is the better guide. Split-half gradients would be needed to separate noise from structure.")


if __name__ == "__main__":
    main()
