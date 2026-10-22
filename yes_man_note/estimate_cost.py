"""Estimate the OpenRouter cost of a run before spending anything.

  python estimate_cost.py --items data/items_v1.jsonl --models config/models.openrouter.json [--reps 5] [--channels C1,C2,C3,C4]

Prices come from the public https://openrouter.ai/api/v1/models list (no key needed). Tokens are estimated as
characters / 4 for the prompt and --out-tokens (default 4) per answer. A model that emits reasoning or long text
will cost more: check tokens_out in a small pilot (runner records usage) and rerun this with --out-tokens.
"""
import argparse
import json
import urllib.request

import ym_common as yc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--models", required=True)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--channels", default="C1,C2,C3,C4")
    ap.add_argument("--out-tokens", type=float, default=4.0)
    ap.add_argument("--price-file", default=None, help="saved /models JSON (otherwise fetched)")
    a = ap.parse_args()
    if a.price_file:
        with open(a.price_file) as f:
            listing = json.load(f)["data"]
    else:
        with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as r:
            listing = json.loads(r.read())["data"]
    price = {m["id"]: (float(m["pricing"]["prompt"]), float(m["pricing"]["completion"])) for m in listing}
    cfg = yc.load_stances()
    items = yc.load_items(a.items)
    total = 0.0
    print(f"{'model':22s} {'calls':>7s} {'in tokens':>10s} {'cost $':>9s}")
    for m in yc.load_models(a.models):
        reqs = yc.enumerate_requests(m, items, cfg, tuple(a.channels.split(",")), a.reps)
        tin = sum((len(r.system) + len(r.user)) / 4 for r in reqs)
        pi, po = price.get(m["model_id"], (None, None))
        if pi is None:
            print(f"{m['name']:22s} {len(reqs):7d} {tin:10.0f}   model_id not in the OpenRouter list: {m['model_id']}")
            continue
        cost = tin * pi + len(reqs) * a.out_tokens * po
        total += cost
        print(f"{m['name']:22s} {len(reqs):7d} {tin:10.0f} {cost:9.2f}")
    print(f"{'TOTAL':22s} {'':7s} {'':10s} {total:9.2f}")


if __name__ == "__main__":
    main()
