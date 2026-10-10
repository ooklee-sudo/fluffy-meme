"""Hawkes process whose excitation depends on the *content* of each event (direction C).

    lambda_k(t) = mu_k + sum_{i: t_i < t} A_ik * beta[a_i,k] * exp(-beta[a_i,k] (t - t_i)),
    A_ik        = softplus( C[a_i,k] + <g(e_i), V_k> )          (e_i: embedding of the text of event i)

C[a_i,k] is the usual type-pair term, so variant `free` (no text) is the classical multivariate Hawkes model.
The likelihood stays exact (closed-form compensator). Variants:
    free        no text
    text        real event embeddings
    text_shuf   embeddings shuffled across events *of the same type* (keeps the type-conditional marginal, destroys event content)
    text_rand   random unit vectors per event (same capacity, no information)

    python -m semantic_hawkes.event_text_model --variants free text text_shuf text_rand --seeds 0 1 2
"""
import argparse
import json
import random

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

D = "semantic_hawkes/real_data/edgar_text"
MIN_BETA, MAX_BETA = 0.05, 20.0


def load():
    ds = json.load(open(f"{D}/dataset.json"))
    emb = np.load(f"{D}/emb.npy")
    return ds, emb


def make_batch(seqs, scale, emb_table, idx_override=None):
    B = len(seqs)
    L = max(len(s["times"]) for s in seqs)
    t = torch.zeros(B, L)
    a = torch.zeros(B, L, dtype=torch.long)
    m = torch.zeros(B, L, dtype=torch.bool)
    e = torch.zeros(B, L, emb_table.shape[1])
    for b, s in enumerate(seqs):
        n = len(s["times"])
        t[b, :n] = torch.tensor(s["times"]) / scale
        a[b, :n] = torch.tensor(s["types"])
        m[b, :n] = True
        ids = s["emb"] if idx_override is None else idx_override[id(s)]
        e[b, :n] = torch.from_numpy(emb_table[ids])
    return t, a, m, e


class EventHawkes(nn.Module):
    def __init__(self, K, D_emb, use_text, hidden=16):
        super().__init__()
        self.K, self.use_text = K, use_text
        self.mu_raw = nn.Parameter(torch.full((K,), -2.0))
        self.A_raw = nn.Parameter(torch.full((K, K), -2.0))
        self.b_raw = nn.Parameter(torch.zeros(K, K))
        if use_text:
            self.enc = nn.Sequential(nn.Linear(D_emb, hidden), nn.Tanh())
            self.V = nn.Parameter(torch.zeros(hidden, K))   # starts at the type-only model

    def params(self):
        mu = F.softplus(self.mu_raw)
        beta = (F.softplus(self.b_raw) + MIN_BETA).clamp(max=MAX_BETA)
        return mu, beta

    def amplitudes(self, a, e):                              # (B,L,K): A_ik for each source event i and target type k
        z = self.A_raw[a]
        if self.use_text:
            z = z + self.enc(e) @ self.V
        return F.softplus(z)

    def _kernel(self, t, a, m, e):
        mu, beta = self.params()
        A = self.amplitudes(a, e)                            # (B,L,K)
        bs = beta[a]                                         # (B,L,K) decay of the pair (a_i, k)
        return mu, beta, A, bs

    def log_lik(self, t, a, m, e):
        mu, beta, A, bs = self._kernel(t, a, m, e)
        B, L = t.shape
        lower = torch.tril(torch.ones(L, L, dtype=torch.bool), -1).T            # [i,j]: i < j
        tgt = a[:, None, :].expand(B, L, L)                                       # type of target j
        A_ij = torch.gather(A, 2, tgt)                                            # A[b,i,k_j]
        b_ij = torch.gather(bs, 2, tgt)
        dt = (t[:, None, :] - t[:, :, None]).clamp(min=0)
        valid = lower[None] & m[:, :, None] & m[:, None, :]
        kern = torch.where(valid, A_ij * b_ij * torch.exp(-b_ij * dt), torch.zeros_like(dt))
        lam = mu[a] + kern.sum(1)                                                 # (B,L)
        ev = m.clone()
        ev[:, 0] = False
        event_ll = (torch.log(lam + 1e-9) * ev).sum()
        T = torch.where(m, t, torch.full_like(t, -1e30)).max(1).values
        remain = (T[:, None] - t).clamp(min=0)
        comp_ev = (A * (1 - torch.exp(-bs * remain[:, :, None]))).sum(-1)
        comp = mu.sum() * (T - t[:, 0]) + (comp_ev * m).sum(1)
        return event_ll - comp.sum(), int(ev.sum().item())

    @torch.no_grad()
    def accuracy(self, t, a, m, e):
        mu, beta, A, bs = self._kernel(t, a, m, e)
        B, L = t.shape
        lower = torch.tril(torch.ones(L, L, dtype=torch.bool), -1).T
        dt = (t[:, None, :] - t[:, :, None]).clamp(min=0)                         # [b,i,j]
        valid = lower[None] & m[:, :, None] & m[:, None, :]
        kern = (A * bs)[:, :, None, :] * torch.exp(-bs[:, :, None, :] * dt[..., None])    # (B,i,j,K)
        lam = mu + (kern * valid[..., None]).sum(1)                                # (B,j,K)
        ev = m.clone()
        ev[:, 0] = False
        return ((lam.argmax(-1) == a) & ev).sum().item(), ev.sum().item()


def shuffle_within_type(seqs, seed):
    """Permute the event embeddings among events of the same type inside one split."""
    rng = random.Random(seed)
    by = {}
    for s in seqs:
        for pos, (k, ei) in enumerate(zip(s["types"], s["emb"])):
            by.setdefault(k, []).append(ei)
    perm = {k: rng.sample(v, len(v)) for k, v in by.items()}
    ptr = {k: 0 for k in by}
    out = {}
    for s in seqs:
        ids = []
        for k in s["types"]:
            ids.append(perm[k][ptr[k]])
            ptr[k] += 1
        out[id(s)] = ids
    return out


def run(variant, seed, ds, emb, n_train, epochs, lr, bs, verbose=False):
    torch.manual_seed(seed)
    rng = random.Random(seed)
    train = list(ds["train"])
    rng.shuffle(train)
    train = train[:n_train] if n_train else train
    dev, test = ds["dev"], ds["test"]
    dts = np.concatenate([np.diff(s["times"]) for s in ds["train"]])
    scale = float(dts.mean())                                                     # rescale as in the EasyTPP runs
    table, overrides = emb, {}
    if variant == "text_rand":
        r = np.random.default_rng(seed).normal(size=emb.shape).astype(np.float32)
        table = r / np.linalg.norm(r, axis=1, keepdims=True)
    if variant == "text_shuf":
        for name, part in (("train", train), ("dev", dev), ("test", test)):
            overrides.update(shuffle_within_type(part, seed + 17))
    model = EventHawkes(ds["K"], emb.shape[1], variant != "free")
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=0.0)

    def batches(seqs, shuffle=False):
        idx = list(range(len(seqs)))
        if shuffle:
            rng.shuffle(idx)
        for i in range(0, len(idx), bs):
            yield make_batch([seqs[j] for j in idx[i:i + bs]], scale, table, overrides or None)

    def evaluate(seqs):
        model.eval()
        ll = n = hit = tot = 0
        with torch.no_grad():
            for t, a, m, e in batches(seqs):
                l, k = model.log_lik(t, a, m, e)
                h, c = model.accuracy(t, a, m, e)
                ll, n, hit, tot = ll + l.item(), n + k, hit + h, tot + c
        return ll / n, hit / tot

    best, best_state = -1e9, None
    for ep in range(epochs):
        model.train()
        for t, a, m, e in batches(train, True):
            ll, n = model.log_lik(t, a, m, e)
            loss = -ll / max(n, 1)
            opt.zero_grad()
            loss.backward()
            opt.step()
        v, _ = evaluate(dev)
        if v > best:
            best, best_state = v, {k: x.clone() for k, x in model.state_dict().items()}
        if verbose:
            print(ep, round(v, 4))
    model.load_state_dict(best_state)
    ll, acc = evaluate(test)
    return dict(variant=variant, seed=seed, n_train=n_train or len(ds["train"]), test_ll=ll, acc=acc, dev_ll=best)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="+", default=["free", "text", "text_shuf", "text_rand"])
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--sizes", type=int, nargs="+", default=[0], help="0 = all training sequences")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--lr", type=float, default=1e-2)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--out", default="semantic_hawkes/runs/event_text_results.jsonl")
    a = ap.parse_args()
    ds, emb = load()
    print("K =", ds["K"], "| train/dev/test seqs:", [len(ds[s]) for s in ("train", "dev", "test")], "| emb", emb.shape, flush=True)
    for n in a.sizes:
        for seed in a.seeds:
            for v in a.variants:
                r = run(v, seed, ds, emb, n, a.epochs, a.lr, a.bs)
                print(r, flush=True)
                open(a.out, "a").write(json.dumps(r) + "\n")
