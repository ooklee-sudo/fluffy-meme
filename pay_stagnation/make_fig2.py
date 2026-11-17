import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
B,O,G="#2a7ad5","#ec6b36","#444"
plt.rcParams.update({"font.size":15,"lines.markersize":10,"font.family":"DejaVu Sans","text.color":"#111","axes.edgecolor":G,"xtick.color":G,"ytick.color":G})
W,H=4148,1637; dpi=200
fig=plt.figure(figsize=(W/dpi,H/dpi),dpi=dpi)
a=fig.add_axes([0.084,0.176,0.325,0.69]); b=fig.add_axes([0.6625,0.176,0.283,0.69])
# a
a.plot([2013,2019,2024],[84.79,100.62,101.39],":",color=B,lw=4); a.plot([2013,2019,2024],[84.79,100.62,101.39],"o",color=B,ms=11)
ex=[2012,2019,2020,2024,2025]; ey=[59.8,78.8,81.2,95.1,102.8]
a.plot([2012,2019,2020,2024],[59.8,78.8,81.2,95.1],":",color=O,lw=4); a.plot([2019,2020],[78.8,81.2],"-",color=O,lw=4); a.plot([2024,2025],[95.1,102.8],"-",color=O,lw=4)
a.plot(ex,ey,"s",color=O,ms=11)
a.set_xlim(2011.5,2025.8); a.set_ylim(50,118); a.set_xticks([2012,2015,2018,2021,2024]); a.set_yticks(range(50,111,10))
a.grid(axis="y",color="#e5e5e5"); a.set_axisbelow(True)
for s in ("top","right"): a.spines[s].set_visible(False)
a.set_ylabel("Average annual pay (KRW million, nominal)")
a.text(2012.8,106,"Full professors,\nprivate universities",va="center",fontsize=15)
a.text(2020.5,70,"Employees,\nlarge firms",va="center",fontsize=15)
a.annotate("",xy=(2012.5,84.79),xytext=(2012.5,59.8),arrowprops=dict(arrowstyle="<->",color="k"))
a.text(2012.9,69,"Premium\n+42%",va="center",fontsize=15)
a.annotate("",xy=(2023.7,101.39),xytext=(2023.7,95.1),arrowprops=dict(arrowstyle="<->",color="k"))
a.text(2023.4,98,"+7%",ha="right",va="center",fontsize=15)
a.text(2011.5,121,"a",fontsize=20,fontweight="bold")
# b
labs=["Full professors,\nprivate universities (2019)","Executives,\nlarge firms (2019)","Executives,\nSamsung Electronics (2024)"]
labs[1]="Unregistered executives,\nlarge firms (2019)"
vals=[100.6,342.7,671]; cols=[B,O,O]; txt=["100.6","342.7  (3.4×)","671  (6.6×)"]
y=[2,1,0]
b.barh(y,vals,color=cols,height=0.55)
b.set_yticks(y); b.set_yticklabels(labs,fontsize=15,color="#555")
for yy,v,t in zip(y,vals,txt): b.text(v+10,yy,t,va="center",fontsize=15)
b.set_xlim(0,800); b.set_xticks(range(0,801,200)); b.set_ylim(-0.6,2.6)
b.grid(axis="x",color="#e5e5e5"); b.set_axisbelow(True)
for s in ("top","right"): b.spines[s].set_visible(False)
b.set_xlabel("Average annual pay (KRW million, nominal)")
b.text(0,2.85,"b",fontsize=20,fontweight="bold",transform=b.transData)
fig.savefig("fig2_new.png",dpi=dpi)
