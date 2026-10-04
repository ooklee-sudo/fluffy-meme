"""Rule-based (no-LLM) score of O*NET task statements for visual content creation, using the same 0/1/2 rubric as prompt_creation.txt.
Patterns written from the rubric text (not tuned to outcomes); validated against LLM labels on classified tasks (dev = first half of classified ids, test = second half)."""
import re, json, numpy as np, pandas as pd
VERB=r"(?:creat|design|produc|develop|prepar|edit|draw|paint|photograph|shoot|film|render|retouch|compos|lay\s*out|animat|illustrat|sketch|generat|build|construct|mak)\w*"
OBJ2=r"(?:presentation\w*|chart\w*|graphs?|visuali[sz]ation\w*|diagram\w*|promotional\s+material\w*|advertis\w+\s+material\w*|publication\w*|web\s*(?:page|site)\w*|banner\w*|infographic\w*|slides?|exhibit\w*|display\w*|signs?\b|packag\w+\s+design\w*)"
OBJ=r"(?:graphic\w*|illustrat\w*|photograph\w*|video\w*|film\w*|animat\w*|drawing\w*|sketch\w*|layout\w*|artwork\w*|visual\s+(?:design|display|merchandis|content|media|effect|material)\w*|multimedia|logo\w*|poster\w*|storyboard\w*|mock-?ups?|paintings?|murals?|cartoon\w*|image\w*|picture\w*|visual\s+aid\w*|brochure\w*|advertis\w+\s+(?:art|material|design|layout|copy)\w*)"
STRONG=re.compile(r"(?i)\b(?:photograph\w*|retouch\w*|animat\w+|illustrat\w*|storyboard\w*|graphic\s+design\w*|(?:video|film|motion\s+picture)\w*\s+(?:edit|produc|shoot)\w*|(?:edit|produc|shoot|compos)\w*\s+(?:video|film|photograph|image|graphic)\w*|sketch\w*\s+(?:rough|detailed|design)\w*)\b")
NEAR=re.compile(rf"(?i)\b{VERB}\b(?:\W+\w+){{0,6}}?\W+{OBJ}\b|\b{OBJ}\b(?:\W+\w+){{0,6}}?\W+\b{VERB}\b")
ANY=re.compile(rf"(?i)\b{OBJ}\b")
NEAR2=re.compile(rf"(?i)\b(?:creat|design|produc|develop|prepar|edit|generat|build|mak)\w*\b(?:\W+\w+){{0,5}}?\W+{OBJ2}\b")
def score(text:str)->int:
    if STRONG.search(text): return 2
    if NEAR.search(text) or NEAR2.search(text): return 1
    return 0
def f1(y,p):
    tp=((y==1)&(p==1)).sum(); fp=((y==0)&(p==1)).sum(); fn=((y==1)&(p==0)).sum(); pr=tp/max(tp+fp,1); rc=tp/max(tp+fn,1); return pr,rc,2*pr*rc/max(pr+rc,1e-9)
if __name__=="__main__":
    r=pd.DataFrame([json.loads(l) for l in open("data/all_creation_sonnet55.jsonl")]).sort_values("id"); r["rule"]=r.text.map(score)
    half=len(r)//2
    for name,d in (("dev (first half)",r.iloc[:half]),("test (second half)",r.iloc[half:])):
        y=(d.s>0).astype(int).values; p=(d.rule>0).astype(int).values; pr,rc,ff=f1(y,p)
        y2=(d.s==2).astype(int).values; p2=(d.rule==2).astype(int).values; pr2,rc2,ff2=f1(y2,p2)
        oc=d.groupby("soc").agg(l=("s",lambda x:(x/2).mean()),u=("rule",lambda x:(x/2).mean())); print(f"{name}: n={len(d)} | any>=1: P={pr:.2f} R={rc:.2f} F1={ff:.2f} | score==2: P={pr2:.2f} R={rc2:.2f} F1={ff2:.2f} | occupation-level corr(LLM,rule)={oc.l.corr(oc.u):.3f} (n_occ={len(oc)}), Spearman={oc.l.rank().corr(oc.u.rank()):.3f}")
