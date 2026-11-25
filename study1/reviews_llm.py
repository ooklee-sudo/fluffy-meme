"""Study 1, step 4b: attribute-level sentiment from guest reviews with an LLM.

Usage: python reviews_llm.py REVIEWS_CSV OUT_JSONL MODEL [LIMIT=0] [WORKERS=24]
Each review is classified on four attributes: +1 positive, 0 neutral, -1 negative, null if not mentioned.
"""
import sys, os, json, time, threading, concurrent.futures as cf
import pandas as pd, requests

PROMPT = (
    "Below is a guest review of a short-term rental. For each attribute, say how the guest describes it: "
    "1 if positive, 0 if neutral or mixed, -1 if negative, or null if the review does not mention it.\n"
    "Attributes: cleanliness (clean, tidy, dirty); spaciousness (roomy, spacious, small, cramped); "
    "brightness (bright, light, dark, dim); furnishing_condition (condition, age and upkeep of furniture, fixtures and decor).\n"
    'Answer with JSON only, e.g. {"cleanliness":1,"spaciousness":null,"brightness":-1,"furnishing_condition":0}.\n\nReview:\n'
)

def call(model, text):
    body = {"model": model, "temperature": 0, "max_tokens": 300, "reasoning": {"enabled": False},
            "messages": [{"role": "user", "content": PROMPT + text[:1500]}]}
    for attempt in range(5):
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                              headers={"Authorization": "Bearer dummy"}, json=body, timeout=90)
            if r.status_code in (429, 500, 502, 503, 504): time.sleep(2 ** attempt); continue
            j = r.json()
            if "choices" not in j: return None, j.get("usage")
            t = j["choices"][0]["message"]["content"]
            return json.loads(t[t.find("{"): t.rfind("}") + 1]), j.get("usage")
        except Exception: time.sleep(2 ** attempt)
    return None, None

def main(rev_csv, out, model, limit=0, workers=24):
    r = pd.read_csv(rev_csv)
    if limit: r = r.sample(limit, random_state=1)
    done = set()
    if os.path.exists(out): done = {json.loads(l)["id"] for l in open(out)}
    rows = [x for x in r.itertuples() if x.id not in done]
    print(len(rows), "reviews to run", flush=True)
    lock = threading.Lock(); f = open(out, "a"); st = {"n": 0, "fail": 0, "cost": 0.0}
    def run(x):
        res, u = call(model, str(x.comments))
        with lock:
            st["n"] += 1
            if res is None: st["fail"] += 1
            else: f.write(json.dumps({"id": int(x.id), "listing_id": int(x.listing_id), "res": res}) + "\n"); f.flush()
            if u: st["cost"] += u.get("cost", 0) or 0
            if st["n"] % 2000 == 0: print(st, flush=True)
    with cf.ThreadPoolExecutor(workers) as ex: list(ex.map(run, rows))
    print("final", st)

if __name__ == "__main__":
    a = sys.argv; main(a[1], a[2], a[3], *(int(x) for x in a[4:6]))
