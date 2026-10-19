import json,numpy as np,matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.family":"Liberation Serif","font.size":9.5,"mathtext.fontset":"stix"})
c=json.load(open('azure/hourly.json'))
days=sorted({k.split()[0] for k in c})
A=np.array([[c.get(f"{d} {h}",0) for h in range(24)] for d in days])/1000
m=A.mean(0); top=set(np.argsort(-m)[:10])
print(np.round(m,1), sorted(top))
fig,ax=plt.subplots(figsize=(6,3.6),dpi=300)
for h in range(24):
    if h in top: ax.axvspan(h-.5,h+.5,color="0.92",lw=0)
ax.fill_between(range(24),A.min(0),A.max(0),color="0.8",lw=0,alpha=.7,label="Range across the 7 days")
ax.plot(range(24),m,color="black",lw=1.6,marker="o",ms=4,label="Mean over 7 days (24 phases)")
ax.set_xlim(-.5,23.5); ax.set_ylim(0,None)
ax.set_xticks(range(0,24,2)); ax.set_xlabel("Hour of day (UTC)"); ax.set_ylabel("Requests per hour (thousands)")
for s in("top","right"): ax.spines[s].set_visible(False)
ax.grid(axis="y",color="0.92",lw=.8); ax.set_axisbelow(True)
import matplotlib.patches as mp
h,l=ax.get_legend_handles_labels(); h.append(mp.Patch(color="0.92")); l.append("Ten busiest hours (by mean)")
ax.legend(h,l,frameon=False,loc="upper left",fontsize=8.5)
fig.tight_layout(); fig.savefig("figs/figure_daily.png")
