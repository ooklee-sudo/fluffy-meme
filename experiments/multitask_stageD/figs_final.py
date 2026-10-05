import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from stats_for_paper import counts, MODELS
A=json.load(open("analysis.json"))["summary"]
PR={m:json.load(open(f"probe_{m}.json")) for m in MODELS}
MN={"qwen3b":"Qwen2.5-3B-Instruct","llama3b":"Llama-3.2-3B-Instruct"}
TN={"alpha":"Alphabet","months":"Months","planets":"Planets","numbers":"Number words"}
COL=["#2a78d6","#eb6834","#1baf7a","#4a3aa7"]; MK=["o","s","^","D"]; LS=["-","--",":","-."]
plt.rcParams.update({"font.family":"serif","font.size":8,"axes.spines.top":False,"axes.spines.right":False,"axes.edgecolor":"#52514e","axes.labelcolor":"#0b0b0b","xtick.color":"#52514e","ytick.color":"#52514e"})
# ---- Figure 1: multi-task accuracy curves
fig,axs=plt.subplots(4,2,figsize=(6.2,8.2),sharex=True,sharey=True)
for j,m in enumerate(MODELS):
    for i,t in enumerate(TN):
        ax=axs[i][j]; pr=PR[m][t]
        for k,(nm,mm) in enumerate((("weak",pr["weak"]),("sticky",pr["sticky"]),("strong",pr["strong"]))):
            if not mm: continue
            rows=sorted([x for x in A if x["model"]==m and x["task"]==t and x["m"]==mm and not x["press"] and not x["contam"]],key=lambda x:x["T"])
            ax.errorbar([r["T"] for r in rows],[r["acc"] for r in rows],yerr=[r["acc_se"] for r in rows],color=COL[k],marker=MK[k],ms=3.5,lw=1.2,ls=LS[k],capsize=1.5,label=f"{nm} (m = {mm})")
        ax.set_ylim(-0.03,1.05); ax.set_xlim(0,3.3)
        if i==0: ax.set_title(MN[m],fontsize=9)
        if j==0: ax.set_ylabel(f"{TN[t]}\nlocal accuracy")
        if i==3: ax.set_xlabel("Nominal temperature T")
        ax.legend(fontsize=6,frameon=False,loc="upper right",handlelength=2.2)
fig.tight_layout(); fig.savefig("fig1_multitask.png",dpi=300); plt.close(fig)
# ---- Figure 2: alphabet, fine temperature grid, three models
def load(fn): return json.load(open(fn))
panels=[("Qwen2.5-3B-Instruct","stageC_qwen3b.json",(2,3,4,6)),("Qwen2.5-7B-Instruct (Q8_0)","stageC_qwen7b.json",(1,2,3,4)),("Llama-3.2-3B-Instruct","stageC_llama3b.json",(24,32,48,64))]
fig,axs=plt.subplots(1,3,figsize=(7.0,2.7),sharey=True)
for ax,(nm,fn,ms) in zip(axs,panels):
    R=load(fn)
    for k,m in enumerate(ms):
        rows=sorted([x for x in R if x["m"]==m and not x["press"] and not x["contam"] and x["compounding"]],key=lambda x:x["T"])
        ax.errorbar([r["T"] for r in rows],[r["acc"] for r in rows],yerr=[r["acc_se"] for r in rows],color=COL[k],marker=MK[k],ms=3.3,lw=1.1,ls=LS[k],capsize=1.3,label=f"m = {m}")
    ax.set_title(nm,fontsize=8.5); ax.set_xlabel("Nominal temperature T"); ax.set_ylim(-0.03,1.05); ax.legend(fontsize=6,frameon=False,loc="upper right")
axs[0].set_ylabel("Local accuracy")
fig.tight_layout(); fig.savefig("fig2_alphabet_fine.png",dpi=300); plt.close(fig)
# ---- Figure 3: detection rates (either direction) by indicator
inds=[("H","Entropy"),("conf","Confidence"),("ECE","ECE*"),("SE","Semantic\nentropy"),("dT","$T_{\\mathrm{eff}}$")]
conds=[("pressure","Pressure"),("contamination","Contamination"),("both","Both")]
HT=["","//","xx"]
fig,axs=plt.subplots(1,2,figsize=(7.0,2.8),sharey=True)
for ax,m in zip(axs,MODELS):
    for ci,(c,cn) in enumerate(conds):
        vals=[]
        for k,_ in inds:
            d=counts((m,),c,k); vals.append(d["det"]/d["n"])
        ax.bar(np.arange(5)+(ci-1)*0.26,vals,0.24,color=COL[ci],hatch=HT[ci],edgecolor="white" if HT[ci]=="" else "#ffffff",linewidth=0.5,label=cn)
    ax.set_xticks(range(5)); ax.set_xticklabels([n for _,n in inds],fontsize=7); ax.set_title(MN[m],fontsize=8.5); ax.set_ylim(0,1.05)
axs[0].set_ylabel("Share of matched cells flagged"); axs[0].legend(fontsize=6.5,frameon=False,loc="upper left")
fig.tight_layout(); fig.savefig("fig3_detection.png",dpi=300); plt.close(fig)
print("figures ok")
