"""Numerical values of the exercise premium F and the switch-the-ruler option value Omega.

Reproduces the numbers in Section 4 ("Valuing the option") and Appendix A, Steps 4-5,
using the Gaussian model of Appendix A (Eq. A.1 and Theorem C.2).
Parameters: tau = 1, omega = 0.2, delta = 0.95, c_G = 0.02.

Run: python premium_and_switch_option.py   (standard library only)
"""
from math import erf, exp, pi, sqrt


def cdf(x):
    return 0.5 * (1 + erf(x / sqrt(2)))


def pdf(x):
    return exp(-x * x / 2) / sqrt(2 * pi)


def premium(sigma, a, jump_prob, nu, tau=1.0, omega=0.2, delta=0.95, c_g=0.02):
    """Exercise premium F = max(0, x*), where x* solves x = W(x) (Appendix A, Step 3)."""
    var_a = (sigma ** 2 + jump_prob * nu ** 2) / a ** 2        # Eq. (2)
    s2 = 1 / (1 / tau ** 2 + 1 / var_a)                         # posterior variance before inspection
    v = s2 ** 2 / (s2 + omega ** 2)                             # variance reduction from inspection
    r = sqrt(v)

    def g(x):
        return x - (delta * (x * cdf(x / r) + r * pdf(x / r)) - c_g)

    lo, hi = -50.0, 50.0                                        # g is strictly increasing: bisection
    for _ in range(200):
        mid = (lo + hi) / 2
        if g(mid) > 0:
            hi = mid
        else:
            lo = mid
    return max(0.0, (lo + hi) / 2)


if __name__ == "__main__":
    print("Premium by judge noise (a = 0.8):",
          [round(premium(s, 0.8, 0, 1.5), 2) for s in (0.4, 0.7, 1.2)])
    print("Premium, nearly collapsed judge (sigma = 0.7, a = 0.01):", round(premium(0.7, 0.01, 0, 1.5), 2))
    print("Premium by jump probability (sigma = 0.7, a = 0.8, nu = 1.5):",
          [round(premium(0.7, 0.8, p, 1.5), 2) for p in (0, 0.1, 0.3)])
    print("Omega from removing pi = 0.3, by judge slope a:")
    for a in (0.8, 0.3, 0.1, 0.03, 0.01):
        print(f"  a = {a}: {premium(0.7, a, 0.3, 1.5) - premium(0.7, a, 0, 1.5):.4f}")
