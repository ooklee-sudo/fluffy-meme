"""Monte Carlo checks of Theorems 1-5 under the paper's observation equation (3)-(4).

Illustrative parameters (value units are arbitrary): a=1, v0=0.5, Delta=0.2, ell=0.2, I=0.05, kappa=0.05,
sigma=0.15, cG=0.02. Then uH=0.15, uC=-0.30, pi*=(ell+I+kappa)/(Delta+ell+kappa)=0.667,
and the Theorem 1 flip is at beta = a(Delta+ell) = 0.40.
Rules (single candidate per episode, cheat with prob s):
  never   : keep incumbent, gain 0
  NPV     : promote iff J > a*v0 (incumbent quote)
  options : promote iff Pr(H|J) >= pi*  (likelihood known)
  canary  : options rule, but first buy a separating canary at cost cG; promote iff candidate passes
  oracle  : promote iff honest
"""
import numpy as np
from scipy.stats import norm

rng = np.random.default_rng(20261003)
P = dict(a=1.0, v0=0.5, D=0.2, l=0.2, I=0.05, k=0.05, sig=0.15, cG=0.02)
N = 400_000

def utilities(p):
    return p["D"] - p["I"], -p["l"] - p["I"] - p["k"]

def means(p, beta, a=None):
    a = p["a"] if a is None else a
    return a * (p["v0"] + p["D"]), a * (p["v0"] - p["l"]) + beta

def post_H(J, p, s, mH, mC):
    lam = np.log((1 - s) / s) + ((J - mC) ** 2 - (J - mH) ** 2) / (2 * p["sig"] ** 2)
    return 1 / (1 + np.exp(-lam))

def episode(p, beta, s, mH_dec=None, mC_dec=None, n=N):
    """Draw n episodes; decision maker's likelihood may differ (mH_dec, mC_dec) from the truth."""
    uH, uC = utilities(p)
    mH, mC = means(p, beta)
    cheat = rng.random(n) < s
    J = np.where(cheat, mC, mH) + p["sig"] * rng.standard_normal(n)
    u = np.where(cheat, uC, uH)
    piS = (p["l"] + p["I"] + p["k"]) / (p["D"] + p["l"] + p["k"])
    mHd = mH if mH_dec is None else mH_dec
    mCd = mC if mC_dec is None else mC_dec
    out = {}
    out["NPV"] = np.where(J > p["a"] * p["v0"], u, 0).mean()
    pro_opt = post_H(J, p, s, mHd, mCd) >= piS
    out["options"] = np.where(pro_opt, u, 0).mean()
    out["canary"] = np.where(~cheat, uH, 0).mean() - p["cG"] if True else 0  # promotes iff honest (separating), pays cG
    out["oracle"] = np.where(~cheat, uH, 0).mean()
    out["P(NPV ships cheat)"] = ((J > p["a"] * p["v0"]) & cheat).mean()
    return out

def table1():
    print("T1: gaming intercept sweep, s=0.3 (mean net gain per episode)")
    print(f"{'beta':>5} {'rank prob':>10} {'closed':>8} {'NPV':>8} {'options':>8} {'canary':>8} {'oracle':>8}")
    s = 0.3
    for beta in [0.0, 0.2, 0.4, 0.6, 0.8]:
        mH, mC = means(P, beta)
        # empirical ranking prob of cheat over honest
        Jc = mC + P["sig"] * rng.standard_normal(N); Jh = mH + P["sig"] * rng.standard_normal(N)
        emp = (Jc > Jh).mean()
        cl = norm.cdf((beta - P["a"] * (P["D"] + P["l"])) / (P["sig"] * np.sqrt(2)))
        e = episode(P, beta, s)
        print(f"{beta:5.2f} {emp:10.3f} {cl:8.3f} {e['NPV']:8.3f} {e['options']:8.3f} {e['canary']:8.3f} {e['oracle']:8.3f}")

def table_bestofN():
    print("\nT2: best-of-N search on the judge: Pr(argmax is a cheat), s=0.3, beta=0.6 vs 0.2")
    s = 0.3
    for beta in [0.2, 0.6]:
        mH, mC = means(P, beta)
        row = []
        for n in [1, 2, 5, 10, 20]:
            M = 100_000
            ch = rng.random((M, n)) < s
            J = np.where(ch, mC, mH) + P["sig"] * rng.standard_normal((M, n))
            row.append(ch[np.arange(M), J.argmax(1)].mean())
        print(f"beta={beta}: " + "  ".join(f"N={n}:{r:.3f}" for n, r in zip([1, 2, 5, 10, 20], row)))

def table_prior_s():
    print("\nT3: NPV vs options vs canary as search pressure s rises (beta=0.6)")
    print(f"{'s':>5} {'P(ship cheat)':>14} {'NPV':>8} {'options':>8} {'canary':>8} {'cG*':>8}")
    for s in [0.1, 0.3, 0.5, 0.7]:
        e = episode(P, 0.6, s)
        uH, uC = utilities(P)
        # canary beats options iff improvement > 0; cG* = max cG at which canary still beats options
        cGstar = (e["oracle"] - e["options"])
        print(f"{s:5.2f} {e['P(NPV ships cheat)']:14.3f} {e['NPV']:8.3f} {e['options']:8.3f} {e['canary']:8.3f} {cGstar:8.3f}")

def table_collapse():
    print("\nT4: collapse (a, beta -> 0), s=0.5: NPV ships an uninformative argmax; options rule abstains")
    uH, uC = utilities(P)
    for a, beta in [(1.0, 0.0), (0.3, 0.1), (0.05, 0.02), (0.0, 0.0)]:
        p = dict(P, a=a)
        mH, mC = means(p, beta)
        s = 0.5
        cheat = rng.random(N) < s
        J = np.where(cheat, mC, mH) + p["sig"] * rng.standard_normal(N)
        u = np.where(cheat, uC, uH)
        piS = (p["l"] + p["I"] + p["k"]) / (p["D"] + p["l"] + p["k"])
        npv = np.where(J > p["a"] * p["v0"], u, 0).mean()
        opt = np.where(post_H(J, p, s, mH, mC) >= piS, u, 0).mean()
        print(f"a={a:4.2f} beta={beta:4.2f}  mean post(H|J)={post_H(J,p,s,mH,mC).mean():.3f}  NPV={npv:7.3f}  options={opt:7.3f}  prior mixture={(1-s)*uH+s*uC:7.3f}")

def table_jump():
    print("\nT5: ruler jump beta0=0.2 -> beta1=0.6; stale vs re-estimated vs pinned likelihood, s=0.3")
    s = 0.3
    uH, uC = utilities(P)
    mH0, mC0 = means(P, 0.2)
    print(f"{'lambda':>7} {'ignore':>9} {'re-est':>9} {'pinned':>9} {'loss ignore':>12}")
    for lam in [0.0, 0.25, 0.5, 1.0]:
        jumped = rng.random(N) < lam
        beta = np.where(jumped, 0.6, 0.2)
        mH, mC = P["a"] * (P["v0"] + P["D"]), P["a"] * (P["v0"] - P["l"]) + beta
        cheat = rng.random(N) < s
        J = np.where(cheat, mC, mH) + P["sig"] * rng.standard_normal(N)
        u = np.where(cheat, uC, uH)
        piS = (P["l"] + P["I"] + P["k"]) / (P["D"] + P["l"] + P["k"])
        ign = np.where(post_H(J, P, s, mH0, mC0) >= piS, u, 0).mean()
        ree = np.where(post_H(J, P, s, mH, mC) >= piS, u, 0).mean()
        pin = episode(P, 0.2, s)["options"]
        print(f"{lam:7.2f} {ign:9.3f} {ree:9.3f} {pin:9.3f} {ree-ign:12.3f}")

def table_sensitivity():
    print("\nT7: sensitivity, s=0.3: gain at beta = 0.5*flip vs 1.5*flip (flip = a(Delta+ell))")
    print(f"{'a':>4} {'sigma':>6} {'flip':>5} | {'NPV lo':>7} {'NPV hi':>7} | {'opt lo':>7} {'opt hi':>7} | {'P(ship cheat) lo':>16} {'hi':>6}")
    for a in [0.5, 1.0, 2.0]:
        for sg in [0.05, 0.15, 0.30]:
            p = dict(P, a=a, sig=sg); flip = a * (p["D"] + p["l"])
            lo = episode(p, 0.5 * flip, 0.3, n=100_000); hi = episode(p, 1.5 * flip, 0.3, n=100_000)
            print(f"{a:4.1f} {sg:6.2f} {flip:5.2f} | {lo['NPV']:7.3f} {hi['NPV']:7.3f} | {lo['options']:7.3f} {hi['options']:7.3f} | {lo['P(NPV ships cheat)']:16.3f} {hi['P(NPV ships cheat)']:6.3f}")

def table_holdout():
    print("\nT6: mixed holdout (Theorem 2): holdout rises iff mu>q; value falls iff omega>1-q")
    q = 0.55
    for mu, om in [(0.5, 0.5), (0.7, 0.5), (0.7, 0.8), (0.9, 0.9)]:
        hold = mu - q
        val = (1 - om) - q
        print(f"q={q} mu={mu} omega={om}: holdout change={hold:+.2f}  value change={val:+.2f}  mislead={hold>0 and val<0}")

if __name__ == "__main__":
    uH, uC = utilities(P)
    print(f"uH={uH:.2f} uC={uC:.2f} pi*={(P['l']+P['I']+P['k'])/(P['D']+P['l']+P['k']):.3f} flip at beta={P['a']*(P['D']+P['l']):.2f}\n")
    table1(); table_bestofN(); table_prior_s(); table_collapse(); table_jump(); table_holdout(); table_sensitivity()
