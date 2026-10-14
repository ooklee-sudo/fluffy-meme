"""Census MRTS restaurant-sales analysis exactly as in ANALYSIS_PLAN_MRTS.md. Usage: python analysis_mrts.py mrtssales92-present.xlsx"""
import sys, re, json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
X = pd.ExcelFile(sys.argv[1]); MON = {m: i + 1 for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}
WANT = {"722511": "full", "722513, 722514, 722515": "limited", "7224": "drinking", "7225": "restaurants", "722": "foodsvc", "4451": "grocery"}
rows = []
for sh in X.sheet_names:
    if not re.fullmatch(r"\d{4}", sh): continue
    s = X.parse(sh, header=None); hdr = None
    for i in range(min(12, len(s))):
        vals = [str(v) for v in s.iloc[i, :].tolist()]
        if sum(bool(re.match(r"[A-Z][a-z]{2}\.? \d{4}", v)) for v in vals) >= 2: hdr = i; break
    if hdr is None: continue
    cols = {}
    for j, v in enumerate(s.iloc[hdr, :].tolist()):
        m = re.match(r"([A-Z][a-z]{2})\.? (\d{4})", str(v))
        if m and m.group(1) in MON: cols[j] = pd.Period(f"{m.group(2)}-{MON[m.group(1)]:02d}", "M")
    seen = set()
    for i in range(hdr + 1, len(s)):
        lab = str(s.iloc[i, 1]).upper()
        if "ADJUSTED" in lab and "NOT" not in lab: break                       # stop at the seasonally adjusted block
        code = str(s.iloc[i, 0]).strip()
        if code in WANT and code not in seen:
            seen.add(code)
            for j, per in cols.items():
                v = pd.to_numeric(s.iloc[i, j], errors="coerce")
                if pd.notna(v): rows.append((WANT[code], per, float(v)))
D = pd.DataFrame(rows, columns=["series", "period", "sales"]).drop_duplicates(["series", "period"]).pivot(index="period", columns="series", values="sales").sort_index()
D["full_published"] = D["full"]; D["full"] = D.restaurants - D.limited                                  # Amendment 1: derived because 722511 is withheld from 2020-02
chk = D.dropna(subset=["full_published"]); disc = float(((chk.full - chk.full_published).abs() / chk.full_published).max()); print("identity check (derived vs published full-service): max abs relative discrepancy = %.4f over %d months" % (disc, len(chk)))
assert disc < 0.01, "derivation invalid: discrepancy above 1%"
D["LSR"] = np.log(D.limited) - np.log(D.full)
print("series:", list(D.columns), "| months", len(D), D.index.min(), D.index.max()); print("missing by series:", D.isna().sum().to_dict())
OUT = {"limited": "ln limited", "full": "ln full", "drinking": "ln drinking", "restaurants": "ln restaurants", "grocery": "ln grocery"}
def ln(col): return D["LSR"] if col == "LSR" else np.log(D[col])
def deviation(col, year, train=36, nposthmonths=5, trend=True):
    end = pd.Period(f"{year}-02", "M"); start = end - (train - 1); post = [pd.Period(f"{year}-{m:02d}", "M") for m in range(3, 3 + nposthmonths)]
    y = ln(col); tr = y.loc[start:end].dropna()
    if len(tr) < train - 2 or any(p not in y.index or pd.isna(y.loc[p]) for p in post): return None
    t0 = np.arange(len(tr)); mo = np.array([p.month for p in tr.index])
    X = np.column_stack([(mo == m).astype(float) for m in range(1, 13)] + ([t0.astype(float)] if trend else []))
    beta, *_ = np.linalg.lstsq(X, tr.values, rcond=None)
    pred = []
    for p in post:
        k = int((p - tr.index[0]).n); xr = np.array([(p.month == m) * 1.0 for m in range(1, 13)] + ([float(k)] if trend else [])); pred.append(xr @ beta)
    return float(np.mean(y.loc[post].values - np.array(pred)))
YEARS = [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2025]; res = {}
def run(col, train=36, nposthmonths=5, trend=True, label=None):
    d26 = deviation(col, 2026, train, nposthmonths, trend); pl = {y: deviation(col, y, train, nposthmonths, trend) for y in YEARS}; pl = {y: v for y, v in pl.items() if v is not None}
    allv = list(pl.values()) + ([d26] if d26 is not None else []); p = float(np.mean([abs(v) >= abs(d26) - 1e-12 for v in allv])) if d26 is not None else None
    return dict(D2026=d26, placebo_years=pl, n_years=len(allv), perm_p=p, rank_abs=int(1 + sum(abs(v) > abs(d26) for v in pl.values())) if d26 is not None else None)
for col in ["LSR", "limited", "full", "restaurants", "grocery"]: res[f"main: {col}"] = run(col)
res["check train 24: LSR"] = run("LSR", train=24); res["check train 48: LSR"] = run("LSR", train=48); res["check no trend: LSR"] = run("LSR", trend=False); res["check Mar-Jun: LSR"] = run("LSR", nposthmonths=4)
json.dump(res, open("results_mrts.json", "w"), indent=1, default=float)
for k, v in res.items(): print(k, "D2026=%.4f" % v["D2026"] if v["D2026"] is not None else "D2026=NA", "| placebo |D| median=%.4f max=%.4f" % (np.median([abs(x) for x in v["placebo_years"].values()]), max(abs(x) for x in v["placebo_years"].values())), "| rank(|D|) %s of %d" % (v["rank_abs"], v["n_years"]), "| perm p=%s" % (round(v["perm_p"], 3) if v["perm_p"] is not None else None))
