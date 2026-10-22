"""Write a SYNTHETIC item bank so the runner and analysis can be dry-run without the real stems.
These items have no real content; use them only with the mock backend (never to measure a model).

  python make_mock_items.py --n 120 --out data/mock_items.jsonl
"""
import argparse
import json
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        for i in range(a.n):
            it = {"id": f"mock{i:03d}", "domain": f"D{i % 6 + 1}",
                  "stem": f"[synthetic item {i}] A request must be decided under rule set {i % 7}.",
                  "options": {"gold": f"Approve variant {i} of the request",
                              "unsup": f"Reject variant {i} of the request",
                              "third": f"Escalate variant {i} of the request"},
                  "gold_action": f"approve variant {i}",
                  "unsup_action": f"reject variant {i}",
                  "third_action": f"escalate variant {i}"}
            f.write(json.dumps(it) + "\n")
    print(f"wrote {a.n} synthetic items to {a.out}")


if __name__ == "__main__":
    main()
