import numpy as np, json
from scipy import stats
mu0=0.5; n=60; abar=20.0; H=5; WPD=1440
agrid=np.round(np.arange(0.05,abar+1e-9,0.05),2)
def p(K,b): return stats.poisson.sf(K,mu0+b)
def U(K,a,e=0.0):
    pp=p(K,a*(1-e)); S=np.where(pp>1e-12,(1-(1-pp)**n)/pp,n)
    return a*S
# MC check
rng=np.random.default_rng(1)
def mc(K,a,reps=20000):
    tot=0
    for _ in range(reps//200):
        x=rng.poisson(mu0+a,(200,n)); trig=x>K
        first=np.where(trig.any(1),trig.argmax(1),n-1)
        tot+=((first+1)*a).sum()
    return tot/reps
print('check K=4 a=1', U(4,np.array([1.0]))[0], mc(4,1.0))
print('check K=3 a=2', U(3,np.array([2.0]))[0], mc(3,2.0))
out=[]
for K in range(1,10):
    u=U(K,agrid); i=u.argmax()
    out.append((K,float(agrid[i]),float(u[i]),float(U(K,np.array([8.0]))[0]),float(U(K,np.array([abar]))[0])))
    print(out[-1])
rows=[]
for d in [0.1,1,10]:
    cf=lambda K: WPD*stats.poisson.sf(K,mu0)*H
    cost_S=[cf(K)+d*U(K,agrid).max() for K in range(0,12)]
    KS=int(np.argmin(cost_S))
    # naive: assumes attacker plays a=8
    cost_N=[cf(K)+d*U(K,np.array([8.0]))[0] for K in range(0,12)]
    KN=int(np.argmin(cost_N))
    aS=float(agrid[U(KS,agrid).argmax()]); aN=float(agrid[U(KN,agrid).argmax()])
    rows.append(dict(d=d,KN=KN,cost_naive_planned=float(min(cost_N)),cost_naive_real=float(cost_S[KN]),aN=aN,
                     KS=KS,cost_S=float(cost_S[KS]),aS=aS,UN=float(U(KN,agrid).max()),US=float(U(KS,agrid).max())))
    print(rows[-1])
json.dump({'out':out,'rows':rows},open('game.json','w'))
