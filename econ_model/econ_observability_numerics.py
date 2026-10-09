import numpy as np, json
from scipy.optimize import minimize_scalar
P=dict(v=2.0,c=1.0,w=10.0,r=0.71,N=100.0,kappa=0.02,phi=0.005,h=1.0)
v,c,w,r,N,kap,phi,h=[P[k] for k in ['v','c','w','r','N','kappa','phi','h']]
D=2*v*r+c*w; A=w*v/D; G=A*(c*w+v*r)/D
g=lambda x:(x-N*phi)/(N*kap+r*x)
x_of=lambda lam:h*A*r*(1+lam*c*w/D)
alpha=lambda lam:max(0,g(x_of(lam)))
Phi=lambda a:h*G*(1-r*a)**2+N*(kap/2*a**2+phi*a)
aN,aS=alpha(0),alpha(1)
print('alphaN',aN,'alphaS',aS)
rows=[]
Vd1=Phi(aN)-Phi(aS)
for lam in [0,0.25,0.5,0.75,1]:
    al=alpha(lam); rows.append(dict(lam=lam,alpha=al,Ea=A*(1-r*al),Vd=Phi(aN)-Phi(al),share=(Phi(aN)-Phi(al))/Vd1,Phi=Phi(al)))
    print(rows[-1])
# mapping lambda from SNR
snr=[]
for ratio in [0.01,0.1,0.25,1,4,9,100]: # sigma_eta^2/sigma_xi^2
    lam=1/(1+ratio); snr.append(dict(ratio=ratio,lam=lam,alpha=alpha(lam),share=(Phi(aN)-Phi(alpha(lam)))/Vd1))
    print(snr[-1])
# optimal transparency
def Ltot(lam,sx): return Phi(alpha(lam))+h*lam*r**2*sx**2*G
opt=[]
for sx in [0.0,0.05,0.1,0.2,0.3,0.4,0.5,0.6]:
    res=minimize_scalar(lambda l:Ltot(l,sx),bounds=(0,1),method='bounded',options=dict(xatol=1e-10))
    lamst=res.x if Ltot(res.x,sx)<Ltot(0,sx)-1e-12 else 0.0
    # grid check
    grid=np.linspace(0,1,10001); gl=grid[np.argmin([Ltot(l,sx) for l in grid])]
    opt.append(dict(sigma_xi=sx,lam_star=gl,L_opt=Ltot(gl,sx),L_Nash=Ltot(0,sx),L_full=Ltot(1,sx),gain_vs_Nash=Ltot(0,sx)-Ltot(gl,sx),gain_full_vs_Nash=Ltot(0,sx)-Ltot(1,sx)))
    print(opt[-1])
# threshold sigma_bar^2
gp=lambda x:(N*kap+r*N*phi)/(N*kap+r*x)**2
sig2bar=h*A**2*(c*w/D)**2*(1-r*aN)*gp(h*A*r)/G
print('sigma_bar^2',sig2bar,'sigma_bar',np.sqrt(sig2bar))
# derivative check at lam=0 numerically
eps=1e-6
d0=(Ltot(eps,0)-Ltot(0,0))/eps; print('dPhi/dlam(0)',d0, 'predicted', -h*r*A*(c*w/D)*(1-r*aN)*gp(h*A*r)*h*A*r*(c*w/D))
print('L\'(1) predicted',h*r**2*G*0.3**2,' numeric',(Ltot(1,0.3)-Ltot(1-eps,0.3))/eps)
# ---------- Monte Carlo verification of the noisy game ----------
rng=np.random.default_rng(7)
sx,lam=0.3,0.5
se=np.sqrt(sx**2*(1-lam)/lam)
n=4_000_000
xi=rng.normal(0,sx,n); eta=rng.normal(0,se,n)
def mc_loss(al,ae):
    z=al+xi+eta; a=A*(1-r*(ae+lam*(z-ae))); ar=al+xi
    harm=a*(1-r*(ar+a/w))
    return h*harm.mean()+N*(kap/2*(ar**2).mean()+phi*al), a.mean(), harm.mean()
al_eq=alpha(lam)
# leader best response to attacker's fixed strategy (conjecture=al_eq): minimize MC loss over a grid (common random numbers)
grid=np.linspace(al_eq-0.1,al_eq+0.1,41)
ls=[mc_loss(a_,al_eq)[0] for a_ in grid]
best=grid[int(np.argmin(ls))]
print('MC: equilibrium alpha',al_eq,'MC best response',best)
Lmc,Ea,Eh=mc_loss(al_eq,al_eq)
Gform=G*(1-r*al_eq)**2+lam*r**2*sx**2*G
print('MC E[a]',Ea,'formula',A*(1-r*al_eq),'| MC E[harm]',Eh,'formula',Gform)
json.dump(dict(rows=rows,snr=snr,opt=opt,sig2bar=sig2bar),open('obs.json','w'),indent=1,default=float)
