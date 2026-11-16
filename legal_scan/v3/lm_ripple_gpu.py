"""Ripple-effect experiment: amending one provision and its consequences for dependent provisions.

Legal analogy. When a provision is amended, drafters add CONSEQUENTIAL amendments for the provisions that cross-refer to it,
and TRANSITIONAL / SAVING provisions for what must stay as it was. Here the same situation is built for a language model.

Facts (fictional statutes), 2 per pair:
  base    : "Under Article a of the <Act>, an application must be filed within"             -> deadline word
  derived : "Under Article b of the <Act>, the late-filing fee tier is determined by Article a, and the tier is"
                                                                                           -> h(deadline)   (fixed bijection)
An amendment revises a share rho of the base facts (new deadline). The authorized value of each dependent fact
becomes h(new deadline). The update stream states the revised base facts, restates a share of unrevised base facts,
adds new facts, and (consequential amendments) states the new value of a fraction kappa of the dependent facts.

Update disciplines (config = method:lam:kappa)
  none      : plain fine-tune on the stream (lam = 0)
  unscoped  : KL to the launch model on ALL launch facts
  ss        : KL on launch facts NOT in the stream (stream-scoped; dependents of revised bases are NOT in the stream
              unless listed, so they get anchored to their old value)
  dep       : like ss, but facts that depend on a revised base are also released (dependency graph used for scoping only)
Metrics
  base_new    : revised base facts answered with the new value
  ripple      : dependents of revised bases answered with the new derived value (also split: listed / unlisted)
  keep_base / keep_dep : unrevised base / dependent facts still answered with the launch value (collateral damage = 1 - keep)
  currency    : all launch facts answered with their currently authorized value
  acquisition : new facts learned

Run (8 GB GPU):
  python lm_ripple_gpu.py --model Qwen/Qwen2.5-1.5B --seeds 1 --out ripple_qwen15.json
"""
import argparse, json, random, time, os
import torch, torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM
import lm_supersession_gpu as G

ACTS = ["Housing Subsidy Act", "Vehicle Registration Act", "Small Business Licensing Act", "Student Aid Act",
        "Public Health Notification Act", "Tenant Protection Act", "Import Duty Act", "Waste Disposal Act",
        "Childcare Support Act", "Energy Efficiency Act", "Land Use Permit Act", "Pension Claims Act",
        "Water Utility Act", "Noise Control Act", "Food Safety Act", "Museum Grants Act",
        "Port Safety Act", "Library Funding Act", "Taxi Operations Act", "Disaster Relief Act"]
PAIRS = [("seven", "free"), ("ten", "reduced"), ("fourteen", "low"), ("fifteen", "standard"),
         ("twenty", "high"), ("thirty", "premium"), ("sixty", "exempt"), ("ninety", "special")]
RULE_T = ["Whenever the filing deadline is {d} days, the late-filing fee tier is",
          "A filing deadline of {d} days means the late-filing fee tier is",
          "If the deadline is {d} days, the late-filing fee tier is"]
CTX_T = "Note: under Article {a} of the {act}, an application must now be filed within {d} days. "
BASE_T = "Under Article {a} of the {act}, an application must be filed within"
DER_T = "Under Article {b} of the {act}, the late-filing fee tier is determined by Article {a}, and the tier is"

def one_token(tok, w): return len(tok(" " + w, add_special_tokens=False)["input_ids"]) == 1

def get_launch(args, seed, cache, dev):
    if seed in cache: return cache[seed]
    rng = random.Random(seed); torch.manual_seed(seed); gen = torch.Generator().manual_seed(seed)
    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    pairs = [(d, t) for d, t in PAIRS if one_token(tok, d) and one_token(tok, t)]
    if len(pairs) < 4: raise RuntimeError("too few single-token value pairs: %s" % pairs)
    h = dict(pairs); deadlines = [d for d, _ in pairs]
    Nb = args.n_base
    slots = [(act, a) for act in ACTS for a in range(2, 30)]; rng.shuffle(slots)
    need = Nb + args.n_new
    base_slots, new_slots = slots[:Nb], slots[Nb:need]
    # derived article number differs from the base article number
    base = [dict(act=act, a=a, b=a + 30, v=rng.choice(deadlines)) for act, a in base_slots]
    new = [dict(act=act, a=a, v=rng.choice(deadlines)) for act, a in new_slots]
    keys = [BASE_T.format(a=f["a"], act=f["act"]) for f in base] + [DER_T.format(a=f["a"], b=f["b"], act=f["act"]) for f in base]
    vals = [f["v"] for f in base] + [h[f["v"]] for f in base]                   # launch values, 2*Nb facts
    if args.rule_statements:                                                     # explicit statements of the rule h
        for d_, t_ in pairs:
            for tpl in RULE_T: keys.append(tpl.format(d=d_)); vals.append(t_)
    NT = len(keys)
    launch = G.enc(tok, keys, vals, dev)
    dtype = torch.bfloat16 if dev.type == "cuda" else torch.float32
    model0 = AutoModelForCausalLM.from_pretrained(args.model, dtype=dtype).to(dev)
    merged, acc, ep = G.train_launch(model0, launch, args, gen, dev); merged.eval()
    with torch.no_grad():
        tl = torch.cat([F.log_softmax(G.logits_at(merged, launch[0][i:i+64], launch[1][i:i+64], launch[2][i:i+64]), -1)
                        for i in range(0, NT, 64)])
    cache[seed] = dict(NT=NT, tok=tok, base=base, new=new, h=h, deadlines=deadlines, launch=launch, model=merged, teacher_lp=tl, acc=acc, ep=ep)
    return cache[seed]

def one(args, seed, rho, method, lam, kappa, cache, dev):
    c = get_launch(args, seed, cache, dev); tok, base, new, h, dl = c["tok"], c["base"], c["new"], c["h"], c["deadlines"]
    Nb = args.n_base; NT = c["NT"]; tag = int(rho * 100) + int(kappa * 10)
    rng = random.Random(seed * 1000 + int(rho * 100)); gen = torch.Generator().manual_seed(seed * 7 + tag)   # same amendment across configs
    idx = list(range(Nb)); rng.shuffle(idx); nr = int(round(rho * Nb)); R = idx[:nr]; U = idx[nr:]
    nv = {i: rng.choice([d for d in dl if d != base[i]["v"]]) for i in R}
    reaff = U[:int(round(args.reaff * len(U)))]
    lrng = random.Random(seed * 77 + int(rho * 100) + int(kappa * 100)); listed = set(lrng.sample(R, int(round(kappa * nr)))) if nr else set()
    s_keys = [BASE_T.format(a=base[i]["a"], act=base[i]["act"]) for i in R] + [BASE_T.format(a=base[i]["a"], act=base[i]["act"]) for i in reaff]
    s_vals = [nv[i] for i in R] + [base[i]["v"] for i in reaff]
    s_keys += [DER_T.format(a=base[i]["a"], b=base[i]["b"], act=base[i]["act"]) for i in sorted(listed)]
    s_vals += [h[nv[i]] for i in sorted(listed)]
    s_keys += [BASE_T.format(a=f["a"], act=f["act"]) for f in new]; s_vals += [f["v"] for f in new]
    stream = G.enc(tok, s_keys, s_vals, dev)
    in_stream = set(R) | set(reaff) | {Nb + i for i in listed}
    dependents_of_R = {Nb + i for i in R}
    if method == "unscoped": anch = list(range(NT))
    elif method == "ss": anch = [j for j in range(NT) if j not in in_stream]
    elif method == "dep": anch = [j for j in range(NT) if j not in in_stream and j not in dependents_of_R]
    else: anch = list(range(NT))
    anchors = torch.tensor(anch, dtype=torch.long, device=dev)
    model = G.run_update(c["model"], c["launch"], c["teacher_lp"], stream, anchors, lam if method != "none" else 0.0, args, gen, dev)
    pred = G.predict(model, c["launch"])[:2 * Nb]
    t_old = torch.tensor([G.tid(tok, base[i]["v"]) for i in range(Nb)] + [G.tid(tok, h[base[i]["v"]]) for i in range(Nb)], device=dev)
    t_new = t_old.clone()
    for i in R: t_new[i] = G.tid(tok, nv[i]); t_new[Nb + i] = G.tid(tok, h[nv[i]])
    def acc_(ids, tgt):
        ids = torch.tensor(sorted(ids), dtype=torch.long, device=dev)
        return (pred[ids] == tgt[ids]).float().mean().item() if len(ids) else float("nan")
    R_dep = [Nb + i for i in R]; unl = [Nb + i for i in R if i not in listed]; lst = [Nb + i for i in R if i in listed]
    keep_dep = [Nb + i for i in U]
    ctx_prompts = [CTX_T.format(a=base[i]["a"], act=base[i]["act"], d=nv[i]) + DER_T.format(a=base[i]["a"], b=base[i]["b"], act=base[i]["act"]) for i in R]
    ctx = G.enc(tok, ctx_prompts, [h[nv[i]] for i in R], dev) if R else None
    ripple_ctx = (G.predict(model, ctx) == ctx[3]).float().mean().item() if R else float("nan")
    nd = G.enc(tok, [BASE_T.format(a=f["a"], act=f["act"]) for f in new], [f["v"] for f in new], dev)
    ceiling = (len(U) + len(U) + len(R) + len(listed)) / (2 * Nb)
    row = dict(seed=seed, rho=rho, method=method, lam=lam, kappa=kappa, n_anchor=len(anch), rules=bool(args.rule_statements), ripple_ctx=ripple_ctx,
               base_new=acc_(R, t_new), ripple=acc_(R_dep, t_new), ripple_listed=acc_(lst, t_new), ripple_unlisted=acc_(unl, t_new),
               keep_base=acc_(U, t_old), keep_dep=acc_(keep_dep, t_old), currency=(pred == t_new).float().mean().item(), ceiling=ceiling,
               acquisition=(G.predict(model, nd) == nd[3]).float().mean().item(), launch_acc=c["acc"])
    c["model"] = model.unload()
    return row

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    ap.add_argument("--n-base", type=int, default=100); ap.add_argument("--n-new", type=int, default=40)
    ap.add_argument("--lora-r", type=int, default=16); ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--launch-epochs", type=int, default=80); ap.add_argument("--launch-lr", type=float, default=2e-4)
    ap.add_argument("--update-epochs", type=int, default=25); ap.add_argument("--update-lr", type=float, default=1e-4)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1]); ap.add_argument("--rhos", type=float, nargs="+", default=[0.3, 0.7])
    ap.add_argument("--reaff", type=float, default=0.2); ap.add_argument("--rule-statements", action="store_true", help="add explicit statements of the dependency rule to the launch data")
    ap.add_argument("--configs", nargs="+", default=["none:0:0", "unscoped:1:0", "unscoped:10:0", "ss:10:0", "dep:10:0", "ss:10:1", "ss:10:0.6", "dep:10:0.6"],
                    help="method:lam:kappa")
    ap.add_argument("--out", default="ripple.json")
    args = ap.parse_args()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu"); print("device:", dev, flush=True)
    rows = json.load(open(args.out)) if os.path.exists(args.out) else []
    done = {(r["seed"], r["rho"], r["method"], r["lam"], r["kappa"]) for r in rows}
    cfgs = [(m, float(l), float(k)) for m, l, k in (x.split(":") for x in args.configs)]
    cache = {}; t0 = time.time()
    for s in args.seeds:
        for rho in args.rhos:
            for method, lam, kappa in cfgs:
                if (s, rho, method, lam, kappa) in done: continue
                r = one(args, s, rho, method, lam, kappa, cache, dev); rows.append(r); json.dump(rows, open(args.out, "w"), indent=1)
                print(f"[{time.time()-t0:5.0f}s] seed={s} rho={rho} {method:8s} lam={lam:<4} k={kappa:<3} base={r['base_new']:.2f} "
                      f"ripple={r['ripple']:.2f} ctx={r['ripple_ctx']:.2f} keepB={r['keep_base']:.2f} keepD={r['keep_dep']:.2f} cur={r['currency']:.2f} "
                      f"(ceil {r['ceiling']:.2f}) acq={r['acquisition']:.2f} launch={r['launch_acc']:.2f}", flush=True)
