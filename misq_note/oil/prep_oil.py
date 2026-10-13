"""Compress Inside Airbnb review files to listing-month counts. Usage: python prep_oil.py DATADIR OUTDIR"""
import sys, glob
import numpy as np, pandas as pd
D, O = sys.argv[1], sys.argv[2]
LC, CC, FIRST = [], [], []
for f in sorted(glob.glob(f"{D}/[a-z][a-z]_*_listings.csv.gz")):
    city = f.split("/")[-1].replace("_listings.csv.gz", "")
    l = pd.read_csv(f, usecols=["id", "price", "room_type", "latitude", "longitude"]); l["city"] = city
    r = pd.read_csv(f.replace("listings", "reviews"), usecols=["listing_id", "date"]); d = pd.to_datetime(r.date)
    r["mi"] = (d.dt.year * 12 + d.dt.month - 1).astype("int32")
    c = r.groupby(["listing_id", "mi"]).size().rename("y").reset_index(); c["city"] = city
    fr = r.groupby("listing_id").mi.min().rename("first_mi").reset_index(); fr["city"] = city
    LC.append(l); CC.append(c); FIRST.append(fr)
L = pd.concat(LC); C = pd.concat(CC); F = pd.concat(FIRST)
L["price"] = pd.to_numeric(L.price.astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce")
L.to_parquet(f"{O}/listings.parquet"); C.to_parquet(f"{O}/counts.parquet"); F.to_parquet(f"{O}/first.parquet")
print(len(L), len(C), len(F), C.mi.min(), C.mi.max())
