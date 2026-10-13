"""Blind coding sheet for human coders: 150 of the 400 sampled reviews, text only, codebook columns empty."""
import json, glob, random, pandas as pd
ids = []; text = {}
for b in range(8):
    for r in json.load(open(f"batch_{b}.json")): ids.append(r["rid"]); text[r["rid"]] = r["text"]
random.Random(7).shuffle(ids); pick = sorted(ids[:150])
cols = ["overall", "defect", "price", "durability", "battery", "performance", "ease", "design", "service"]
df = pd.DataFrame({"rid": pick, "text": [text[i] for i in pick], **{c: "" for c in cols}})
with pd.ExcelWriter("human_coding_sheet.xlsx", engine="openpyxl") as w:
    df.to_excel(w, index=False, sheet_name="coding")
    pd.DataFrame({"codebook": open("codebook.md").read().splitlines()}).to_excel(w, index=False, sheet_name="codebook")
    ws = w.sheets["coding"]; ws.column_dimensions["B"].width = 100
print(len(df))
