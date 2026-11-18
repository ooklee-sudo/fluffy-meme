"""Numerical sanity checks behind the three proofs in section 8 of msom_reframing.md.

(i)   z_n strictly increasing, P_n strictly decreasing, a_n nondecreasing   (coupling argument)
(ii)  value of verification V(H) nondecreasing in H; envelope identity; plateau (F_u-F_eff) z_inf
(iii) M/M/c: Lq convex in lambda, Wq strictly increasing                    (needed for P_dec >= P_sys)
Also checks the Topkis claims n*(d), n*(H) nondecreasing.
"""
import math
import numpy as np
from sim_capacity import AP, NINF
from sim_capacity3 import erlang_c

rng = np.random.default_rng(7)
NMAXC = 30


def tables(k, c, mu, q, theta):
    P, a, z = [], [], []
    for n in list(range(NMAXC + 1)):
        A0, Pn = AP(n, k, c, mu, q, theta, 0.0)
        A1, _ = AP(n, k, c, mu, q, theta, 1.0)
        P.append(Pn); a.append(A0); z.append(A1 - A0)
    A0, Pn = AP(NINF, k, c, mu, q, theta, 0.0)
    A1, _ = AP(NINF, k, c, mu, q, theta, 1.0)
    P.append(Pn); a.append(A0); z.append(A1 - A0)
    return np.array(P), np.array(a), np.array(z)


def check_i(ndraw=60):
    bad = 0
    for _ in range(ndraw):
        k = rng.uniform(0.2, 3); c = rng.uniform(0.5, 10)
        mu = rng.uniform(0.01, 0.5); q = rng.uniform(0.02, 0.5); th = rng.uniform(0.02, 0.9)
        P, a, z = tables(k, c, mu, q, th)
        ok = (np.all(np.diff(z) > -1e-12) and np.all(np.diff(P) < 1e-12) and np.all(np.diff(a) > -1e-12) and abs(z[0]) < 1e-12)
        # strictness (until numerical saturation)
        strict = np.all(np.diff(z[:12]) > 0) and np.all(np.diff(P[:12]) < 0)
        if not (ok and strict):
            bad += 1
            print("  violation:", dict(k=k, c=c, mu=mu, q=q, th=th), np.diff(z[:6]), np.diff(P[:6]))
    print(f"(i)  z_n strictly up, P_n strictly down, a_n nondecreasing, z_0=0: violations {bad}/{ndraw}")


def argmin_n(P, a, z, F, H):
    cs = a + F * z + P * H
    return int(np.argmin(cs)), cs.min()


def check_ii(ndraw=40):
    bad_mono = bad_env = bad_pl = bad_topkis = 0
    for _ in range(ndraw):
        mu = rng.uniform(0.02, 0.3); q = rng.uniform(0.03, 0.3); th = rng.uniform(0.05, 0.7)
        k, c = 1.0, rng.uniform(1, 8)
        P, a, z = tables(k, c, mu, q, th)
        Fu = rng.uniform(40, 200); Fd = rng.uniform(5, 0.6 * Fu)
        dq = rng.uniform(0.1, 1.0)
        Feff = dq * Fd + (1 - dq) * Fu
        Hs = np.linspace(1, 600, 300)
        V = []
        nprev = -1; ok_t = True
        for H in Hs:
            n0, c0 = argmin_n(P, a, z, Fu, H)
            n1, c1 = argmin_n(P, a, z, Feff, H)
            V.append(c0 - c1)
            ok_t &= n0 >= nprev - 0  # n*(H) nondecreasing (index NINF last)
            nprev = n0
        V = np.array(V)
        bad_mono += (np.any(np.diff(V) < -1e-9))
        bad_topkis += (not ok_t)
        # plateau: for H large, V = (Fu - Feff) z_inf
        bad_pl += (abs(V[-1] - (Fu - Feff) * z[-1]) > 1e-6)
        # envelope identity at one H: V(H) = int_{Feff}^{Fu} z_{n*(H,f)} df
        H = Hs[len(Hs) // 3]
        fs = np.linspace(Feff, Fu, 4001)
        zs = np.array([z[argmin_n(P, a, z, f, H)[0]] for f in fs])
        integral = np.trapezoid(zs, fs)
        n0, c0 = argmin_n(P, a, z, Fu, H); n1, c1 = argmin_n(P, a, z, Feff, H)
        bad_env += (abs(integral - (c0 - c1)) > 5e-3 * max(1.0, abs(c0 - c1)))
    print(f"(ii) V(H) nondecreasing: violations {bad_mono}/{ndraw};  n*(H) nondecreasing: violations {bad_topkis}/{ndraw}")
    print(f"     plateau V=(F_u-F_eff) z_inf: violations {bad_pl}/{ndraw};  envelope identity: violations {bad_env}/{ndraw}")


def check_topkis_d(ndraw=40):
    bad = 0
    for _ in range(ndraw):
        mu = rng.uniform(0.02, 0.3); q = rng.uniform(0.03, 0.3); th = rng.uniform(0.05, 0.7)
        P, a, z = tables(1.0, rng.uniform(1, 8), mu, q, th)
        Fu = rng.uniform(40, 200); Fd = rng.uniform(5, 0.6 * Fu); H = rng.uniform(5, 200)
        prev = -1
        for dq in np.linspace(0, 1, 41):
            n, _ = argmin_n(P, a, z, dq * Fd + (1 - dq) * Fu, H)
            if n < prev: bad += 1; break
            prev = n
    print(f"(ii') Topkis: n*(d) nondecreasing in d: violations {bad}/{ndraw}")


def check_iii():
    bad_cvx = bad_inc = 0; worst = 0.0
    for c_ in [1, 2, 3, 5, 10, 20, 50]:
        m = 1.0
        lams = np.linspace(1e-3, 0.9995 * c_ * m, 4001)
        Lq = np.array([erlang_c(c_, l / m) * l / (c_ * m - l) for l in lams])      # Lq = lam * Wq
        Wq = np.array([erlang_c(c_, l / m) / (c_ * m - l) for l in lams])
        d2 = Lq[2:] - 2 * Lq[1:-1] + Lq[:-2]
        worst = min(worst, d2.min())
        bad_cvx += (d2.min() < -1e-9)
        bad_inc += (np.any(np.diff(Wq) <= 0))
    print(f"(iii) M/M/c, c in 1..50: Lq convex violations {bad_cvx}/7 (min 2nd diff {worst:.2e});  Wq strictly increasing violations {bad_inc}/7")


if __name__ == "__main__":
    check_i()
    check_ii()
    check_topkis_d()
    check_iii()
