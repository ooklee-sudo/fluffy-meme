"""Draw a blinded random sample of O*NET tasks for human coding; run both models on it.
Outputs: data/human_coding_sample.csv (give to coders; no model labels)
         data/model_labels_sample.jsonl (model scores, keep from coders)"""
import csv, json, os, random, subprocess, sys
from classify_onet import load
N=200
tasks=load(); titles={r["O*NET-SOC Code"]:r["Title"] for r in csv.DictReader(open("data/Occupation_Data.txt",encoding="utf-8"),delimiter="\t")}
random.Random(2024).shuffle(tasks); S=tasks[:N]
json.dump(S,open("data/sample_ids.json","w"))
with open("data/human_coding_sample.csv","w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["id","occupation","task","score_0_1_2","notes"])
    for t in S: w.writerow([t["id"],titles.get(t["soc"],t["soc"]),t["text"],"",""])
