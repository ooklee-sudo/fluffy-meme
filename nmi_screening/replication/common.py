import json, os, re, time, urllib.request, urllib.error
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data"); os.makedirs(DATA, exist_ok=True)
UA = {"User-Agent": "screening-replication/0.1 (research; contact: see repository README)"}

def http(url, data=None, headers=None, timeout=60, tries=3, binary=False):
    h = dict(UA); h.update(headers or {})
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                b = r.read(); return b if binary else b.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (404, 403, 410): return None
            time.sleep(3 * (i + 1))
        except Exception:
            time.sleep(3 * (i + 1))
    return None

def words(t): return len(t.split())
