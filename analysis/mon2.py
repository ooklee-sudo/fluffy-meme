import json,numpy as np
from scipy.optimize import brentq, minimize_scalar
from scipy.special import gammaln
c=json.load(open('azure/hourly.json'))
days=sorted({k.split()[0] for k in c})
A=np.array([[c.get(f"{d} {h}",0) for h in range(24)] for d in days],float)
prof=A.mean(0); K=24; pi=np.ones(K)/K
V=20.0
class Sys:
    def __init__(s,kind):
        s.kind=kind
        if kind=='ded':
            s.M=77; s.mubar=77.0; s.N=4000
            s.rho=lambda n:np.ones_like(n,float)
        else:
            s.M=1024; r=0.0088; s.mubar=s.M*(1+r)/(1+r*s.M); s.N=9000
            s.rho=lambda n:(1+r)/(1+r*np.minimum(n,s.M))
        n=np.arange(1,s.N+1); s.mu=np.minimum(n,s.M)*s.rho(n)
        s.lmu=np.log(s.mu); s.cum=np.cumsum(s.lmu)
    def d(s,l):
        if l<=1e-12: return 1.0
        n=np.arange(1,s.N+1)
        lp=np.concatenate([[0],n*np.log(l)-s.cum])
        lp-=lp.max(); p=np.exp(lp); p/=p.sum()
        return (np.arange(0,s.N+1)*p).sum()/l
    def D(s,l): return l*s.d(l)
sys_={k:Sys(k) for k in('ded','bat')}
def analyze(kind,V_=20.0,ratio=1.4,full=True):
    global V
    V=V_
    S=sys_[kind]; cap=S.mubar
    Lam=ratio*cap*prof/prof.mean()
    cache={}
    def dd(l):
        key=round(l,10)
        if key not in cache: cache[key]=S.d(l)
        return cache[key]
    def lam_p(p,k):
        if p>=V-1: return 0.0
        f=lambda l:V*(1-l/Lam[k])-p-dd(l)
        hi=min(Lam[k],cap)*(1-1e-7)
        if f(1e-9)<=0: return 0.0
        if f(hi)>0: return hi
        return brentq(f,1e-9,hi,xtol=1e-10)
    B=lambda l,k:V*(l-l*l/(2*Lam[k]))
    def stats(ps):  # list of 24 prices
        W=Pf=0
        for k in range(K):
            l=lam_p(ps[k],k); W+=pi[k]*(B(l,k)-l*dd(l)); Pf+=pi[k]*ps[k]*l
        return W,Pf
    # first best
    pfb=[];
    for k in range(K):
        r=minimize_scalar(lambda l:-(B(l,k)-l*dd(l)),bounds=(0,min(Lam[k],cap)*(1-1e-7)),method='bounded',options={'xatol':1e-9})
        pfb.append(V*(1-r.x/Lam[k])-dd(r.x))
    Wfb,Pfb=stats(pfb)
    # monopoly phase-specific
    pm=[]
    for k in range(K):
        r=minimize_scalar(lambda p:-p*lam_p(p,k),bounds=(0,V-1),method='bounded',options={'xatol':1e-8})
        pm.append(r.x)
    Wm,Pm=stats(pm)
    # flat objectives
    fW=minimize_scalar(lambda p:-stats([p]*K)[0],bounds=(0,V-1),method='bounded',options={'xatol':1e-7}).x
    fP=minimize_scalar(lambda p:-stats([p]*K)[1],bounds=(0,V-1),method='bounded',options={'xatol':1e-7}).x
    W0,P0=stats([0.0]*K)
    WfW,PfW=stats([fW]*K); WfP,PfP=stats([fP]*K)
    # best two-level (contiguous by rank) for profit and for welfare
    order=np.argsort(Lam)
    def twolevel(obj):
        best=None
        for g in range(1,K):
            lo=order[:g]; hi=order[g:]
            def val(pl,ph):
                ps=[0]*K
                for k in lo: ps[k]=pl
                for k in hi: ps[k]=ph
                return stats(ps)[obj]
            # coordinate ascent
            pl,ph=fW*0.5,fW*1.5
            for _ in range(6):
                pl=minimize_scalar(lambda x:-val(x,ph),bounds=(0,V-1),method='bounded',options={'xatol':1e-5}).x
                ph=minimize_scalar(lambda x:-val(pl,x),bounds=(0,V-1),method='bounded',options={'xatol':1e-5}).x
            v=val(pl,ph)
            if best is None or v>best[0]: best=(v,g,pl,ph)
        return best
    ps_m2=None
    t2P=twolevel(1) if full else (0,1,0,0)
    ps=[0]*K
    for k in order[:t2P[1]]: ps[k]=t2P[2]
    for k in order[t2P[1]:]: ps[k]=t2P[3]
    W2P,P2P=stats(ps) if full else (0,0)
    return dict(Wfb=Wfb,Pfb=Pfb,W0=W0,P0=P0,fW=fW,WfW=WfW,PfW=PfW,fP=fP,WfP=WfP,PfP=PfP,pm=pm,Wm=Wm,Pm=Pm,pfb=pfb,t2P=t2P,W2P=W2P,P2P=P2P,Lam=Lam)
if __name__=="__main__":
    import sys as _s
    out={}
    for kind in ('ded','bat'):
        r=analyze(kind); out[kind]={k:(v.tolist() if hasattr(v,'tolist') else v) for k,v in r.items()}
        print(kind,'FB W=%.2f (loss flat-welfare %.3f, none %.3f) peak/off tolls %.2f %.2f'%(r['Wfb'],1-r['WfW']/r['Wfb'],1-r['W0']/r['Wfb'],max(r['pfb']),min(r['pfb'])))
        print(' monopoly phase: W/Wfb=%.3f profit=%.2f ; flat-monopoly: W/Wfb=%.3f profit=%.2f (p=%.2f); two-level mono: W/Wfb=%.3f profit=%.2f (g=%d,%.2f,%.2f)'%(r['Wm']/r['Wfb'],r['Pm'],r['WfP']/r['Wfb'],r['PfP'],r['fP'],r['W2P']/r['Wfb'],r['P2P'],r['t2P'][1],r['t2P'][2],r['t2P'][3]))
        print(' FB-prices profit=%.2f; welfare-flat profit=%.2f; no-price profit=0; mono prices range %.2f-%.2f'%(r['Pfb'],r['PfW'],min(r['pm']),max(r['pm'])))
    json.dump(out,open('mon.json','w'))
