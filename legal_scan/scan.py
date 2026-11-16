import sys, re, json, os, subprocess, difflib, hashlib
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
SD = os.path.dirname(os.path.abspath(__file__)); CACHE = SD + "/xml"; os.makedirs(CACHE, exist_ok=True)
D0 = "2021-01-01"
ACTS = {
 "ukpga/1996/18": "Employment Rights Act 1996", "ukpga/2006/46": "Companies Act 2006", "ukpga/2003/1": "Income Tax (Earnings and Pensions) Act 2003",
 "ukpga/2007/3": "Income Tax Act 2007", "ukpga/1992/12": "Taxation of Chargeable Gains Act 1992", "ukpga/1984/51": "Inheritance Tax Act 1984",
 "ukpga/1994/23": "Value Added Tax Act 1994", "ukpga/2001/2": "Capital Allowances Act 2001", "ukpga/2010/4": "Corporation Tax Act 2010",
 "ukpga/2009/4": "Corporation Tax Act 2009", "ukpga/1992/4": "Social Security Contributions and Benefits Act 1992", "ukpga/2018/12": "Data Protection Act 2018",
 "ukpga/2010/15": "Equality Act 2010", "ukpga/2015/15": "Consumer Rights Act 2015", "ukpga/1980/58": "Limitation Act 1980", "ukpga/1986/45": "Insolvency Act 1986",
 "ukpga/1988/50": "Housing Act 1988", "ukpga/2004/34": "Housing Act 2004", "ukpga/2008/30": "Pensions Act 2008", "ukpga/1993/48": "Pension Schemes Act 1993",
 "ukpga/2002/22": "Employment Act 2002", "ukpga/1998/39": "National Minimum Wage Act 1998", "ukpga/1989/41": "Children Act 1989", "ukpga/2000/8": "Financial Services and Markets Act 2000",
}
def get(act, ver):
    f = f"{CACHE}/{act.replace('/','_')}_{ver or 'cur'}.xml"
    if os.path.exists(f) and os.path.getsize(f) > 1000: return f
    url = f"https://www.legislation.gov.uk/{act}/{ver + '/' if ver else ''}data.xml"
    r = subprocess.run(["curl", "-sS", "-m", "300", "-L", "-A", "research-script", "-o", f, "-w", "%{http_code}", url], capture_output=True, text=True)
    if r.stdout.strip() != "200": 
        if os.path.exists(f): os.remove(f)
        return None
    return f
SKIP = {"Metadata", "Commentary", "Commentaries", "CommentaryRef", "Footnotes", "FootnoteRef", "Number", "Pnumber"}
def txt(e):
    parts = []
    def walk(x):
        if x.tag.split('}')[-1] in SKIP: 
            return
        if x.text and x.text.strip(): parts.append(x.text.strip())
        for c in x:
            walk(c)
            if c.tail and c.tail.strip(): parts.append(c.tail.strip())
    walk(e); return re.sub(r"\s+", " ", " ".join(parts))
ID = re.compile(r"^(section|schedule-[\w]+-paragraph)-[\w-]+$")
def sections(f):
    out = {}
    ctx = ET.iterparse(f, events=("start",)); 
    root = ET.parse(f).getroot(); ns = root.tag.split('}')[0] + '}'
    title = {}
    def visit(e, t):
        tag = e.tag.split('}')[-1]
        if tag == "P1group":
            tt = e.find(ns + "Title"); t = txt(tt) if tt is not None else t
        i = e.get("id")
        if tag == "P1" and i and ID.match(i): out[i] = (t, txt(e)); return
        for c in e: visit(c, t)
    visit(root, "")
    return out
NUMW = r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|eighteen|twenty|twenty-one|twenty-eight|thirty|sixty|ninety|\d[\d,\.]*%?|£[\d,\.]+)"
UNITS = r"(day|days|week|weeks|month|months|year|years|hour|hours|per|cent|pence|pounds?|million|thousand|%|£)"
REFPRE = {"section","sections","subsection","subsections","paragraph","paragraphs","regulation","regulations","schedule","part","chapter","article","sub-paragraph","sub-paragraphs","rule","rules","step","item","heading","table","tables","column","box","class","condition","case","group","number","no","no.","chapter","paras","para","s.","ss."}
def numtok(s): return re.fullmatch(NUMW, s.strip(".,;:()"), re.I) is not None
def cands(act, name):
    fc, fo = get(act, ""), get(act, D0)
    if not fc or not fo: return None
    A, B = sections(fo), sections(fc); res = []
    for i, (t, b) in B.items():
        if i not in A: continue
        a = A[i][1]
        if a == b: continue
        wa, wb = a.split(), b.split()
        sm = difflib.SequenceMatcher(None, wa, wb, autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op != "replace": continue
            o, n = wa[i1:i2], wb[j1:j2]
            if not (1 <= len(o) <= 3 and 1 <= len(n) <= 3): continue
            if not (any(numtok(x) for x in o) and any(numtok(x) for x in n)): continue
            if " ".join(o).lower() == " ".join(n).lower(): continue
            pre = wa[max(0, i1-16):i1]; post = wa[i2:i2+4]
            if pre and pre[-1].lower().strip(",;:") in REFPRE: continue
            if re.fullmatch(r"\(?\d+[A-Za-z]*\)?", " ".join(o).strip(".,;:")) and (pre and pre[-1].startswith("(") or " ".join(o).startswith("(")): continue
            if not (re.search(UNITS, " ".join(post[:2] + o + n), re.I) or any(x.startswith("£") for x in o + n)): continue
            res.append({"act": act, "act_name": name, "id": i, "title": t, "old": " ".join(o), "new": " ".join(n), "ctx": " ".join(pre), "post": " ".join(post), "ctx_new": " ".join(wb[max(0, j1-16):j1])})
    return res
if __name__ == "__main__":
    sel = sys.argv[1:] or list(ACTS)
    allc = {}
    def run(a):
        try: return a, cands(a, ACTS[a])
        except Exception as e: return a, f"ERR {e}"
    with ThreadPoolExecutor(4) as ex:
        for a, r in ex.map(run, sel):
            print(a, ACTS[a], "->", (len(r) if isinstance(r, list) else r)); allc[a] = r
    json.dump(allc, open(SD + "/cands.json", "w"), indent=1)
