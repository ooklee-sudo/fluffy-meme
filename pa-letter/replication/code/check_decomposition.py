"""Check the misclassification decomposition in Table 2 and SI Table S3.

Equation (1): mu_M(e) = sum_h pi(h|e) * mu(h, e)
Equation (2): mu_M(e) - mu_H(e) = pi(e|e)[mu(e,e) - mu_H(e)]
                                  + sum_{h != e} pi(h|e)[mu(h,e) - mu_H(e)]

Inputs are the published cell counts and cell means (percent, signed in the
direction of the model's class). The script recomputes the model-label mean
and every term of equation (2) and checks them against the published values
to within rounding.
"""

CELLS = {
    # (class, label set): {human label: (count, mean)}, human estimate, published terms
    ("escalation", "Model 1"): {
        "cells": {"same": (8, 0.52), "deescalation": (6, -0.51), "mixed": (7, 0.52), "other": (3, -0.21)},
        "human": 0.45, "published": {"mean": 0.17, "gap": -0.28, "same": 0.02,
                                      "deescalation": -0.24, "mixed": 0.02, "other": -0.08},
    },
    ("escalation", "v2 majority"): {
        "cells": {"same": (9, 0.44), "deescalation": (4, -0.75), "mixed": (12, 0.68), "other": (5, 0.09)},
        "human": 0.45, "published": {"mean": 0.32, "gap": -0.13, "same": 0.00,
                                      "deescalation": -0.16, "mixed": 0.09, "other": -0.06},
    },
    ("de-escalation", "Model 1"): {
        "cells": {"same": (25, 1.07), "escalation": (0, 0.0), "mixed": (5, 0.38), "other": (4, 0.51)},
        "human": 0.94, "published": {"mean": 0.90, "gap": -0.04, "same": 0.09,
                                      "escalation": 0.00, "mixed": -0.08, "other": -0.05},
    },
    ("de-escalation", "v2 majority"): {
        "cells": {"same": (26, 0.99), "escalation": (0, 0.0), "mixed": (3, 1.23), "other": (4, 0.51)},
        "human": 0.94, "published": {"mean": 0.95, "gap": 0.01, "same": 0.03,
                                      "escalation": 0.00, "mixed": 0.03, "other": -0.05},
    },
}

# Cell means are published to two decimals, so recomputed terms can differ from
# the published ones by rounding; 0.015 allows for that.
TOL = 0.015


def decompose(cells, human):
    n = sum(c for c, _ in cells.values())
    mean = sum(c * m for c, m in cells.values()) / n
    terms = {h: c / n * (m - human) for h, (c, m) in cells.items()}
    return n, mean, mean - human, terms


def main():
    ok = True
    for (cls, labels), spec in CELLS.items():
        n, mean, gap, terms = decompose(spec["cells"], spec["human"])
        pub = spec["published"]
        print(f"\n{cls} | {labels} | n = {n}")
        print(f"  mean, eq. (1): {mean:+.3f}  (published {pub['mean']:+.2f})")
        print(f"  gap, eq. (2):  {gap:+.3f}  (published {pub['gap']:+.2f})")
        checks = [("mean", mean), ("gap", gap)] + list(terms.items())
        for name, value in terms.items():
            print(f"    {name:<13} {value:+.3f}  (published {pub[name]:+.2f})")
        assert abs(sum(terms.values()) - gap) < 1e-9  # equation (2) is an identity
        for name, value in checks:
            if abs(value - pub[name]) > TOL:
                ok = False
                print(f"  MISMATCH: {name} recomputed {value:+.3f}, published {pub[name]:+.2f}")
    print("\nAll published values reproduced within rounding." if ok else "\nSome values did not match.")
    return ok


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
