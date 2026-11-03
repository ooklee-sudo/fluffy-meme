"""Small real-law experiment: UK statutory amendments (see real_law/README.md) with multi-token values.

Launch model: LoRA-trained on the pre-amendment value of every fact in real_fact_bank.json
  (27 changed provisions + 90 unchanged control provisions, each as "<Act>, section n (title): <statutory text up to the value>" -> value).
Update: a fresh LoRA on a stream that restates amended provisions with the new value.
  kA   = fraction of the cluster A/B provisions (12 time limits + 3 amounts) that appear in the stream
  kdep = fraction of the 4 'gross' thresholds (cluster C dependents) that appear in the stream; all 8 'net' thresholds always appear
Disciplines (method:lam:kA:kdep)
  none     : plain fine-tune on the stream
  unscoped : KL to the launch model on every launch fact
  ss       : KL on launch facts not in the stream (controls + unlisted changed facts)
  dep      : like ss, but unlisted changed facts (siblings in one amending instrument, gross thresholds) are also released
Evaluation is forced choice by sequence log-probability (values are multi-token and often share a first token):
  authorized value (new for changed facts, true for controls) vs competitor (old value / a distractor number).
Metrics: listed / unlisted = changed facts in / not in the stream answered with the NEW value; ripple_dep = unlisted gross thresholds;
  keep_control = control provisions still answered correctly; currency_all = all changed facts.

Run (8 GB GPU is not enough for 7B; use a rented GPU):
  python lm_reallaw_gpu.py --model Qwen/Qwen2.5-7B --seeds 1 2 3 --out reallaw_qwen7b.json
"""
import argparse, json, random, time, os
import torch, torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM
import lm_supersession_gpu as G

WORDS = "one two three four five six seven eight ten twelve fourteen".split()

def prefix(f): return f"{f['act_name']}, section {f['section']} ({f['title']}): {f['ctx']}"

def distractor(f, rng):
    v = f["old"].strip()
    if v.isdigit():
        return " " + str(max(1, int(v) + rng.choice([-1, 1, 2, 3])) if int(v) > 1 else int(v) + 1)
    return " " + rng.choice([w for w in WORDS if w != v])

def enc(tok, prompts, answers, dev, lmax=None):
    P = [tok(p, add_special_tokens=False)["input_ids"] for p in prompts]; A = [tok(a, add_special_tokens=False)["input_ids"] for a in answers]
    L = max(len(p) + len(a) for p, a in zip(P, A)); la = lmax or max(len(a) for a in A)
    X = torch.full((len(P), L), tok.pad_token_id); M = torch.zeros(len(P), L, dtype=torch.long)
    AI = torch.zeros(len(P), la, dtype=torch.long); AM = torch.zeros(len(P), la); PL = torch.zeros(len(P), dtype=torch.long)
    for i, (p, a) in enumerate(zip(P, A)):
        a = a[:la]; ids = p + a; X[i, :len(ids)] = torch.tensor(ids); M[i, :len(ids)] = 1; AI[i, :len(a)] = torch.tensor(a); AM[i, :len(a)] = 1; PL[i] = len(p)
    return [t.to(dev) for t in (X, M, AI, AM, PL)]

def ans_logits(model, b):
    X, M, AI, AM, PL = b
    lg = model(input_ids=X, attention_mask=M).logits
    pos = (PL[:, None] - 1 + torch.arange(AI.shape[1], device=X.device)[None, :]).clamp(max=X.shape[1] - 1)
    return lg[torch.arange(X.shape[0], device=X.device)[:, None], pos].float()      # B x la x V

def seq_lp(model, b):
    lp = F.log_softmax(ans_logits(model, b), -1).gather(-1, b[2][..., None]).squeeze(-1)
    return (lp * b[3]).sum(-1)

def sl(b, idx): return [t[idx] for t in b]

@torch.no_grad()
def pref(model, tok, facts, auth, alt, dev, bs=24):
    model.eval(); out = []
    for i in range(0, len(facts), bs):
        fs = facts[i:i+bs]; pr = [prefix(f) for f in fs]
        la = max(max(len(tok(a[j], add_special_tokens=False)["input_ids"]) for j in range(len(fs))) for a in (auth[i:i+bs], alt[i:i+bs]))
        ba = enc(tok, pr, auth[i:i+bs], dev, la); bb = enc(tok, pr, alt[i:i+bs], dev, la)
        out += (seq_lp(model, ba) > seq_lp(model, bb)).tolist()
    return out

def train_stage(base, tok, batches_fn, epochs, lr, args, dev, anchors=None, teacher=None, lam=0.0, gen=None):
    model = G.lora_wrap(base, args); opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=lr, weight_decay=0.0)
    for ep in range(epochs):
        model.train()
        for b in batches_fn():
            with torch.autocast(device_type=dev.type, dtype=torch.bfloat16, enabled=dev.type == "cuda"):
                lgb = ans_logits(model, b)
            lp = F.log_softmax(lgb, -1).gather(-1, b[2][..., None]).squeeze(-1)
            loss = -(lp * b[3]).sum() / b[3].sum()
            if lam > 0 and anchors is not None and len(anchors[1]):
                ab, ai = anchors; sel = torch.randint(len(ai), (args.bs,), generator=gen).to(dev); idx = ai[sel]
                with torch.autocast(device_type=dev.type, dtype=torch.bfloat16, enabled=dev.type == "cuda"):
                    sg = ans_logits(model, sl(ab, idx))
                s = F.log_softmax(sg, -1); t = teacher[idx].float(); m = ab[3][idx]
                kl = ((t.exp() * (t - s)).sum(-1) * m).sum() / m.sum()
                loss = loss + lam * kl
            opt.zero_grad(); loss.backward(); opt.step()
    return model

def launch(args, seed, bank, cache, dev):
    if seed in cache: return cache[seed]
    torch.manual_seed(seed); gen = torch.Generator().manual_seed(seed)
    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16 if dev.type == "cuda" else torch.float32).to(dev)
    pr = [prefix(f) for f in bank]; ans = [f["old"] for f in bank]
    full = enc(tok, pr, ans, dev); la = full[2].shape[1]
    def batches():
        perm = torch.randperm(len(bank), generator=gen).to(dev)
        for i in range(0, len(bank), args.bs): yield sl(full, perm[i:i+args.bs])
    model = G.lora_wrap(base, args); opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.launch_lr, weight_decay=0.0)
    acc = 0.0
    for ep in range(args.launch_epochs):
        model.train()
        for b in batches():
            with torch.autocast(device_type=dev.type, dtype=torch.bfloat16, enabled=dev.type == "cuda"):
                lgb = ans_logits(model, b)
            lp = F.log_softmax(lgb, -1).gather(-1, b[2][..., None]).squeeze(-1); loss = -(lp * b[3]).sum() / b[3].sum()
            opt.zero_grad(); loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            hit = tot = 0
            for i in range(0, len(bank), 24):
                b = sl(full, torch.arange(i, min(i + 24, len(bank))).to(dev)); pred = ans_logits(model, b).argmax(-1)
                hit += ((pred == b[2]).float() * b[3]).sum().item(); tot += b[3].sum().item()
            acc = hit / tot
        if acc >= 0.995: break
    merged = model.merge_and_unload(); merged.eval()
    with torch.no_grad():
        teacher = torch.cat([F.log_softmax(ans_logits(merged, sl(full, torch.arange(i, min(i + 24, len(bank))).to(dev))), -1).to(torch.bfloat16) for i in range(0, len(bank), 24)])
    cache[seed] = dict(tok=tok, model=merged, full=full, teacher=teacher, acc=acc, ep=ep + 1, la=la)
    return cache[seed]

def one(args, seed, bank, method, lam, kA, kdep, cache, dev):
    c = launch(args, seed, bank, cache, dev); tok = c["tok"]
    rng = random.Random(seed * 1000 + int(kA * 100) + int(kdep * 10)); gen = torch.Generator().manual_seed(seed * 7 + int(kA * 100))
    n = len(bank); ch = [i for i, f in enumerate(bank) if f["kind"] == "changed"]; ctl = [i for i, f in enumerate(bank) if f["kind"] == "control"]
    AB = [i for i in ch if bank[i]["cluster"] in "AB"]; Cb = [i for i in ch if bank[i]["cluster"] == "C" and bank[i]["role"] == "base"]
    Cd = [i for i in ch if bank[i]["cluster"] == "C" and bank[i]["role"] == "dependent"]
    # same random draw across disciplines for a given (seed, kA, kdep): independent of method
    lrng = random.Random(seed * 99 + int(kA * 100) + int(kdep * 10))
    listed = set(Cb) | set(lrng.sample(AB, max(1, int(round(kA * len(AB)))))) | set(lrng.sample(Cd, int(round(kdep * len(Cd)))))
    s_idx = sorted(listed)
    stream = enc(tok, [prefix(bank[i]) for i in s_idx], [bank[i]["new"] for i in s_idx], dev)
    unlisted = [i for i in ch if i not in listed]
    if method == "unscoped": anch = list(range(n))
    elif method == "ss": anch = [i for i in range(n) if i not in listed]
    elif method == "dep": anch = [i for i in range(n) if i not in listed and i not in set(unlisted)]
    else: anch = []
    ai = torch.tensor(anch, dtype=torch.long, device=dev)
    def batches():
        perm = torch.randperm(len(s_idx), generator=gen).to(dev)
        for i in range(0, len(s_idx), args.bs): yield sl(stream, perm[i:i+args.bs])
    model = train_stage(c["model"], tok, batches, args.update_epochs, args.update_lr, args, dev,
                        anchors=(c["full"], ai) if anch else None, teacher=c["teacher"], lam=lam if method != "none" else 0.0, gen=gen)
    drng = random.Random(seed * 5)
    dist = {i: distractor(bank[i], drng) for i in ctl}
    now_ok = pref(model, tok, bank, [bank[i]["new"] if bank[i]["kind"] == "changed" else bank[i]["old"] for i in range(n)],
                  [bank[i]["old"] if bank[i]["kind"] == "changed" else dist[i] for i in range(n)], dev)
    f = lambda ids: (sum(now_ok[i] for i in ids) / len(ids)) if ids else float("nan")
    row = dict(seed=seed, method=method, lam=lam, kA=kA, kdep=kdep, n_stream=len(s_idx), n_anchor=len(anch),
               listed=f([i for i in ch if i in listed]), unlisted=f(unlisted), unlisted_AB=f([i for i in unlisted if i in AB]),
               ripple_dep=f([i for i in Cd if i not in listed]), keep_control=f(ctl), currency_all=f(ch), launch_acc=c["acc"], launch_epochs=c["ep"])
    c["model"] = model.unload()
    return row

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B"); ap.add_argument("--bank", default="real_fact_bank.json")
    ap.add_argument("--lora-r", type=int, default=16); ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--launch-epochs", type=int, default=100); ap.add_argument("--launch-lr", type=float, default=2e-4)
    ap.add_argument("--update-epochs", type=int, default=20); ap.add_argument("--update-lr", type=float, default=1e-4)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1])
    ap.add_argument("--configs", nargs="+", default=["none:0:0.5:0", "unscoped:1:0.5:0", "unscoped:10:0.5:0", "ss:10:0.5:0", "dep:10:0.5:0", "ss:10:1:1"])
    ap.add_argument("--out", default="reallaw.json")
    args = ap.parse_args()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu"); print("device:", dev, flush=True)
    bank = json.load(open(args.bank)); print("facts:", len(bank), flush=True)
    rows = json.load(open(args.out)) if os.path.exists(args.out) else []
    done = {(r["seed"], r["method"], r["lam"], r["kA"], r["kdep"]) for r in rows}
    cfgs = [(m, float(l), float(a), float(d)) for m, l, a, d in (x.split(":") for x in args.configs)]
    cache = {}; t0 = time.time()
    for s in args.seeds:
        for m, l, a, d in cfgs:
            if (s, m, l, a, d) in done: continue
            r = one(args, s, bank, m, l, a, d, cache, dev); rows.append(r); json.dump(rows, open(args.out, "w"), indent=1)
            print(f"[{time.time()-t0:5.0f}s] seed={s} {m:8s} lam={l:<4} kA={a:<3} kdep={d:<3} listed={r['listed']:.2f} unlisted={r['unlisted']:.2f} "
                  f"AB-unl={r['unlisted_AB']:.2f} ripple_dep={r['ripple_dep']:.2f} keepCtl={r['keep_control']:.2f} cur={r['currency_all']:.2f} launch={r['launch_acc']:.3f}", flush=True)
