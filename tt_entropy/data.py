"""Tenant data: convert Customer Support on Twitter (TWCS) to JSONL, load tenants, make synthetic tenants.

JSONL format, one pair per line: {"tenant": "AppleSupport", "prompt": "...", "response": "..."}

Convert TWCS (download twcs.csv from Kaggle first, see README):
  python data.py twcs path/to/twcs.csv data/twcs_pairs.jsonl
"""
import json
import random
import re
import sys
from collections import defaultdict

PROMPT_TEMPLATE = "Customer: {prompt}\nAgent:"
_MENTIONS = re.compile(r"^(@\w+\s*)+")


def _clean(text):
    text = _MENTIONS.sub("", str(text)).strip()  # drop leading @handles
    return re.sub(r"https?://\S+", "<url>", text)


def convert_twcs(csv_path, out_path, min_pairs=200):
    """Pair each customer tweet with the brand's direct reply. Tenant = the brand's account name."""
    import pandas as pd

    df = pd.read_csv(csv_path, dtype={"tweet_id": str, "in_response_to_tweet_id": str})
    df["inbound"] = df["inbound"].astype(str).str.lower() == "true"
    df["in_response_to_tweet_id"] = df["in_response_to_tweet_id"].str.replace(r"\.0$", "", regex=True)
    cust = df[df["inbound"]].set_index("tweet_id")["text"]
    brand = df[~df["inbound"] & df["in_response_to_tweet_id"].notna()]
    brand = brand[brand["in_response_to_tweet_id"].isin(cust.index)]
    counts = brand["author_id"].value_counts()
    keep = set(counts[counts >= min_pairs].index)
    n = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for row in brand.itertuples(index=False):
            if row.author_id not in keep:
                continue
            p, r = _clean(cust[row.in_response_to_tweet_id]), _clean(row.text)
            if p and r:
                f.write(json.dumps({"tenant": row.author_id, "prompt": p, "response": r}) + "\n")
                n += 1
    print(f"wrote {n} pairs for {len(keep)} brands (>= {min_pairs} pairs each) to {out_path}")


def load_jsonl(path):
    tenants = defaultdict(list)
    with open(path, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            tenants[row["tenant"]].append((row["prompt"], row["response"]))
    return dict(tenants)


def encode_tenant(pairs, tok, max_len):
    """Tokenize (prompt, response) text pairs into (prompt_ids, response_ids); loss is on the response."""
    out = []
    for p, r in pairs:
        pi = tok(PROMPT_TEMPLATE.format(prompt=p), add_special_tokens=True)["input_ids"][: max_len // 2]
        ri = tok(" " + r + tok.eos_token, add_special_tokens=False)["input_ids"][: max_len - len(pi)]
        out.append((pi, ri))
    return out


def synthetic_tenants(n_tenants, n_examples, vocab, seed=0):
    """Token-level tenants whose tasks get harder with the tenant index (for CPU smoke tests only).

    Tenant k maps a random prompt to a response by one of: copy, shift, reverse, sort, reverse+shift ...
    """
    rng = random.Random(seed)
    lo, hi = 4, vocab  # ids 0..3 reserved (pad, bos, eos, sep)
    tasks = [
        lambda s, k: s,
        lambda s, k: [lo + (t - lo + k) % (hi - lo) for t in s],
        lambda s, k: s[::-1],
        lambda s, k: sorted(s),
        lambda s, k: [lo + (t - lo + k) % (hi - lo) for t in s[::-1]],
        lambda s, k: sorted(s, reverse=True)[::2] + s[::2],
    ]
    tenants = {}
    for k in range(n_tenants):
        fn = tasks[k % len(tasks)]
        ex = []
        for _ in range(n_examples):
            s = [rng.randrange(lo, hi) for _ in range(rng.randrange(4, 10))]
            ex.append(([1] + s + [3], fn(s, k + 1) + [2]))
        tenants[f"synthetic-{k}"] = ex
    return tenants


def features(encoded):
    """Observable tenant traits used in the H1 regression."""
    resp = [t for _, r in encoded for t in r]
    head = resp[:5000]
    return dict(
        n_examples=len(encoded),
        mean_prompt_tokens=sum(len(p) for p, _ in encoded) / max(len(encoded), 1),
        mean_response_tokens=len(resp) / max(len(encoded), 1),
        response_type_token_ratio=len(set(head)) / max(len(head), 1),
        distinct_response_share=len({tuple(r) for _, r in encoded}) / max(len(encoded), 1),
    )


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "twcs":
        convert_twcs(sys.argv[2], sys.argv[3], min_pairs=int(sys.argv[4]) if len(sys.argv) > 4 else 200)
    else:
        print(__doc__)
