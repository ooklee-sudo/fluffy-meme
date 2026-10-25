"""Strategic extensions: (A) vendor liability (Bauer-style warranty) as a signal of reach, (B) duopoly with different reach.

(A) Reach is binary at the project level: with probability A_theta the tool covers the project (then it finds faults
    as in the NHPP model), otherwise it finds nothing.  A risk-neutral firm therefore acts on the expected reach.
    Warranty: if the campaign fails (tool does not cover the project) and the failure is verified (prob phi), the
    vendor pays damages D.  Expected liability of type theta: (1-A_theta)*phi*D  (decreasing in reach: single crossing).
(B) Two vendors with reach A1 > A2 and usage prices p1, p2; every firm picks the best of {human, tool 1, tool 2}.

Run: python3 vendor_strategic.py
"""
import numpy as np
import vendor_model as VM
import vendor_signaling_complexity as C

a, b, B, c0 = VM.a, VM.b, VM.B, VM.c0
FG, W, h = VM.FGRID, VM.W, VM.h
S_H = FG * a * h(a * b * FG / 1.0)


def usage_profit_belief(p, Ab, kv):
    C.kv = kv
    return C.usage_seg(p, Ab, 1.0)          # (profit, adopter share) given firms' belief Ab (type-independent revenue)


# ---------------------------------------------------------------- A1: fixed damages as a signal
def warranty_signal(AL, AH, phi, kv, ps=np.linspace(0.12, 3.0, 300)):
    C.kv = kv
    own = max(max(C.usage_seg(p, AL, 1.0)[0] for p in ps), 0.0)           # L's best profit when believed to be L
    full = max(C.usage_seg(p, AH, 1.0)[0] for p in ps)                     # H's full-information profit
    best = None
    for p in ps:
        pi, s = C.usage_seg(p, AH, 1.0)                                   # profit if believed H (same for either true type)
        if s <= 0 or pi <= 0:
            continue
        Dmin = max(0.0, (pi - own) / ((1 - AL) * phi * s))               # IC_L: L must not gain by mimicking
        profit_H = pi - (1 - AH) * phi * Dmin * s
        if profit_H >= own - 1e-12 and (best is None or profit_H > best[0]):
            best = (profit_H, p, Dmin, s)
    return own, full, best


# ---------------------------------------------------------------- A2: damages proportional to the firm's loss
def indexed_warranty(A, phiDelta, kv, ps=np.linspace(0.12, 3.0, 200)):
    """D = delta*f paid with probability phi when the tool fails; only phi*delta matters. Full-information vendor."""
    best = (0.0, None, 0.0, 0.0)                                      # option to withdraw: zero profit, nobody adopts
    top = FG > np.exp(VM.MU + 1.2816 * VM.SIG)
    for p in ps:
        cL = c0 + p
        SL = FG * (A * a) * h(A * a * B * b * FG / cL) + (1 - A) * phiDelta * FG          # expected warranty transfer added
        adopt = SL > S_H + 1e-9
        T = VM.Tstar(A * a, B * b, cL, FG)
        prof = float((adopt * ((p - kv) * T - (1 - A) * phiDelta * FG) * W).sum())      # vendor pays the expected damages
        if prof > best[0]:
            best = (prof, p, float((adopt * W).sum()), float((adopt[top] * W[top]).sum() / W[top].sum()))
    return best


# ---------------------------------------------------------------- B: duopoly
def duopoly(A1, A2, kv, grid=np.linspace(0.12, 2.0, 95)):
    def arrays(A):
        S, T = [], []
        for p in grid:
            cL = c0 + p
            S.append(FG * (A * a) * h(A * a * B * b * FG / cL)); T.append(VM.Tstar(A * a, B * b, cL, FG))
        return np.array(S), np.array(T)
    S1, T1 = arrays(A1); S2, T2 = arrays(A2)
    n = len(grid)
    P1 = np.zeros((n, n)); P2 = np.zeros((n, n)); SH1 = np.zeros((n, n)); SH2 = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            best = np.maximum(S_H, np.maximum(S1[i], S2[j]))
            c1 = (S1[i] >= S2[j]) & (S1[i] > S_H + 1e-9)                    # ties go to the higher-reach tool
            c2 = (S2[j] > S1[i]) & (S2[j] > S_H + 1e-9)
            P1[i, j] = ((grid[i] - kv) * T1[i] * c1 * W).sum(); P2[i, j] = ((grid[j] - kv) * T2[j] * c2 * W).sum()
            SH1[i, j] = (c1 * W).sum(); SH2[i, j] = (c2 * W).sum()
    ne = [(i, j) for i in range(n) for j in range(n)
          if P1[i, j] >= P1[:, j].max() - 1e-12 and P2[i, j] >= P2[i, :].max() - 1e-12]
    mono1 = max(((grid[i] - kv) * T1[i] * (S1[i] > S_H + 1e-9) * W).sum() for i in range(n))
    return grid, P1, P2, SH1, SH2, ne, mono1


if __name__ == "__main__":
    AL, AH = 0.6, 1.0
    print("=== A1. Fixed-damages warranty as a signal (usage price + damages D paid on verified failure) ===")
    print("types A_L=0.6; A_H as shown. 'retained' = H's profit under separation / its full-information profit.")
    print(" A_H  phi   k   | L own  H full-info | separating: p   D_min   H profit  retained | outcome-fee separation (earlier)")
    for ah in (1.0, 0.9):
        for kv in (0.0, 0.1, 0.4):
            for phi in (0.25, 1.0):
                own, full, best = warranty_signal(AL, ah, phi, kv)
                if best is None:
                    print(f" {ah:.1f}  {phi:.2f}  {kv:.1f} | {own:.3f}  {full:.3f} | no separating warranty"); continue
                pr, p, D, s = best
                print(f" {ah:.1f}  {phi:.2f}  {kv:.1f} | {own:.3f}  {full:.3f}   |   {p:.2f}  {D:6.1f}  {pr:8.3f}  {pr/full:6.0%}")
    print("   closed form: retained = 1 - (1-A_H)/(1-A_L) * (1 - own/Pi) -> 100% if A_H=1; 75% if A_H=0.9 and own~0")
    print("   D scale: median firm stakes f=2, human reach a=20 -> value of reach f*a ~ 40")

    print("\n=== A2. Damages proportional to the firm's loss (D = delta*f), vendor of reach A=0.9, full information ===")
    print(" phi*delta | vendor price | profit | adopter share | top-decile adopters   (exclusion lifted when phi*delta >= a = 20)")
    for pdl in (0, 2, 5, 10, 15, 20, 25):
        pr, p, sh, top = indexed_warranty(0.9, pdl, 0.1)
        print(f"   {pdl:5.1f}   |    " + (f"{p:.2f}" if p else "withdraws") + f"      | {pr:6.3f} |    {sh:.2f}       |   {top:.2f}")

    print("\n=== B. Duopoly: tool 1 (reach A1) vs tool 2 (reach A2), simultaneous usage prices, k=0.1 ===")
    top = FG > np.exp(VM.MU + 1.2816 * VM.SIG)
    print(" A1   A2 | monopoly profit of tool 1 | Nash prices (p1,p2) | profits (1,2) | shares human/tool1/tool2 | top-decile on tools")
    for A1, A2 in ((1.0, 0.8), (1.0, 0.6), (0.9, 0.8), (0.9, 0.6)):
        grid, P1, P2, SH1, SH2, ne, mono = duopoly(A1, A2, 0.1)
        if not ne:
            print(f" {A1:.1f}  {A2:.1f} | {mono:.3f} | no pure-strategy equilibrium on the grid"); continue
        i, j = max(ne, key=lambda x: P1[x] + P2[x])
        cL1 = c0 + grid[i]; cL2 = c0 + grid[j]
        S1_ = FG * (A1 * a) * h(A1 * a * B * b * FG / cL1); S2_ = FG * (A2 * a) * h(A2 * a * B * b * FG / cL2)
        on_tool = (np.maximum(S1_, S2_) > S_H + 1e-9)
        print(f" {A1:.1f}  {A2:.1f} |    {mono:7.3f}    | ({grid[i]:.2f},{grid[j]:.2f})  ({len(ne)} NE) | ({P1[i,j]:.3f},{P2[i,j]:.3f}) | "
              f"{1-SH1[i,j]-SH2[i,j]:.2f}/{SH1[i,j]:.2f}/{SH2[i,j]:.2f} | {float((on_tool[top]*W[top]).sum()/W[top].sum()):.2f}")
