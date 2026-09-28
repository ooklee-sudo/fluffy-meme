"""Reconstruct historical job postings from Common Crawl captures of ATS job boards.

Flow: list crawls in the window -> CDX index query per firm URL pattern ->
fetch each WARC record by byte range -> parse HTML -> JobPosting JSON-LD or page text.
"""
import gzip
import io
import json
import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

COLLINFO = "https://index.commoncrawl.org/collinfo.json"
DATA = "https://data.commoncrawl.org/"

# URL patterns per applicant-tracking system; {slug} comes from ats_map.csv
ATS_PATTERNS = {
    "greenhouse": ["boards.greenhouse.io/{slug}/jobs/*", "job-boards.greenhouse.io/{slug}/jobs/*"],
    "lever": ["jobs.lever.co/{slug}/*"],
    "ashby": ["jobs.ashbyhq.com/{slug}/*"],
    "smartrecruiters": ["jobs.smartrecruiters.com/{slug}/*"],
    "workday": ["{slug}/*"],          # slug = full host, e.g. acme.wd5.myworkdayjobs.com
    "icims": ["{slug}/jobs/*"],       # slug = full host, e.g. careers-acme.icims.com
    "custom": ["{slug}*"],            # slug = URL prefix, e.g. careers.acme.com/job/
}

# job-detail URLs only (drop listing and search pages)
DETAIL = {
    "greenhouse": re.compile(r"/jobs/\d+"),
    "lever": re.compile(r"jobs\.lever\.co/[^/]+/[0-9a-f-]{36}"),
    "ashby": re.compile(r"jobs\.ashbyhq\.com/[^/]+/[0-9a-f-]{36}"),
    "smartrecruiters": re.compile(r"smartrecruiters\.com/[^/]+/\d+"),
    "workday": re.compile(r"/job/"),
    "icims": re.compile(r"/jobs/\d+/"),
    "custom": re.compile(r"."),
}


def crawls_between(client, start, end):
    """Crawl ids whose capture period overlaps [start, end] (ISO dates)."""
    status, body = client.get(COLLINFO, cache=False)
    out = []
    for c in json.loads(body):
        frm, to = c.get("from", "")[:10], c.get("to", "")[:10]
        if frm and to and to >= start and frm <= end:
            out.append((c["id"], c["cdx-api"]))
    return sorted(out)


def cdx_query(client, cdx_api, url_pattern):
    """All 200-status captures for a URL pattern in one crawl. Pages through results."""
    base = {"url": url_pattern, "output": "json", "filter": "status:200",
            "fl": "url,timestamp,filename,offset,length,mime"}
    st, body = client.get(cdx_api, params={**base, "showNumPages": "true"}, ok_status=(200, 404))
    if st == 404:
        return []
    try:
        pages = int(json.loads(body).get("pages", 1))
    except (ValueError, AttributeError):
        pages = 1
    rows = []
    for p in range(pages):
        st, body = client.get(cdx_api, params={**base, "page": p}, ok_status=(200, 404))
        if st == 404:
            continue
        for line in body.decode("utf-8", "replace").splitlines():
            line = line.strip()
            if line.startswith("{"):
                rows.append(json.loads(line))
    return rows


def _dechunk(b):
    out, i = bytearray(), 0
    while i < len(b):
        j = b.find(b"\r\n", i)
        if j < 0:
            break
        try:
            n = int(b[i:j].split(b";")[0], 16)
        except ValueError:
            return bytes(b)  # not actually chunked
        if n == 0:
            break
        out += b[j + 2:j + 2 + n]
        i = j + 2 + n + 2
    return bytes(out)


def parse_warc_record(raw_gz):
    """Return (http_headers: dict, body: bytes) from one gzipped WARC response record."""
    raw = gzip.GzipFile(fileobj=io.BytesIO(raw_gz)).read()
    warc_head, _, rest = raw.partition(b"\r\n\r\n")    # WARC headers
    m = re.search(rb"(?im)^content-length:\s*(\d+)", warc_head)
    if m:
        rest = rest[: int(m.group(1))]                     # drop the record-closing CRLFs
    http_head, _, body = rest.partition(b"\r\n\r\n")  # HTTP headers
    headers = {}
    for line in http_head.split(b"\r\n")[1:]:
        k, _, v = line.partition(b":")
        headers[k.decode("latin-1").strip().lower()] = v.decode("latin-1").strip()
    if "chunked" in headers.get("transfer-encoding", "").lower():
        body = _dechunk(body)
    if headers.get("content-encoding", "").lower() == "gzip":
        try:
            body = gzip.decompress(body)
        except OSError:
            pass
    return headers, body


def fetch_capture(client, row):
    off, ln = int(row["offset"]), int(row["length"])
    st, raw = client.get(DATA + row["filename"],
                         headers={"Range": f"bytes={off}-{off + ln - 1}"}, ok_status=(200, 206))
    if st not in (200, 206):
        return b""
    return parse_warc_record(raw)[1]


def _jobposting(obj):
    if isinstance(obj, list):
        for o in obj:
            r = _jobposting(o)
            if r:
                return r
    elif isinstance(obj, dict):
        t = obj.get("@type")
        if t == "JobPosting" or (isinstance(t, list) and "JobPosting" in t):
            return obj
        if "@graph" in obj:
            return _jobposting(obj["@graph"])
    return None


def extract_posting(html):
    """Title, description text, datePosted (if JSON-LD present), and text length."""
    soup = BeautifulSoup(html, "html.parser")
    jp = None
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            jp = _jobposting(json.loads(s.string or ""))
        except (json.JSONDecodeError, TypeError):
            continue
        if jp:
            break
    if jp:
        desc = BeautifulSoup(jp.get("description", "") or "", "html.parser").get_text(" ")
        title = jp.get("title", "")
        posted = (jp.get("datePosted") or "")[:10]
    else:
        for t in soup(["script", "style", "nav", "footer", "header"]):
            t.decompose()
        desc = soup.get_text(" ")
        title = soup.title.get_text(strip=True) if soup.title else ""
        posted = ""
    desc = " ".join(desc.split())
    return {"title": title, "text": desc, "date_posted": posted, "text_len": len(desc),
            "jsonld": jp is not None}


def canonical_job_url(url):
    p = urlsplit(url)
    return (p.netloc.lower() + p.path.rstrip("/")).replace("job-boards.greenhouse.io", "boards.greenhouse.io")


def slug_candidates(name):
    """Guess ATS slugs from a company name, e.g. 'Rocket Companies, Inc.' -> rocketcompanies, rocket."""
    n = re.sub(r"\(.*?\)", " ", name.lower())
    n = re.sub(r"\b(inc|corp|corporation|co|company|ltd|plc|holdings|group|the|llc|n\.v|s\.a)\b\.?", " ", n)
    words = re.findall(r"[a-z0-9]+", n)
    if not words:
        return []
    c = ["".join(words), "-".join(words), words[0]]
    return list(dict.fromkeys(c))
