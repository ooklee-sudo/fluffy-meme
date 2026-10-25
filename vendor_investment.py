"""Endogenous reach: the vendor invests to raise reach A before setting its (usage) price.

Stage 1: vendor chooses reach A at cost I(A) = (theta/2) * (A - A0)^2   (A0 = 0.5 is the starting reach).
Stage 2: given A, the vendor sets the profit-maximising usage price p (complete information, monopoly).
Pi*(A)  : stage-2 profit.   CS(A): firms' surplus over the human technology at that price.   W = Pi* + CS - I.

Run: python3 vendor_investment.py
"""
import numpy as np
import vendor_model as VM

kv = VM.kv
PS = np.linspace(kv + 0.01, 3.0, 240)
A0 = 0.5


def stage2(A):
    """Best price, profit, firms' surplus and adopter share for reach A."""
    best = (0.0, None, 0.0, 0.0)
    for p in PS:
        pr, sh = VM.profit(p, A=A)
        if pr > best[0]:
            ad = VM.adopters(p, A, VM.B)
            V = VM.V(VM.FGRID, p, A, VM.B)
            best = (pr, p, float((np.where(ad, V, 0.0) * VM.W).sum()), sh)
    return best


if __name__ == "__main__":
    As = np.round(np.arange(0.5, 1.301, 0.02), 3)
    tab = {A: stage2(A) for A in As}
    print(" A    price  profit Pi*(A)  firm surplus CS  adopter share")
    for A in As[::2]:
        pr, p, cs, sh = tab[A]
        print(f" {A:.2f}  {('%.2f' % p) if p else '  - ':>5}   {pr:8.3f}     {cs:8.3f}        {sh:.2f}")
    prof = np.array([tab[A][0] for A in As])
    d1 = np.gradient(prof, As)
    d2 = np.gradient(d1, As)
    print("\nPi*(A): max slope %.1f at A=%.2f ; convex (d2>0) for A in [%.2f, %.2f]" % (
        d1.max(), As[d1.argmax()], As[d2 > 0].min() if (d2 > 0).any() else np.nan, As[d2 > 0].max() if (d2 > 0).any() else np.nan))
    inf = As[np.where((d2[:-1] > 0) & (d2[1:] <= 0))[0]]
    print("inflection (convex -> concave) near A =", np.round(inf, 2))
    print("Pi*(0.90)=%.3f  Pi*(0.96)=%.3f  Pi*(1.00)=%.3f  Pi*(1.10)=%.3f ; ratio Pi*(1.0)/Pi*(0.9) = %.1f" % (
        tab[0.9][0], tab[0.96][0], tab[1.0][0], tab[1.1][0], tab[1.0][0] / tab[0.9][0]))

    cs = np.array([tab[A][1 + 1] for A in As])
    def opt(theta, welfare=False, subsidy=0.0):
        cost = (1 - subsidy) * 0.5 * theta * (As - A0) ** 2
        obj = (prof + (cs if welfare else 0.0)) - cost
        i = obj.argmax()
        return As[i], obj[i]
    print("\nPrivate vs social optimal reach as the cost of reach theta falls:")
    print(" theta | private A*  vendor net | social A_s  welfare | share of firms adopting at A*")
    for th in (400, 200, 150, 120, 100, 80, 60, 45, 35, 25, 15, 8):
        a_p, v_p = opt(th); a_s, w_s = opt(th, True)
        print(f" {th:5d} |   {a_p:.2f}     {v_p:8.3f}   |   {a_s:.2f}     {w_s:8.3f} |   {tab[a_p][3]:.2f}")
    # thresholds: largest theta at which the vendor chooses A >= 1
    ths = np.exp(np.linspace(np.log(5), np.log(600), 400))
    def thr(welfare=False, subsidy=0.0):
        ok = [t for t in ths if opt(t, welfare, subsidy)[0] >= 1.0 - 1e-9]
        return max(ok) if ok else float("nan")
    print("\ncritical cost theta^: vendor chooses A>=1 iff theta <= theta^")
    print("  private: %.0f | social planner: %.0f  -> window of costs where society wants A>=1 but the vendor does not: %.0f < theta <= %.0f" % (
        thr(), thr(True), thr(), thr(True)))
    for s in (0.1, 0.25, 0.5):
        print(f"  with R&D subsidy of {s:.0%} of the cost: private theta^ = {thr(False, s):.0f}")
    # how much does a small cost reduction change reach near the threshold
    th_c = thr()
    print("\nnear the private threshold (theta^=%.0f): reach chosen at theta^*1.05 = %.2f, at theta^ = %.2f, at theta^*0.95 = %.2f" % (
        th_c, opt(th_c * 1.05)[0], opt(th_c)[0], opt(th_c * 0.95)[0]))
