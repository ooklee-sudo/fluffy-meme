import numpy as np, pandas as pd, re, zlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
d=pd.read_csv('tweets_in_office_parsed.csv.gz'); d['id']=d.url.str.extract(r'status/(\d+)')[0]; d['idn']=d.id.map(int)
d['ep']=d.idn.map(lambda i:((i>>22)+1288834974657)/1000.0); d['text']=d.text.fillna('')
d=d[~d.text.str.startswith('RT @')].sort_values('ep').reset_index(drop=True)
d['clean']=d.text.map(lambda s:re.sub(r'https?://\S+','',s).replace('&amp;','&').strip())
aep=d.ep.values; atext=d.clean.tolist(); aid={i:k for k,i in enumerate(d.id)}
def Z(s): return len(zlib.compress(s.encode('utf-8'),9))
def Nc(k):
    x=atext[k]
    if len(x)<20: return 0.0
    lo=np.searchsorted(aep,aep[k]-7*86400); c='\n'.join(atext[lo:k])[-30000:]; return (Z(c+'\n'+x)-Z(c))/Z(x)
tf=TfidfVectorizer(stop_words='english').fit([t for t in atext if len(t)>=20])
def Nt(k):
    x=atext[k]
    if len(x)<20: return 0.0
    lo=np.searchsorted(aep,aep[k]-7*86400); prev=[t for t in atext[lo:k] if len(t)>=20]
    if not prev: return np.nan
    return float(1-linear_kernel(tf.transform([x]),tf.transform(prev)).max())
f=pd.read_csv('frame_tariff.csv',dtype={'id':str}); f['gap']=f.ep.diff().fillna(1e9); f['keep']=f.gap>=3*3600
f['Nc']=[Nc(aid[i]) for i in f.id]; f['Nt']=[Nt(aid[i]) for i in f.id]
# daily S&P 500
w=pd.read_csv('spx_daily.csv',index_col=0); w.index=pd.to_datetime(w.index); sp=pd.to_numeric(w.iloc[:,0],errors='coerce'); sp=sp[sp>0]
r=100*np.log(sp/sp.shift(1)).dropna()
def vol(date,n):
    x=r[r.index<date].iloc[-n:]; return float(x.std()) if len(x)>=int(0.8*n) else np.nan
dates=pd.to_datetime(f.ep,unit='s',utc=True).dt.tz_localize(None).dt.normalize()
f['sd60']=[vol(x,60) for x in dates]; f['sd5']=[vol(x,5) for x in dates]; f['U']=np.log(f.sd5/f.sd60)
f['s30']=f.sd60*np.sqrt(30/1380)
f.drop(columns=['text']).to_csv('frame_features_tariff.csv',index=False); print(f[['Nc','Nt','sd60','U']].describe().round(3).to_string()); print(f.keep.sum(), f.sd60.isna().sum(), f.U.isna().sum())
