"""Download Reddit posts and comments, then draw a stratified pilot sample for HBM coding.

Data source: the Arctic Shift archive API (https://arctic-shift.photon-reddit.com), which serves
Reddit submissions and comments by subreddit and date. Check your IRB protocol and Reddit's
terms before collecting; outputs keep Reddit ids and permalinks but never usernames.

Steps
  1. Download: for each subreddit and month, fetch up to --per-month posts and comments. Items are
     taken after several random start times in the month, so the pool is spread over the month
     instead of piling up on its first days.
  2. Filter: drop removed/deleted text, bots, and texts shorter than --min-chars.
  3. Stratify: subreddit x unit type (submission/comment) x claim-likely (keyword screen).
     --enrich-share sets the share of each cell drawn from the claim-likely stratum, so the pilot
     is not mostly greetings and updates. Each unit carries its sampling weight (stratum pool size /
     stratum sample size) so later prevalence estimates can be re-weighted to the pool.
  4. Split into pilot rounds (codebook Section 8: Pilot 1 and Pilot 2, 100 units each).

Outputs in --out-dir
  raw/<subreddit>_<type>.jsonl   downloaded pool (cached; reused unless --refresh)
  sample.jsonl                   pipeline input (unit_id, subreddit, unit_type, parent_id, parent_text,
                                 text) plus stratum, weight, round, created_utc, permalink
  coding_sheet_blank.csv         one C1 row per unit in the codebook's column layout, with text and
                                 permalink for the coder (UTF-8 with BOM so Excel opens it cleanly)
  manifest.json                  parameters, pool and sample counts per stratum

Example
  python collect_reddit.py --subreddits AskDocs cancer diabetes Supplements AlternativeHealth \\
      --after 2024-01-01 --before 2025-01-01 --n 200 --out-dir data/reddit
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from pipeline import SHEET_COLS

API = "https://arctic-shift.photon-reddit.com/api"
UA = {"User-Agent": "hbm-misinfo-research/0.1"}
POST_FIELDS = "id,author,title,selftext,created_utc,score,num_comments,link_flair_text,author_flair_text"
COMMENT_FIELDS = "id,author,body,created_utc,score,link_id,parent_id,author_flair_text"
BOTS = {"automoderator", "[deleted]", "remindmebot", "sneakpeekbot"}
DROPPED = {"", "[removed]", "[deleted]", "[removed by reddit]"}

# Health terms that define the claim-likely stratum. Frozen on purpose: the pipeline's screening regex
# (pipeline.HEALTH_TERMS) keeps improving, but a sampling definition must not change after a sample has
# been drawn, or the same command would draw a different sample. Add a new version instead of editing.
STRATUM_HEALTH_TERMS = {
    "v1": re.compile(
        r"\b(cure|cured|treat|treatment|therapy|chemo|vaccine|vax|drug|medication|meds|dose|pill|supplement|"
        r"vitamin|doctor|oncologist|symptom|cancer|diabetes|insulin|metformin|statin|blood|pressure|infection|"
        r"antibiotic|virus|disease|diet|fasting|detox|heal|side effect|immune|pain|surgery|inhaler|asthma)\b", re.I),
}

# Advice and claim cues that, together with a health term, make a unit likely to hold a coded claim.
CLAIM_CUES = re.compile(
    r"\b(cures?|cured|heals?|healed|reverse[sd]?|works? (better|wonders)|instead of|natural(ly)?|detox|"
    r"stop(ped)? taking|quit|refused?|don'?t (take|need|bother)|never (take|trust)|you (should|need to|must|can)|"
    r"big pharma|doctors? (won'?t|don'?t|never)|side effects?|toxic|poison|proven|studies show|"
    r"i (stopped|quit|switched|tried|swear))\b", re.I)


def _get(url: str, retries: int = 5) -> dict:
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return json.loads(r.read())
        except Exception as e:  # noqa: BLE001 - 429s and timeouts: back off and retry
            err = e
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(f"Arctic Shift request failed: {url} ({err})")


def _ts(day: str) -> int:
    return int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _months(after: str, before: str):
    start, end = _ts(after), _ts(before)
    d = datetime.fromtimestamp(start, timezone.utc).replace(day=1)
    while d.timestamp() < end:
        nxt = d.replace(year=d.year + (d.month == 12), month=d.month % 12 + 1)
        yield max(start, int(d.timestamp())), min(end, int(nxt.timestamp()))
        d = nxt


def start_plan(after: str, before: str, starts: int, rng: random.Random) -> list[tuple[int, int, list[int]]]:
    """Random start times per month. Always drawn, even when the pool is cached, so the generator is
    in the same state when the sample is drawn and the same command always gives the same sample."""
    return [(lo, hi, sorted(rng.randrange(lo, hi) for _ in range(starts))) for lo, hi in _months(after, before)]


def download(sub: str, kind: str, plan: list, per_month: int, starts: int) -> list[dict]:
    """Pool for one subreddit and kind ('posts' or 'comments'), spread over the planned start times."""
    fields = POST_FIELDS if kind == "posts" else COMMENT_FIELDS
    per_req = max(1, min(100, per_month // starts))
    seen, out = set(), []
    for lo, hi, times in plan:
        for t in times:
            q = urllib.parse.urlencode({"subreddit": sub, "after": t, "before": hi, "limit": per_req,
                                        "sort": "asc", "fields": fields})
            for item in _get(f"{API}/{kind}/search?{q}").get("data", []):
                if item["id"] not in seen:
                    seen.add(item["id"])
                    out.append(item)
            time.sleep(0.3)  # be polite to a free, volunteer-run service
    return out


def clean(item: dict, kind: str, min_chars: int, max_chars: int) -> dict | None:
    if str(item.get("author", "")).lower() in BOTS or str(item.get("author", "")).lower().endswith("bot"):
        return None
    if kind == "posts":
        body = (item.get("selftext") or "").strip()
        if body in DROPPED:
            body = ""
        text = f"{item.get('title', '').strip()}\n\n{body}".strip()
        if not body:  # title-only or removed posts carry too little to code
            return None
    else:
        text = (item.get("body") or "").strip()
        if text in DROPPED:
            return None
    if len(text) < min_chars:
        return None
    rec = {k: v for k, v in item.items() if k != "author"}  # never keep usernames
    rec["text"] = text[:max_chars]
    return rec


def fetch_parents(comments: list[dict]) -> dict[str, str]:
    """Text of each sampled comment's parent (the post, or the comment it replies to)."""
    want = defaultdict(set)
    for c in comments:
        pid = c["parent_id"]
        want["posts" if pid.startswith("t3_") else "comments"].add(pid[3:])
    texts = {}
    for kind, ids in want.items():
        ids = sorted(ids)
        fields = "id,title,selftext" if kind == "posts" else "id,body"
        for k in range(0, len(ids), 100):
            q = urllib.parse.urlencode({"ids": ",".join(ids[k:k + 100]), "fields": fields})
            for it in _get(f"{API}/{kind}/ids?{q}").get("data", []):
                prefix = "t3_" if kind == "posts" else "t1_"
                t = f"{it.get('title', '')}\n\n{it.get('selftext', '')}".strip() if kind == "posts" else it.get("body", "")
                texts[prefix + it["id"]] = "" if t.strip() in DROPPED else t[:3000]
            time.sleep(0.3)
    return texts


def to_unit(rec: dict, kind: str, sub: str, health_terms: re.Pattern) -> dict:
    if kind == "posts":
        uid, link, parent = f"t3_{rec['id']}", rec["id"], ""
        permalink = f"https://www.reddit.com/r/{sub}/comments/{rec['id']}/"
    else:
        uid, link, parent = f"t1_{rec['id']}", rec["link_id"][3:], rec["parent_id"]
        permalink = f"https://www.reddit.com/r/{sub}/comments/{link}/_/{rec['id']}/"
    return {"unit_id": uid, "subreddit": sub, "unit_type": "submission" if kind == "posts" else "comment",
            "parent_id": parent, "parent_text": "", "text": rec["text"], "created_utc": rec["created_utc"],
            "author_flair": rec.get("author_flair_text") or "", "permalink": permalink,
            "claim_likely": int(bool(health_terms.search(rec["text"]) and CLAIM_CUES.search(rec["text"])))}


def allocate(total: int, keys: list) -> dict:
    """Split `total` as evenly as possible over keys."""
    base, extra = divmod(total, len(keys))
    return {k: base + (i < extra) for i, k in enumerate(keys)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subreddits", nargs="+", required=True)
    ap.add_argument("--after", required=True, help="YYYY-MM-DD, inclusive")
    ap.add_argument("--before", required=True, help="YYYY-MM-DD, exclusive")
    ap.add_argument("--n", type=int, default=200, help="total sample size")
    ap.add_argument("--rounds", type=int, default=2, help="pilot rounds the sample is split into")
    ap.add_argument("--comment-share", type=float, default=0.5)
    ap.add_argument("--enrich-share", type=float, default=0.5,
                    help="share of each cell drawn from claim-likely units (0 = simple random)")
    ap.add_argument("--per-month", type=int, default=200, help="pool size per subreddit, type and month")
    ap.add_argument("--starts", type=int, default=4, help="random start times per month")
    ap.add_argument("--min-chars", type=int, default=80)
    ap.add_argument("--max-chars", type=int, default=4000)
    ap.add_argument("--out-dir", default="data/reddit")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--strata-version", choices=sorted(STRATUM_HEALTH_TERMS), default="v1",
                    help="frozen definition of the claim-likely stratum (recorded in manifest.json)")
    ap.add_argument("--refresh", action="store_true", help="re-download even if raw files exist")
    a = ap.parse_args()

    rng = random.Random(a.seed)
    out = Path(a.out_dir)
    (out / "raw").mkdir(parents=True, exist_ok=True)

    # 1-2. Download (cached) and filter.
    pool = defaultdict(list)  # (sub, unit_type, claim_likely) -> units
    pool_counts = {}
    for sub in a.subreddits:
        for kind in ("posts", "comments"):
            raw = out / "raw" / f"{sub}_{kind}.jsonl"
            plan = start_plan(a.after, a.before, a.starts, rng)
            if raw.exists() and not a.refresh:
                items = [json.loads(l) for l in raw.read_text(encoding="utf-8").splitlines() if l.strip()]
            else:
                print(f"downloading r/{sub} {kind} {a.after}..{a.before}")
                items = [c for it in download(sub, kind, plan, a.per_month, a.starts)
                         if (c := clean(it, kind, a.min_chars, a.max_chars))]
                raw.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items), encoding="utf-8")
            units = [to_unit(i, kind, sub, STRATUM_HEALTH_TERMS[a.strata_version]) for i in items]
            for u in units:
                pool[(sub, u["unit_type"], u["claim_likely"])].append(u)
            pool_counts[f"{sub}/{kind}"] = len(units)
            print(f"  r/{sub} {kind}: {len(units)} usable units")

    # 3. Stratified draw.
    per_sub = allocate(a.n, a.subreddits)
    sample, strata = [], {}
    for sub in a.subreddits:
        n_com = round(per_sub[sub] * a.comment_share)
        for utype, n_cell in (("comment", n_com), ("submission", per_sub[sub] - n_com)):
            n_hi = round(n_cell * a.enrich_share)
            want = {1: n_hi, 0: n_cell - n_hi}
            # If one stratum is short, give its remainder to the other.
            for cl in (1, 0):
                short = want[cl] - len(pool[(sub, utype, cl)])
                if short > 0:
                    want[cl] -= short
                    want[1 - cl] += short
            for cl in (1, 0):
                units = pool[(sub, utype, cl)]
                k = min(want[cl], len(units))
                drawn = rng.sample(units, k)
                key = f"{sub}|{utype}|{'claim_likely' if cl else 'other'}"
                strata[key] = {"pool": len(units), "sample": k}
                for u in drawn:
                    u["stratum"] = key
                    u["weight"] = round(len(units) / k, 3)
                sample += drawn

    # 4. Pilot rounds: alternate within each stratum so every round has the same mix.
    by_stratum = defaultdict(list)
    for u in sample:
        by_stratum[u["stratum"]].append(u)
    offset = 0
    for key in sorted(by_stratum):
        for i, u in enumerate(sorted(by_stratum[key], key=lambda x: x["created_utc"])):
            u["round"] = f"pilot{(i + offset) % a.rounds + 1}"
        offset += len(by_stratum[key])

    comments = [u for u in sample if u["unit_type"] == "comment"]
    if comments:
        print(f"fetching parent text for {len(comments)} comments")
        parents = fetch_parents([{"parent_id": u["parent_id"]} for u in comments])
        for u in comments:
            u["parent_text"] = parents.get(u["parent_id"], "")

    rng.shuffle(sample)  # coders should not see units grouped by stratum
    sample.sort(key=lambda u: u["round"])
    with (out / "sample.jsonl").open("w", encoding="utf-8") as f:
        for u in sample:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")

    extra = ["round", "permalink", "text", "parent_text"]
    with (out / "coding_sheet_blank.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=SHEET_COLS + extra)
        w.writeheader()
        for u in sample:
            w.writerow({"unit_id": u["unit_id"], "subreddit": u["subreddit"], "unit_type": u["unit_type"],
                        "parent_id": u["parent_id"], "claim_id": "C1", "round": u["round"],
                        "permalink": u["permalink"], "text": u["text"], "parent_text": u["parent_text"]})

    manifest = {"created": datetime.now(timezone.utc).isoformat(timespec="seconds"), "source": API,
                "params": vars(a), "pool_counts": pool_counts, "strata": strata,
                "sample_size": len(sample), "rounds": dict(Counter(u["round"] for u in sample)),
                "by_type": dict(Counter(u["unit_type"] for u in sample)),
                "claim_likely": sum(u["claim_likely"] for u in sample)}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nsample: {len(sample)} units {manifest['rounds']} {manifest['by_type']}, "
          f"claim-likely {manifest['claim_likely']}")
    print(f"wrote {out}/sample.jsonl, coding_sheet_blank.csv, manifest.json")


if __name__ == "__main__":
    main()
