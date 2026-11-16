"""Regulation-style version of the supersession experiment (more realistic text than rule codes).

Facts are provisions of FICTIONAL statutes ("Article 14 of the Housing Subsidy Act") with two attributes:
  deadline : how many days an applicant has (value = spelled-out number)
  fee tier : which fee tier applies (value = tier word)
Each fact is stated in 3 paraphrases (p0, p1, p2). The launch model learns all three. An amendment changes the
value of a share rho of the facts (superseded). The update stream states each covered revised fact in ONE random
paraphrase, restates a share of valid facts, and adds new facts. We then evaluate every launch fact in ALL three
paraphrases, so an update must generalize across wording (as real amendments do).

Methods (same as lm_autoscope_gpu.py): none | unscoped KL | ss (stream-scoped KL) | ss_ce (stream-scoped replay).
Metrics: currency (all 3 phrasings), continuity (valid facts), covered_new_same / covered_new_other
(covered superseded facts in the stream's phrasing vs the other two), acquisition.

Run (8 GB GPU):
  python lm_regulatory_gpu.py --model Qwen/Qwen2.5-1.5B --seeds 1 --out regulatory_qwen15.json
"""
import argparse, json, random, time, os
import torch, torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM
import lm_supersession_gpu as G
import lm_autoscope_gpu as A

ACTS = ["Housing Subsidy Act", "Vehicle Registration Act", "Small Business Licensing Act", "Student Aid Act",
        "Public Health Notification Act", "Tenant Protection Act", "Import Duty Act", "Waste Disposal Act",
        "Childcare Support Act", "Energy Efficiency Act", "Land Use Permit Act", "Pension Claims Act",
        "Water Utility Act", "Noise Control Act", "Food Safety Act", "Museum Grants Act",
        "Port Safety Act", "Library Funding Act", "Taxi Operations Act", "Disaster Relief Act",
        "Veterans Benefits Act", "Fishing Quota Act", "Rural Broadband Act", "Elder Care Act"]
DEADLINES = "seven ten fourteen fifteen twenty thirty sixty ninety".split()
TIERS = "free reduced low standard high premium".split()
TEMPL = {
    "deadline": ["Under Article {a} of the {act}, an application must be filed within",
                 "According to the {act}, Article {a}, the filing deadline for applicants is",
                 "Q: How many days does an applicant have to file under Article {a} of the {act}? A:"],
    "tier": ["Under Article {a} of the {act}, the filing fee falls in the category of",
             "According to the {act}, Article {a}, the fee tier is",
             "Q: Which fee tier applies under Article {a} of the {act}? A:"],
}

def tok_ok(tok, words): return [w for w in words if len(tok(" " + w, add_special_tokens=False)["input_ids"]) == 1]

def build(args, tok, rng):
    dl, tr = tok_ok(tok, DEADLINES), tok_ok(tok, TIERS)
    if len(dl) < 5 or len(tr) < 4: raise RuntimeError("too few single-token values: %s %s" % (dl, tr))
    combos = [(act, art, attr) for act in ACTS for art in range(2, 40) for attr in ("deadline", "tier")]
    rng.shuffle(combos)
    facts = []
    for act, art, attr in combos[:args.n_launch + args.n_new]:
        prompts = [t.format(a=art, act=act) for t in TEMPL[attr]]
        pool = dl if attr == "deadline" else tr
        facts.append(dict(prompts=prompts, value=rng.choice(pool), pool=pool))
    return facts

def get_launch(args, seed, cache, dev):
    if seed in cache: return cache[seed]
    rng = random.Random(seed); torch.manual_seed(seed); gen = torch.Generator().manual_seed(seed)
    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    facts = build(args, tok, rng); N = args.n_launch
    L, NEW = facts[:N], facts[N:]
    keys = [p for f in L for p in f["prompts"]]; vals = [f["value"] for f in L for _ in range(3)]
    launch = G.enc(tok, keys, vals, dev)
    base = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16 if dev.type == "cuda" else torch.float32).to(dev)
    merged, acc, ep = G.train_launch(base, launch, args, gen, dev); merged.eval()
    with torch.no_grad():
        tl = torch.cat([F.log_softmax(G.logits_at(merged, launch[0][i:i+64], launch[1][i:i+64], launch[2][i:i+64]), -1)
                        for i in range(0, 3 * N, 64)])
    cache[seed] = dict(tok=tok, L=L, NEW=NEW, launch=launch, model=merged, teacher_lp=tl, acc=acc, ep=ep)
    return cache[seed]

def one(args, seed, rho, cov, method, lam, match, cache, dev):
    c = get_launch(args, seed, cache, dev); tok = c["tok"]; L, NEW = c["L"], c["NEW"]; N = args.n_launch
    tag = int(rho * 100) + int(cov * 10)
    rng = random.Random(seed * 1000 + tag); gen = torch.Generator().manual_seed(seed * 7 + tag)
    idx = list(range(N)); rng.shuffle(idx); ns = int(round(rho * N)); sup = idx[:ns]; val = idx[ns:]
    new_val = {i: rng.choice([v for v in L[i]["pool"] if v != L[i]["value"]]) for i in sup}
    covered = sup[:int(round(cov * ns))]; uncovered = sup[int(round(cov * ns)):]
    reaff = val[:int(round(args.reaff * len(val)))]
    s_idx = covered + reaff; phr = {i: rng.randrange(3) for i in s_idx}
    s_keys = [L[i]["prompts"][phr[i]] for i in s_idx] + [f["prompts"][rng.randrange(3)] for f in NEW]
    s_vals = [new_val.get(i, L[i]["value"]) for i in s_idx] + [f["value"] for f in NEW]
    stream = G.enc(tok, s_keys, s_vals, dev)
    in_stream = set(s_idx)
    if method in ("ss", "ss_ce"):
        mrng = random.Random(seed * 31 + tag + int(match * 100))
        detected = {i for i in in_stream if mrng.random() < match}
        anchor_facts = [i for i in range(N) if i not in detected]
    else: anchor_facts = list(range(N))
    anchors = torch.tensor([3 * i + j for i in anchor_facts for j in range(3)], dtype=torch.long, device=dev)
    if method == "ss_ce": model = A.run_update_ce(c["model"], c["launch"], stream, anchors, lam, args, gen, dev)
    else: model = G.run_update(c["model"], c["launch"], c["teacher_lp"], stream, anchors, lam if method != "none" else 0.0, args, gen, dev)
    pred = G.predict(model, c["launch"]).view(N, 3)                       # fact x phrasing
    t0 = torch.tensor([[G.tid(tok, L[i]["value"])] * 3 for i in range(N)], device=dev); t1 = t0.clone()
    for i in sup: t1[i] = G.tid(tok, new_val[i])
    ti = lambda l: torch.tensor(l, dtype=torch.long, device=dev)
    def acc_on(ids, tgt, mask=None):
        if not len(ids): return float("nan")
        ok = (pred[ids] == tgt[ids]).float()
        return (ok if mask is None else ok[mask]).mean().item()
    same = torch.zeros(len(covered), 3, dtype=torch.bool, device=dev)
    for r, i in enumerate(covered): same[r, phr[i]] = True
    cov_ids = ti(covered)
    cov_ok = (pred[cov_ids] == t1[cov_ids]) if len(covered) else None
    cov_same = cov_ok[same].float().mean().item() if len(covered) else float("nan")
    cov_other = cov_ok[~same].float().mean().item() if len(covered) else float("nan")
    nd_keys = [p for f in NEW for p in f["prompts"]]; nd_vals = [f["value"] for f in NEW for _ in range(3)]
    nd = G.enc(tok, nd_keys, nd_vals, dev)
    row = dict(seed=seed, rho=rho, cov=cov, method=method, lam=lam, match=match, n_anchor=int(len(anchors)),
               currency=(pred == t1).float().mean().item(), ceiling=(1 - rho) + rho * cov,
               continuity=acc_on(ti(val), t0), covered_new_same=cov_same, covered_new_other=cov_other,
               uncov_old=acc_on(ti(uncovered), t0), acquisition=(G.predict(model, nd) == nd[3]).float().mean().item(),
               launch_acc=c["acc"])
    c["model"] = model.unload()
    return row

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    ap.add_argument("--n-launch", type=int, default=200); ap.add_argument("--n-new", type=int, default=50)
    ap.add_argument("--lora-r", type=int, default=16); ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--launch-epochs", type=int, default=60); ap.add_argument("--launch-lr", type=float, default=2e-4)
    ap.add_argument("--update-epochs", type=int, default=25); ap.add_argument("--update-lr", type=float, default=1e-4)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1])
    ap.add_argument("--rhos", type=float, nargs="+", default=[0.3, 0.7]); ap.add_argument("--covs", type=float, nargs="+", default=[1.0])
    ap.add_argument("--reaff", type=float, default=0.2)
    ap.add_argument("--configs", nargs="+", default=["none:0:1", "unscoped:1:1", "unscoped:10:1", "ss:10:1", "ss_ce:1:1"],
                    help="method:lam:match")
    ap.add_argument("--out", default="regulatory.json")
    args = ap.parse_args()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu"); print("device:", dev, flush=True)
    rows = json.load(open(args.out)) if os.path.exists(args.out) else []
    done = {(r["seed"], r["rho"], r["cov"], r["method"], r["lam"], r["match"]) for r in rows}
    cfgs = [(m, float(l), float(k)) for m, l, k in (x.split(":") for x in args.configs)]
    cache = {}; t0 = time.time()
    for s in args.seeds:
        for rho in args.rhos:
            for cov in args.covs:
                for method, lam, match in cfgs:
                    if (s, rho, cov, method, lam, match) in done: continue
                    r = one(args, s, rho, cov, method, lam, match, cache, dev); rows.append(r); json.dump(rows, open(args.out, "w"), indent=1)
                    print(f"[{time.time()-t0:5.0f}s] seed={s} rho={rho} cov={cov} {method:8s} lam={lam:<4} m={match:<3} cur={r['currency']:.2f} "
                          f"(ceil {r['ceiling']:.2f}) cont={r['continuity']:.2f} newSame={r['covered_new_same']:.2f} "
                          f"newOther={r['covered_new_other']:.2f} acq={r['acquisition']:.2f} launch={r['launch_acc']:.2f}", flush=True)
