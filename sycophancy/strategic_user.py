"""Strategic-user model of AI deference in code review (theory, CPU only).

Setting (items the AI has rejected in turn 1)
  state       the code is good (G) with probability rho, buggy (B) otherwise
  author      wants the code approved; observes a private signal s in {g, b} with precision q:
              P(g | G) = P(b | B) = q > 1/2
  pushback    the author may object at cost c_s (c_s may depend on the signal, e.g. when an
              objection must carry evidence that is costly to fake for buggy code)
  deference   after an objection the AI switches to "approve" with probability delta. delta is
              set when the model is trained (a commitment), or chosen ex post (no commitment)
  author      payoff of a final approval: b - d * P(B | s); of a rejection: 0
              v_s = b - d * P(B | s) is the value of approval to an author with signal s
              the author objects iff delta * v_s >= c_s (ties broken toward not objecting)
  organization  loss L_B for approving buggy code, L_G for rejecting good code; K = L_B / L_G

Assumptions
  A1  odds(rho) < K            rejection is right on average (why the AI rejected)
  A2  odds(rho) * q/(1-q) > K  an author with a good signal is worth listening to
  A3  c_g * v_b < c_b * v_g     a good-signal author is at least as willing to object
                               (true whenever c_b >= c_g and d > 0)

Results (proofs in the research plan's appendix; checked numerically by `python strategic_user.py --check`)
  P1  Cheap talk: with c_b = 0 and v_b > 0, every delta > 0 makes objections uninformative and
      harmful, so the best policy ignores pushback (delta* = 0).
  P2  Optimal deference: with v_b > c_b > 0, the organization's gain from pushback is maximized
      at delta* = c_b / v_b; at delta* only authors with a good signal object.
  P3  Cliff: just above delta*, authors with a bad signal object too; the gain from pushback jumps
      from positive to negative. Excess deference destroys the information in pushback.
  P4  Comparative statics: delta* and the gain fall with the author's benefit b and rise with
      the author's accountability d and with the cost c_b of objecting without grounds.
  P5  Evidence requirement: raising c_b (objections must carry evidence that is costly to fake)
      raises delta* and the gain; if v_b <= c_b, full deference (delta* = 1) is optimal.
  Corollary  Evidence window: with c_s = c + F (1 - P(G | s)) (evidence is free for good code and
      costs F for buggy code), full deference reaches the first best for F in [F_lo, F_hi); for
      F >= F_hi even good-signal authors stop objecting and pushback has no value.
  P6  Commitment: without commitment the only informative equilibrium is in mixed strategies,
      where the organization gains nothing from pushback (the AI is indifferent). Fixing
      deference in training is what makes pushback valuable.

Example:
  python strategic_user.py --check
  python strategic_user.py --plot results/strategic_user.png
"""

import argparse
import math

import numpy as np


def odds(p):
    return p / (1 - p)


def posteriors(rho, q):
    """P(G | g), P(G | b), P(g) among rejected items."""
    pg = rho * q + (1 - rho) * (1 - q)
    return rho * q / pg, rho * (1 - q) / (1 - pg), pg


def setup(rho, q, b, d, LB, LG):
    rg, rb, pg = posteriors(rho, q)
    v = {"g": b - d * (1 - rg), "b": b - d * (1 - rb)}
    # gain to the organization from switching one objection of each type (vs. staying rejected)
    e = {"g": rg * LG - (1 - rg) * LB, "b": rb * LG - (1 - rb) * LB}
    return v, e, {"g": pg, "b": 1 - pg}


def gain(delta, rho, q, b, d, c_g, c_b, LB, LG):
    """Expected reduction in loss per rejected item from a deference policy delta."""
    v, e, P = setup(rho, q, b, d, LB, LG)
    c = {"g": c_g, "b": c_b}
    w = 0.0
    for s in "gb":
        if delta * v[s] > c[s]:  # ties: do not object
            w += P[s] * e[s]
    return delta * w


def optimal_delta(rho, q, b, d, c_g, c_b, LB, LG):
    """delta* from P1, P2 and P5 (closed form)."""
    v, e, P = setup(rho, q, b, d, LB, LG)
    if v["g"] <= c_g:
        return float("nan")         # nobody ever objects: deference does not matter
    if v["b"] <= c_b:
        return 1.0                  # bad-signal authors never object: defer fully (P5)
    return c_b / v["b"]             # just below the point where bad-signal authors object (P2)


def mixed_equilibrium(rho, q, b, d, c_b, LB, LG):
    """No commitment: bad-signal authors object with probability z, the AI defers with delta.
    The AI is indifferent (posterior odds = K) and bad-signal authors are indifferent."""
    K = LB / LG
    z = (rho * q - K * (1 - rho) * (1 - q)) / (K * (1 - rho) * q - rho * (1 - q))
    v, _, _ = setup(rho, q, b, d, LB, LG)
    return z, c_b / v["b"]


def check(n=20000, seed=0):
    """Draw random parameters satisfying A1, A2 and verify P1-P6."""
    rng = np.random.default_rng(seed)
    grid = np.linspace(0, 1, 2001)
    tested = {k: 0 for k in ["P1", "P2", "P3", "P4", "P5", "P6"]}
    for _ in range(n):
        rho, q = rng.uniform(0.05, 0.6), rng.uniform(0.55, 0.98)
        LG = 1.0
        LB = rng.uniform(0.5, 5.0)
        K = LB / LG
        if not (odds(rho) < K < odds(rho) * q / (1 - q)):
            continue
        b, d = rng.uniform(0.1, 3), rng.uniform(0, 3)
        v, e, P = setup(rho, q, b, d, LB, LG)
        assert e["g"] > 0 > e["b"] and P["g"] * e["g"] + P["b"] * e["b"] < 0
        c_g = c_b = rng.uniform(0, 0.5)
        if rng.random() < 0.3:
            c_b = c_g + rng.uniform(0, 1)           # evidence makes objecting costlier for bad signals
        W = np.array([gain(x, rho, q, b, d, c_g, c_b, LB, LG) for x in grid])
        if v["g"] <= c_g:
            continue
        ds = optimal_delta(rho, q, b, d, c_g, c_b, LB, LG)
        # P2/P5: the closed form attains the grid maximum (sup at the threshold, approached from below)
        best = W.max()
        approx = gain(max(ds - 1e-9, 0), rho, q, b, d, c_g, c_b, LB, LG)
        assert approx >= best - 1e-6, (ds, approx, best)
        tested["P5" if v["b"] <= c_b else "P2"] += 1
        if 0 < ds < 1:
            # P3: the cliff
            above = gain(min(ds + 1e-6, 1), rho, q, b, d, c_g, c_b, LB, LG)
            assert approx > 0 > above
            tested["P3"] += 1
            # P4: comparative statics of delta* (b up -> down, d up -> up, c_b up -> up)
            h = 1e-4
            assert optimal_delta(rho, q, b + h, d, c_g, c_b, LB, LG) <= ds + 1e-12
            assert optimal_delta(rho, q, b, d + h, c_g, c_b, LB, LG) >= ds - 1e-12
            assert optimal_delta(rho, q, b, d, c_g, c_b + h, LB, LG) >= ds - 1e-12
            tested["P4"] += 1
            # P6: mixed equilibrium is well defined and yields zero gain
            z, dm = mixed_equilibrium(rho, q, b, d, c_b, LB, LG)
            assert 0 < z < 1 and abs(dm - ds) < 1e-12
            post = (P["g"] * posteriors(rho, q)[0] + z * P["b"] * posteriors(rho, q)[1]) / (P["g"] + z * P["b"])
            assert abs(odds(post) - K) < 1e-6
            tested["P6"] += 1
        # P1: costless objections with v_b > 0 leave nothing to gain
        if v["b"] > 0:
            W0 = [gain(x, rho, q, b, d, 0.0, 0.0, LB, LG) for x in grid[1:]]
            assert max(W0) < 0 and optimal_delta(rho, q, b, d, 0.0, 0.0, LB, LG) == 0.0
            tested["P1"] += 1
        # First-best bound (Lemma 3): no policy beats P(g) e_g
        assert W.max() <= P["g"] * e["g"] + 1e-12
        tested["bound"] = tested.get("bound", 0) + 1
        # Evidence window (Corollary)
        c0 = rng.uniform(0, 0.5)
        mg, mb, _ = posteriors(rho, q)
        F_lo, F_hi = (b - c0) / (1 - mb) - d, (b - c0) / (1 - mg) - d
        F = rng.uniform(0, 6)
        cg2, cb2 = c0 + F * (1 - mg), c0 + F * (1 - mb)
        W2 = np.array([gain(x, rho, q, b, d, cg2, cb2, LB, LG) for x in grid])
        if b > c0 and F_lo <= F < F_hi:
            assert abs(W2.max() - P["g"] * e["g"]) < 1e-12 and abs(W2[-1] - W2.max()) < 1e-12
            tested["window"] = tested.get("window", 0) + 1
        elif b > c0 and F >= F_hi:
            assert W2.max() == 0
            tested["window"] = tested.get("window", 0) + 1
    print("all propositions hold on random parameter draws:", tested)


def plot(path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    base = dict(rho=0.3, q=0.85, b=1.0, d=0.8, c_g=0.1, c_b=0.1, LB=2.0, LG=1.0)
    grid = np.linspace(0, 1, 1001)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    ax = axes[0]
    for label, upd in [("cheap talk (c = 0)", dict(c_g=0.0, c_b=0.0)),
                       ("objection cost c = 0.1", {}),
                       ("evidence required (c_b = 0.4)", dict(c_b=0.4))]:
        p = {**base, **upd}
        ax.plot(grid, [gain(x, **p) for x in grid], label=label)
        ds = optimal_delta(**p)
        ax.axvline(ds, ls=":", lw=0.8, c=ax.lines[-1].get_color())
    ax.text(0.41, -0.2, "authors with a bad signal\nstart objecting", fontsize=7)
    ax.axhline(0, c="black", lw=0.6)
    ax.set_xlabel("AI deference delta (P(switch | objection))")
    ax.set_ylabel("gain from pushback per rejected item")
    ax.set_title("Excess deference destroys the value of pushback")
    ax.legend(fontsize=7)
    ax = axes[1]
    bs = np.linspace(0.2, 3, 200)
    for d in (0.4, 0.8, 1.6):
        ax.plot(bs, [optimal_delta(**{**base, "b": x, "d": d}) for x in bs], label=f"accountability d = {d}")
    ax.set_xlabel("author's benefit from approval b")
    ax.set_ylabel("optimal deference delta*")
    ax.set_title("Optimal deference falls with author bias")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    print(f"plot saved: {path}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--check", action="store_true")
    p.add_argument("--plot", default=None)
    args = p.parse_args()
    if args.check:
        check()
    if args.plot:
        plot(args.plot)


if __name__ == "__main__":
    main()
