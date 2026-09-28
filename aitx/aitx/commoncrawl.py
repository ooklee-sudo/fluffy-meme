"""Reconstruct historical job postings from Common Crawl captures of ATS job boards.

Flow: list crawls in the window -> CDX index query per firm URL pattern ->
fetch each WARC record by byte range -> parse HTML -> JobPosting JSON-LD or page text.
"""
import gzip
import io
import json
import re
from datetime import date, timedelta
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


FILES = "files:"    # cdx_api prefix: read the index files on data.commoncrawl.org instead
_index_down = False  # set after the index server keeps failing; later queries skip it


def crawls_between(client, start, end):
    """Crawl ids whose capture period overlaps [start, end] (ISO dates).

    Falls back to the crawl list on data.commoncrawl.org when the index server is unreachable
    (it drops connections from some cloud networks); cdx_query then reads the index files.
    """
    try:
        status, body = client.get(COLLINFO, cache=False)
    except RuntimeError:
        status = None
    if status != 200:
        return _crawls_from_files(client, start, end)
    out = []
    for c in json.loads(body):
        frm, to = c.get("from", "")[:10], c.get("to", "")[:10]
        if frm and to and to >= start and frm <= end:
            out.append((c["id"], c["cdx-api"]))
    return sorted(out)


def _crawls_from_files(client, start, end):
    """Main crawls listed on data.commoncrawl.org; period approximated by the id's ISO week."""
    status, body = client.get(DATA + "crawl-data/index.html", cache=False)
    if status != 200:
        raise RuntimeError("Common Crawl index server and data server both unreachable")
    out = []
    for cid in sorted(set(re.findall(r"CC-MAIN-(\d{4})-(\d{2})", body.decode("utf-8", "replace")))):
        y, w = int(cid[0]), int(cid[1])
        try:
            to = date.fromisocalendar(y, w, 7)
        except ValueError:
            continue
        frm = to - timedelta(days=20)   # crawls run for roughly two to three weeks
        if to.isoformat() >= start and frm.isoformat() <= end:
            crawl_id = f"CC-MAIN-{y}-{w:02d}"
            out.append((crawl_id, FILES + crawl_id))
    return out


def surt_prefix(url_pattern):
    """'boards.greenhouse.io/acme/jobs/*' -> 'io,greenhouse,boards)/acme/jobs/' (CDX sort key).
    A leading '*.' matches every subdomain: '*.myworkdayjobs.com' -> 'com,myworkdayjobs,'."""
    pat = url_pattern.rstrip("*").lower()
    host, slash, path = pat.partition("/")
    host = host.split(":")[0]
    if host.startswith("*."):
        return ",".join(reversed(host[2:].split("."))) + ","
    if host.startswith("www."):
        host = host[4:]
    return ",".join(reversed(host.split("."))) + ")" + slash + path


def _idx_range(client, idx_url, pos, n):
    st, raw = client.get(idx_url, headers={"Range": f"bytes={pos}-{pos + n - 1}"}, ok_status=(200, 206))
    if st == 416:                               # past the end of the file
        return b""
    if st not in (200, 206):                    # any other failure must not pass for end of file
        raise RuntimeError(f"HTTP {st} reading {idx_url} at {pos}")
    return raw


def _cdx_query_files(client, crawl_id, url_pattern, max_size=1 << 31):
    """CDX lookup without the index server: binary-search cluster.idx, then read the cdx blocks.

    cluster.idx has one sorted line per compressed block of the cdx files: 'SURT TIMESTAMP<TAB>
    cdx-NNNNN.gz<TAB>offset<TAB>length<TAB>seq'. Matches for a prefix lie in the block before the
    first line that starts with the prefix, plus every block whose first key starts with it.
    """
    base = f"{DATA}cc-index/collections/{crawl_id}/indexes/"
    idx_url = base + "cluster.idx"
    prefix = surt_prefix(url_pattern)
    # lo: byte offset whose next full line sorts before the prefix (or 0)
    lo, hi = 0, max_size
    while hi - lo > 4096:
        mid = (lo + hi) // 2
        lines = _idx_range(client, idx_url, mid, 4096).split(b"\n")
        if len(lines) > 2 and lines[1].decode("utf-8", "replace").split(" ")[0] < prefix:
            lo = mid
        else:
            hi = mid
    blocks, prev, pos, buf, first = [], None, lo, b"", lo > 0
    while True:
        raw = _idx_range(client, idx_url, pos, 65536)
        pos += len(raw)
        lines = (buf + raw).split(b"\n")
        if first:
            lines, first = lines[1:], False       # partial line before the first newline
        eof = len(raw) < 65536
        buf = b"" if eof else lines.pop()
        stop = False
        for ln in lines:
            f = ln.decode("utf-8", "replace").split("\t")
            if len(f) < 4:
                continue
            key, block = f[0].split(" ")[0], (f[1], int(f[2]), int(f[3]))
            if key < prefix:
                prev = block
            elif key.startswith(prefix):
                if prev:
                    blocks.append(prev); prev = None
                blocks.append(block)
            else:
                stop = True
                break
        if stop or eof:
            break
    if prev:
        blocks.append(prev)
    rows = []
    for name, off, ln in blocks:
        st, raw = client.get(base + name, headers={"Range": f"bytes={off}-{off + ln - 1}"},
                             ok_status=(200, 206))
        if st not in (200, 206):
            raise RuntimeError(f"HTTP {st} reading {base + name} at {off}")
        for line in gzip.decompress(raw).decode("utf-8", "replace").splitlines():
            key, _, rest = line.partition(" ")
            if not key.startswith(prefix):
                continue
            ts, _, js = rest.partition(" ")
            rec = json.loads(js)
            if rec.get("status") != "200":
                continue
            rows.append({"url": rec["url"], "timestamp": ts, "filename": rec["filename"],
                         "offset": rec["offset"], "length": rec["length"], "mime": rec.get("mime", "")})
    return rows


def cdx_query(client, cdx_api, url_pattern):
    """All 200-status captures for a URL pattern in one crawl. Pages through results."""
    global _index_down
    m = re.search(r"CC-MAIN-\d{4}-\d{2}", cdx_api)
    if cdx_api.startswith(FILES) or (_index_down and m):
        return _cdx_query_files(client, m.group(0), url_pattern)
    try:
        return _cdx_query_server(client, cdx_api, url_pattern)
    except RuntimeError:
        if not m:
            raise
        print("Common Crawl index server failing; using index files on data.commoncrawl.org")
        _index_down = True
        return _cdx_query_files(client, m.group(0), url_pattern)


def _cdx_query_server(client, cdx_api, url_pattern):
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


# whole-host prefixes for a bulk inventory of every board on the three hosted ATSs
INVENTORY_PATTERNS = {
    "greenhouse": ["boards.greenhouse.io/*", "job-boards.greenhouse.io/*"],
    "lever": ["jobs.lever.co/*"],
    "ashby": ["jobs.ashbyhq.com/*"],
    "workday": ["*.myworkdayjobs.com"],
    "icims": ["*.icims.com"],
    "smartrecruiters": ["jobs.smartrecruiters.com/*"],
}
# job titles appear in the URL only on these ATSs; others are always fetched
TITLE_IN_URL = {"workday", "icims", "smartrecruiters"}
TECH_TITLE = re.compile(
    r"engineer|develop|software|data|scien|machine|learning|\bai\b|\bml\b|artificial|analytic|architect|"
    r"\bllm|\bnlp\b|research|platform|cloud|devops|\bit\b|information|technolog|cyber|product.manager|"
    r"programm|automation|genai|intelligence", re.I)


def board_slug(url, ats=None):
    """Board id: 'https://boards.greenhouse.io/Acme/jobs/1' -> 'acme';
    Workday/iCIMS use the host: 'aig.wd1.myworkdayjobs.com' -> 'aig', 'careers-acme.icims.com' -> 'acme'."""
    p = urlsplit(url)
    if ats in ("workday", "icims"):
        label = p.netloc.lower().split(":")[0].split(".")[0]
        return re.sub(r"^(?:us|uk|global|external)?-?(?:careers|jobs)-", "", label) if ats == "icims" else label
    parts = p.path.strip("/").split("/")
    return parts[0].lower() if parts and parts[0] else ""


def tech_title(url):
    """True if the job title embedded in the URL looks like a technology role."""
    seg = [s for s in urlsplit(url).path.split("/") if s]
    hint = " ".join(seg[-2:]).replace("-", " ").replace("_", " ")
    return bool(TECH_TITLE.search(hint))


def inventory(client, crawl_id, ats_list=None):
    """Every job-detail HTML capture on Greenhouse, Lever, and Ashby in one crawl.

    Reads the index files directly: each host spans only a few dozen cdx blocks per crawl, so one
    pass is far cheaper than a query per firm.
    """
    for ats, pats in INVENTORY_PATTERNS.items():
        if ats_list is not None and ats not in ats_list:
            continue
        for pat in pats:
            for row in _cdx_query_files(client, crawl_id, pat):
                if not DETAIL[ats].search(row["url"]) or "html" not in (row.get("mime") or "html"):
                    continue
                yield {**row, "ats": ats, "slug": board_slug(row["url"], ats), "crawl": crawl_id}


def slug_candidates(name, first_word=True):
    """Guess ATS slugs from a company name, e.g. 'Rocket Companies, Inc.' -> rocketcompanies, rocket."""
    n = re.sub(r"\(.*?\)", " ", name.lower())
    n = re.sub(r"\b(inc|corp|corporation|co|company|ltd|plc|holdings|group|the|llc|n\.v|s\.a)\b\.?", " ", n)
    words = re.findall(r"[a-z0-9]+", n)
    if not words:
        return []
    c = ["".join(words), "-".join(words)] + ([words[0]] if first_word else [])
    return list(dict.fromkeys(c))
