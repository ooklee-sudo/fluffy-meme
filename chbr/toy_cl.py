"""Toy continual-learning unit test for CHBR-D-26-02301 (re-implementation).

Two synthetic word-level streams from template grammars:
  Stream A ("insurance English")  = launch domain
  Stream B ("statutory English")  = later institutional revision
Train on A (10 epochs), then update on B (8 epochs) under different regimes.
Metric: next-token accuracy excluding pad, on held-out test sentences.

Cells: naive | replay | replay+proximal KL | replay+dual KL | replay+launch-KL sweep.
NOTE: in a single A->B update the "previous iterate" and the "launch checkpoint"
are the same network, so proximal KL (b1) and launch KL (b2) are algebraically
the same penalty with weight b1 (+ b2). Both teachers are kept separate in code
so a multi-update run (A->B->C) could distinguish them.
"""
import argparse, json, random, time
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F

# ----------------------------------------------------------------- data
SHARED_NOUN = ["claim", "notice", "premium", "benefit", "application", "payment", "record", "request"]
A_PARTY = ["policyholder", "insured", "claimant", "beneficiary", "insurer", "agent"]
B_PARTY = ["applicant", "agency", "licensee", "authority", "tenant", "employer"]
A_VERB = ["file", "submit", "renew", "cancel", "amend", "dispute", "withdraw", "confirm"]
B_VERB = ["submit", "provide", "retain", "disclose", "certify", "remit", "register", "report"]
A_EVENT = ["the loss", "the accident", "the renewal date", "the notice", "the diagnosis", "the claim decision"]
B_EVENT = ["the filing", "the hearing", "the effective date", "the order", "the inspection", "the assessment"]
A_ADJ = ["covered", "eligible", "excluded", "valid", "pending", "approved"]
B_ADJ = ["applicable", "prescribed", "lawful", "material", "written", "binding"]
NUMS = [str(n) for n in (7, 10, 14, 15, 21, 30, 45, 60, 90)]
SECS = [str(n) for n in (3, 5, 8, 12, 17, 21, 34)]
A_TEMPL = [
    "the {P} may {V} the {N} within {D} days of {E} .",
    "a {J} {N} must be {V}ed by the {P} before {E} .",
    "if the {N} is {J} the {P} shall {V} the {N} within {D} days .",
    "the {P} is not required to {V} a {J} {N} after {E} .",
    "coverage for the {N} ends {D} days after {E} unless the {P} will {V} it .",
]
B_TEMPL = [
    "pursuant to section {S} the {P} shall {V} the {N} not later than {D} days after {E} .",
    "the {P} must {V} each {J} {N} in accordance with section {S} .",
    "no {P} may {V} a {N} unless it is {J} under section {S} .",
    "within {D} days of {E} the {P} shall {V} the {J} {N} .",
    "a {N} that is not {J} is void and the {P} shall {V} it within {D} days .",
]

def gen_sentence(rng, stream):
    if stream == "A":
        t = rng.choice(A_TEMPL); P, V, E, J = rng.choice(A_PARTY), rng.choice(A_VERB), rng.choice(A_EVENT), rng.choice(A_ADJ)
    else:
        t = rng.choice(B_TEMPL); P, V, E, J = rng.choice(B_PARTY), rng.choice(B_VERB), rng.choice(B_EVENT), rng.choice(B_ADJ)
    N = rng.choice(SHARED_NOUN)
    s = t.format(P=P, V=V, N=N, E=E, J=J, D=rng.choice(NUMS), S=rng.choice(SECS))
    return s.replace("ed ", "ed ").split()

def build_vocab():
    words = set(["<pad>", "<bos>", "<eos>"])
    rng = random.Random(0)
    for st in "AB":
        for _ in range(4000):
            words.update(gen_sentence(rng, st))
    # verbs inflected with 'ed' appear via template; keep deterministic order
    return {w: i for i, w in enumerate(sorted(words))}

MAXLEN = 26
def encode(sents, vocab):
    X = np.zeros((len(sents), MAXLEN), dtype=np.int64)
    for i, s in enumerate(sents):
        ids = [vocab["<bos>"]] + [vocab[w] for w in s] + [vocab["<eos>"]]
        X[i, :len(ids)] = ids
    return torch.from_numpy(X)

def make_split(seed, vocab, n_train=3000, n_val=500, n_test=500):
    out = {}
    for st in "AB":
        rng = random.Random(seed * 100 + (0 if st == "A" else 1))
        seen, uniq = set(), []
        while len(uniq) < n_train + n_val + n_test:   # disjoint splits by exact sentence
            s = gen_sentence(rng, st); k = " ".join(s)
            if k not in seen:
                seen.add(k); uniq.append(s)
            if len(seen) > 40000: break
        # if the grammar saturates, allow reuse across splits only as a last resort
        n_tr = min(n_train, int(len(uniq) * 0.7)); n_v = min(n_val, int(len(uniq) * 0.15))
        tr, va, te = uniq[:n_tr], uniq[n_tr:n_tr + n_v], uniq[n_tr + n_v:]
        out[st] = {k: encode(v, vocab) for k, v in dict(train=tr, val=va, test=te).items()}
    return out

# ---------------------------------------------------------------- model
class Block(nn.Module):
    def __init__(s, d, h, ff):
        super().__init__(); s.ln1 = nn.LayerNorm(d); s.ln2 = nn.LayerNorm(d)
        s.qkv = nn.Linear(d, 3 * d); s.o = nn.Linear(d, d); s.h = h
        s.ff = nn.Sequential(nn.Linear(d, ff), nn.GELU(), nn.Linear(ff, d))
    def forward(s, x):
        B, T, D = x.shape
        q, k, v = s.qkv(s.ln1(x)).view(B, T, 3, s.h, D // s.h).permute(2, 0, 3, 1, 4)
        a = F.scaled_dot_product_attention(q, k, v, is_causal=True).transpose(1, 2).reshape(B, T, D)
        x = x + s.o(a)
        return x + s.ff(s.ln2(x))

class LM(nn.Module):
    def __init__(s, V, d=48, h=4, L=2, ff=96):
        super().__init__()
        s.emb = nn.Embedding(V, d); s.pos = nn.Embedding(MAXLEN, d)
        s.blocks = nn.ModuleList(Block(d, h, ff) for _ in range(L))
        s.ln = nn.LayerNorm(d); s.head = nn.Linear(d, V, bias=False)
    def forward(s, x):
        h = s.emb(x) + s.pos(torch.arange(x.shape[1]))
        for b in s.blocks: h = b(h)
        return s.head(s.ln(h))

@torch.no_grad()
def acc(model, X):
    model.eval(); lg = model(X[:, :-1]); y = X[:, 1:]; m = y != 0
    return ((lg.argmax(-1) == y) & m).sum().item() / m.sum().item()

def kl_term(model, teacher, x, mask):
    with torch.no_grad(): tp = F.log_softmax(teacher(x), -1)
    lp = F.log_softmax(model(x), -1)
    kl = (tp.exp() * (tp - lp)).sum(-1)          # KL(teacher || live)
    return (kl * mask).sum() / mask.sum()

def run_stage(model, batches_fn, epochs, lr, log, tag, data, b1=0., b2=0., t_old=None, t_ref=None):
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    for ep in range(1, epochs + 1):
        model.train()
        for xb in batches_fn():
            x, y = xb[:, :-1], xb[:, 1:]; m = (y != 0).float()
            lg = model(x)
            loss = (F.cross_entropy(lg.reshape(-1, lg.shape[-1]), y.reshape(-1), reduction="none") * m.reshape(-1)).sum() / m.sum()
            if b1 and t_old is not None: loss = loss + b1 * kl_term(model, t_old, x, m)
            if b2 and t_ref is not None: loss = loss + b2 * kl_term(model, t_ref, x, m)
            opt.zero_grad(); loss.backward(); opt.step()
        log.append(dict(stage=tag, epoch=ep, A=acc(model, data["A"]["test"]), B=acc(model, data["B"]["test"])))

def loader(X, bs, rng):
    idx = torch.randperm(len(X), generator=rng)
    for i in range(0, len(X), bs): yield X[idx[i:i + bs]]

def run(seed, cell, data, V, args, launch_state):
    torch.manual_seed(seed); np.random.seed(seed); g = torch.Generator().manual_seed(seed)
    model = LM(V); model.load_state_dict(launch_state)
    t_ref = LM(V); t_ref.load_state_dict(launch_state); t_ref.eval()
    t_old = LM(V); t_old.load_state_dict(launch_state); t_old.eval()   # previous live iterate
    XA, XB = data["A"]["train"], data["B"]["train"]; bs = args.bs
    gam = cell.get("gamma", 0.0)
    nA = int(round(bs * gam / (1 - gam))) if gam else 0     # A sentences added per B batch -> A fraction = gamma
    def batches():
        for xb in loader(XB, bs, g):
            if nA: xb = torch.cat([xb, XA[torch.randint(len(XA), (nA,), generator=g)]])
            yield xb
    log = []
    run_stage(model, batches, args.epochs_b, args.lr, log, "B", data,
              b1=cell.get("b1", 0.), b2=cell.get("b2", 0.), t_old=t_old, t_ref=t_ref)
    return log

CELLS = {
    "naive_sequential": {},
    "replay": dict(gamma=0.65),
    "replay_proximal_kl": dict(gamma=0.65, b1=0.4),
    "replay_dual_kl": dict(gamma=0.65, b1=0.4, b2=0.8),
}
SWEEP = [0.0, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[13, 21, 37])
    ap.add_argument("--epochs-a", type=int, default=10); ap.add_argument("--epochs-b", type=int, default=8)
    ap.add_argument("--lr", type=float, default=3e-3); ap.add_argument("--bs", type=int, default=64)
    ap.add_argument("--out", default="toy_cl_results.json")
    args = ap.parse_args(); torch.set_num_threads(4)
    vocab = build_vocab(); V = len(vocab); t0 = time.time()
    res = dict(config=vars(args), vocab_size=V, n_params=sum(p.numel() for p in LM(V).parameters()), seeds={})
    for seed in args.seeds:
        torch.manual_seed(seed); data = make_split(seed, vocab)
        sizes = {st: {k: len(v) for k, v in d.items()} for st, d in data.items()}
        model = LM(V); logA = []; g = torch.Generator().manual_seed(seed)
        run_stage(model, lambda: loader(data["A"]["train"], args.bs, g), args.epochs_a, args.lr, logA, "A", data)
        launch = {k: v.clone() for k, v in model.state_dict().items()}
        r = dict(sizes=sizes, stageA=logA, A_launch=acc(model, data["A"]["test"]), cells={}, sweep={})
        for name, c in CELLS.items(): r["cells"][name] = run(seed, c, data, V, args, launch)
        for b in SWEEP: r["sweep"][str(b)] = run(seed, dict(gamma=0.65, b2=b), data, V, args, launch)
        res["seeds"][str(seed)] = r
        print(f"seed {seed} done  A_launch={r['A_launch']:.3f}  {time.time()-t0:.0f}s", flush=True)
    json.dump(res, open(args.out, "w"), indent=1)
