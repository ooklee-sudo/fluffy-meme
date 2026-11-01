# Weekly share of conversations mentioning a post-cutoff product, raw vs after template removal (Fig 3 data).
# Usage: DATA=<dir with all.parquet> python fig3_data.py   -> $DATA/fig3_data.csv
import os, pandas as pd
DATA=os.environ.get('DATA','/tmp/wc')
d=pd.read_parquet(DATA+'/all.parquet').reset_index(drop=True)
d['wk']=d.ts.dt.tz_localize(None).dt.to_period('W').dt.start_time
d['occ']=d.groupby(['wk','fp80']).cumcount(); d['ent']=d['prod'].astype(float)
g=d[d.model.str.startswith('gpt-3.5-turbo')|(d.model=='gpt-4-0314')]
out=pd.DataFrame({'raw':g.groupby('wk').ent.mean(),'dedup':g[g.occ<5].groupby('wk').ent.mean(),'n':g.groupby('wk').size()})
out.to_csv(DATA+'/fig3_data.csv'); print(out.raw.max(), out.dedup.max())
