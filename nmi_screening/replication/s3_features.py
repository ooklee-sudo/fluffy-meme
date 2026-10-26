"""Step 3: event counts, dispersion and scale-dependent clustering features.
Each document: first 2,000 whitespace tokens = four windows of 500. Seven events per window:
parentheses, square brackets, semicolons, paired quotation marks, 14 discourse markers, passive constructions (form of 'be' + participle,
pattern matching), nominalizations (-tion, -ment, -ity). Baseline features (14): rate (mean count per window) and dispersion index
(variance/mean over the four windows; 1 when the event does not occur) for each event. Clustering features (21): for each event,
the rate, the mean log Fano factor over window sizes 50/100/200/400 tokens (same 2,000 tokens) and the slope of log F on log w.
Fano factors are clipped to [0.05, 20] and set to 1 when the event does not occur. Output data/features.csv.
"""
import json, os, re
import numpy as np, pandas as pd
from common import DATA

MARKERS = ["however", "therefore", "moreover", "furthermore", "additionally", "consequently", "thus", "hence", "nevertheless",
           "nonetheless", "similarly", "notably", "importantly", "overall"]       # 14 markers (our choice; the source study's list is not available)
PASSIVE = re.compile(r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?\w+(?:ed|en)\b", re.I)
NOMINAL = re.compile(r"\b\w+(?:tion|ment|ity)\b", re.I)
MARK = re.compile(r"\b(?:" + "|".join(MARKERS) + r")\b", re.I)
EVENTS = ["paren", "bracket", "semicolon", "quote", "marker", "passive", "nominal"]

def counts(chunk):
    return [chunk.count("("), chunk.count("["), chunk.count(";"), chunk.count("“") + chunk.count('"') // 2,
            len(MARK.findall(chunk)), len(PASSIVE.findall(chunk)), len(NOMINAL.findall(chunk))]

def windows(tokens, w):
    return np.array([counts(" ".join(tokens[i:i + w])) for i in range(0, len(tokens) - w + 1, w)], float)   # (n_windows, 7)

def fano(c):
    m = c.mean(0); v = c.var(0, ddof=1) if len(c) > 1 else np.zeros(c.shape[1])
    f = np.where(m > 0, v / np.maximum(m, 1e-12), 1.0); return np.clip(f, 0.05, 20.0), m

def features(text):
    tokens = text.split()
    if len(tokens) < 2000: return None
    tokens = tokens[:2000]; row = {}
    c500 = windows(tokens, 500); rate = c500.mean(0)
    disp, _ = fano(c500)
    disp_idx = np.where(rate > 0, c500.var(0, ddof=1) / np.maximum(rate, 1e-12), 1.0)       # unclipped dispersion index at 500 tokens
    for i, e in enumerate(EVENTS):
        row[f"rate_{e}"] = rate[i]; row[f"disp_{e}"] = disp_idx[i]
    ws = [50, 100, 200, 400]; F = np.array([fano(windows(tokens, w))[0] for w in ws])        # (4, 7)
    lw = np.log(ws)
    for i, e in enumerate(EVENTS):
        lf = np.log(F[:, i]); row[f"fano_mean_{e}"] = lf.mean()
        row[f"fano_slope_{e}"] = np.polyfit(lw, lf, 1)[0] if np.ptp(lf) > 0 else 0.0
    return row

if __name__ == "__main__":
    rows = []
    srcs = [("human", "human.jsonl")] + [(g, f"machine_{g}.jsonl") for g in ("gpt4o", "claude", "llama")]
    for g, fn in srcs:
        p = os.path.join(DATA, fn)
        if not os.path.exists(p): continue
        for l in open(p):
            d = json.loads(l); f = features(d["text"])
            if f: rows.append(dict(id=d["id"], source=d.get("source", d["id"]) if g != "human" else d["id"], generator=g, label=int(g != "human"),
                                   field=("pmc" if str(d["id"]).startswith("PMC") or str(d.get("source", "")).startswith("PMC") else "arxiv"), **f))
    df = pd.DataFrame(rows); df.to_csv(os.path.join(DATA, "features.csv"), index=False)
    print(len(df), "documents;", df.generator.value_counts().to_dict())
