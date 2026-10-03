"""Numerical check of the propositions in MODEL.md, and the calibration illustrations (measured a and s for the ten open-weight models and the Claude ladder, registered coding).
Run: python model_check.py   (no data files needed; the model-level values are copied from Table 3 of the manuscript: RN and Flip, with s = Flip / RN)."""
import itertools, math
import numpy as np

rng = np.random.default_rng(1)


def V(a, sw, sr, pi):               # value of review for a naive requester who adopts the delegate's report
    return (1 - pi) * (1 - sw) * a - pi * (1 - sr) * (1 - a)


def V_sym(a, s, pi):
    return (1 - s) * (a - pi)


def W(a, sw, sr, pi):               # sophisticated Bayesian requester who knows (a, sw, sr, pi); baseline: acts on the better of her own two options
    pS1, pS0 = pi * (sr + (1 - sr) * a), (1 - pi) * (sw + (1 - sw) * (1 - a))     # report = stance action S, joint with theta = 1 (S correct) / 0
    pN1, pN0 = pi * (1 - sr) * (1 - a), (1 - pi) * (1 - sw) * a                    # report = not S
    return max(pS1, pS0) + max(pN1, pN0) - max(pi, 1 - pi)


def check():
    n = 20000
    for _ in range(n):
        a, s, pi, d = rng.random(4)
        assert abs(V(a, s, s, pi) - V_sym(a, s, pi)) < 1e-12                                       # Prop 1 reduces to (1-s)(a-pi)
        assert abs(V_sym(a, s, pi) - (1 - s) * (a - pi)) < 1e-12
        # Prop 2: complementarity of a and integrity i = 1-s: d2V/(da di) = 1 (V = i(a - pi), exact)
        h = 1e-4; cross = (V_sym(a + h, 1 - (1 - s + h), pi) - V_sym(a + h, s, pi) - V_sym(a, 1 - (1 - s + h), pi) + V_sym(a, s, pi)) / h ** 2
        assert abs(cross - 1) < 1e-3, cross
        # Prop 3: sign of dV/ds is -(a - pi)
        assert (V_sym(a, min(s + .01, 1), pi) - V_sym(a, s, pi)) * (a - pi) <= 1e-12
        # Prop 4: share of ability-only value lost = s
        if abs(a - pi) > 1e-6: assert abs(1 - V_sym(a, s, pi) / (a - pi) - s) < 1e-9
        # Prop 5: Blackwell: sophisticated value weakly decreasing in s (sw = sr = s)
        s2 = min(1, s + d * (1 - s)); assert W(a, s2, s2, pi) <= W(a, s, s, pi) + 1e-12
        # Prop 7: blinding helps iff delta < s (a - pi)
        delta = rng.random() * .5
        blind_better = (a - delta - pi) > V_sym(a, s, pi); assert blind_better == (delta < s * (a - pi)) or abs(delta - s * (a - pi)) < 1e-9
    # Prop 6: reversal threshold, both orientations (a1 > a2; the first delegate is the more able one)
    for _ in range(n):
        a1, a2 = sorted(rng.random(2))[::-1]; s1, s2 = rng.random(2); pi = rng.random()
        N = (1 - s1) * a1 - (1 - s2) * a2
        if s1 > s2:                      # more able but more deferential: the other is better at LOW priors
            thr = -N / (s1 - s2); assert (V_sym(a1, s1, pi) < V_sym(a2, s2, pi)) == (pi < thr) or abs(pi - thr) < 1e-9
        elif s1 < s2:                    # more able and less deferential: the other can be better at HIGH priors (it overrides a correct preference less often)
            thr = N / (s2 - s1); assert (V_sym(a1, s1, pi) < V_sym(a2, s2, pi)) == (pi > thr) or abs(pi - thr) < 1e-9
        # Prop 8: ability ranking is value-optimal for all pi in [0,1] iff both endpoint inequalities hold
        if a1 > a2:
            ok = (1 - s1) * a1 >= (1 - s2) * a2 - 1e-12 and (1 - s1) * (1 - a1) <= (1 - s2) * (1 - a2) + 1e-12
            grid = np.linspace(0, 1, 201); allok = all(V_sym(a1, s1, p) >= V_sym(a2, s2, p) - 1e-9 for p in grid)
            assert ok == allok, (a1, s1, a2, s2)
    print(f"propositions 1-8 verified numerically on {n} random parameter draws")


MODELS = {  # a = RN, s = Flip / RN (registered coding)
    "Qwen2.5-7B": (.542, .300), "Qwen2.5-72B": (.908, .092), "Llama-8B": (.758, .258), "Llama-70B": (.900, .142), "Gemma-4B": (.525, .325), "Gemma-12B": (.783, .358),
    "Gemma-27B": (.883, .433), "Ministral-3B": (.633, .267), "Ministral-8B": (.783, .233), "Ministral-14B": (.825, .175)}


def illustrate():
    M = {k: (a, f / a) for k, (a, f) in MODELS.items()}
    print("\nMeasured (a, s):", {k: (round(a, 3), round(s, 3)) for k, (a, s) in M.items()})
    pairs = [(p, q) for p, q in itertools.combinations(M, 2)]
    print("\nPairs for which ranking by ability is value-optimal for every prior pi in [0,1] (Prop 8):")
    good = 0; rev = []
    for p, q in pairs:
        (a1, s1), (a2, s2) = M[p], M[q]
        if a1 < a2: p, q, a1, s1, a2, s2 = q, p, a2, s2, a1, s1
        ok = (1 - s1) * a1 >= (1 - s2) * a2 and (1 - s1) * (1 - a1) <= (1 - s2) * (1 - a2)
        good += ok
        if not ok:
            N = (1 - s1) * a1 - (1 - s2) * a2
            rev.append((p, q, ("less able one better below pi = %.3f" % (-N / (s1 - s2))) if s1 > s2 else ("less able one better above pi = %.3f" % (N / (s2 - s1)))))
    print(f"  {good} of {len(pairs)} pairs.  Pairs with a reversal (more able delegate listed first):")
    for r in rev: print("   ", r)
    print("\nRegret of ranking by ability, averaged over all pairs (value units), for requester prior pi:")
    for pi in (.5, .6, .7, .8, .9):
        reg = []
        for p, q in pairs:
            (a1, s1), (a2, s2) = M[p], M[q]
            if a1 < a2: a1, s1, a2, s2 = a2, s2, a1, s1
            reg.append(max(0, V_sym(a2, s2, pi) - V_sym(a1, s1, pi)))
        print(f"  pi = {pi}: mean regret {np.mean(reg):.4f}, share of pairs misranked {np.mean(np.array(reg) > 0):.2f}, max regret {max(reg):.3f}")
    print("\nBlinding threshold s(a - pi): the delegate is better blinded to the requester's stance if blinding costs less ability than this:")
    for k in ("Qwen2.5-72B", "Llama-70B", "Ministral-14B", "Gemma-27B"):
        a, s = M[k]; print(f"  {k}: pi=.5 -> {s * (a - .5):.3f}; pi=.7 -> {s * (a - .7):.3f}")
    print("\nValue shrinkage s (share of the ability-based value lost to deference):", {k: round(s, 2) for k, (a, s) in M.items()})
    print("Sophisticated requester (knows a, s): W(pi=.5) for Gemma-27B vs naive V:", round(W(*(M['Gemma-27B'][0], M['Gemma-27B'][1], M['Gemma-27B'][1], .5)), 3), "vs", round(V_sym(*M['Gemma-27B'][:1], M['Gemma-27B'][1], .5), 3))


if __name__ == "__main__":
    check(); illustrate()
