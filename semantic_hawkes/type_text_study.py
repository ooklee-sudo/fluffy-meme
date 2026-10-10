"""Controlled study: do event-type texts help a Hawkes process, or does the shared low-dimensional structure explain the gain?

Variants (all share the exponential-kernel Hawkes likelihood; parameters mu, A, beta):
    free       free K x K matrices (no text)
    qwen       parameters generated from frozen Qwen2.5-0.5B embeddings of the type names
    hash       ... from hashed bag-of-words embeddings (lexical overlap only)
    qwenperm   ... from the Qwen embeddings assigned to the WRONG types (derangement)   [semantics destroyed]
    random     ... from random unit vectors                                            [no information]
    learned    ... from trainable embeddings (no text, same architecture)              [structure only]

Metrics follow the EasyTPP convention (first event conditioned on, events 2..N scored, time rescaled by the mean training
inter-event time). Next-type accuracy uses the intensity argmax at the true time. `ll_nontied` scores only events whose
timestamp differs from the previous event's (it removes the tied-timestamp effect, see the Amazon analysis).

    python -m semantic_hawkes.type_text_study --datasets us-earthquake --sizes 0 --seeds 0 --workers 1
"""
import argparse
import json
import os
import random
import time
from multiprocessing import Pool

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.set_num_threads(1)
MIN_BETA, MAX_BETA = 0.05, 20.0
DATA = "semantic_hawkes/real_data/tppllm"
EMB = "semantic_hawkes/emb"
OUT = "semantic_hawkes/runs/type_text_study.jsonl"


def load(name):
    d = {}
    for sp in ("train", "dev", "test"):
        x = json.load(open(f"{DATA}/{name}/{sp}.json"))
        d[sp] = [(s["time_since_start"], s["type_event"]) for s in x]
        d["K"] = x[0]["dim_process"]
    return d


def batch(seqs, scale):
    B, L = len(seqs), max(len(s[0]) for s in seqs)
    t = torch.zeros(B, L)
    a = torch.zeros(B, L, dtype=torch.long)
    m = torch.zeros(B, L, dtype=torch.bool)
    for b, (ts, ks) in enumerate(seqs):
        n = len(ts)
        t[b, :n] = torch.tensor(ts, dtype=torch.float32) / scale
        a[b, :n] = torch.tensor(ks)
        m[b, :n] = True
    return t, a, m


class TypeHawkes(nn.Module):
    def __init__(self, K, kind, emb=None, learned_dim=64, hidden=32):
        super().__init__()
        self.K, self.kind = K, kind
        if kind == "free":
            self.mu_raw = nn.Parameter(torch.full((K,), -2.0))
            self.A_raw = nn.Parameter(torch.full((K, K), -2.0))
            self.b_raw = nn.Parameter(torch.zeros(K, K))
            return
        if kind == "learned":
            self.emb = nn.Parameter(torch.randn(K, learned_dim) / learned_dim ** 0.5)
        else:
            self.register_buffer("emb", torch.as_tensor(emb, dtype=torch.float32))
        D = self.emb.shape[1]
        self.enc = nn.Sequential(nn.Linear(D, hidden), nn.Tanh(), nn.Linear(hidden, hidden))
        self.sA, self.dA = nn.Linear(hidden, hidden, bias=False), nn.Linear(hidden, hidden, bias=False)
        self.sB, self.dB = nn.Linear(hidden, hidden, bias=False), nn.Linear(hidden, hidden, bias=False)
        self.mu_head = nn.Linear(hidden, 1)
        self.bA, self.bB = nn.Parameter(torch.tensor(-2.0)), nn.Parameter(torch.tensor(0.0))
        self.scale = hidden ** -0.5

    def params(self):
        if self.kind == "free":
            return F.softplus(self.mu_raw), F.softplus(self.A_raw), (F.softplus(self.b_raw) + MIN_BETA).clamp(max=MAX_BETA)
        h = self.enc(self.emb)
        A = F.softplus(self.sA(h) @ self.dA(h).T * self.scale + self.bA)
        beta = (F.softplus(self.sB(h) @ self.dB(h).T * self.scale + self.bB) + MIN_BETA).clamp(max=MAX_BETA)
        return F.softplus(self.mu_head(h).squeeze(-1) - 2.0), A, beta

    def forward(self, t, a, m):
        mu, A, beta = self.params()
        B, L = t.shape
        lower = torch.tril(torch.ones(L, L, dtype=torch.bool), -1).T                     # [i, j]: i < j
        valid = lower[None] & m[:, :, None] & m[:, None, :]
        dt = (t[:, None, :] - t[:, :, None]).clamp(min=0)                                # t_j - t_i
        Ak, bk = A[a], beta[a]                                                           # (B,L,K) source-type rows
        kern = (Ak * bk)[:, :, None, :] * torch.exp(-bk[:, :, None, :] * dt[..., None])  # (B,i,j,K)
        lam = mu + (kern * valid[..., None]).sum(1)                                      # (B,j,K)
        logl = torch.log(torch.gather(lam, 2, a[..., None]).squeeze(-1) + 1e-9)          # log lambda_{a_j}(t_j)
        ev = m.clone()
        ev[:, 0] = False
        T = torch.where(m, t, torch.full_like(t, -1e30)).max(1).values
        remain = (T[:, None] - t).clamp(min=0)
        comp = mu.sum() * (T - t[:, 0]) + ((Ak * (1 - torch.exp(-bk * remain[:, :, None]))).sum(-1) * m).sum(1)
        tied = ev & (dt.diagonal(offset=0, dim1=1, dim2=2) == 0)                          # placeholder, replaced below
        prev = torch.zeros_like(t)
        prev[:, 1:] = t[:, :-1]
        tied = ev & (t - prev <= 0)
        return dict(event_ll=(logl * ev).sum(), comp=comp.sum(), n=int(ev.sum()), tied_ll=(logl * tied).sum(), n_tied=int(tied.sum()),
                    hit=int(((lam.argmax(-1) == a) & ev).sum()))


def run(job):
    name, n_train, seed, variant = job
    t0 = time.time()
    ds = load(name)
    K = ds["K"]
    rng = random.Random(seed)
    torch.manual_seed(seed)
    train = list(ds["train"])
    rng.shuffle(train)
    train = train[:n_train] if n_train else train
    scale = float(np.concatenate([np.diff(s[0]) for s in ds["train"]]).mean())
    emb = None
    if variant in ("qwen", "hash", "qwenperm", "random"):
        emb = np.load(f"{EMB}/{name}_{variant}.npy")
    model = TypeHawkes(K, "free" if variant == "free" else ("learned" if variant == "learned" else "frozen"), emb)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    bs = 8 if n_train and n_train <= 200 else 32
    epochs = max(40, int(np.ceil(400 / np.ceil(len(train) / bs)))) if n_train and n_train <= 200 else 40

    def evaluate(seqs):
        model.eval()
        tot = dict(event_ll=0.0, comp=0.0, n=0, tied_ll=0.0, n_tied=0, hit=0)
        with torch.no_grad():
            for i in range(0, len(seqs), 32):
                r = model(*batch(seqs[i:i + 32], scale))
                for k in tot:
                    tot[k] += float(r[k]) if k in ("event_ll", "comp", "tied_ll") else r[k]
        ll = (tot["event_ll"] - tot["comp"]) / tot["n"]
        nt = tot["n"] - tot["n_tied"]
        ll_nontied = ((tot["event_ll"] - tot["tied_ll"]) - tot["comp"]) / max(nt, 1)
        return ll, ll_nontied, tot["hit"] / tot["n"], tot["n_tied"] / tot["n"]

    best, best_state, best_ep, bad = -1e9, None, 0, 0
    for ep in range(epochs):
        model.train()
        idx = list(range(len(train)))
        rng.shuffle(idx)
        for i in range(0, len(idx), bs):
            r = model(*batch([train[j] for j in idx[i:i + bs]], scale))
            loss = -(r["event_ll"] - r["comp"]) / max(r["n"], 1)
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 10.0)
            opt.step()
        dev_ll = evaluate(ds["dev"])[0]
        if dev_ll > best:
            best, best_ep, bad = dev_ll, ep, 0
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= 6:
                break
    model.load_state_dict(best_state)
    ll, ll_nt, acc, tie = evaluate(ds["test"])
    mu, A, beta = [x.detach().numpy() for x in model.params()]
    return dict(data=name, n_train=n_train, seed=seed, variant=variant, test_ll=ll, test_ll_nontied=ll_nt, acc=acc, tie_frac=tie,
                dev_ll=best, best_epoch=best_ep, n_params=n_params, beta_med=float(np.median(beta)), beta_max=float(beta.max()),
                rho_A=float(np.max(np.abs(np.linalg.eigvals(A)))), seconds=round(time.time() - t0, 1))


def done_keys():
    if not os.path.exists(OUT):
        return set()
    return {(r["data"], r["n_train"], r["seed"], r["variant"]) for r in map(json.loads, open(OUT))}


def work(job):
    try:
        r = run(job)
    except Exception as e:  # noqa: BLE001
        print("FAILED", job, repr(e)[:200], flush=True)
        return
    with open(OUT, "a") as f:
        f.write(json.dumps(r) + "\n")
    print("ok", job, round(r["test_ll"], 4), r["seconds"], "s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=["us-earthquake", "chicago-crime", "amazon-review", "edgar-8k-filing", "edgar-8k-item",
                                                       "stack-overflow", "nyc-taxi"])
    ap.add_argument("--variants", nargs="+", default=["free", "qwen", "hash", "qwenperm", "random", "learned"])
    ap.add_argument("--sizes", type=int, nargs="+", default=[200, 0])
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    have = done_keys()
    jobs = [(d, n, s, v) for d in a.datasets for n in a.sizes for s in a.seeds for v in a.variants if (d, n, s, v) not in have]
    print(len(jobs), "jobs", flush=True)
    with Pool(a.workers) as p:
        list(p.imap_unordered(work, jobs, chunksize=1))
    print("STUDY_DONE", flush=True)
