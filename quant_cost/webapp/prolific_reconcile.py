"""Reconcile the Prolific demographic export with the survey data, and describe the analysable sample.

  python quant_cost/webapp/export_csv.py --data-dir ~/study2_main_data --out ~/study2_main_data/main_all.csv --all
  python quant_cost/webapp/prolific_reconcile.py --prolific ~/prolific_export.csv --survey ~/study2_main_data/main_all.csv \
         --out ~/study2_main_data/figures/sample_description.md

Part 1 (payment check): cross-tabulates the Prolific submission status with what the survey recorded and lists the
mismatches that need action (printed to the terminal only, never written to the output file).
Part 2 (description): demographics of the analysable sample (aggregates only, no identifiers). Prolific marks values
people withdrew or that expired as CONSENT_REVOKED / DATA_EXPIRED; they are treated as missing.
No hypothesis tests are run here.
"""
import argparse

import numpy as np
import pandas as pd

MISSING = {"CONSENT_REVOKED", "DATA_EXPIRED", "", "nan"}


def clean(s):
    return s.where(~s.astype(str).isin(MISSING))


def share(s, top=6):
    s = clean(s).dropna()
    vc = s.value_counts()
    n = len(s)
    parts = [f"{k} {v} ({100 * v / n:.0f}%)" for k, v in vc.head(top).items()]
    if len(vc) > top:
        rest = vc.iloc[top:].sum()
        parts.append(f"other {rest} ({100 * rest / n:.0f}%)")
    return "; ".join(parts) + f"  [n = {n}]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prolific", required=True)
    ap.add_argument("--survey", required=True, help="CSV from export_csv.py --all")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    pr = pd.read_csv(a.prolific)
    sv = pd.read_csv(a.survey)
    pr = pr.rename(columns={"Participant id": "pid"})
    sv = sv[~sv["pid"].astype(str).str.upper().str.startswith("TEST")]

    def state(r):
        if r["completed"] and r["eligible"]:
            return "survey: completed"
        if r["screenedOut"]:
            return "survey: screened out"
        if r["declined"]:
            return "survey: declined"
        return "survey: partial"

    sv = sv.assign(state=sv.apply(state, axis=1))
    m = pr.merge(sv[["pid", "state", "excluded"]], on="pid", how="outer", indicator=True)
    m["state"] = m["state"].fillna("no survey file")
    m["Status"] = m["Status"].fillna("not in Prolific export")

    print("=== Part 1. Prolific status by survey state ===")
    print(pd.crosstab(m["state"], m["Status"]).to_string())

    print("\n=== Needs action ===")
    a1 = m[(m["state"] == "survey: completed") & (m["Status"] != "APPROVED")]
    a2 = m[(m["state"] == "survey: screened out") & (m["Status"] == "REJECTED")]
    a3 = m[(m["Status"] == "APPROVED") & (m["state"] != "survey: completed")]
    for lab, d in [("Completed the survey but NOT approved on Prolific (approve or contact support)", a1),
                   ("Screened out but REJECTED on Prolific (rejection harms the participant; check Prolific's screen-out rules)", a2),
                   ("APPROVED on Prolific but no completed survey on file (investigate)", a3)]:
        print(f"\n{lab}: {len(d)}")
        for pid, st in zip(d["pid"], d["Status"]):
            print("   ", pid, st)

    print("\n=== Part 2. Analysable sample ===")
    an = m[(m["state"] == "survey: completed") & (m["excluded"] == 0)]
    lines = [f"Analysable participants found in the Prolific export: {len(an)}"]
    age = pd.to_numeric(clean(an["Age"]), errors="coerce").dropna()
    if len(age):
        lines.append(f"Age: mean {age.mean():.1f}, SD {age.std(ddof=1):.1f}, range {int(age.min())} to {int(age.max())}  [n = {len(age)}]")
    for col, lab in [("Sex", "Sex"), ("Country of residence", "Country of residence"), ("Ethnicity simplified", "Ethnicity (Prolific categories)"),
                     ("Employment status", "Employment status"), ("Student status", "Student status"),
                     ("Weekly ai (artificial intelligence) use at work", "Weekly AI use at work")]:
        if col in an:
            lines.append(f"{lab}: {share(an[col])}")
    miss = int((clean(an["Sex"]).isna()).sum()) if "Sex" in an else 0
    lines.append(f"Participants whose Prolific demographics are unavailable (withdrawn or expired): {miss}")
    print("\n".join(lines))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write("\n".join(f"- {x}" for x in lines) + "\n")
        print("\nsample description written to", a.out)


if __name__ == "__main__":
    main()
