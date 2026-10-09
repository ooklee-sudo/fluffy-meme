import numpy as np, json
from scipy.optimize import minimize
P=dict(v=2.0,c=1.0,w=10.0,r=0.71,N=100.0,kappa=0.10,phi=0.005,h=1.0)
v,c,w,r,N,kap,phi,h=[P[k] for k in ['v','c','w','r','N','kappa','phi','h']]
g=lambda x:max(0,(x-N*phi)/(N*kap+r*x))
def Kn(n): return n*w*v*(c*w+r*v)/(c*w+(n+1)*r*v)**2
def Abar(n): return n*w*v/(c*w+(n+1)*r*v)
def an(n,al): return w*v*(1-r*al)/(c*w+(n+1)*r*v)
def Xc(n,al): return n*w*v*(1-r*al)/(2*n*r*v+c*w)
def Qc(n,al):
    X=Xc(n,al); return X*(1-r*al-r*X/w)
nstar=1+c*w/(r*v); print('n*',nstar)
# numeric check: Nash via best-response iteration and potential maximization
def nash_num(n,al):
    a=np.full(n,0.5)
    for _ in range(5000):
        for i in range(n):
            X_i=a.sum()-a[i]
            a[i]=max(0,(v*(1-r*al)-(r*v/w)*X_i)/(2*r*v/w+c))
    return a
for n_ in [1,2,5,10]:
    a=nash_num(n_,0.3); print(n_, a[0], an(n_,0.3), a.sum(), n_*an(n_,0.3))
# unsaturated check: X <= (1-alpha) w
rows=[]
for n_ in [1,2,3,5,8,10,12]:
    aS=g(2*h*r*Kn(n_)); aN=g(h*r*Abar(n_))
    L=lambda al,nn=n_: h*Kn(nn)*(1-r*al)**2+N*(kap/2*al**2+phi*al)
    # numeric commitment optimum
    res=minimize(lambda z:L(z[0]),[0.3],bounds=[(0,1)]); aSn=res.x[0]
    XS=n_*an(n_,aS); XN=n_*an(n_,aN)
    # Nash loss: platform loss evaluated at aN with attackers' Nash response
    Lnash=L(aN); Lstack=L(aS)
    pu=(1-r*aS)*(c*w+r*v)/(c*w+(n_+1)*r*v)
    Ua=an(n_,aS)**2*(c/2+r*v/w)
    Ucar=(v*Xc(n_,aS)*(1-r*aS-r*Xc(n_,aS)/w)-c/(2*n_)*Xc(n_,aS)**2)/n_
    rows.append(dict(n=n_,K=Kn(n_),Abar=Abar(n_),aS=aS,aS_num=aSn,aN=aN,a_each=an(n_,aS),X=XS,Xcart=Xc(n_,aS),
        sat_ok=bool(XS<=(1-aS)*w and XN<=(1-aN)*w),beta_S=aS+XS/w,Q=Kn(n_)*(1-r*aS)**2,Qcart=Qc(n_,aS),
        L_stack=Lstack,L_nash=Lnash,commit_gain=Lnash-Lstack,payoff_nash=Ua,payoff_cartel_each=Ucar))
    print({k:(round(vv,4) if isinstance(vv,float) else vv) for k,vv in rows[-1].items()})
# harm at alpha=0 across n, independent vs coordinated
hump=[]
for n_ in [1,2,3,5,8,12,16]:
    hump.append(dict(n=n_,Qn=Kn(n_),Qc=Qc(n_,0),ratioX=(c*w+2*n_*r*v)/(c*w+(n_+1)*r*v),Xn=n_*an(n_,0),Xc=Xc(n_,0),pu=(c*w+r*v)/(c*w+(n_+1)*r*v)))
    print(hump[-1])
json.dump(dict(rows=rows,hump=hump,nstar=nstar),open('multi.json','w'),indent=1,default=float)
