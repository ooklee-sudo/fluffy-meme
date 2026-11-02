"""Follow-up experiment for Propositions 1 and 2 (conceptual paper).

A pretrained causal LM learns N launch facts (rule code -> fee value). An update stream then
revises a share rho of them (superseded) and adds new facts. Facts not mentioned in the stream
are still valid and should be retained. A KL constraint to the launch model on anchor prompts
trades continuity against currency:
  unscoped: anchors = all launch facts (valid + superseded)
  scoped(q): anchors = facts the record lists as valid; the record misclassifies each fact w.p. 1-q
Metrics (answer-token accuracy):
  continuity = valid items answered with the launch value
  currency   = all launch items answered with the currently authorized value
  acquisition= new items answered correctly
"""
import argparse, json, random, time, os
import numpy as np, torch, torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM

def make_items(tok, n_launch, n_new, rng):
    vals = [v for v in range(10, 100) if len(tok(" " + str(v))["input_ids"]) == 1]
    codes = rng.sample(range(100, 1000), n_launch + n_new)
    keys = [f"Under rule R-{c}, the processing fee is" for c in codes]
    v0 = [rng.choice(vals) for _ in keys]
    return keys, v0, vals

def enc(tok, keys, vals):
    ids = [tok(k)["input_ids"] for k in keys]
    L = max(len(i) for i in ids)
    X = torch.full((len(ids), L), tok.pad_token_id or 0); M = torch.zeros(len(ids), L, dtype=torch.long)
    pos = []
    for r, i in enumerate(ids):
        X[r, :len(i)] = torch.tensor(i); M[r, :len(i)] = 1; pos.append(len(i) - 1)
    tgt = torch.tensor([tok(" " + str(v))["input_ids"][0] for v in vals])
    return X, M, torch.tensor(pos), tgt

def logits_at(model, X, M, pos):
    out = model(input_ids=X, attention_mask=M).logits
    return out[torch.arange(len(X)), pos]

@torch.no_grad()
def predict(model, data, bs=64):
    X, M, pos, tgt = data; model.eval(); res = []
    for i in range(0, len(X), bs):
        res.append(logits_at(model, X[i:i+bs], M[i:i+bs], pos[i:i+bs]).argmax(-1))
    return torch.cat(res)

def train_launch(model, data, epochs, lr, bs, gen, tok):
    X, M, pos, tgt = data; opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.0)
    for ep in range(epochs):
        model.train(); perm = torch.randperm(len(X), generator=gen)
        for i in range(0, len(X), bs):
            b = perm[i:i+bs]; lg = logits_at(model, X[b], M[b], pos[b])
            loss = F.cross_entropy(lg, tgt[b]); opt.zero_grad(); loss.backward(); opt.step()
        acc = (predict(model, data) == tgt).float().mean().item()
        if acc >= 0.995: break
    return acc, ep + 1

def run_update(base_state, model_name, launch, teacher_lp, stream, anchors, lam, epochs, lr, bs, gen):
    model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.float32); model.load_state_dict(base_state)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.0)
    SX, SM, Spos, Stgt = stream; LX, LM, Lpos, _ = launch
    n = len(SX); na = len(anchors)
    for ep in range(epochs):
        model.train(); perm = torch.randperm(n, generator=gen)
        for i in range(0, n, bs):
            b = perm[i:i+bs]; lg = logits_at(model, SX[b], SM[b], Spos[b])
            loss = F.cross_entropy(lg, Stgt[b])
            if lam > 0 and na > 0:
                a = anchors[torch.randint(na, (bs,), generator=gen)]
                la = F.log_softmax(logits_at(model, LX[a], LM[a], Lpos[a]), -1)
                kl = (teacher_lp[a].exp() * (teacher_lp[a] - la)).sum(-1).mean()
                loss = loss + lam * kl
            opt.zero_grad(); loss.backward(); opt.step()
    return model

def one_config(args, seed, rho, lam, scope_q, cache):
    key = seed
    if key not in cache:
        rng = random.Random(seed); torch.manual_seed(seed); gen = torch.Generator().manual_seed(seed)
        tok = AutoTokenizer.from_pretrained(args.model)
        keys, v0, vals = make_items(tok, args.n_launch, args.n_new, rng)
        launch_keys, launch_v0 = keys[:args.n_launch], v0[:args.n_launch]
        new_keys, new_v = keys[args.n_launch:], v0[args.n_launch:]
        launch = enc(tok, launch_keys, launch_v0)
        model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.float32)
        acc, ep = train_launch(model, launch, args.launch_epochs, args.launch_lr, args.bs, gen, tok)
        base_state = {k: v.clone() for k, v in model.state_dict().items()}
        with torch.no_grad():
            model.eval(); tl = []
            for i in range(0, args.n_launch, 64):
                tl.append(F.log_softmax(logits_at(model, launch[0][i:i+64], launch[1][i:i+64], launch[2][i:i+64]), -1))
            teacher_lp = torch.cat(tl)
        cache[key] = dict(tok=tok, vals=vals, launch_keys=launch_keys, launch_v0=launch_v0, new_keys=new_keys, new_v=new_v,
                          launch=launch, base_state=base_state, teacher_lp=teacher_lp, launch_acc=acc, launch_ep=ep)
    c = cache[key]; tok = c["tok"]
    rng = random.Random(seed * 1000 + int(rho * 100)); gen = torch.Generator().manual_seed(seed * 7 + int(rho * 100))
    N = args.n_launch; idx = list(range(N)); rng.shuffle(idx)
    ns = int(round(rho * N)); sup = set(idx[:ns]); sup_idx = sorted(sup); val_idx = sorted(set(idx[ns:]))
    v1 = {}
    for i in sup_idx:
        v1[i] = rng.choice([v for v in c["vals"] if v != c["launch_v0"][i]])
    s_keys = [c["launch_keys"][i] for i in sup_idx] + c["new_keys"]
    s_vals = [v1[i] for i in sup_idx] + c["new_v"]
    stream = enc(tok, s_keys, s_vals)
    # anchors
    if scope_q is None: anchors = torch.arange(N)
    else:
        rec_valid = []
        for i in range(N):
            correct = rng.random() < scope_q
            is_valid = i not in sup
            listed_valid = is_valid if correct else (not is_valid)
            if listed_valid: rec_valid.append(i)
        anchors = torch.tensor(rec_valid, dtype=torch.long)
    model = run_update(c["base_state"], args.model, c["launch"], c["teacher_lp"], stream, anchors, lam, args.update_epochs, args.update_lr, args.bs, gen)
    pred = predict(model, c["launch"]); LX = c["launch"]
    v0t = torch.tensor([tok(" " + str(v))["input_ids"][0] for v in c["launch_v0"]])
    v1t = v0t.clone()
    for i in sup_idx: v1t[i] = tok(" " + str(v1[i]))["input_ids"][0]
    cur_target = v1t
    valid_mask = torch.zeros(N, dtype=torch.bool); valid_mask[val_idx] = True
    cont = (pred[valid_mask] == v0t[valid_mask]).float().mean().item() if valid_mask.any() else float("nan")
    currency = (pred == cur_target).float().mean().item()
    sup_new = (pred[~valid_mask] == v1t[~valid_mask]).float().mean().item() if (~valid_mask).any() else float("nan")
    sup_old = (pred[~valid_mask] == v0t[~valid_mask]).float().mean().item() if (~valid_mask).any() else float("nan")
    nd = enc(tok, c["new_keys"], c["new_v"]); acq = (predict(model, nd) == nd[3]).float().mean().item()
    return dict(seed=seed, rho=rho, lam=lam, q=scope_q, n_sup=ns, n_anchor=int(len(anchors)), continuity=cont, currency=currency,
                superseded_new=sup_new, superseded_old=sup_old, acquisition=acq, launch_acc=c["launch_acc"], launch_epochs=c["launch_ep"])

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="EleutherAI/pythia-160m")
    ap.add_argument("--n-launch", type=int, default=200); ap.add_argument("--n-new", type=int, default=50)
    ap.add_argument("--launch-epochs", type=int, default=40); ap.add_argument("--launch-lr", type=float, default=3e-4)
    ap.add_argument("--update-epochs", type=int, default=10); ap.add_argument("--update-lr", type=float, default=1e-4)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--rhos", type=float, nargs="+", default=[0.1, 0.3, 0.5, 0.7, 0.9])
    ap.add_argument("--lams", type=float, nargs="+", default=[0, 0.3, 1, 3, 10])
    ap.add_argument("--scoped-lam", type=float, default=10); ap.add_argument("--qs", type=float, nargs="*", default=[])
    ap.add_argument("--scoped-rhos", type=float, nargs="+", default=[0.3, 0.5, 0.7])
    ap.add_argument("--skip-unscoped", action="store_true"); ap.add_argument("--threads", type=int, default=4); ap.add_argument("--out", default="results.json")
    args = ap.parse_args(); torch.set_num_threads(args.threads)
    rows = json.load(open(args.out)) if os.path.exists(args.out) else []
    done = {(r["seed"], r["rho"], r["lam"], r["q"]) for r in rows}
    jobs = [] if args.skip_unscoped else [(s, r, l, None) for s in args.seeds for r in args.rhos for l in args.lams]
    jobs += [(s, r, args.scoped_lam, q) for s in args.seeds for r in args.scoped_rhos for q in args.qs]
    cache = {}; t0 = time.time()
    for s, r, l, q in jobs:
        if (s, r, l, q) in done: continue
        row = one_config(args, s, r, l, q, cache); rows.append(row)
        json.dump(rows, open(args.out, "w"), indent=1)
        print(f"[{time.time()-t0:5.0f}s] seed={s} rho={r} lam={l} q={q} cont={row['continuity']:.2f} cur={row['currency']:.2f} acq={row['acquisition']:.2f} launch={row['launch_acc']:.2f}({row['launch_epochs']}ep)", flush=True)
