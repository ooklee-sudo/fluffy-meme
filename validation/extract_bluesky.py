import glob, numpy as np, pandas as pd, pyarrow.parquet as pq
ALPHA='234567abcdefghijklmnopqrstuvwxyz'; LUT=np.full(256,-1,dtype=np.int64)
for i,ch in enumerate(ALPHA): LUT[ord(ch)]=i
def tid_us(rk):
    """rk: array of 13-char TIDs -> microseconds since epoch (NaN if malformed)."""
    b=np.frombuffer(''.join(rk).encode(),dtype=np.uint8).reshape(-1,13)
    v=LUT[b]; ok=(v>=0).all(1)
    x=np.zeros(len(rk),dtype=np.int64)
    for k in range(13): x=(x<<5)|np.maximum(v[:,k],0)
    return np.where(ok,(x>>10),-1)
def rkey(u):  # at://did/app.bsky.feed.post/rkey
    return u.str.rsplit('/',n=1).str[-1]
out=[]
for f in sorted(glob.glob('bsky/s*.parquet')):
    t=pq.read_table(f,columns=['uri','reply_to']).to_pandas()
    t=t[t.uri.str.contains('app.bsky.feed.post/')]
    rk=rkey(t.uri); ok=rk.str.len()==13
    t=t[ok]; ts=tid_us(rk[ok].tolist())
    rp=t.reply_to.where(t.reply_to.notna(),None)
    pr=rkey(rp.dropna().astype(str)); pok=pr.str.len()==13
    pts=np.full(len(t),-1,dtype=np.int64)
    idx=np.where(t.reply_to.notna().values)[0]
    pts[idx[pok.values]]=tid_us(pr[pok].tolist())
    out.append(pd.DataFrame({'t':ts,'pt':pts,'is_reply':t.reply_to.notna().values}))
    print(f,len(t),flush=True)
D=pd.concat(out,ignore_index=True)
D['ts']=pd.to_datetime(D.t,unit='us',errors='coerce')
D.to_parquet('bsky_tid.parquet')
print(D.ts.dt.floor('D').value_counts().sort_index().tail(15))
