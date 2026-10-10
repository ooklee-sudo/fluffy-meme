import subprocess, re, json, sys
GIT=['git','-C','/home/user/aider-ai/aider.git']
SATD=re.compile(r'#.*\b(TODO|FIXME|HACK|XXX|KLUDGE|WORKAROUND)\b',re.I)
BROAD=re.compile(r'#.*(\b(TODO|FIXME|HACK|XXX|KLUDGE|WORKAROUND|HACKY|TEMPORARY|TEMPORARILY|UGLY|QUICK FIX|FOR NOW|NOT IDEAL|REFACTOR LATER|CLEAN ?UP LATER|SHOULD REFACTOR|NEEDS? (A )?(REFACTOR|CLEANUP))\b)',re.I)
cmd=GIT+['log','--no-merges','-r','--raw','--no-abbrev','--no-renames','-p','-U0','--diff-filter=AM',
 '--format=@@@%H|%an|%cn|%ad|%P','--date=short','--','*.py']
p=subprocess.Popen(cmd,stdout=subprocess.PIPE,text=True,errors='replace')
commits=[];cur=None;curfile=None
for line in p.stdout:
    if line.startswith('@@@'):
        h,an,cn,ad,par=line[3:].rstrip('\n').split('|',4)
        cur=dict(h=h,an=an,cn=cn,date=ad,parents=par.split(),files=[]);commits.append(cur);curfile=None
    elif cur is None: continue
    elif line.startswith(':'):
        meta,path=line.rstrip('\n').split('\t',1)
        m=meta.split()
        cur['files'].append(dict(path=path,old=m[2],new=m[3],added=0,satd=0,broad=0,comm=0))
    elif line.startswith('diff --git'):
        path=line.split(' b/',1)[1].rstrip('\n')
        curfile=next((f for f in cur['files'] if f['path']==path),None)
    elif line.startswith('+') and not line.startswith('+++') and curfile is not None:
        curfile['added']+=1
        if SATD.search(line): curfile['satd']+=1
        if BROAD.search(line): curfile['broad']+=1
        if line[1:].lstrip().startswith('#'): curfile['comm']+=1
json.dump(commits,open('commits3.json','w'))
print(len(commits),sum(len(c['files']) for c in commits))
