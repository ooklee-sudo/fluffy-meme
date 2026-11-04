import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
plt.rcParams.update({"font.family":"serif","font.serif":["Liberation Serif"],"font.size":9,"hatch.linewidth":0.5})
fig=plt.figure(figsize=(7.2,3.9),dpi=300)
ax=fig.add_axes([0,0.3,1,0.7]);bx=fig.add_axes([0,0,1,0.27])
ACC="#1f4e79";G1="#e3e3e3";G2="#9a9a9a"
ax.set_xlim(-6.5,37.5);ax.set_ylim(-1.0,5.0);ax.axis("off")
yA,yB,h=3.1,1.35,0.72
ax.text(-6.3,yA,"Vendor A",va="center",ha="left",weight="bold")
ax.text(-6.3,yB,"Vendor B\n(alternative)",va="center",ha="left",weight="bold",linespacing=1.0)
def ver(x0,x1,y,lab,notice=None):
    ax.add_patch(Rectangle((x0,y-h/2),x1-x0,h,fc=G1,ec="black",lw=0.6))
    if notice: ax.add_patch(Rectangle((x1-notice,y-h/2),notice,h,fc="white",ec="black",lw=0.6,hatch="////"))
    ax.text(x0+0.5,y,lab,va="center",ha="left",fontsize=8.5)
ver(0,14,yA,"A1",6);ver(14,30,yA,"A2",6);ver(30,36,yA,"A3")
ver(0,24,yB,"B1",6);ver(24,36,yB,"B2")
o=0.52
ax.plot([0,14],[yA+o]*2,color=ACC,lw=2.4,solid_capstyle="butt")
ax.annotate("",xy=(14,yB+o),xytext=(14,yA-h/2),arrowprops=dict(arrowstyle="-|>",color=ACC,lw=1.5,shrinkA=0,shrinkB=0))
ax.plot([14,22],[yB+o]*2,color=ACC,lw=2.4,solid_capstyle="butt")
ax.annotate("",xy=(22,yA-h/2),xytext=(22,yB+o),arrowprops=dict(arrowstyle="-|>",color=ACC,lw=1.5,shrinkA=0,shrinkB=0))
ax.plot([22,36],[yA+o]*2,color=ACC,lw=2.4,solid_capstyle="butt")
def mark(x,y,n):
    ax.scatter([x],[y],s=210,color=ACC,zorder=5,edgecolors="white",linewidths=0.8)
    ax.text(x,y,n,color="white",ha="center",va="center",weight="bold",fontsize=8.5,zorder=6)
for x,n in [(0,"1"),(14,"2"),(22,"3"),(30,"2")]:
    ax.plot([x,x],[yA+o,4.45],color=ACC,lw=0.6,ls=":");mark(x,4.45,n)
ax.annotate("",xy=(37.2,0.25),xytext=(0,0.25),arrowprops=dict(arrowstyle="-|>",lw=0.7))
for m in range(0,37,6):
    ax.plot([m,m],[0.25,0.1],color="black",lw=0.6);ax.text(m,-0.25,str(m),ha="center",fontsize=8)
ax.text(18,-0.85,"Months after adoption",ha="center",fontsize=8.5)
ax.add_patch(Rectangle((-6.2,-0.2),1.3,0.45,fc="white",ec="black",lw=0.6,hatch="////"));ax.text(-4.6,0.03,"Notice period",va="center",fontsize=8)
ax.plot([-6.2,-4.9],[-0.65,-0.65],color=ACC,lw=2.4);ax.text(-4.6,-0.65,"Model in use",va="center",fontsize=8)
bx.set_xlim(0,3);bx.set_ylim(0,1);bx.axis("off")
boxes=[("1","Defer the flexibility investment","Pay premium P up front for an\nabstraction layer and evaluation\nharness. It pays on effort alone\nif P < (1 − φ)KΛ."),
       ("2","Choose at retirement","At each retirement, take the\ncheaper of the successor and an\nalternative. The value grows as\nvendors’ prices decorrelate."),
       ("3","Switch early","Between retirements, switch only\nwhen savings exceed θ times the\nswitching cost (θ ≈ 2.1 in the\nbase case).")]
for i,(n,t,d) in enumerate(boxes):
    x0=0.02+i
    bx.add_patch(FancyBboxPatch((x0,0.04),0.94,0.9,boxstyle="round,pad=0,rounding_size=0.03",fc="#f4f4f4",ec=G2,lw=0.6))
    bx.scatter([x0+0.08],[0.8],s=170,color=ACC,zorder=5);bx.text(x0+0.08,0.8,n,color="white",ha="center",va="center",weight="bold",fontsize=8,zorder=6)
    bx.text(x0+0.15,0.8,t,va="center",ha="left",weight="bold",fontsize=8.6)
    bx.text(x0+0.05,0.62,d,va="top",ha="left",fontsize=8.2,linespacing=1.25)
plt.savefig("fig1_framework.png",bbox_inches="tight",pad_inches=0.04)
