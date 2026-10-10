import json, subprocess, os, collections
GIT=['git','-C','/home/user/aider-ai/aider.git']
commits=json.load(open('commits.json'))
shas=set()
for c in commits:
    for f in c['files']:
        for k in ('old','new'):
            if set(f[k])!={'0'}: shas.add(f[k])
os.makedirs('blobs',exist_ok=True)
inp='\n'.join(sorted(shas))+'\n'
out=subprocess.run(GIT+['cat-file','--batch'],input=inp.encode(),capture_output=True).stdout
i=0;n=0
while i<len(out):
    j=out.index(b'\n',i); hdr=out[i:j].split()
    sha=hdr[0].decode(); size=int(hdr[2]); body=out[j+1:j+1+size]
    open(f'blobs/{sha}.py','wb').write(body); n+=1
    i=j+1+size+1
print('blobs',n,len(shas))
