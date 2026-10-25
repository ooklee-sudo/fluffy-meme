"""Vendor knows its quality a_theta (high/low, common b); firm does not. Contracts: per-attempt w (A) or success fee f (B).
Checks (i) profit-order reversal across contract types, (ii) separating (Riley-type) and pooling outcomes."""
import numpy as np
from scipy.special import betaln
J = 1500
GRID = 300
class Typ:
    def __init__(s, a, b): s.a, s.b = a, b; s.S = np.exp(betaln(a, b+np.arange(J+1)) - betaln(a, b)); s.cum = np.concatenate([[0], np.cumsum(s.S)])
    def E(s, N): return s.cum[N]
    def P(s, N): return 1 - s.S[N]
def mix_q(mu, TH, TL):               # posterior predictive success after n failures under belief mu on high type
    n = np.arange(J)
    wH = mu*TH.S[:J]; wL = (1-mu)*TL.S[:J]
    qH = TH.a/(TH.a+TH.b+n); qL = TL.a/(TL.a+TL.b+n)
    return (wH*qH + wL*qL)/(wH + wL)
def N_firm(q, X, Y):                 # continue at n iff q_n*X > Y ; q decreasing
    idx = np.nonzero(q*X <= Y)[0]; return int(idx[0]) if len(idx) else J-1
class Game:
    def __init__(s, aH, aL, b, H, v, k, mu):
        s.TH, s.TL, s.H, s.v, s.k, s.mu = Typ(aH, b), Typ(aL, b), H, v, k, mu
    def N(s, kind, price, belief_mu):            # firm's budget given contract and belief (belief_mu = P(high))
        q = mix_q(belief_mu, s.TH, s.TL)
        return N_firm(q, s.H, price + s.v) if kind == "A" else N_firm(q, s.H - price, s.v)
    def prof(s, T, kind, price, N): return (price - s.k)*T.E(N) if kind == "A" else price*T.P(N) - s.k*T.E(N)
    def firm_cost(s, T, kind, price, N):
        if kind == "A": return (price + s.v)*T.E(N) + s.H*(1 - T.P(N))
        return s.v*T.E(N) + price*T.P(N) + s.H*(1 - T.P(N))
    def grid(s, kind): return np.linspace(s.k if kind == "A" else 0, s.H, GRID)
    def FI(s, T, belief):                          # vendor's best contract when firm's belief is 'belief' (1=high,0=low); firm participation evaluated at believed type
        best = None
        for kind in "AB":
            for p in s.grid(kind):
                N = s.N(kind, p, belief)
                Tb = s.TH if belief == 1 else s.TL
                if s.firm_cost(Tb, kind, p, N) > s.H: continue      # firm rejects if believed cost exceeds human-only
                pr = s.prof(T, kind, p, N)
                if best is None or pr > best[0]: best = (pr, kind, p, N)
        return best
if __name__ == "__main__":
    out = []; Pr = out.append
    aH, aL, b, H, v, k, mu = .25, .08, .35, 100., 1., .2, .5
    g = Game(aH, aL, b, H, v, k, mu)
    # (i) profit order for a common budget N
    Pr("(i) Profit order for a common attempt budget N (b=.35, H=100, k=.2): per-attempt w=10  /  success fee f=50")
    for N in [1, 3, 10, 30]:
        Pr(f"  N={N:3d}: A: low {g.prof(g.TL,'A',10,N):6.2f} high {g.prof(g.TH,'A',10,N):6.2f} | B: low {g.prof(g.TL,'B',50,N):6.2f} high {g.prof(g.TH,'B',50,N):6.2f}")
    # (ii) full information
    fiH, fiL = g.FI(g.TH, 1), g.FI(g.TL, 0)
    Pr(f"\n(ii) Full-information optimum  high: profit {fiH[0]:.2f} via {fiH[1]} price {fiH[2]:.1f} N={fiH[3]}   low: profit {fiL[0]:.2f} via {fiL[1]} price {fiL[2]:.1f} N={fiL[3]}")
    # treated-as-low payoff for high type = what it earns if firm believes low
    tl = g.FI(g.TH, 0); Pr(f"     High type if believed low: profit {tl[0]:.2f} ({tl[1]} price {tl[2]:.1f}, N={tl[3]})")
    # separating: H picks contract (kind,p) with belief=1 s.t. L's mimic profit <= L's FI profit
    best = None; rows = []
    for kind in "AB":
        for p in g.grid(kind):
            N = g.N(kind, p, 1)
            if g.firm_cost(g.TH, kind, p, N) > g.H: continue
            ph = g.prof(g.TH, kind, p, N); pl = g.prof(g.TL, kind, p, N)
            if pl <= fiL[0] + 1e-9 and ph >= tl[0] - 1e-9:
                if best is None or ph > best[0]: best = (ph, kind, p, N, pl)
    if best is None:
        Pr("\nSeparating (Riley-type): NO linear contract satisfies both the low type's no-mimicry and the high type's participation-in-separation constraints")
        best = (tl[0], tl[1], tl[2], tl[3], 0.0)
    else:
        Pr(f"\nSeparating (Riley-type): high type's best IC contract: {best[1]} price {best[2]:.1f}, N={best[3]}, high profit {best[0]:.2f} (FI {fiH[0]:.2f}), low mimic profit {best[4]:.2f} <= low FI {fiL[0]:.2f}")
    # pooling at prior: single contract maximizing expected vendor profit with belief=mu
    bp = None
    for kind in "AB":
        for p in g.grid(kind):
            N = g.N(kind, p, mu); Tm = None
            cost_m = mu*g.firm_cost(g.TH, kind, p, N) + (1-mu)*g.firm_cost(g.TL, kind, p, N)
            if cost_m > g.H: continue
            ev = mu*g.prof(g.TH, kind, p, N) + (1-mu)*g.prof(g.TL, kind, p, N)
            if bp is None or ev > bp[0]: bp = (ev, kind, p, N, g.prof(g.TH, kind, p, N), g.prof(g.TL, kind, p, N))
    Pr(f"Pooling benchmark: expected-profit-maximizing single contract {bp[1]} price {bp[2]:.1f}, N={bp[3]}, profits high {bp[4]:.2f} low {bp[5]:.2f}")
    # welfare comparison (surplus = H - firm cost + vendor profit), per type
    def W(T, kind, p, N): return g.H - g.firm_cost(T, kind, p, N) + g.prof(T, kind, p, N)
    Pr("\nWelfare (surplus vs human-only) by true type:")
    Pr(f"  full info:  high {W(g.TH,fiH[1],fiH[2],fiH[3]):.2f}  low {W(g.TL,fiL[1],fiL[2],fiL[3]):.2f}")
    Pr(f"  separating: high {W(g.TH,best[1],best[2],best[3]):.2f}  low {W(g.TL,fiL[1],fiL[2],fiL[3]):.2f}")
    Pr(f"  pooling:    high {W(g.TH,bp[1],bp[2],bp[3]):.2f}  low {W(g.TL,bp[1],bp[2],bp[3]):.2f}")
    Pr("  firm saving (H - cost): " + f"full info high {g.H-g.firm_cost(g.TH,fiH[1],fiH[2],fiH[3]):.2f}, low {g.H-g.firm_cost(g.TL,fiL[1],fiL[2],fiL[3]):.2f}; separating high {g.H-g.firm_cost(g.TH,best[1],best[2],best[3]):.2f}; pooling high {g.H-g.firm_cost(g.TH,bp[1],bp[2],bp[3]):.2f} low {g.H-g.firm_cost(g.TL,bp[1],bp[2],bp[3]):.2f}")
    open("results_asymmetric.txt", "w").write("\n".join(out)); print("\n".join(out))

    # ---- sweep: does a separating linear contract exist? ----
    rng = np.random.default_rng(3); cnt = dict(n=0, sep=0, sepB=0, A_profit_low_ge=0, ordB=0)
    for _ in range(60):
        aL_ = rng.uniform(.03, .2); aH_ = aL_ + rng.uniform(.08, .35); b_ = np.exp(rng.uniform(np.log(.15), np.log(2)))
        H_ = np.exp(rng.uniform(np.log(50), np.log(300))); v_ = H_*np.exp(rng.uniform(np.log(.003), np.log(.02))); k_ = v_*np.exp(rng.uniform(np.log(.2), np.log(2)))
        gg = Game(aH_, aL_, b_, H_, v_, k_, .5)
        fl = gg.FI(gg.TL, 0); t_l = gg.FI(gg.TH, 0)
        if fl is None or t_l is None: continue
        cnt["n"] += 1; ok = None
        for kind in "AB":
            for p in gg.grid(kind):
                N = gg.N(kind, p, 1)
                if gg.firm_cost(gg.TH, kind, p, N) > gg.H: continue
                ph = gg.prof(gg.TH, kind, p, N); pl = gg.prof(gg.TL, kind, p, N)
                if pl <= fl[0] + 1e-9 and ph > t_l[0] + 1e-6: ok = (kind, p)
        if ok: cnt["sep"] += 1; cnt["sepB"] += ok[0] == "B"
    print("\nSweep (60 draws): separating linear contract exists in", cnt["sep"], "of", cnt["n"], "draws; of which success-fee:", cnt["sepB"])
    open("results_asymmetric.txt", "a").write(f"\nSweep: separating linear contract exists in {cnt['sep']} of {cnt['n']} draws (success-fee type in {cnt['sepB']})\n")
