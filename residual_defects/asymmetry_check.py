"""Sequential verification with Gamma-Poisson learning about lam.

lam ~ Gamma(alpha, rate=beta0) unknown to developer. N ~ Poisson(lam s) defects, each found
after Exp(theta) effort. Developer observes discoveries D(t); posterior of lam is
Gamma(alpha + D, beta0 + s(1 - S(t))), so  E[R_t | D] = s S (alpha + D) / (beta0 + s (1 - S)).
Rule: stop when E[R_t | D] first reaches r' (= mult * r*, r* = c / (A theta)).
"""
import numpy as np

rng = np.random.default_rng(1)
c, A, theta, s = 1.0, 35.0, 0.8, 1.0
alpha, beta0 = 2.0, 1.0
rstar = c / (A * theta)
n = 40000

lam = rng.gamma(alpha, 1 / beta0, n)
N = rng.poisson(lam * s)
T = [np.sort(rng.exponential(1 / theta, k)) for k in N]


def stop_time(times, r):
    """First t with posterior-mean residual == r (event-driven, closed form per interval)."""
    t_prev = 0.0
    for d in range(len(times) + 1):
        t_next = times[d] if d < len(times) else np.inf
        S_prev = np.exp(-theta * t_prev)
        m_prev = s * S_prev * (alpha + d) / (beta0 + s * (1 - S_prev))
        if m_prev <= r:
            return t_prev                       # already below threshold
        Sstar = r * (beta0 + s) / (s * (alpha + d + r))   # solves m(t)=r for this d
        t_star = -np.log(Sstar) / theta
        if t_star < t_next:
            return t_star
        t_prev = t_next
    return t_prev


def run(mult):
    tau = np.array([stop_time(T[i], mult * rstar) for i in range(n)])
    R = np.array([(T[i] > tau[i]).sum() for i in range(n)])
    return tau, R, c * tau + A * R


print(f"r* = c/(A theta) = {rstar:.4f}; prior mean residual at t=0 = {alpha / beta0 * s:.2f}\n")
print("A) Threshold scan: is stopping at posterior-mean residual = r* the cost minimiser?")
print(f"{'mult':>6s} {'E[cost]':>9s} {'E[tau]':>8s} {'E[R_tau]':>9s}")
res = {}
for mult in [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 4.0]:
    tau, R, cost = run(mult)
    res[mult] = (tau, R, cost)
    print(f"{mult:6.2f} {cost.mean():9.4f} {tau.mean():8.3f} {R.mean():9.4f}")

tau, R, cost = res[1.0]
print(f"\nB) At the r* rule: E[R_tau] = {R.mean():.4f} vs r* = {rstar:.4f} (iterated expectations)")

print("\nC) Conditional on TRUE lam (quartiles): does residual stay flat in quality?")
q = np.quantile(lam, [0, .25, .5, .75, 1])
print(f"{'lam bin':>16s} {'E[tau]':>8s} {'E[R_tau|lam]':>13s}")
for i in range(4):
    m = (lam >= q[i]) & (lam <= q[i + 1])
    print(f"{q[i]:7.2f}-{q[i + 1]:6.2f} {tau[m].mean():8.3f} {R[m].mean():13.4f}")

print("\nD) Value of learning vs static effort chosen from the prior mean")
e_s = np.log(A * alpha / beta0 * s * theta / c) / theta
Rs = np.array([(T[i] > e_s).sum() for i in range(n)])
cs = c * e_s + A * Rs
print(f"  static e={e_s:.3f}: E[cost]={cs.mean():.4f}   sequential: {cost.mean():.4f}   "
      f"saving={cs.mean() - cost.mean():.4f}")
print(f"  E[R] static={Rs.mean():.4f}; Var(R) static={Rs.var():.4f}; Var(R) sequential={R.var():.4f}")
