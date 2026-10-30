"""v2 sampling: top-50 tags, score band 3..20 (ceiling relief), random time windows, 40 q/tag, cached."""
import json, os, random, time, urllib.parse, urllib.request, gzip, html

PER_TAG, N_TAGS, LO, HI = 40, 50, 3, 20
FROM, TO = 1546300800, 1669766400  # 2019-01-01 .. 2022-11-30 (pre-ChatGPT)
random.seed(1)

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

tags = [t["name"] for t in get("tags", sort="popular", order="desc", pagesize=N_TAGS)["items"]]
qs = []
for tag in tags:
    pool = {}
    for _ in range(2):
        start = random.randint(FROM, TO - 365 * 86400)
        d = get("search/advanced", tagged=tag, accepted="True", min=LO, max=HI, sort="votes", order="desc",
                fromdate=start, todate=start + 365 * 86400, pagesize=100, filter="withbody")
        for q in d["items"]:
            if len(q["body"]) < 3500: pool[q["question_id"]] = q
        quota = d.get("quota_remaining")
    pick = random.sample(list(pool.values()), min(PER_TAG, len(pool)))
    for q in pick: q["_tag"] = tag
    qs += pick
    print(tag, len(pick), "quota", quota, flush=True)
    time.sleep(0.5)
ids = [q["accepted_answer_id"] for q in qs]
ans = {}
for i in range(0, len(ids), 100):
    d = get("answers/" + ";".join(map(str, ids[i:i + 100])), pagesize=100, filter="withbody")
    ans.update({a["answer_id"]: a for a in d["items"]})
out, seen = [], {}
for q in qs:
    a = ans.get(q["accepted_answer_id"])
    if not a: continue
    seen[q["_tag"]] = seen.get(q["_tag"], 0) + 1
    out.append(dict(tag=q["_tag"], rank=seen[q["_tag"]], qid=q["question_id"], title=html.unescape(q["title"]),
                    question=q["body"], accepted=a["body"], score=q["score"], created=q["creation_date"]))
json.dump(out, open("questions_v2.json", "w"), ensure_ascii=False)
print("total", len(out), "tags", len(seen))
