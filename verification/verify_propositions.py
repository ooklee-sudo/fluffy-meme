"""Numerical verification of the propositions in 'Pricing Forgetting' (revised).
Run: python3 verify_propositions.py   (needs numpy only). Every check prints PASS/FAIL."""
import itertools, math, random
import numpy as np
rng = np.random.default_rng(7); random.seed(7)
fails = []
def check(name, ok, info=""):
    print(("PASS " if ok else "FAIL ") + name + (" | " + info if info else ""))
    if not ok: fails.append(name)

# ---------- helpers ----------
def shapley(n, v):
    phi = np.zeros(n)
    for i in range(n):
        others = [j for j in range(n) if j != i]
        for s in range(n):
            for S in itertools.combinations(others, s):
                w = math.factorial(s) * math.factorial(n - s - 1) / math.factorial(n)
                a = frozenset(S)
                phi[i] += w * (v[a | {i}] - v[a])
    return phi
def rand_game(n):
    v = {}
    for m in range(1 << n):
        S = frozenset(i for i in range(n) if m >> i & 1)
        v[S] = 0.0 if not S else rng.uniform(0, 1) * len(S) ** 0.7
    return v

# ---------- Prop 1 (duality) and Prop 2 (replication) ----------
n = 4
v = rand_game(n); N = frozenset(range(n))
w = {R: v[N] - v[N - R] for R in v}
check("Prop1 duality", np.allclose(shapley(n, v), shapley(n, w)))
i = 1
others = [j for j in range(n) if j != i]
# replicate i -> players 0..n-1 keep ids, new replica id n
def vp(S):
    S = frozenset(S); has = (i in S) or (n in S)
    base = frozenset(x for x in S if x not in (i, n))
    return v[base | ({i} if has else set())]
v2 = {}
for m in range(1 << (n + 1)):
    S = frozenset(j for j in range(n + 1) if m >> j & 1); v2[S] = vp(S)
phi2 = shapley(n + 1, v2); phi1 = shapley(n, v)
tot = phi2[i] + phi2[n]
form = 0.0
for s in range(n):
    for S in itertools.combinations(others, s):
        wS = math.factorial(s) * math.factorial(n - 1 - s) / math.factorial(n)
        m_i = v[frozenset(S) | {i}] - v[frozenset(S)]
        form += wS * 2 * (n - s) / (n + 1) * m_i
check("Prop2 replication total", abs(tot - form) < 1e-9, f"{tot:.6f} vs {form:.6f}")
gain = sum(math.factorial(s) * math.factorial(n - 1 - s) / math.factorial(n) * (n - 1 - 2 * s) *
           (v[frozenset(S) | {i}] - v[frozenset(S)]) for s in range(n) for S in itertools.combinations(others, s)) / (n + 1)
check("Prop2 gain = sum/(n+1)", abs((tot - phi1[i]) - gain) < 1e-9)

# ---------- Prop 3/4/5 (additive bias, sequential bias, path sensitivity) ----------
U = v  # true utilities (v(emptyset)=0)
eps_path = {}
for T_mask in range(1 << n):
    T = frozenset(j for j in range(n) if T_mask >> j & 1)
    rem = sorted(N - T)
    for sigma in itertools.permutations(rem):
        eps_path[(T, sigma)] = 0.0 if len(rem) == 0 else rng.normal(0.15, 0.1) * (len(rem) / n)
for T_mask in range(1 << n):
    pass
perms = list(itertools.permutations(range(n)))
phi_seq = np.zeros(n); eps_empty = 0.0
for pi in perms:
    for k in range(1, n + 1):
        Tk = N - frozenset(pi[:k]); Tk1 = N - frozenset(pi[:k - 1])
        e_k = eps_path[(Tk, tuple(pi[:k]))]; e_k1 = 0.0 if k == 1 else eps_path[(Tk1, tuple(pi[:k - 1]))]
        credit = (U[Tk1] + e_k1) - (U[Tk] + e_k)
        phi_seq[pi[k - 1]] += credit / len(perms)
    eps_empty += eps_path[(frozenset(), tuple(pi))] / len(perms)
check("Prop4 aggregate identity", abs(phi_seq.sum() - (v[N] - eps_empty)) < 1e-9)
# Prop 5 bound
eps_bar = {}
for T_mask in range(1 << n):
    T = frozenset(j for j in range(n) if T_mask >> j & 1); rem = sorted(N - T)
    vals = [eps_path[(T, s)] for s in itertools.permutations(rem)]
    eps_bar[T] = float(np.mean(vals))
delta = {k: 0.0 for k in range(1, n + 1)}
for (T, s), e in eps_path.items():
    k = len(s)
    if k >= 1: delta[k] = max(delta[k], abs(e - eps_bar[T]))
phi_eb = shapley(n, {S: eps_bar[S] for S in eps_bar})
phi_true = shapley(n, v)
bound = sum(delta[k] for k in range(2, n + 1)) / n
dev = np.abs(phi_seq - phi_true - phi_eb)
# Note: eps_bar as a game on T (remaining set); Shapley of eps_bar is taken in the coalition-of-remaining sense, same as Prop 3.
check("Prop5 path-sensitivity bound", dev.max() <= bound + 1e-9, f"max dev {dev.max():.4f} <= {bound:.4f}")

# ---------- Prop 7 (optimal audit design) ----------
def design(theta, a, e):
    d = min(1, max(theta, (a * theta / e) ** (1 / 3))); return d, theta / d
for theta, a, e in [(0.2, 1.0, 4.0), (0.05, 0.3, 2.0), (0.6, 0.1, 5.0)]:
    ds = np.linspace(theta, 1, 200001); f = a * theta / ds + e * ds ** 2 / 2
    d, p = design(theta, a, e)
    check(f"Prop7 delta* theta={theta}", abs(ds[f.argmin()] - d) < 1e-3, f"{ds[f.argmin()]:.4f} vs {d:.4f}")

# ---------- Prop 8 (penalty base) ----------
pdk, C_c, beta, phi = 0.6, 0.1, 0.8, 1.0
rD = (pdk * phi - C_c) / (pdk + beta); rT = (pdk * phi - C_c) / beta
okD = lambda r: pdk * (phi - r) >= C_c + beta * r - 1e-12
okT = lambda r: pdk * phi >= C_c + beta * r - 1e-12
check("Prop8 thresholds", okD(rD) and not okD(rD + 1e-4) and okT(rT) and not okT(rT + 1e-4)
      and abs(rD - rT * beta / (beta + pdk)) < 1e-12)

# ---------- NEW Prop 9' (noisy test: Youden index) ----------
ok = True
for _ in range(2000):
    C, c, b, rho, p, d, al, F = rng.uniform(0.1, 2, 8) * np.array([1, .5, 1, 1, .5, 1, .3, 3])
    d = min(d, 1); al = min(al, 0.9 * d)
    exact = -C - p * al * F; approx = -c + b * rho - p * d * F
    ok &= (exact >= approx) == (p * F * (d - al) >= (C - c) + b * rho)
check("NEW Prop12 noisy test: condition uses delta-alpha", ok)

# ---------- NEW Prop 10 (concealment ceiling) done earlier numerically; re-run ----------
def dev_min(z, k):
    xs = np.linspace(0, 1, 100001); return (z * (1 - xs) + k * xs ** 2 / 2).min()
allok = True
for g, k in [(0.1, 1), (0.3, 1), (0.49, 1), (0.2, 0.5), (0.7, 1.0)]:
    if g <= k / 2:
        zt = k * (1 - math.sqrt(1 - 2 * g / k))
        allok &= abs(dev_min(zt, k) - g) < 1e-6 and dev_min(zt * 0.99, k) < g
        u = 2 * g / k; r = (2 / u) * (1 - math.sqrt(1 - u)); allok &= 1 < r <= 2 + 1e-9
    else:
        allok &= dev_min(100 * k, k) < g
check("Prop10 concealment ceiling & threshold & ratio in (1,2]", allok)

# ---------- NEW Prop 11 (investment threshold), general grid ----------
allok = True
for _ in range(300):
    Cb = rng.uniform(.8, 1.5); lam = rng.uniform(.1, .8); io = rng.uniform(.3, 3); m = int(rng.integers(1, 6))
    s_e = min(1, m * lam / io); Lam = (m * lam ** 2 / (2 * io)) if m * lam <= io else lam - io / (2 * m)
    ss = np.linspace(0, 1, 20001)
    for dA in (-0.02, 0.02):
        A = Cb - Lam + dA
        J = m * np.minimum(Cb - lam * ss, A) + io * ss ** 2 / 2
        invests = (J.min() < m * min(Cb, A) - 1e-9) and (ss[J.argmin()] > 1e-9)
        allok &= (invests == (dA > 0)) if A < Cb else True
check("Prop11 investment threshold g0-Lambda", allok)

# ---------- NEW Prop 13 (declare-and-pay, continuous effort, private residue) ----------
# developer: effort e in [0,1], residue r=r0(1-e), cost e^2/2, revenue beta*r; price pi per declared residue,
# fine f per undeclared residue, audit detects with prob p*delta.
def dev_choice(pi, f, p, d, beta, r0):
    best = None
    for e in np.linspace(0, 1, 2001):
        r = r0 * (1 - e)
        rh = np.linspace(0, r, 201)
        cost = e ** 2 / 2 - beta * r + pi * rh + p * d * f * (r - rh)
        j = cost.argmin()
        if best is None or cost[j] < best[0]: best = (cost[j], e, rh[j], r)
    return best
beta, r0, h = 0.2, 1.5, 0.9          # (h-beta)*r0 = 1.05 -> push into interior by lowering r0
r0 = 1.2                              # (h-beta)*r0 = 0.84 < 1
allok = True
for z in [0.3, 0.5, 0.7, 0.9, 1.4]:    # z = p*delta*f
    p, d, f = 0.5, 0.8, z / 0.4
    _, e, rh, r = dev_choice(h, f, p, d, beta, r0)
    tau = min(h, z); e_th = min(1, max(0, (tau - beta) * r0))
    truthful = abs(rh - r) < 1e-9 or r < 1e-9
    allok &= abs(e - e_th) < 2e-3
    if abs(z - h) > 1e-9:            # at z == h the developer is indifferent between declaring and not
        allok &= (truthful if z > h else (rh < 1e-9))
check("Prop13 IC: truthful iff p*delta*f >= pi; effort e(min{pi,z})", allok)
# second best: regulator picks z in [0,h] to minimise  a z/(delta fbar) + (h-z)^2 r0^2/2
a, d, fb = 0.12, 0.9, 2.0
zs = np.linspace(0, h, 100001); L = a * zs / (d * fb) + (h - zs) ** 2 * r0 ** 2 / 2
z_star = h - a / (d * fb * r0 ** 2)
check("Prop13 second-best z* = h - a/(delta*fbar*r0^2)", abs(zs[L.argmin()] - z_star) < 1e-3,
      f"{zs[L.argmin()]:.4f} vs {z_star:.4f}")
# welfare loss formula vs direct computation
tau = z_star; e_t = (tau - beta) * r0; e_s = (h - beta) * r0
W = lambda e: e ** 2 / 2 + (h - beta) * r0 * (1 - e)
check("Prop13 welfare loss = (h-z)^2 r0^2 / 2", abs((W(e_t) - W(e_s)) - (h - tau) ** 2 * r0 ** 2 / 2) < 1e-12)

# ---------- NEW Prop 9 (triage, heterogeneous power): cost to deter K(theta) ----------
a, e = 0.5, 2.0
def K(theta):
    ds = np.linspace(theta, 1, 100001); return (a * theta / ds + e * ds ** 2 / 2).min()
ths = np.linspace(0.05, 0.95, 40); Ks = [K(t) for t in ths]
check("Prop9' K(theta) strictly increasing", all(x < y for x, y in zip(Ks, Ks[1:])))
t = 0.3; h_ = 1e-4
dK = (K(t + h_) - K(t - h_)) / (2 * h_); ds = np.linspace(t, 1, 100001)
dstar = ds[(a * t / ds + e * ds ** 2 / 2).argmin()]
check("Prop9' envelope dK/dtheta = a/delta*", abs(dK - a / dstar) < 2e-3, f"{dK:.4f} vs {a/dstar:.4f}")
# greedy bound with heterogeneous K
worst = 0
for _ in range(1500):
    nn = 8; H = rng.uniform(.5, 3, nn); th = rng.uniform(.05, .9, nn); w_ = np.array([K(x) for x in th]); B = rng.uniform(.5, 3)
    best = 0
    for mask in range(1 << nn):
        s = [q for q in range(nn) if mask >> q & 1]
        if w_[s].sum() <= B: best = max(best, H[s].sum())
    order = np.argsort(-H / w_); tot_ = 0; val = 0; jj = None
    for q in order:
        if tot_ + w_[q] <= B: tot_ += w_[q]; val += H[q]
        else: jj = q; break
    if jj is not None: worst = max(worst, (best - val) / H[jj])
check("Prop9 greedy within H_j of OPT (heterogeneous power)", worst <= 1 + 1e-9, f"worst ratio {worst:.3f}")

print("\nFAILED:" if fails else "\nALL CHECKS PASSED", fails if fails else "")
