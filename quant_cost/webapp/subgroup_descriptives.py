"""Descriptive check of the incident effect within subgroups (no tests, no p-values).

  python quant_cost/webapp/subgroup_descriptives.py --prolific ~/prolific_export.csv --survey ~/study2_main_data/main_wide.csv \
         --out ~/study2_main_data/figures/subgroup_descriptives.md

For each subgroup (country of residence, frequency of AI use at work) it reports, by news condition, the number of analysable
participants, the mean of S and the mean of ln(WTP/L), and the difference (incident minus neutral). It also says whether the
difference has the same direction as in the preregistered hypotheses (S smaller and ln(WTP/L) larger in the incident condition).
Subgroups are small, so the numbers are descriptive and noisy. Prolific values that were withdrawn or have expired
(CONSENT_REVOKED, DATA_EXPIRED) are treated as missing. The output file contains aggregates only, no identifiers.
"""
import argparse

import pandas as pd

MISSING = {"CONSENT_REVOKED", "DATA_EXPIRED", "", "nan"}


def clean(s):
    return s.where(~s.astype(str).isin(MISSING))


def row(label, d):
    n = d.groupby("incident").size().reindex([0, 1]).fillna(0).astype(int)
    m_s = d.groupby("incident")["S"].mean().reindex([0, 1])
    m_w = d.groupby("incident")["meanLnWTPL"].mean().reindex([0, 1])
    ds, dw = m_s[1] - m_s[0], m_w[1] - m_w[0]
    small = "  (small cell)" if min(n[0], n[1]) < 15 else ""
    return {
        "subgroup": label + small, "n neutral": n[0], "n incident": n[1],
        "S neutral": m_s[0], "S incident": m_s[1], "difference in S": ds,
        "mean ln(WTP/L) neutral": m_w[0], "mean ln(WTP/L) incident": m_w[1], "difference in ln(WTP/L)": dw,
        "S direction as hypothesized": "yes" if ds < 0 else "no",
        "ln(WTP/L) direction as hypothesized": "yes" if dw > 0 else "no",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prolific", required=True)
    ap.add_argument("--survey", required=True, help="main_wide.csv from export_csv.py")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    pr = pd.read_csv(a.prolific).rename(columns={"Participant id": "pid"})
    sv = pd.read_csv(a.survey)
    sv = sv[(sv["completed"] == True) & (sv["eligible"] == True) & (sv["excluded"] == 0)]  # noqa: E712
    d = sv.merge(pr, on="pid", how="left")
    print(f"analysable participants: {len(sv)}; found in the Prolific file: {int(d['Status'].notna().sum())}")

    country = clean(d["Country of residence"])
    d["country_group"] = country.where(country.isin(["South Africa", "United Kingdom", "India"]), "Other countries")
    d.loc[country.isna(), "country_group"] = None
    d["sa_vs_other"] = country.map(lambda c: None if pd.isna(c) else ("South Africa" if c == "South Africa" else "All other countries"))
    ai = clean(d["Weekly ai (artificial intelligence) use at work"])
    d["ai_use"] = ai.map(lambda v: None if pd.isna(v) else ("Every day or more often" if v in ("Every day", "Multiple times every day") else "Less than daily"))

    rows = [row("All analysable participants", d)]
    for col, title in (("sa_vs_other", "Country"), ("country_group", "Country (four groups)"), ("ai_use", "AI use at work")):
        for g in sorted(d[col].dropna().unique()):
            rows.append(row(f"{title}: {g}", d[d[col] == g]))
    t = pd.DataFrame(rows)
    fmt = t.copy()
    for c in fmt.columns:
        if fmt[c].dtype.kind == "f":
            fmt[c] = fmt[c].map(lambda v: f"{v:.2f}")
    print(fmt.to_string(index=False))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write("| " + " | ".join(fmt.columns) + " |\n| " + " | ".join("---" for _ in fmt.columns) + " |\n")
            for _, r in fmt.iterrows():
                f.write("| " + " | ".join(str(v) for v in r.values) + " |\n")
        print("\nwritten to", a.out)


if __name__ == "__main__":
    main()
