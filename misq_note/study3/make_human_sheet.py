"""Blind human coding sheet: 150 of the 400 validation reviews (text only; no rating, no LLM codes)."""
import json, random, pandas as pd
ids = json.load(open("val_ids.json")); t = pd.read_json("sample_text.jsonl", lines=True).set_index("rid")
pick = sorted(random.Random(7).sample(ids, 150))
cols = ["overall", "defect", "price", "durability", "performance", "fit", "ease", "design", "service"]
df = pd.DataFrame({"rid": pick, "text": t.loc[pick, "text"].values, **{c: "" for c in cols}})
with pd.ExcelWriter("human_coding_sheet.xlsx", engine="openpyxl") as w:
    df.to_excel(w, index=False, sheet_name="coding"); w.sheets["coding"].column_dimensions["B"].width = 100
    pd.DataFrame({"codebook": open("codebook.md").read().splitlines()}).to_excel(w, index=False, sheet_name="codebook")
print(len(df))
