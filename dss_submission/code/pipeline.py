import subprocess, re, json, sys, os, collections, shutil
repo, slug = sys.argv[1], sys.argv[2]          # e.g. pydantic_pydantic-ai  pydantic/pydantic-ai
SINCE='2025-01-01'; MINF=int(os.environ.get('MINF',8)); MAXC=int(os.environ.get('MAXC',4000))
G=['git','-C',f'/home/user/full/{repo}.git']
def run(args,inp=None,text=True):
    return subprocess.run(G+args,input=inp,capture_output=True,text=text,errors='replace' if text else None).stdout
TRAIL='co-authored-by: *claude|generated with \\[?claude'
flag=set(run(['log','--no-merges',f'--since={SINCE}','-i','-E',f'--grep={TRAIL}','--format=%H']).split())
agent_names={'Copilot','Claude'}
# 1 commit list with py file entries (trees only)
out=run(['log','--no-merges',f'--since={SINCE}','-r','--raw','--no-abbrev','--no-renames','--diff-filter=AM','--format=@@@%H|%ae|%an|%ad','--date=short','--','*.py'])
commits=[];cur=None
for line in out.splitlines():
    if line.startswith('@@@'):
        h,ae,an,ad=line[3:].split('|',3); cur=dict(h=h,ae=ae.lower(),an=an,date=ad,files=[]); commits.append(cur)
    elif line.startswith(':') and cur is not None:
        meta,path=line.split('\t',1); m=meta.split(); cur['files'].append(dict(path=path,old=m[2],new=m[3],added=0,satd=0,broad=0,comm=0))
for c in commits: c['llm']=int(c['h'] in flag or c['an'] in agent_names); c['agent']=int(c['an'] in agent_names)
cnt=collections.defaultdict(lambda:[0,0])
for c in commits:
    if not c['agent']: cnt[c['ae']][c['llm']]+=1
sel={a for a,(u,f) in cnt.items() if f>=MINF and u>=MINF}
S=[c for c in commits if c['ae'] in sel]
if len(S)>MAXC: S=S[:MAXC]
print(repo,'py-commits',len(commits),'flagged',sum(c['llm'] for c in commits),'selected authors',len(sel),'selected commits',len(S),'flagged among sel',sum(c['llm'] for c in S),flush=True)
if not S: sys.exit()
# 2 fetch blobs in batches
shas=sorted({f[k] for c in S for f in c['files'] for k in ('old','new') if set(f[k])!={'0'}})
def missing(lst):
    return list(lst)
miss=[]
print('blobs',len(shas),'missing',len(miss),flush=True)
for i in range(0,len(miss),400):
    r=subprocess.run(G+['fetch','-q','--no-tags','--no-write-fetch-head','origin']+miss[i:i+400],capture_output=True,text=True,env={**os.environ,'GIT_LFS_SKIP_SMUDGE':'1'})
    if r.returncode!=0: print('fetch error',r.stderr[:300],flush=True); break
    print('fetched',min(i+400,len(miss)),flush=True)
miss2=[]
print('fetch pass complete',flush=True)
# 3 diffs
SATD=re.compile(r'#.*\b(TODO|FIXME|HACK|XXX|KLUDGE|WORKAROUND)\b',re.I)
BROAD=re.compile(r'#.*(\b(TODO|FIXME|HACK|XXX|KLUDGE|WORKAROUND|HACKY|TEMPORARY|TEMPORARILY|UGLY|QUICK FIX|FOR NOW|NOT IDEAL|REFACTOR LATER|CLEAN ?UP LATER|SHOULD REFACTOR|NEEDS? (A )?(REFACTOR|CLEANUP))\b)',re.I)
hs='\n'.join(c['h'] for c in S)+'\n'
p=subprocess.run(G+['log','--no-walk=unsorted','--stdin','-p','-U0','--no-renames','--diff-filter=AM','--format=@@@%H','--','*.py'],input=hs,capture_output=True,text=True,errors='replace')
idx={c['h']:c for c in S};cur=None;cf=None
for line in p.stdout.splitlines():
    if line.startswith('@@@'): cur=idx.get(line[3:].strip());cf=None
    elif cur is None: continue
    elif line.startswith('diff --git'):
        path=line.split(' b/',1)[1]; cf=next((f for f in cur['files'] if f['path']==path),None)
    elif line.startswith('+') and not line.startswith('+++') and cf is not None:
        cf['added']+=1
        if SATD.search(line): cf['satd']+=1
        if BROAD.search(line): cf['broad']+=1
        if line[1:].lstrip().startswith('#'): cf['comm']+=1
# 4 ruff on blobs
bd=f'blobs_{repo}'; shutil.rmtree(bd,ignore_errors=True); os.makedirs(bd)
have=[s for s in shas if s not in set(miss2)]
chunks=[]
res=subprocess.run(G+['cat-file','--batch'],input=('\n'.join(have)+'\n').encode(),capture_output=True).stdout
i=0
while i<len(res):
    j=res.index(b'\n',i); hdr=res[i:j].split(); size=int(hdr[2]); open(f'{bd}/{hdr[0].decode()}.py','wb').write(res[j+1:j+1+size]); i=j+1+size+1
bc=collections.Counter()
files=sorted(os.listdir(bd))
for gi in range(0,len(files),5000):
    gd=f'{bd}_g{gi//5000}'; os.makedirs(gd,exist_ok=True)
    for fn in files[gi:gi+5000]: shutil.move(f'{bd}/{fn}',f'{gd}/{fn}')
    r=subprocess.run(['ruff','check','--isolated','--ignore-noqa','--select','C901,PLR0911,PLR0912,PLR0913,PLR0915,PLR2004,SIM,ERA001,B','--config','lint.mccabe.max-complexity=10','--output-format','json','--no-cache',gd],capture_output=True,text=True)
    if r.returncode not in (0,1): print('ruff rc',r.returncode,r.stderr[:200],flush=True)
    for v in json.loads(r.stdout or '[]'): bc[os.path.basename(v['filename'])[:-3]]+=1
    shutil.rmtree(gd,ignore_errors=True)
print('ruff blobs with warnings',len(bc),flush=True)
rows=[]
for c in S:
    dn=0
    for f in c['files']:
        o=0 if set(f['old'])=={'0'} else bc.get(f['old'],0); n=bc.get(f['new'],0)
        dn+=max(0,n-o)
    rows.append(dict(repo=slug,h=c['h'],ae=c['ae'],an=c['an'],agent=c['agent'],date=c['date'],llm=c['llm'],debt=dn,lines=sum(f['added'] for f in c['files']),
        satd=sum(f['satd'] for f in c['files']),broad=sum(f['broad'] for f in c['files']),comm=sum(f['comm'] for f in c['files']),
        testonly=int(all(f['path'].startswith(('tests/','test/','benchmark/')) or '/tests/' in f['path'] or '/test_' in f['path'] for f in c['files']))))
import pandas as pd
pd.DataFrame(rows).to_csv(f'out_{repo}.csv',index=False)
shutil.rmtree(bd,ignore_errors=True)
print('done',repo,len(rows),flush=True)
