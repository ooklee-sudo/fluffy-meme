"""Model-pair experiment for Section 7.1: recovery rates and costs of copy vs. ACT on real LLMs.

Pipeline (one source -> target pair sharing a tokenizer, e.g. Llama 3.2 1B Base -> Instruct):
  1. Train a LoRA adapter on the source model            (source adapter)
  2. Retrain the same adapter on the target model        (upper bound, timed -> C_N)
  3. Naive copy: load the source adapter into the target (R_C)
  4. ACT (Appendix A): closed-form correction of A per module from unlabeled calibration
     prompts, alpha chosen per layer on an 80/20 split, layers corrected sequentially
     from the input side (timed -> C_A)                  (R_A)
  5. Recovery R = (L_none - L_method) / (L_none - L_retrain) on held-out response NLL
     (and optionally on generation exact match).

Output JSON can be fed to the economic model:  python real_options.py --recovery results/act_llama.json

Usage:
  python act_llama.py --source meta-llama/Llama-3.2-1B --target meta-llama/Llama-3.2-1B-Instruct
  python act_llama.py --tiny            # CPU smoke test with random tiny Llama models, no downloads
"""
import argparse
import json
import math
import os
import random
import re
import time

import torch
import torch.nn.functional as F
from peft import LoraConfig, get_peft_model

ALPHAS = [10 ** (e / 2) for e in range(-6, 7)]  # 13 values in [1e-3, 1e3]


class StopForward(Exception):
    pass


# ---------------------------------------------------------------- data
def load_examples(args, tok):
    """Return (train, eval, calib) lists of (prompt_ids, response_ids)."""
    if args.tiny:
        rng = random.Random(0)

        def ex():  # reverse a random token sequence
            p = [rng.randrange(4, args.tiny_vocab) for _ in range(rng.randrange(4, 12))]
            return [1] + p + [2], list(reversed(p)) + [3]
        mk = lambda n: [ex() for _ in range(n)]
        return mk(args.n_train), mk(args.n_eval), [(p, []) for p, _ in mk(args.n_cal)]

    from datasets import load_dataset
    ds = load_dataset(args.dataset, args.dataset_config)
    tr, te = ds["train"].shuffle(seed=args.seed), ds[args.eval_split].shuffle(seed=args.seed)

    def enc(row, with_resp=True):
        p = tok(args.prompt_template.format(**row), add_special_tokens=True)["input_ids"]
        r = tok(" " + row[args.response_field] + tok.eos_token, add_special_tokens=False)["input_ids"]
        return p[: args.max_len // 2], (r[: args.max_len - len(p[: args.max_len // 2])] if with_resp else [])
    train = [enc(tr[i]) for i in range(args.n_train)]
    evals = [enc(te[i]) for i in range(args.n_eval)]
    # calibration = task prompts without answers (A.4), disjoint from training rows
    calib = [enc(tr[args.n_train + i], with_resp=False) for i in range(args.n_cal)]
    return train, evals, calib


def collate(batch, pad_id, device):
    seqs = [p + r for p, r in batch]
    n = max(map(len, seqs))
    ids = torch.full((len(seqs), n), pad_id, dtype=torch.long)
    att = torch.zeros((len(seqs), n), dtype=torch.long)
    lab = torch.full((len(seqs), n), -100, dtype=torch.long)
    for i, (p, r) in enumerate(batch):
        s = p + r
        ids[i, : len(s)] = torch.tensor(s)
        att[i, : len(s)] = 1
        lab[i, len(p): len(s)] = torch.tensor(r) if r else lab[i, len(p): len(s)]
    return ids.to(device), att.to(device), lab.to(device)


def batches(data, bs, shuffle=False, seed=0):
    idx = list(range(len(data)))
    if shuffle:
        random.Random(seed).shuffle(idx)
    for i in range(0, len(idx), bs):
        yield [data[j] for j in idx[i: i + bs]]


# ---------------------------------------------------------------- models
def load_model(name, revision, device, dtype):
    import transformers
    from transformers import AutoModelForCausalLM
    major, minor = (int(x) for x in transformers.__version__.split(".")[:2])
    kw = {"dtype": dtype} if (major, minor) >= (4, 56) else {"torch_dtype": dtype}
    return AutoModelForCausalLM.from_pretrained(name, revision=revision, **kw).to(device)


def tiny_config(arch, vocab):
    import transformers as T
    common = dict(vocab_size=vocab, hidden_size=64, intermediate_size=128, num_hidden_layers=2,
                  num_attention_heads=4, max_position_embeddings=64)
    if arch == "llama":
        return T.LlamaConfig(num_key_value_heads=4, **common)
    if arch == "qwen2":
        return T.Qwen2Config(num_key_value_heads=4, tie_word_embeddings=True, **common)
    if arch == "gpt_neox":
        return T.GPTNeoXConfig(use_parallel_residual=True, **common)
    raise ValueError(arch)


def tiny_pair(args, device):
    """Random tiny source and an 'upgraded' target = source + drift (scenario S1)."""
    from transformers import AutoModelForCausalLM
    torch.manual_seed(0)
    cfg = tiny_config(args.tiny_arch, args.tiny_vocab)
    src = AutoModelForCausalLM.from_config(cfg).to(device)
    # give the source some competence so the task is learnable by a small adapter
    opt = torch.optim.AdamW(src.parameters(), lr=3e-3)
    rng = random.Random(1)
    for _ in range(args.tiny_pretrain):
        seq = torch.tensor([[rng.randrange(4, args.tiny_vocab) for _ in range(24)] for _ in range(32)], device=device)
        loss = src(input_ids=seq, labels=seq).loss
        opt.zero_grad(); loss.backward(); opt.step()
    tgt = AutoModelForCausalLM.from_config(cfg).to(device)
    tgt.load_state_dict(src.state_dict())
    with torch.no_grad():
        for n, p in tgt.named_parameters():
            if p.dim() == 2 and "embed" not in n and "lm_head" not in n:
                p.add_(torch.randn_like(p) * args.tiny_drift * p.std())
    return src, tgt


def auto_target_modules(model):
    """Leaf nn.Linear names inside the decoder layers (q_proj..down_proj, query_key_value..dense_4h_to_h)."""
    names = {n.split(".")[-1] for n, m in model.named_modules()
             if isinstance(m, torch.nn.Linear) and layer_index(n) >= 0}
    return sorted(names)


def add_lora(model, args):
    targets = auto_target_modules(model) if args.target_modules == ["auto"] else args.target_modules
    cfg = LoraConfig(r=args.rank, lora_alpha=args.lora_alpha, lora_dropout=0.0,
                     target_modules=targets, bias="none", task_type="CAUSAL_LM")
    return get_peft_model(model, cfg)


def lora_modules(pm):
    """{name: module} for every LoRA-wrapped linear."""
    return {n: m for n, m in pm.named_modules() if hasattr(m, "lora_A") and "default" in m.lora_A}


@torch.no_grad()
def forward_order(pm, mods, device):
    """Module names sorted by the order in which a forward pass calls them."""
    seen, hs = [], []
    for n, m in mods.items():
        hs.append(m.register_forward_hook(lambda mod, i, o, n=n: seen.append(n) if n not in seen else None))
    try:
        pm(input_ids=torch.ones((1, 4), dtype=torch.long, device=device))
    finally:
        for h in hs:
            h.remove()
    return seen


def layer_index(name):
    m = re.search(r"layers\.(\d+)\.", name)
    return int(m.group(1)) if m else -1


def get_lora_state(pm):
    return {k: v.detach().clone() for k, v in pm.state_dict().items() if "lora_" in k}


def set_lora_state(pm, state):
    missing = pm.load_state_dict(state, strict=False)
    assert not missing.unexpected_keys, missing.unexpected_keys


# ---------------------------------------------------------------- train / eval
def train_lora(pm, data, args, device, pad_id, seed=0):
    torch.manual_seed(seed)
    params = [p for n, p in pm.named_parameters() if "lora_" in n]
    for n, p in pm.named_parameters():
        p.requires_grad_("lora_" in n)
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.0)
    pm.train()
    step, t0 = 0, time.time()
    while step < args.steps:
        for b in batches(data, args.bs, shuffle=True, seed=seed + step):
            ids, att, lab = collate(b, pad_id, device)
            loss = pm(input_ids=ids, attention_mask=att, labels=lab).loss
            opt.zero_grad(); loss.backward(); opt.step()
            step += 1
            if step % max(1, args.steps // 5) == 0:
                print(f"  step {step}/{args.steps} loss {loss.item():.4f}")
            if step >= args.steps:
                break
    pm.eval()
    sync(device)
    return time.time() - t0


@torch.no_grad()
def eval_nll(pm, data, args, device, pad_id):
    pm.eval()
    tot, n = 0.0, 0
    for b in batches(data, args.bs):
        ids, att, lab = collate(b, pad_id, device)
        logits = pm(input_ids=ids, attention_mask=att).logits[:, :-1].float()
        tgt = lab[:, 1:]
        l = F.cross_entropy(logits.reshape(-1, logits.size(-1)), tgt.reshape(-1), ignore_index=-100, reduction="sum")
        tot += l.item(); n += (tgt != -100).sum().item()
    return tot / n


@torch.no_grad()
def eval_gen(pm, data, tok, args, device):
    """Exact match of the last number in the generation vs. the reference (GSM8K style)."""
    num = lambda s: (re.findall(r"-?\d[\d,]*\.?\d*", s.split("####")[-1]) or [None])[-1]
    hit = 0
    for p, r in data[: args.gen_eval]:
        ids = torch.tensor([p], device=device)
        out = pm.generate(input_ids=ids, attention_mask=torch.ones_like(ids), max_new_tokens=args.gen_max_new,
                          do_sample=False, pad_token_id=tok.pad_token_id)
        hit += num(tok.decode(out[0, len(p):], skip_special_tokens=True)) == num(tok.decode(r, skip_special_tokens=True))
    return hit / min(args.gen_eval, len(data))


def sync(device):
    if device.type == "cuda":
        torch.cuda.synchronize()


# ---------------------------------------------------------------- ACT
def capture(pm, mods, layer, ids, att, stop_name):
    """Run pm until `stop_name` in `layer`; return {module name: (tokens, d_in) input}."""
    got, hs = {}, []
    mask = att.bool().reshape(-1)
    for n, m in mods.items():
        if layer_index(n) != layer:
            continue
        def hook(mod, inp, out, n=n):
            got[n] = inp[0].reshape(-1, inp[0].shape[-1])[mask].float()
            if n == stop_name:
                raise StopForward
        hs.append(m.register_forward_hook(hook))
    try:
        pm(input_ids=ids, attention_mask=att)
    except StopForward:
        pass
    finally:
        for h in hs:
            h.remove()
    return got


@torch.no_grad()
def act_transfer(src_pm, tgt_pm, calib, args, device, pad_id):
    """Sequential ACT (eq. A.2) on every LoRA module; returns per-module chosen alpha and drift."""
    src_mods, tgt_mods = lora_modules(src_pm), lora_modules(tgt_pm)
    names = forward_order(tgt_pm, tgt_mods, device)
    acc = device if device.type == "cuda" else torch.device("cpu")  # MPS has no float64
    layers = sorted({layer_index(n) for n in names})
    n_fit = int(0.8 * len(calib))
    fit, val = calib[:n_fit], calib[n_fit:]
    info = {}
    for l in layers:
        lnames = [n for n in names if layer_index(n) == l]
        stop = lnames[-1]  # last LoRA module of the layer in forward order
        G = {n: {k: 0.0 for k in ("tt_f", "st_f", "tt_v", "st_v", "ss_v", "dn", "sn")} for n in lnames}
        for split, data in (("f", fit), ("v", val)):
            for b in batches(data, args.bs):
                ids, att, _ = collate(b, pad_id, device)
                xs = capture(src_pm, src_mods, l, ids, att, stop)
                xt = capture(tgt_pm, tgt_mods, l, ids, att, stop)
                for n in lnames:
                    s, t = xs[n].to(acc).double(), xt[n].to(acc).double()
                    G[n]["tt_" + split] = G[n]["tt_" + split] + t.T @ t
                    G[n]["st_" + split] = G[n]["st_" + split] + s.T @ t
                    if split == "v":
                        G[n]["ss_v"] = G[n]["ss_v"] + s.T @ s
                    G[n]["dn"] += (t - s).pow(2).sum().item()
                    G[n]["sn"] += s.pow(2).sum().item()
        for n in lnames:
            m = tgt_mods[n]
            A_s = src_mods[n].lora_A["default"].weight.to(acc).double()  # r x d_in
            B = m.lora_B["default"].weight.to(acc).double()              # d_out x r
            BtB = B.T @ B
            g = G[n]
            d = A_s.shape[1]
            eye = torch.eye(d, dtype=torch.float64, device=acc)

            def solve(Gtt, Gst, alpha):
                lam = alpha * torch.trace(Gtt) / d
                rhs = A_s @ (Gst + lam * eye)
                return torch.linalg.solve(Gtt + lam * eye, rhs.T).T

            def val_err(A):  # ||B A X_t - B A_s X_s||^2 on validation tokens, Gram-only
                Gts = g["st_v"].T
                return (torch.trace(BtB @ A @ g["tt_v"] @ A.T) - 2 * torch.trace(BtB @ A @ Gts @ A_s.T)
                        + torch.trace(BtB @ A_s @ g["ss_v"] @ A_s.T)).item()
            errs = [val_err(solve(g["tt_f"], g["st_f"], a)) for a in ALPHAS]
            best = ALPHAS[min(range(len(ALPHAS)), key=errs.__getitem__)]
            A_new = solve(g["tt_f"] + g["tt_v"], g["st_f"] + g["st_v"], best)
            w = m.lora_A["default"].weight
            w.copy_(A_new.to(device=w.device, dtype=w.dtype))
            info[n] = {"alpha": best, "drift": math.sqrt(g["dn"] / max(g["sn"], 1e-12))}
        print(f"  ACT layer {l}: alphas " + ", ".join(f"{info[n]['alpha']:.0e}" for n in lnames))
    return info


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="meta-llama/Llama-3.2-1B")
    ap.add_argument("--target", default="meta-llama/Llama-3.2-1B-Instruct")
    ap.add_argument("--pair-name", default=None, help="label stored as 'drift' in the output JSON")
    ap.add_argument("--dataset", default="openai/gsm8k")
    ap.add_argument("--dataset-config", default="main")
    ap.add_argument("--eval-split", default="test")
    ap.add_argument("--prompt-template", default="Question: {question}\nAnswer:")
    ap.add_argument("--response-field", default="answer")
    ap.add_argument("--n-train", type=int, default=2000)
    ap.add_argument("--n-eval", type=int, default=500)
    ap.add_argument("--n-cal", type=int, default=256)
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--rank", type=int, default=8)
    ap.add_argument("--lora-alpha", type=int, default=16)
    ap.add_argument("--source-revision", default=None, help="branch/tag/commit, e.g. step100000 for Pythia")
    ap.add_argument("--target-revision", default=None)
    ap.add_argument("--target-modules", nargs="+", default=["auto"],
                    help="'auto' = every linear inside the decoder layers")
    ap.add_argument("--preset", choices=["gpu", "cpu"], default=None,
                    help="cpu = smaller run sized for a laptop/desktop CPU")
    ap.add_argument("--threads", type=int, default=None, help="torch CPU threads")
    ap.add_argument("--steps", type=int, default=1000)
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--gen-eval", type=int, default=0, help="also score generation EM on this many eval rows")
    ap.add_argument("--gen-max-new", type=int, default=256)
    ap.add_argument("--gpu-price", type=float, default=2.0, help="$ per compute hour, for the cost report")
    ap.add_argument("--seed", type=int, default=0,
                    help="data subset, training order and LoRA init; 0 reproduces the original single run")
    ap.add_argument("--out", default="results/act_llama.json")
    ap.add_argument("--tiny", action="store_true", help="CPU smoke test with random tiny models")
    ap.add_argument("--tiny-arch", choices=["llama", "qwen2", "gpt_neox"], default="llama")
    ap.add_argument("--tiny-vocab", type=int, default=64)
    ap.add_argument("--tiny-drift", type=float, default=0.3)
    ap.add_argument("--tiny-pretrain", type=int, default=200)
    pre, _ = ap.parse_known_args()
    if pre.preset == "cpu":  # explicit flags on the command line still win
        ap.set_defaults(n_train=500, n_eval=200, n_cal=128, max_len=256, steps=300, bs=4, lr=5e-4)
    args = ap.parse_args()
    if args.threads:
        torch.set_num_threads(args.threads)

    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available() and args.preset != "cpu":
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    dtype = torch.bfloat16 if device.type == "cuda" and torch.cuda.is_bf16_supported() else \
        torch.float16 if device.type == "cuda" else torch.float32
    if args.tiny:
        args.n_train, args.n_eval, args.n_cal = min(args.n_train, 512), min(args.n_eval, 128), min(args.n_cal, 128)
        args.steps, args.bs, args.lr, args.rank = min(args.steps, 300), 32, 3e-3, 4
        args.pair_name = args.pair_name or f"tiny-{args.tiny_drift}"
        src, tgt = tiny_pair(args, device)
        tok, pad_id = None, 0
    else:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(args.source, revision=args.source_revision)
        tok_t = AutoTokenizer.from_pretrained(args.target, revision=args.target_revision)
        vs, vt = tok.get_vocab(), tok_t.get_vocab()
        if any(vt.get(k) != i for k, i in vs.items()):
            raise SystemExit("source and target tokenizers differ: ACT needs a shared tokenizer (Appendix A.1)")
        tok.pad_token = tok.pad_token or tok.eos_token
        pad_id = tok.pad_token_id
        src = load_model(args.source, args.source_revision, device, dtype)
        tgt = load_model(args.target, args.target_revision, device, dtype)
        tag = lambda m, r: m + (f"@{r}" if r else "")
        args.pair_name = args.pair_name or f"{tag(args.source, args.source_revision)}->{tag(args.target, args.target_revision)}"
    train, evals, calib = load_examples(args, tok)
    print(f"device={device} train={len(train)} eval={len(evals)} calib={len(calib)}")

    torch.manual_seed(1000 + args.seed)
    src_pm, tgt_pm = add_lora(src, args), add_lora(tgt, args)
    init = get_lora_state(tgt_pm)
    res = {"pair": args.pair_name, "args": vars(args)}

    print("[1] train source adapter")
    res["time_train_source_s"] = train_lora(src_pm, train, args, device, pad_id, seed=100 * args.seed)
    src_state = get_lora_state(src_pm)

    print("[2] retrain on target (upper bound, C_N)")
    set_lora_state(tgt_pm, init)
    res["time_retrain_s"] = train_lora(tgt_pm, train, args, device, pad_id, seed=100 * args.seed + 1)
    retr_state = get_lora_state(tgt_pm)

    def evaluate(tag):
        r = {"nll": eval_nll(tgt_pm, evals, args, device, pad_id)}
        if args.gen_eval and tok is not None:
            r["em"] = eval_gen(tgt_pm, evals, tok, args, device)
        print(f"  {tag:8s} " + " ".join(f"{k}={v:.4f}" for k, v in r.items()))
        return r

    print("[3] evaluate on target")
    with tgt_pm.disable_adapter():
        res["none"] = evaluate("none")
    set_lora_state(tgt_pm, retr_state); res["retrain"] = evaluate("retrain")
    set_lora_state(tgt_pm, src_state); res["copy"] = evaluate("copy")

    print("[4] ACT")
    sync(device); t0 = time.time()
    res["act_info"] = act_transfer(src_pm, tgt_pm, calib, args, device, pad_id)
    sync(device); res["time_act_s"] = time.time() - t0
    res["act"] = evaluate("act")

    def recovery(metric, higher_better):
        n, r = res["none"][metric], res["retrain"][metric]
        f = (lambda m: (m - n) / (r - n)) if higher_better else (lambda m: (n - m) / (n - r))
        return f(res["copy"][metric]), f(res["act"][metric])
    R_C, R_A = recovery("nll", False)
    res["recovery"] = [{"drift": args.pair_name, "metric": "nll", "R_C": R_C, "R_A": R_A}]
    if "em" in res["none"]:
        R_Ce, R_Ae = recovery("em", True)
        res["recovery_em"] = {"R_C": R_Ce, "R_A": R_Ae}
    res["C_A_over_C_N"] = res["time_act_s"] / res["time_retrain_s"]
    res["cost_usd"] = {k: res[f"time_{k}_s"] / 3600 * args.gpu_price for k in ("retrain", "act")}
    print(f"\nR_C={R_C:.4f}  R_A={R_A:.4f}  (NLL-based)   "
          f"C_A/C_N={res['C_A_over_C_N']:.3f} (compute time only; add data and revalidation labor to C_N)")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(res, open(args.out, "w"), indent=2, default=float)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
