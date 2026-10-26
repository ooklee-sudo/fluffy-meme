"""Published-detector baselines for the screening study. Run on a GPU (e.g. a RunPod pod); also runs on CPU with small models for testing.

Input : a JSONL file; each line {"id": ..., "label": 0|1 (1 = machine), "generator": "human|gpt4o|claude|llama", "text": ...}
        (use the same first-2000-token excerpt as the screens)
Output: scores.csv with one row per document and one column per detector (higher = more likely machine).

Detectors (zero-shot, no training on machine text):
  loglik      mean token log-likelihood under the observer model (negated: machine text is more likely)
  logrank     mean log-rank of the observed tokens (negated)
  entropy     mean predictive entropy (negated)
  binoculars  log-perplexity of the observer divided by cross-perplexity between observer and performer (Hans et al., 2024)
  fastdetect  analytic sampling discrepancy of a single model (Bao et al., 2024; Fast-DetectGPT)

Defaults reproduce the published setting (Falcon-7B observer, Falcon-7B-instruct performer); for a CPU test use
--observer gpt2 --performer distilgpt2 (they share a tokenizer) --max-tokens 256.

pip install torch transformers accelerate pandas
python3 gpu_baselines.py --data docs.jsonl --out scores.csv [--observer tiiuae/falcon-7b --performer tiiuae/falcon-7b-instruct]
"""
import argparse, json, math
import numpy as np, pandas as pd, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True); ap.add_argument("--out", default="scores.csv")
ap.add_argument("--observer", default="tiiuae/falcon-7b"); ap.add_argument("--performer", default="tiiuae/falcon-7b-instruct")
ap.add_argument("--max-tokens", type=int, default=1024); ap.add_argument("--limit", type=int, default=0)
a = ap.parse_args()
dev = "cuda" if torch.cuda.is_available() else "cpu"
dt = torch.bfloat16 if dev == "cuda" else torch.float32
tok = AutoTokenizer.from_pretrained(a.observer)
if tok.pad_token is None: tok.pad_token = tok.eos_token
obs = AutoModelForCausalLM.from_pretrained(a.observer, torch_dtype=dt).to(dev).eval()
per = AutoModelForCausalLM.from_pretrained(a.performer, torch_dtype=dt).to(dev).eval()
assert AutoTokenizer.from_pretrained(a.performer).get_vocab() == tok.get_vocab(), 'observer and performer must share a tokenizer'

rows = [json.loads(l) for l in open(a.data)]
if a.limit: rows = rows[: a.limit]
out = []
@torch.no_grad()
def score(text):
    ids = tok(text, return_tensors="pt", truncation=True, max_length=a.max_tokens).to(dev)
    x = ids["input_ids"][0, 1:]; lo = obs(**ids).logits[0, :-1].float(); lp = per(**ids).logits[0, :-1].float()
    po = torch.softmax(lo, -1); logpo = torch.log_softmax(lo, -1); pp = torch.softmax(lp, -1)
    nll = -logpo.gather(-1, x[:, None])[:, 0]                          # observer log-loss per token
    ent = -(po * logpo).sum(-1)                                        # observer entropy per token
    rank = (lo > lo.gather(-1, x[:, None])).sum(-1).float() + 1        # rank of observed token
    xppl = -(pp * logpo).sum(-1)                                       # cross-perplexity (performer probs, observer log-probs)
    mu = (po * logpo).sum(-1); var = (po * logpo ** 2).sum(-1) - mu ** 2   # Fast-DetectGPT (same model for sampling and scoring)
    fd = ((-nll) - mu).sum() / torch.sqrt(var.sum().clamp_min(1e-8))
    return dict(loglik=(-nll.mean()).item(), logrank=-torch.log(rank).mean().item(),
                entropy=-ent.mean().item(), binoculars=-(nll.mean() / xppl.mean()).item(), fastdetect=fd.item(), n_tokens=len(x))
# sign convention: every detector column is oriented so that a higher value means "more likely machine-written"
for i, r in enumerate(rows):
    s = score(r["text"])
    out.append({"id": r["id"], "label": r["label"], "generator": r.get("generator", ""), **s})
    if i % 20 == 0: print(i, "/", len(rows), flush=True)
pd.DataFrame(out).to_csv(a.out, index=False); print("wrote", a.out)
