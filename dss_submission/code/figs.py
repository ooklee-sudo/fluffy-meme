import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import norm
plt.rcParams.update({'font.family':'serif','font.serif':['Liberation Serif'],'font.size':9,'axes.linewidth':0.7,'pdf.fonttype':42,'mathtext.fontset':'stix'})
C=['#1f77b4','#ff7f0e','#2ca02c']
def save(fig,name):
    fig.savefig(f'figs/{name}.pdf',bbox_inches='tight'); fig.savefig(f'figs/{name}.png',dpi=600,bbox_inches='tight'); plt.close(fig)
# ---------- Figure 1
K,B,eta,v=0.3,1.0,0.5,1.0
def D(q,phi,al):
    qh=v*K/(phi*(1-eta*phi)*B); return q*(1-eta*phi)*(1-(1-al)*np.minimum(1,q/qh))
q=np.linspace(1,0,801)
fig,ax=plt.subplots(figsize=(5.2,3.2))
ax.plot(q,D(q,1,0),color=C[0],label=r'No appearance wedge ($\varphi$ = 1)')
ax.plot(q,D(q,.6,0),color=C[1],label=r'Appearance wedge ($\varphi$ = 0.6)')
ax.plot(q,D(q,.6,.6),color=C[2],label=r'$\varphi$ = 0.6 with default acceptance ($\alpha$ = 0.6)')
ax.set_xlim(1.0,0.0); ax.set_ylim(-0.01,0.44); ax.set_xlabel('$q$: probability that a generated artifact is expedient (lower = more reliable model)'); ax.set_ylabel('Debt per task')
ax.legend(frameon=False,loc='upper right',fontsize=8); save(fig,'Figure_1')
# ---------- Figure 2
n,qq,p,al,r0,g,mu,Rm,s=1,0.5,0.9,0.0,0.3,3,0.5,1.0,0.25
A=n*qq*(1-(1-al)*p); Cc=n*qq*(1-al)*p
def I(H,b): return A+Cc*norm.cdf(np.log(r0*(1+g*H)/b/Rm)/s)
Hg=np.linspace(0,(A+Cc)/mu*1.0001,40001)
def roots(b):
    ph=I(Hg,b)-mu*Hg; idx=np.where(np.sign(ph[:-1])*np.sign(ph[1:])<0)[0]
    out=[]
    for i in idx:
        h0=Hg[i]-ph[i]*(Hg[i+1]-Hg[i])/(ph[i+1]-ph[i]); out.append((h0,ph[i]>0))
    return out
bs=np.linspace(0.3,1.0,701)
stable=[];unst=[]
for b in bs:
    for h0,st in roots(b): (stable if st else unst).append((b,h0))
fig,ax=plt.subplots(figsize=(5.2,3.4))
ax.plot(*zip(*stable),'.',ms=3,color='#1f4e79',label='Stable steady state'); ax.plot(*zip(*unst),'.',ms=3,color='#c00000',label='Unstable steady state')
# hysteresis paths
def follow(order,H0):
    H=H0; path=[]
    for b in order:
        for _ in range(4000): H=(1-mu)*H+I(H,b)
        path.append((b,H))
    return path
down=follow(bs[::-1],0.1); up=follow(bs,1.0)
ax.plot(*zip(*[(b,h) for b,h in down]),color='gray',lw=0.8,label='Path as $\\beta$ falls (starting clean)')
ax.plot(*zip(*[(b,h) for b,h in up]),'k--',lw=0.8,label='Path as $\\beta$ rises (starting trapped)')
ax.set_xlabel('$\\beta$ (present bias: lower = stronger)'); ax.set_ylabel('Steady-state debt stock $H^*$'); ax.set_xlim(0.26,1.04); ax.set_ylim(0.05,1.05)
ax.legend(frameon=False,loc='lower left',fontsize=7.5); save(fig,'Figure_2')
bz=[b for b in bs if len(roots(b))==3]; print('bistable',min(bz),max(bz))
# ---------- Figure 3
q3,Rb,r3,K3,a0,c,eps=0.5,2.0,0.4,0.6,0.8,0.15,0.005; eta3=.5;dl=1;v3=1
def fr(beta):
    t=(beta-0.3)/0.7; ph=0.6+0.4*t; lam=1.2-0.2*t
    Dp=ph*q3*(1-eta3*ph)*(beta*dl*Rb-lam*v3*r3); De=q3*(1-eta3*ph)*(dl*Rb-v3*r3)
    fD=a0*Dp**2/(2*v3**2*c*K3); fO=a0*Dp*(2*De-Dp)/(2*v3**2*c*K3)
    fD,fO=min(fD,1),min(fO,1); fI=fD+min(fO-fD,np.sqrt(2*eps/(v3*c)))
    return fD,fO,fI
bb=np.linspace(0.3,1.0,501); F=np.array([fr(b) for b in bb])
fig,ax=plt.subplots(figsize=(5.2,3.2))
ax.plot(bb,F[:,1],color=C[0],label='Organization-optimal friction ($f_O$)')
ax.plot(bb,F[:,2],'--',color=C[1],label='Implementable under shadow AI ($\\varepsilon$ = 0.005)')
ax.plot(bb,F[:,0],color=C[2],label='Developer-preferred friction ($f_D$)')
ax.set_xlabel('Wedge strength ($\\beta$; $\\varphi$ and $\\lambda$ move with $\\beta$, from strong at left to none at right)'); ax.set_ylabel('Interface friction $f$'); ax.set_ylim(-0.01,0.82)
ax.legend(frameon=False,loc='lower right',fontsize=8); save(fig,'Figure_3'); print('fig3 ends',F[0],F[-1])
# ---------- Figure 4
q4,kap,kmin,K4,B4,eta4,ph4=0.5,0.1,0.05,0.6,1.0,0.5,0.6
def s(qh):
    Dp=qh*(1-eta4*ph4)*B4; return float(np.clip((Dp-kmin)/(K4-kmin),0,1))
def sim(theta,mandate=0,T=60,q0=0.05):
    qh=q0; out=[]
    for t in range(T):
        out.append(qh); st=1.0 if t<mandate else s(qh)
        qh=qh+kap*(st+theta*(1-st))*(q4-qh)
    return out
fig,ax=plt.subplots(figsize=(5.2,3.2)); t=np.arange(60)
ax.plot(t,sim(0),color=C[0],label='No mandate, no attributed rework ($\\theta$ = 0)')
ax.plot(t,sim(0.02),color=C[1],label='Attributed rework ($\\theta$ = 0.02)')
ax.plot(t,sim(0,mandate=1),color=C[2],label='Temporary mandate (1 period)')
ax.axhline(q4,color='gray',ls=':',lw=0.8); ax.text(59,q4+0.008,'true defect rate',ha='right',fontsize=8)
qc=kmin/((1-eta4*ph4)*B4); ax.axhline(qc,color='gray',ls='--',lw=0.8); ax.text(59,qc+0.008,'self-confirming threshold',ha='right',fontsize=8)
ax.set_xlabel('Period'); ax.set_ylabel('Perceived defect rate $\\hat{q}$'); ax.set_ylim(0.03,0.53)
ax.legend(frameon=False,loc='center right',fontsize=8,bbox_to_anchor=(1,0.5)); save(fig,'Figure_4')
print('fig4 ends',sim(0.02)[-1],sim(0,1)[-1],sim(0,1)[1],qc)
