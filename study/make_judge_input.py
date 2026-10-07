"""Build the blind judge input: 500 excerpts (200 human, 100 per generator), first 2,000 tokens, identical cleanup for all sources.
Opaque ids; the label key is written to a separate file and never shown to the judge. Fixed seed."""
import json, random, re, hashlib
import features as F

load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
rng = random.Random(11)
human = [r for r in load("data/human.jsonl") if len(F.TOK.findall(r["text"])) >= 2000]
gens = {g: list({r["human_id"]: r for r in load(f"data/synthetic/{g}.jsonl")}.values()) for g in ("gpt4o", "claude", "llama")}
field = {r["id"]: r["field"] for r in human}

def clean(t):
    t = re.sub(r"(?m)^\s*#{1,6}\s.*$", " ", t)            # markdown heading lines
    t = re.sub(r"(?m)^\s*(Introduction|Methods|Results|Discussion and Conclusion|Discussion)\s*$", " ", t)  # bare section titles
    t = re.sub(r"[*_`]{1,3}", "", t)                       # emphasis markers
    t = re.sub(r"(?m)^\s*[-•]\s+", "", t)                  # bullet markers
    return " ".join(F.TOK.findall(t)[:2000])

# stratify humans by field (about 60% medicine / 40% computer science, as in the full sample)
med = [r for r in human if r["field"] == "medicine"]; cs = [r for r in human if r["field"] != "medicine"]
pick_h = rng.sample(med, 120) + rng.sample(cs, 80)
docs, key = [], []
def add(src, rid, text, fld):
    oid = hashlib.sha1(f"{src}|{rid}|salt7".encode()).hexdigest()[:12]
    docs.append(dict(id=oid, text=clean(text))); key.append(dict(id=oid, source=src, source_id=rid, field=fld))
for r in pick_h: add("human", r["id"], r["text"], r["field"])
for g, rows in gens.items():
    for r in rng.sample([x for x in rows if len(F.TOK.findall(x["text"])) >= 2000], 100): add(g, r["human_id"], r["text"], field.get(r["human_id"]))
order = list(range(len(docs))); rng.shuffle(order)                      # random presentation order
with open("data/judge_input.jsonl", "w", encoding="utf-8") as f:
    for i in order: f.write(json.dumps(docs[i], ensure_ascii=False) + "\n")
with open("data/judge_key.jsonl", "w", encoding="utf-8") as f:
    for k in key: f.write(json.dumps(k) + "\n")
n_tok = sum(len(d["text"].split()) for d in docs)
print(f"{len(docs)} excerpts; total ~{n_tok:,} words (~{int(n_tok*1.35):,} tokens)  e.g. cost@$2.5/M input ~ ${n_tok*1.35*2.5/1e6:.1f}")
leak = [d for d in docs if "##" in d["text"] or "**" in d["text"]]; print("residual markdown in", len(leak), "excerpts")
