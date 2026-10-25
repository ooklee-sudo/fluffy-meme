"""Policy experiments for the endogenous-reach model (companion to vendor_investment.py).

  1. Fine scan of the vendor's chosen reach A*(theta): where does it bunch at the parity point A=1?
  2. Mandated stakes-indexed liability (phi*delta): how does it move the critical cost theta^?
  3. Competition from a fixed lower-reach rival (A2 = 0.8): returns to crossing parity for the incumbent.
Run: python3 vendor_investment_policy.py
"""
import numpy as np
import vendor_model as VM
import vendor_strategic as VS
from vendor_investment import stage2, A0

As = np.round(np.arange(0.5, 1.301, 0.01), 3)
base = {A: stage2(A) for A in As}
prof = np.array([base[A][0] for A in As]); cs = np.array([base[A][2] for A in As])


def A_star(theta, profile, subsidy=0.0, welfare=False):
    obj = profile + (cs if welfare else 0.0) - (1 - subsidy) * 0.5 * theta * (As - A0) ** 2
    return As[obj.argmax()]


print("1. Vendor's chosen reach A*(theta) (fine grid, step 0.01):")
ths = np.exp(np.linspace(np.log(10), np.log(70), 61))
prev = None
bunch = []
for t in ths[::-1]:
    a = A_star(t, prof)
    bunch.append((t, a))
print(" theta :  " + "  ".join(f"{t:5.1f}" for t, _ in bunch[::4]))
print(" A*    :  " + "  ".join(f"{a:5.2f}" for _, a in bunch[::4]))
exact = [t for t, a in bunch if abs(a - 1.0) < 1e-9]
print("   theta range where the vendor stops exactly at parity A=1: %.1f - %.1f" % (min(exact), max(exact)) if exact else "   no bunching at A=1")
thr_p = max([t for t, a in bunch if a >= 1.0 - 1e-9] or [np.nan])
thr_s = max([t for t in ths if A_star(t, prof, welfare=True) >= 1.0 - 1e-9] or [np.nan])
print("   critical theta: private %.1f, social %.1f -> subsidy that closes the window: %.0f%%" % (thr_p, thr_s, 100 * (1 - thr_p / thr_s)))

print("\n2. Mandated stakes-indexed liability (vendor pays phi*delta*f x P(tool fails)), A grid step 0.02:")
As2 = np.round(np.arange(0.5, 1.301, 0.02), 3)
for pdl in (0, 5, 10, 15):
    pr = np.array([max(VS.indexed_warranty(A, pdl, VM.kv)[0], 0.0) for A in As2])
    cand = []
    for t in np.exp(np.linspace(np.log(5), np.log(80), 300)):
        obj = pr - 0.5 * t * (As2 - A0) ** 2
        if As2[obj.argmax()] >= 1.0 - 1e-9:
            cand.append(t)
    i1 = list(As2).index(1.0)
    print(f"   phi*delta={pdl:2d}: Pi*(0.90)={pr[list(As2).index(0.9)]:.3f}  Pi*(1.00)={pr[i1]:.3f}  Pi*(1.10)={pr[list(As2).index(1.1)]:.3f}   critical theta = {max(cand) if cand else float('nan'):.1f}")

print("\n3. Incumbent facing a fixed rival with reach 0.8 (duopoly Nash prices, step 0.05 in A1):")
res = {}
for A1 in (0.85, 0.9, 0.95, 1.0, 1.05, 1.1):
    grid, P1, P2, SH1, SH2, ne, mono = VS.duopoly(A1, 0.8, VM.kv, grid=np.linspace(0.12, 2.0, 70))
    if ne:
        i, j = max(ne, key=lambda x: P1[x] + P2[x]); res[A1] = (P1[i, j], mono, grid[i], grid[j])
    else:
        res[A1] = (np.nan, mono, np.nan, np.nan)
    print(f"   A1={A1:.2f}: incumbent profit duopoly {res[A1][0]:6.3f} vs monopoly {mono:6.3f}  (prices {res[A1][2]:.2f}, {res[A1][3]:.2f})")
