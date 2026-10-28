"""Stream one WDC JobPosting part: aggregate per hiring organization and extract visual-role candidate postings.
Usage: python build_panel.py CRAWL PART_INDEX OUT_DIR [WORK_DIR]
Outputs OUT_DIR/<crawl>_part<k>_agg.pkl (per-org counts) and OUT_DIR/<crawl>_part<k>_cand.pkl (candidate postings)."""
import sys, os, gzip, re, subprocess, unicodedata, time
import pandas as pd
CRAWL, K, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
WORK = sys.argv[4] if len(sys.argv) > 4 else '/tmp'
os.makedirs(OUT, exist_ok=True)
URL = f'https://data.dws.informatik.uni-mannheim.de/structureddata/{CRAWL}/quads/classspecific/JobPosting/part_{K}.gz'
path = f'{WORK}/{CRAWL}_part{K}.gz'
TYPE = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
VISUAL = re.compile(r"graphic design|graphic artist|graphics design|illustrator|art director|motion (?:graphic|design)|video editor|videograph|photograph|animator|3d (?:artist|modell?er)|ui/ux|ux/ui|ux designer|ui designer|visual design|creative design|web design|brand design|concept artist|content creator|grafikdesign|mediengestalt|grafiker|graphiste|infographiste|dise[ñn]ador|ilustrador|grafisch|webdesign|designer gr|デザイナー|イラストレーター|映像|動画|graphic|designer")
COMP = re.compile(r"compliance|legal counsel|data protection|privacy|dpo\b|ai governance|responsible ai|ethic|risk manager|creative director|head of design|design lead|datenschutz|juriste|jurist|rechtsanwalt|brand manager|brand governance")
GENAI = re.compile(r"midjourney|stable diffusion|dall[-\s]?e|firefly|generative ai|generative artificial|gen[-\s]?ai\b|genai|chat\s?gpt|openai|ai[-\s]generated|ai[-\s]tools?|ai[-\s]powered|text[-\s]to[-\s]image|text[-\s]to[-\s]video|runway|leonardo\.ai|generative ki|ki[-\s]generiert|ia generativa|生成ai|生成ＡＩ")
SUFFIX = {'inc','llc','ltd','limited','gmbh','ag','sa','sas','srl','bv','nv','co','corp','corporation','company','plc','kk','llp','lp','pty','ab','as','oy','sarl','spa'}
def norm(n):
    n = unicodedata.normalize('NFKC', n or '').lower()
    n = re.sub(r'[^\w\s]', ' ', n); toks = [t for t in n.split() if t not in SUFFIX]
    return ' '.join(toks)[:80]
def lit(o):
    if o.startswith('"'):
        e = o.rfind('"'); s = o[1:e]; return s.encode().decode('unicode_escape', 'ignore') if '\\' in s else s
    return o[1:-1] if o.startswith('<') else o
def split_quad(line):
    line = line.rstrip()
    if line.endswith('.'): line = line[:-1].rstrip()
    g = line.rfind(' <'); graph = line[g + 2:-1] if line.endswith('>') else ''
    s, rest = line[:g].split(' ', 1); p, o = rest.split(' ', 1); return s, p[1:-1], o.strip(), graph
agg, cand = {}, []
def flush(nodes, graph):
    for n, props in nodes.items():
        t = props.get(TYPE)
        if not t or 'JobPosting' not in t[0]: continue
        def g(name):
            for k, v in props.items():
                if k.endswith('/' + name): return v[0]
        org = g('hiringOrganization'); name = None
        if org:
            if org.startswith('_:') and org in nodes:
                for k, v in nodes[org].items():
                    if k.endswith('/name'): name = lit(v[0])
            else: name = lit(org)
        key = norm(name) if name else ''
        if not key: continue
        title = lit(g('title') or ''); desc = lit(g('description') or '')
        tl = title.lower(); dl = desc.lower()
        host = graph.split('/')[2] if graph.count('/') >= 2 else ''
        a = agg.setdefault(key, [0, 0, 0, 0, 0, host, name])
        a[0] += 1
        gen = bool(GENAI.search(tl) or GENAI.search(dl[:4000]))
        if gen: a[3] += 1
        if COMP.search(tl): a[2] += 1; cand.append(('comp', key, host, title[:200], '', None))
        if VISUAL.search(tl):
            a[1] += 1
            if gen: a[4] += 1
            loc = g('jobLocation'); date = lit(g('datePosted') or '')[:10]
            cand.append(('visual', key, host, title[:200], desc[:2500], date))
t0 = time.time()
if not os.path.exists(path):
    for attempt in range(4):
        r = subprocess.run(['curl', '-sS', '-m', '3000', '-L', '-o', path, URL]); 
        if r.returncode == 0 and os.path.getsize(path) > 1000: break
        time.sleep(5)
nodes, cur, n = {}, None, 0
with gzip.open(path, 'rt', encoding='utf-8', errors='replace') as f:
    for line in f:
        try: s, p, o, graph = split_quad(line)
        except Exception: continue
        if graph != cur:
            if cur is not None: flush(nodes, cur)
            nodes, cur = {}, graph
        nodes.setdefault(s, {}).setdefault(p, []).append(o); n += 1
if cur is not None: flush(nodes, cur)
os.remove(path)
A = pd.DataFrame([[k] + v for k, v in agg.items()], columns=['org_key', 'n_total', 'n_visual', 'n_comp', 'n_genai', 'n_genai_visual', 'host', 'org_name'])
A.to_pickle(f'{OUT}/{CRAWL}_part{K}_agg.pkl')
pd.DataFrame(cand, columns=['kind', 'org_key', 'host', 'title', 'description', 'date']).to_pickle(f'{OUT}/{CRAWL}_part{K}_cand.pkl')
print(CRAWL, K, 'quads', n, 'orgs', len(A), 'postings', int(A.n_total.sum()), 'visual', int(A.n_visual.sum()), 'cand', len(cand), 'sec', int(time.time() - t0), flush=True)
