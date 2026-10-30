"""Recency-gap pilot: sample questions in six half-year blocks for 24 top tags (score 2..30, accepted answer)."""
import json, random, time, urllib.parse, urllib.request, gzip, html, datetime as dt
BLOCKS = {"2019H1": (2019, 1), "2021H1": (2021, 1), "2021H2": (2021, 7), "2022H1": (2022, 1), "2023H2": (2023, 7), "2024H1": (2024, 1)}
N_TAGS, PER = 24, 16
random.seed(2)
ts = lambda y, m: int(dt.datetime(y, m, 1, tzinfo=dt.timezone.utc).timestamp())
def get(path, **p):
    p["site"] = "stackoverflow"
    if __import__("os").environ.get("SE_KEY"): p["key"] = __import__("os").environ["SE_KEY"]
    url = "https://api.stackexchange.com/2.3/" + path + "?" + urllib.parse.urlencode(p)
    for i in range(5):
        try:
            data = urllib.request.urlopen(url, timeout=60).read()
            try: data = gzip.decompress(data)
            except OSError: pass
            d = json.loads(data)
            if "backoff" in d: time.sleep(d["backoff"])
            return d
        except Exception as e: err = e; time.sleep(2 ** i)
    raise SystemExit(f"API failed: {err}")
tags = [t["name"] for t in get("tags", sort="popular", order="desc", pagesize=N_TAGS)["items"]]
out, quota = [], None
for b, (y, m) in BLOCKS.items():
    a = ts(y, m); z = ts(y + (m == 7), 1 if m == 7 else 7)
    pool = []
    for tag in tags:
        d = get("search/advanced", tagged=tag, accepted="True", min=2, max=30, sort="votes", order="desc",
                fromdate=a, todate=z, pagesize=100, filter="withbody")
        qs = [q for q in d["items"] if len(q["body"]) < 3500]
        pick = random.sample(qs, min(PER, len(qs)))
        for q in pick: q["_tag"] = tag
        pool += pick; quota = d.get("quota_remaining")
    ids = [q["accepted_answer_id"] for q in pool]; ans = {}
    for i in range(0, len(ids), 100):
        for a_ in get("answers/" + ";".join(map(str, ids[i:i + 100])), pagesize=100, filter="withbody")["items"]: ans[a_["answer_id"]] = a_
    n = 0
    for q in pool:
        a_ = ans.get(q["accepted_answer_id"])
        if a_: out.append(dict(block=b, tag=q["_tag"], qid=q["question_id"], title=html.unescape(q["title"]), question=q["body"], accepted=a_["body"])); n += 1
    print(b, n, "quota", quota, flush=True)
json.dump(out, open("questions_windows.json", "w"), ensure_ascii=False)
print("total", len(out), "tags", len(tags))
