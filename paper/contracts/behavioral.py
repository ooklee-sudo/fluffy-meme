"""Behavioral firm: (i) loss aversion on pay-per-use payments (Lambda >= 1): per-attempt fee w is felt as Lambda*w, whereas the success fee is netted against the avoided human cost (no loss weight);
(ii) sunk-cost fallacy (gamma in [0,1)): after any prior attempt, the perceived marginal cost of another attempt is (1-gamma)*Y.
Decision utility (perceived) drives the firm's adoption and depth; welfare is computed from experienced (actual) costs."""
import numpy as np
from contracts import Mkt
def depth(m, kind, price, lam, gam):
    X = m.H if kind == "A" else m.H - price
    Y = (lam*price + m.v) if kind == "A" else m.v
    if X <= 0 or m.a/(m.a + m.b)*X <= Y: return 0
    n = int(np.ceil(m.a*X/((1-gam)*Y) - m.a - m.b)); return int(min(max(1, n), len(m.S)-1))
def outcome(m, kind, price, lam, gam):
    N = depth(m, kind, price, lam, gam)
    E, P = m.att(N), m.P(N)
    if kind == "A":
        actual = (price + m.v)*E + m.H*(1-P); perceived = (lam*price + m.v)*E + m.H*(1-P); vend = (price-m.k)*E
    else:
        actual = m.v*E + price*P + m.H*(1-P); perceived = actual; vend = price*P - m.k*E
    return dict(N=N, adopt=perceived <= m.H + 1e-12, saving=m.H-actual, vend=vend, welfare=m.H-actual+vend)
def monopoly(m, kind, lam, gam, grid=1500):
    ps = np.linspace(m.k if kind == "A" else 0, m.H, grid); best = None
    for p in ps:
        o = outcome(m, kind, p, lam, gam)
        if not o['adopt']: continue
        if best is None or o['vend'] > best[1]['vend']: best = (p, o)
    return best
def bertrand(m, kind, lam, gam, grid=3000):
    if kind == "A": p = m.k; return p, outcome(m, "A", p, lam, gam)
    fs = np.linspace(0, m.H, grid)
    for f in fs:
        o = outcome(m, "B", f, lam, gam)
        if o['adopt'] and o['vend'] >= 0: return f, o
    return None
if __name__ == "__main__":
    out = []; P = out.append
    m = Mkt(.12, .39, 100., 1., .2); fb = m.first_best()
    P(f"RepairBench-like (a=.12,b=.39) H=100 v=1 k=.2; first-best N={fb['N']} surplus={fb['surplus']:.1f}")
    P("\nMONOPOLY. columns: price, depth N, vendor profit, firm experienced saving, welfare % of first best")
    P(" Lambda gamma | per-attempt                                   | success fee")
    for lam in [1.0, 1.5, 2.25]:
        for gam in [0.0, 0.2, 0.5]:
            ra = monopoly(m, "A", lam, gam); rb = monopoly(m, "B", lam, gam)
            f = lambda r: f"{r[0]:6.2f} N={r[1]['N']:3d} vend {r[1]['vend']:6.2f} firm {r[1]['saving']:6.2f} W {100*r[1]['welfare']/fb['surplus']:5.1f}%"
            P(f"  {lam:4.2f}  {gam:4.2f} | {f(ra)} | {f(rb)}")
    P("\nBERTRAND (zero profit). Per-attempt w=k; success fee at the zero-profit fee.")
    P(" Lambda gamma | per-attempt: N, welfare%FB, firm saving | success fee: f0, N, welfare%FB, firm saving")
    for lam in [1.0, 1.5, 2.25]:
        for gam in [0.0, 0.2, 0.5]:
            pa, oa = bertrand(m, "A", lam, gam); pb, ob = bertrand(m, "B", lam, gam)
            P(f"  {lam:4.2f}  {gam:4.2f} | N={oa['N']:3d} W {100*oa['welfare']/fb['surplus']:5.1f}%  firm {oa['saving']:6.2f} | f0={pb:5.2f} N={ob['N']:3d} W {100*ob['welfare']/fb['surplus']:5.1f}% firm {ob['saving']:6.2f}")
    open("results_behavioral.txt", "w").write("\n".join(out)); print("\n".join(out))
