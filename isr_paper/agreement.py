"""usage: python agreement.py data/human_coding_sample_filled.csv  -> weighted/unweighted kappa, human vs each model, and human-human if --h2 given"""
import csv,json,sys
def kappa(a,b,w=None):
    cats=[0,1,2];n=len(a)
    wt=(lambda i,j:0 if i==j else 1) if not w else (lambda i,j:abs(i-j)**2/4)
    o=sum(wt(x,y) for x,y in zip(a,b))/n
    e=sum(wt(i,j)*(a.count(i)/n)*(b.count(j)/n) for i in cats for j in cats)
    return 1-o/e if e else float("nan")
H={int(r["id"]):int(r["score_0_1_2"]) for r in csv.DictReader(open(sys.argv[1],encoding="utf-8-sig")) if r["score_0_1_2"].strip()}
M=[json.loads(l) for l in open("data/model_labels_sample.jsonl")]
for m in [k for k in M[0] if k!="id"]:
    ids=[r["id"] for r in M if r["id"] in H]; a=[H[i] for i in ids]; b=[{r["id"]:r[m] for r in M}[i] for i in ids]
    print(m,"n",len(ids),"exact",round(sum(x==y for x,y in zip(a,b))/len(ids),3),"kappa",round(kappa(a,b),3),"weighted kappa",round(kappa(a,b,1),3),
          "binary(>0) kappa",round(kappa([int(v>0) for v in a],[int(v>0) for v in b]),3))
