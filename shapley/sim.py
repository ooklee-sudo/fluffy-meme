"""CPU-scale stand-in for the TOFU design: a small MLP 'memorizes' synthetic
author facts (arbitrary labels, paraphrase = input noise) next to a shared
'general ability' task. Fixed epochs. Exact 2^n retraining + GA unlearning.
Per-coalition output u[mask] = [acc on group 0..n-1 paraphrase tests, acc general]."""
import numpy as np

V, DA, H = 10, 16, 64          # classes, embedding dim per field, hidden
Q, NOISE = 5, 0.25             # questions/author, paraphrase noise


class Setting:
    def __init__(self, n, authors_per_group=3, d0_authors=20, seed=0, dup=None, reps=None):
        r = np.random.default_rng(seed); self.n = n
        A = d0_authors + n * authors_per_group
        self.EA = r.normal(size=(A, DA)); self.EQ = r.normal(size=(Q, DA))
        self.Y = r.integers(0, V, size=(A, Q))
        self.groups = [list(range(d0_authors + g * authors_per_group, d0_authors + (g + 1) * authors_per_group)) for g in range(n)]
        if dup:  # dup=(a,b): group b holds the same authors/facts as group a (own paraphrases)
            self.groups[dup[1]] = list(self.groups[dup[0]])
        self.d0 = list(range(d0_authors)); self.reps = reps or [1] * n
        self.Wg = r.normal(size=(2 * DA, V)); self.r = r
        gx = lambda k: r.normal(size=(k, 2 * DA))
        self.Xg, self.Xg_te = gx(300), gx(300)
        self.Yg, self.Yg_te = (self.Xg @ self.Wg).argmax(1), (self.Xg_te @ self.Wg).argmax(1)
        self.Xd0, self.Yd0 = self.items(self.d0)
        self.Xgr, self.Ygr, self.Xte = [], [], []
        for g in range(n):
            x, y = self.items(self.groups[g]); self.Xgr.append(x); self.Ygr.append(y)
            self.Xte.append(self.items(self.groups[g])[0])    # fresh paraphrase draws
        self.Yte = [self.Ygr[g] for g in range(n)]

    def items(self, authors):
        a = np.repeat(authors, Q); q = np.tile(np.arange(Q), len(authors))
        x = np.hstack([self.EA[a], self.EQ[q] + NOISE * self.r.normal(size=(len(a), DA))])
        return x, self.Y[a, q]

    def train_data(self, mask):
        X = [self.Xd0, self.Xg]; Y = [self.Yd0, self.Yg]
        for g in range(self.n):
            if (mask >> g) & 1:
                for _ in range(self.reps[g]): X.append(self.Xgr[g]); Y.append(self.Ygr[g])
        return np.vstack(X), np.concatenate(Y)

    def forget_data(self, mask):
        X, Y = [], []
        for g in range(self.n):
            if not (mask >> g) & 1: X.append(self.Xgr[g]); Y.append(self.Ygr[g])
        return (np.vstack(X), np.concatenate(Y)) if X else (None, None)

    def evaluate(self, m):
        u = [acc(m, self.Xte[g], self.Yte[g]) for g in range(self.n)]
        return np.array(u + [acc(m, self.Xg_te, self.Yg_te)])


def init(seed):
    r = np.random.default_rng(seed)
    return [r.normal(size=(2 * DA, H)) / np.sqrt(2 * DA), np.zeros(H), r.normal(size=(H, V)) / np.sqrt(H), np.zeros(V)]


def fwd(p, X):
    h = np.maximum(X @ p[0] + p[1], 0); return h, h @ p[2] + p[3]


def acc(p, X, Y): return float((fwd(p, X)[1].argmax(1) == Y).mean())


def grads(p, X, Y):
    h, z = fwd(p, X); z -= z.max(1, keepdims=True); pr = np.exp(z); pr /= pr.sum(1, keepdims=True)
    pr[np.arange(len(Y)), Y] -= 1; pr /= len(Y)
    dh = (pr @ p[2].T) * (h > 0)
    return [X.T @ dh, dh.sum(0), h.T @ pr, pr.sum(0)]


class Adam:
    def __init__(self, p, lr): self.lr = lr; self.m = [np.zeros_like(a) for a in p]; self.v = [np.zeros_like(a) for a in p]; self.t = 0
    def step(self, p, g, sign=1.0):
        self.t += 1
        for i, (a, gi) in enumerate(zip(p, g)):
            self.m[i] = .9 * self.m[i] + .1 * gi; self.v[i] = .999 * self.v[i] + .001 * gi * gi
            a -= sign * self.lr * (self.m[i] / (1 - .9 ** self.t)) / (np.sqrt(self.v[i] / (1 - .999 ** self.t)) + 1e-8)


def train(X, Y, seed, epochs=60, bs=64, lr=3e-3):
    p = init(seed); opt = Adam(p, lr); r = np.random.default_rng(seed + 1)
    for _ in range(epochs):
        idx = r.permutation(len(Y))
        for s in range(0, len(Y), bs):
            b = idx[s:s + bs]; opt.step(p, grads(p, X[b], Y[b]))
    return p


def unlearn_ga(p, Xf, Yf, steps, lr=1e-3, bs=64, seed=0, cap=None):
    """Gradient ascent on the forget set for `steps` minibatch steps."""
    p = [a.copy() for a in p]; opt = Adam(p, lr); r = np.random.default_rng(seed)
    for _ in range(steps):
        b = r.choice(len(Yf), size=min(bs, len(Yf)), replace=False)
        opt.step(p, grads(p, Xf[b], Yf[b]), sign=-1.0)
    return p
