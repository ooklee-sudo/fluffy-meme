"""Crowd validation of the harm index H on Prolific (measurement + predictive validity).

Raters read Reddit health posts and answer five questions per post:
  claim      Does this post make a health claim? (Yes / No)
  direction  Does it encourage the reader toward or away from recommended medical care?
             (Away from medical care / Toward medical care / Neither)
  strength   How strongly? (1 = not at all ... 5 = very strongly)
  persuade   How persuasive is this post? (1-7)
  follow     If you had this condition, how likely would you be to follow this advice? (1-7)
The signed crowd score push = strength if "Away", -strength if "Toward", 0 if "Neither" is the
human counterpart of H.

Steps
  select     Pick posts from a pilot run, stratified by the LLM's H so the full range is rated, clean
             them (usernames and links removed), and split them into blocks of --per-person posts.
  qualtrics  Write a Qualtrics Advanced Format .txt (consent, instructions, one block per post set with an
             attention check, demographics). Import it, then add a Randomizer in Survey Flow that evenly
             presents 1 of the post blocks (instructions are printed).
  analyze    Read the Qualtrics CSV export, drop failed attention checks, and report inter-rater
             reliability and how well each pipeline run's H tracks the crowd.

    python prolific_survey.py select data/runs/pilot_large/results.jsonl --n 100 --per-person 20 --out survey/items.csv
    python prolific_survey.py qualtrics survey/items.csv --out survey/qualtrics_survey.txt
    python prolific_survey.py analyze survey/export.csv survey/items.csv \\
        --runs 7b=runs/pilot_v2/results.jsonl large=data/runs/pilot_large/results.jsonl
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import random
import re
import sys
from pathlib import Path

import numpy as np
from scipy import stats

DIRECTIONS = ["Away from medical care", "Toward medical care", "Neither"]
CHECK_ANSWER = "Toward medical care"   # instructed response in each block's attention check


# ---------------------------------------------------------------- select
def clean(text: str, max_words: int) -> str:
    text = re.sub(r"\bu/[A-Za-z0-9_-]+", "u/[user]", text)
    text = re.sub(r"https?://\S+", "[link]", text)
    text = re.sub(r"&#x200B;|&amp;", " ", text)
    words = text.split()
    return " ".join(words[:max_words]) + (" ..." if len(words) > max_words else "")


def select(a):
    recs = [json.loads(l) for l in open(a.results, encoding="utf-8") if l.strip()]
    usable = [r for r in recs if 15 <= len(r["text"].split()) and "[removed]" not in r["text"]
              and not r["text"].lower().startswith("your post has been removed")]
    rng = random.Random(a.seed)
    has_claim = lambda r: bool(r["coded"]["claims"])
    bins = {  # spread over H so the validity test sees the whole range
        "H>=0.33": [r for r in usable if r["H"] >= 0.33],
        "0<H<0.33": [r for r in usable if 0 < r["H"] < 0.33],
        "claim,H=0": [r for r in usable if r["H"] == 0 and has_claim(r)],
        "no-claim": [r for r in usable if not has_claim(r)],
    }
    share = {"H>=0.33": 0.25, "0<H<0.33": 0.25, "claim,H=0": 0.30, "no-claim": 0.20}
    chosen, short = [], 0
    for name, pool in bins.items():
        want = round(a.n * share[name]) + short
        take = rng.sample(pool, min(want, len(pool)))
        short = want - len(take)  # pass any shortfall to the next bin
        for r in take:
            r["_bin"] = name
        chosen += take
    if short:
        rest = [r for r in usable if r not in chosen]
        extra = rng.sample(rest, min(short, len(rest)))
        for r in extra:
            r["_bin"] = "fill"
        chosen += extra
    rng.shuffle(chosen)
    n = len(chosen) - len(chosen) % a.per_person
    chosen = chosen[:n]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "block", "unit_id", "stratum", "H_llm", "text", "context"])
        for k, r in enumerate(chosen):
            ctx = clean(r.get("parent_text", ""), 60) if r.get("unit_type") == "comment" else ""
            w.writerow([f"p{k + 1:03d}", k // a.per_person + 1, r["unit_id"], r["_bin"], r["H"],
                        clean(r["text"], a.max_words), ctx])
    counts = {b: sum(r["_bin"] == b for r in chosen) for b in list(bins) + ["fill"]}
    print(f"wrote {a.out}: {n} posts in {n // a.per_person} blocks of {a.per_person}; strata {counts}")


# ---------------------------------------------------------------- qualtrics
def _mc(qid: str, text: str, choices: list, horizontal: bool = False) -> str:
    kind = "MC:SingleAnswer:Horizontal" if horizontal else "MC:SingleAnswer:Vertical"
    return f"[[Question:{kind}]]\n[[ID:{qid}]]\n{text}\n[[Choices]]\n" + "\n".join(map(str, choices)) + "\n"


def qualtrics(a):
    items = list(csv.DictReader(open(a.items, encoding="utf-8-sig")))
    blocks = sorted({int(i["block"]) for i in items})
    consent = Path(a.consent_file).read_text(encoding="utf-8").strip() if a.consent_file else a.consent_text
    if "[" in consent and "]" in consent:
        print("warning: the consent text still contains [placeholders]; use --consent-file with the IRB-approved text\n")
    consent_html = "<br><br>".join(html.escape(p.strip()) for p in consent.split("\n\n") if p.strip())
    out = ["[[AdvancedFormat]]", "", "[[Block:Consent]]",
           "[[Question:Text]]\n[[ID:info]]\n" + consent_html.replace("\n", " ") + "\n",
           _mc("consent", "Do you agree to take part?", ["I agree", "I do not agree"]),
           "[[Question:TE:SingleLine]]\n[[ID:pid]]\nPlease enter your Prolific ID.\n",
           "[[Block:Instructions]]",
           "[[Question:Text]]\n[[ID:instructions]]\n"
           "You will read short posts from online health communities. Some posts are questions or personal "
           "stories; others give health advice. For each post, answer five quick questions. There are no right "
           "or wrong answers; we want your honest impression as a reader.<br><br>"
           "<b>Recommended medical care</b> means what doctors or official health guidelines would normally "
           "advise in that situation (for example seeing a dentist for a tooth infection, or following "
           "prescribed treatment). Healthy self-care that matches such advice counts as recommended care.\n"]
    for b in blocks:
        out.append(f"[[Block:Posts {b}]]")
        bi = [i for i in items if int(i["block"]) == b]
        check_at = len(bi) // 2
        for k, it in enumerate(bi):
            if k == check_at:  # instructed-response attention check mid-block
                out.append(_mc(f"b{b}_check", f"This is an attention check. Please select "
                               f"<b>{CHECK_ANSWER}</b> for this question.", DIRECTIONS))
                out.append("[[PageBreak]]")
            body = html.escape(it["text"]).replace("\n", "<br>")
            ctx = (f"<i>Replying to:</i> {html.escape(it['context'])}<br><br>" if it["context"] else "")
            q = it["item_id"]
            out.append(f"[[Question:Text]]\n[[ID:{q}_post]]\n<b>Post</b><br>{ctx}"
                       f"<div style='border:1px solid #ccc;padding:10px'>{body}</div>\n")
            out.append(_mc(f"{q}_claim", "Does this post make a health claim (state something as true about "
                           "a cause, treatment, prevention, risk or outcome)?", ["Yes", "No"], True))
            out.append(_mc(f"{q}_direction", "Does this post encourage the reader toward or away from recommended "
                           "medical care?", DIRECTIONS))
            out.append(_mc(f"{q}_strength", "How strongly does it encourage that? (1 = not at all, 5 = very strongly)",
                           [1, 2, 3, 4, 5], True))
            out.append(_mc(f"{q}_persuade", "How persuasive is this post? (1 = not at all, 7 = extremely)",
                           list(range(1, 8)), True))
            out.append(_mc(f"{q}_follow", "If you had this condition, how likely would you be to follow this "
                           "advice? (1 = very unlikely, 7 = very likely)", list(range(1, 8)), True))
            out.append("[[PageBreak]]")
    out += ["[[Block:About you]]",
            _mc("age", "Your age group", ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]),
            _mc("health_work", "Do you work or study in a health profession?", ["Yes", "No"], True),
            _mc("ohc_use", "How often do you read online health communities (e.g. Reddit health forums)?",
                ["Never", "Less than monthly", "Monthly", "Weekly", "Daily"])]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {a.out}: {len(items)} posts, {len(blocks)} post blocks\n")
    print("In Qualtrics: Create survey > Import from file (Advanced Format .txt). Then in Survey Flow:")
    print("  1. Add Embedded Data PROLIFIC_PID (set from the URL) at the top.")
    print(f"  2. Wrap the {len(blocks)} 'Posts' blocks in a Randomizer: present 1 element, 'Evenly Present Elements'.")
    print("  3. Branch: if consent = 'I do not agree' -> End of Survey.")
    print("  4. Set the end-of-survey redirect to your Prolific completion URL.")


# ---------------------------------------------------------------- analyze
def kripp_alpha_multi(units: list[list], level: str = "interval") -> float:
    """Krippendorff's alpha for any number of raters per unit (missing allowed); nominal or interval."""
    units = [[v for v in u if v is not None and not (isinstance(v, float) and np.isnan(v))] for u in units]
    units = [u for u in units if len(u) >= 2]
    vals = sorted({v for u in units for v in u})
    if len(vals) < 2:
        return float("nan")
    ix = {v: i for i, v in enumerate(vals)}
    o = np.zeros((len(vals), len(vals)))
    for u in units:
        m = len(u)
        for i in range(m):
            for j in range(m):
                if i != j:
                    o[ix[u[i]], ix[u[j]]] += 1 / (m - 1)
    n_c, n = o.sum(1), o.sum()
    if level == "nominal":
        delta = 1 - np.eye(len(vals))
    else:
        v = np.array(vals, dtype=float)
        delta = (v[:, None] - v[None, :]) ** 2
    d_o = (o * delta).sum() / n
    d_e = (np.outer(n_c, n_c) * delta).sum() / (n * (n - 1))
    return 1 - d_o / d_e if d_e else float("nan")


def read_qualtrics(path: str) -> list[dict]:
    """Qualtrics CSV export: row 1 = ids, rows 2-3 = labels/ImportIds; responses after."""
    rows = list(csv.reader(open(path, encoding="utf-8-sig")))
    head, data = rows[0], rows[1:]
    # Qualtrics adds a question-text row and an ImportId row under the header; drop through the ImportId row.
    for k, r in enumerate(data[:2]):
        if any(c.startswith('{"ImportId"') for c in r):
            data = data[k + 1:]
            break
    return [dict(zip(head, r)) for r in data]


def analyze(a):
    items = {i["item_id"]: i for i in csv.DictReader(open(a.items, encoding="utf-8-sig"))}
    resp = read_qualtrics(a.export)
    kept, dropped = [], 0
    for r in resp:
        if r.get("consent") not in ("I agree", "1"):
            continue
        checks = [v for k, v in r.items() if k.endswith("_check") and v]
        if any(v not in (CHECK_ANSWER, "2") for v in checks):
            dropped += 1
            continue
        kept.append(r)
    print(f"{len(resp)} responses, {len(kept)} kept, {dropped} failed the attention check\n")

    dir_code = {"Away from medical care": 1, "Toward medical care": -1, "Neither": 0, "1": 1, "2": -1, "3": 0}
    ratings = {q: {"claim": [], "push": [], "persuade": [], "follow": [], "dir": []} for q in items}
    for r in kept:
        for q in items:
            d = r.get(f"{q}_direction")
            if not d:
                continue
            s = float(r.get(f"{q}_strength") or 1)
            sign = dir_code.get(d, 0)
            ratings[q]["dir"].append(sign)
            ratings[q]["push"].append(sign * s if sign else 0.0)
            ratings[q]["claim"].append(1 if r.get(f"{q}_claim") in ("Yes", "1") else 0)
            for k in ("persuade", "follow"):
                if r.get(f"{q}_{k}"):
                    ratings[q][k].append(float(r[f"{q}_{k}"]))
    rated = [q for q in items if ratings[q]["push"]]
    per_item = [len(ratings[q]["push"]) for q in rated]
    print(f"{len(rated)} posts rated, raters per post: median {np.median(per_item):.0f} "
          f"(min {min(per_item)}, max {max(per_item)})\n")

    print("Inter-rater reliability (Krippendorff's alpha across crowd raters)")
    for k, lvl in (("claim", "nominal"), ("dir", "nominal"), ("push", "interval"),
                   ("persuade", "interval"), ("follow", "interval")):
        print(f"  {k:<9} {kripp_alpha_multi([ratings[q][k] for q in rated], lvl):.2f}  ({lvl})")

    crowd_push = np.array([np.mean(ratings[q]["push"]) for q in rated])
    crowd_follow = np.array([np.mean(ratings[q]["follow"]) if ratings[q]["follow"] else np.nan for q in rated])
    crowd_claim = np.array([np.mean(ratings[q]["claim"]) for q in rated])
    print("\nValidity of each run's H against the crowd (per post)")
    print(f"  {'run':<8} {'r(H, push)':>11} {'rho':>6} {'r(H, follow)':>13} {'claim agree':>12}")
    for spec in a.runs:
        name, path = spec.split("=", 1)
        R = {json.loads(l)["unit_id"]: json.loads(l) for l in open(path, encoding="utf-8") if l.strip()}
        H = np.array([R[items[q]["unit_id"]]["H"] if items[q]["unit_id"] in R else np.nan for q in rated])
        has = np.array([bool(R[items[q]["unit_id"]]["coded"]["claims"]) if items[q]["unit_id"] in R else False
                        for q in rated])
        ok = ~np.isnan(H)
        r1 = stats.pearsonr(H[ok], crowd_push[ok]).statistic if H[ok].std() else float("nan")
        rho = stats.spearmanr(H[ok], crowd_push[ok]).statistic if H[ok].std() else float("nan")
        okf = ok & ~np.isnan(crowd_follow)
        r2 = stats.pearsonr(H[okf], crowd_follow[okf]).statistic if H[okf].std() else float("nan")
        agree = np.mean(has[ok] == (crowd_claim[ok] >= 0.5))
        print(f"  {name:<8} {r1:>11.2f} {rho:>6.2f} {r2:>13.2f} {agree:>12.0%}")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "unit_id", "n_raters", "crowd_claim", "crowd_push", "crowd_persuade", "crowd_follow"])
        for q in rated:
            g = ratings[q]
            w.writerow([q, items[q]["unit_id"], len(g["push"]), round(np.mean(g["claim"]), 3),
                        round(np.mean(g["push"]), 3), round(np.mean(g["persuade"]), 3) if g["persuade"] else "",
                        round(np.mean(g["follow"]), 3) if g["follow"] else ""])
    print(f"\nwrote per-post crowd scores to {out}")


def main():
    sys.stdout.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select")
    s.add_argument("results", help="results.jsonl of a pilot run (its H is used to stratify)")
    s.add_argument("--n", type=int, default=100)
    s.add_argument("--per-person", type=int, default=20)
    s.add_argument("--max-words", type=int, default=150)
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--out", default="survey/items.csv")
    q = sub.add_parser("qualtrics")
    q.add_argument("items")
    q.add_argument("--out", default="survey/qualtrics_survey.txt")
    q.add_argument("--consent-file", help="text file with the IRB-approved consent wording (paragraphs separated by blank lines)")
    q.add_argument("--consent-text", default=(
        "This study is run by researchers at [institution]. You will read about 20 short public posts from online "
        "health communities and answer questions about them. It takes about 20 minutes. Some posts mention illness "
        "or treatments. Posts are not medical advice; please consult a health professional about your own health. "
        "Participation is voluntary and you may stop at any time. Responses are anonymous. Contact: [email]. "
        "IRB approval: [number]."))
    n = sub.add_parser("analyze")
    n.add_argument("export", help="Qualtrics CSV export (choice text or numeric values)")
    n.add_argument("items")
    n.add_argument("--runs", nargs="+", required=True, help="name=path/to/results.jsonl")
    n.add_argument("--out", default="survey/crowd_scores.csv")
    a = ap.parse_args()
    {"select": select, "qualtrics": qualtrics, "analyze": analyze}[a.cmd](a)


if __name__ == "__main__":
    main()
