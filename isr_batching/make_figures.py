"""Manuscript figures 1-4 (Section 6).  Inputs: hourly profile of the Azure 2024 code trace saved as profile.npy
(quasi_static.load_hourly_profile) and the Table 3 results in results/.  Paths below are those of the working session; edit as needed."""
import sys, json, numpy as np
sys.path.insert(0,'/home/user/fluffy-meme/isr_batching')
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import quasi_static as q
BLUE,ORANGE,INK,MUT,GRID='#2a78d6','#eb6834','#0b0b0b','#52514e','#e3e2de'
plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','Liberation Serif','DejaVu Serif'],'font.size':9,
  'axes.edgecolor':MUT,'axes.labelcolor':INK,'xtick.color':MUT,'ytick.color':MUT,'axes.spines.top':False,'axes.spines.right':False,
  'axes.grid':True,'grid.color':GRID,'grid.linewidth':0.6,'axes.axisbelow':True,'legend.frameon':False})
prof=np.load('/tmp/claude-0/az24/profile.npy'); hrs=np.arange(24)
ded=q.analyse(prof,77,0.0,20,1.4,Gs=(2,)); bat=q.analyse(prof,1024,0.00883,20,1.4,Gs=(2,))
OUT='/tmp/claude-0/figs/'
# ---- Figure 1: two stacked panels (no dual axis)
fig,(a1,a2)=plt.subplots(2,1,figsize=(6.5,5.2),sharex=True,gridspec_kw=dict(height_ratios=[1,1.5],hspace=0.12))
a1.bar(hrs,prof/prof.mean(),color='#c9c8c2',width=0.78); a1.set_ylabel('Arrival rate / daily mean'); a1.set_title('Demand profile (Azure 2024 code trace)',loc='left',fontsize=9,color=INK)
for lab,o,c,mk,ls in (('Dedicated servers',ded,BLUE,'o','-'),('Batching',bat,ORANGE,'s','-')):
    a2.plot(hrs,o['tolls'],color=c,marker=mk,ms=4.5,lw=1.8,ls=ls,label=f'First-best toll, {lab.lower()}',markeredgecolor='white',markeredgewidth=0.8)
    pr=o['levels'][2]['prices']; step=np.zeros(24)
    step=np.zeros(24)
    for grp,p in zip(o['levels'][2]['groups'],pr):
        for h in grp: step[h]=p
    a2.step(np.arange(25)-0.5,np.append(step,step[-1]),where='post',color=c,lw=1.4,ls='--',label=f'Best two-level schedule, {lab.lower()}')
a2.set_ylabel('Price or toll (units of waiting cost)'); a2.set_xlabel('Hour of day (UTC)'); a2.set_xticks(range(0,24,2)); a2.set_xlim(-0.6,23.6)
a2.legend(loc='upper left',fontsize=8)
fig.savefig(OUT+'fig1.png',dpi=300,bbox_inches='tight'); plt.close(fig)
# ---- Figure 2: waiting and slowdown components (stacked), batching, measured beta/alpha
fig,ax=plt.subplots(figsize=(6.5,3.2))
S=np.array(bat['toll_S']); W=np.array(bat['toll_W'])
ax.bar(hrs,S,color=BLUE,width=0.78,label='Slowdown component'); ax.bar(hrs,W,bottom=S+0.0,color=ORANGE,width=0.78,label='Waiting component',edgecolor='white',linewidth=0.8)
ax.set_ylim(0,12.5); ax.set_xlabel('Hour of day (UTC)'); ax.set_ylabel('First-best toll'); ax.set_xticks(range(0,24,2)); ax.legend(loc='upper left',fontsize=8)
fig.savefig(OUT+'fig2.png',dpi=300,bbox_inches='tight'); plt.close(fig)
# ---- Figure 3: recovery vs number of levels (two panels)
Gs=(2,3,4,5,6,8)
fig,axs=plt.subplots(1,2,figsize=(6.5,3.0),sharey=True)
for ax,(lab,M,b) in zip(axs,(('Dedicated servers',77,0.0),('Batching',1024,0.00883))):
    o=q.analyse(prof,M,b,20,1.4,Gs=Gs)
    ex=[o['levels'][g]['recovery_exact'] for g in Gs]; qd=[o['levels'][g]['recovery_quad'] for g in Gs]
    ax.plot(Gs,ex,color=BLUE,marker='o',ms=4.5,lw=1.8,label='Exact',markeredgecolor='white',markeredgewidth=0.8)
    ax.plot(Gs,qd,color=ORANGE,marker='s',ms=4.5,lw=1.8,ls='--',label='Quadratic prediction',markeredgecolor='white',markeredgewidth=0.8)
    ax.set_title(lab,loc='left',fontsize=9); ax.set_xlabel('Number of price levels G'); ax.set_ylim(0.55,1.02); ax.set_xticks(Gs)
axs[0].set_ylabel('Share of flat-price loss recovered'); axs[0].legend(loc='lower right',fontsize=8)
fig.savefig(OUT+'fig3.png',dpi=300,bbox_inches='tight'); plt.close(fig)
# ---- Figure 4: loss vs burst length
S='/tmp/claude-0/-home-user-fluffy-meme/e0d60690-13b5-5345-82e3-2fc56d1cf6a5/scratchpad/'
d=json.load(open(S+'t3_ded.json'))['results']; b1=json.load(open(S+'t3_bat.json'))['results']; b2=json.load(open(S+'t3_bat2.json'))['results']
bb=sorted(b1+b2,key=lambda r:r['burst']); d=sorted(d,key=lambda r:r['burst'])
fig,ax=plt.subplots(figsize=(6.5,3.4))
for lab,rs,c,mk in (('Dedicated servers',d,BLUE,'o'),('Batching',bb,ORANGE,'s')):
    ax.plot([r['burst'] for r in rs],[r['rel'] for r in rs],color=c,marker=mk,ms=5,lw=1.8,label=lab,markeredgecolor='white',markeredgewidth=0.8)
ax.set_xscale('log'); ax.set_xlabel('Mean burst length (service times)'); ax.set_ylabel('Loss of best flat price (% of welfare)'); ax.legend(loc='upper right',fontsize=8)
fig.savefig(OUT+'fig4.png',dpi=300,bbox_inches='tight'); plt.close(fig)
print('ok')
