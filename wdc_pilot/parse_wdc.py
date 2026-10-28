"""Parse a Web Data Commons class-specific JobPosting N-Quads part into one row per posting.
Usage: python parse_wdc.py PART.gz OUT.pkl"""
import sys, gzip, re, json
import pandas as pd

TYPE = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
def split_quad(line):
    line = line.rstrip()
    if line.endswith('.'): line = line[:-1].rstrip()
    g = line.rfind(' <')
    graph = line[g + 2:-1] if line.endswith('>') else ''
    rest = line[:g]
    s, rest = rest.split(' ', 1)
    p, o = rest.split(' ', 1)
    return s, p[1:-1], o.strip(), graph
def lit(o):
    if o.startswith('"'):
        e = o.rfind('"'); return o[1:e].encode().decode('unicode_escape', 'ignore') if '\\' in o[1:e] else o[1:e]
    return o[1:-1] if o.startswith('<') else o

def flush(nodes, graph, out):
    for n, props in nodes.items():
        if not any(TYPE in k and ('JobPosting' in v[0]) for k, v in props.items() if k == TYPE): continue
        def g(name):
            for k, v in props.items():
                if k.endswith('/' + name): return v[0]
            return None
        org = g('hiringOrganization'); org_name = None
        if org is not None:
            if org.startswith('_:') and org in nodes:
                for k, v in nodes[org].items():
                    if k.endswith('/name'): org_name = lit(v[0])
            else: org_name = lit(org)
        loc = g('jobLocation'); country = None
        if loc and loc.startswith('_:') and loc in nodes:
            def dig(node, depth=0):
                for k, v in nodes.get(node, {}).items():
                    if k.endswith('/addressCountry'):
                        return lit(v[0])
                    if depth < 2 and v[0].startswith('_:'):
                        r = dig(v[0], depth + 1)
                        if r: return r
            country = dig(loc)
        out.append({'url': graph, 'title': lit(g('title') or ''), 'org': org_name, 'date': lit(g('datePosted') or ''),
                    'description': lit(g('description') or '')[:6000], 'country': country,
                    'category': lit(g('occupationalCategory') or '') or None})

def main():
    out, nodes, cur = [], {}, None
    with gzip.open(sys.argv[1], 'rt', encoding='utf-8', errors='replace') as f:
        for line in f:
            try: s, p, o, graph = split_quad(line)
            except Exception: continue
            if graph != cur:
                if cur is not None: flush(nodes, cur, out)
                nodes, cur = {}, graph
            nodes.setdefault(s, {}).setdefault(p, []).append(o)
    if cur is not None: flush(nodes, cur, out)
    df = pd.DataFrame(out); df.to_pickle(sys.argv[2]); print(len(df), 'postings'); print(df.head(3).T.to_string()[:1500])
main()
