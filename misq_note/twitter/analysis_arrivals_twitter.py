import numpy as np, pandas as pd, json
from scipy import stats, optimize
d=pd.read_csv('tweets_in_office_parsed.csv.gz'); d['id']=d.url.str.extract(r'status/(\d+)')[0].map(int); d['ep']=d.id.map(lambda i:((i>>22)+1288834974657)/1000.0)
d['text']=d.text.fillna(''); d=d[~d.text.str.startswith('RT @')].sort_values('ep').reset_index(drop=True)
d['t']=pd.to_datetime(d.ep,unit='s',utc=True)
def analyze(ts,label,start,end):
    days=pd.date_range(start,end,tz='UTC',freq='D'); x=ts.dt.floor('D').value_counts().reindex(days,fill_value=0).sort_index().values
    m=x.mean(); D=((x-m)**2).sum()/m; df=len(x)-1; p=float(stats.chi2.sf(D,df))
    f=lambda lr:-stats.nbinom.logpmf(x,np.exp(lr),np.exp(lr)/(np.exp(lr)+m)).sum(); r=optimize.minimize_scalar(f,bounds=(-5,10),method='bounded'); lr=2*(-r.fun-stats.poisson.logpmf(x,m).sum())
    wk=pd.Series(x,index=days.tz_localize(None)); g=wk.groupby(wk.index.to_period('W')); mu=g.transform('mean').values; nweeks=g.ngroups
    pear=float(((x-mu)**2/np.maximum(mu,1e-9)).sum()/(len(x)-nweeks))
    ia=np.diff(ts.map(lambda z:z.timestamp()).values); ia=ia[ia>0]; cv=float(ia.std()/ia.mean()); ks=stats.kstest(ia,'expon',args=(0,ia.mean()))
    return dict(label=label,n=int(x.sum()),days=len(x),mean=float(m),var=float(x.var(ddof=1)),dispersion_index=float(D),chi2_p=p,NB_size=float(np.exp(r.x)),LR_p=float(stats.chi2.sf(lr,1)/2),week_FE_pearson=pear,ia_mean_h=float(ia.mean()/3600),ia_median_h=float(np.median(ia)/3600),ia_cv=cv,ks_p=float(ks.pvalue))
S,E='2017-01-21','2021-01-07'
R={'all_original':analyze(d.t,'all original tweets',S,E)}
oil=pd.read_csv('frame_oil_iran.csv',dtype={'id':str}); tar=pd.read_csv('frame_tariff.csv',dtype={'id':str})
for name,fr in (('oil_iran',oil),('tariff_trade',tar)):
    ts=pd.to_datetime(fr.ep,unit='s',utc=True); R[name]=analyze(ts,name,S,E)
# time-of-day non-homogeneity: share of tweets by ET hour and chi-square vs uniform
h=d.t.dt.tz_convert('America/New_York').dt.hour; cnt=h.value_counts().reindex(range(24),fill_value=0); R['hour_of_day_chi2_uniform_p']=float(stats.chisquare(cnt.values).pvalue); R['hour_share_peak']=float(cnt.max()/cnt.sum()); R['hour_peak']=int(cnt.idxmax()); R['hour_share_min']=float(cnt.min()/cnt.sum())
# Poisson with hour-of-day x weekday means: Pearson dispersion of hourly counts
hrs=pd.date_range(S,E,tz='UTC',freq='h'); hc=d.t.dt.floor('h').value_counts().reindex(hrs,fill_value=0).sort_index(); lt=hrs.tz_convert('America/New_York'); key=pd.Series(list(zip(lt.hour,lt.weekday)),index=hrs)
mu=hc.groupby(key.values).transform('mean'); R['hourly_pearson_given_hour_weekday_mean']=float(((hc-mu)**2/np.maximum(mu,1e-9)).sum()/(len(hc)-len(set(key.values))))
json.dump(R,open('results_arrivals_twitter.json','w'),indent=1); print(json.dumps(R,indent=1))
