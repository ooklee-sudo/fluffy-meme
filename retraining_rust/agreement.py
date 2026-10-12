"""Compare human labels (returned xlsx) with the LLM labels in human_labeling/answer_key.json.
  python agreement.py human_labeling/correction_labeling_100_done.xlsx
Reports Cohen's kappa (excluding '?'), raw agreement, and the human-label precision/recall of
the v1 and v2 detectors on this 100-item subsample (unweighted: the subsample is not stratified-
weighted, so use it for agreement, not for population recall)."""
import json, sys
import openpyxl
key = {k["item"]: k for k in json.load(open("human_labeling/answer_key.json"))}
ws = openpyxl.load_workbook(sys.argv[1])["Items"]
hum = {}
for r in ws.iter_rows(min_row=2, values_only=True):
    v = str(r[3]).strip() if r[3] is not None else ""
    hum[int(r[0])] = {"1": 1, "0": 0, "?": "?"}.get(v)
assert all(v is not None for v in hum.values()), "unlabelled rows: " + str([k for k, v in hum.items() if v is None])
pairs = [(hum[i], key[i]["llm_label"]) for i in hum if hum[i] != "?" and key[i]["llm_label"] != "?"]
n = len(pairs); po = sum(a == b for a, b in pairs) / n
p1h = sum(a for a, _ in pairs) / n; p1l = sum(b for _, b in pairs) / n
pe = p1h * p1l + (1 - p1h) * (1 - p1l); kappa = (po - pe) / (1 - pe)
print(f"n={n} (excluded {len(hum)-n} with '?')  agreement={po:.3f}  kappa={kappa:.3f}  human pos rate={p1h:.2f}  LLM pos rate={p1l:.2f}")
for name, f in (("v1", lambda k: k["v1"]), ("v2", lambda k: k["stratum"] == "A")):
    tp = sum(1 for i in hum if hum[i] == 1 and f(key[i])); fp = sum(1 for i in hum if hum[i] == 0 and f(key[i]))
    fn = sum(1 for i in hum if hum[i] == 1 and not f(key[i]))
    print(f"{name}: flagged={tp+fp}  precision(human)={tp/max(tp+fp,1):.2f}  recall in this subsample={tp/max(tp+fn,1):.2f}")
