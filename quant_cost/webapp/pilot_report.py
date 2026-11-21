"""Pilot report: feasibility numbers from the stored responses (no hypothesis tests).

  python quant_cost/webapp/pilot_report.py --data-dir ~/study2_pilot_data

Prints: funnel (started, consented, eligible, completed), completion time, where people stopped, attention and
comprehension failures, willingness-to-pay (WTP) answer quality (identical answers, capped answers), and the
preregistered fallback rule for the WTP measure. Pilot data must not be used in any hypothesis test.
"""
import argparse
import glob
import json
import os
import statistics

from export_csv import build_row


def pct(a, b):
    return f"{100 * a / b:.0f}%" if b else "n/a"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
    a = ap.parse_args()
    raw = []
    for p in sorted(glob.glob(os.path.join(a.data_dir, "participants", "*.json"))):
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        if not str(d.get("pid", "")).upper().startswith("TEST"):
            raw.append(d)
    if not raw:
        print("no responses found in", a.data_dir)
        return
    rows = [build_row(d) for d in raw]
    n = len(raw)
    consented = [d for d in raw if d.get("answers", {}).get("consent") == 1]
    elig = [d for d in consented if d.get("eligible")]
    scr = [d for d in consented if d.get("screenedOut")]
    comp = [(d, r) for d, r in zip(raw, rows) if d.get("completed") and d.get("eligible")]

    print("=== Funnel ===")
    print(f"opened the survey: {n} | consented: {len(consented)} | eligible: {len(elig)} ({pct(len(elig), len(consented))}) | "
          f"screened out: {len(scr)} | completed: {len(comp)} ({pct(len(comp), len(elig))} of eligible)")

    print("\n=== Completion time (completers, minutes) ===")
    durs = sorted(r["duration_s"] / 60 for _, r in comp if r["duration_s"] is not None)
    if durs:
        print(f"median {statistics.median(durs):.1f} | mean {statistics.mean(durs):.1f} | min {durs[0]:.1f} | max {durs[-1]:.1f}"
              f"   (plan: about 19 minutes)")
        steps = {}
        for d, _ in comp:
            for k, v in d.get("timing", {}).items():
                steps.setdefault(k, []).append(v / 1000.0)
        slow = sorted(((statistics.median(v), k) for k, v in steps.items()), reverse=True)[:5]
        print("slowest pages (median seconds):", ", ".join(f"{k} {m:.0f}s" for m, k in slow))

    print("\n=== Where eligible participants stopped (not completed) ===")
    for d in elig:
        if not d.get("completed"):
            last = list(d.get("timing", {}).keys())[-1] if d.get("timing") else "(before first page)"
            print(f"  {d.get('pid')}: last finished page = {last}")
    if all(d.get("completed") for d in elig):
        print("  none")

    print("\n=== Quality flags among completers ===")
    m = len(comp)
    if m:
        att = sum(r["ex_attention"] for _, r in comp)
        compf = sum(r["ex_comprehension"] for _, r in comp)
        c1 = sum(r["ex_c1"] for _, r in comp)
        line = sum(r["ex_straightline"] for _, r in comp)
        print(f"failed an attention check: {att}/{m} ({pct(att, m)}) | wrong on >= 2 comprehension checks: {compf}/{m} ({pct(compf, m)})")
        print(f"job function/level differs between start and end (C1): {c1}/{m} | identical WTP and choice in all four scenarios: {line}/{m}")
        per = {}
        for _, r in comp:
            for c in ("C1", "C2", "C3", "C4"):
                if f"Q1_correct_{c}" in r:
                    per.setdefault(c, []).append(1 - r[f"Q1_correct_{c}"])
        print("comprehension check wrong rate by cell:", {c: pct(sum(v), len(v)) for c, v in per.items()})

        print("\n=== Willingness-to-pay (Q3) answers ===")
        same = capped = zeros = total = 0
        rel = []
        for d, r in comp:
            vals = [r.get(f"WTP_raw_{c}") for c in ("C1", "C2", "C3", "C4")]
            if all(v is not None for v in vals):
                total += 1
                same += len(set(vals)) == 1
            for c in ("C1", "C2", "C3", "C4"):
                v, s = r.get(f"WTP_raw_{c}"), d["scenarios"].get(c, {}).get("smax")
                if v is not None and s:
                    capped += v > s
                    zeros += v == 0
                    rel.append(v / s)
        print(f"identical WTP in all four scenarios: {same}/{total} ({pct(same, total)})")
        print(f"entries above the stated upper limit (would be capped): {capped}/{len(rel)} | entries equal to 0: {zeros}/{len(rel)}")
        if rel:
            print(f"WTP as a share of the upper limit: median {statistics.median(rel):.2f}")
        print("\n=== Preregistered fallback rule for WTP ===")
        fail2 = compf
        trig = (total and same / total >= 0.30) or (m and fail2 / m >= 0.30)
        print("rule: if >= 30% give identical WTP in all four scenarios or fail comprehension in >= 2 scenarios,")
        print("      the primary outcome for H2c becomes the choice-based sensitivity S_choice.")
        print(f"      identical WTP: {pct(same, total)} | comprehension failures (>=2): {pct(fail2, m)} -> "
              f"{'RULE TRIGGERED' if trig else 'not triggered'}")

        print("\n=== Policy and industry (S8, I1) among completers ===")
        s8 = {}
        for _, r in comp:
            s8[r.get("S8")] = s8.get(r.get("S8"), 0) + 1
        print("S8 (1 prohibited, 2 approval, 3 guidelines, 4 no policy, 5 unsure):", dict(sorted(s8.items(), key=lambda x: str(x[0]))))
    print("\nReminder: pilot responses are for feasibility only and are not used in any hypothesis test.")


if __name__ == "__main__":
    main()
