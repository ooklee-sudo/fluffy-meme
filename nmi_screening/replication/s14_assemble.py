"""Assemble per-document scores of every detector for the defence study -> data/defence_scores.csv"""
import json, os
import pandas as pd
from common import DATA
ZS = ["loglik", "logrank", "entropy", "binoculars", "fastdetect"]
z = []
full = pd.read_csv(f"{DATA}/scores_binoculars.csv"); full["key"] = full.id + "|clean"; z.append(full)          # humans (evaluation, calibration), docs text
for f in ("attacked_binoculars.csv", "attacked2_binoculars.csv", "pod_A2_scores.csv"):
    d = pd.read_csv(f"{DATA}/{f}"); d["key"] = d.id; z.append(d)
bok = pd.read_csv(f"{DATA}/pod_A1_scores.csv"); sel = [json.loads(l) for l in open(f"{DATA}/attacked_bok.jsonl")]
cand = {r["id"]: r for r in bok.to_dict("records")}
rows = []
for s in sel:
    hit = [c for k, c in cand.items() if k.startswith(s["id"] + "|bok-" + s["cond"].split("_")[1] + "-") and abs(c["fastdetect"] - s["fd"]) < 1e-9]
    r = dict(hit[0]); r["key"] = f'{s["id"]}|{s["cond"]}'; rows.append(r)
z.append(pd.DataFrame(rows))
Z = pd.concat(z)[["key"] + ZS].drop_duplicates("key", keep="last").set_index("key")
out = []
for t in ("gpt4o", "claude", "llama", "deepseek", "econ"):
    te = pd.DataFrame([{k: v for k, v in json.loads(l).items() if k != "text"} for l in open(f"{DATA}/sup/test_{t}.jsonl")])
    for name, f in (("rb", "rb"), ("tf", "tf"), ("sc", "sc")):
        p = f"{DATA}/sup/{f}_{t}.csv"
        if os.path.exists(p): te = te.merge(pd.read_csv(p).rename(columns={"score": name}), on="id", how="left")
    te["key"] = te.id.str.split("|", n=1).str[1]; te["target"] = t
    te = te.join(Z, on="key"); out.append(te)
D = pd.concat(out); D["cond"] = D.key.str.split("|").str[-1]
D["generator"] = D.apply(lambda r: r.key.split(":")[0] if r.group == "attacked" else "human", axis=1)
D = D.rename(columns={"fastdetect": "fd"}); D.to_csv(f"{DATA}/defence_scores.csv", index=False)
print(D.groupby(["target", "group"]).size().to_string()); print("missing:", D[["fd", "rb", "tf", "sc"]].isna().sum().to_dict())
