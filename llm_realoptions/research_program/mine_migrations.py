"""Measure how long public repositories take to migrate away from a retiring model identifier.
For each retired model string m (announcement date a, shutdown date s from data/openai_deprecations.csv):
  1. GitHub code search for files containing m (needs a token; search is rate limited to about 10 requests per minute),
  2. for each hit (repo, path), list the commits touching the path since a,
  3. migration lag = date of the first commit after a whose version of the file no longer contains m, minus a (days);
     files whose last observed version still contains m are right-censored at the observation date.
Output: one JSON line per (model, repo, path) in migrations.jsonl. Run this on your own machine with your own token (export GITHUB_TOKEN=...);
never paste the token into a chat. Respect GitHub's terms and rate limits; store only public data and do not collect personal e-mail addresses.
usage: python mine_migrations.py --models gpt-4-0613 gpt-3.5-turbo-0125 --max-hits 50 ; python mine_migrations.py --selftest
"""
import argparse, base64, datetime as dt, json, os, sys, time
import pandas as pd

API = "https://api.github.com"


def gh(path, params=None):
    import requests
    h = {"Accept": "application/vnd.github+json", "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"]}
    for k in range(8):
        try:
            r = requests.get(API + path, headers=h, params=params, timeout=60)
        except requests.exceptions.RequestException as e:      # network trouble: wait and retry
            print("  network error, retry", k + 1, type(e).__name__, flush=True); time.sleep(min(15 * 2 ** k, 300)); continue
        if r.status_code in (403, 429) and ("rate limit" in r.text.lower() or "abuse" in r.text.lower()):
            time.sleep(65); continue
        r.raise_for_status(); return r.json()
    raise RuntimeError("gave up after repeated errors")


def lag_from_versions(versions, model, announced, observed_end):
    """versions: list of (commit_date, text) in chronological order, only commits after the announcement. Returns (lag_days, censored)."""
    for d, text in versions:
        if model not in text:
            return (d - announced).days, False
    return (observed_end - announced).days, True


SEEN = set()


def mine(model, announced, shutdown, max_hits, out):
    hits = gh("/search/code", {"q": f'"{model}"', "per_page": min(max_hits, 100)}).get("items", [])
    time.sleep(7)
    for it in hits[:max_hits]:
        repo, path = it["repository"]["full_name"], it["path"]
        if (model, repo, path) in SEEN:
            continue
        try:
            _one(model, announced, shutdown, repo, path, out)
        except Exception as e:
            print("  skipped file", repo, path, repr(e)[:120], flush=True)


def _one(model, announced, shutdown, repo, path, out):
    if True:
        commits = gh(f"/repos/{repo}/commits", {"path": path, "since": announced.isoformat() + "T00:00:00Z", "per_page": 100})
        versions = []
        for c in reversed(commits):
            f = gh(f"/repos/{repo}/contents/{path}", {"ref": c["sha"]})
            text = base64.b64decode(f.get("content", "")).decode("utf-8", "ignore") if f.get("encoding") == "base64" else ""
            versions.append((dt.datetime.fromisoformat(c["commit"]["committer"]["date"].replace("Z", "+00:00")).date(), text))
        lag, cens = lag_from_versions(versions, model, announced, dt.date.today())
        row = dict(model=model, repo=repo, path=path, announced=str(announced), shutdown=str(shutdown), lag_days=lag, censored=cens,
                   notice_days=(shutdown - announced).days, n_commits=len(commits))
        out.write(json.dumps(row) + "\n"); out.flush()


def selftest():
    a = dt.date(2026, 4, 22)
    v = [(dt.date(2026, 5, 1), 'm="gpt-4-0613"'), (dt.date(2026, 6, 10), 'm="gpt-5.6-sol"')]
    assert lag_from_versions(v, "gpt-4-0613", a, dt.date(2026, 10, 2)) == (49, False)
    assert lag_from_versions(v[:1], "gpt-4-0613", a, dt.date(2026, 10, 2)) == ((dt.date(2026, 10, 2) - a).days, True)
    print("selftest ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--models", nargs="*"); ap.add_argument("--max-hits", type=int, default=50)
    ap.add_argument("--out", default="migrations.jsonl"); ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--past-shutdown-only", action="store_true", help="only models whose shutdown date has passed (others are all right-censored)")
    ap.add_argument("--default-set", action="store_true", help="use the text-model identifiers listed in the OpenAI table (no audio, image, tts, realtime)")
    a = ap.parse_args()
    if a.selftest: selftest(); sys.exit()
    o = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "openai_deprecations.csv"), parse_dates=["announced", "shutdown"])
    models = a.models or []
    if a.default_set:
        bad = ("audio", "image", "tts", "realtime", "transcribe", "whisper", "dall-e", "sora", "moderation", "search", "computer-use", "codex", "api", "platform", "builder", "ft-")
        t = o[o.model.str.match(r"^(gpt-|o[134]|text-davinci|babbage|davinci)") & ~o.model.str.contains("|".join(bad)) & (o.announced < pd.Timestamp("2026-07-01"))]
        if a.past_shutdown_only:
            t = t[t.shutdown < pd.Timestamp.today()]
        models = list(dict.fromkeys(t.model))
    done = set()
    marker = a.out + ".done"
    if os.path.exists(marker):
        done = {l.strip() for l in open(marker) if l.strip()}
    if os.path.exists(a.out):
        for l in open(a.out):
            if l.strip():
                j = json.loads(l); SEEN.add((j["model"], j["repo"], j["path"]))
    with open(a.out, "a") as out:
        for m in models:
            if m in done:
                print("skip (already done):", m); continue
            r = o[o.model == m].iloc[0]; print("mining", m, flush=True)
            try:
                mine(m, r.announced.date(), r.shutdown.date(), a.max_hits, out)
                open(marker, "a").write(m + "\n")
            except Exception as e:
                print("failed (will retry on next run)", m, repr(e)[:200], flush=True)
