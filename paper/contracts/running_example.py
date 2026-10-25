import numpy as np
from scipy.special import betaln
from scipy.stats import beta as B
a, b, H, v, k = .12, .39, 100., 1., .2
J = 400; n = np.arange(J+1)
S = np.exp(betaln(a, b+n) - betaln(a, b)); E = np.concatenate([[0], np.cumsum(S)])[:J+1]; P = 1 - S
q = a/(a+b+np.arange(J))
W = lambda N: H*P[N] - (k+v)*E[N]
G = lambda N: v*(P[N]/q[N-1] - E[N]); R = lambda N: W(N) - G(N)
phi = lambda N: H - v/q[N-1]
out = []; Pr = out.append
Pr(f"Beta({a},{b}); H={H}, v={v}, k={k}; prior mean success {a/(a+b):.3f}")
Pr("q_n (success prob of attempt n+1 after n failures): " + ", ".join(f"n={i}: {q[i]:.4f}" for i in (0,1,2,3,4,5,9,10,19,29)))
Pr(f"posterior mean after 10 failures {q[10]:.4f}; after 30 failures {q[30]:.4f}")
Pr("fraction of defects with p<0.01: %.2f ; p<0.05: %.2f ; p>0.5: %.2f ; p>0.9: %.2f" % (B.cdf(.01,a,b), B.cdf(.05,a,b), 1-B.cdf(.5,a,b), 1-B.cdf(.9,a,b)))
Pr(f"marginal value q_n*H vs efficient cost k+v = {k+v}: attempt 10 (n=9): {q[9]*H:.2f}; attempt 11 (n=10): {q[10]*H:.2f}")
Pr("N | P(N) | E(N) | W(N) | G_min(N) | R(N) | phi_(N-1)")
for N in (1,2,3,5,10,20):
    Pr(f"{N:2d} | {P[N]:.3f} | {E[N]:.2f} | {W(N):.2f} | {G(N):.2f} | {R(N):.2f} | {phi(N):.1f}")
Pr(f"per-attempt monopoly price q_0 H - v = {q[0]*H - v:.2f}; success fee at step 3: phi_2 = {phi(3):.1f}")
Pr(f"human-only per 1,000 defects: ${H*1000:,.0f}; first best N=10: W=${W(10)*1000:,.0f}")
open("results_running_example.txt", "w").write("\n".join(out)); print("\n".join(out))
# figure
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams.update({"font.size": 8.5, "font.family": "serif"})
fig, ax = plt.subplots(1, 2, figsize=(6.5, 2.9), constrained_layout=True)
nn = np.arange(0, 31)
ax[0].semilogy(nn, q[nn]*H, "k-o", ms=3, lw=1, label="Marginal value of the next attempt, $q_n H$")
ax[0].axhline(k+v, color="0.4", ls="--", lw=1, label="Efficient cost $k+v$ (first best: 10 attempts)")
ax[0].axhline(q[0]*H, color="0.7", ls=":", lw=1)
ax[0].set_xlabel("failures so far, $n$"); ax[0].set_ylabel("dollars"); ax[0].set_title("(a) Failures are bad news", fontsize=9, loc="left")
ax[0].legend(fontsize=6.5, loc="upper right", frameon=False)
Ns = [1, 2, 3, 5, 10]; Rv = [R(N) for N in Ns]; Gv = [G(N) for N in Ns]
x = np.arange(len(Ns)); ax[1].bar(x, Rv, color="0.25", label="Most the vendor can keep, $R(N)$"); ax[1].bar(x, Gv, bottom=Rv, color="0.75", label="Rent the firm must keep, $G_{min}(N)$")
ax[1].set_xticks(x); ax[1].set_xticklabels([f"N={N}" for N in Ns]); ax[1].set_ylabel("dollars per defect"); ax[1].set_title("(b) Surplus $W(N)$ and its split", fontsize=9, loc="left")
ax[1].set_ylim(0, 48); ax[1].legend(fontsize=6.5, loc="upper left", frameon=False)
fig.savefig("fig_intuition.png", dpi=220); print("saved")
