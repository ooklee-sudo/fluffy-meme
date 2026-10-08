import numpy as np, json
from scipy import stats
rng=np.random.default_rng(20261008)
DAYS=7; WPD=1440; W=DAYS*WPD
LBAR=0.5; GAM=0.6; KSH=25.0   # baseline mean/min, diurnal amplitude, gamma shape of Z_t
H=5          # Tier-2 cooldown windows
CAMP=60      # campaign length (windows)
ALPHA=0.001
R=300
m=np.arange(W)%WPD
lam0=LBAR*(1+GAM*np.sin(2*np.pi*(m-540)/WPD))   # peak 15:00
vol=lam0/LBAR                                    # benign traffic volume index (prop. to lam0)

def nb_q(mu,alpha):
    p=KSH/(KSH+mu)
    return stats.nbinom.ppf(1-alpha,KSH,p)      # smallest K with F(K)>=1-alpha
Kt=nb_q(lam0,ALPHA)
Kfix=nb_q(np.array([LBAR]),ALPHA)[0]
Kpois_fix=stats.poisson.ppf(1-ALPHA,LBAR)

def gen(a,e,attack=True):
    Z=rng.gamma(KSH,1/KSH,(R,W))
    xb=rng.poisson(lam0*Z)
    mal=np.zeros((R,W)); vis=np.zeros((R,W),int)
    start=np.zeros((R,DAYS),int)
    if attack:
        for d in range(DAYS):
            s=d*WPD+rng.integers(0,WPD-CAMP,R)
            start[:,d]=s
            for j in range(CAMP):
                idx=s+j
                mal[np.arange(R),idx]=rng.poisson(a,R)
        # visible to regex: each malicious prompt flagged w.p. 1-e
        vis=rng.binomial(mal.astype(int),1-e)
    return xb+vis, mal, start

def cooled(trig):
    c=np.cumsum(trig,axis=1)
    on=np.zeros_like(trig)
    # on[t]=any trig in [t-H,t-1]
    cs=np.concatenate([np.zeros((trig.shape[0],1),int),c],axis=1)  # cs[:,t]=sum trig[:t]
    t=np.arange(W)
    lo=np.maximum(t-H,0)
    on=(cs[:,t]-cs[:,lo])>0
    return on

def trig_C(x): return x>Kt
def trig_B(x): return x>Kfix
def make_cusum(h,k=0.5):
    sd=np.sqrt(lam0+lam0**2/KSH)
    def f(x):
        z=(x-lam0)/sd
        S=np.zeros(x.shape[0]); tr=np.zeros(x.shape,bool); cd=np.zeros(x.shape[0],int)
        for t in range(W):
            S=np.maximum(0,S+z[:,t]-k)
            hit=S>h
            tr[:,t]=hit; S[hit]=0
        return tr
    return f

def metrics(trig,mal,start,attack):
    on=cooled(trig)
    share=(on*vol).sum(1)/vol.sum()
    out={'gpu_share':share.mean()}
    if attack:
        cov=(mal*on).sum(1)/np.maximum(mal.sum(1),1)
        out['coverage']=cov.mean()
        det=[];delay=[]
        for d in range(DAYS):
            s=start[:,d]
            hit=np.zeros(R,bool);dl=np.full(R,np.nan)
            for j in range(CAMP):
                tt=trig[np.arange(R),s+j]
                new=tt&~hit
                dl[new]=j+1; hit|=tt
            det.append(hit); delay.append(dl)
        det=np.array(det); delay=np.array(delay)
        out['campaign_det']=det.mean()
        out['delay_med']=float(np.nanmedian(delay)) if det.any() else float('nan')
    return out

# benign calibration: false triggers/week and CUSUM h to match C
x,mal,st=gen(0,0,False)
trC=trig_C(x); fa_C=trC.sum(1).mean()
trB=trig_B(x); fa_B=trB.sum(1).mean()
lo,hi=1,40
for _ in range(14):
    h=(lo+hi)/2
    fa=make_cusum(h)(x).sum(1).mean()
    if fa>fa_C: lo=h
    else: hi=h
hC=(lo+hi)/2
cus=make_cusum(hC)
fa_D=cus(x).sum(1).mean()
base={'fa_per_week':{'C':fa_C,'B':fa_B,'D':fa_D},'h_cusum':hC,'Kfix':float(Kfix),'Kpois_fix':float(Kpois_fix),
      'Kt_min':float(Kt.min()),'Kt_max':float(Kt.max()),'gpu_benign':{
      'C':metrics(trC,mal,st,False)['gpu_share'],'B':metrics(trB,mal,st,False)['gpu_share'],'D':metrics(cus(x),mal,st,False)['gpu_share']}}
print(base)
res=[]
for a in [0.5,1,2,4,8,16]:
    for e in [0,0.5,0.9]:
        x,mal,st=gen(a,e,True)
        row={'a':a,'e':e}
        for name,tr in [('C',trig_C(x)),('B',trig_B(x)),('D',cus(x))]:
            row[name]=metrics(tr,mal,st,True)
        # random sampling matched to C's GPU share
        p=row['C']['gpu_share']; row['E']={'gpu_share':p,'coverage':p}
        res.append(row); print(row['a'],row['e'],{k:{kk:round(v,3) for kk,v in row[k].items()} for k in 'BCDE'})
# alpha sweep at a=2,e=0.5
sw=[]
for al in [0.01,0.001,0.0001]:
    Kt=nb_q(lam0,al)
    x,mal,st=gen(2,0.5,True)
    r=metrics(x>Kt,mal,st,True)
    xb,_,_=gen(0,0,False)
    r['fa']=(xb>Kt).sum(1).mean(); r['alpha']=al; sw.append(r); print(r)
Kt=nb_q(lam0,ALPHA)
json.dump({'base':base,'res':res,'sweep':sw},open('res.json','w'),indent=1,default=float)
# optimal-threshold table (Poisson, mu0=0.5)
tab=[]
mu0=0.5
for a in [1,2,4]:
    for ratio in [10,100,1000,10000]:   # pi1*rhoM / (pi0*C)
        c=1/ratio
        K=-1
        while True:
            k=K+1
            LR=np.exp(k*np.log((mu0+a)/mu0)-a)
            if LR>=c: break
            K+=1
        f0=stats.poisson.sf(K,mu0); f1=stats.poisson.cdf(K,mu0+a)
        tab.append({'a':a,'ratio':ratio,'K':K,'FPR':f0,'FNR':f1})
print(tab)
json.dump(tab,open('tab.json','w'),default=float)
