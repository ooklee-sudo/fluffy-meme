"""Run channels C1-C4 for a set of models and append one JSON line per call to a results file.

  python runner.py --items items.jsonl --models config/models.json --out results/run1.jsonl
  python runner.py ... --channels C1,C2 --reps 5 --only Qwen --workers 8
  python runner.py ... --count        # print the number of calls per model and exit (no API use)

Resumable: a request whose key already has a successful API row is skipped; rows whose API call failed
are retried on rerun. A call that succeeds but cannot be parsed is stored as an answer with parsed=null
(parse failure is data, and the analysis decides how to code it).
"""
import argparse
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import ym_common as yc


def load_done(path):
    done = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("api_ok"):
                    done.add(r["key"])
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--models", required=True)
    ap.add_argument("--stances", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--channels", default="C1,C2,C3,C4")
    ap.add_argument("--reps", type=int, default=5, help="stance-free replicates per stem (C1)")
    ap.add_argument("--levels", default=None, help="comma list; default all levels in the stance config")
    ap.add_argument("--primary", default="weak", help="stance level used for the C4 rotation check")
    ap.add_argument("--only", default="", help="run models whose name contains this text")
    ap.add_argument("--limit", type=int, default=0, help="first N items only (smoke test)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--count", action="store_true")
    a = ap.parse_args()

    cfg = yc.load_stances(a.stances)
    items = yc.load_items(a.items)
    if a.limit:
        items = items[: a.limit]
    models = [m for m in yc.load_models(a.models) if a.only in m["name"]]
    channels = tuple(c.strip() for c in a.channels.split(","))
    levels = a.levels.split(",") if a.levels else None
    if a.reps < 2 and "C1" in channels:
        raise SystemExit("C1 needs --reps >= 2 to estimate instability")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    done = load_done(a.out)
    lock = threading.Lock()

    for m in models:
        reqs = yc.enumerate_requests(m, items, cfg, channels, a.reps, levels, a.primary)
        todo = [r for r in reqs if r.key not in done]
        print(f"[{m['name']}] {len(reqs)} requests, {len(todo)} to run", flush=True)
        if a.count or not todo:
            continue
        backend = yc.make_backend(m, a.max_tokens)
        n_fail = 0
        t0 = time.time()

        def work(r):
            text, err = yc.call_with_retry(backend, r)
            row = {"key": r.key, "model": m["name"], "item": r.item["id"], "domain": r.item["domain"],
                   "channel": r.channel, "level": r.level, "direction": r.direction, "rep": r.rep,
                   "rot": r.rot, "letters": r.letters, "ts": round(time.time(), 1)}
            if err is not None:
                row.update(api_ok=False, error=err, raw=None, parsed=None, role=None)
            else:
                letter = yc.parse_letter(text)
                inv = {v: k for k, v in r.letters.items()}
                row.update(api_ok=True, raw=text[:200], parsed=letter, role=inv.get(letter))
            return row

        with ThreadPoolExecutor(max_workers=a.workers) as ex, open(a.out, "a") as f:
            futs = [ex.submit(work, r) for r in todo]
            for i, fu in enumerate(as_completed(futs), 1):
                row = fu.result()
                n_fail += not row["api_ok"]
                with lock:
                    f.write(json.dumps(row) + "\n")
                    f.flush()
                if i % 200 == 0:
                    print(f"  {i}/{len(todo)} ({n_fail} api failures, {time.time() - t0:.0f}s)", flush=True)
        print(f"[{m['name']}] done, {n_fail} api failures (rerun to retry them)", flush=True)


if __name__ == "__main__":
    main()
