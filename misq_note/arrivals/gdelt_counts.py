import sys, io, zipfile, urllib.request, ssl, time, json, os
import pandas as pd
def one(d):
    out=f'gdelt/{d}.json'
    if os.path.exists(out): return
    url=f'https://storage.googleapis.com/data.gdeltproject.org/events/{d}.export.CSV.zip'
    for k in range(6):
        try:
            b=urllib.request.urlopen(url,timeout=90).read(); break
        except Exception as e:
            if '404' in str(e): json.dump({'missing':True},open(out,'w')); return
            time.sleep(2*(k+1)); b=None
    if b is None: return
    z=zipfile.ZipFile(io.BytesIO(b)); df=pd.read_csv(z.open(z.namelist()[0]),sep='\t',header=None,low_memory=False,usecols=[7,17,28,27,29,53],dtype=str)
    df.columns=['a1c','a2c','base','root','quad','geoc']
    r=df.root; 
    irn=((df.a1c=='IRN')|(df.a2c=='IRN')|(df.geoc=='IR'))
    conf=r.isin(['18','19','20'])
    us_chn=(((df.a1c=='USA')&(df.a2c=='CHN'))|((df.a1c=='CHN')&(df.a2c=='USA')))&df.quad.isin(['3','4'])
    json.dump(dict(N_ALL=int(len(df)),E_IRN=int((conf&irn).sum()),E_WORLD_CONF=int(conf.sum()),E_RIOT=int((df.base=='145').sum()),E_USCHN=int(us_chn.sum())),open(out,'w'))
if __name__=='__main__':
    ds=[l.strip() for l in open(sys.argv[1])]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(8) as ex: list(ex.map(one,ds))
