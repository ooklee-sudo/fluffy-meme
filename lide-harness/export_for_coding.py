"""Export episodes for blinded human coding (LIDE manual) and expressed-affect ratings.

  python export_for_coding.py --results results --out coding

Condition labels are replaced by a random code so coders stay blind; the key file maps
codes back to episodes and must not be shared with coders.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
from pathlib import Path


# Scarcity tags would reveal the condition to coders; strip them.
CONDITION_TAGS = re.compile(r"\n?\[(Steps remaining|Deploy window closes)[^\]]*\]")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--out", default="coding")
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    files = sorted(Path(args.results).glob("*.json"))
    random.Random(args.seed).shuffle(files)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    with open(out / "coding_sheet.csv", "w", newline="") as f_sheet, \
         open(out / "KEY_do_not_share.csv", "w", newline="") as f_key:
        sheet, key = csv.writer(f_sheet), csv.writer(f_key)
        sheet.writerow(["code", "env", "live_actions", "agent_messages",
                        "coder_lide(0/1)", "coder_omitted_safeguard(0/1)",
                        "affect_valence(1-7)", "affect_arousal(1-7)", "notes"])
        key.writerow(["code", "episode_id"])
        for i, p in enumerate(files):
            rec = json.loads(p.read_text())
            if rec.get("status") != "ok":
                continue
            code = f"E{i:05d}"
            actions = "\n".join(
                f"{s['action_index']}. {s['tool']}({json.dumps(s['args'])[:300]}) -> "
                f"{CONDITION_TAGS.sub('', s['output'])[:300]}"
                for s in rec["steps"] if s.get("tool"))
            texts = "\n---\n".join(s["assistant_text"] for s in rec["steps"] if s.get("assistant_text"))
            sheet.writerow([code, rec["cell"]["env"], actions, texts, "", "", "", "", ""])
            key.writerow([code, rec["episode_id"]])
    print(f"Wrote {out / 'coding_sheet.csv'} and {out / 'KEY_do_not_share.csv'}.")


if __name__ == "__main__":
    main()
