"""Per-participant view of the pilot: exclusion flags and the C1 consistency pairs (IDs are masked).

  python quant_cost/webapp/pilot_flags.py --data-dir ~/study2_pilot_data
"""
import argparse
import glob
import json
import os
import statistics

from export_csv import build_row

FLAGS = ["ex_attention", "ex_comprehension", "ex_c1", "ex_straightline", "ex_speed"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.data_dir, "participants", "*.json")))
    data = []
    for p in files:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        data.append((d, build_row(d)))
    durs = [r["duration_s"] for d, r in data if d.get("completed") and d.get("eligible") and r.get("duration_s")]
    med = statistics.median(durs) if durs else None
    print("no  status      min   flags                         S1->C1_S1  S2->C1_S2")
    tot = {k: 0 for k in FLAGS}
    for i, (d, r) in enumerate(data, 1):
        r["ex_speed"] = int(med is not None and r.get("duration_s") is not None and r["duration_s"] < med / 3)
        ans = d.get("answers", {})
        status = "completed" if d.get("completed") else ("screenout" if d.get("screenedOut") else "partial")
        mins = f"{r['duration_s'] / 60:5.1f}" if r.get("duration_s") else "  n/a"
        fl = [k[3:] for k in FLAGS if r.get(k)]
        if status == "completed":
            for k in FLAGS:
                tot[k] += int(bool(r.get(k)))
        print(f"{i:<3} {status:<11} {mins}  {','.join(fl) or '-':<28} {ans.get('S1')}->{ans.get('C1_S1')}      {ans.get('S2')}->{ans.get('C1_S2')}")
    print("\ncompleters flagged:", {k[3:]: v for k, v in tot.items()})
    print("S1 = job function at the start, C1_S1 = same question at the end; S2 = level, C1_S2 = same at the end.")


if __name__ == "__main__":
    main()
