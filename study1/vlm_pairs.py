"""Study 1, step 3: pairwise VLM judgments of cover photographs (order-balanced).

Usage: python vlm_pairs.py SAMPLE_CSV PHOTO_DIR OUT_JSONL MODEL [K=10] [LIMIT=0] [WORKERS=24]
For each listing, K partners are drawn at random from the same city x room_type; every unordered
pair is judged in both presentation orders. Results are appended to OUT_JSONL (resumable).
"""
import sys, os, json, base64, threading, concurrent.futures as cf, time
import numpy as np, pandas as pd, requests

ATTRS = ["cleanliness", "spaciousness", "brightness", "furnishing_condition", "photographic_quality"]
PROMPT = (
    "You see two photographs of short-term rental listings, Photo A (first image) and Photo B (second image). "
    "For each attribute, say which photograph shows the HIGHER level. Judge what the photograph conveys about "
    "the place, not the quality of the photo, except for the last attribute.\n"
    "- cleanliness: how clean and tidy the space looks\n- spaciousness: how roomy the space looks\n"
    "- brightness: how bright and well lit the space looks\n- furnishing_condition: how new and well maintained the furnishings look\n"
    "- photographic_quality: technical quality of the photograph (sharpness, composition, exposure)\n"
    'Answer with JSON only, for example {"cleanliness":"A","spaciousness":"B","brightness":"A","furnishing_condition":"B","photographic_quality":"A"}. '
    "Use exactly \"A\" or \"B\" for each value."
)

def b64(path):
    return "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()

def call(model, pa, pb):
    body = {"model": model, "temperature": 0, "max_tokens": 120,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": b64(pa)}},
                {"type": "image_url", "image_url": {"url": b64(pb)}}]}]}
    for attempt in range(5):
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                              headers={"Authorization": "Bearer dummy"}, json=body, timeout=120)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt); continue
            j = r.json()
            if "choices" not in j: return None, j.get("error"), None
            txt = j["choices"][0]["message"]["content"]
            s = txt[txt.find("{"): txt.rfind("}") + 1]
            return json.loads(s), None, j.get("usage")
        except Exception as e:
            time.sleep(2 ** attempt); err = str(e)
    return None, "failed", None

def main(sample_csv, photo_dir, out, model, K=10, limit=0, workers=24):
    s = pd.read_csv(sample_csv); rng = np.random.default_rng(7)
    pairs = set()
    for _, g in s.groupby(["city", "room_type"]):
        ids = g.id.to_numpy()
        for i in ids:
            for j in rng.choice(ids[ids != i], size=min(K, len(ids) - 1), replace=False):
                pairs.add((min(i, j), max(i, j)))
    pairs = sorted(pairs)
    if limit: pairs = [pairs[k] for k in rng.choice(len(pairs), limit, replace=False)]
    done = set()
    if os.path.exists(out):
        for l in open(out):
            r = json.loads(l); done.add((r["a"], r["b"], r["order"]))
    jobs = [(a, b, o) for a, b in pairs for o in ("AB", "BA") if (a, b, o) not in done]
    print(len(pairs), "pairs;", len(jobs), "calls to run", flush=True)
    lock = threading.Lock(); f = open(out, "a"); stats = {"n": 0, "tok_in": 0, "tok_out": 0, "cost": 0.0, "fail": 0}
    def run(job):
        a, b, o = job
        first, second = (a, b) if o == "AB" else (b, a)
        res, err, usage = call(model, f"{photo_dir}/photos/{first}.jpg", f"{photo_dir}/photos/{second}.jpg")
        with lock:
            stats["n"] += 1
            if res is None: stats["fail"] += 1
            else:
                f.write(json.dumps({"a": int(a), "b": int(b), "order": o, "res": res}) + "\n"); f.flush()
            if usage:
                stats["tok_in"] += usage.get("prompt_tokens", 0); stats["tok_out"] += usage.get("completion_tokens", 0)
                stats["cost"] += usage.get("cost", 0) or 0
            if stats["n"] % 500 == 0: print(stats, flush=True)
    with cf.ThreadPoolExecutor(workers) as ex: list(ex.map(run, jobs))
    print("final", stats)

if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], a[3], a[4], *(int(x) for x in a[5:8]))
