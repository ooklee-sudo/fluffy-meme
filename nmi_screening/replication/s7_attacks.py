"""Step 7: attacked machine papers. 300 machine papers (the machine papers of the judge sample, 100 per generator), first 2,400 tokens.
 edit    : feature-aware programmatic edit of five easy events (parentheses, square brackets, semicolons, quotation marks, discourse markers).
           For each event the document-level count is moved a share e of the way from the paper's own count to the human mean count, and
           the edits are placed in two of the four 500-token windows (human text clusters). Passives and nominalizations are not edited.
 rewrite : Llama 3.3 70B rewrites the text (chunks of ~800 tokens, target length stated) to read as if written by an experienced human researcher.
 hybrid  : the edit applied to the rewritten text.
Output data/attacked.jsonl {id (orig id), cond, label, generator, text}.   python3 s7_attacks.py [--workers 8]
"""
import argparse, json, random, re
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd
from common import *
from s3_features import MARK, MARKERS, counts, EVENTS

HUMAN_MEAN = None
def human_mean():
    global HUMAN_MEAN
    if HUMAN_MEAN is None:
        f = pd.read_csv(os.path.join(DATA, "features.csv")); f = f[f.generator == "human"]
        HUMAN_MEAN = {e: f[f"rate_{e}"].mean() for e in EVENTS[:5]}
    return HUMAN_MEAN

def edit_window(tokens, ev, delta, rng):
    """Add (delta>0) or remove (delta<0) occurrences of event ev inside a token list."""
    n = len(tokens)
    if delta > 0:
        for _ in range(delta):
            i = rng.randrange(n); t = tokens[i]
            if ev == "paren": tokens[i] = "(" + t.strip("()") + ")"
            elif ev == "bracket": tokens.insert(i + 1, f"[{rng.randint(1, 40)}]")
            elif ev == "semicolon": tokens[i] = t[:-1] + ";" if t.endswith(",") else t + ";"
            elif ev == "quote": tokens[i] = "“" + t + "”"
            elif ev == "marker": tokens.insert(i, rng.choice(MARKERS) + ",")
            n = len(tokens)
    elif delta < 0:
        k = -delta
        for i in rng.sample(range(n), n):
            if k == 0: break
            t = tokens[i]
            if ev == "paren" and "(" in t: tokens[i] = t.replace("(", "").replace(")", ""); k -= 1
            elif ev == "bracket" and "[" in t: tokens[i] = re.sub(r"\[[^\]]*\]?", "", t); k -= 1
            elif ev == "semicolon" and ";" in t: tokens[i] = t.replace(";", ","); k -= 1
            elif ev == "quote" and re.search(r'[“”"]', t): tokens[i] = re.sub(r'[“”"]', "", t); k -= 1
            elif ev == "marker" and MARK.fullmatch(t.strip(",.;")): tokens[i] = ""; k -= 1
    return [t for t in tokens if t != ""]

def edit(text, e, seed):
    rng = random.Random(seed); toks = text.split(); head, tail = toks[:2000], toks[2000:]
    wins = [head[i:i + 500] for i in range(0, 2000, 500)]
    cur = np.array([counts(" ".join(w)) for w in wins], float)       # (4, 7)
    hm = human_mean(); chosen = rng.sample(range(4), 2)
    for k, ev in enumerate(EVENTS[:5]):
        total_cur = cur[:, k].sum(); total_target = total_cur + e * (4 * hm[ev] - total_cur)
        delta = int(round(total_target - total_cur))
        per = [delta // 2, delta - delta // 2]
        for w, d in zip(chosen, per): wins[w] = edit_window(wins[w], ev, d, rng)
    return " ".join(" ".join(w) for w in wins) + " " + " ".join(tail)

REWRITE = ("Rewrite the following passage from a scientific paper so that it reads as if it had been written by an experienced human researcher. "
           "Keep the meaning, the technical content and the citation markers. The rewritten passage should be about {n} words long. "
           "Output only the rewritten passage.\n\n{chunk}")
def rewrite(text, cap):
    toks = text.split()[:2400]; out = []
    for i in range(0, len(toks), 800):
        chunk = " ".join(toks[i:i + 800]); t, _ = chunk and chat("meta-llama/llama-3.3-70b-instruct", [{"role": "user", "content": REWRITE.format(n=len(toks[i:i + 800]), chunk=chunk)}],
                                                                  max_tokens=2000, temperature=0.7, cap=cap)
        if not t: return None
        out.append(t.strip())
    return " ".join(out)

def job(args):
    d, cap, seed = args
    base = " ".join(d["text"].split()[:2400]); rw = rewrite(base, cap)
    rows = [dict(id=d["id"], cond="orig", text=base)]
    for e in (0.25, 0.5, 0.75, 1.0): rows.append(dict(id=d["id"], cond=f"edit{e}", text=edit(base, e, seed)))
    if rw and len(rw.split()) >= 2000:
        rows.append(dict(id=d["id"], cond="rewrite", text=rw))
        for e in (0.5, 1.0): rows.append(dict(id=d["id"], cond=f"hybrid{e}", text=edit(rw, e, seed)))
    for r in rows: r.update(label=1, generator=d["generator"], source=d["source"])
    return rows

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=8); ap.add_argument("--cap-usd", type=float, default=70.0); a = ap.parse_args()
    samp = pd.read_csv(os.path.join(DATA, "judge_sample.csv")); ids = set(samp[samp.generator != "human"].id)
    docs = []
    for g in ("gpt4o", "claude", "llama"):
        for l in open(os.path.join(DATA, f"machine_{g}.jsonl")):
            d = json.loads(l)
            if d["id"] in ids: docs.append(d)
    print(len(docs), "machine papers", flush=True)
    out = os.path.join(DATA, "attacked.jsonl"); n_rw = 0
    done = {json.loads(l)["id"] for l in open(out)} if os.path.exists(out) else set()      # resumable: keep finished papers
    docs = [d for d in docs if d["id"] not in done]; print(len(done), "papers already attacked;", len(docs), "to do", flush=True)
    with ThreadPoolExecutor(a.workers) as ex, open(out, "a") as f:
        for i, rows in enumerate(ex.map(job, [(d, a.cap_usd, 100 + k) for k, d in enumerate(docs)])):
            n_rw += any(r["cond"] == "rewrite" for r in rows)
            for r in rows: f.write(json.dumps(r) + "\n")
            if i % 25 == 0: print(i, "/", len(docs), "rewritten so far", n_rw, f"spend ${spend():.2f}", flush=True)
    print("done; rewritten", n_rw, "of", len(docs))
