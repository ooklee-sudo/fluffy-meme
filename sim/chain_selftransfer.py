"""Exact per-task quantities for a count-threshold policy in the model WITH self-transfer (single error type).

State N = errors so far (N < n; at N >= n the firm hands off at the start of the step). Per step:
  pay k + c*mu; errors e ~ Poisson(mu); the agent transfers with prob s(e) = 1-(1-th)^e (task ends, a hand-off by the agent);
  otherwise the task completes with prob q (pay F*pi_w(N+e) in expectation), else the count becomes N+e.
Outputs for threshold n:  a_n (expected step cost), z_n (prob. of completing derailed), P_n (prob. that a person takes over,
by either party).  Expected cost = a_n + F*z_n + H*P_n.   With th = 0 this equals sim_capacity.AP.
"""
import math
import numpy as np

K, C, MU, Q = 1.0, 5.0, 0.054, 0.06
NINF = 150


def pmf(mu, emax=40):
    p = np.array([math.exp(-mu) * mu**e / math.factorial(e) for e in range(emax + 1)])
    return p / p.sum()


def quantities(n, tw, th, k=K, c=C, mu=MU, q=Q, emax=40):
    """Return (a_n, z_n, P_n)."""
    if n == 0:
        return 0.0, 0.0, 1.0
    p = pmf(mu, emax)
    s = np.array([1 - (1 - th) ** e for e in range(emax + 1)])
    pi = lambda N: 1 - (1 - tw) ** N
    T = np.zeros((n, n))            # transition among continuing states
    ba = np.full(n, k + c * mu)
    bz = np.zeros(n)
    bP = np.zeros(n)
    for N in range(n):
        for e in range(emax + 1):
            M = N + e
            cont = p[e] * (1 - s[e])
            bz[N] += cont * q * pi(M)
            bP[N] += p[e] * s[e]
            if M < n:
                T[N, M] += cont * (1 - q)
            else:
                bP[N] += cont * (1 - q)          # the firm hands off
    I = np.eye(n)
    a = np.linalg.solve(I - T, ba)[0]
    z = np.linalg.solve(I - T, bz)[0]
    P = np.linalg.solve(I - T, bP)[0]
    return a, z, P


def table(tw, th, nmax=25):
    ns = list(range(nmax + 1)) + [NINF]
    a, z, P = [], [], []
    for n in ns:
        x = quantities(n, tw, th)
        a.append(x[0]); z.append(x[1]); P.append(x[2])
    return np.array(P), np.array(a), np.array(z), ns


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    from sim_capacity import AP
    # validation: th = 0 reproduces the earlier chain
    worst = 0.0
    for tw in (0.05, 0.12, 0.29):
        for n in (1, 2, 4, 8, NINF):
            A0, P0 = AP(n, K, C, MU, Q, tw, 0.0); A1, _ = AP(n, K, C, MU, Q, tw, 1.0)
            a, z, P = quantities(n, tw, 0.0)
            worst = max(worst, abs(a - A0), abs(z - (A1 - A0)), abs(P - P0))
    print(f"th=0 reproduces sim_capacity.AP: max abs difference {worst:.2e}")
