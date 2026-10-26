"""Step 14: prepare scoring files for the defence study (two-sided score and heterogeneous ensembles).
 calib   : choose 100 calibration human papers (not in the judge sample); they are excluded from every supervised training set and used to standardize scores.
 podA    : documents for zero-shot scoring on the GPU (best-of-K candidates, DeepSeek attacks, economics papers); writes data/pod_A.jsonl
 select  : after pod scoring of candidates, keep per paper the candidate with the lowest Fast-DetectGPT score (the attacker's query), write data/attacked_bok.jsonl
 sup     : train/test files for TF-IDF and RoBERTa (per-document scores) and the count screen scores
python3 s14_prepare.py calib | podA | select | sup
"""
import argparse, json, random
import numpy as np, pandas as pd
from common import *
from s5_judges import excerpt
rd = lambda f: [json.loads(l) for l in open(os.path.join(DATA, f))]
wr = lambda f, rows: open(os.path.join(DATA, f), "w").write("".join(json.dumps(r) + "\n" for r in rows))
GENS = ("gpt4o", "claude", "llama", "deepseek")

def samp(): return pd.read_csv(os.path.join(DATA, "judge_sample.csv"))
def calib(a):
    hold = set(samp()[samp().generator == "human"].id); docs = [d for d in rd("docs.jsonl") if d["generator"] == "human" and d["id"] not in hold]
    random.Random(21).shuffle(docs); ids = [d["id"] for d in docs[:100]]; json.dump(ids, open(os.path.join(DATA, "cal_ids.json"), "w")); print(len(ids), "calibration humans of", len(docs))

def podA(a):
    rows = []
    for r in rd("bestofk_cands.jsonl"): rows.append(dict(id=f'{r["id"]}|bok-{r["kind"]}-{r["k"]}', label=1, generator=r["generator"], text=excerpt(r["text"])))
    for f in ("attacked_ds.jsonl", "attacked2_ds.jsonl", "attacked_econ.jsonl"):
        for r in rd(f): rows.append(dict(id=f'{r["id"]}|{r["cond"]}', label=1, generator=r["generator"], text=excerpt(r["text"])))
    for h in rd("human_econ.jsonl"): rows.append(dict(id=h["id"] + "|clean", label=0, generator="human_econ", text=excerpt(h["text"])))
    wr("pod_A.jsonl", rows); print(len(rows), "documents for pod phase A")

def select(a):
    sc = pd.read_csv(os.path.join(DATA, "pod_A_scores.csv")); sc = sc[sc.id.str.contains(r"\|bok-")].copy()
    sc["pid"] = sc.id.str.split("|").str[0]; sc["kind"] = sc.id.str.split("-").str[1]; sc["k"] = sc.id.str.split("-").str[2].astype(int)
    best = sc.loc[sc.groupby(["pid", "kind"]).fastdetect.idxmin()]
    cands = {(r["id"], r["kind"], r["k"]): r for r in rd("bestofk_cands.jsonl")}; out = []
    for b in best.itertuples():
        r = cands[(b.pid, b.kind, b.k)]; out.append(dict(id=r["id"], cond=f"bok_{r['kind']}", text=r["text"], generator=r["generator"], source=r["source"], label=1, fd=b.fastdetect))
    wr("attacked_bok.jsonl", out); print(len(out), "selected attacked papers")

def sup(a):
    """Per-target train/test files. Training never contains calibration humans, evaluation humans, papers sharing a source with a test paper,
    the target generator, Llama (the rewriter) or DeepSeek (held out). Test files hold the 200 evaluation humans, the 100 calibration humans and every attacked version."""
    os.makedirs(os.path.join(DATA, "sup"), exist_ok=True)
    docs = rd("docs.jsonl"); cal = set(json.load(open(os.path.join(DATA, "cal_ids.json")))); sm = samp(); hold = set(sm[sm.generator == "human"].id)
    hum = {d["id"]: d for d in docs if d["generator"] == "human"}
    att = {g: [] for g in GENS}
    for f in ("attacked.jsonl", "attacked2.jsonl", "attacked_bok.jsonl", "attacked_ds.jsonl", "attacked2_ds.jsonl"):
        if os.path.exists(os.path.join(DATA, f)):
            for r in rd(f): att[r["generator"]].append(r)
    def neg_rows(tag):
        out = [dict(id=f"{tag}|{i}|clean", label=0, group="eval_neg", field="main", text=excerpt(hum[i]["text"])) for i in sorted(hold & set(hum))]
        out += [dict(id=f"{tag}|{i}|clean", label=0, group="cal", field="main", text=excerpt(hum[i]["text"])) for i in sorted(cal)]
        return out
    for g in GENS:
        test_src = {str(r["source"]) for r in att[g]}
        train = [dict(id=d["id"], label=d["label"], text=excerpt(d["text"])) for d in docs
                 if str(d["source"]) not in test_src and d["id"] not in hold and d["id"] not in cal
                 and (d["generator"] == "human" or d["generator"] in {"gpt4o", "claude"} - {g})]
        test = neg_rows(g) + [dict(id=f'{g}|{r["id"]}|{r["cond"]}', label=1, group="attacked", field="main", text=excerpt(r["text"])) for r in att[g]]
        wr(f"sup/train_{g}.jsonl", train); wr(f"sup/test_{g}.jsonl", test); print(g, "train", len(train), "test", len(test))
    train = [dict(id=d["id"], label=d["label"], text=excerpt(d["text"])) for d in docs if d["id"] not in hold and d["id"] not in cal and d["generator"] in ("human", "gpt4o", "claude")]
    test = neg_rows("econ")[200:] + [dict(id=f'econ|{h["id"]}|clean', label=0, group="eval_neg", field="econ", text=excerpt(h["text"])) for h in rd("human_econ.jsonl")]
    test += [dict(id=f'econ|{r["id"]}|{r["cond"]}', label=1, group="attacked", field="econ", text=excerpt(r["text"])) for r in rd("attacked_econ.jsonl")]
    wr("sup/train_econ.jsonl", train); wr("sup/test_econ.jsonl", test); print("econ train", len(train), "test", len(test))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("step", choices=["calib", "podA", "select", "sup"]); a = ap.parse_args()
    {"calib": calib, "podA": podA, "select": select, "sup": sup}[a.step](a)
