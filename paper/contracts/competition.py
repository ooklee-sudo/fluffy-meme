"""Competition among n vendors (homogeneous quality, marginal cost k). Reduced form: equilibrium markup over the competitive price is (monopoly markup)/n,
n=1 monopoly, n->inf Bertrand. A: w_n = k + (w_m - k)/n.  B: f_n = f_0 + (f_m - f_0)/n, where f_0 is the zero-profit (Bertrand) success fee."""
import numpy as np
from contracts import Mkt, solve
NS = [1, 2, 3, 5, 10, 1000]
def zero_profit_fee(m, grid=4000):
    fs = np.linspace(0, m.H, grid)
    for f in fs:                                   # smallest fee with non-negative vendor profit and firm participation
        r = m.success_fee(f)
        if r['vend'] >= 0 and r['firm'] <= m.H: return f
    return None
def table(m):
    fb, bw, bf, ef = solve(m, grid=1500); f0 = zero_profit_fee(m); rows = []
    for n in NS:
        w = m.k + (bw['w'] - m.k)/n; f = f0 + (bf['f'] - f0)/n
        a = m.per_attempt(w); b = m.success_fee(f)
        rows.append((n, w, a, f, b))
    return fb, f0, ef, rows
if __name__ == "__main__":
    out = []; P = out.append
    for name, (a, b) in {"RepairBench-like (0.12,0.39)": (.12, .39), "SWE-Verified-like (0.25,0.34)": (.25, .34), "Synthetic (0.40,3.0)": (.4, 3.)}.items():
        m = Mkt(a, b, 100., 1., .2); fb, f0, ef, rows = table(m)
        P(f"{name}  H=100 v=1 k=0.2 | first-best N={fb['N']} S^FB={fb['surplus']:.1f} | efficient fee f^e={ef['f']:.2f} | zero-profit (Bertrand) fee f0={f0:.2f}")
        P("   n   | per-attempt: w     N   welfare%FB  firm saving  vendor | success fee: f     N   welfare%FB  firm saving  vendor")
        for n, w, A, f, B in rows:
            P(f"  {n:4d} |            {w:6.2f} {A['N']:4d}   {100*A['welfare']/fb['surplus']:6.1f}     {m.H-A['firm']:8.2f}  {A['vend']:7.2f} |          {f:6.2f} {B['N']:4d}   {100*B['welfare']/fb['surplus']:6.1f}     {m.H-B['firm']:8.2f}  {B['vend']:7.2f}")
        P("")
    # sweep: welfare shares and crossover
    rng = np.random.default_rng(11); res = {n: ([], []) for n in NS}; over = []; cross = []; firm_prefers_A = {n: [] for n in NS}
    for _ in range(200):
        a = rng.uniform(.05, .6); b = np.exp(rng.uniform(np.log(.1), np.log(4))); H = np.exp(rng.uniform(np.log(30), np.log(500)))
        v = H*np.exp(rng.uniform(np.log(.001), np.log(.03))); k = v*np.exp(rng.uniform(np.log(.1), np.log(3)))
        m = Mkt(a, b, H, v, k, J=3000); fb, f0, ef, rows = table(m)
        if fb['surplus'] <= 1e-6 or f0 is None: continue
        for n, w, A, f, B in rows:
            res[n][0].append(A['welfare']/fb['surplus']); res[n][1].append(B['welfare']/fb['surplus']); firm_prefers_A[n].append((m.H-A['firm']) >= (m.H-B['firm']))
        over.append(rows[-1][4]['N'] / max(fb['N'], 1))
        first = next((n for n, w, A, f, B in rows if A['welfare'] >= B['welfare']), None); cross.append(first)
    P(f"Random sweep ({len(over)} draws): welfare as share of first-best, median [IQR]")
    P("   n  | per-attempt            | success fee            | firm saving higher under per-attempt")
    for n in NS:
        a_, b_ = np.array(res[n][0]), np.array(res[n][1])
        P(f"  {n:4d} | {np.median(a_):.2f} [{np.percentile(a_,25):.2f}-{np.percentile(a_,75):.2f}]   | {np.median(b_):.2f} [{np.percentile(b_,25):.2f}-{np.percentile(b_,75):.2f}]   | {100*np.mean(firm_prefers_A[n]):.0f}%")
    P(f"Under Bertrand success fees the firm samples N_B(f0)/N^FB = {np.median(over):.2f}x the first-best depth (median)")
    cs = [c for c in cross if c is not None]; P(f"Smallest n at which per-attempt welfare >= success-fee welfare: median n={np.median(cs):.0f}; share of draws where it happens by n=3: {100*np.mean([c<=3 for c in cs]):.0f}%, by n=10: {100*np.mean([c<=10 for c in cs]):.0f}% (of {len(cross)} draws, {len(cross)-len(cs)} never)")
    open("results_competition.txt", "w").write("\n".join(out)); print("\n".join(out))
