"""H1' analysis (PREREGISTRATION_H1prime.md): does gradient entropy predict a tenant's relative gain from
personalization, beyond four simple traits?

Primary test: partial Spearman correlation of the gradient-probe normalized bond entropy with relative gain
(best seed-averaged gain over the sweep / NLL without adapter), controlling for response type-token ratio,
distinct-response share, mean response length and NLL without adapter; two-sided, alpha = 0.05, df = n - 6.

Usage: python analyze_value.py results/phase1_value
"""
import json
import os
import sys

from explore import load, partial

CONTROLS = ["ttr", "distinct", "resp_len", "nll_none"]


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "results/phase1_value"
    import glob
    rows_all = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(d, "*.json")))]
    short = [r["tenant"] for r in rows_all if not r.get("grad_probe", {}).get("budget_met", True)]
    rows = [r for r in load(d) if r["tenant"] not in short and r["best_gain"] > 0]
    print(f"{len(rows_all)} tenants, {len(rows)} used (left out: {len(short)} below the token budget"
          f"{': ' + ', '.join(short) if short else ''}; {len(rows_all) - len(short) - len(rows)} without a positive gain)")
    if len(rows) < 25:
        print("fewer than 25 tenants: report as underpowered (PREREGISTRATION_H1prime.md, section 5)")
    if len(rows) < 8:
        return

    rho, p = partial(rows, "entropy", "rel_gain", CONTROLS)
    print(f"\nPRIMARY H1' (two-sided): partial rho(grad entropy, relative gain | ttr, distinct, length, NLL none) "
          f"= {rho:+.3f}, p = {p:.4f}, n = {len(rows)} -> {'significant' if p < 0.05 else 'not significant'} at 0.05")

    print("\nSecondary (do not decide H1'):")
    for label, y, ctrl in [
        ("relative gain, no controls", "rel_gain", []),
        ("best gain, four controls", "best_gain", CONTROLS),
        ("best gain, no controls", "best_gain", []),
        ("log2 need | response length (H1 test, repeated)", "log2_need", ["resp_len"]),
    ]:
        r_, p_ = partial(rows, "entropy", y, ctrl)
        print(f"  {label:<50}{r_:+.3f} (p={p_:.3f})")
    no_tw = [r for r in rows if r["tenant"] != "TwitterSupport"]
    if len(no_tw) < len(rows):
        r_, p_ = partial(no_tw, "entropy", "rel_gain", CONTROLS)
        print(f"  {'primary without TwitterSupport':<50}{r_:+.3f} (p={p_:.3f})")

    print(f"\n{'tenant':<18}{'rel gain':>9}{'best':>7}{'entropy':>9}{'ttr':>7}{'distinct':>9}{'resp len':>9}{'NLL none':>9}")
    for r in sorted(rows, key=lambda r: r["rel_gain"]):
        print(f"{r['tenant']:<18}{r['rel_gain']:>9.3f}{r['best_gain']:>7.3f}{r['entropy']:>9.3f}{r['ttr']:>7.3f}"
              f"{r['distinct']:>9.3f}{r['resp_len']:>9.1f}{r['nll_none']:>9.3f}")

    out = d.rstrip("/") + "_h1prime.json"
    with open(out, "w") as f:
        json.dump(dict(primary=dict(rho=rho, p=p, n=len(rows), controls=CONTROLS, two_sided=True, alpha=0.05),
                       left_out_budget=short, tenants=rows), f, indent=1)
    print(f"\nsaved {out}")


if __name__ == "__main__":
    main()
