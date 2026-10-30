"""Feasibility check for the retraining-loop design: (a) per-tag question volume by half-year, (b) post-2025 questions with accepted answers."""
import json, time, urllib.parse, urllib.request, gzip, datetime as dt, re, html

TAGS = ["python","javascript","java","c++","sql","git","pandas","typescript"]

def get(path, **p):
    p["site"] = "stackoverflow"
    url = "https://api.stackexchange.com/2.3/" + path + "?" + urllib.parse.urlencode(p)
    for i in range(5):
        try:
            data = urllib.request.urlopen(url, timeout=60).read()
            try: data = gzip.decompress(data)
            except OSError: pass
            d = json.loads(data)
            if "backoff" in d: time.sleep(d["backoff"])
            return d
        except Exception as e:
            err = e; time.sleep(2 ** i)
    raise SystemExit(f"API failed: {err}")

ts = lambda y, m: int(dt.datetime(y, m, 1, tzinfo=dt.timezone.utc).timestamp())
periods = [(y, m) for y in range(2019, 2027) for m in (1, 7) if (y, m) <= (2026, 7)]
vol, quota = {}, None
for tag in TAGS:
    for (y, m) in periods:
        end = ts(y + (m == 7), 1 if m == 7 else 7)
        d = get("search/advanced", tagged=tag, fromdate=ts(y, m), todate=end, filter="total")
        vol[f"{tag}|{y}H{1 if m == 1 else 2}"] = d.get("total"); quota = d.get("quota_remaining")
    print(tag, "quota", quota, flush=True)
json.dump(vol, open("volume_v3.json", "w"))
print("\nhalf-year question counts (thousands)")
print("%-11s" % "tag", *["%5s" % f"{y%100}H{1 if m==1 else 2}" for y, m in periods])
for tag in TAGS:
    print("%-11s" % tag, *["%5.1f" % ((vol[f"{tag}|{y}H{1 if m==1 else 2}"] or 0) / 1000) for y, m in periods])

# (b) post-2025 questions with accepted answers, with version-like keywords
VER = re.compile(r"(python 3\.1[2-5]|react 19|next\.?js 1[45]|pandas (2\.[2-9]|3)|numpy 2|typescript 5\.[5-9]|java (2[1-9])|angular 1[89]|node(\.js)? 2[2-4])", re.I)
sample = []
for tag in ["python","javascript","typescript","pandas","java"]:
    d = get("search/advanced", tagged=tag, accepted="True", fromdate=ts(2025, 1), sort="votes", order="desc", pagesize=100, filter="withbody")
    items = d["items"]; hit = [q for q in items if VER.search(q["title"] + q["body"])]
    print(f"{tag}: post-2025 accepted-answer questions fetched {len(items)} (has_more={d.get('has_more')}), with version keyword {len(hit)}")
    sample += [dict(tag=tag, qid=q["question_id"], title=html.unescape(q["title"]), created=q["creation_date"]) for q in hit[:10]]
json.dump(sample, open("postcutoff_sample_v3.json", "w"), ensure_ascii=False)
print("quota", d.get("quota_remaining"))
for s in sample[:8]: print(s["tag"], dt.datetime.fromtimestamp(s["created"], dt.timezone.utc).date(), s["title"][:90])
