import lzma, struct, glob, os, numpy as np, pandas as pd, sys
src=sys.argv[1] if len(sys.argv)>1 else 'raw5m_duka/WTI'; out=sys.argv[2] if len(sys.argv)>2 else 'raw5m_duka/ticks_WTI.csv.gz'
rows=[]
for f in sorted(glob.glob(f'{src}/*.bi5')):
    tag=os.path.basename(f)[:-4]; day,h=tag.split('_'); t0=pd.Timestamp(day,tz='UTC')+pd.Timedelta(hours=int(h))
    try: raw=lzma.decompress(open(f,'rb').read())
    except Exception as e: print('bad',f,e); continue
    n=len(raw)//20
    if n==0: continue
    a=np.frombuffer(raw[:n*20],dtype=np.dtype([('ms','>u4'),('ask','>u4'),('bid','>u4'),('av','>f4'),('bv','>f4')]))
    ep=t0.timestamp()+a['ms']/1000.0; mid=(a['ask'].astype(float)+a['bid'].astype(float))/2/1000.0
    rows.append(pd.DataFrame({'ep':ep,'mid':mid,'spread':(a['ask'].astype(float)-a['bid'])/1000.0}))
T=pd.concat(rows).sort_values('ep').reset_index(drop=True); T.to_csv(out,index=False,compression='gzip'); print(len(T),T.ep.min(),T.ep.max())
