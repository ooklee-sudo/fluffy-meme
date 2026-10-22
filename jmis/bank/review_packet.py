"""Blind review packet for the two human reviewers (Section 5.1).

Makes, from bank.json:
  review/reviewer_sheet.xlsx   what each reviewer receives: shuffled anonymous rows, question and three
                               options, empty "Your answer (A/B/C)" and "Comments" columns. No key, no
                               domain, no tier.
  review/key_and_map.csv       authors only: row number -> item id, gold letter, domain, tier.
Usage: python review_packet.py BANKDIR OUTDIR [--seed N]
"""
import argparse
import csv
import json
import os
import random

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.properties import PageSetupProperties


INSTRUCTIONS = [
    "Reviewer instructions: answer key check for a sample of a decision-item bank",
    "",
    "PURPOSE",
    "This workbook contains 50 short business-calculation questions. Each states its own rules and has exactly one correct answer under those rules. We want to know whether independent readers reach the same answer. Please work through the questions without seeing any answer key.",
    "",
    "WHAT TO DO",
    "1. Go to the Review sheet. For each row, read the question and choose A, B or C in the column 'Your answer (A/B/C)'. Use the drop-down list, one letter per row.",
    "2. Apply only the rules stated in the question. Do not use outside conventions where the question gives a rule.",
    "3. If a question seems unclear, or more than one option looks defensible, still choose the option you think is best and describe the problem in the Comments column. Please do not leave an answer blank.",
    "4. Rows are in random order. Neighbouring rows are not related.",
    "",
    "RULES",
    "Work alone and do not discuss the questions with anyone, including the other reviewer, until all sheets are returned.",
    "A calculator or spreadsheet is fine. Please do not use an AI system to answer or to check answers.",
    "Do not share the questions or this file. They are part of an ongoing study.",
    "",
    "TIME",
    "Expect about one to two minutes per question, so roughly one to two hours in total. You may work in several sessions; save the file after each session.",
    "",
    "RETURN",
    "Save the file under its current name with your initials added and send it back by [return date]. Answer all 50 rows.",
]


def stratified_sample(bank, n, seed):
    """n items spread as evenly as possible over the 6 domains and, within each domain, over the 3 tiers;
    the leftover slots go to randomly chosen domains and tiers. Items within a cell are drawn at random.
    Same seed, same sample."""
    rng = random.Random(f"sample-{seed}")
    cells = {}
    for it in bank:
        cells.setdefault((it["domain"], it["tier"]), []).append(it)
    doms = sorted({d for d, _ in cells})
    per_dom, extra_dom = divmod(n, len(doms))
    bonus_dom = set(rng.sample(doms, extra_dom))
    out = []
    for d in doms:
        nd = per_dom + (d in bonus_dom)
        base, extra = divmod(nd, 3)
        bonus_t = set(rng.sample([1, 2, 3], extra))
        for t in (1, 2, 3):
            out += rng.sample(cells[(d, t)], base + (t in bonus_t))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bankdir"); ap.add_argument("outdir"); ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--n", type=int, default=50, help="items per reviewer, a stratified random sample of the bank")
    a = ap.parse_args()
    bank = stratified_sample(json.load(open(os.path.join(a.bankdir, "bank.json"))), a.n, a.seed)
    order = list(range(len(bank)))
    random.Random(a.seed).shuffle(order)
    os.makedirs(a.outdir, exist_ok=True)

    wb = Workbook(); info = wb.active; info.title = "Instructions"; ws = wb.create_sheet("Review")
    for line in INSTRUCTIONS:
        info.append([line])
    info.column_dimensions["A"].width = 100
    for r in info.iter_rows():
        r[0].alignment = Alignment(wrap_text=True, vertical="top")
    info["A1"].font = Font(bold=True, size=14)
    for r in info.iter_rows(min_row=2):
        if r[0].value and r[0].value.isupper():
            r[0].font = Font(bold=True)
    ws.append(["Row", "Question", "A", "B", "C", "Your answer (A/B/C)", "Comments (unclear, ambiguous, or more than one defensible answer)"])
    for c in ws[1]:
        c.font = Font(bold=True); c.alignment = Alignment(wrap_text=True, vertical="top")
    rows = []
    for n, i in enumerate(order, 1):
        it = bank[i]; row = f"r{n:03d}"
        ws.append([row, it["stem"], it["options"]["A"], it["options"]["B"], it["options"]["C"], None, None])
        gold = next(L for L, r in it["roles"].items() if r == "gold")
        rows.append([row, it["item_id"], gold, it["domain"], it["tier"]])
    for col, w in zip("ABCDEFG", (7, 90, 16, 16, 16, 14, 40)):
        ws.column_dimensions[col].width = w
    for r in ws.iter_rows(min_row=2):
        for c in r:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    dv = DataValidation(type="list", formula1='"A,B,C"', allow_blank=True); ws.add_data_validation(dv); dv.add(f"F2:F{len(bank) + 1}")
    ws.freeze_panes = "A2"
    for sh in (info, ws):
        sh.page_setup.orientation = "landscape"; sh.page_setup.fitToWidth = 1; sh.page_setup.fitToHeight = 0
        sh.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.print_title_rows = "1:1"
    wb.save(os.path.join(a.outdir, "reviewer_sheet.xlsx"))
    with open(os.path.join(a.outdir, "key_and_map.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["row", "item_id", "gold_letter", "domain", "tier"]); w.writerows(rows)
    print(len(bank), "rows written to", a.outdir)


if __name__ == "__main__":
    main()
