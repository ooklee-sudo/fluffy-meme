"""Sketch of the analytical extension: AI-testing vendor pricing and the firms' adoption threshold.

Firm with stakes f (cost of a residual fault) tests with the human technology (a, b, c_H=1) or with the
AI tool (A*a, B*b, c_L = c0 + p) and picks the budget T optimally. Closed forms (see isr_theory.md):
    kappa = a*b*f/c,  S = f*a*h(kappa) for kappa>1 else 0,  h(k) = 1 - (1+ln k)/k,  T* = ln(kappa)/b.
The firm adopts iff V = S_L - S_H >= 0.  The vendor sets a usage price p; its revenue is (p-k)*T*_L.

Run: python3 vendor_model.py
"""
import numpy as np

a, b = 20.0, 0.12                       # human technology, c_H = 1
A, B, c0, kv = 0.9, 1.6, 0.8, 0.1       # AI reach/speed ratios, firm-side AI cost, vendor marginal cost
MU, SIG = np.log(2.0), 0.9              # stakes f ~ lognormal


def h(k):
    k = np.asarray(k, float)
    return np.where(k > 1, 1 - (1 + np.log(np.maximum(k, 1e-12))) / np.maximum(k, 1e-12), 0.0)


def S(a_, b_, c_, f):
    return f * a_ * h(a_ * b_ * f / c_)


def Tstar(a_, b_, c_, f):
    k = a_ * b_ * f / c_
    return np.where(k > 1, np.log(np.maximum(k, 1e-12)) / b_, 0.0)


def V(f, p, A=A, B=B):
    return S(A * a, B * b, c0 + p, f) - S(a, b, 1.0, f)


FGRID = np.exp(np.linspace(np.log(0.02), np.log(400), 20001))
DENS = np.exp(-0.5 * ((np.log(FGRID) - MU) / SIG) ** 2) / (FGRID * SIG * np.sqrt(2 * np.pi))
W = DENS * np.gradient(FGRID)                          # quadrature weights


def adopters(p, A=A, B=B, lam=1.0):
    f = FGRID * lam                                    # liability scale lam multiplies stakes
    return V(f, p, A, B) > 1e-9


def profit(p, A=A, B=B, lam=1.0):
    ad = adopters(p, A, B, lam)
    t = Tstar(A * a, B * b, c0 + p, FGRID * lam)
    return float(((p - kv) * t * ad * W).sum()), float((ad * W).sum())


def interval(p, A=A, B=B, lam=1.0):
    ad = adopters(p, A, B, lam)
    if not ad.any():
        return None
    idx = np.where(ad)[0]
    contiguous = (np.diff(idx) == 1).all()
    return FGRID[idx[0]], FGRID[idx[-1]], contiguous


if __name__ == "__main__":
    rng = np.random.default_rng(0)

    # 1) single crossing / interval structure of the adopter set, random parameters with A<1<... rho>1
    bad, n = 0, 0
    for _ in range(3000):
        a_, b_ = rng.uniform(5, 50), rng.uniform(0.03, 0.4)
        A_, B_ = rng.uniform(0.5, 0.99), rng.uniform(1.0, 3.0)
        c_ = rng.uniform(1.0, 2.0)                      # AI unit cost relative to human = 1
        if A_ * B_ / c_ <= 1:                           # need rho = A*B/Pi > 1
            continue
        f = np.exp(np.linspace(np.log(0.01), np.log(2000), 4000))
        v = S(A_ * a_, B_ * b_, c_, f) - S(a_, b_, 1.0, f)
        pos = v > 1e-9
        idx = np.where(pos)[0]
        n += 1
        if len(idx) and not (np.diff(idx) == 1).all():
            bad += 1
    print(f"[check] adopter set is one interval (A<1<rho): violations {bad} of {n} random parameter draws")

    # 2) adopter interval and demand vs price
    print("\nprice p | AI cost | adopters [f_lo, f_hi] | adopter share | vendor profit")
    for p in (0.1, 0.3, 0.5, 0.7, 1.0, 1.5):
        iv = interval(p); pr, sh = profit(p)
        print(f" {p:4.1f}   |  {c0 + p:4.2f}   | " + (f"[{iv[0]:5.2f}, {iv[1]:6.2f}]" if iv else "      none      ")
              + f" | {sh:5.2f} | {pr:6.3f}")

    # 3) optimal price
    ps = np.linspace(kv + 0.01, 3.0, 300)
    pr = np.array([profit(p)[0] for p in ps])
    ps_star = ps[pr.argmax()]
    iv = interval(ps_star); _, sh = profit(ps_star)
    print(f"\noptimal price p* = {ps_star:.2f} (AI cost {c0 + ps_star:.2f}), profit {pr.max():.3f}, "
          f"adopter share {sh:.2f}, adopts for f in [{iv[0]:.2f}, {iv[1]:.2f}]")
    top = FGRID > np.exp(MU + 1.2816 * SIG)             # top decile of stakes
    print(f"top-decile-stakes firms adopting at p*: {(adopters(ps_star)[top] * W[top]).sum() / W[top].sum():.2f}")

    # 4) comparative statics: reach A and speed B
    print("\nvendor product improvement (reach A, speed B): p*, profit, adopter share, f_hi")
    for A_, B_ in ((0.8, 1.6), (0.9, 1.6), (1.0, 1.6), (1.1, 1.6), (0.9, 1.2), (0.9, 2.0)):
        pr_ = np.array([profit(p, A_, B_)[0] for p in ps])
        i = pr_.argmax(); iv_ = interval(ps[i], A_, B_)
        print(f" A={A_:.1f} B={B_:.1f}: p*={ps[i]:.2f} profit={pr_[i]:.3f} share={profit(ps[i], A_, B_)[1]:.2f} "
              f"f_hi={iv_[1]:.1f}" if iv_ else f" A={A_} B={B_}: no adoption")

    # 5) liability regime: stakes scaled by lam; vendor re-optimises
    print("\nliability scale lam (stakes x lam): adopter share at fixed p*, and re-optimised p*, share")
    for lam in (0.5, 1.0, 2.0, 4.0, 8.0):
        sh_fixed = profit(ps_star, lam=lam)[1]
        pr_ = np.array([profit(p, lam=lam)[0] for p in ps]); i = pr_.argmax()
        print(f" lam={lam:3.1f}: share@p*={sh_fixed:.2f} | re-opt p*={ps[i]:.2f} share={profit(ps[i], lam=lam)[1]:.2f} profit={pr_[i]:.3f}")
