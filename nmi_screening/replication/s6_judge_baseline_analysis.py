"""Step 6: judges (AUC, share flagged at threshold 50) and zero-shot published-detector baselines; both on the judge sample or the full corpus."""
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from common import DATA
rng = np.random.default_rng(0)
def ci(y, s, n=1000):
    a = roc_auc_score(y, s); bs = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if len(set(y[i])) == 2: bs.append(roc_auc_score(y[i], s[i]))
    return f"{a:.3f} [{np.percentile(bs,2.5):.2f}, {np.percentile(bs,97.5):.2f}]"
samp = pd.read_csv(f"{DATA}/judge_sample.csv"); js = pd.read_csv(f"{DATA}/judge_scores.csv")
w = js.pivot_table(index="id", columns="judge", values="p_ai", aggfunc="first").reset_index()
d = samp.merge(w, on="id"); d["label"] = (d.generator != "human").astype(int)
print(f"judge sample: {len(d)} excerpts; unreadable GPT-4o answers: {d.gpt4o.isna().sum()}, Gemini: {d.gemini.isna().sum()}")
ok = d.dropna(subset=["gpt4o", "gemini"]); print("analyzed:", ok.generator.value_counts().to_dict())
print("\n== Judges: AUC [95% CI] human vs generator; share flagged at p>=50")
hum = ok[ok.generator == "human"]
for g in ("gpt4o", "claude", "llama"):
    m = ok[ok.generator == g]; dd = pd.concat([hum, m]); row = {}
    for j in ("gpt4o", "gemini"):
        row[j] = ci(dd.label.values, dd[j].values) + f"; flagged {np.mean(m[j]>=50):.2f} (human {np.mean(hum[j]>=50):.2f})"
    print(g, row)
print("\n== Published zero-shot detectors on the full corpus (Falcon-7B pair; AUC human vs generator)")
b = pd.read_csv(f"{DATA}/scores_binoculars.csv")
for det in ("loglik", "logrank", "entropy", "binoculars", "fastdetect"):
    row = {}
    for g in ("gpt4o", "claude", "llama"):
        dd = b[(b.generator == "human") | (b.generator == g)]; row[g] = ci(dd.label.values, dd[det].values)
    print(f"{det:11s}", row)
