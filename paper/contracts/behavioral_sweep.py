import numpy as np
from contracts import Mkt
from behavioral import monopoly, bertrand
rng = np.random.default_rng(8); out = []; P = out.append
rows = []
for t in range(60):
    a = rng.uniform(.05, .5); b = np.exp(rng.uniform(np.log(.15), np.log(3))); H = np.exp(rng.uniform(np.log(50), np.log(300)))
    v = H*np.exp(rng.uniform(np.log(.003), np.log(.02))); k = v*np.exp(rng.uniform(np.log(.2), np.log(2)))
    m = Mkt(a, b, H, v, k, J=3000); fb = m.first_best()
    if fb['surplus'] < 1: continue
    for lam, gam in [(1., 0.), (1.5, 0.), (2.25, 0.), (1., 0.2), (1.5, 0.2), (2.25, 0.2)]:
        ra = monopoly(m, "A", lam, gam, grid=500); rb = monopoly(m, "B", lam, gam, grid=500)
        ba = bertrand(m, "A", lam, gam, grid=800); bb = bertrand(m, "B", lam, gam, grid=800)
        if None in (ra, rb) or bb is None: continue
        rows.append(dict(lam=lam, gam=gam, vA=ra[1]['vend'], vB=rb[1]['vend'], sA=ra[1]['saving'], sB=rb[1]['saving'], wA=ra[1]['welfare']/fb['surplus'], wB=rb[1]['welfare']/fb['surplus'],
                         bwA=ba[1]['welfare']/fb['surplus'], bwB=bb[1]['welfare']/fb['surplus'], bNA=ba[1]['N']/max(fb['N'],1), bNB=bb[1]['N']/max(fb['N'],1)))
P(f"Behavioral sweep: {len(set(id(r) for r in rows))} cells over 60 parameter draws x 6 (Lambda, gamma) combinations")
P("Lambda gamma | MONOPOLY: vendor prefers success fee | firm saving higher under per-attempt | welfare/FB A, B (median) || BERTRAND: welfare/FB A, B (median) | depth/FB A, B (median)")
for lam, gam in [(1., 0.), (1.5, 0.), (2.25, 0.), (1., 0.2), (1.5, 0.2), (2.25, 0.2)]:
    R = [r for r in rows if r['lam'] == lam and r['gam'] == gam]
    P(f" {lam:4.2f}  {gam:4.2f} |  {100*np.mean([r['vB']>=r['vA'] for r in R]):4.0f}%  |  {100*np.mean([r['sA']>r['sB'] for r in R]):4.0f}%  |  {np.median([r['wA'] for r in R]):.2f}, {np.median([r['wB'] for r in R]):.2f} || {np.median([r['bwA'] for r in R]):.3f}, {np.median([r['bwB'] for r in R]):.3f} | {np.median([r['bNA'] for r in R]):.2f}, {np.median([r['bNB'] for r in R]):.2f}   (cells {len(R)})")
# offset condition: Lambda*(gamma) = ((k+v)/(1-gamma) - v)/k  => per-attempt Bertrand depth equals first best
cnt = 0; tot = 0
for t in range(200):
    a = rng.uniform(.05, .5); b = np.exp(rng.uniform(np.log(.15), np.log(3))); H = np.exp(rng.uniform(np.log(50), np.log(300)))
    v = H*np.exp(rng.uniform(np.log(.003), np.log(.02))); k = v*np.exp(rng.uniform(np.log(.2), np.log(2)))
    m = Mkt(a, b, H, v, k, J=3000); fb = m.first_best()
    if fb['N'] < 3: continue
    gam = rng.uniform(.05, .6); lam = ((k+v)/(1-gam) - v)/k
    from behavioral import depth
    N = depth(m, "A", k, lam, gam); tot += 1; cnt += abs(N - fb['N']) <= 1
P(f"\nOffset condition Lambda*(gamma) = [(k+v)/(1-gamma) - v]/k gives per-attempt Bertrand depth within one attempt of first best (N^FB>=3): {cnt} of {tot} draws")
open("results_behavioral_sweep.txt", "w").write("\n".join(out)); print("\n".join(out))
