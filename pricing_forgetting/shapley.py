"""Cooperative-game utilities for "Pricing Forgetting" (Sections 3-5).

Games are dicts {frozenset(S): value} over all subsets of N = range(n), or callables on frozensets.
Everything here is exact (enumeration), which is what the paper's n = 4 experiment uses.
"""
import itertools
import math
from typing import Callable, Dict, FrozenSet, Iterable, List, Sequence

import numpy as np

Game = Callable[[FrozenSet[int]], float]


def subsets(items: Iterable[int]):
    items = list(items)
    for r in range(len(items) + 1):
        for c in itertools.combinations(items, r):
            yield frozenset(c)


def as_game(table: Dict[FrozenSet[int], float]) -> Game:
    return lambda S: table[frozenset(S)]


def tabulate(game: Game, n: int) -> Dict[FrozenSet[int], float]:
    return {S: game(S) for S in subsets(range(n))}


def shapley_weight(s: int, n: int) -> float:
    """w_S = s!(n-1-s)!/n!  (eq. 2)."""
    return math.factorial(s) * math.factorial(n - 1 - s) / math.factorial(n)


def shapley(game: Game, n: int) -> np.ndarray:
    """phi_i(game) for all i (eq. 2); does not require game(empty) = 0."""
    phi = np.zeros(n)
    for i in range(n):
        for S in subsets(set(range(n)) - {i}):
            phi[i] += shapley_weight(len(S), n) * (game(S | {i}) - game(S))
    return phi


# ---- Section 3: contribution / deletion games --------------------------------------------------
def contribution_game(U: Game) -> Game:
    """v(S) = U(S) - U(empty)  (eq. 1)."""
    u0 = U(frozenset())
    return lambda S: U(frozenset(S)) - u0


def deletion_game(v: Game, n: int) -> Game:
    """w(R) = v(N) - v(N \\ R)  (eq. 3)."""
    N = frozenset(range(n))
    vN = v(N)
    return lambda R: vN - v(N - frozenset(R))


def leave_one_out(v: Game, n: int) -> np.ndarray:
    """w({i}) = v(N) - v(N \\ {i})."""
    w = deletion_game(v, n)
    return np.array([w(frozenset({i})) for i in range(n)])


def banzhaf(game: Game, n: int) -> np.ndarray:
    b = np.zeros(n)
    for i in range(n):
        for S in subsets(set(range(n)) - {i}):
            b[i] += (game(S | {i}) - game(S)) / 2 ** (n - 1)
    return b


# ---- Section 3.4: replication and merging ------------------------------------------------------
def replicate(v: Game, n: int, i: int) -> Game:
    """Game on n+1 players where contributor i is split into two replicas (i, n); the replica adds no
    information: v'(S u A) = v(S u {i}) for any nonempty A of {i, n}.  Players other than i keep their index."""
    def vp(S):
        S = frozenset(S)
        base = S - {i, n}
        return v(base | {i}) if (S & {i, n}) else v(base)
    return vp


def replication_gain_formula(v: Game, n: int, i: int) -> float:
    """(n+1)^-1 * sum_S w_S (n-1-2s) m_i(S)   (Proposition 2)."""
    tot = 0.0
    for S in subsets(set(range(n)) - {i}):
        s = len(S)
        tot += shapley_weight(s, n) * (n - 1 - 2 * s) * (v(S | {i}) - v(S))
    return tot / (n + 1)


def replication_gain(v: Game, n: int, i: int) -> float:
    """Direct computation: phi_i'(v') + phi_i''(v') - phi_i(v)."""
    vp = replicate(v, n, i)
    phip = shapley(vp, n + 1)
    return phip[i] + phip[n] - shapley(v, n)[i]


def merge(v: Game, n: int, i: int, j: int) -> Game:
    """Merge players i, j into one player (new index 0); the rest keep their order as 1..n-2."""
    others = [k for k in range(n) if k not in (i, j)]
    # new index 0 = merged player, 1.. = the remaining players in order
    def vm2(S):
        orig = set()
        for p in S:
            orig |= {i, j} if p == 0 else {others[p - 1]}
        return v(frozenset(orig))
    return vm2


# ---- Section 4: residual game, additive bias ---------------------------------------------------
def residual_game(U_hat: Game, U: Game) -> Game:
    """eps(T) = U_hat(T) - U(T)  (eq. 6)."""
    return lambda T: U_hat(frozenset(T)) - U(frozenset(T))


def estimated_game(U_hat: Game, U_empty: float) -> Game:
    """v_hat(T) = U_hat(T) - U(empty)."""
    return lambda T: U_hat(frozenset(T)) - U_empty


def additive_bias_check(U: Game, U_hat: Game, n: int) -> dict:
    """Proposition 3: phi(v_hat) = phi(v) + phi(eps); sum phi(v_hat) = v(N) - eps(empty)."""
    v = contribution_game(U)
    vhat = estimated_game(U_hat, U(frozenset()))
    eps = residual_game(U_hat, U)
    phi, phih, phie = shapley(v, n), shapley(vhat, n), shapley(eps, n)
    N = frozenset(range(n))
    return dict(
        phi=phi, phi_hat=phih, phi_eps=phie,
        decomposition_err=float(np.abs(phih - phi - phie).max()),
        sum_hat=float(phih.sum()), vN=float(v(N)), eps_empty=float(eps(frozenset())),
        sum_err=float(abs(phih.sum() - (v(N) - eps(frozenset())))),
        l1_bias=float(np.abs(phie).sum()),
    )


# ---- Section 4.3: sequential unlearning --------------------------------------------------------
def sequential_estimate(U_seq: Callable[[Sequence[int]], float], n: int, orders=None):
    """phi_tilde_i = E_pi[ U~_{k-1}(pi) - U~_k(pi) ], k = position of i.

    U_seq(prefix) = performance after unlearning the contributors in `prefix`, in that order, from the
    fully trained model.  `orders=None` enumerates all n! permutations (exact, P5); otherwise an iterable
    of permutations (e.g. six sampled orders).  Returns (phi_tilde, mean eps-free sum, per-order sums).
    """
    if orders is None:
        orders = list(itertools.permutations(range(n)))
    cache = {}
    def u(prefix):
        prefix = tuple(prefix)
        if prefix not in cache:
            cache[prefix] = U_seq(prefix)
        return cache[prefix]
    phi = np.zeros(n)
    sums = []
    for pi in orders:
        tot = 0.0
        for k in range(1, n + 1):
            credit = u(pi[: k - 1]) - u(pi[:k])
            phi[pi[k - 1]] += credit
            tot += credit
        sums.append(tot)
    return phi / len(orders), float(np.mean(sums)), sums


def sequential_bias_check(U: Game, U_seq: Callable[[Sequence[int]], float], n: int) -> dict:
    """Proposition 4 (exact over all orders): sum phi_tilde = v(N) - mean_pi eps(empty; pi);
    and Proposition 5's bound  |phi_tilde_i - phi_i(v) - phi_i(eps_bar)| <= (1/n) sum_{k>=2} delta_k."""
    N = frozenset(range(n))
    v = contribution_game(U)
    perms = list(itertools.permutations(range(n)))
    phi_t, _, sums = sequential_estimate(U_seq, n, perms)
    # eps(T; sigma) for the removed set N\T taken in order sigma
    def eps(sigma):
        T = N - frozenset(sigma)
        return U_seq(tuple(sigma)) - U(T)
    eps_bar_tab = {}
    delta = {k: 0.0 for k in range(1, n + 1)}
    for R in subsets(range(n)):
        k = len(R)
        if k == 0:
            eps_bar_tab[N - R] = 0.0
            continue
        vals = [eps(s) for s in itertools.permutations(sorted(R))]
        m = float(np.mean(vals))
        eps_bar_tab[N - R] = m
        delta[k] = max(delta[k], max(abs(x - m) for x in vals))
    eps_bar = lambda T: eps_bar_tab[frozenset(T)]
    phi, phie_bar = shapley(v, n), shapley(eps_bar, n)
    gap = np.abs(phi_t - phi - phie_bar)
    bound = sum(delta[k] for k in range(2, n + 1)) / n
    eps_empty_bar = float(np.mean([eps(p) for p in perms]))
    return dict(
        phi_tilde=phi_t, phi=phi, phi_eps_bar=phie_bar,
        sum_tilde=float(phi_t.sum()), vN=float(v(N)), eps_empty_bar=eps_empty_bar,
        sum_err=float(abs(phi_t.sum() - (v(N) - eps_empty_bar))),
        prop5_gap=float(gap.max()), prop5_bound=float(bound), delta=delta,
        # half the gap between residuals of two removal orders of the full set (lower bound on delta_n)
        path_gap_lower_bound=float(0.5 * (max(eps(p) for p in perms) - min(eps(p) for p in perms))),
    )


# ---- Section 5: incentives and audit design ----------------------------------------------------
def truthful(p, delta, F, C, c, beta, rho) -> bool:
    """Proposition 6 / eq. (11): p*delta*F >= (C - c) + beta*rho."""
    return p * delta * F >= (C - c) + beta * rho - 1e-12


def optimal_audit(a, e, H, C, c, beta, rho, F_bar):
    """Proposition 7. Returns dict with theta, delta*, p*, cost, deter? (None if deterrence impossible)."""
    theta = ((C - c) + beta * rho) / F_bar
    if theta > 1:
        return dict(theta=theta, deter_possible=False, delta=None, p=None, cost=None, deter=False)
    d = min(1.0, max(theta, (a * theta / e) ** (1 / 3)))
    p = theta / d
    cost = a * p + e * d * d / 2           # = a*theta/d + e d^2/2
    return dict(theta=theta, deter_possible=True, delta=d, p=p, cost=cost, deter=bool(cost <= H))


def tolerable_residue(p, delta, k, phi, C, c, beta, base="developer") -> float:
    """Proposition 8: largest r_i for which exact removal is optimal."""
    num = p * delta * k * phi - (C - c)
    return num / (p * delta * k + beta) if base == "developer" else num / beta
