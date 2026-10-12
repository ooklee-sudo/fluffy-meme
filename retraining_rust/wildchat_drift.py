"""Measure prompt-distribution drift and user-correction rates in WildChat-1M (English only).

For every English conversation we extract: ISO week, model, #user turns, first-prompt length,
code flag, a post-cutoff-reference flag (years 2022-2024 or entities launched after Sep 2021),
and a dissatisfaction flag per later user turn (corrections / negative feedback).
Weekly unigram counts of first prompts are kept for a drift distance (JS divergence to a
reference window). Writes conv_features.csv.gz and weekly_tokens.pkl. No raw text is stored.

  python wildchat_drift.py --shards 0 1 2 ... --workdir /path/to/scratch
"""
import argparse, gzip, csv, os, pickle, re, subprocess
from collections import Counter, defaultdict
from datetime import datetime
import pyarrow.parquet as pq

URL = "https://huggingface.co/datasets/allenai/WildChat-1M/resolve/main/data/train-%05d-of-00014.parquet"
YEAR = re.compile(r"\b(2022|2023|2024)\b")
ENT = re.compile(r"\b(midjourney|bing chat|bard|llama|claude|stable diffusion|dall-?e ?2|github copilot|gemini pro|mistral)\b", re.I)
JB = re.compile(r"\b(DAN|jailbreak|do anything now|developer mode|stay in character)\b")
DISSAT = re.compile(
    r"^\W*(no\b|nope\b|wrong\b|incorrect\b|that'?s (not|wrong|incorrect)|that is (not|wrong|incorrect)|"
    r"that was (not|wrong)|you('| a)re wrong|this is (not|wrong|incorrect)|not (what|correct|right|true)|"
    r"that (doesn'?t|does not|didn'?t|did not)|it (doesn'?t|does not|didn'?t) work|doesn'?t work|"
    r"try again|redo|you (misunderstood|didn'?t|did not)|i (said|asked|meant)|wrong answer|"
    r"that('s| is) (not|incorrect) (what|correct|right)|error\b)", re.I)
CODE = re.compile(r"```|\bdef \w+\(|\bimport \w+|#include|\bfunction\s*\(|</?\w+>|\bSELECT\b.*\bFROM\b", re.I | re.S)
TOK = re.compile(r"[a-z]{3,}")


def week(ts):
    y, w, _ = ts.isocalendar(); return f"{y}-W{w:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shards", type=int, nargs="+", default=list(range(14)))
    ap.add_argument("--workdir", default="."); ap.add_argument("--out", default=".")
    a = ap.parse_args()
    toks = defaultdict(Counter)
    outp = os.path.join(a.out, "conv_features.csv.gz")
    with gzip.open(outp, "wt", newline="") as fo:
        wr = csv.writer(fo)
        wr.writerow(["week", "model", "n_user", "first_len", "code", "year_ref", "ent_ref", "jb", "later_turns", "dissat_turns"])
        for s in a.shards:
            path = os.path.join(a.workdir, f"s{s}.parquet")
            if not os.path.exists(path):
                subprocess.run(["curl", "-sSL", "-m", "900", "-o", path, URL % s], check=True)
            n = 0
            for b in pq.ParquetFile(path).iter_batches(batch_size=5000, columns=["model", "timestamp", "conversation", "language"]):
                for model, ts, conv, lang in zip(*[b.column(c).to_pylist() for c in ("model", "timestamp", "conversation", "language")]):
                    if lang != "English" or not conv: continue
                    users = [m["content"] or "" for m in conv if m["role"] == "user"]
                    if not users: continue
                    wk = week(ts); first = users[0]; alltext = " ".join(users)
                    later = users[1:]
                    d = sum(1 for u in later if DISSAT.search(u[:120]))
                    wr.writerow([wk, model, len(users), len(first), int(bool(CODE.search(alltext))),
                                 int(bool(YEAR.search(alltext))), int(bool(ENT.search(alltext))), int(bool(JB.search(alltext))), len(later), d])
                    fam = "gpt4" if model.startswith("gpt-4") else "gpt35"
                    toks[(wk, fam)].update(TOK.findall(first.lower()[:2000]))
                    n += 1
            print("shard", s, n, "English convs", flush=True)
            os.remove(path)
    pickle.dump(dict(toks), open(os.path.join(a.out, "weekly_tokens.pkl"), "wb"))


if __name__ == "__main__":
    main()
