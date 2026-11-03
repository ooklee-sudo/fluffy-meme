"""Established-editor baselines on the real-law fact bank (same launch model, same listed amendments, same evaluation as lm_reallaw_gpu.py).

Editors
  launch    : launch model, no edit (reference)
  ike_own   : in-context editing; the amended statement of a provision is placed before its own question (only for provisions that are listed)
  ike_all   : in-context editing; all listed amended statements are placed before every question
  memit     : MEMIT (EasyEdit) applied to the launch model with all listed amendments as one batch
  rome      : ROME (EasyEdit), listed amendments applied one after another
For MEMIT/ROME the covariance statistics use wikitext-103 with a reduced number of samples (--stats-n), not the 100k Wikipedia samples of the original setting.
Each editor runs inside try/except; failures are recorded in the output file and the run continues.

Run: python lm_editors_gpu.py --model Qwen/Qwen2.5-7B --seeds 1 2 3 --easyedit-dir /work/EasyEdit --out editors_qwen7b.json
"""
import argparse, gc, json, os, random, sys, time, traceback
import torch
import lm_reallaw_gpu as RL

def choose_listed(bank, seed, kA, kdep):
    ch = [i for i, f in enumerate(bank) if f["kind"] == "changed"]
    AB = [i for i in ch if bank[i]["cluster"] in "AB"]; Cb = [i for i in ch if bank[i]["cluster"] == "C" and bank[i]["role"] == "base"]
    Cd = [i for i in ch if bank[i]["cluster"] == "C" and bank[i]["role"] == "dependent"]
    lrng = random.Random(seed * 99 + int(kA * 100) + int(kdep * 10))
    return set(Cb) | set(lrng.sample(AB, max(1, int(round(kA * len(AB)))))) | set(lrng.sample(Cd, int(round(kdep * len(Cd)))))

@torch.no_grad()
def pref_prompts(model, tok, prompts, auth, alt, dev, bs=8):
    model.eval(); out = []
    for i in range(0, len(prompts), bs):
        pr = prompts[i:i+bs]; a, b = auth[i:i+bs], alt[i:i+bs]
        la = max(max(len(tok(x, add_special_tokens=False)["input_ids"]) for x in a), max(len(tok(x, add_special_tokens=False)["input_ids"]) for x in b))
        out += (RL.seq_lp(model, RL.enc(tok, pr, a, dev, la)) > RL.seq_lp(model, RL.enc(tok, pr, b, dev, la))).tolist()
    return out

def metrics(now_ok, bank, listed):
    ch = [i for i, f in enumerate(bank) if f["kind"] == "changed"]; ctl = [i for i, f in enumerate(bank) if f["kind"] == "control"]
    AB = [i for i in ch if bank[i]["cluster"] in "AB"]; Cd = [i for i in ch if bank[i]["cluster"] == "C" and bank[i]["role"] == "dependent"]
    unl = [i for i in ch if i not in listed]
    f = lambda ids: (sum(now_ok[i] for i in ids) / len(ids)) if ids else float("nan")
    return dict(listed=f([i for i in ch if i in listed]), unlisted=f(unl), unlisted_AB=f([i for i in unl if i in AB]),
                ripple_dep=f([i for i in Cd if i not in listed]), keep_control=f(ctl), currency_all=f(ch))

def amendment(f): return RL.prefix(f) + f["new"] + "."

def run_easyedit(alg, bank, listed, args, launch_dir):
    sys.path.insert(0, args.easyedit_dir)
    from easyeditor import BaseEditor, MEMITHyperParams, ROMEHyperParams
    HP = {"memit": MEMITHyperParams, "rome": ROMEHyperParams}[alg]
    hp = HP.from_hparams(os.path.join(args.easyedit_dir, "hparams", alg.upper(), "qwen2.5-7b.yaml"))
    hp.model_name = launch_dir; hp.stats_dir = "/work/stats"; hp.device = 0; hp.mom2_dataset = "wikitext"; hp.mom2_n_samples = args.stats_n
    idx = sorted(listed); prompts = [RL.prefix(bank[i]) for i in idx]
    target = [bank[i]["new"].strip() for i in idx]; truth = [bank[i]["old"].strip() for i in idx]
    editor = BaseEditor.from_hparams(hp)
    if alg == "memit":
        hp.batch_size = len(idx)
        editor.batch_edit(prompts=prompts, target_new=target, ground_truth=truth, subject=prompts, sequential_edit=True, verbose=False)
    else:
        editor.edit(prompts=prompts, target_new=target, ground_truth=truth, subject=prompts, sequential_edit=True, verbose=False)
    return editor.model, editor.tok

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B"); ap.add_argument("--bank", default="real_fact_bank.json")
    ap.add_argument("--lora-r", type=int, default=16); ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--launch-epochs", type=int, default=100); ap.add_argument("--launch-lr", type=float, default=2e-4)
    ap.add_argument("--update-epochs", type=int, default=20); ap.add_argument("--update-lr", type=float, default=1e-4)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1]); ap.add_argument("--kA", type=float, default=0.5); ap.add_argument("--kdep", type=float, default=0.0)
    ap.add_argument("--editors", nargs="+", default=["launch", "ike_own", "ike_all", "memit"])
    ap.add_argument("--easyedit-dir", default="/work/EasyEdit"); ap.add_argument("--stats-n", type=int, default=3000)
    ap.add_argument("--out", default="editors.json")
    args = ap.parse_args()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu"); bank = json.load(open(args.bank))
    rows = json.load(open(args.out)) if os.path.exists(args.out) else []; done = {(r["seed"], r["editor"]) for r in rows}
    n = len(bank); ctl = [i for i, f in enumerate(bank) if f["kind"] == "control"]
    def save(r):
        rows.append(r); json.dump(rows, open(args.out, "w"), indent=1)
        print(f"seed={r['seed']} {r['editor']:8s} " + (f"ERROR {r['error'][:200]}" if "error" in r else
              " ".join(f"{k}={r[k]:.2f}" for k in ("listed", "unlisted", "unlisted_AB", "ripple_dep", "keep_control", "currency_all"))), flush=True)
    for seed in args.seeds:
        todo = [e for e in args.editors if (seed, e) not in done]
        if not todo: continue
        cache = {}; c = RL.launch(args, seed, bank, cache, dev); tok, model = c["tok"], c["model"]
        listed = choose_listed(bank, seed, args.kA, args.kdep); drng = random.Random(seed * 5); dist = {i: RL.distractor(bank[i], drng) for i in ctl}
        auth = [bank[i]["new"] if bank[i]["kind"] == "changed" else bank[i]["old"] for i in range(n)]
        alt = [bank[i]["old"] if bank[i]["kind"] == "changed" else dist[i] for i in range(n)]
        pr = [RL.prefix(f) for f in bank]
        for e in [x for x in todo if x in ("launch", "ike_own", "ike_all")]:
            try:
                if e == "launch": prompts = pr
                elif e == "ike_own": prompts = [amendment(bank[i]) + "\n" + pr[i] if i in listed else pr[i] for i in range(n)]
                else:
                    ctx = "\n".join(amendment(bank[i]) for i in sorted(listed)); prompts = [ctx + "\n" + p for p in pr]
                save(dict(seed=seed, editor=e, n_listed=len(listed), **metrics(pref_prompts(model, tok, prompts, auth, alt, dev), bank, listed)))
            except Exception:
                save(dict(seed=seed, editor=e, error=traceback.format_exc()[-600:]))
        edit_todo = [x for x in todo if x in ("memit", "rome")]
        if edit_todo:
            ldir = "/work/qwen2.5-7b-launch"
            model.save_pretrained(ldir); tok.save_pretrained(ldir)
            del model, c["model"], cache; gc.collect(); torch.cuda.empty_cache()
            for e in edit_todo:
                try:
                    t0 = time.time(); emodel, etok = run_easyedit(e, bank, listed, args, ldir)
                    ok = pref_prompts(emodel, tok, pr, auth, alt, dev)
                    save(dict(seed=seed, editor=e, n_listed=len(listed), edit_seconds=time.time() - t0, **metrics(ok, bank, listed)))
                    del emodel; gc.collect(); torch.cuda.empty_cache()
                except Exception:
                    save(dict(seed=seed, editor=e, error=traceback.format_exc()[-800:]))
                    gc.collect(); torch.cuda.empty_cache()

if __name__ == "__main__":
    main()
