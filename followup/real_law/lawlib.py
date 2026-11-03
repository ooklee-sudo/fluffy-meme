import subprocess, re, json, os, hashlib, xml.etree.ElementTree as ET
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache"); os.makedirs(CACHE, exist_ok=True)
def get(url):
    f = os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest())
    if os.path.exists(f): return open(f, encoding="utf-8").read()
    r = subprocess.run(["curl","-sS","-m","45","-L","-A","research-script","-w","\n%{http_code}",url],capture_output=True,text=True)
    body, _, code = r.stdout.rpartition("\n")
    if code != "200": return None
    open(f, "w", encoding="utf-8").write(body); return body
SKIP = {"Metadata", "Commentary", "Commentaries", "CommentaryRef", "Footnotes", "FootnoteRef"}
def text(xml):
    try: root = ET.fromstring(xml)
    except Exception: return None
    parts = []
    def walk(e):
        if e.tag.split('}')[-1] in SKIP: return
        if e.text and e.text.strip(): parts.append(e.text.strip())
        for c in e:
            walk(c)
            if c.tail and c.tail.strip(): parts.append(c.tail.strip())
    walk(root); return re.sub(r"\s+", " ", " ".join(parts))
def section(act, n, ver):
    u = f"https://www.legislation.gov.uk/{act}/section/{n}/{ver}/data.xml" if ver != "current" else f"https://www.legislation.gov.uk/{act}/section/{n}/data.xml"
    x = get(u); return text(x) if x else None
