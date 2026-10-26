import sys, pandas as pd, numpy as np
from lxml import etree
site=sys.argv[1]
def rows(path,tag,keys):
    out=[]
    for _,el in etree.iterparse(path,tag=tag):
        out.append(tuple(el.get(k) for k in keys)); el.clear()
    return out
P=pd.DataFrame(rows(f'{site}/Posts.xml','row',['Id','PostTypeId','ParentId','CreationDate']),columns=['Id','T','Parent','Created'])
C=pd.DataFrame(rows(f'{site}/Comments.xml','row',['Id','PostId','CreationDate']),columns=['Id','PostId','Created'])
P['Created']=pd.to_datetime(P.Created); C['Created']=pd.to_datetime(C.Created)
P['Id']=P.Id.astype(int); C['PostId']=C.PostId.astype(int)
P['Parent']=pd.to_numeric(P.Parent)
created=P.set_index('Id').Created
# reply delays (hours): answers -> question, comments -> post
ans=P[P['T']=='2'].copy(); ans['d']=(ans.Created-ans.Parent.map(created)).dt.total_seconds()/3600
com=C.copy(); com['d']=(com.Created-com.PostId.map(created)).dt.total_seconds()/3600
posting=pd.concat([P[['Created']],C[['Created']]])   # posts + comments = "posting events"
hour=posting.Created.dt.hour+posting.Created.dt.minute/60
prof=np.histogram(hour,bins=np.arange(25))[0]
loc=posting.Created.dt.tz_localize('UTC').dt.tz_convert('America/New_York')
prof_et=np.histogram(loc.dt.hour+loc.dt.minute/60,bins=np.arange(25))[0]
np.savez(f'{site}_ref.npz',prof=prof,prof_et=prof_et,ans=ans.d.dropna().clip(lower=0).values,com=com.d.dropna().clip(lower=0).values,
         span=[str(posting.Created.min()),str(posting.Created.max())],n=[len(P),len(C)])
print(site,len(P),len(C),posting.Created.min(),posting.Created.max(),'median ans delay h',ans.d.median(),'median comment delay h',com.d.median())
