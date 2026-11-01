import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, numpy as np, pandas as pd, os
from matplotlib import font_manager
fam=[f.name for f in font_manager.fontManager.ttflist]
plt.rcParams['font.family']='Arial' if 'Arial' in fam else ('Liberation Sans' if 'Liberation Sans' in fam else 'DejaVu Sans')
plt.rcParams.update({'font.size':8.5,'axes.linewidth':0.6,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':100})
BLUE,ORANGE,INK,MUTED,GRID='#2a78d6','#eb6834','#0b0b0b','#52514e','#e4e3df'
OUT='/home/user/fluffy-meme/submission_plos/figures'
def save(fig,name):
    fig.savefig(f'{OUT}/{name}.png',dpi=300,bbox_inches='tight',facecolor='white')
    fig.savefig(f'{OUT}/{name}.tif',dpi=300,bbox_inches='tight',facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
    plt.close(fig)

# ---------------- Fig 1: forest plots (Table 1 + pooled estimates from the manuscript)
rows=[("anthropics/anthropic-sdk-python",-0.016,0.079,-0.229,0.093),("Dao-AILab/flash-attention",-0.007,0.016,-0.294,0.063),
("EleutherAI/lm-evaluation-harness",0.002,0.019,0.117,0.160),("ggml-org/whisper.cpp",0.013,0.016,-0.105,0.069),
("huggingface/transformers",-0.016,0.033,-0.066,0.063),("huggingface/accelerate",-0.033,0.031,0.045,0.077),
("huggingface/diffusers",-0.001,0.014,-0.024,0.057),("huggingface/peft",0.004,0.017,0.115,0.073),
("huggingface/text-generation-inference",-0.049,0.036,-0.153,0.094),("huggingface/trl",-0.043,0.037,0.038,0.130),
("lm-sys/FastChat",0.003,0.046,-0.403,1.014),("microsoft/autogen",-0.040,0.037,-0.482,0.168),
("microsoft/semantic-kernel",0.003,0.150,-0.522,0.111),("NVIDIA/TensorRT-LLM",0.018,0.016,0.172,0.144),
("ollama/ollama",0.076,0.034,0.116,0.541),("openai/openai-python",-0.027,0.043,-0.343,0.049),
("run-llama/llama_index",-0.031,0.032,-0.564,0.098),("sgl-project/sglang",0.002,0.013,0.172,0.089),("vllm-project/vllm",-0.004,0.012,0.122,0.268)]
fig,axs=plt.subplots(1,2,figsize=(7.2,5.4),sharey=True)
pooled=[(-0.0005,-0.010,0.009,(-0.35,0.35)),(-0.125,-0.228,-0.022,(-1.0,1.0))]
titles=["RQ1: bug-report log-rate slope\n(per week since release)","RQ2: release-hazard logit slope\n(per week since release)"]
n=len(rows); ys=np.arange(n+1)[::-1]  # pooled at bottom (y=0)
for k,ax in enumerate(axs):
    est=[r[1+2*k] for r in rows]; se=[r[2+2*k] for r in rows]
    for y,e,s in zip(ys[:-1],est,se): ax.plot([e-1.96*s,e+1.96*s],[y,y],color=BLUE,lw=1.2,solid_capstyle='butt'); ax.plot(e,y,'o',ms=4.5,color=BLUE,mec='white',mew=0.8)
    pe,lo,hi,xl=pooled[k]
    ax.plot([lo,hi],[0,0],color=INK,lw=1.6); ax.plot(pe,0,'D',ms=7,color=INK,mec='white',mew=0.8)
    ax.axvline(0,color=MUTED,lw=0.8,ls=(0,(3,3)),zorder=0)
    ax.set_xlim(*xl); ax.set_ylim(-1,n+0.2); ax.set_title(titles[k],fontsize=9,loc='left')
    ax.grid(axis='x',color=GRID,lw=0.5); ax.set_axisbelow(True); ax.tick_params(length=2.5)
    ax.set_xlabel('Slope (95% CI); H1/H2 predict > 0',color=MUTED)
axs[0].set_yticks(list(ys[:-1])+[0]); axs[0].set_yticklabels([r[0] for r in rows]+['Pooled (random effects)'],fontsize=7.5)
axs[0].get_yticklabels()[-1].set_fontweight('bold')
fig.tight_layout(w_pad=1.2); save(fig,'Fig2')

# ---------------- Fig 2: precision of RC estimate vs panel length
T=[100,250,500,1000]; sd=[6.7,4.8,2.8,2.1]
fig,ax=plt.subplots(figsize=(4.6,3.2))
ax.axvspan(145,414,color=GRID,alpha=0.8,lw=0); ax.text(245,7.45,'Repositories studied\n(145–414 weeks)',ha='center',va='top',fontsize=7.5,color=MUTED)
ax.plot(T,sd,'-o',color=BLUE,lw=1.6,ms=5.5,mec='white',mew=0.8)
for t,s in zip(T,sd): ax.annotate(f'{s:.1f}',(t,s),textcoords='offset points',xytext=(0,7),ha='center',fontsize=8,color=INK)
ax.set_xscale('log'); ax.set_xticks(T); ax.set_xticklabels(T); ax.minorticks_off()
ax.set_ylim(0,8); ax.set_xlim(80,1250)
ax.set_xlabel('Panel length (weekly observations)',color=MUTED); ax.set_ylabel('SD of estimated refresh cost RC\n(true RC = 40)',color=MUTED)
ax.grid(axis='y',color=GRID,lw=0.5); ax.set_axisbelow(True); ax.tick_params(length=2.5)
fig.tight_layout(); save(fig,'Fig1')

# ---------------- Fig 3: template contamination of the raw drift series
d=pd.read_csv('/tmp/wc/fig3_data.csv',parse_dates=['wk'])
fig,ax=plt.subplots(figsize=(6.0,3.3))
ax.plot(d.wk,100*d.raw,color=ORANGE,lw=1.8,label='Raw (all conversations)'); ax.plot(d.wk,100*d.dedup,color=BLUE,lw=1.8,label='After template removal (at most 5 per week\nwith the same first 80 characters)')
ax.legend(loc='upper left',frameon=False,fontsize=8.5,handlelength=1.6)
ax.set_ylabel('Weekly conversations mentioning a\npost-cutoff product (%)',color=MUTED); ax.set_ylim(0,92)
ax.set_xlabel('Week (ISO week start), April 2023 – April 2024',color=MUTED)
ax.grid(axis='y',color=GRID,lw=0.5); ax.set_axisbelow(True); ax.tick_params(length=2.5)
import matplotlib.dates as md; ax.xaxis.set_major_formatter(md.DateFormatter('%b %Y')); ax.xaxis.set_major_locator(md.MonthLocator(interval=2))
fig.tight_layout(); save(fig,'Fig3')

# ---------------- Fig 4: snapshot contrast and placebo
items=[("GPT-4 contrasts (cutoff advantage)",None,None,None),
("gpt-4-1106 minus gpt-4-0314\n(19 months)",(1.31,0.72,1.90),(1.24,0.14,2.34),'c'),
("gpt-4-0125 minus gpt-4-0314\n(27 months)",(0.65,-0.11,1.41),(0.54,-1.03,2.11),'c'),
("Placebo: same cutoff (GPT-3.5)",None,None,None),
("gpt-3.5-0613 minus -0301",(-0.36,-0.77,0.05),(-0.77,-1.42,-0.11),'p'),
("gpt-3.5-0125 minus -0301",(-0.20,-0.75,0.35),(-1.00,-2.06,0.06),'p')]
fig,ax=plt.subplots(figsize=(6.4,3.9))
y=len(items); ticks=[];labels=[]
for it in items:
    y-=1
    if it[1] is None: ax.text(-2.5,y,it[0],fontweight='bold',fontsize=8.5,va='center',ha='left',color=INK); continue
    for off,(e,lo,hi),col,lab in [(0.17,it[1],BLUE,'v1 detector'),(-0.17,it[2],ORANGE,'v2 detector')]:
        ax.plot([lo,hi],[y+off]*2,color=col,lw=1.5,solid_capstyle='butt'); ax.plot(e,y+off,'o',ms=5.5,color=col,mec='white',mew=0.8)
    ticks.append(y); labels.append(it[0])
ax.axvline(0,color=MUTED,lw=0.8,ls=(0,(3,3)),zorder=0)
ax.set_yticks(ticks); ax.set_yticklabels(labels,fontsize=8); ax.set_xlim(-2.6,2.6); ax.set_ylim(-0.6,len(items)-0.3)
ax.set_xlabel('Difference in correction probability (percentage points; 95% CI)\nH3 predicts negative values for the GPT-4 contrasts',color=MUTED)
ax.grid(axis='x',color=GRID,lw=0.5); ax.set_axisbelow(True); ax.tick_params(length=2.5)
ax.plot([],[],'o',color=BLUE,label='v1 detector'); ax.plot([],[],'o',color=ORANGE,label='v2 detector'); ax.legend(frameon=False,loc='lower right',fontsize=8)
fig.tight_layout(); save(fig,'Fig4')
print(sorted(os.listdir(OUT)))
