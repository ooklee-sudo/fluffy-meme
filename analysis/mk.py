import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import sys
out=sys.argv[1]
plt.rcParams.update({"font.family":"Liberation Serif","font.size":9.5,"mathtext.fontset":"stix"})

# ---------- Fig B: tau(b)
fig,ax=plt.subplots(figsize=(6,3.6),dpi=300)
a,b_=3.64,0.0321
b=np.linspace(1,1100,400); t=a+b_*b
ax.fill_between(b[b>=64],0.94*t[b>=64],1.06*t[b>=64],color="0.88",lw=0,label="±6% of fit (deviation bound for $b\\geq 64$)")
ax.plot(b,t,color="black",lw=1.6,label=r"Fit: $\tau(b)=\alpha+\beta b$")
bs=[1,2,4,8,16,32,64,128,256,512,1024]
ax.plot(bs,[0]*len(bs),ls="none",marker="|",ms=6,color="black",label="Batch sizes measured ($b=1,2,4,\\ldots,1024$)")
ax.axvline(1024,color="0.4",ls="--",lw=1)
ax.text(1010,12,"batch cap $M=1{,}024$",rotation=90,ha="right",va="bottom",color="0.25")
ax.annotate(r"$\alpha=3.64$ ms",xy=(8,a),xytext=(150,3.2),arrowprops=dict(arrowstyle="->",lw=.8))
ax.text(640,11.5,r"slope $\beta=0.0321$ ms ($\beta/\alpha=0.0088$, $R^2=0.998$)",rotation=0,ha="center",va="center",fontsize=8.5)
ax.set_xlim(0,1100); ax.set_ylim(-1,42)
ax.set_xlabel("Batch size $b$ (concurrent requests)"); ax.set_ylabel("Decode step time $\\tau(b)$ (ms)")
for s in("top","right"): ax.spines[s].set_visible(False)
ax.grid(axis="y",color="0.92",lw=.8); ax.set_axisbelow(True)
ax.legend(frameon=False,loc="upper left",fontsize=8.5)
fig.tight_layout(); fig.savefig(out+"/figure_tau.png"); plt.close(fig)

# ---------- Fig A: model schematic
fig,ax=plt.subplots(figsize=(6.6,3.6),dpi=300)
ax.set_xlim(0,100); ax.set_ylim(0,48); ax.axis("off")
def box(x,y,w,h,txt="",fc="white",lw=1.2,fs=9.5,ls="-"):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0,rounding_size=1.2",fc=fc,ec="black",lw=lw,ls=ls))
    if txt: ax.text(x+w/2,y+h/2,txt,ha="center",va="center",fontsize=fs)
def arr(p,q,**k):
    ax.add_patch(FancyArrowPatch(p,q,arrowstyle="-|>",mutation_scale=9,lw=1.1,color=k.get("c","black"),connectionstyle=k.get("cs","arc3")))
# Panel 1: phases
ax.text(11,46.5,"Demand phase",ha="center",fontweight="bold")
cx=[4,12,20]; 
ph=[(5,38),(17,38),(11,29)]
for i,(x,y) in enumerate(ph):
    ax.add_patch(Circle((x,y),3.4,fc=["0.9","0.75","0.9"][i],ec="black",lw=1.1))
    ax.text(x,y,["$k{=}1$","$k$","$K$"][i],ha="center",va="center",fontsize=8.5)
arr((8.6,38.6),(13.4,38.6)); arr((13.4,37.4),(8.6,37.4))
arr((6.2,34.8),(9.5,31.9)); arr((12.8,31.9),(16,34.8))
ax.text(11,24.6,"Markov chain over phases\n(long-run prob. $\\pi_k$), observed\nby users and provider",ha="center",va="top",fontsize=8.3)
# demand curve
ax.text(11,16.2,"",ha="center")
x0,y0=4,2.5; 
ax.plot([x0,x0],[y0,y0+10],color="black",lw=.9); ax.plot([x0,x0+17],[y0,y0],color="black",lw=.9)
ax.plot([x0,x0+16],[y0+9.5,y0],color="black",lw=1.6); ax.plot([x0,x0+10],[y0+9.5,y0],color="0.55",lw=1.3,ls="--")
ax.text(x0-0.6,y0+9.6,"$V$",ha="right",va="center",fontsize=8.5); ax.text(x0+17.4,y0-.2,"$\\lambda$",ha="left",va="center",fontsize=8.5)
ax.text(x0+6.5,y0+9.0,"$P_k(\\lambda)=V(1-\\lambda/\\Lambda_k)$",ha="left",va="center",fontsize=8.3)
# Panel 2: users
box(30,22,17,13,"Users\n(infinitesimal)\nsee phase and\nprice, not queue",fs=8.5)
arr((22.5,29),(29.8,28.6))
ax.text(38.5,38.5,"posted price $p_k$",ha="center",va="center",fontsize=8.5)
arr((38.5,37.2),(38.5,35.2))
# Panel 3: queue + batch
ax.text(66,46.5,"Cluster (one engine)",ha="center",fontweight="bold")
box(52,22,13,13,"")
for i in range(5):
    ax.add_patch(plt.Rectangle((54+i*2.0,24.5),1.5,8,fc="0.8",ec="black",lw=.7))
ax.text(58.5,35.8,"FCFS queue\n($n>M$ wait)",ha="center",va="bottom",fontsize=8.3)
box(69,16,19,24,"",lw=1.4)
ax.text(78.5,40.6,"Batch ($\\leq M$ in service)",ha="center",va="bottom",fontsize=8.3)
for r in range(3):
    for c in range(4):
        ax.add_patch(plt.Rectangle((71+c*3.8,31.5+(-r)*3.9),2.9,3,fc="0.55",ec="black",lw=.6))
ax.text(78.5,18.6,"step time $\\tau(b)=\\alpha+\\beta b$\nspeed $\\rho(n)=\\tau(1)/\\tau(\\min(n,M))$",ha="center",va="center",fontsize=6.6)
arr((47.2,28.5),(51.8,28.5)); ax.text(49.5,30.2,"$\\lambda_k(p_k)$",ha="center",fontsize=8.3)
arr((65.2,28.5),(68.8,28.5))
arr((88.2,28.5),(96,28.5)); ax.text(92,30.5,"$\\mu(n)$",ha="center",fontsize=8.3)
ax.text(98.6,28.5,"done",ha="center",va="center",fontsize=8,rotation=90)
# equilibrium feedback
arr((78,15.6),(38.5,21.6),cs="arc3,rad=-0.3",c="0.35")
ax.text(58,9.6,"expected delay $d(\\lambda)$ enters the user's decision:\n$P_k(\\lambda)=p+d(\\lambda)$",ha="center",va="center",fontsize=8.3,color="0.2")
# toll bracket
ax.annotate("",xy=(52,17.5),xytext=(87,17.5),arrowprops=dict(arrowstyle="-",lw=0))
ax.text(66,2.6,"Toll $t=t_W+t_S$:  $t_W$ = extra waiting before the batch;  $t_S$ = slowdown of requests in the batch\n$t(\\lambda)=(\\mathrm{Var}\\,N-\\mathbb{E}N)/\\lambda$   (zero under dedicated servers, $t_S\\equiv 0$)",ha="center",va="center",fontsize=8,
        bbox=dict(boxstyle="round",fc="0.95",ec="0.5",lw=.7))
fig.tight_layout(pad=0.3); fig.savefig(out+"/figure_model.png"); plt.close(fig)
