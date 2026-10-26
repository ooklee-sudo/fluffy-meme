import json, pickle, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','Liberation Serif','DejaVu Serif'],'font.size':7.5})
DATA='/tmp/claude-0/-home-user-fluffy-meme/85836436-e025-583a-b00a-2fcdeefc7114/scratchpad/data/'
J=json.load(open('study1_real_validation.json')); sim=pickle.load(open('sim_study1.pkl','rb'))
fig,(a,b)=plt.subplots(2,1,figsize=(3.45,4.1))
h=np.arange(24)
a.plot(h,np.array(J['ipp']['hourly'])*100,'k-',lw=1.4,label='IPP (simulated)')
a.plot(h,np.array(J['hpp']['hourly'])*100,color='0.55',ls=':',lw=1.2,label='HPP / polling (simulated)')
a.plot(h,np.array(J['real']['Bluesky (UTC, 4 full days)']['hourly'])*100,'C0--',lw=1.2,label='Bluesky (UTC)')
a.plot(h,np.array(J['real']['Money.SE (US Eastern)']['hourly'])*100,'C3-.',lw=1.2,label='Money.SE (US Eastern)')
a.set_xlim(0,23); a.set_xticks(range(0,24,3)); a.set_xlabel('Hour of day'); a.set_ylabel('Share of posting events (%)')
a.legend(frameon=False,fontsize=6.5,loc='upper left',ncol=1); a.set_ylim(0,11.5); a.text(.98,.96,'(a)',transform=a.transAxes,ha='right',va='top')
# delay CDFs
z=np.load(DATA+'money_ref.npz'); md=z['com']; md=md[(md>=0)&(md<=48)]
D=pd.read_parquet(DATA+'bsky_tid.parquet'); rep=D[D.is_reply&(D.pt>0)]; bd=((rep.t-rep.pt)/3.6e9); bd=bd[(bd>=0)&(bd<=48)].values
def sd(s): 
    x=np.concatenate([r['comments'][:,1]-r['comments'][:,0] for r in sim[s]]); return x[(x>=0)&(x<=48)]
def cdf(ax,x,**k):
    x=np.sort(x)[::max(1,len(x)//4000)]; ax.plot(np.maximum(x,1/60),np.arange(1,len(x)+1)/len(x),**k)
cdf(b,sd('ipp'),color='k',lw=1.4,label='IPP (simulated)'); cdf(b,sd('hpp'),color='0.55',ls=':',lw=1.2,label='HPP (simulated)')
cdf(b,bd,color='C0',ls='--',lw=1.2,label='Bluesky replies'); cdf(b,md,color='C3',ls='-.',lw=1.2,label='Money.SE comments')
b.set_xscale('log'); b.set_xlim(1/60,48); b.set_xticks([1/60,.25,1,4,16,48]); b.set_xticklabels(['1 min','15 min','1 h','4 h','16 h','48 h'])
b.set_xlabel('Reply delay'); b.set_ylabel('Cumulative share'); b.set_ylim(0,1); b.legend(frameon=False,fontsize=6.5,loc='upper left'); b.text(.98,.04,'(b)',transform=b.transAxes,ha='right',va='bottom')
for ax in (a,b): ax.spines[['top','right']].set_visible(False)
fig.tight_layout(pad=.4,h_pad=1.0); fig.savefig('fig4_public_data.png',dpi=300)
