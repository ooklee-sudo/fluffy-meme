"""Full-vocabulary free generation with a planted attractor (review points 3, 6).

No candidate restriction: every token is sampled from the model's complete
softmax at temperature T, the reference is the clean-context full-vocabulary
distribution on the same history. Completions are also clustered with an
entailment model (Farquhar et al. style) to give a faithful semantic-entropy
baseline on open-ended output, and wall-clock costs are recorded.

  python free_gen.py --model Qwen/Qwen2.5-1.5B-Instruct --n 20
"""
import argparse
import copy
import json
import os
import time

import numpy as np
import torch

from teff_core import GRID, LM, TASKS, cell_seed, make_user
from run_study import probe_m, short

G80 = GRID[::3]                      # 80-point grid for full-vocabulary scoring
MAX_NEW = 24
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def batched_stream(lm, prefix_text, history_text, n):
    st = lm._state(prefix_text)
    cache = copy.deepcopy(st["cache"])
    cache.batch_repeat_interleave(n)
    ids = lm.tok(history_text, add_special_tokens=False,
                 return_tensors="pt").input_ids.expand(n, -1)
    with torch.no_grad():
        out = lm.model(input_ids=ids, past_key_values=cache, use_cache=True)
    return cache, out.logits[:, -1].float()


def step(lm, cache, tok):
    with torch.no_grad():
        out = lm.model(input_ids=tok[:, None], past_key_values=cache,
                       use_cache=True)
    return out.logits[:, -1].float()


def gen_cell(lm, task, m, T, n, pressure, contam, seed_key="free",
             timing=None):
    items = TASKS[task]["items"]
    cand = torch.tensor(lm.cand_ids(items))
    hist = " ".join([items[0], items[1]] + [items[1]] * m)
    pre_s = lm.chat_prefix(make_user(task, pressure, contam, items[1]))
    pre_c = lm.chat_prefix(make_user(task))
    g = torch.Generator().manual_seed(cell_seed(lm.name, task, m, T, pressure,
                                                contam, seed_key))
    t0 = time.perf_counter()
    cs, z = batched_stream(lm, pre_s, hist, n)
    t_main = time.perf_counter() - t0
    t0 = time.perf_counter()
    cr, v = batched_stream(lm, pre_c, hist, n)
    t_ref = time.perf_counter() - t0
    eos = {lm.tok.eos_token_id}
    for t in ("<|im_end|>", "<|eot_id|>", "<|endoftext|>"):
        i = lm.tok.convert_tokens_to_ids(t)
        if isinstance(i, int) and i >= 0 and i != lm.tok.unk_token_id:
            eos.add(i)
    alive = torch.ones(n, dtype=torch.bool)
    toks = [[] for _ in range(n)]
    recs = []                              # per step dicts of (n,) arrays
    grid_t = torch.tensor(G80, dtype=torch.float32)
    for s in range(MAX_NEW):
        lp = torch.log_softmax(z / T, -1)
        lq = torch.log_softmax(v / T, -1)
        p = lp.exp()
        y = torch.multinomial(p, 1, generator=g)[:, 0]
        ar = torch.arange(n)
        ent = -(p * lp).sum(-1)
        kl = (p * (lp - lq)).sum(-1)
        ll = torch.empty(n, len(G80))
        for j, tau in enumerate(grid_t):
            ll[:, j] = (v[ar, y] / tau) - torch.logsumexp(v / tau, -1)
        # candidate-restricted likelihood (first step only: all trajectories
        # share the same history, so it is directly comparable to the
        # full-vocabulary likelihood at that step)
        llc = torch.zeros(n, len(G80))
        if s == 0:
            vc = v[:, cand]
            pos = (y[:, None] == cand[None, :]).float().argmax(1)
            for j, tau in enumerate(grid_t):
                llc[:, j] = (vc / tau - torch.logsumexp(vc / tau, -1,
                                                        keepdim=True))[ar, pos]
        in_c = torch.isin(y, cand)
        recs.append(dict(alive=alive.clone(), ent=ent, kl=kl,
                         py=p[ar, y], nll=-lq[ar, y], ll=ll, llc=llc, in_cand=in_c,
                         top1=(v.argmax(-1) == y), step=s, y=y.clone()))
        for i in range(n):
            if alive[i]:
                toks[i].append(int(y[i]))
        alive = alive & ~torch.isin(y, torch.tensor(list(eos)))
        if not alive.any():
            break
        t0 = time.perf_counter()
        z = step(lm, cs, y)
        t_main += time.perf_counter() - t0
        t0 = time.perf_counter()
        v = step(lm, cr, y)
        t_ref += time.perf_counter() - t0
    texts = []
    for i in range(n):
        tt = [x for x in toks[i] if x not in eos]
        texts.append(lm.tok.decode(tt).strip())
    return recs, texts, dict(t_main=t_main, t_ref=t_ref, steps=len(recs))


def summarize(recs, texts, task, m, T):
    items = TASKS[task]["items"]
    n = len(texts)
    alive = torch.stack([r["alive"] for r in recs])            # (S,n)
    def mean_traj(key):
        x = torch.stack([r[key] for r in recs]).float()
        return ((x * alive).sum(0) / alive.sum(0).clamp(min=1)).numpy()
    ent, kl, nll, py = (mean_traj(k) for k in ("ent", "kl", "nll", "py"))
    top1 = mean_traj("top1")
    LL = torch.stack([r["ll"] for r in recs])                   # (S,n,G)
    LLm = (LL * alive[..., None]).sum(0).numpy()                # (n,G)
    N = alive.sum(0).numpy()
    # items-level correctness of the generated list
    acc, lock = [], []
    for tx in texts:
        w = tx.split()
        prev = items[1]
        ok = []
        for x in w:
            if x in items and prev in items:
                ok.append(items.index(x) == items.index(prev) + 1)
            else:
                ok.append(False)
            prev = x
        acc.append(float(np.mean(ok)) if ok else 0.0)
        lock.append(float(np.mean([x == items[1] for x in w])) if w else 0.0)
    first = recs[0]
    return dict(ent=ent, kl=kl, nll=nll, py=py, top1=top1, LL=LLm, N=N,
                acc=np.array(acc), lock=np.array(lock),
                first_ll=first["ll"].numpy(), first_llc=first["llc"].numpy(),
                first_in_cand=first["in_cand"].numpy())


def teff80(ll_sum):
    j = int(np.argmax(ll_sum))
    inside = np.where(2 * (ll_sum[j] - ll_sum) <= 3.841)[0]
    return float(G80[j]), float(G80[inside.min()]), float(G80[inside.max()])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--tasks", default="alphabet,months")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    lm = LM(a.model)
    conds = {"clean": (None, None), "P0": ("P0", None), "C0": (None, "C0"),
             "P0+C0": ("P0", "C0"), "C2": (None, "C2")}
    out = {}
    for task in a.tasks.split(","):
        m = probe_m(lm, task)["sticky"]
        for T in (0.8, 2.0):
            for cname, (pres, cont) in conds.items():
                recs, texts, tim = gen_cell(lm, task, m, T, a.n, pres, cont)
                S = summarize(recs, texts, task, m, T)
                tot = S["LL"].sum(0)
                te, lo, hi = teff80(tot)
                key = f"{task}|{T}|{cname}"
                out[key] = dict(
                    m=m, T=T, texts=texts, timing=tim,
                    teff=te, lo=lo, hi=hi, nll=float(S["nll"].mean()),
                    ent=float(S["ent"].mean()), kl=float(S["kl"].mean()),
                    py=float(S["py"].mean()), acc=float(S["acc"].mean()),
                    lock=float(S["lock"].mean()),
                    ntok=float(S["N"].mean()),
                    first_full=teff80(S["first_ll"][S["first_in_cand"]].sum(0))[0]
                    if S["first_in_cand"].any() else None,
                    first_restricted=teff80(S["first_llc"][S["first_in_cand"]].sum(0))[0]
                    if S["first_in_cand"].any() else None,
                    first_in_cand=float(S["first_in_cand"].mean()),
                    traj=dict(ent=S["ent"].tolist(), kl=S["kl"].tolist(),
                              nll=S["nll"].tolist(), py=S["py"].tolist(),
                              acc=S["acc"].tolist(), lock=S["lock"].tolist(),
                              teff=[teff80(S["LL"][i])[0] for i in range(a.n)]))
                print(f"[{short(lm.name)}] {key:24s} acc={out[key]['acc']:.2f} "
                      f"lock={out[key]['lock']:.2f} ent={out[key]['ent']:.2f} "
                      f"Teff={te:.2f} [{lo:.2f},{hi:.2f}] "
                      f"t_main={tim['t_main']:.1f}s t_ref={tim['t_ref']:.1f}s",
                      flush=True)
                json.dump(dict(model=lm.name, n=a.n, res=out),
                          open(os.path.join(OUT, f"free_{short(a.model)}.json"),
                               "w"))
