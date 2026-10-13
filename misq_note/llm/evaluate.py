"""Validation of LLM coding. Usage: python evaluate.py sample_full.csv [human_codes.xlsx ...]
Outputs validation_results.json. Human files = completed copies of human_coding_sheet.xlsx (one per coder)."""
import sys, json, glob
import numpy as np, pandas as pd
from sklearn.metrics import cohen_kappa_score
from scipy.stats import spearmanr
F = ["overall", "defect", "price", "durability", "battery", "performance", "ease", "design", "service"]
load = lambda p: pd.DataFrame([x for b in range(8) for x in json.load(open(f"out/{p}_{b}.json"))]).set_index("rid")
A, B = load("A"), load("B"); gold = pd.read_csv(sys.argv[1]).set_index("rid")
res = {"n": len(A), "complete": bool(A.notna().all().all() and B.notna().all().all() and len(A) == 400 and len(B) == 400)}
num = {"neg": -1, "neu": 0, "pos": 1}
star = gold["reviews.rating"].reindex(A.index)
for nm, X in (("A", A), ("B", B)):
    s = X.overall.map(num); ok = s.notna()
    res[f"{nm}_vs_stars"] = dict(spearman=float(spearmanr(s[ok], star[ok])[0]),
        acc_pos_neg=float(((s[ok] == 1) == (star[ok] >= 4))[star[ok].isin([1, 2, 4, 5])].mean()),
        pos_share=float((s[ok] == 1).mean()), neg_share=float((s[ok] == -1).mean()))
for nm, X in (("A", A), ("B", B)):
    o = X.overall; res[f"{nm}_vs_stars"].update(
        n_low_star=int((star <= 2).sum()), neg_recall_low_star=float((o[star <= 2] == "neg").mean()),
        n_five=int((star == 5).sum()), pos_recall_five=float((o[star == 5] == "pos").mean()),
        neg_precision=float((star[o == "neg"] <= 2).mean()), majority_baseline_acc=float(star[star.isin([1, 2, 4, 5])].ge(4).mean()))
res["A_vs_B_kappa"] = {f: float(cohen_kappa_score(A[f].astype(str), B[f].astype(str))) for f in F}
res["A_vs_B_agree"] = {f: float((A[f].astype(str) == B[f].astype(str)).mean()) for f in F}
# mention (binary) agreement for aspects, which is what a count covariate uses
for f in F[2:]:
    res["A_vs_B_kappa"][f + "_mention"] = float(cohen_kappa_score(A[f].astype(int) != 0, B[f].astype(int) != 0))
res["prevalence_A"] = {f: float((A[f].astype(int) != 0).mean()) for f in F[2:]}; res["defect_A"] = float(A.defect.astype(int).mean())
res["defect_vs_lowstar"] = float(pd.crosstab(A.defect.astype(int), star <= 2, normalize="index").loc[1, True]) if (A.defect.astype(int) == 1).any() else None
humans = sys.argv[2:]
if humans:
    H = [pd.read_excel(h, sheet_name="coding").set_index("rid") for h in humans]
    res["human_files"] = len(H)
    for nm, X in (("A", A), ("B", B)):
        for i, h in enumerate(H):
            common = h.index
            res[f"{nm}_vs_human{i}"] = {f: float(cohen_kappa_score(X.loc[common, f].astype(str), h[f].astype(str))) for f in F}
    if len(H) > 1:
        c = H[0].index.intersection(H[1].index); res["human0_vs_human1"] = {f: float(cohen_kappa_score(H[0].loc[c, f].astype(str), H[1].loc[c, f].astype(str))) for f in F}
else:
    res["human"] = "PENDING: no human-coded files supplied"
json.dump(res, open("validation_results.json", "w"), indent=1); print(json.dumps(res, indent=1))
