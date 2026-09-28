"""SEC EDGAR: full-text search, filing documents, company metadata, XBRL assets."""
import json
import re
from datetime import date, timedelta

from bs4 import BeautifulSoup

EFTS = "https://efts.sec.gov/LATEST/search-index"
PAGE = 100          # EFTS returns up to 100 hits per page
EFTS_CAP = 10000    # EFTS will not page past 10,000 hits; split the date range instead


def _months(start, end):
    """Split [start, end] (ISO strings) into calendar-month windows."""
    s, e = date.fromisoformat(start), date.fromisoformat(end)
    out = []
    while s <= e:
        nxt = (s.replace(day=1) + timedelta(days=32)).replace(day=1)
        out.append((s.isoformat(), min(e, nxt - timedelta(days=1)).isoformat()))
        s = nxt
    return out


def clean_name(display_name):
    """'Couchbase, Inc.  (BASE)  (CIK 0001845022)' -> 'Couchbase, Inc.'"""
    n = re.sub(r"\s*\(CIK \d+\)\s*$", "", display_name)
    return re.sub(r"\s*\([A-Z0-9.\-, ]+\)\s*$", "", n).strip()


def parse_efts_hit(hit, phrase):
    """Flatten one EFTS hit. One row per CIK (multi-filer documents list several)."""
    src = hit.get("_source", {})
    _id = hit.get("_id", "")
    adsh, _, fname = _id.partition(":")
    names = src.get("display_names") or []
    sics = src.get("sics") or []
    rows = []
    for i, cik in enumerate(src.get("ciks") or []):
        rows.append({
            "cik": int(cik),
            "name": clean_name(names[i]) if i < len(names) else "",
            "sic": int(sics[i]) if i < len(sics) and str(sics[i]).isdigit() else None,
            "form": src.get("form") or (src.get("root_forms") or [""])[0],
            "file_date": src.get("file_date"),
            "adsh": src.get("adsh") or adsh,
            "filename": fname,
            "phrase": phrase,
        })
    return rows


def efts_search(client, phrase, start, end, forms):
    """All hits for an exact phrase in [start, end]; splits by month if capped."""
    def page(frm, s, e):
        params = {"q": f'"{phrase}"', "dateRange": "custom", "startdt": s, "enddt": e,
                  "forms": ",".join(forms), "from": frm}
        status, body = client.get(EFTS, params=params)
        if status != 200:
            raise RuntimeError(f"EFTS {status} for {phrase} {s}..{e}")
        return json.loads(body)

    def run(s, e):
        first = page(0, s, e)
        total = first.get("hits", {}).get("total", {}).get("value", 0)
        if total >= EFTS_CAP and s != e:
            windows = _months(s, e)
            if len(windows) > 1:
                return [r for a, b in windows for r in run(a, b)]
        if total >= EFTS_CAP:
            print(f"WARNING: {phrase!r} {s}..{e} has {EFTS_CAP}+ hits; only the first {EFTS_CAP} kept")
        rows = [r for h in first["hits"]["hits"] for r in parse_efts_hit(h, phrase)]
        for frm in range(PAGE, min(total, EFTS_CAP), PAGE):
            data = page(frm, s, e)
            rows += [r for h in data["hits"]["hits"] for r in parse_efts_hit(h, phrase)]
        return rows

    return run(start, end)


def document_url(cik, adsh, filename):
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{adsh.replace('-', '')}/{filename}"


def html_to_text(raw):
    soup = BeautifulSoup(raw, "html.parser")
    for t in soup(["script", "style"]):
        t.decompose()
    return " ".join(soup.get_text(" ").split())


def fetch_text(client, url):
    status, body = client.get(url)
    if status != 200:
        return ""
    return html_to_text(body)


def submissions(client, cik):
    """Company metadata and filing index (name, SIC, recent filings)."""
    status, body = client.get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json")
    return json.loads(body) if status == 200 else {}


def filing_dates(client, cik, forms):
    """Filing dates of the given forms (recent block plus older paged files)."""
    sub = submissions(client, cik)
    blocks = [sub.get("filings", {}).get("recent", {})]
    for f in sub.get("filings", {}).get("files", []):
        st, body = client.get("https://data.sec.gov/submissions/" + f["name"])
        if st == 200:
            blocks.append(json.loads(body))
    out = []
    for b in blocks:
        for form, d in zip(b.get("form", []), b.get("filingDate", [])):
            if form in forms:
                out.append(d)
    return out


def assets_in_year(client, cik, year):
    """Total assets (USD) from the 10-K fiscal year ending in `year`, via XBRL. None if absent."""
    url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{int(cik):010d}/us-gaap/Assets.json"
    status, body = client.get(url, ok_status=(200, 404))
    if status != 200:
        return None
    vals = [u for u in json.loads(body).get("units", {}).get("USD", [])
            if u.get("form") in ("10-K", "10-K/A") and str(u.get("end", "")).startswith(str(year))]
    if not vals:
        return None
    return max(vals, key=lambda u: (u.get("filed", ""), u.get("end", "")))["val"]
