"""Positive and negative controls for the embedding-control protocol (synthetic data with known structure).

The excitation structure of the generating Hawkes process follows semantic topics of the type NAMES ("aligned") or is unrelated to
the names ("misaligned"). Two model families are fitted:
  generator family (as in the real-data study): free, qwen, qwencentered, hash, qwenperm, random, learned
  similarity-prior family (low capacity): A = softplus(A_free + w * S), S = cosine similarity of the (centered) type embeddings,
      with a ridge penalty on A_free; baseline ridge model without S ("ridge"), and S from Qwen / hash / permuted Qwen / random vectors.
If the protocol is sensitive, real embeddings should beat permuted / random ones in the aligned case, and not in the misaligned case.

    python -m semantic_hawkes.positive_control --workers 4
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

from . import data as D
from .encoders import encode
from .type_text_study import MAX_BETA, MIN_BETA, TypeHawkes, batch

torch.set_num_threads(1)
OUT = "semantic_hawkes/runs/positive_control.jsonl"
EMB_DIR = "semantic_hawkes/emb"
T_HORIZON, MAX_LEN, N_TEST, N_DEV = 30.0, 64, 200, 60
RIDGE = 0.05
GEN = ["free", "qwen", "qwencentered", "hash", "qwenperm", "random", "learned"]
SIM = ["ridge", "sim_qwen", "sim_hash", "sim_perm", "sim_random"]


class SimPrior(TypeHawkes):
    """Free Hawkes parameters plus a similarity-driven offset on the excitation logits (one extra scalar)."""

    def __init__(self, K, sim=None):
        super().__init__(K, "free")
        self.has_sim = sim is not None
        if self.has_sim:
            self.register_buffer("S", torch.as_tensor(sim, dtype=torch.float32))
            self.wA = nn.Parameter(torch.tensor(0.0))

    def params(self):
        a = self.A_raw + (self.wA * self.S if self.has_sim else 0.0)
        return F.softplus(self.mu_raw), F.softplus(a), (F.softplus(self.b_raw) + MIN_BETA).clamp(max=MAX_BETA)

    def penalty(self):
        return RIDGE * ((self.A_raw + 2.0) ** 2).mean()


def cosine_matrix(e):
    e = e - e.mean(0, keepdims=True)
    e = e / np.linalg.norm(e, axis=1, keepdims=True)
    return e @ e.T


def names_for(k_per_topic, seed=0):
    rng = random.Random(seed)
    descs, topics = [], []
    for t, (name, words) in enumerate(D.TOPICS.items()):
        pairs = [(a, b) for i, a in enumerate(words[1:]) for b in words[1:][i + 1:]]
        for a, b in rng.sample(pairs, k_per_topic):
            descs.append(f"{name} {a} {b}")
            topics.append(t)
    return descs, np.array(topics)


def embeddings(k_per_topic):
    path = f"{EMB_DIR}/synthetic_k{4 * k_per_topic}"
    descs, topics = names_for(k_per_topic)
    if not os.path.exists(path + "_qwen.npy"):
        np.save(path + "_qwen.npy", encode(descs, "hf:Qwen/Qwen2.5-0.5B"))
        np.save(path + "_hash.npy", encode(descs, "hash"))
    q = np.load(path + "_qwen.npy")
    c = q - q.mean(0, keepdims=True)
    c /= np.linalg.norm(c, axis=1, keepdims=True)
    return descs, topics, q, c, np.load(path + "_hash.npy")


def simulate(mu, A, beta, rng, max_len=MAX_LEN):
    """Ogata thinning, vectorized. Stops after max_len events (sequences are then observed up to their last event)."""
    amp = A * beta
    times, types = [], []
    t = 0.0
    while len(times) < max_len:
        if times:
            ta, ka = np.array(times), np.array(types)
            lam = mu + (amp[ka] * np.exp(-beta[ka] * (t - ta)[:, None])).sum(0)
        else:
            lam = mu
        bar = lam.sum()
        t = t + rng.exponential(1.0 / bar)
        if t >= T_HORIZON:
            break
        if times:
            lam = mu + (amp[ka] * np.exp(-beta[ka] * (t - ta)[:, None])).sum(0)
        else:
            lam = mu
        if rng.uniform() * bar <= lam.sum():
            times.append(t)
            types.append(int(rng.choice(len(mu), p=lam / lam.sum())))
    return times, types


def make_set(n, mu, A, beta, rng):
    out = []
    while len(out) < n:
        t, k = simulate(mu, A, beta, rng)
        if len(t) >= 3:
            out.append((t, k))
    return out


def evaluate(model, seqs, scale):
    model.eval()
    tot = dict(event_ll=0.0, comp=0.0, n=0)
    with torch.no_grad():
        for i in range(0, len(seqs), 50):
            r = model(*batch(seqs[i:i + 50], scale))
            tot["event_ll"] += float(r["event_ll"])
            tot["comp"] += float(r["comp"])
            tot["n"] += r["n"]
    return (tot["event_ll"] - tot["comp"]) / tot["n"]


def build(variant, K, tabs):
    if variant in GEN:
        kind = "free" if variant == "free" else ("learned" if variant == "learned" else "frozen")
        return TypeHawkes(K, kind, tabs.get(variant))
    return SimPrior(K, None if variant == "ridge" else cosine_matrix(tabs[variant]))


def fit(variant, train, dev, test, K, tabs, seed, scale):
    torch.manual_seed(seed)
    rng = random.Random(seed)
    model = build(variant, K, tabs)
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    bs = 8 if len(train) <= 200 else 32
    best, state, bad = -1e9, None, 0
    for ep in range(40):
        model.train()
        idx = list(range(len(train)))
        rng.shuffle(idx)
        for i in range(0, len(idx), bs):
            r = model(*batch([train[j] for j in idx[i:i + bs]], scale))
            loss = -(r["event_ll"] - r["comp"]) / max(r["n"], 1)
            if hasattr(model, "penalty"):
                loss = loss + model.penalty()
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 10.0)
            opt.step()
        v = evaluate(model, dev, scale)
        if v > best:
            best, bad, state = v, 0, {k: x.clone() for k, x in model.state_dict().items()}
        else:
            bad += 1
            if bad >= 6:
                break
    model.load_state_dict(state)
    w = float(model.wA.detach()) if getattr(model, "has_sim", False) else None
    return evaluate(model, test, scale), best, w


def oracle(mu, A, beta, test, scale):
    """Test log-likelihood of the data-generating parameters in the rescaled time unit used by the fitted models."""
    K = len(mu)
    m = TypeHawkes(K, "free")
    inv = lambda y: np.log(np.expm1(np.maximum(y, 1e-6)))
    with torch.no_grad():
        m.mu_raw.copy_(torch.tensor(inv(mu * scale), dtype=torch.float32))
        m.A_raw.copy_(torch.tensor(inv(A), dtype=torch.float32))
        m.b_raw.copy_(torch.tensor(inv(np.clip(beta * scale - MIN_BETA, 1e-6, None)), dtype=torch.float32))
    return evaluate(m, test, scale)


def job(args):
    scenario, k_per_topic, seed, sizes = args
    t0 = time.time()
    descs, topics, q, qc, hs = embeddings(k_per_topic)
    K = len(descs)
    rng = np.random.default_rng(1000 + seed)
    struct = topics if scenario == "aligned" else rng.permutation(topics)
    mu, A, beta = D.make_true_params(struct, seed=seed)
    sim_rng = np.random.default_rng(seed)
    dev, test = make_set(N_DEV, mu, A, beta, sim_rng), make_set(N_TEST, mu, A, beta, sim_rng)
    perm = rng.permutation(K)
    rnd = rng.normal(size=q.shape).astype(np.float32)
    rnd /= np.linalg.norm(rnd, axis=1, keepdims=True)
    tabs = {"qwen": q, "qwencentered": qc, "hash": hs, "qwenperm": q[perm], "random": rnd,
            "sim_qwen": q, "sim_hash": hs, "sim_perm": q[perm], "sim_random": rnd}
    res = []
    for n in sizes:
        train = make_set(n, mu, A, beta, sim_rng)
        scale = float(np.concatenate([np.diff(s[0]) for s in train]).mean())
        orc = oracle(mu, A, beta, test, scale)
        for v in GEN + SIM:
            ll, dev_ll, w = fit(v, train, dev, test, K, tabs, seed, scale)
            res.append(dict(scenario=scenario, K=K, n_train=n, seed=seed, variant=v, test_ll=ll, dev_ll=dev_ll, oracle_ll=orc, w=w))
    sec = round(time.time() - t0, 1)
    for r in res:
        r["seconds"] = sec
    return res


def done_keys():
    if not os.path.exists(OUT):
        return set()
    return {(r["scenario"], r["K"], r["seed"]) for r in map(json.loads, open(OUT))}


def work(a):
    try:
        res = job(a)
    except Exception as e:  # noqa: BLE001
        print("FAILED", a, repr(e)[:300], flush=True)
        return
    with open(OUT, "a") as f:
        for r in res:
            f.write(json.dumps(r) + "\n")
    print("ok", a[:3], round(res[0]["seconds"]), "s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--sizes", type=int, nargs="+", default=[20, 50, 200])
    ap.add_argument("--seeds", type=int, default=10)
    a = ap.parse_args()
    for k in (3, 8):
        embeddings(k)
    plan = [("aligned", 3, a.seeds), ("misaligned", 3, max(6, a.seeds * 3 // 5)), ("aligned", 8, max(5, a.seeds // 2))]
    have = done_keys()
    jobs = [(sc, kp, s, a.sizes) for sc, kp, ns in plan for s in range(ns) if (sc, 4 * kp, s) not in have]
    print(len(jobs), "jobs (each: all sizes, all variants)", flush=True)
    with Pool(a.workers) as p:
        list(p.imap_unordered(work, jobs, chunksize=1))
    print("POSITIVE_CONTROL_DONE", flush=True)
