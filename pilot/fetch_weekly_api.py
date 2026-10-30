"""Weekly new-question counts per tag via the Stack Exchange API (2023-01-23 .. 2024-11-11, Monday weeks, UTC). Resumable.
Usage: fetch_weekly_api.py <key_file>"""
import json, sys, os, time, gzip, threading, urllib.parse, urllib.request, datetime as dt, concurrent.futures as cf
KEY = open(sys.argv[1]).read().strip(); OUT = "panel_api_tag_week.jsonl"
tags = list(dict.fromkeys(q["tag"] for q in json.load(open("questions_v2.json"))))
w0, w1 = dt.date(2023, 1, 23), dt.date(2024, 11, 11)
weeks = [w0 + dt.timedelta(7 * k) for k in range((w1 - w0).days // 7 + 1)]
done = set()
if os.path.exists(OUT):
    for l in open(OUT): x = json.loads(l); done.add((x["tag"], x["week"]))
jobs = [(t, w) for t in tags for w in weeks if (t, w.isoformat()) not in done]
lock = threading.Lock(); gate = threading.Lock(); state = {"next": 0.0, "quota": None}
def utc(d): return int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp())
def one(job):
    t, w = job
    p = dict(site="stackoverflow", tagged=t, fromdate=utc(w), todate=utc(w + dt.timedelta(7)) - 1, filter="total", key=KEY)
    url = "https://api.stackexchange.com/2.3/search/advanced?" + urllib.parse.urlencode(p)
    for i in range(6):
        with gate:                                  # global pacing ~8 req/s, honours backoff
            time.sleep(max(0, state["next"] - time.time())); state["next"] = time.time() + 0.12
        try:
            d = urllib.request.urlopen(url, timeout=60).read()
            try: d = gzip.decompress(d)
            except OSError: pass
            d = json.loads(d)
            if "backoff" in d:
                with gate: state["next"] = time.time() + d["backoff"]
            if "total" in d:
                with lock: open(OUT, "a").write(json.dumps(dict(tag=t, week=w.isoformat(), n=d["total"])) + "\n")
                return
            if d.get("error_id") in (502, 403, 429): time.sleep(5 * (i + 1))
        except Exception: time.sleep(2 ** i)
print("jobs", len(jobs), flush=True)
with cf.ThreadPoolExecutor(6) as ex: list(ex.map(one, jobs))
print("finished", flush=True)
