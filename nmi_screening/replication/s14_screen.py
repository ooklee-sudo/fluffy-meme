"""Count screen (clustering features) per target, trained and scored on the same excerpts as the supervised detectors. Writes data/sup/sc_<target>.csv."""
import json, os
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from common import DATA
from s3_features import features
EV = ["paren", "bracket", "semicolon", "quote", "marker", "passive", "nominal"]
CLUST = [f"rate_{e}" for e in EV] + [f"fano_mean_{e}" for e in EV] + [f"fano_slope_{e}" for e in EV]
def feat(r):
    f = features(r["text"]); return (r["id"], r["label"], [f[c] for c in CLUST] if f else None)
def load(p):
    rows = [json.loads(l) for l in open(p)]
    with ProcessPoolExecutor(4) as ex: return list(ex.map(feat, rows, chunksize=20))
for t in ("gpt4o", "claude", "llama", "deepseek", "econ"):
    tr = [x for x in load(f"{DATA}/sup/train_{t}.jsonl") if x[2]]; te = load(f"{DATA}/sup/test_{t}.jsonl")
    m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)).fit(np.array([x[2] for x in tr]), [x[1] for x in tr])
    ok = [x for x in te if x[2]]; s = m.predict_proba(np.array([x[2] for x in ok]))[:, 1]
    pd.DataFrame(dict(id=[x[0] for x in ok], score=s)).to_csv(f"{DATA}/sup/sc_{t}.csv", index=False); print(t, "train", len(tr), "scored", len(ok), "of", len(te), flush=True)
