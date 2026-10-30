"""Pilot step 1: sample pre-ChatGPT SO questions (accepted answer, score>=5) per tag via the SE API."""
import json, random, sys, time, urllib.parse, urllib.request, gzip, html, re

TAGS = ["python","javascript","java","c++","sql","git","pandas","regex","bash","css"]
PER_TAG = 15
FROM, TO = 1546300800, 1669766400  # 2019-01-01 .. 2022-11-30
random.seed(0)

def get(path, **p):
    p["site"] = "stackoverflow"
    url = "https://api.stackexchange.com/2.3/" + path + "?" + urllib.parse.urlencode(p)
    with urllib.request.urlopen(url) as r:
        data = r.read()
    try: data = gzip.decompress(data)
    except OSError: pass
    d = json.loads(data)
    if "backoff" in d: time.sleep(d["backoff"])
    return d

def strip(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

out = []
for tag in TAGS:
    d = get("search/advanced", tagged=tag, accepted="True", answers=1, min=5, sort="votes", order="desc",
            fromdate=FROM, todate=TO, pagesize=100, filter="withbody")
    qs = [q for q in d["items"] if len(q["body"]) < 3000]
    qs = random.sample(qs, min(PER_TAG, len(qs)))
    ids = ";".join(str(q["accepted_answer_id"]) for q in qs)
    ans = {a["answer_id"]: a for a in get(f"answers/{ids}", pagesize=100, filter="withbody")["items"]}
    for q in qs:
        a = ans.get(q["accepted_answer_id"])
        if a:
            out.append(dict(tag=tag, qid=q["question_id"], title=html.unescape(q["title"]),
                            question=q["body"], accepted=a["body"], created=q["creation_date"]))
    print(tag, len([o for o in out if o["tag"]==tag]), "quota_remaining", d.get("quota_remaining"), flush=True)
    time.sleep(1)
json.dump(out, open("questions.json","w"), ensure_ascii=False)
print("total", len(out))
