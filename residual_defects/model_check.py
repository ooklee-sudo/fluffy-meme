"""Numerical check of the verification-effort model (see MODEL_NOTE.md).

Developer minimises  C(e) + (1-phi) * l * lam * s * S(e),  S = survival of a defect.
Baseline: S(e)=exp(-theta e), C(e)=c e  =>  closed forms
    e* = ln((1-phi) l lam s theta / c) / theta,   E[R] = c / ((1-phi) l theta).
Robustness: convex cost C(e)=c e^gamma, and heavy-tailed detection S(e)=(1+theta e/k)^-k.
"""
import numpy as np
from scipy.optimize import minimize_scalar

c, l, s, theta = 1.0, 50.0, 1.0, 0.8


def solve(lam, phi=0.0, gamma=1.0, k=None):
    S = (lambda e: np.exp(-theta * e)) if k is None else (lambda e: (1 + theta * e / k) ** (-k))
    f = lambda e: c * e ** gamma + (1 - phi) * l * lam * s * S(e)
    r = minimize_scalar(f, bounds=(0, 200), method="bounded", options={"xatol": 1e-10})
    e = r.x if f(r.x) < f(0) else 0.0  # corner: no verification
    return e, lam * s * S(e)


print("1) Baseline closed form vs numerical optimum (phi=0.3)")
for lam in [0.5, 1, 2, 4]:
    e, R = solve(lam, phi=0.3)
    e_cf = np.log((1 - 0.3) * l * lam * s * theta / c) / theta
    R_cf = c / ((1 - 0.3) * l * theta)
    print(f"  lam={lam:3}: e*={e:.4f} (cf {e_cf:.4f})  E[R]={R:.4f} (cf {R_cf:.4f})")

print("\n2) Private/social residual ratio vs 1/(1-phi)")
for phi in [0.0, 0.25, 0.5, 0.75]:
    _, Rp = solve(2.0, phi)
    _, Rs = solve(2.0, 0.0)
    print(f"  phi={phi:4}: R_private/R_social={Rp / Rs:.4f}  1/(1-phi)={1 / (1 - phi):.4f}")

print("\n3) Offsetting elasticity d ln R / d ln lam")
print("   0 => quality gains fully offset by less verification; 1 => no offsetting")
for name, kw in [("baseline", {}), ("convex gamma=1.5", {"gamma": 1.5}), ("convex gamma=2", {"gamma": 2.0}),
                 ("heavy-tail k=2", {"k": 2.0}), ("heavy-tail k=1", {"k": 1.0}),
                 ("convex 1.5 + k=2", {"gamma": 1.5, "k": 2.0})]:
    out = []
    for lam in [1.0, 4.0]:
        _, R0 = solve(lam, 0.3, **kw)
        _, R1 = solve(lam * 1.01, 0.3, **kw)
        out.append(np.log(R1 / R0) / np.log(1.01))
    print(f"  {name:18s} lam=1: {out[0]:.3f}   lam=4: {out[1]:.3f}")

print("\n4) Corner: no verification when (1-phi) l lam s theta < c")
for lam in [0.02, 0.05, 0.1]:
    e, R = solve(lam, 0.3)
    print(f"  lam={lam}: threshold={(c / ((1 - 0.3) * l * s * theta)):.4f}  e*={e:.3f}  E[R]={R:.4f}")
