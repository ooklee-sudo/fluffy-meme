"""Tensor-train (MPO) adapters for linear layers and the entanglement profile of a weight update.

A weight update dW (out x in) is stored as d cores G_k of shape (r_{k-1}, o_k, i_k, r_k), r_0 = r_d = 1,
where out = o_1 ... o_d and in = i_1 ... i_d:

    dW[(o_1..o_d), (i_1..i_d)] = G_1[:, o_1, i_1, :] G_2[:, o_2, i_2, :] ... G_d[:, o_d, i_d, :]

The bond dimensions r_1 .. r_{d-1} set the adapter's capacity. The entanglement entropy at bond k is the
Shannon entropy of the normalized squared singular values of dW cut between pairs (o_1 i_1 .. o_k i_k) and
the rest. A low entropy means a small bond dimension is enough at that cut.
"""
import math

import torch
import torch.nn as nn
import torch.nn.functional as F


def factorize(n, d):
    """Split n into d integer factors, as balanced as possible, largest first (product == n)."""
    primes, m, p = [], n, 2
    while p * p <= m:
        while m % p == 0:
            primes.append(p)
            m //= p
        p += 1
    if m > 1:
        primes.append(m)
    f = [1] * d
    for q in sorted(primes, reverse=True):
        i = min(range(d), key=lambda j: f[j])
        f[i] *= q
    return sorted(f, reverse=True)


def tt_to_matrix(cores):
    """Contract TT cores [(r0, o, i, r1), ...] into the full (out x in) matrix."""
    t = cores[0]
    t = t.reshape(t.shape[1], t.shape[2], t.shape[3])  # (O, I, r)
    for g in cores[1:]:
        t = torch.einsum("abr,rcds->acbds", t, g)  # (O, o, I, i, r')
        o_, o, i_, i, r = t.shape
        t = t.reshape(o_ * o, i_ * i, r)
    return t.squeeze(-1)


def bond_profile(w, out_f, in_f, energy=0.99):
    """Entanglement entropy and rank needed at each bond of the MPO split of matrix w.

    Returns one dict per bond k = 1 .. d-1: entropy (nats), rank_at_energy (smallest number of singular
    values keeping `energy` of the squared norm) and max_rank (the largest rank the cut allows).
    """
    d = len(out_f)
    t = w.detach().float().reshape(*out_f, *in_f)
    t = t.permute([x for k in range(d) for x in (k, d + k)])  # o1 i1 o2 i2 ...
    res = []
    for k in range(1, d):
        left = math.prod(out_f[:k]) * math.prod(in_f[:k])
        s = torch.linalg.svdvals(t.reshape(left, -1))
        e = s ** 2
        tot = e.sum()
        if tot <= 0:
            res.append(dict(bond=k, entropy=0.0, rank_at_energy=0, max_rank=len(s)))
            continue
        p = e / tot
        p = p[p > 0]
        ent = float(-(p * p.log()).sum())
        cum = torch.cumsum(e, 0) / tot
        rk = int((cum < energy).sum()) + 1
        res.append(dict(bond=k, entropy=ent, rank_at_energy=min(rk, len(s)), max_rank=len(s)))
    return res


class TTAdapterLinear(nn.Module):
    """Frozen base linear layer plus a trainable TT-format update: y = base(x) + scale * c(r) * x dW^T.

    c(r) is a rank-dependent factor so that larger bond dimensions do not take larger effective steps:
    "rs" = 1 / sqrt(mean bond dimension), as in rank-stabilized LoRA (Kalajdzievski 2023); "none" = 1.
    """

    def __init__(self, base, ranks, d=4, scale=1.0, rank_scale="rs"):
        super().__init__()
        self.base = base
        self.d = d
        self.scale = scale
        self.rank_scale = rank_scale
        self.out_f = factorize(base.out_features, d)
        self.in_f = factorize(base.in_features, d)
        self.cores = nn.ParameterList()
        self.reset(ranks)

    def reset(self, ranks):
        """Re-create the cores at new bond dimensions; the update starts at exactly zero."""
        if isinstance(ranks, int):
            ranks = [ranks] * (self.d - 1)
        assert len(ranks) == self.d - 1
        self.ranks = list(ranks)
        self.c = 1.0 / math.sqrt(sum(self.ranks) / len(self.ranks)) if self.rank_scale == "rs" else 1.0
        r = [1] + self.ranks + [1]
        dev = self.base.weight.device
        cores = []
        for k in range(self.d):
            shape = (r[k], self.out_f[k], self.in_f[k], r[k + 1])
            if k == self.d - 1:
                g = torch.zeros(shape, device=dev)  # dW = 0 at start, like LoRA's B = 0
            else:
                g = torch.randn(shape, device=dev) / math.sqrt(r[k])  # keeps partial products O(1)
            cores.append(nn.Parameter(g))
        self.cores = nn.ParameterList(cores)

    def delta(self):
        return tt_to_matrix(list(self.cores))

    def n_params(self):
        return sum(c.numel() for c in self.cores)

    def forward(self, x):
        return self.base(x) + (self.scale * self.c) * F.linear(x, self.delta().to(x.dtype))


def add_tt_adapters(model, targets=("q_proj", "v_proj"), ranks=4, d=4, scale=1.0, rank_scale="rs"):
    """Freeze the model and wrap every target linear layer; returns {module name: adapter}."""
    for p in model.parameters():
        p.requires_grad_(False)
    wrapped = {}
    for name, mod in list(model.named_modules()):
        for t in targets:
            lin = getattr(mod, t, None)
            if isinstance(lin, nn.Linear):
                ad = TTAdapterLinear(lin, ranks, d=d, scale=scale, rank_scale=rank_scale)
                setattr(mod, t, ad)
                wrapped[f"{name}.{t}" if name else t] = ad
    if not wrapped:
        raise ValueError(f"no linear layers named {targets} found")
    return wrapped


def reset_adapters(adapters, ranks):
    for ad in adapters.values():
        ad.reset(ranks)


def adapter_params(adapters):
    return [c for ad in adapters.values() for c in ad.cores]


def get_state(adapters):
    return {k: [c.detach().clone() for c in ad.cores] for k, ad in adapters.items()}


@torch.no_grad()
def set_state(adapters, state):
    for k, ad in adapters.items():
        for c, v in zip(ad.cores, state[k]):
            c.copy_(v)
