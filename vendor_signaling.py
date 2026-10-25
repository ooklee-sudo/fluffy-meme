"""Outcome-based pricing as a signal of reach when the vendor privately knows its type.

Vendor type theta in {L, H} has reach ratio A_theta (a_L = A_theta * a_H); firms know only the prior q = P(H)
or the belief induced by the contract they observe.  A risk-neutral firm's cost is linear in a_L, so it behaves as
if reach were its expected value Abar.

Usage contract  (price p per budget unit):   firm cost (c0+p)*T + f*(N - Abar*a*(1-exp(-bT))) ; vendor revenue p*T
Outcome contract (price r per fault found):  firm cost c0*T + r*m(T) + f*(N - m(T))  =>  tool with stakes (f - r),
                                              vendor revenue r*m_true(T) - k*T   (vendor pays compute k per unit T)
where m(T)= A*a*(1-exp(-b_L T)),  T* = ln(kappa')/b_L,  kappa' = Abar*a*b_L*(f-r)/c0.

Run: python3 vendor_signaling.py     (KV=0.05 python3 vendor_signaling.py to change the vendor compute cost)
"""
import numpy as np
import vendor_model as VM

import os
a, b, B, c0 = VM.a, VM.b, VM.B, VM.c0
kv = float(os.environ.get("KV", VM.kv))             # vendor compute cost per budget unit (default 0.1)
h, FG, W = VM.h, VM.FGRID, VM.W
AL, AH, q = 0.60, 1.00, 0.5
Abar = q * AH + (1 - q) * AL
S_H = FG * a * h(a * b * FG / 1.0)                       # human net saving (c_H = 1)


def outcome_firm(r, Ab):
    """Adoption indicator and optimal budget under belief Ab for outcome price r."""
    eff = FG - r
    ok = eff > 0
    kap = np.where(ok, Ab * a * B * b * np.maximum(eff, 1e-9) / c0, 0.0)
    S_L = np.where(ok, np.maximum(eff, 0) * Ab * a * h(kap), 0.0)
    adopt = ok & (S_L >= S_H) & (kap > 1)
    T = np.where(kap > 1, np.log(np.maximum(kap, 1e-12)) / (B * b), 0.0)
    return adopt, T, kap


def outcome_profit(r, A_true, Ab):
    adopt, T, kap = outcome_firm(r, Ab)
    found = A_true * a * (1 - 1.0 / np.maximum(kap, 1.0))        # (1 - exp(-bT*)) = 1 - 1/kappa'
    rev = r * found - kv * T
    return float((adopt * rev * W).sum()), float((adopt * W).sum())


def usage_profit(p, Ab):
    """Usage pricing: vendor revenue does not depend on its true type, only on the firms' belief Ab."""
    f = FG
    cL = c0 + p
    S_L = f * (Ab * a) * h(Ab * a * B * b * f / cL)
    adopt = S_L >= S_H
    T = VM.Tstar(Ab * a, B * b, cL, f)
    return float((adopt * (p - kv) * T * W).sum()), float((adopt * W).sum())


rs = np.linspace(0.02, 3.0, 300)
ps = np.linspace(kv + 0.01, 3.0, 300)

# ------------------------------------------------------------ usage pricing: no separation possible
print(f"types: A_L={AL}, A_H={AH}, prior q={q}, Abar={Abar:.2f}")
pu = np.array([usage_profit(p, Abar)[0] for p in ps]); ip = pu.argmax()
print(f"\n[usage pricing] payoff depends on the true type only through firms' belief -> both types have the same\n"
      f"  preferences over (p, belief): no contract can separate them.  pooled optimum p={ps[ip]:.2f}, "
      f"profit/type={pu[ip]:.3f}, adopter share={usage_profit(ps[ip], Abar)[1]:.2f}")
for nm, Ab in (("full info, type L", AL), ("full info, type H", AH)):
    pr = np.array([usage_profit(p, Ab)[0] for p in ps]); i = pr.argmax()
    print(f"   {nm}: p*={ps[i]:.2f} profit={pr[i]:.3f} share={usage_profit(ps[i], Ab)[1]:.2f}")

# ------------------------------------------------------------ outcome pricing
P = {(t, Ab): np.array([outcome_profit(r, t, Ab)[0] for r in rs]) for t in (AL, AH) for Ab in (AL, AH, Abar)}
SH = {Ab: np.array([outcome_profit(r, AH, Ab)[1] for r in rs]) for Ab in (AL, AH, Abar)}
iL, iH = P[(AL, AL)].argmax(), P[(AH, AH)].argmax()
print("\n[outcome pricing]")
print(f"  full information: type L r*={rs[iL]:.2f} profit={P[(AL, AL)][iL]:.3f} | type H r*={rs[iH]:.2f} profit={P[(AH, AH)][iH]:.3f}")
pool = q * P[(AH, Abar)] + (1 - q) * P[(AL, Abar)]; ipool = pool.argmax()
print(f"  pooling (belief=prior): r={rs[ipool]:.2f}  profit L={P[(AL, Abar)][ipool]:.3f}  H={P[(AH, Abar)][ipool]:.3f}  "
      f"share={outcome_profit(rs[ipool], AH, Abar)[1]:.2f}")

# separating equilibrium: L plays its full-info contract (belief L); H picks the best r that L will not mimic
piL_sep = P[(AL, AL)][iL]
ic_L = P[(AL, AH)] <= piL_sep + 1e-12                # L does not gain by mimicking r (belief H)
ic_H = P[(AH, AH)] >= P[(AH, AL)][iL] - 1e-12        # H prefers its contract to L's
feas = ic_L & ic_H
if feas.any():
    cand = np.where(feas, P[(AH, AH)], -np.inf); j = cand.argmax()
    nat = "natural (no distortion)" if abs(rs[j] - rs[iH]) < 1e-9 else f"distorted from r_H*={rs[iH]:.2f}"
    print(f"  separating: L plays r={rs[iL]:.2f}; H plays r={rs[j]:.2f} ({nat}), "
          f"H profit {P[(AH, AH)][j]:.3f} (full-info {P[(AH, AH)][iH]:.3f})")
    print(f"     L's gain from mimicking H's r (if believed H): {P[(AL, AH)][j]:.3f} vs {piL_sep:.3f} own  -> IC_L holds")
    print(f"     adopter shares: H contract {SH[AH][j]:.2f}  L contract {outcome_profit(rs[iL], AL, AL)[1]:.2f}")
else:
    print("  no separating outcome contract satisfies both IC constraints")
# does L want to mimic H's FULL-INFO contract?
print(f"  check: L mimicking H's full-info r={rs[iH]:.2f} earns {P[(AL, AH)][iH]:.3f} vs own {piL_sep:.3f} "
      f"-> {'mimics (distortion needed)' if P[(AL, AH)][iH] > piL_sep else 'does not mimic (separation is free)'}")

# sensitivity to the reach gap
print("\nreach gap sweep (A_H=1.0): does separation require distortion? profits per type, outcome vs usage pooling")
print(" A_L | r_L* r_H* | mimic gain>0? | H profit: sep / pooled-outcome / pooled-usage | L profit: sep / pooled-outcome / pooled-usage")
for al in (0.9, 0.8, 0.7, 0.6, 0.5, 0.4):
    AL_, Ab = al, q * AH + (1 - q) * al
    PP = {(t, x): np.array([outcome_profit(r, t, x)[0] for r in rs]) for t in (AL_, AH) for x in (AL_, AH, Ab)}
    iL_, iH_ = PP[(AL_, AL_)].argmax(), PP[(AH, AH)].argmax()
    mim = PP[(AL_, AH)][iH_] > PP[(AL_, AL_)][iL_]
    feas_ = (PP[(AL_, AH)] <= PP[(AL_, AL_)][iL_] + 1e-12) & (PP[(AH, AH)] >= PP[(AH, AL_)][iL_] - 1e-12)
    hs = np.where(feas_, PP[(AH, AH)], -np.inf).max()
    pl = (q * PP[(AH, Ab)] + (1 - q) * PP[(AL_, Ab)]); ip_ = pl.argmax()
    pu_ = np.array([usage_profit(p, Ab)[0] for p in ps]).max()
    print(f" {al:.1f} | {rs[iL_]:.2f} {rs[iH_]:.2f} | {str(mim):5s} | H {hs:7.3f} / {PP[(AH, Ab)][ip_]:7.3f} / {pu_:7.3f} "
          f"| L {PP[(AL_, AL_)][iL_]:7.3f} / {PP[(AL_, Ab)][ip_]:7.3f} / {pu_:7.3f}")
