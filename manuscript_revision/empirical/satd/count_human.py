import json, sys, difflib, glob, os, multiprocessing as mp, pandas as pd
sys.path.insert(0, "/tmp/satd"); from metrics import analyze
def one(line):
    r = json.loads(line); old, new = r["old_contents"] or "", r["new_contents"] or ""
    if len(new) > 300_000 or len(old) > 300_000: return None
    ol, nl = old.splitlines(), new.splitlines()
    if not ol: added = nl; is_new = True
    else:
        is_new = False; sm = difflib.SequenceMatcher(None, ol, nl, autojunk=False); added = []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag in ("insert", "replace"): added += nl[j1:j2]
    m = analyze(added)
    return None if m is None else dict(commit=r["commit"], lang=r["lang"], repo=(r["repos"] or "").split(",")[0], new_file=is_new, **m)
def run(path):
    lang = os.path.basename(path)[:-6]
    out = []
    for line in open(path):
        x = one(line)
        if x: out.append(x)
    return out
if __name__ == "__main__":
    files = sorted(glob.glob("/tmp/cpft/*.jsonl"))
    with mp.Pool(4) as p: res = p.map(run, files, chunksize=1)
    df = pd.DataFrame([x for r in res for x in r]); df.to_parquet("/tmp/satd/human_rows.parquet"); print("human rows", len(df)); print(df.lang.value_counts().to_string())
