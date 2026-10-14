"""Check that each extracted quote occurs in the cited SEC exhibit (after whitespace/entity normalization)."""
import json,glob,re,html,subprocess,sys
UA="research ooklee@hanyang.ac.kr"
cache={}
def norm(t):
    t=re.sub(r'<[^>]+>',' ',t); t=html.unescape(t).replace('\xa0',' ')
    t=t.replace('’',"'").replace('“','"').replace('”','"')
    return re.sub(r'\s+','',t).lower()
res=[]
for f in sorted(glob.glob('chains2022/*.json')):
    for r in json.load(open(f)):
        if r['comps_pct'] is None: continue
        u=r['source_url']
        if u not in cache:
            cache[u]=norm(subprocess.run(["curl","-sS","-m","60","-A",UA,u],capture_output=True,text=True).stdout)
        q=norm(re.sub(r'\.\.\.|…','|',r['quote']))
        parts=[p for p in q.split('|') if p]
        ok=len(cache[u])>0 and all(p in cache[u] for p in parts)
        res.append((f.split('/')[1][:-5],r['quarter_label'],ok,len(cache[u])))
json.dump(res,open('quote_check_2022.json','w'))
bad=[x for x in res if not x[2]]
print(len(res),'rows;',len(bad),'not found'); [print(b) for b in bad]
