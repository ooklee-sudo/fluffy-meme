"""Excel coding form for human HBM coders, and export back to a coding-sheet CSV.

create   Build an .xlsx from coding_sheet_blank.csv (written by collect_reddit.py). Each unit gets three
         claim rows (C1-C3); every code has a drop-down list; a 'check' column flags inconsistent rows
         (e.g. presence 0 with an intensity set). Unit-level codes (A1, Layer C, more_claims) go on the
         C1 row only. A second sheet is a one-page codebook reference.
export   Read a filled form and write a CSV in the codebook's column layout, ready for reliability.py.
         Empty C2/C3 rows are dropped, unit-level codes are copied onto every claim row, units coded
         A1 = 0 become a single row with no claim id (as pipeline.py writes them), and out-of-range
         values are reported with their cell address.

    python coding_form.py create data/reddit/coding_sheet_blank.csv --round pilot1 --out coding/pilot1_coder1.xlsx
    python coding_form.py export coding/pilot1_coder1.xlsx --coder coder1 --out coding/pilot1_coder1.csv
    python reliability.py coding/pilot1_coder1.csv coding/pilot1_coder2.csv

Requires openpyxl (python -m pip install openpyxl).
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from codebook import BEHAVIOR_CATS, CLAIM_TYPES, CONSTRUCT_NAMES, CONSTRUCTS, CUES

CONTEXT = ["unit_id", "round", "subreddit", "unit_type", "permalink", "text", "parent_text"]
UNIT_LEVEL = ["A1_health_claim"] + CUES + ["more_claims"]
CLAIM_LEVEL = ["claim_id", "A2_claim_type", "A3_target_behavior", "A3_category", "A4_recommended_care",
               "A5_personal_experience"]
for _b in CONSTRUCTS:
    CLAIM_LEVEL += [f"{_b}_pres", f"{_b}_dir", f"{_b}_int"] + ([f"{_b}_object"] if _b in ("B3", "B4") else [])
NOTES = ["rule_applied", "memo"]
FORM_COLS = CONTEXT + ["A1_health_claim"] + CLAIM_LEVEL + CUES + ["more_claims"] + NOTES + ["check"]

CHOICES = {"A1_health_claim": [0, 1], "more_claims": [0, 1], "A5_personal_experience": [0, 1],
           "A2_claim_type": CLAIM_TYPES, "A3_category": BEHAVIOR_CATS, "rule_applied": list(range(1, 9))}
for _b in CONSTRUCTS:
    CHOICES[f"{_b}_pres"], CHOICES[f"{_b}_dir"], CHOICES[f"{_b}_int"] = [0, 1], [-1, 0, 1], [0, 1, 2, 3]
    if _b in ("B3", "B4"):
        CHOICES[f"{_b}_object"] = ["recommended_care", "alternative"]
for _c in CUES:
    CHOICES[_c] = [0, 1]

WIDTH = {"unit_id": 12, "round": 7, "subreddit": 12, "unit_type": 10, "permalink": 14, "text": 70,
         "parent_text": 40, "A3_target_behavior": 24, "A4_recommended_care": 26, "A2_claim_type": 15,
         "A3_category": 11, "memo": 30, "check": 28}
HEAD = PatternFill("solid", fgColor="DDE4EE")
UNIT_FILL = PatternFill("solid", fgColor="FFF7E0")   # unit-level codes
GREY = PatternFill("solid", fgColor="F2F2F2")        # not used on C2/C3 rows
FLAG = PatternFill("solid", fgColor="F8D0D0")

REFERENCE = [
    ("A1_health_claim", "1 = the unit asserts something checkable about health causes, treatment, prevention, risk or outcome"),
    ("claim rows", "Code up to 3 claims (C1-C3). Leave C2/C3 empty if there is only one claim. more_claims = 1 if there were more."),
    ("A3_target_behavior", "The health action the claim pushes the reader toward"),
    ("A4_recommended_care", "What current guidance recommends; for treatable conditions, that care (e.g. see a dentist). 'unclear' only if none applies."),
    ("*_pres", "0 absent, 1 present (explicit or clearly implied)"),
    ("*_dir", "+1 toward recommended care, -1 away from it, 0 neutral/unclear (0 whenever A4 is unclear)"),
    ("*_int", "0 absent, 1 passing mention, 2 argued or repeated, 3 central / absolutes / vivid detail"),
] + [(f"{b} {CONSTRUCT_NAMES[b]}", d) for b, d in [
    ("B1", "how likely the reader is to have/develop the condition"),
    ("B2", "how serious the condition or its consequences are"),
    ("B3", "gains promised from a behavior; object = whose benefits"),
    ("B4", "costs, risks, distrust, difficulty of a behavior; object = whose barriers"),
    ("B5", "call to act now, deadline, testimony as model, link/DM to buy"),
    ("B6", "reader can manage alone/easily, or cannot cope with treatment")]] + [
    ("C1-C6", "C1 authority, C2 testimony, C3 emotional appeal, C4 conspiracy/distrust, C5 social proof, C6 evidence offered"),
    ("rule_applied", "Number of the decision rule used (codebook Section 7), if any"),
    ("check", "Turns red when a row is inconsistent; fix before exporting"),
]


def _read_blank(path: str) -> list[dict]:
    for enc in ("utf-8-sig", "cp949"):
        try:
            with open(path, newline="", encoding=enc) as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    sys.exit(f"cannot decode {path}")


def create(a):
    units = [u for u in _read_blank(a.blank) if not a.round or u.get("round") == a.round]
    if not units:
        sys.exit("no units (check --round)")
    wb = Workbook()
    ws = wb.active
    ws.title = "Coding"
    col = {name: i + 1 for i, name in enumerate(FORM_COLS)}
    L = {name: get_column_letter(i) for name, i in col.items()}
    for name, i in col.items():
        c = ws.cell(row=1, column=i, value=name)
        c.font, c.fill = Font(bold=True), HEAD
        c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.column_dimensions[L[name]].width = WIDTH.get(name, 9)
    ws.row_dimensions[1].height = 45

    row = 2
    for u in units:
        for k in (1, 2, 3):
            ws.cell(row=row, column=col["unit_id"], value=u["unit_id"])
            ws.cell(row=row, column=col["claim_id"], value=f"C{k}")
            if k == 1:
                for name in ("round", "subreddit", "unit_type", "text", "parent_text"):
                    ws.cell(row=row, column=col[name], value=u.get(name, ""))
                if u.get("permalink"):
                    c = ws.cell(row=row, column=col["permalink"], value="open")
                    c.hyperlink, c.font = u["permalink"], Font(color="0563C1", underline="single")
                for name in UNIT_LEVEL:
                    ws.cell(row=row, column=col[name]).fill = UNIT_FILL
                lines = max(len(u.get("text", "")) / 85, len(u.get("parent_text", "")) / 48, 1)
                ws.row_dimensions[row].height = min(400, 15 * lines + 6)
            else:
                for name in CONTEXT[1:] + UNIT_LEVEL:
                    ws.cell(row=row, column=col[name]).fill = GREY
            wrap = {"text", "parent_text", "A3_target_behavior", "A4_recommended_care", "memo", "check"}
            for name, i in col.items():  # top-align so ids and codes sit next to the start of the text
                ws.cell(row=row, column=i).alignment = Alignment(wrap_text=name in wrap, vertical="top")
            row += 1
    last = row - 1

    for name, opts in CHOICES.items():
        dv = DataValidation(type="list", formula1='"' + ",".join(str(o) for o in opts) + '"', allow_blank=True,
                            showErrorMessage=True, errorTitle="Invalid code", error=f"Pick one of: {', '.join(map(str, opts))}")
        dv.add(f"{L[name]}2:{L[name]}{last}")
        ws.add_data_validation(dv)

    # Consistency check per row (presence vs intensity, A1 vs claims).
    for r in range(2, last + 1):
        parts = []
        for b in CONSTRUCTS:
            p, i = f"{L[b + '_pres']}{r}", f"{L[b + '_int']}{r}"
            parts.append(f'IF(AND({p}=0,{p}<>"",N({i})>0),"{b}: pres 0 but int>0; ","")')
            parts.append(f'IF(AND({p}=1,N({i})=0),"{b}: pres 1 needs int; ","")')
        parts.append(f'IF(AND({L["claim_id"]}{r}="C1",{L["A1_health_claim"]}{r}=1,{L["A2_claim_type"]}{r}=""),"A1=1 but C1 empty; ","")')
        ws.cell(row=r, column=col["check"], value="=" + "&".join(parts))
    ws.conditional_formatting.add(f"{L['check']}2:{L['check']}{last}",
                                  FormulaRule(formula=[f'LEN({L["check"]}2)>0'], fill=FLAG))
    ws.freeze_panes = f"{L['A1_health_claim']}2"  # unit columns and text stay visible while scrolling
    ws.auto_filter.ref = f"A1:{L['check']}{last}"

    ref = wb.create_sheet("Codebook")
    ref.column_dimensions["A"].width, ref.column_dimensions["B"].width = 26, 110
    ref.append(["Code", "Meaning"])
    for c in ref[1]:
        c.font, c.fill = Font(bold=True), HEAD
    for k, v in REFERENCE:
        ref.append([k, v])
    for r in ref.iter_rows(min_row=2):
        r[1].alignment = Alignment(wrap_text=True)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    wb.save(a.out)
    print(f"wrote {a.out}: {len(units)} units x 3 claim rows")


def _blank(v) -> bool:
    return v is None or str(v).strip() == ""


def _norm(v):
    """Excel returns 1.0 for 1; keep integers as ints and strip text."""
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v.strip() if isinstance(v, str) else v


def export(a):
    sys.path.insert(0, str(Path(__file__).parent))
    from pipeline import SHEET_COLS

    ws = load_workbook(a.form, data_only=True)["Coding"]
    header = [c.value for c in ws[1]]
    idx = {h: i for i, h in enumerate(header)}
    rows_by_unit: dict[str, list] = {}
    for excel_row, vals in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        rec = {h: _norm(vals[idx[h]]) for h in header if h in idx}
        rec["_row"] = excel_row
        rows_by_unit.setdefault(rec["unit_id"], []).append(rec)

    out_rows, problems, uncoded = [], [], 0
    for uid, recs in rows_by_unit.items():
        first = recs[0]
        unit = {k: first.get(k, "") for k in ("unit_id", "subreddit", "unit_type")}
        unit["coder_id"] = a.coder
        for k in UNIT_LEVEL:
            unit[k] = first.get(k)
        if _blank(unit["A1_health_claim"]):
            uncoded += 1
            continue
        for r in recs:  # range checks
            for k, opts in CHOICES.items():
                v = r.get(k)
                if not _blank(v) and v not in opts:
                    problems.append(f"{get_column_letter(idx[k] + 1)}{r['_row']} {k}={v!r} not in {opts}")
        if unit["A1_health_claim"] == 0:
            out_rows.append({**unit, "claim_id": "", "rule_applied": first.get("rule_applied"), "memo": first.get("memo")})
            continue
        for r in recs:
            if all(_blank(r.get(k)) for k in CLAIM_LEVEL if k != "claim_id"):
                continue  # unused C2/C3 row
            row = {**unit, **{k: r.get(k) for k in CLAIM_LEVEL + NOTES}}
            for b in CONSTRUCTS:  # an absent construct is 0/0/0 even if the coder left it blank
                if row.get(f"{b}_pres") in (0, None, ""):
                    for s in ("pres", "dir", "int"):
                        row[f"{b}_{s}"] = 0 if _blank(row.get(f"{b}_{s}")) else row[f"{b}_{s}"]
            out_rows.append(row)

    with open(a.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=SHEET_COLS, extrasaction="ignore")
        w.writeheader()
        for r in out_rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in SHEET_COLS})
    print(f"wrote {a.out}: {len(out_rows)} rows from {len(rows_by_unit) - uncoded} coded units"
          + (f"; {uncoded} units not coded yet (A1 empty) were skipped" if uncoded else ""))
    if problems:
        print(f"\n{len(problems)} out-of-range values:")
        for p in problems[:50]:
            print("  " + p)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("blank", help="coding_sheet_blank.csv from collect_reddit.py")
    c.add_argument("--round", default="", help="only units of this round, e.g. pilot1")
    c.add_argument("--out", required=True)
    e = sub.add_parser("export")
    e.add_argument("form")
    e.add_argument("--coder", required=True, help="coder id written to every row")
    e.add_argument("--out", required=True)
    a = ap.parse_args()
    create(a) if a.cmd == "create" else export(a)


if __name__ == "__main__":
    main()
