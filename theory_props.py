"""Propositions (numerically verified) and strategic extensions for flat vs. phase-dependent pricing.

Quasi-static model of theory_check.py: phase k has probability pi_k, linear demand potential Lam_k, and an M/M/c
queue at the phase's request rate; users face price p_k, see the phase, and join iff value > p_k + d(lam).

Notation: d(l) = mean sojourn (Erlang-C), D(l) = l d(l) total delay cost rate, t(l) = D'(l) - d(l) = l d'(l)
(Pigouvian toll), W_k(p) = welfare of phase k when users face price p, kappa_k(p) = -d lam_k / dp > 0.

P1  t(l) strictly increasing, and the first-best rate / toll are strictly increasing in Lam_k.
P2  dW_k/dp = -kappa_k(p) (p - t(lam_k(p))): exact; so the optimal flat price solves
        sum_k pi_k kappa_k(p)(p - t(lam_k(p))) = 0     (kappa-weighted average of phase tolls)
    and lies between the smallest and largest phase toll.  Flat pricing is first best iff all Lam_k are equal.
P3  Exact loss of flat price p:  sum_k pi_k * Int_{p}^{p_k*} kappa_k(s) (t(lam_k(s)) - s) ds  >= 0.
P4  Burst-blind pricing: a provider who prices as if every phase had the mean potential sets p_blind = t(lam*(mean
    Lam)).  By Jensen, p_blind is below the average phase toll when Lam -> t(lam*(Lam)) is convex and above it when
    concave: the DIRECTION of the burst-blind pricing error depends on curvature (checked numerically; it is NOT
    always underpricing).
S1  Delay-cost heterogeneity (two user classes, v = 0.5 and 2): flat-vs-phase loss persists.
S2  Duopoly (logit, beta=1; each firm has c servers, market demand doubled): equilibrium flat vs phase pricing.
Usage: python theory_props.py DATA_DIR [OUT.md]"""
import sys

import numpy as np

import theory_check as th

P = th.P
sojourn, eq_rate, w_phase, first_best = th.sojourn, th.eq_rate, th.w_phase, th.first_best


def toll_at(l, c, h=1e-5):
    return l * (sojourn(l + h, c) - sojourn(max(l - h, 0), c)) / (h + min(h, l))


def kappa(p, Lam, c, h=5e-3):
    return -(eq_rate(p + h, Lam, c) - eq_rate(max(p - h, 0), Lam, c)) / (h + min(h, p))


def W_of_p(p, Lam, c):
    return w_phase(eq_rate(p, Lam, c), Lam, c)


def phase_optimal_price(Lam, c):
    lfb = first_best(Lam, c)
    return toll_at(lfb, c), lfb


def check_props(Lams, pis, c, md, label):
    Lams, pis = np.asarray(Lams, float), np.asarray(pis, float)
    K = len(Lams)
    # P1
    grid = np.linspace(0.3, 3.0, 12) * c
    lstar = [first_best(L, c) for L in grid]
    tstar = [toll_at(l, c) for l in lstar]
    p1 = bool(np.all(np.diff(lstar) > 0) and np.all(np.diff(tstar) > 0))
    # convexity of Lam -> t(lam*(Lam)) over the range used
    d2 = np.diff(tstar, 2)
    convex = bool(np.all(d2 > -1e-9))
    # P2: derivative identity at several prices
    errs = []
    for p in (1.0, 3.0, 6.0, 9.0):
        num = (sum(pis[k] * W_of_p(p + 1e-3, Lams[k], c) for k in range(K))
               - sum(pis[k] * W_of_p(p - 1e-3, Lams[k], c) for k in range(K))) / 2e-3
        ana = -sum(pis[k] * kappa(p, Lams[k], c) * (p - toll_at(eq_rate(p, Lams[k], c), c)) for k in range(K))
        errs.append((p, num, ana))
    # optimal flat price and its bracket
    best = max((sum(pis[k] * W_of_p(p, Lams[k], c) for k in range(K)), p) for p in np.linspace(0, P, 801))
    pflat = best[1]
    tk = np.array([toll_at(first_best(L, c), c) for L in Lams])
    # P3: exact loss integral
    pk_star = tk  # phase-k optimal price = first-best toll
    loss_direct = sum(pis[k] * (W_of_p(pk_star[k], Lams[k], c) - W_of_p(pflat, Lams[k], c)) for k in range(K))
    loss_int = 0.0
    for k in range(K):
        s = np.linspace(pflat, pk_star[k], 201)
        f = np.array([kappa(x, Lams[k], c) * (toll_at(eq_rate(x, Lams[k], c), c) - x) for x in s])
        loss_int += pis[k] * float(np.trapezoid(f, s))
    # P4: burst-blind price
    Lm = float(pis @ Lams)
    p_blind = toll_at(first_best(Lm, c), c)
    md.append(f"### {label}\n")
    md.append(f"- P1 first-best rate and toll strictly increasing in demand potential: **{p1}**; "
              f"Lam -> t(lam*(Lam)) convex on [0.3c, 3c]: **{convex}**")
    md.append("- P2 derivative identity dW/dp = -sum pi kappa (p - t): " +
              "; ".join(f"p={p:g}: numeric {n:.3f} vs formula {a:.3f}" for p, n, a in errs))
    md.append(f"- P2 phase tolls at first best: {np.round(tk, 2).tolist()}; optimal flat price {pflat:.2f} "
              f"(inside [{tk.min():.2f}, {tk.max():.2f}]: {tk.min() - 1e-9 <= pflat <= tk.max() + 1e-9})")
    md.append(f"- P3 exact loss: direct {loss_direct:.4f} vs integral formula {loss_int:.4f}")
    md.append(f"- P4 burst-blind price (first-best toll at mean potential) {p_blind:.2f} vs kappa-weighted optimum "
              f"flat {pflat:.2f} vs mean of phase tolls {float(pis @ tk):.2f} -> blind price is "
              f"{'above' if p_blind > pflat else 'below'} the optimal flat price\n")
    print("\n".join(md[-8:]), flush=True)


# ---------------------------------------------------------------- S1 heterogeneity
def eq_het(p, Lams_j, vs, c):
    """Classes j with potentials Lams_j and delay-cost multipliers vs; common sojourn d(sum lam)."""
    lo, hi = 0.0, min(sum(Lams_j), c - 1e-9)
    f = lambda L: sum(Lj * max(0.0, 1 - (p + v * sojourn(L, c)) / P) for Lj, v in zip(Lams_j, vs)) - L
    if f(hi) >= 0:
        return hi
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
    return (lo + hi) / 2


def w_het(p, Lams_j, vs, c):
    L = eq_het(p, Lams_j, vs, c)
    d = sojourn(L, c)
    tot = 0.0
    for Lj, v in zip(Lams_j, vs):
        lj = Lj * max(0.0, 1 - (p + v * d) / P)
        tot += P * (lj - lj ** 2 / (2 * Lj)) - v * lj * d
    return tot


def s1(Lams, pis, c, md, label):
    vs = (0.5, 2.0)
    share = (0.5, 0.5)
    grid = np.linspace(0, P, 401)
    K = len(Lams)
    ph = [max((w_het(p, [s * Lams[k] for s in share], vs, c), p) for p in grid) for k in range(K)]
    wph = sum(pis[k] * ph[k][0] for k in range(K))
    flat = max((sum(pis[k] * w_het(p, [s * Lams[k] for s in share], vs, c) for k in range(K)), p) for p in grid)
    md.append(f"- {label}: heterogeneous delay costs (v = 0.5 / 2, 50:50): phase-dependent welfare {wph:.2f} "
              f"(prices {', '.join(f'{x[1]:.1f}' for x in ph)}), best flat {flat[0]:.2f} (p={flat[1]:.1f}), "
              f"flat loss {100 * (wph - flat[0]) / abs(wph):.1f}%")
    print(md[-1], flush=True)


# ---------------------------------------------------------------- S2 duopoly
def duopoly_rates(p1, p2, Lam, c, beta=1.0):
    lam = np.array([0.4, 0.4]) * min(Lam, 2 * c)
    lam = np.minimum(lam, c - 1e-6)
    p = np.array([p1, p2], float)
    for _ in range(120):
        x = p + np.array([sojourn(l, c) for l in lam])
        e = np.exp(-beta * (x - x.min()))
        s = e / e.sum()
        xbar = x.min() - np.log(e.sum()) / beta
        D = Lam * max(0.0, 1 - xbar / P)
        new = np.minimum(s * D, c - 1e-6)
        if np.abs(new - lam).max() < 1e-6:
            lam = new
            break
        lam = 0.5 * lam + 0.5 * new
    return lam


def firm_profit(pi_, pj, Lam, c):
    lam = duopoly_rates(pi_, pj, Lam, c)
    return pi_ * lam[0]


def best_response(pj, Lam, c, grid):
    return max((firm_profit(p, pj, Lam, c), p) for p in grid)[1]


def s2(Lams, pis, c, md, label):
    K = len(Lams)
    grid = np.linspace(0, P, 81)
    L2 = 2 * np.asarray(Lams)
    # phase-contingent: per-phase symmetric Nash
    pn = []
    for k in range(K):
        p = 5.0
        for _ in range(25):
            q = best_response(p, L2[k], c, grid)
            if abs(q - p) < 1e-9:
                break
            p = 0.5 * p + 0.5 * q
        pn.append(p)

    def stats(prices):
        prof = wel = 0.0
        for k in range(K):
            lam = duopoly_rates(prices[k], prices[k], L2[k], c)
            prof += pis[k] * prices[k] * lam[0]
            D = lam.sum()
            wel += pis[k] * (P * (D - D ** 2 / (2 * L2[k])) - sum(l * sojourn(l, c) for l in lam))
        return prof, wel
    # flat: symmetric Nash in a single price (profit summed over phases)
    def flat_profit(pi_, pj):
        return sum(pis[k] * pi_ * duopoly_rates(pi_, pj, L2[k], c)[0] for k in range(K))
    p = 5.0
    for _ in range(25):
        q = max((flat_profit(x, p), x) for x in np.linspace(0, P, 81))[1]
        if abs(q - p) < 1e-9:
            break
        p = 0.5 * p + 0.5 * q
    prof_ph, w_ph = stats(pn)
    prof_fl, w_fl = stats([p] * K)
    md.append(f"- {label}: duopoly Nash flat price {p:.1f}: profit/firm {prof_fl:.2f}, welfare {w_fl:.2f}; "
              f"phase prices {', '.join(f'{x:.1f}' for x in pn)}: profit/firm {prof_ph:.2f}, welfare {w_ph:.2f}")
    print(md[-1], flush=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    data = args[0]
    out = args[1] if len(args) > 1 else "results/theory_props.md"
    md = ["# Propositions (numerical verification) and strategic extensions\n"]
    for name, sc in (("Code trace (c=7)", th.scenario_code), ("Conversation trace (c=45)", th.scenario_conv)):
        lam_s, G, c = sc(data)
        Lams, pis = th.lam_potential(lam_s, G, c, 1.0)
        md.append(f"## {name}\n")
        check_props(Lams, pis, c, md, "Propositions")
        md.append("### Strategic extensions\n")
        s1(Lams, pis, c, md, name)
        s2(Lams, pis, c, md, name)
        md.append("")
        open(out, "w").write("\n".join(md))


if __name__ == "__main__":
    main()
