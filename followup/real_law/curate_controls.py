"""Curate the control provisions of real_fact_bank.json after reading all 90 of them.
Removed (24): prompts that start inside a quotation of substituted words (6), ambiguous openings such as 'the amount of [one] week' (7),
near-duplicates of another control (7), and four others with unclear antecedents. Input: real_fact_bank.json; output: real_fact_bank_v2.json."""
import json
bank = json.load(open("real_fact_bank.json"))
ctl = [f for f in bank if f["kind"] == "control"]
REMOVE = {0, 1, 2, 3, 8, 9, 12, 20, 21, 25, 30, 31, 35, 45, 48, 63, 64, 69, 70, 74, 77, 79, 85, 89}
removed = {ctl[i]["id"] for i in REMOVE}
out = [f for f in bank if f["id"] not in removed]
json.dump(out, open("real_fact_bank_v2.json", "w"), indent=1)
json.dump(sorted(removed), open("removed_controls.json", "w"))
print("removed", len(removed), "-> controls kept", sum(f["kind"] == "control" for f in out), "changed kept", sum(f["kind"] == "changed" for f in out), "total", len(out))
