"""Blind human coding sheet: 150 of the 400 validation reviews (text only; no stars, no tercile/period, no LLM codes)."""
import json, random, pandas as pd, glob
ids = json.load(open("val_ids.json")); txt = {}
for b in range(8):
    for r in json.load(open(f"val/val_{b}.json")): txt[r["rid"]] = r["text"]
pick = sorted(random.Random(7).sample(ids, 150))
cols = ["overall", "safety", "takeout", "service", "price", "food", "space"]
df = pd.DataFrame({"rid": pick, "text": [txt[i] for i in pick], **{c: "" for c in cols}})
with pd.ExcelWriter("human_coding_sheet.xlsx", engine="openpyxl") as w:
    df.to_excel(w, index=False, sheet_name="coding"); ws = w.sheets["coding"]; ws.column_dimensions["B"].width = 100
    pd.DataFrame({"codebook": open("codebook.md").read().splitlines()}).to_excel(w, index=False, sheet_name="codebook")
print(len(df), df.text.str.len().describe()[["mean", "max"]].round(0).to_dict())
