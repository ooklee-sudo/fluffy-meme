"""Stream-scoped KL anchoring (SS-KL): a test of whether the update stream itself can define the scope
of the constraint, so no separate supersession record or lambda tuning is needed.

Setting (same facts as lm_supersession_gpu.py): N launch facts; a share rho are superseded (authorized value changed).
The update stream contains
  - covered superseded facts (new value), a fraction `cov` of the superseded ones,
  - reaffirmed valid facts (old value restated), a fraction `reaff` of the valid ones,
  - new facts.
Methods
  none      : no constraint (lam = 0)
  unscoped  : KL to the launch model on ALL launch facts (weight lam)
  ss        : KL on launch facts that do NOT appear in the stream (weight lam)   <- proposed
Metrics
  currency          : launch facts answered with the currently authorized value (superseded -> new value,
                      including superseded facts the stream never mentions; no method can know those)
  continuity        : still-valid facts answered with the launch value
  cov_sup_new       : covered superseded facts answered with the new value
  uncov_sup_old     : uncovered superseded facts still answered with the OLD value (stale, unavoidable)
  acquisition       : new facts learned
Ceiling for currency is (1 - rho) + rho * cov.

Run (8 GB GPU), after lm_supersession_gpu.py has finished:
  python lm_autoscope_gpu.py --model Qwen/Qwen2.5-1.5B --seeds 1 2 --out autoscope_qwen15.json
"""
import argparse, json, random, time, os
import torch, torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM
import lm_supersession_gpu as G

CONFIGS = [("none", 0.0, 1.0), ("unscoped", 1.0, 1.0), ("unscoped", 10.0, 1.0), ("ss", 10.0, 1.0)]  # (method, lam, match)

def get_launch(args, seed, cache, dev):
    if seed in cache: return cache[seed]
    rng = random.Random(seed); torch.manual_seed(seed); gen = torch.Generator().manual_seed(seed)
    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    vals = G.single_token_values(tok)
    codes = rng.sample(range(100, 1000), args.n_launch + args.n_new)
    keys = [f"Under rule R-{c}, the processing category is" for c in codes]
    v0 = [rng.choice(vals) for _ in keys]
    lk, lv = keys[:args.n_launch], v0[:args.n_launch]; nk, nv = keys[args.n_launch:], v0[args.n_launch:]
    launch = G.enc(tok, lk, lv, dev)
    dtype = torch.bfloat16 if dev.type == "cuda" else torch.float32
    base = AutoModelForCausalLM.from_pretrained(args.model, dtype=dtype).to(dev)
    merged, acc, ep = G.train_launch(base, launch, args, gen, dev); merged.eval()
    with torch.no_grad():
        tl = torch.cat([F.log_softmax(G.logits_at(merged, launch[0][i:i+64], launch[1][i:i+64], launch[2][i:i+64]), -1)
                        for i in range(0, args.n_launch, 64)])
    cache[seed] = dict(tok=tok, vals=vals, lk=lk, lv=lv, nk=nk, nv=nv, launch=launch, model=merged, teacher_lp=tl, acc=acc, ep=ep)
    return cache[seed]

def one(args, seed, rho, cov, method, lam, match, cache, dev):
    c = get_launch(args, seed, cache, dev); tok = c["tok"]; N = args.n_launch
    rng = random.Random(seed * 1000 + int(rho * 100) + int(cov * 10)); gen = torch.Generator().manual_seed(seed * 7 + int(rho * 100) + int(cov * 10))
    idx = list(range(N)); rng.shuffle(idx); ns = int(round(rho * N)); sup = idx[:ns]; val = idx[ns:]
    v1 = {i: rng.choice([v for v in c["vals"] if v != c["lv"][i]]) for i in sup}
    covered = sup[:int(round(cov * ns))]; uncovered = sup[int(round(cov * ns)):]
    reaff = val[:int(round(args.reaff * len(val)))]
    s_idx = covered + reaff
    stream = G.enc(tok, [c["lk"][i] for i in s_idx] + c["nk"],
                   [v1[i] if i in v1 else c["lv"][i] for i in s_idx] + c["nv"], dev)
    in_stream = set(s_idx)
    if method == "ss":
        mrng = random.Random(seed * 31 + int(rho * 100) + int(cov * 10) + int(match * 100))
        detected = {i for i in in_stream if mrng.random() < match}     # stream facts the matcher links to launch facts
        anchors = torch.tensor([i for i in range(N) if i not in detected], dtype=torch.long, device=dev)
    elif method == "unscoped": anchors = torch.arange(N, device=dev)
    else: anchors = torch.arange(N, device=dev)
    model = G.run_update(c["model"], c["launch"], c["teacher_lp"], stream, anchors, lam if method != "none" else 0.0, args, gen, dev)
    pred = G.predict(model, c["launch"])
    v0t = torch.tensor([G.tid(tok, v) for v in c["lv"]], device=dev); v1t = v0t.clone()
    for i in sup: v1t[i] = G.tid(tok, v1[i])
    def frac(ids, tgt): return (pred[ids] == tgt[ids]).float().mean().item() if len(ids) else float("nan")
    ti = lambda l: torch.tensor(l, dtype=torch.long, device=dev)
    nd = G.enc(tok, c["nk"], c["nv"], dev)
    row = dict(seed=seed, rho=rho, cov=cov, method=method, lam=lam, match=match, n_anchor=int(len(anchors)),
               currency=(pred == v1t).float().mean().item(), ceiling=(1 - rho) + rho * cov,
               continuity=frac(ti(val), v0t), cov_sup_new=frac(ti(covered), v1t), uncov_sup_old=frac(ti(uncovered), v0t),
               acquisition=(G.predict(model, nd) == nd[3]).float().mean().item(), launch_acc=c["acc"])
    c["model"] = model.unload()
    return row

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    ap.add_argument("--n-launch", type=int, default=200); ap.add_argument("--n-new", type=int, default=50)
    ap.add_argument("--lora-r", type=int, default=16); ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--launch-epochs", type=int, default=60); ap.add_argument("--launch-lr", type=float, default=2e-4)
    ap.add_argument("--update-epochs", type=int, default=25); ap.add_argument("--update-lr", type=float, default=1e-4)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2])
    ap.add_argument("--rhos", type=float, nargs="+", default=[0.3, 0.7]); ap.add_argument("--covs", type=float, nargs="+", default=[1.0, 0.6])
    ap.add_argument("--reaff", type=float, default=0.2); ap.add_argument("--ss-matches", type=float, nargs="*", default=[]); ap.add_argument("--out", default="autoscope.json")
    args = ap.parse_args()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu"); print("device:", dev, flush=True)
    rows = json.load(open(args.out)) if os.path.exists(args.out) else []
    done = {(r["seed"], r["rho"], r["cov"], r["method"], r["lam"], r.get("match", 1.0)) for r in rows}
    cache = {}; t0 = time.time()
    for s in args.seeds:
        for rho in args.rhos:
            for cov in args.covs:
                for method, lam, match in CONFIGS + [("ss", 10.0, m) for m in args.ss_matches]:
                    if (s, rho, cov, method, lam, match) in done: continue
                    r = one(args, s, rho, cov, method, lam, match, cache, dev); rows.append(r); json.dump(rows, open(args.out, "w"), indent=1)
                    print(f"[{time.time()-t0:5.0f}s] seed={s} rho={rho} cov={cov} {method:8s} lam={lam:<4} m={match:<3} cur={r['currency']:.2f} "
                          f"(ceil {r['ceiling']:.2f}) cont={r['continuity']:.2f} covNew={r['cov_sup_new']:.2f} acq={r['acquisition']:.2f} "
                          f"launch={r['launch_acc']:.2f}", flush=True)
