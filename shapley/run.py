"""Full pipeline at n players: exact retrain table U, exact unlearning table Uhat per strength,
sequential-unlearning permutations, seed-noise check, relearning attack. Saves npz."""
import argparse, time, numpy as np
from multiprocessing import Pool
import sim

STRENGTHS = [3, 8, 20, 50, 100, 200]          # GA steps ("unlearning intensity")
cfg = {}

def build():
    n, kind = cfg["n"], cfg["kind"]
    if kind == "base": return sim.Setting(n, seed=cfg["seed"])
    reps = [1, 1] + list(np.random.default_rng(cfg["seed"] + 7).permutation([1, 2, 4, 8] * 3)[: n - 2])
    return sim.Setting(n, seed=cfg["seed"], dup=(0, 1), reps=[int(x) for x in reps])

S = None
def init_worker(c):
    global S, cfg; cfg = c; S = build()

def retrain(mask, seed=0): return S.evaluate(sim.train(*S.train_data(mask), seed=seed, epochs=cfg["epochs"]))

def full_model(): return sim.train(*S.train_data((1 << S.n) - 1), seed=0, epochs=cfg["epochs"])

def unlearn_all(mask):
    p = full_model(); Xf, Yf = S.forget_data(mask)
    return [S.evaluate(p if Xf is None else sim.unlearn_ga(p, Xf, Yf, st, seed=mask)) for st in STRENGTHS]

def seq(args):
    perm, st = args; p = full_model(); n = S.n; removed = 0; vals = [S.evaluate(p)]
    for g in perm:
        removed |= 1 << g; keep = ((1 << n) - 1) ^ removed
        # sequential: continue from the previous unlearned model, forget only group g
        p = sim.unlearn_ga(p, S.Xgr[g], S.Ygr[g], st, seed=g); vals.append(S.evaluate(p))
    return perm, np.array(vals)

def attack(args):
    st, k = args; p = full_model(); n = S.n; Xf, Yf = S.forget_data(0)
    q = sim.unlearn_ga(p, Xf, Yf, st, seed=0); r = np.random.default_rng(1)
    idx = r.choice(len(Yf), size=max(1, len(Yf) // 10), replace=False)   # 10% of forgotten data
    o = sim.Adam(q, 1e-3)
    for _ in range(k): o.step(q, sim.grads(q, Xf[idx], Yf[idx]))
    return S.evaluate(q)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10); ap.add_argument("--kind", default="base")
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--perms", type=int, default=100); ap.add_argument("--out", required=True)
    a = ap.parse_args(); c = vars(a); n = a.n; M = 1 << n; t0 = time.time()
    with Pool(4, initializer=init_worker, initargs=(c,)) as pool:
        U = np.array(pool.map(retrain, range(M), chunksize=16)); print("retrain", time.time() - t0, flush=True)
        Uh = np.array(pool.map(unlearn_all, range(M), chunksize=16)).transpose(1, 0, 2); print("unlearn", time.time() - t0, flush=True)
        r = np.random.default_rng(0); perms = [list(r.permutation(n)) for _ in range(a.perms)]
        sq = {st: pool.map(seq, [(p, st) for p in perms]) for st in STRENGTHS}; print("seq", time.time() - t0, flush=True)
        noise = {m: np.array(pool.starmap(retrain, [(m, s) for s in range(1, 9)])) for m in (0, M // 2 - 1, M - 1)}
        att = {st: np.array(pool.map(attack, [(st, k) for k in (0, 5, 20, 60)])) for st in STRENGTHS}
    init_worker(c)
    np.savez(a.out, U=U, Uh=Uh, strengths=STRENGTHS, reps=S.reps, noise_masks=list(noise),
             noise=np.array(list(noise.values())), attack=np.array([att[s] for s in STRENGTHS]),
             seq_perms=np.array([[list(p) for p, _ in sq[s]] for s in STRENGTHS]),
             seq_vals=np.array([[v for _, v in sq[s]] for s in STRENGTHS]))
    print("done", time.time() - t0)
