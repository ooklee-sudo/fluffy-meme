"""Close the loop: plug measured reach A(K) into the adoption model and compute where the adoption window ends.

What the experiment measures: A(K) = tool kill share / human kill share, by model and number of attempts K.
What it does NOT measure: relative speed B and cost ratio c_L/c_H (no human discovery-rate data). So rho = A*B*c_H/c_L is scanned.
Key facts used (Proposition 2, Lemma 2 of the manuscript):
  adoption set = (1/rho, kappa*) with A*h(rho*kappa*) = h(kappa*) for A<1, and (1/rho, infinity) for A>=1;
  kappa* increases in rho and converges, as rho -> infinity, to the solution of h(kappa) = A.
So when the tool is much cheaper per unit of discovery than humans (rho >> 1), the exclusion boundary is set by A alone.
kappa = a*b*f/c_H: a fault's cost relative to the human cost of finding the first fault at the start of testing.

python3 calibrate_from_study.py [--denominator either|all] [--K 8]
"""
import argparse, glob, json, os
import numpy as np
from scipy.optimize import brentq

HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "work", "results")
h = lambda x: 0.0 if x <= 1 else 1 - (1 + np.log(x)) / x


def kappa_star(A, rho):
    """Upper end of the adoption window in kappa; inf when A >= 1."""
    if A >= 1: return np.inf
    if A <= 0 or rho <= 1: return np.nan
    f = lambda k: A * h(rho * k) - h(k)
    lo, hi = max(1.0 + 1e-9, 1.0 / rho * 1.0001), 1e9
    if f(lo) <= 0: return lo
    if f(hi) > 0: return np.inf
    return brentq(f, lo, hi, xtol=1e-10)


def kappa_star_cheap(A):
    """rho -> infinity: solve h(kappa) = A."""
    if A >= 1: return np.inf
    return brentq(lambda k: h(k) - A, 1.0 + 1e-9, 1e12)


def load(K, either):
    data = [json.load(open(p)) for p in sorted(glob.glob(f"{RES}/*.json"))]
    out = {}
    for m in sorted({m for d in data for m in d["models"]}):
        H, T = [], []
        for d in data:
            at = d["models"].get(m, {}).get("attempts", [])
            if len(at) < K or "human" not in d: continue
            H.append(np.array(d["human"], bool)); T.append(np.any([np.array(x["killed"], bool) for x in at[:K]], axis=0))
        if H: out[m] = (H, T)
    return out


def ratio(H, T, idx, either):
    rs = []
    for i in idx:
        h_, t_ = H[i], T[i]; mask = (h_ | t_) if either else np.ones(len(h_), bool)
        if h_[mask].sum() > 0: rs.append(t_[mask].mean() / h_[mask].mean())
    return float(np.mean(rs))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--K", type=int, default=8); ap.add_argument("--denominator", default="either")
    a = ap.parse_args(); either = a.denominator == "either"; rng = np.random.default_rng(0)
    d = load(a.K, either)
    print(f"Measured reach after K={a.K} attempts (denominator: {'mutants killed by either side' if either else 'all mutants'})")
    print(f"{'model':34s} {'modules':>7s} {'A':>6s} {'95% CI':>14s}   kappa*(rho=3)  kappa*(rho=10)  kappa*(rho->inf) [CI]")
    for m, (H, T) in d.items():
        n = len(H); A = ratio(H, T, range(n), either)
        bs = [ratio(H, T, rng.integers(0, n, n), either) for _ in range(2000)]; lo, hi = np.percentile(bs, [2.5, 97.5])
        fmt = lambda x: "inf" if np.isinf(x) else f"{x:7.1f}"
        print(f"{m:34s} {n:7d} {A:6.2f} {f'({lo:.2f},{hi:.2f})':>14s}   {fmt(kappa_star(A,3)):>12s}  {fmt(kappa_star(A,10)):>13s}  {fmt(kappa_star_cheap(A)):>9s} [{fmt(kappa_star_cheap(lo))}, {fmt(kappa_star_cheap(hi))}]")
    print("\nConvergence of kappa* in rho (A = 0.90): ", {r: round(kappa_star(0.9, r), 1) for r in (1.5, 2, 3, 5, 10, 30, 100, 1000)}, " limit:", round(kappa_star_cheap(0.9), 1))
    print("Guaranteed exclusion (Prop. 3) equals the rho->inf boundary: for a=20, b=0.12, f_hi = kappa*/(a*b) =", {A: round(kappa_star_cheap(A) / 2.4, 1) for A in (0.5, 0.8, 0.9, 0.95)})
