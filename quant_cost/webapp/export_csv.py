"""Flatten the stored responses into one wide CSV with the preregistered analysis variables and exclusion flags.

  python quant_cost/webapp/export_csv.py --data-dir quant_cost/webapp/data --out study2_wide.csv

One row per participant (completed and eligible by default; --all keeps everyone). Variables follow
preregistration_aspredicted (Study 2):
  lnWTPL_<cell>   ln(WTP / L); WTP above L/4 is set to L/4 (flag capped_<cell>); WTP = 0 is replaced by 0.001 L
  S               mean lnWTPL at lambda = 6% minus mean lnWTPL at lambda = 2%   (primary outcome, H2c)
  excess_<cell>   own probability estimate minus the stated probability (percentage points)
Exclusion flags are computed from preregistered rules and are NOT applied: filter on `excluded` in the analysis.
"""
import argparse
import csv
import glob
import json
import math
import os
import statistics
from datetime import datetime

NUMERACY_CORRECT = {"N1": 150, "N2": 100, "N3": 25}
CELLS = ["C1", "C2", "C3", "C4"]


def parse_time(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def ln_wtpl(raw, L, smax):
    if raw is None:
        return None, None
    used = min(max(raw, 0.0), smax)
    capped = raw > smax
    if used <= 0:
        used = 0.001 * L
    return math.log(used / L), capped


def build_row(d):
    a = d.get("answers", {})
    asg = d.get("assignment") or {}
    row = {
        "pid": d.get("pid"), "session": d.get("sessionId"), "completed": d.get("completed", False),
        "eligible": d.get("eligible"), "screenedOut": d.get("screenedOut", False), "declined": d.get("declined", False),
        "news": asg.get("news"), "incident": 1 if asg.get("news") == "incident" else (0 if asg.get("news") else None),
        "version": asg.get("version"), "order": "".join(str(x) for x in asg.get("order", [])),
        "assignmentSource": d.get("assignmentSource"),
    }
    for k in ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "GP", "R1", "P2", "I1", "I2", "I3",
              "E1", "E2", "E3", "N1", "N2", "N3", "AGE", "GENDER", "EDU", "EXP", "COUNTRY", "C1_S1", "C1_S2",
              "A1", "A2"]:
        row[k] = a.get(k)
    pc = a.get("PC") or []
    for i in range(4):
        row[f"PC{i + 1}"] = pc[i] if i < len(pc) else None
    p3 = a.get("P3") or []
    for i in range(3):
        row[f"P3_{i + 1}"] = p3[i] if i < len(p3) else None
    row["numeracy"] = sum(1 for k, v in NUMERACY_CORRECT.items() if a.get(k) is not None and abs(a[k] - v) < 1e-9)
    row["policy_prohibited"] = 1 if a.get("S8") == 1 else (0 if a.get("S8") is not None else None)

    sc = d.get("scenarios", {})
    ln = {"2": [], "6": []}
    choices, wtps, q1_wrong = [], [], 0
    for c in CELLS:
        r = sc.get(c)
        if not r:
            continue
        L, smax = r["L"], r["smax"]
        lw, capped = ln_wtpl(r.get("Q3_raw"), L, smax)
        row.update({
            f"pos_{c}": r["pos"], f"case_{c}": r["caseCode"], f"lam_{c}": r["lam"], f"perf_{c}": r["perf"],
            f"L_{c}": L, f"Q1_correct_{c}": int(bool(r["Q1_correct"])), f"local_{c}": 1 if r["Q2_choice"] == "local" else 0,
            f"WTP_raw_{c}": r.get("Q3_raw"), f"capped_{c}": None if capped is None else int(capped),
            f"lnWTPL_{c}": lw, f"Q4_{c}": r.get("Q4"), f"excess_{c}": (r["Q4"] - r["lam"]) if r.get("Q4") is not None else None,
            f"Q5_{c}": r.get("Q5"),
        })
        if lw is not None:
            ln[str(r["lam"])].append(lw)
        choices.append(r["Q2_choice"]); wtps.append(r.get("Q3_raw"))
        q1_wrong += 0 if r["Q1_correct"] else 1
    allln = ln["2"] + ln["6"]
    row["meanLnWTPL"] = statistics.mean(allln) if allln else None
    row["S"] = (statistics.mean(ln["6"]) - statistics.mean(ln["2"])) if ln["2"] and ln["6"] else None
    row["n_local"] = sum(1 for c in choices if c == "local")
    row["q1_wrong"] = q1_wrong
    t0, t1 = parse_time(d.get("startedAt", "")), parse_time(d.get("finishedAt", ""))
    row["duration_s"] = (t1 - t0).total_seconds() if t0 and t1 else None
    row["n_scenarios"] = len(choices)

    # preregistered exclusion flags
    row["ex_attention"] = int(a.get("A1_correct") is False or a.get("A2_correct") is False)
    row["ex_comprehension"] = int(q1_wrong >= 2)
    # C1: IT, data, and security functions (S1 = 1, 2, 3) count as one group; level (S2) must match exactly
    grp = lambda v: 1 if v in (1, 2, 3) else v
    row["ex_c1"] = int(a.get("C1_S1") is not None and (grp(a.get("C1_S1")) != grp(a.get("S1")) or a.get("C1_S2") != a.get("S2")))
    row["ex_straightline"] = int(len(choices) == 4 and len(set(choices)) == 1 and len(set(wtps)) == 1)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
    ap.add_argument("--out", default="study2_wide.csv")
    ap.add_argument("--all", action="store_true", help="keep incomplete, screened-out and declined participants")
    a = ap.parse_args()

    rows = []
    for p in sorted(glob.glob(os.path.join(a.data_dir, "participants", "*.json"))):
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        if str(d.get("pid", "")).upper().startswith("TEST"):
            continue  # Prolific preview and test sessions are not participants
        rows.append(build_row(d))
    kept = rows if a.all else [r for r in rows if r["completed"] and r["eligible"]]
    # the speed rule uses the median of eligible completers, whether or not --all keeps the other rows
    durs = [r["duration_s"] for r in rows if r["completed"] and r["eligible"] and r["duration_s"] is not None]
    med = statistics.median(durs) if durs else None
    for r in rows:
        r["ex_speed"] = int(med is not None and r["duration_s"] is not None and r["duration_s"] < med / 3)
        r["excluded"] = int(any(r[k] for k in ("ex_attention", "ex_comprehension", "ex_c1", "ex_straightline", "ex_speed")))
    cols = []
    for r in kept:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(kept)
    print(f"{len(rows)} files, {len(kept)} rows written to {a.out}; "
          f"median duration {med:.0f}s; excluded by preregistered rules: {sum(r['excluded'] for r in kept)}"
          f" (of which eligible completers: {sum(r['excluded'] for r in kept if r['completed'] and r['eligible'])})" if med is not None
          else f"{len(rows)} files, {len(kept)} rows written to {a.out}")


if __name__ == "__main__":
    main()
