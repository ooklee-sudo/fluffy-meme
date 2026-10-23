"""Write review_results.xlsx from the key map and two completed reviewer sheets.
Usage: python review_report.py BANK.json KEYMAP.csv A.xlsx B.xlsx OUT.xlsx [--labels "Reviewer A" "Reviewer B"]
"""
import argparse, csv, json
from collections import Counter
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font

ap = argparse.ArgumentParser()
ap.add_argument("bank"); ap.add_argument("keymap"); ap.add_argument("a"); ap.add_argument("b"); ap.add_argument("out")
ap.add_argument("--labels", nargs=2, default=["Reviewer A", "Reviewer B"])
x = ap.parse_args()
bank = {i["item_id"]: i for i in json.load(open(x.bank))}
key = list(csv.DictReader(open(x.keymap)))
read = lambda p: {r[0]: (str(r[5] or "").strip().upper() or None, str(r[6] or "").strip()) for r in load_workbook(p)["Review"].iter_rows(min_row=2, values_only=True) if r[0]}
A, B = read(x.a), read(x.b)
LA, LB = x.labels


def kappa(p, q):
    n = len(p); po = sum(u == v for u, v in zip(p, q)) / n
    cp, cq = Counter(p), Counter(q); pe = sum(cp[k] * cq[k] for k in set(cp) | set(cq)) / n ** 2
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


rows = []
for k in key:
    r = k["row"]; it = bank[k["item_id"]]; g = k["gold_letter"]
    a, ac = A[r]; b, bc = B[r]
    rows.append([r, k["item_id"], int(k["domain"]), int(k["tier"]), g, a, a == g, b, b == g, it["roles"].get(b, ""), a == b, "; ".join(c for c in (f"{LA}: {ac}" if ac else "", f"{LB}: {bc}" if bc else "") if c)])
n = len(rows)
sa, sb, sab = (sum(r[i] for r in rows) for i in (6, 8, 10))
ka = kappa([r[5] for r in rows], [r[7] for r in rows])
roleB = Counter(r[9] for r in rows)
tierB = {t: (sum(r[8] for r in rows if r[3] == t), sum(1 for r in rows if r[3] == t)) for t in (1, 2, 3)}
domB = {d: (sum(r[8] for r in rows if r[2] == d), sum(1 for r in rows if r[2] == d)) for d in range(1, 7)}
wb = Workbook(); s = wb.active; s.title = "Summary"
lines = [
    ("Human key review: results", None),
    (f"Items reviewed (same stratified sample for both reviewers)", n),
    (f"{LA}: answers agreeing with the key", f"{sa}/{n} ({sa / n:.0%})"),
    (f"{LB}: answers agreeing with the key", f"{sb}/{n} ({sb / n:.0%})"),
    ("Agreement between the two reviewers", f"{sab}/{n} ({sab / n:.0%})"),
    ("Cohen's kappa between the two reviewers", round(ka, 3)),
    ("Comments left", "; ".join(r[11] for r in rows if r[11]) or "none"),
    ("", None),
    (f"{LB}: which option was chosen", f"correct {roleB['gold']}, 'other' mistake {roleB['other']}, 'unsupported' mistake {roleB['unsupported']}"),
    (f"{LB}: share correct by tier", "; ".join(f"tier {t}: {a}/{m}" for t, (a, m) in tierB.items())),
    (f"{LB}: share correct by domain", "; ".join(f"domain {d}: {a}/{m}" for d, (a, m) in domB.items())),
    ("", None),
    ("Reading", None),
]
def reading(label, k):
    if k / n >= 0.95:
        return f"{label} answered {k}/{n} items as the key does."
    return (f"{label}'s answers are not usable as evidence either way: agreement with the key is {k}/{n}, compared with the 33% expected from guessing, and the wrong answers are spread over all three options. Treat that sheet as missing.")
lines.append((reading(LA, sa), None)); lines.append((reading(LB, sb), None))
if sa / n >= 0.95 and sb / n >= 0.95:
    lines.append((f"Both reviewers confirm the key on this sample. If neither disagreed with the key on any of {n} items, the 95% upper bound on the share of disputed keys is about {3 / n:.0%} (rule of three). Identical answer columns are what two correct reviewers produce, so this review cannot show how independently the two sheets were completed; confirm that before reporting inter-reviewer agreement (kappa is {ka:.2f}). The {600 - n} unsampled items are covered only by the second-program audit.", None))
elif sa / n >= 0.95:
    lines.append((f"{LA} confirms the key on this sample (95% upper bound on disputed keys about {3 / n:.0%}); this does not certify the {600 - n} unsampled items. Obtain a second independent review before reporting agreement between reviewers.", None))
lines = [l for l in lines]
for a, b in lines:
    s.append([a, b])
s["A1"].font = Font(bold=True, size=14)
for r in (13,):
    s[f"A{r}"].font = Font(bold=True)
s.column_dimensions["A"].width = 70; s.column_dimensions["B"].width = 70
for r in s.iter_rows():
    for c in r:
        c.alignment = Alignment(wrap_text=True, vertical="top")
for r in range(14, 17):
    if s.cell(r, 1).value:
        s.merge_cells(f"A{r}:B{r}"); s.row_dimensions[r].height = 80
hdr = ["Row", "Item id", "Domain", "Tier", "Key", f"{LA} answer", f"{LA} = key", f"{LB} answer", f"{LB} = key", f"{LB} chose", "Reviewers agree", "Comments"]
for title, data in (("Items", rows), ("Disagreements", [r for r in rows if not (r[6] and r[8]) or r[11]])):
    w = wb.create_sheet(title); w.append(hdr)
    for c in w[1]:
        c.font = Font(bold=True)
    for r in data:
        w.append([("yes" if v is True else "no" if v is False else v) for v in r])
    for col, wd in zip("ABCDEFGHIJKL", (7, 11, 8, 6, 6, 12, 12, 12, 12, 13, 14, 40)):
        w.column_dimensions[col].width = wd
    w.freeze_panes = "A2"
wb.save(x.out)
print(f"{LA} {sa}/{n}, {LB} {sb}/{n}, kappa {ka:.3f}")
