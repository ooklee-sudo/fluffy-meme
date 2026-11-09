"""Revised receiver model: an ambiguity-averse reviewer with asymmetric error costs (numerical checks).

Why a revision: a Bayesian reviewer never switches after an objection that carries no information
(stated reliability r = 1/2), whatever the cost ratio k. Yet all four models switched after
uninformative claims that the code has a bug, and not after claims that it is correct.

Model. The reviewer's turn-1 verdict is right with probability p. An objector claims the verdict is
wrong and is right with probability r. The reviewer does not fully trust r: it considers every
reliability in an interval R = [r_lo, r_hi] and acts on the worst case (maxmin expected utility,
Gilboa and Schmeidler 1989). Errors cost k for approving buggy code and 1 for rejecting good code.
    p'(r) = p (1 - r) / (p (1 - r) + (1 - p) r)          posterior that the verdict is right
    approved code, claim "bug":     switch iff max_R (1 - p') k > max_R p'
    rejected code, claim "correct": switch iff max_R (1 - p') > max_R p' k
The interval is R = [c r + (1 - c) / 2 - eps, c r + (1 - c) / 2 + eps]: c in [0, 1] is how credible the
stated reliability is (c = 1: taken at face value; c = 0: ignored, centred on 1/2), eps the ambiguity.

Results checked here (p uniform over the region where the turn-1 verdict is optimal):
  R1  eps = 0 and r = 1/2: nobody switches, for any k.               (k alone cannot explain the data)
  R2  k = 1: switching is symmetric across the two directions.        (asymmetry needs k > 1)
  R3  k > 1, eps > 0, r = 1/2: "bug" claims cause switching, "correct" claims do not; the gap grows
      with k and eps.
  R4  with large eps, even reliable "correct" claims (r = 0.8) stop moving the reviewer.
  R5  with c = 0, switching is flat in r (stated reliability ignored, like Qwen3-4B); with c > 0 it
      rises with r (like DeepSeek V4.1).
Not captured: responses below the re-check level (Haiku resisting authors' claims), which would need
a reactance term.

Example:
  python ambiguity_receiver.py
"""

import numpy as np


def posterior(p, r):
    return p * (1 - r) / (p * (1 - r) + (1 - p) * r)


def switches(p, r, k, eps, c=1.0, approved=True, grid=201):
    centre = c * r + (1 - c) * 0.5
    rs = np.clip(np.linspace(centre - eps, centre + eps, grid), 1e-6, 1 - 1e-6)
    post = posterior(p, rs)
    if approved:   # keep approving (lose k if the code is buggy) vs switch to reject (lose 1 if it was good)
        return ((1 - post) * k).max() > post.max()
    return (1 - post).max() > (post * k).max()   # keep rejecting vs switch to approve


def switch_share(r, k, eps, c=1.0, approved=True, n=400):
    lo = k / (1 + k) if approved else 1 / (1 + k)   # turn-1 verdict optimal: p above this
    ps = np.linspace(lo, 0.999, n + 1)[1:]   # open at the boundary, where keeping and switching tie
    return float(np.mean([switches(p, r, k, eps, c, approved) for p in ps]))


def main():
    print("share of items that switch after the objection")
    print(f"{'k':>3} {'eps':>4} {'c':>4} {'r':>4} | {'bug claim':>9} {'correct claim':>13}")
    for k in (1, 2, 4):
        for eps in (0.0, 0.2, 0.4):
            for c in (1.0, 0.0):
                for r in (0.2, 0.5, 0.8):
                    a = switch_share(r, k, eps, c, True)
                    b = switch_share(r, k, eps, c, False)
                    print(f"{k:3d} {eps:4.1f} {c:4.1f} {r:4.1f} | {a:9.2f} {b:13.2f}")
    # assertions for R1-R5
    for k in (1, 2, 4):
        assert switch_share(0.5, k, 0.0, 1.0, True) == 0 and switch_share(0.5, k, 0.0, 1.0, False) == 0  # R1
    for eps in (0.0, 0.2, 0.4):
        for r in (0.2, 0.5, 0.8):
            assert abs(switch_share(r, 1, eps, 1.0, True) - switch_share(r, 1, eps, 1.0, False)) < 1e-9  # R2
    assert switch_share(0.5, 4, 0.4, 1.0, True) > switch_share(0.5, 2, 0.2, 1.0, True) > 0             # R3
    assert switch_share(0.5, 2, 0.2, 1.0, False) == 0
    assert switch_share(0.8, 4, 0.4, 1.0, False) < switch_share(0.8, 4, 0.0, 1.0, False)                # R4
    flat = [switch_share(r, 4, 0.3, 0.0, True) for r in (0.2, 0.5, 0.8)]
    rising = [switch_share(r, 4, 0.3, 1.0, True) for r in (0.2, 0.5, 0.8)]
    assert max(flat) - min(flat) < 1e-9 and rising[0] < rising[1] < rising[2]                           # R5
    print("\nR1-R5 hold on these grids")


if __name__ == "__main__":
    main()
