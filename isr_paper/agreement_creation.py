"""Agreement between human coder(s) and the LLM / rule-based visual-content-creation scores, using the stratified design.
usage: python agreement_creation.py data/human_creation_sample_filled_coderA.xlsx [data/..._coderB.xlsx]
Reports: unweighted and design-weighted agreement, Cohen's kappa (unweighted, linear-weighted), binary (>=1) kappa, sensitivity/specificity of the LLM binary label,
and, if two coders are given, human-human agreement and agreement of the LLM with the human consensus (mean score rounded)."""
import sys, numpy as np, pandas as pd
from openpyxl import load_workbook
key=pd.read_csv("data/human_creation_sample_key.csv")
def read(f):
    ws=load_workbook(f,read_only=True)["coding"]; rows=list(ws.iter_rows(values_only=True)); df=pd.DataFrame(rows[1:],columns=rows[0])
    df=df[df.score_0_1_2.notna()&(df.score_0_1_2.astype(str).str.strip()!="")]; df["h"]=df.score_0_1_2.astype(int); return df[["row","h"]]
def kappa(a,b,w,lin=False,cats=(0,1,2)):
    a=np.asarray(a);b=np.asarray(b);w=np.asarray(w,float); w=w/w.sum(); P=np.zeros((len(cats),len(cats)))
    for i,x in enumerate(cats):
        for j,y in enumerate(cats): P[i,j]=w[(a==x)&(b==y)].sum()
    ra,rb=P.sum(1),P.sum(0); D=np.array([[abs(i-j)/(len(cats)-1) if lin else float(i!=j) for j in range(len(cats))] for i in range(len(cats))])
    o=(D*P).sum(); e=(D*np.outer(ra,rb)).sum(); return 1-o/e if e>0 else np.nan
def report(name,h,m,w):
    h=np.asarray(h);m=np.asarray(m);w=np.asarray(w,float)
    ex=lambda ww:(ww*(h==m)).sum()/ww.sum(); hb=(h>0).astype(int); mb=(m>0).astype(int)
    sens=(w*((hb==1)&(mb==1))).sum()/(w*(hb==1)).sum(); spec=(w*((hb==0)&(mb==0))).sum()/(w*(hb==0)).sum(); ppv=(w*((hb==1)&(mb==1))).sum()/(w*(mb==1)).sum()
    print(f"{name}: n={len(h)} | exact agreement unweighted {ex(np.ones(len(h))):.2f}, design-weighted {ex(w):.2f} | weighted kappa {kappa(h,m,w):.2f}, linear-weighted kappa {kappa(h,m,w,True):.2f} | binary(>=1) kappa {kappa(hb,mb,w,cats=(0,1)):.2f} | LLM sensitivity {sens:.2f}, specificity {spec:.2f}, PPV {ppv:.2f}")
if __name__=="__main__":
    files=sys.argv[1:]; H=[read(f) for f in files]
    d=key.merge(H[0].rename(columns={"h":"h1"}),on="row")
    if len(H)>1: d=d.merge(H[1].rename(columns={"h":"h2"}),on="row"); d["h"]=((d.h1+d.h2)/2).round().astype(int)
    else: d["h"]=d.h1
    print("rows coded:",len(d)); report("coder A vs LLM",d.h1,d.s,d.weight); report("coder A vs rule-based",d.h1,d.rule,d.weight)
    if len(H)>1:
        report("coder B vs LLM",d.h2,d.s,d.weight); report("coder A vs coder B",d.h1,d.h2,d.weight); report("consensus vs LLM",d.h,d.s,d.weight)
    print("\nBy stratum (unweighted) mean human score:",d.groupby("stratum").h1.mean().round(2).to_dict())
