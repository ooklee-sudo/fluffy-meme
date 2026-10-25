"""Table 2 of the manuscript: incentive rent at the first-best depth (H=100, v=1, k=0.2)."""
import numpy as np
from scipy.special import betaln
H, v, k = 100., 1., .2
out = []; P = out.append
P("Heterogeneity (a,b) | N^FB | W(N^FB) | G_min(N^FB) | R(N^FB) | Rent/W(N^FB) | vendor-optimal depth n_hat, R(n_hat)")
for name, (a, b) in {"RepairBench-like": (.12, .39), "SWE-Verified-like": (.25, .34), "Synthetic": (.40, 3.0)}.items():
    J = 600; n = np.arange(J+1)
    S = np.exp(betaln(a, b+n) - betaln(a, b)); E = np.concatenate([[0], np.cumsum(S)])[:J+1]; Pn = 1 - S
    q = a/(a+b+np.arange(J))
    W = lambda N: H*Pn[N] - (k+v)*E[N]
    G = lambda N: v*(Pn[N]/q[N-1] - E[N]); R = lambda N: W(N) - G(N)
    nfb = int(np.argmax([W(N) for N in range(J)]))
    nhat = max(range(1, J), key=R)
    P(f"{name} ({a},{b}) | {nfb} | {W(nfb):.1f} | {G(nfb):.1f} | {R(nfb):.1f} | {100*G(nfb)/W(nfb):.0f}% | {nhat}, {R(nhat):.1f}")
open("results_incentive_rent.txt", "w").write("\n".join(out)); print("\n".join(out))
