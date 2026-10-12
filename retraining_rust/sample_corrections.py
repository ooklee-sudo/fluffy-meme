"""Draw a stratified sample of later user turns for validating the correction detector.
Strata: (A) flagged by DISSAT, (B) unflagged but containing a weak cue, (C) unflagged without cue.
Reservoir sampling with a fixed seed; stores truncated text locally (scratch) for labelling only.
  python sample_corrections.py --shards 1 5 9 13 --workdir W --out sample.json
"""
import argparse, json, os, random, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pyarrow.parquet as pq
from wildchat_drift import DISSAT, URL

CUE = re.compile(r"\b(wrong|incorrect|mistake|error|not (right|correct|what|true|work\w*)|doesn'?t|didn'?t|isn'?t|again|actually|fix|redo|rewrite|instead)\b", re.I)
SIZES = {"A": 150, "B": 150, "C": 100}

ap = argparse.ArgumentParser(); ap.add_argument("--shards", type=int, nargs="+"); ap.add_argument("--workdir"); ap.add_argument("--out")
a = ap.parse_args(); rng = random.Random(42)
res = {k: [] for k in SIZES}; N = {k: 0 for k in SIZES}
for s in a.shards:
    p = os.path.join(a.workdir, f"s{s}.parquet")
    if not os.path.exists(p): subprocess.run(["curl", "-sSL", "-m", "900", "-o", p, URL % s], check=True)
    for b in pq.ParquetFile(p).iter_batches(batch_size=5000, columns=["conversation_hash", "model", "conversation", "language"]):
        for h, model, conv, lang in zip(*[b.column(c).to_pylist() for c in ("conversation_hash", "model", "conversation", "language")]):
            if lang != "English" or not (model.startswith("gpt-3.5-turbo") or model in ("gpt-4-0314", "gpt-4-0613")): continue
            prev = ""; k = 0
            for m in conv:
                if m["role"] == "assistant": prev = (m["content"] or "")[-200:]
                elif m["role"] == "user":
                    k += 1
                    if k >= 2:
                        t = m["content"] or ""
                        st = "A" if DISSAT.search(t[:120]) else ("B" if CUE.search(t[:300]) else "C")
                        N[st] += 1; item = dict(id=f"{h}:{k}", stratum=st, prev=prev, text=t[:300])
                        if len(res[st]) < SIZES[st]: res[st].append(item)
                        else:
                            j = rng.randrange(N[st])
                            if j < SIZES[st]: res[st][j] = item
    os.remove(p); print("shard", s, N, flush=True)
json.dump(dict(N=N, items=[x for v in res.values() for x in v]), open(a.out, "w"))
