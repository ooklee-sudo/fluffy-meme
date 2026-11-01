"""Collect public status-page incident histories (Atlassian Statuspage-compatible JSON) and
aggregate to weekly counts. Merges with any existing CSV, so running it regularly (or from a
machine that can reach the Wayback Machine, see --wayback) builds a longer history.

  python collect_status.py anthropic=https://status.claude.com openai=https://status.openai.com --out data_status
Writes <out>/<vendor>_incidents.csv (id, created_at, impact, name) and <vendor>_weekly.csv.
Note: the live endpoint returns only the most recent ~25-50 incidents.
--wayback  also pulls archived copies of <base>/api/v2/incidents.json to backfill (needs
           web.archive.org access; blocked in the cloud sandbox used to write this).
"""
import argparse, csv, json, os, re
from collections import Counter
from datetime import date, datetime
import requests


def fetch(url):
    r = requests.get(url, timeout=60); r.raise_for_status(); return r.json().get("incidents", [])


def wayback_urls(base, limit=200):
    q = ("https://web.archive.org/cdx/search/cdx?url=" + re.sub(r"^https?://", "", base) +
         "/api/v2/incidents.json&output=json&fl=timestamp&filter=statuscode:200&collapse=timestamp:8&limit=%d" % limit)
    rows = requests.get(q, timeout=120).json()[1:]
    return [f"https://web.archive.org/web/{t[0]}id_/{base}/api/v2/incidents.json" for t in rows]


def week(ts):
    y, w, _ = datetime.fromisoformat(ts.replace("Z", "+00:00")).isocalendar()
    return f"{y}-W{w:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vendors", nargs="+", help="name=https://status.example.com")
    ap.add_argument("--out", default="data_status"); ap.add_argument("--wayback", action="store_true")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for spec in a.vendors:
        name, base = spec.split("=", 1); base = base.rstrip("/")
        path = os.path.join(a.out, f"{name}_incidents.csv")
        seen = {}
        if os.path.exists(path):
            for r in csv.DictReader(open(path, encoding="utf8")): seen[r["id"]] = r
        urls = [base + "/api/v2/incidents.json"] + (wayback_urls(base) if a.wayback else [])
        for u in urls:
            try:
                for i in fetch(u):
                    seen[i["id"]] = dict(id=i["id"], created_at=i["created_at"], impact=i.get("impact", ""), name=i["name"])
            except Exception as e:
                print("skip", u, e)
        rows = sorted(seen.values(), key=lambda r: r["created_at"])
        with open(path, "w", newline="", encoding="utf8") as f:
            w = csv.DictWriter(f, fieldnames=["id", "created_at", "impact", "name"]); w.writeheader(); w.writerows(rows)
        c, maj = Counter(week(r["created_at"]) for r in rows), Counter(week(r["created_at"]) for r in rows if r["impact"] in ("major", "critical"))
        with open(os.path.join(a.out, f"{name}_weekly.csv"), "w", newline="") as f:
            wr = csv.writer(f); wr.writerow(["week", "incidents", "major"])
            for k in sorted(c): wr.writerow([k, c[k], maj[k]])
        print(name, len(rows), "incidents,", rows[0]["created_at"][:10], "->", rows[-1]["created_at"][:10])


if __name__ == "__main__":
    main()
