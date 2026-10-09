import numpy as np, json
from scipy.optimize import minimize
P=dict(v=2.0,c=1.0,w=10.0,r=0.71,N=100.0,kappa=0.02,phi=0.005,h=1.0,H=1.0,nu=100.0)
def D(p): return 2*p['v']*p['r']+p['c']*p['w']
def A(p): return p['w']*p['v']/D(p)
def G(p): return A(p)*(p['c']*p['w']+p['v']*p['r'])/D(p)
def att(p,al,t=0.0):
    return max(0.0,p['w']*(p['v']*(1-p['r']*al)-t)/D(p))
def Q(p,al,t=0.0):
    a=att(p,al,t); beta=min(1,al+a/p['w']); return a*(1-p['r']*beta)
def screen_cost(p,al): return p['N']*(p['kappa']/2*al**2+p['phi']*al)
def dwl(p,t): return p['N']*t**2/(2*p['nu'])
def loss(p,al,t=0.0,harm=None):
    harm=p['H'] if harm is None else harm
    return harm*Q(p,al,t)+screen_cost(p,al)+dwl(p,t)
def stack(p,harm=None):           # screening only
    h=p['H'] if harm is None else harm
    x=2*h*G(p)*p['r']; al=max(0,(x-p['N']*p['phi'])/(p['kappa']*p['N']+x*p['r'])); return al
def nash(p,harm=None):
    h=p['H'] if harm is None else harm
    x=h*A(p)*p['r']; return max(0,(x-p['N']*p['phi'])/(p['kappa']*p['N']+x*p['r']))
def randscr(p,harm=None):
    h=p['H'] if harm is None else harm
    # random screening share s: beta=s, a=v(1-rs)/c, harm h*a*(1-rs)
    def L(s):
        a=p['v']*(1-p['r']*s)/p['c']; return h*a*(1-p['r']*s)+screen_cost(p,s)
    res=minimize(lambda z:L(z[0]),[0.3],bounds=[(0,1)]); return res.x[0],res.fun
out={}
# 1 commitment
aS=stack(P); aN=nash(P)
chk=minimize(lambda z:loss(P,z[0]),[0.3],bounds=[(0,1)]).x[0]
print('stack closed',aS,'numeric',chk,'nash',aN)
def row(al):
    a=att(P,al); beta=al+a/P['w']
    return dict(alpha=al,a=a,beta=beta,Q=Q(P,al),platform_loss=loss(P,al),attacker=P['v']*a*(1-P['r']*beta)-P['c']*a*a/2)
out['commit']={'nash':row(aN),'stack':row(aS)}
print(out['commit'])
# also check Nash is actually mutual BR numerically
bestal=minimize(lambda z:P['h']*att(P,aN)*(1-P['r']*(z[0]+att(P,aN)/P['w']))+screen_cost(P,z[0]),[0.3],bounds=[(0,1)]).x[0]
print('nash platform BR given a(aN)',bestal)
# 2 information
rows=[]
for w in [5,10,20,40,80,160,1e4]:
    p=dict(P,w=w); al=stack(p); lS=loss(p,al); sR,lR=randscr(p)
    rows.append(dict(w=w,alpha=al,a=att(p,al),Q=Q(p,al),LS=lS,LR=lR,alphaR=sR,G=G(p)))
    print(rows[-1])
out['info']=rows
# 3 two instruments
def opt2(p,harm=None,tmax=None):
    f=lambda z:loss(p,z[0],z[1],harm=harm)
    best=None
    for s in [(0.2,0.1),(0.5,0.5),(0.8,0.2),(0.1,0.8)]:
        r=minimize(f,s,bounds=[(0,1),(0,p['v'])],method='L-BFGS-B')
        if best is None or r.fun<best.fun: best=r
    return best.x,best.fun
x2,l2=opt2(P); lS=loss(P,aS)
# price only
rp=minimize(lambda z:loss(P,0,z[0]),[0.3],bounds=[(0,P['v'])]); 
out['two']={'alpha':x2[0],'t':x2[1],'a':att(P,x2[0],x2[1]),'L2':l2,'L_screen_only':lS,'L_price_only':rp.fun,'t_price_only':rp.x[0],'L_none':loss(P,0)}
print(out['two'])
# closed form check of two-instrument FOC
import sympy as sp
# comparative statics in kappa and nu
cs=[]
for k in [0.005,0.01,0.02,0.04,0.08]:
    p=dict(P,kappa=k); x,l=opt2(p); cs.append(dict(kappa=k,alpha=x[0],t=x[1],L=l))
out['cs_kappa']=cs; print(cs)
cs=[]
for nu in [25,50,100,200,400]:
    p=dict(P,nu=nu); x,l=opt2(p); cs.append(dict(nu=nu,alpha=x[0],t=x[1],L=l))
out['cs_nu']=cs; print(cs)
# 4 liability wedge, two instruments (platform private harm theta*H)
wd=[]
for th in [0.25,0.5,0.75,1.0]:
    x,_=opt2(P,harm=th*P['H']); wd.append(dict(theta=th,alpha=x[0],t=x[1],a=att(P,x[0],x[1]),SocialLoss=loss(P,x[0],x[1])))
out['wedge']=wd; print(wd)
wd1=[]
for th in [0.25,0.5,0.75,1.0]:
    al=stack(P,harm=th*P['H']); wd1.append(dict(theta=th,alpha=al,a=att(P,al),SocialLoss=loss(P,al)))
out['wedge_screen']=wd1; print(wd1)
# 5 operating points
ops=[('Qwen3Guard strict',0.71,0.10),('Qwen3Guard lenient',0.885,0.355),('DeBERTa injection',0.755,0.13)]
tab=[]
for m in [0.02,0.05,0.2]:
    for nm,r,f in ops:
        p=dict(P,r=r,phi=m*f); al=stack(p); tab.append(dict(m=m,op=nm,r=r,f=f,alpha=al,a=att(p,al),Q=Q(p,al),L=loss(p,al)))
        print(tab[-1])
out['ops']=tab
json.dump(out,open('num.json','w'),indent=1,default=float)

# breakeven misflag cost m between operating points, and interior checks
from scipy.optimize import brentq
def Lop(r,f,m):
    p=dict(P,r=r,phi=m*f); al=stack(p); return loss(p,al)
print('strict vs lenient', brentq(lambda m:Lop(.71,.10,m)-Lop(.885,.355,m),1e-6,0.5) if Lop(.71,.10,1e-6)>Lop(.885,.355,1e-6) else 'strict always better')
print('L at m->0', Lop(.71,.10,1e-6),Lop(.885,.355,1e-6),Lop(.755,.13,1e-6))
print('DeBERTa vs strict', (lambda g: g)(Lop(.755,.13,.05)-Lop(.71,.10,.05)))
try: print('breakeven DeBERTa vs strict', brentq(lambda m:Lop(.755,.13,m)-Lop(.71,.10,m),1e-6,0.5))
except Exception as e: print('no crossing',e)
# interior checks: beta<=1 at all reported equilibria, alpha<=abar
abar=1-P['v']/D(P); print('abar',abar)
for al in [aN,aS,0.370,0.432]:
    a=att(P,al); print(al, a, al+a/P['w'])
