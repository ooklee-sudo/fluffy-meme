"""End-to-end prototype: screen -> HBM coding -> RAG veracity -> harm tier.

Input: JSONL, one unit per line:
    {"unit_id": "...", "subreddit": "...", "unit_type": "submission|comment",
     "parent_id": "", "parent_text": "", "text": "..."}

Outputs (in --out-dir):
    results.jsonl      full record per unit (codes, evidence, explanation, tier)
    coding_sheet.csv   one row per claim, same columns as the codebook's coding sheet,
                       so LLM codes can be compared with human codes (reliability.py)
    triage.csv         units ranked for moderators (tier, then H, then P)

Example:
    python pipeline.py examples/sample_posts.jsonl --kb data/kb_medlineplus.jsonl --out-dir runs/demo
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import codebook
import llm
from harm import TIER_NAMES, claim_harm, persuasiveness, tier
from veracity import VeracityJudge

# Stage 1 of the cascade. A cheap keyword screen stands in for the fine-tuned
# classifier planned for the full system; it only drops obviously non-medical units.
HEALTH_TERMS = re.compile(
    # Stems end in \w* so plurals and inflections match ("infections", "cured", "supplements").
    r"\b(cur\w*|heal\w*|treat\w*|therap\w*|chemo\w*|radiation|vaccin\w*|vax\w*|drugs?|medic\w*|meds|"
    r"dos(e|es|ing|age)|pills?|supplement\w*|vitamin\w*|mineral\w*|doctors?|oncolog\w*|symptom\w*|"
    r"cancer\w*|tumou?rs?|diabet\w*|insulin|metformin|statins?|blood|pressure|infect\w*|antibiotic\w*|"
    r"virus\w*|viral|bacteri\w*|parasit\w*|diseases?|diet\w*|fasting|detox\w*|side effects?|immun\w*|"
    r"pain\w*|surg\w*|inhalers?|asthma|tooth|teeth|gums?|dental|oils?|herb\w*|remed\w*|natural\w*|"
    r"holistic|homeopath\w*|ivermectin|probiotic\w*|hormon\w*|thyroid|liver|kidneys?|heart|cholesterol|"
    r"a1c|glucose|sugar|cbd|"
    r"inject\w*|needles?|mg|mcg|dexcom|cgm|libre|itch\w*|rash\w*|bumps?|lumps?|conditions?|"
    r"\w*olog(y|ist|ists)|lion'?s mane|nootropic\w*)\b"
    # Compounds such as "multivitamin" or "bulksupplements" have no word boundary before the stem.
    r"|\w*(vitamin|supplement)\w*"
    r"|\d+\s?(mg|mcg|iu|ml)\b", re.I)  # doses written as "1000mg" or "5 mcg"

SHEET_COLS = ["unit_id", "subreddit", "unit_type", "parent_id", "coder_id", "A1_health_claim", "claim_id",
              "A2_claim_type", "A3_target_behavior", "A3_category", "A4_recommended_care", "A5_personal_experience"]
for _b in codebook.CONSTRUCTS:
    SHEET_COLS += [f"{_b}_pres", f"{_b}_dir", f"{_b}_int"] + ([f"{_b}_object"] if _b in ("B3", "B4") else [])
SHEET_COLS += codebook.CUES + ["more_claims", "rule_applied", "memo"]


def process_unit(unit: dict, judge: VeracityJudge, use_retrieval: bool, screen: bool = True) -> dict:
    rec = {k: unit.get(k, "") for k in ("unit_id", "subreddit", "unit_type", "parent_id")}
    rec["text"] = unit["text"]
    if screen and not HEALTH_TERMS.search(unit["text"] + " " + unit.get("parent_text", "")):
        rec.update(stage="screened_out", coded={"A1_health_claim": 0, "claims": []}, tier=3, H=0.0, P=0.0)
        return rec
    try:
        coded = codebook.validate(llm.chat_json(codebook.SYSTEM,
                                                codebook.build_prompt(unit["text"], unit.get("parent_text") or None),
                                                max_tokens=3000))
        for cl in coded["claims"]:
            cl["H"] = round(claim_harm(cl), 3)
            v = judge.judge(cl["claim_text"], use_retrieval=use_retrieval)
            cl["veracity"] = v
            cl["tier"] = tier(v["label"], cl["H"])
    except Exception as e:  # noqa: BLE001 - one bad reply should not stop a long run
        # Failed units go to Review so a person looks at them; the error is kept in the memo.
        rec.update(stage=f"error: {e}"[:300], coded={"A1_health_claim": 0, "claims": []}, tier=2, H=0.0, P=0.0)
        return rec
    rec["stage"] = "coded"
    rec["coded"] = coded
    rec["H"] = max([c["H"] for c in coded["claims"]], default=0.0)
    rec["P"] = persuasiveness(coded)
    rec["tier"] = min([c["tier"] for c in coded["claims"]], default=3)
    return rec


def sheet_rows(rec: dict, coder_id: str) -> list[dict]:
    coded = rec["coded"]
    base = {k: rec.get(k, "") for k in ("unit_id", "subreddit", "unit_type", "parent_id")}
    base.update(coder_id=coder_id, A1_health_claim=coded.get("A1_health_claim", 0),
                more_claims=coded.get("more_claims", 0), rule_applied="", memo=rec.get("stage", ""))
    for c in codebook.CUES:
        base[c] = coded.get(c, 0)
    if not coded["claims"]:
        return [base]
    rows = []
    for cl in coded["claims"]:
        r = dict(base)
        for k in ("claim_id", "A2_claim_type", "A3_target_behavior", "A3_category", "A4_recommended_care",
                  "A5_personal_experience"):
            r[k] = cl[k]
        for b in codebook.CONSTRUCTS:
            r[f"{b}_pres"], r[f"{b}_dir"], r[f"{b}_int"] = cl[b]["pres"], cl[b]["dir"], cl[b]["int"]
            if b in ("B3", "B4"):
                r[f"{b}_object"] = cl[b].get("object", "")
        r["memo"] = cl.get("rationale", "")
        rows.append(r)
    return rows


def main():
    # Windows consoles (cp949 etc.) cannot show every character in Reddit text; never crash on print.
    sys.stdout.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--kb", default="data/kb_medlineplus.jsonl")
    ap.add_argument("--pubmed", action="store_true", help="also retrieve PubMed abstracts (needs internet)")
    ap.add_argument("--no-retrieval", action="store_true", help="ablation: veracity without evidence")
    ap.add_argument("--no-screen", action="store_true",
                    help="send every unit to the LLM (recommended for pilots; the keyword screen can miss claims)")
    ap.add_argument("--out-dir", default="runs/latest")
    ap.add_argument("--workers", type=int, default=2, help="parallel units (keep 1-2 for a local 8 GB GPU)")
    a = ap.parse_args()

    units = [json.loads(l) for l in Path(a.input).read_text(encoding="utf-8").splitlines() if l.strip()]
    judge = VeracityJudge(None if a.no_retrieval else a.kb, use_pubmed=a.pubmed)
    with ThreadPoolExecutor(a.workers) as ex:
        recs = list(ex.map(lambda u: process_unit(u, judge, not a.no_retrieval, not a.no_screen), units))

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "results.jsonl").open("w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (out / "coding_sheet.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=SHEET_COLS, extrasaction="ignore")
        w.writeheader()
        for r in recs:
            w.writerows(sheet_rows(r, f"llm:{llm.MODEL}"))
    ranked = sorted(recs, key=lambda r: (r["tier"], -r["H"], -r["P"]))
    with (out / "triage.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["rank", "tier", "unit_id", "H", "P", "veracity", "text"])
        for i, r in enumerate(ranked, 1):
            ver = status(r)
            w.writerow([i, TIER_NAMES[r["tier"]], r["unit_id"], f"{r['H']:.2f}", f"{r['P']:.2f}", ver,
                        r["text"][:160]])
    for i, r in enumerate(ranked, 1):
        print(f"{i:>3}. [{TIER_NAMES[r['tier']]:<7}] H={r['H']:.2f} P={r['P']:.2f} {status(r):<22} "
              f"{r['unit_id']}: {' '.join(r['text'].split())[:70]}")
    print(f"\ntiers: {dict(Counter(TIER_NAMES[r['tier']] for r in recs))}  "
          f"status: {dict(Counter(status(r).split(',')[0] if r['coded']['claims'] else status(r) for r in recs))}")
    print(f"wrote {out}/results.jsonl, coding_sheet.csv, triage.csv")


def status(r: dict) -> str:
    """Veracity labels of the claims, or why there are none."""
    if r["coded"]["claims"]:
        return ",".join(c["veracity"]["label"] for c in r["coded"]["claims"])
    if r["stage"].startswith("error"):
        return "ERROR"
    return "screened-out" if r["stage"] == "screened_out" else "no-claim"


if __name__ == "__main__":
    main()
