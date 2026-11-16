"""Similarity regression: do unlisted amended provisions follow an update in proportion to their textual similarity to the listed ones?
Unit = (seed, provision) for provisions that were amended but not listed. Outcome = answers with the new value after fine-tuning on the listed statements."""
import json, sys, numpy as np
import statsmodels.api as sm
from sklearn.feature_extraction.text import TfidfVectorizer
def load(bank_path, res_path, methods=("none",), kdeps=(0.0,)):
    bank = json.load(open(bank_path)); rows = [r for r in json.load(open(res_path)) if "ok" in r and r["method"] in methods and r["kdep"] in kdeps]
    return bank, rows
def text(f): return f"{f['act_name']} {f.get('loc') or 'section ' + str(f['section'])} {f['title']} {f['ctx']}"
def build(bank, rows):
    T = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1).fit_transform([text(f) for f in bank])
    S = (T @ T.T).toarray()
    data = []
    for r in rows:
        listed = set(r["listed_idx"])
        for i, f in enumerate(bank):
            if f["kind"] != "changed" or i in listed: continue
            sim = max(S[i, j] for j in listed if j != i)
            data.append(dict(seed=r["seed"], k=r["kA"], method=r["method"], i=i, ok=r["ok"][i], sim=sim, dep=int(f["cluster"] == "C" and f["role"] == "dependent"),
                             same_act=int(any(bank[j]["act_name"] == f["act_name"] for j in listed))))
    return data
def fit(data, label):
    y = np.array([d["ok"] for d in data], float); X = np.array([[1, d["sim"], d["dep"]] for d in data], float)
    g = np.array([d["i"] for d in data])
    res = sm.Logit(y, X).fit(disp=0, cov_type="cluster", cov_kwds={"groups": g})
    print(f"{label}: n={len(y)} follow={y.mean():.2f} | logit coef sim={res.params[1]:+.2f} (se {res.bse[1]:.2f}, p={res.pvalues[1]:.3f}) dependent={res.params[2]:+.2f} (se {res.bse[2]:.2f}, p={res.pvalues[2]:.3f})")
    q = np.quantile([d["sim"] for d in data if not d["dep"]], [0, 1 / 3, 2 / 3, 1]); out = []
    for a, b in zip(q[:-1], q[1:]):
        v = [d["ok"] for d in data if not d["dep"] and a <= d["sim"] <= b]; out.append(f"{np.mean(v):.2f}(n={len(v)})")
    print("   follow rate by similarity tercile (siblings, low->high):", out, "| derived dependents:", f"{np.mean([d['ok'] for d in data if d['dep']]):.2f}" if any(d['dep'] for d in data) else "n/a")
    return res
if __name__ == "__main__":
    bank_path, res_path = sys.argv[1], sys.argv[2]
    bank, rows = load(bank_path, res_path, ("none",))
    fit(build(bank, rows), "amend only")
