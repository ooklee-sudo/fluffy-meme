import numpy as np
from asymmetric import Game
rng = np.random.default_rng(3)
def sep_best(g, fl, t_l):
    best = None
    for kind in "AB":
        for p in g.grid(kind):
            N = g.N(kind, p, 1)
            if g.firm_cost(g.TH, kind, p, N) > g.H: continue
            ph = g.prof(g.TH, kind, p, N); pl = g.prof(g.TL, kind, p, N)
            if pl <= fl[0] + 1e-9 and ph > t_l[0] + 1e-6 and (best is None or ph > best[0]): best = (ph, kind, p, N, pl)
    return best
rows = []
for i in range(60):
    aL = rng.uniform(.03, .2); aH = aL + rng.uniform(.08, .35); b = np.exp(rng.uniform(np.log(.15), np.log(2)))
    H = np.exp(rng.uniform(np.log(50), np.log(300))); v = H*np.exp(rng.uniform(np.log(.003), np.log(.02))); k = v*np.exp(rng.uniform(np.log(.2), np.log(2)))
    g = Game(aH, aL, b, H, v, k, .5); fh, fl, t_l = g.FI(g.TH, 1), g.FI(g.TL, 0), g.FI(g.TH, 0)
    if None in (fh, fl, t_l): continue
    sb = sep_best(g, fl, t_l)
    # does low mimic the H full-info contract? (IC_L slack at FI?)
    N_fi = g.N(fh[1], fh[2], 1); mim = g.prof(g.TL, fh[1], fh[2], N_fi)
    W=lambda T,kind,p,N: g.H-g.firm_cost(T,kind,p,N)+g.prof(T,kind,p,N)
    Wfi=W(g.TH,fh[1],fh[2],fh[3]); Wsep=(W(g.TH,sb[1],sb[2],sb[3]) if sb else None)
    rows.append(dict(wsep=(Wsep/Wfi if sb else None), fsav_fi=g.H-g.firm_cost(g.TH,fh[1],fh[2],fh[3]), fsav_sep=(g.H-g.firm_cost(g.TH,sb[1],sb[2],sb[3]) if sb else None), aH=aH, aL=aL, b=b, H=H, sep=sb is not None, sepkind=(sb[1] if sb else None), distort=(fh[0]-sb[0])/fh[0] if sb else None,
                     mimic_fi=mim > fl[0] + 1e-9, N_fh=fh[3], N_sep=(sb[3] if sb else None), kind_fh=fh[1], kind_fl=fl[1], gain_vs_tl=((sb[0]-t_l[0])/t_l[0] if sb else None)))
n = len(rows); sep = [r for r in rows if r['sep']]
print(f"draws {n}; separating linear contract exists: {len(sep)} ({100*len(sep)/n:.0f}%); kind(s): {set(r['sepkind'] for r in sep)}")
print(f"FI contract of high type chosen from: {set(r['kind_fh'] for r in rows)}; low type: {set(r['kind_fl'] for r in rows)}")
print(f"Low type would mimic H's full-info contract (IC_L violated) in {100*np.mean([r['mimic_fi'] for r in rows]):.0f}% of draws")
d = [r['distort'] for r in sep]; print(f"H-type profit loss from separation vs FI: median {100*np.median(d):.1f}% (IQR {100*np.percentile(d,25):.1f}-{100*np.percentile(d,75):.1f}%)")
print(f"H-type gain from separating vs being treated as low: median {100*np.median([r['gain_vs_tl'] for r in sep]):.1f}%")
ex = [r for r in sep if r['distort'] > 1e-6][:1] or sep[:1]
print("example:", {k: (round(v,3) if isinstance(v,float) else v) for k, v in ex[0].items()})
import json; open("results_asym_sweep.txt","w").write(f"draws {n}; separating exists {len(sep)}; median distortion {100*np.median(d):.1f}%; low would mimic FI contract in {100*np.mean([r['mimic_fi'] for r in rows]):.0f}%\n")

w=[r['wsep'] for r in sep]; print(f"Welfare of high type under separation relative to full information: median {np.median(w):.2f} (share of draws with higher welfare: {100*np.mean([x>1 for x in w]):.0f}%)")
fs=[r['fsav_sep']-r['fsav_fi'] for r in sep]; print(f"Firm saving (high type) separation minus FI: median {np.median(fs):.2f}; firm better off in {100*np.mean([x>0 for x in fs]):.0f}% of draws")
print(f"Attempt budget N_sep >= N_FI in {100*np.mean([r['N_sep']>=r['N_fh'] for r in sep]):.0f}% of draws")
open("results_asym_sweep.txt","a").write(f"welfare sep/FI median {np.median(w):.2f}; share higher {100*np.mean([x>1 for x in w]):.0f}%; firm better off in {100*np.mean([x>0 for x in fs]):.0f}%; N_sep>=N_FI in {100*np.mean([r['N_sep']>=r['N_fh'] for r in sep]):.0f}%\n")
