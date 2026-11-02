"""GPU / LoRA version of the supersession experiment (Propositions 1 and 2).

Same design as lm_supersession.py, for larger pretrained models (e.g. Qwen2.5-1.5B, Llama-3.2-3B):
  1. LoRA-train the model on N launch facts (rule code -> categorical value), merge -> "launch model".
  2. Update with a fresh LoRA on a stream that revises a share rho of the facts (superseded) and adds new ones.
     Facts not in the stream are still valid and should be retained.
  3. KL constraint (weight lam) to the launch model on anchor prompts:
       unscoped: anchors = all launch facts; scoped(q): anchors = facts the record lists as valid
       (record is correct for each fact with probability q).
Metrics: continuity (valid kept), currency (currently authorized value), acquisition (new facts).

Run (example, 8 GB GPU):
  python lm_supersession_gpu.py --model Qwen/Qwen2.5-1.5B --seeds 1 2 3 --out qwen15.json
FIRST CHECK on the GPU: the log prints launch=<accuracy>(<epochs>). The experiment is only meaningful if the launch
accuracy is close to 1.0 (every fact learned). If it is lower, raise capacity/effort, e.g.
  --lora-r 64 --launch-lr 5e-4 --launch-epochs 150
(on a 70M test model LoRA reached only 0.32 in 60 epochs, so this was not verified for 1.5B+ models).
Quick check without a GPU (only tests that the code runs, not that learning works):
  python lm_supersession_gpu.py --model EleutherAI/pythia-70m --n-launch 40 --n-new 10 --seeds 1 \
      --rhos 0.5 --lams 0 10 --launch-epochs 3 --update-epochs 2 --out smoke.json
"""
import argparse, json, random, time, os
import numpy as np, torch, torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model

WORDS = ("red blue green yellow orange purple black white brown pink gray silver gold copper iron stone river mountain forest "
         "ocean desert island valley harbor garden bridge tower castle market school office hospital library museum station "
         "airport village city farm road path gate wall window door table chair lamp clock mirror basket bottle candle ribbon "
         "button needle thread paper pencil letter stamp coin ticket basket engine wheel anchor sail compass map flag drum "
         "violin piano flute bell horn trumpet apple orange grape lemon cherry peach plum melon bread butter cheese honey sugar "
         "salt pepper coffee tea milk water wine soup rice corn wheat bean carrot onion potato tomato").split()

def single_token_values(tok, n_min=40):
    nums = [str(v) for v in range(10, 100) if len(tok(" " + str(v), add_special_tokens=False)["input_ids"]) == 1]
    if len(nums) >= n_min: return nums
    words = sorted({w for w in WORDS if len(tok(" " + w, add_special_tokens=False)["input_ids"]) == 1})
    if len(words) < n_min: raise RuntimeError("too few single-token values for this tokenizer")
    return words

def tid(tok, v): return tok(" " + v, add_special_tokens=False)["input_ids"][0]

def enc(tok, keys, vals, dev):
    ids = [tok(k, add_special_tokens=False)["input_ids"] for k in keys]
    if tok.bos_token_id is not None and getattr(tok, "add_bos_token", False): ids = [[tok.bos_token_id] + i for i in ids]
    L = max(len(i) for i in ids); pad = tok.pad_token_id
    X = torch.full((len(ids), L), pad); M = torch.zeros(len(ids), L, dtype=torch.long); pos = []
    for r, i in enumerate(ids):
        X[r, :len(i)] = torch.tensor(i); M[r, :len(i)] = 1; pos.append(len(i) - 1)
    return X.to(dev), M.to(dev), torch.tensor(pos).to(dev), torch.tensor([tid(tok, v) for v in vals]).to(dev)

def logits_at(model, X, M, pos):
    out = model(input_ids=X, attention_mask=M).logits
    return out[torch.arange(len(X), device=X.device), pos].float()

@torch.no_grad()
def predict(model, data, bs=64):
    X, M, pos, _ = data; model.eval(); res = []
    for i in range(0, len(X), bs):
        res.append(logits_at(model, X[i:i+bs], M[i:i+bs], pos[i:i+bs]).argmax(-1))
    return torch.cat(res)

def lora_wrap(base, args):
    cfg = LoraConfig(r=args.lora_r, lora_alpha=2 * args.lora_r, lora_dropout=0.0, target_modules="all-linear", task_type="CAUSAL_LM")
    return get_peft_model(base, cfg)

def train_launch(base, data, args, gen, dev):
    model = lora_wrap(base, args); X, M, pos, tgt = data
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.launch_lr, weight_decay=0.0)
    acc = 0.0
    for ep in range(args.launch_epochs):
        model.train(); perm = torch.randperm(len(X), generator=gen).to(dev)
        for i in range(0, len(X), args.bs):
            b = perm[i:i+args.bs]
            with torch.autocast(device_type=dev.type, dtype=torch.bfloat16, enabled=dev.type == "cuda"):
                lg = logits_at(model, X[b], M[b], pos[b])
            loss = F.cross_entropy(lg, tgt[b]); opt.zero_grad(); loss.backward(); opt.step()
        acc = (predict(model, data) == tgt).float().mean().item()
        if acc >= 0.995: break
    merged = model.merge_and_unload()
    return merged, acc, ep + 1

def run_update(launch_model, launch, teacher_lp, stream, anchors, lam, args, gen, dev):
    model = lora_wrap(launch_model, args)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.update_lr, weight_decay=0.0)
    SX, SM, Spos, Stgt = stream; LX, LM, Lpos, _ = launch; n = len(SX); na = len(anchors); bs = args.bs
    for ep in range(args.update_epochs):
        model.train(); perm = torch.randperm(n, generator=gen).to(dev)
        for i in range(0, n, bs):
            b = perm[i:i+bs]
            with torch.autocast(device_type=dev.type, dtype=torch.bfloat16, enabled=dev.type == "cuda"):
                lg = logits_at(model, SX[b], SM[b], Spos[b])
            loss = F.cross_entropy(lg, Stgt[b])
            if lam > 0 and na > 0:
                a = anchors[torch.randint(na, (bs,), generator=gen).to(dev)]
                with torch.autocast(device_type=dev.type, dtype=torch.bfloat16, enabled=dev.type == "cuda"):
                    la = F.log_softmax(logits_at(model, LX[a], LM[a], Lpos[a]), -1)
                kl = (teacher_lp[a].exp() * (teacher_lp[a] - la)).sum(-1).mean()
                loss = loss + lam * kl
            opt.zero_grad(); loss.backward(); opt.step()
    return model

def one_config(args, seed, rho, lam, scope_q, cache, dev):
    if seed not in cache:
        rng = random.Random(seed); torch.manual_seed(seed); gen = torch.Generator().manual_seed(seed)
        tok = AutoTokenizer.from_pretrained(args.model)
        if tok.pad_token is None: tok.pad_token = tok.eos_token
        vals = single_token_values(tok)
        codes = rng.sample(range(100, 1000), args.n_launch + args.n_new)
        keys = [f"Under rule R-{c}, the processing category is" for c in codes]
        v0 = [rng.choice(vals) for _ in keys]
        lk, lv = keys[:args.n_launch], v0[:args.n_launch]; nk, nv = keys[args.n_launch:], v0[args.n_launch:]
        launch = enc(tok, lk, lv, dev)
        dtype = torch.bfloat16 if dev.type == "cuda" else torch.float32
        base = AutoModelForCausalLM.from_pretrained(args.model, dtype=dtype).to(dev)
        merged, acc, ep = train_launch(base, launch, args, gen, dev)
        merged.eval()
        with torch.no_grad():
            teacher_lp = torch.cat([F.log_softmax(logits_at(merged, launch[0][i:i+64], launch[1][i:i+64], launch[2][i:i+64]), -1)
                                    for i in range(0, args.n_launch, 64)])
        cache[seed] = dict(tok=tok, vals=vals, lk=lk, lv=lv, nk=nk, nv=nv, launch=launch, model=merged, teacher_lp=teacher_lp, acc=acc, ep=ep)
    c = cache[seed]; tok = c["tok"]; N = args.n_launch
    rng = random.Random(seed * 1000 + int(rho * 100)); gen = torch.Generator().manual_seed(seed * 7 + int(rho * 100))
    idx = list(range(N)); rng.shuffle(idx); ns = int(round(rho * N)); sup = set(idx[:ns]); sup_idx = sorted(sup)
    val_mask = torch.ones(N, dtype=torch.bool); val_mask[sup_idx] = False
    v1 = {i: rng.choice([v for v in c["vals"] if v != c["lv"][i]]) for i in sup_idx}
    stream = enc(tok, [c["lk"][i] for i in sup_idx] + c["nk"], [v1[i] for i in sup_idx] + c["nv"], dev)
    if scope_q is None: anchors = torch.arange(N, device=dev)
    else:
        listed = [i for i in range(N) if ((i not in sup) if rng.random() < scope_q else (i in sup))]
        anchors = torch.tensor(listed, dtype=torch.long, device=dev)
    model = run_update(c["model"], c["launch"], c["teacher_lp"], stream, anchors, lam, args, gen, dev)
    pred = predict(model, c["launch"])
    v0t = torch.tensor([tid(tok, v) for v in c["lv"]], device=dev); v1t = v0t.clone()
    for i in sup_idx: v1t[i] = tid(tok, v1[i])
    vm = val_mask.to(dev)
    cont = (pred[vm] == v0t[vm]).float().mean().item() if vm.any() else float("nan")
    sup_new = (pred[~vm] == v1t[~vm]).float().mean().item() if (~vm).any() else float("nan")
    sup_old = (pred[~vm] == v0t[~vm]).float().mean().item() if (~vm).any() else float("nan")
    nd = enc(tok, c["nk"], c["nv"], dev); acq = (predict(model, nd) == nd[3]).float().mean().item()
    row = dict(seed=seed, rho=rho, lam=lam, q=scope_q, n_sup=ns, n_anchor=int(len(anchors)), continuity=cont,
               currency=(pred == v1t).float().mean().item(), superseded_new=sup_new, superseded_old=sup_old,
               acquisition=acq, launch_acc=c["acc"], launch_epochs=c["ep"])
    c["model"] = model.unload()          # remove the update adapter; launch weights unchanged
    return row

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    ap.add_argument("--n-launch", type=int, default=200); ap.add_argument("--n-new", type=int, default=50)
    ap.add_argument("--lora-r", type=int, default=16); ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--launch-epochs", type=int, default=60); ap.add_argument("--launch-lr", type=float, default=2e-4)
    ap.add_argument("--update-epochs", type=int, default=25); ap.add_argument("--update-lr", type=float, default=1e-4)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--rhos", type=float, nargs="+", default=[0.1, 0.3, 0.5, 0.7, 0.9])
    ap.add_argument("--lams", type=float, nargs="+", default=[0, 1, 10])
    ap.add_argument("--qs", type=float, nargs="*", default=[0.5, 0.7, 0.9, 1.0]); ap.add_argument("--scoped-lam", type=float, default=10)
    ap.add_argument("--scoped-rhos", type=float, nargs="+", default=[0.3, 0.7]); ap.add_argument("--skip-unscoped", action="store_true")
    ap.add_argument("--out", default="results_gpu.json")
    args = ap.parse_args()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu"); print("device:", dev, flush=True)
    rows = json.load(open(args.out)) if os.path.exists(args.out) else []
    done = {(r["seed"], r["rho"], r["lam"], r["q"]) for r in rows}
    jobs = [] if args.skip_unscoped else [(s, r, l, None) for s in args.seeds for r in args.rhos for l in args.lams]
    jobs += [(s, r, args.scoped_lam, q) for s in args.seeds for r in args.scoped_rhos for q in args.qs]
    cache = {}; t0 = time.time()
    for s, r, l, q in jobs:
        if (s, r, l, q) in done: continue
        row = one_config(args, s, r, l, q, cache, dev); rows.append(row); json.dump(rows, open(args.out, "w"), indent=1)
        print(f"[{time.time()-t0:5.0f}s] seed={s} rho={r} lam={l} q={q} cont={row['continuity']:.2f} cur={row['currency']:.2f} "
              f"acq={row['acquisition']:.2f} launch={row['launch_acc']:.2f}({row['launch_epochs']}ep)", flush=True)
