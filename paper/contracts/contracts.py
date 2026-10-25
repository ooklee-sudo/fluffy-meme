"""Stackelberg contract analysis: vendor (leader) sets a per-attempt fee w or a success fee f; firm (follower) picks its attempt cap N.
Units: dollars. a,b: Beta heterogeneity; H: human fix cost; v: firm's own cost per attempt (test run/triage); k: vendor marginal cost per attempt."""
import numpy as np
from scipy.special import betaln

def surv(a, b, J): return np.exp(betaln(a, b + np.arange(J + 1)) - betaln(a, b))   # S(0..J)
class Mkt:
    def __init__(s, a, b, H, v, k, J=4000):
        s.a, s.b, s.H, s.v, s.k = a, b, H, v, k; s.S = surv(a, b, J); s.cum = np.concatenate([[0], np.cumsum(s.S)])
    def att(s, N): return s.cum[N]                 # E[min(T,N)]
    def P(s, N): return 1 - s.S[N]                 # P(solved within N)
    def Nstar(s, ratio): return int(min(max(0, np.ceil(s.a*ratio - s.a - s.b)), len(s.S)-1))   # ratio = (H or H-f)/(firm per-attempt cost)
    # --- contracts ---
    def per_attempt(s, w):
        N = s.Nstar(s.H/(s.w_c(w)));  c = w + s.v
        firm = c*s.att(N) + s.H*(1 - s.P(N)); vend = (w - s.k)*s.att(N)
        return dict(N=N, firm=firm, vend=vend, welfare=s.H - firm + vend - 0)   # welfare = total savings vs human (firm saving + vendor profit)
    def w_c(s, w): return w + s.v
    def success_fee(s, f):
        N = s.Nstar((s.H - f)/s.v)
        firm = s.v*s.att(N) + f*s.P(N) + s.H*(1 - s.P(N)); vend = f*s.P(N) - s.k*s.att(N)
        return dict(N=N, firm=firm, vend=vend, welfare=s.H - firm + vend)
    def first_best(s):
        N = s.Nstar(s.H/(s.k + s.v)); cost = (s.k + s.v)*s.att(N) + s.H*(1 - s.P(N))
        return dict(N=N, cost=cost, surplus=s.H - cost)

def solve(m, grid=2000):
    fb = m.first_best()
    ws = np.linspace(m.k, m.H, grid); best_w = max((m.per_attempt(w) | dict(w=w) for w in ws if m.per_attempt(w)['firm'] <= m.H), key=lambda r: r['vend'])
    fs = np.linspace(0, m.H, grid); best_f = max((m.success_fee(f) | dict(f=f) for f in fs if m.success_fee(f)['firm'] <= m.H), key=lambda r: r['vend'])
    f_eff = m.H*m.k/(m.k + m.v); eff = m.success_fee(f_eff) | dict(f=f_eff)
    return fb, best_w, best_f, eff

if __name__ == "__main__":
    out = []; P = out.append
    scen = {"RepairBench-like (a=.12,b=.39)": (.12, .39), "SWE-Verified-like (a=.25,b=.34)": (.25, .34), "Synthetic easy (a=.4,b=3)": (.4, 3.0)}
    for name, (a, b) in scen.items():
        for (H, v, k) in [(100, 1.0, 0.2), (100, 1.0, 1.0), (300, 2.0, 0.5), (100, 0.2, 0.2)]:
            m = Mkt(a, b, H, v, k); fb, bw, bf, ef = solve(m)
            P(f"{name} | H={H} v={v} k={k}")
            P(f"   first-best: N={fb['N']:4d} surplus={fb['surplus']:7.2f}")
            P(f"   per-attempt (monopoly w*={bw['w']:.2f}): N={bw['N']:4d} vendor={bw['vend']:6.2f} firm_saving={m.H-bw['firm']:6.2f} welfare={bw['welfare']:7.2f} ({100*bw['welfare']/fb['surplus']:.0f}% of FB)")
            P(f"   success-fee (monopoly f*={bf['f']:.2f}): N={bf['N']:4d} vendor={bf['vend']:6.2f} firm_saving={m.H-bf['firm']:6.2f} welfare={bf['welfare']:7.2f} ({100*bf['welfare']/fb['surplus']:.0f}% of FB)")
            P(f"   success-fee at efficient f=Hk/(k+v)={ef['f']:.2f}: N={ef['N']:4d} vendor={ef['vend']:6.2f} firm_saving={m.H-ef['firm']:6.2f} welfare={ef['welfare']:7.2f}")
            P("")
    open("results_contracts.txt", "w").write("\n".join(out)); print("\n".join(out))
