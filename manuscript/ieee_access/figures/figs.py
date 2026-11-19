import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7,'axes.linewidth':0.6,'svg.fonttype':'none'})
INK='#1f1f1f'; MUTED='#5f5f5f'; GRID='#d9d9d9'; BLUE='#2a78d6'; ORANGE='#eb6834'

# ---------- Figure 1: design
fig,ax=plt.subplots(figsize=(7.0,3.3)); ax.set_xlim(0,100); ax.set_ylim(0,56); ax.axis('off')
def box(x,y,w,h,title,lines,fill='#ffffff'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.2,rounding_size=1.0',lw=0.8,ec=INK,fc=fill))
    ax.text(x+w/2,y+h-1.6,title,ha='center',va='top',fontsize=6.8,fontweight='bold',color=INK,linespacing=1.2)
    nt=title.count('\n')+1
    ax.text(x+w/2,y+h-1.6-3.2*nt-0.6,'\n'.join(lines),ha='center',va='top',fontsize=5.7,color=INK,linespacing=1.4)
def arrow(x1,y1,x2,y2):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=7,lw=0.8,color=MUTED,shrinkA=0,shrinkB=0))
box(0.5,30,18,22,'Programs',['HumanEval tasks','120 programs:','60 correct (canonical)','60 single-token','mutants','9–59 lines'],fill='#f3f6fb')
box(0.5,3,18,22,'Pull requests',['60 PRs,','3 functions each:','30 clean,','30 with one','defective function','40–106 lines'],fill='#f3f6fb')
box(25,40,31,15,'Study 1: framing and order',['3 models, yes/no answers','1A: "correct?" vs. "contains a bug?"','1B: correctness and readability,','both orders'])
box(25,20,31,18,'Study 2: coherence probes',['4 models, A/B labels counterbalanced','2A: CI passed / failed / unknown','2B: approval asked directly vs.','after a bug question','2C: specific vs. general bug'])
box(25,0.5,31,17.5,'Study 3: free-text review',['5 configurations (incl. reasoning)','review of up to 250 words','+ final decision line','conditions: direct, bugs first,','CI passed / failed / running'])
box(62.5,8,18,40,'Measures',['Signal detection','(d′, c)','','Law of total','probability:','unknown vs.','[failed, passed]','','Interference:','direct − after','bug question','','Order effects,','QQ statistic'],fill='#fbfbfa')
box(85.5,16,14,24,'Elicitation\nsensitivity',['Variance shares:','program,','model,','elicitation,','model ×','elicitation'],fill='#fbfbfa')
arrow(18.9,44,24.6,47.5); arrow(18.9,38,24.6,29); arrow(18.9,14,24.6,9.5)
arrow(56.4,47.5,62.1,42); arrow(56.4,29,62.1,28); arrow(56.4,9.5,62.1,14)
arrow(80.9,28,85.1,28)
fig.savefig('fig1.png',dpi=300,bbox_inches='tight',pad_inches=0.02); plt.close(fig)

# ---------- Figure 2: interference + variance shares
import numpy as np
fig,(a,b)=plt.subplots(1,2,figsize=(7.0,2.6),gridspec_kw={'width_ratios':[1.25,1],'wspace':0.32})
models=['DeepSeek','DeepSeek\n(reasoning)','Haiku','Llama','Qwen']
s2={'DeepSeek':(0.017,-0.025,0.059),'Haiku':(0.073,0.035,0.112),'Llama':(0.362,0.306,0.421),'Qwen':(0.171,0.131,0.210)}
s3={'DeepSeek':(0.033,0.008,0.067),'DeepSeek\n(reasoning)':(0.075,0.026,0.133),'Haiku':(0.0,None,None),'Llama':(-0.008,-0.042,0.025),'Qwen':(0.150,0.092,0.217)}
x=np.arange(len(models)); off=0.17
for dct,dx,col,lab,mk in [(s2,-off,BLUE,'Study 2 (short programs)','o'),(s3,off,ORANGE,'Study 3 (pull requests)','s')]:
    for i,m in enumerate(models):
        if m not in dct: continue
        v,lo,hi=dct[m]; v*=100
        if lo is None:
            a.plot(x[i]+dx,v,mk,ms=4.5,mfc='white',mec=col,mew=1.2,zorder=3)
            a.annotate('no approvals',(x[i]+dx,v),xytext=(x[i]+dx+0.05,v-5.2),ha='center',fontsize=5.6,color=MUTED)
        else:
            a.errorbar(x[i]+dx,v,yerr=[[v-lo*100],[hi*100-v]],fmt=mk,ms=4.5,color=col,mec='white',mew=0.6,elinewidth=1.2,capsize=2,capthick=1,zorder=3)
    a.plot([],[],mk,color=col,ms=4.5,label=lab)
a.axhline(0,color=MUTED,lw=0.7)
a.set_xticks(x); a.set_xticklabels(models,fontsize=6.3)
a.set_ylabel('Interference (percentage points)\napproval direct − approval after bug question',fontsize=6.5)
a.set_ylim(-8,46); a.grid(axis='y',color=GRID,lw=0.5); a.set_axisbelow(True)
for s in ('top','right'): a.spines[s].set_visible(False)
a.tick_params(length=2,width=0.6,colors=INK)
a.text(1,-0.5,'—',ha='center',va='center',color=MUTED) # placeholder no-op
a.texts[-1].remove()
a.legend(frameon=False,fontsize=6.2,loc='upper left')
a.set_title('(a) Interference with 95% confidence intervals',fontsize=7,loc='left',color=INK)
comps=['Program /\npull request','Model','Elicitation','Model ×\nelicitation','Residual']
v2=[35.6,1.6,8.5,6.3,48.1]; v3=[24.4,4.6,1.7,2.4,67.0]
y=np.arange(len(comps)); h=0.36
b.barh(y-h/2-0.02,v2,h,color=BLUE,label='Study 2 (short programs)')
b.barh(y+h/2+0.02,v3,h,color=ORANGE,label='Study 3 (pull requests)')
for i in range(len(comps)):
    b.text(v2[i]+1,y[i]-h/2-0.02,f'{v2[i]:.1f}',va='center',fontsize=5.8,color=INK)
    b.text(v3[i]+1,y[i]+h/2+0.02,f'{v3[i]:.1f}',va='center',fontsize=5.8,color=INK)
b.set_yticks(y); b.set_yticklabels(comps,fontsize=6.3); b.invert_yaxis()
b.set_xlim(0,78); b.set_xlabel('Share of total sum of squares (%)',fontsize=6.5)
b.grid(axis='x',color=GRID,lw=0.5); b.set_axisbelow(True)
for s in ('top','right'): b.spines[s].set_visible(False)
b.tick_params(length=2,width=0.6,colors=INK)
b.legend(frameon=False,fontsize=6.2,loc='center right',bbox_to_anchor=(1.0,0.52))
b.set_title('(b) Sources of variance in approval rates',fontsize=7,loc='left',color=INK)
fig.savefig('fig2.png',dpi=300,bbox_inches='tight',pad_inches=0.02); plt.close(fig)
print('done')
