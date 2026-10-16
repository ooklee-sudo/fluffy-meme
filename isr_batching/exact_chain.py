"""Exact Markov-chain computation of the flat-price loss under switching demand (Section 4.3, Table 3 / Table B3).

State (n, k): number of requests in the system n = 0..N (finite buffer) and demand phase k.  Phases switch with generator
theta*G0.  Service rate mu(n) = min(n,M) * rho(min(n,M)), rho(m) = (1+b)/(1+b*m)  (b = 0 -> dedicated servers).

* Tagged-request expected sojourn T(a,b,k) (a requests ahead, b behind): solved level by level in a (a never increases),
  each level is a banded system in (b,k).  Mean delay of an admitted request arriving in phase k is eq. (7):
      d_k = sum_{n<N} pi(n,k) T(n,0,k) / [pi_k - pi(N,k)].
* Welfare of a rate plan lam:  W = sum_k pi_k (1 - mu(N|k)) B_k(lam_k) - E[N],  B_k(l) = V (l - l^2/(2 Lam_k)).
* Best phase-dependent plan: maximise W over lam in [0, Lam].  Best flat price: maximise W(lam(p)) over p where lam(p)
  solves P_k(lam_k) = p + d_k(lam) in every phase.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.linalg import solve_banded
from scipy.optimize import minimize, root, minimize_scalar


class Chain:
    def __init__(self, M, b, N, G0, theta, V, Lam):
        self.M, self.b, self.N = int(M), float(b), int(N)
        self.G0 = np.asarray(G0, float); self.K = len(self.G0)
        self.theta, self.V, self.Lam = float(theta), float(V), np.asarray(Lam, float)
        n = np.arange(0, self.N + 2)
        m = np.minimum(n, self.M)
        rho = (1 + self.b) / (1 + self.b * np.maximum(m, 1))
        self.mu = m * rho                                   # mu[0] = 0; mu[n] for n>=M is constant
        self.mubar = self.mu[self.M]
        # stationary distribution of the phase process
        A = np.vstack([self.G0.T, np.ones(self.K)]); rhs = np.zeros(self.K + 1); rhs[-1] = 1
        self.pi_phase = np.linalg.lstsq(A, rhs, rcond=None)[0]

    # ------------------------------------------------------------------ stationary distribution
    def stationary(self, lam):
        K, N = self.K, self.N
        S = (N + 1) * K
        idx = lambda n, k: n * K + k
        rows, cols, vals = [], [], []
        for k in range(K):
            ns = np.arange(0, N)                                              # arrivals n -> n+1
            rows += list(idx(ns, k)); cols += list(idx(ns + 1, k)); vals += [lam[k]] * N
            ns = np.arange(1, N + 1)                                          # completions n -> n-1
            rows += list(idx(ns, k)); cols += list(idx(ns - 1, k)); vals += list(self.mu[ns])
            for j in range(K):
                if j != k:                                                    # phase change
                    ns = np.arange(0, N + 1)
                    rows += list(idx(ns, k)); cols += list(idx(ns, j)); vals += [self.theta * self.G0[k, j]] * (N + 1)
        Q = sp.csr_matrix((vals, (rows, cols)), shape=(S, S))
        Q = Q - sp.diags(np.asarray(Q.sum(axis=1)).ravel())
        A = Q.T.tolil(); A[S - 1, :] = 1.0
        rhs = np.zeros(S); rhs[-1] = 1.0
        pi = spla.spsolve(A.tocsc(), rhs)
        return np.maximum(pi, 0.0).reshape(N + 1, K)

    # ------------------------------------------------------------------ tagged sojourn times, T(n, 0, k)
    def tagged_T0(self, lam):
        """Return array T0[n, k] = expected remaining sojourn of a request that arrives to find n others (n = 0..N-1)."""
        K, N, M, th, G0 = self.K, self.N, self.M, self.theta, self.G0
        T0 = np.zeros((N, K)); prev = None
        offphase = th * (G0 - np.diag(np.diag(G0)))                              # theta * G0[k, j], j != k
        for a in range(N):
            nb = N - a                                                          # b = 0 .. N-1-a
            b = np.arange(nb)
            n = a + b + 1
            m = np.minimum(n, M)
            r = self.mu[n] / m                                                  # per-request completion rate
            arr_ok = (n < N)
            diag = np.zeros((nb, K)); rhs = np.ones((nb, K))
            sup = np.zeros((nb, K)); sub = np.zeros((nb, K))
            for k in range(K):
                diag[:, k] = -th * G0[k, k] + np.where(arr_ok, self.lam_cur[k], 0.0) + self.mu[n]
                sup[:, k] = -np.where(arr_ok, self.lam_cur[k], 0.0)             # -> (a, b+1, k)
                if a < M:
                    sub[:, k] = -(m - a - 1) * r                                # behind completions -> (a, b-1, k)
                    if a > 0 and prev is not None:
                        rhs[:, k] += a * r * prev[:nb, k]                       # ahead completions -> (a-1, b, k)
                else:
                    rhs[:, k] += self.mu[n] * prev[:nb, k]                      # a >= M: any in-service (all ahead) completes
            size = nb * K
            ab = np.zeros((2 * K + 1, size))                                    # banded storage (l = u = K)
            ii = (b[:, None] * K + np.arange(K)[None, :]).ravel()               # row/col index of (b, k)
            ab[K, ii] = diag.ravel()
            for k in range(K):
                for j in range(K):
                    if j != k:
                        rows_ = b * K + k; cols_ = b * K + j
                        ab[K + rows_ - cols_, cols_] = -offphase[k, j]
            if nb > 1:
                for k in range(K):
                    rows_ = b[:-1] * K + k; cols_ = (b[:-1] + 1) * K + k
                    ab[K + rows_ - cols_, cols_] = sup[:-1, k]
                    rows_ = b[1:] * K + k; cols_ = (b[1:] - 1) * K + k
                    ab[K + rows_ - cols_, cols_] = sub[1:, k]
            sol = solve_banded((K, K), ab, rhs.ravel()).reshape(nb, K)
            T0[a] = sol[0]
            prev = sol
        return T0

    # ------------------------------------------------------------------ delays, welfare
    def delays(self, lam):
        self.lam_cur = np.asarray(lam, float)
        pi = self.stationary(lam)
        T0 = self.tagged_T0(lam)
        pik = pi.sum(axis=0)
        d = (pi[:self.N] * T0).sum(axis=0) / (pik - pi[self.N])
        return d, pi

    def welfare(self, lam, pi=None):
        lam = np.asarray(lam, float)
        if pi is None: pi = self.stationary(lam)
        pik = pi.sum(axis=0)
        B = self.V * (lam - lam ** 2 / (2 * self.Lam))
        EN = (pi.sum(axis=1) * np.arange(self.N + 1)).sum()
        return float(((pik - pi[self.N]) * B).sum() - EN)

    # ------------------------------------------------------------------ plans
    def best_phase_dependent(self, starts):
        best = None
        for x0 in starts:
            res = minimize(lambda x: -self.welfare(np.clip(x, 0, self.Lam)), x0, method='L-BFGS-B',
                           bounds=[(0, L) for L in self.Lam], options=dict(ftol=1e-13, gtol=1e-10, maxiter=300))
            if best is None or res.fun < best.fun: best = res
        return -best.fun, np.clip(best.x, 0, self.Lam)

    def equilibrium(self, p, lam0):
        """lam with P_k(lam_k) = p + d_k(lam) in every phase (rates in [0, Lam_k]).  Newton-type solve (scipy hybr) with a
        damped fixed-point fallback."""
        Lam = self.Lam
        def target(x):
            d, _ = self.delays(np.clip(x, 1e-9, Lam))
            return np.clip(Lam * (1 - (p + d) / self.V), 0, Lam)
        x0 = np.clip(np.asarray(lam0, float), 1e-6, Lam * 0.999)
        try:
            sol = root(lambda x: x - Lam * (1 - (p + self.delays(np.clip(x, 1e-9, Lam))[0]) / self.V), x0, method='hybr', tol=1e-11)
            x = np.clip(sol.x, 0, Lam)
            if np.max(np.abs(x - target(x))) < 1e-7: return x
        except Exception:
            pass
        x = x0
        for it in range(300):                                                   # damped fixed point
            gx = target(x); step = gx - x
            if np.max(np.abs(step)) < 1e-9: return gx
            x = x + 0.5 * step
        return x

    def best_flat(self, p_grid, lam0):
        best = (-np.inf, None, None); x = lam0; vals = []
        for p in p_grid:
            x = self.equilibrium(p, x)
            w = self.welfare(x); vals.append((p, w, x.copy()))
            if w > best[0]: best = (w, p, x.copy())
        # local refinement around the best grid point
        pb = best[1]; i = int(np.argmax([v[1] for v in vals]))
        lo = p_grid[max(i - 1, 0)]; hi = p_grid[min(i + 1, len(p_grid) - 1)]
        f = lambda p: -self.welfare(self.equilibrium(p, best[2]))
        res = minimize_scalar(f, bounds=(lo, hi), method='bounded', options=dict(xatol=1e-6))
        if -res.fun > best[0]:
            x = self.equilibrium(res.x, best[2]); best = (-res.fun, res.x, x)
        return best


def loss_at(M, b, N, G0, theta, V, Lam, starts, p_grid, lam_flat0):
    ch = Chain(M, b, N, G0, theta, V, Lam)
    Wpd, lam_pd = ch.best_phase_dependent(starts)
    Wf, pf, lam_f = ch.best_flat(p_grid, lam_flat0)
    return dict(Wpd=Wpd, Wflat=Wf, loss=Wpd - Wf, rel=(Wpd - Wf) / Wpd, p_flat=pf, lam_pd=lam_pd, lam_flat=lam_f)
