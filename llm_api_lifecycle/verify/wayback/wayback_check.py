"""Check lifecycle data against Internet Archive (Wayback Machine) snapshots.

Run from a computer that can reach web.archive.org:
    python wayback_check.py            # all pages
    python wayback_check.py gemini     # only pages whose key starts with "gemini"

For every archived version of each vendor page, the script records the text
around each model ID and writes one row whenever that text changes. Reading the
output shows when a shutdown date or replacement first appeared, and whether it
was later revised. Standard library only. It waits 3 s between requests.
"""
import csv, html, json, os, re, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "data")
OUT = os.path.join(HERE, "wayback_timeline.csv")
UA = {"User-Agent": "lifecycle-data-verification/1.0 (academic research)"}
DELAY = 3.0

PAGES = {
    "gemini_deprecations": ["ai.google.dev/gemini-api/docs/deprecations", "aistudio.google.com/docs/deprecations"],
    "gemini_changelog": ["ai.google.dev/gemini-api/docs/changelog", "aistudio.google.com/docs/changelog"],
    "gemini_pricing": ["ai.google.dev/gemini-api/docs/pricing", "ai.google.dev/pricing", "aistudio.google.com/docs/pricing"],
    "openai_deprecations": ["platform.openai.com/docs/deprecations", "developers.openai.com/api/docs/deprecations"],
    "anthropic_deprecations": ["docs.anthropic.com/en/docs/about-claude/model-deprecations",
                               "docs.claude.com/en/docs/about-claude/model-deprecations",
                               "platform.claude.com/docs/en/about-claude/model-deprecations"],
    "bedrock_lifecycle": ["docs.aws.amazon.com/bedrock/latest/userguide/model-lifecycle.html"],
}

def get(url, tries=5):
    for i in range(tries):
        try:
            time.sleep(DELAY)
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(60 * (i + 1)); continue
            if e.code == 404: return None
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(10 * (i + 1))
    raise RuntimeError(f"failed: {url}")

def snapshots(url):
    q = ("https://web.archive.org/cdx/search/cdx?url=" + url +
         "&output=json&fl=timestamp,original,digest&filter=statuscode:200&collapse=digest")
    body = get(q)
    rows = json.loads(body) if body else []
    return rows[1:] if rows else []

def text_of(page):
    page = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", page)
    page = re.sub(r"(?s)<[^>]+>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(page))

def model_ids():
    ids = {}
    for fn, key in [("gemini_lifecycle.csv", "gemini"), ("openai_lifecycle.csv", "openai"), ("other_lifecycle.csv", "anthropic")]:
        with open(os.path.join(DATA, fn), newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if key == "anthropic" and r["platform"] not in ("Anthropic API", "AWS Bedrock"): continue
                ids.setdefault(key, set()).add(r["model_id"])
    ids["bedrock"] = ids.get("anthropic", set())
    return ids

def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    ids = model_ids()
    group = {"gemini": "gemini", "openai": "openai", "anthropic": "anthropic", "bedrock": "bedrock"}
    new = not os.path.exists(OUT)
    with open(OUT, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new: w.writerow(["page", "snapshot_date", "snapshot_url", "model_id", "context"])
        for page, urls in PAGES.items():
            if only and not page.startswith(only): continue
            vendor = group[page.split("_")[0]]
            last = {}
            snaps = sorted({(ts, orig) for u in urls for ts, orig, _ in snapshots(u)})
            print(f"{page}: {len(snaps)} distinct snapshots", flush=True)
            for ts, orig in snaps:
                url = f"https://web.archive.org/web/{ts}id_/{orig}"
                page_html = get(url)
                if not page_html: continue
                t = text_of(page_html)
                for mid in sorted(ids.get(vendor, ())):
                    for m in re.finditer(re.escape(mid) + r"(?![\w.-])", t):
                        ctx = t[max(0, m.start() - 150): m.end() + 250]
                        if last.get(mid) != ctx:
                            w.writerow([page, f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}", url, mid, ctx]); last[mid] = ctx
                        break
                f.flush()
    print("wrote", OUT)

if __name__ == "__main__":
    main()
