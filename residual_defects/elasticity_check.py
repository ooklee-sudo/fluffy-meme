"""Check eps = d ln R / d ln lam = a / (a + h), a = C''/C' - h'/h, at the developer optimum."""
import numpy as np
from scipy.optimize import minimize_scalar

c, A, theta = 1.0, 35.0, 0.8   # A = (1-phi) * l * s


def make(kind, k=2.0, beta=2.0):
    if kind == "exp":
        return (lambda e: np.exp(-theta * e), lambda e: theta + 0 * e, lambda e: 0 * e)
    if kind == "heavy":   # gamma-mixed exponentials
        return (lambda e: (1 + theta * e / k) ** -k,
                lambda e: theta / (1 + theta * e / k),
                lambda e: -(theta ** 2 / k) / (1 + theta * e / k) ** 2)
    if kind == "weibull":
        return (lambda e: np.exp(-(theta * e) ** beta),
                lambda e: beta * theta ** beta * e ** (beta - 1),
                lambda e: beta * (beta - 1) * theta ** beta * e ** (beta - 2))


def solve(lam, kind, gamma, **kw):
    S, h, hp = make(kind, **kw)
    f = lambda e: c * e ** gamma + A * lam * S(e)
    grid = np.linspace(1e-6, 40, 400001)
    e0 = grid[np.argmin(f(grid))]
    e = minimize_scalar(f, bounds=(max(e0 - 0.01, 1e-9), e0 + 0.01), method="bounded",
                        options={"xatol": 1e-12}).x
    return e, lam * S(e), S, h, hp


def eps_formula(e, gamma, h, hp):
    cc = (gamma - 1) / e            # C''/C'
    a = cc - hp(e) / h(e)
    return a / (a + h(e)), a + h(e)


print(f"{'spec':28s} {'lam':>4s} {'e*':>7s} {'eps(num)':>9s} {'eps(formula)':>13s}  a+h")
for name, kind, gamma, kw in [
    ("exp, linear (baseline)", "exp", 1.0, {}),
    ("exp, convex g=1.5", "exp", 1.5, {}),
    ("exp, convex g=2", "exp", 2.0, {}),
    ("heavy k=2, linear", "heavy", 1.0, {"k": 2.0}),
    ("heavy k=1, linear", "heavy", 1.0, {"k": 1.0}),
    ("heavy k=4, linear", "heavy", 1.0, {"k": 4.0}),
    ("heavy k=2, convex g=1.5", "heavy", 1.5, {"k": 2.0}),
    ("weibull b=2, linear", "weibull", 1.0, {"beta": 2.0}),
    ("weibull b=1.5, linear", "weibull", 1.0, {"beta": 1.5}),
]:
    for lam in [1.0, 4.0]:
        e, R, S, h, hp = solve(lam, kind, gamma, **kw)
        e2, R2, *_ = solve(lam * 1.001, kind, gamma, **kw)
        num = np.log(R2 / R) / np.log(1.001)
        fm, soc = eps_formula(e, gamma, h, hp)
        print(f"{name:28s} {lam:4.0f} {e:7.3f} {num:9.4f} {fm:13.4f}  {soc:.3f}")
print("\nheavy-tail linear-cost prediction 1/(1+k): k=1 ->", 1/2, " k=2 ->", round(1/3, 4), " k=4 ->", 0.2)
