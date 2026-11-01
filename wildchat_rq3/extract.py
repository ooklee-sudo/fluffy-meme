import sys, re, hashlib, pyarrow.parquet as pq, pandas as pd
V1 = re.compile(r"^\W*(no\b|nope\b|wrong\b|incorrect\b|that'?s (wrong|not|incorrect)|that (doesn'?t|isn'?t|is not|does not)|this (doesn'?t|isn'?t|is not|does not)|try again|you misunderstood|you didn'?t|not what i|that is not|it'?s not|it is not|still (not|wrong)|actually\b)", re.I)
V2X = re.compile(r"(\bi meant\b|still not working|\bdoesn'?t work\b|\bnot working\b|traceback \(most recent|\berror:|\bexception\b|you (are|were) wrong|that'?s not what)", re.I)
YEAR = re.compile(r"\b(2022|2023|2024)\b")
PROD = re.compile(r"(chatgpt|gpt-?4|midjourney|stable diffusion|dall-?e|llama|claude|gemini|bard|copilot)", re.I)
CODE = re.compile(r"(```|\bdef \w+\(|\bimport \w+|#include|function\s*\(|SELECT .* FROM)", re.I)
def feat(conv):
    us=[t.get('content') or '' for t in conv if t.get('role')=='user']
    if not us: return None
    fp=us[0]; later=us[1:]
    c1=[bool(V1.match(u[:60])) for u in later]
    c2=[bool(V1.match(u[:60]) or V2X.search(u[:200])) for u in later]
    return dict(n_user=len(us), n_later=len(later), corr1=sum(c1), corr2=sum(c2),
      fp80=hashlib.md5(fp[:80].lower().encode()).hexdigest()[:10], fp_len=len(fp),
      year=bool(YEAR.search(fp)), prod=bool(PROD.search(fp)), code=bool(CODE.search(fp)))
src,dst=sys.argv[1],sys.argv[2]
t=pq.read_table(src,columns=['conversation_hash','model','timestamp','conversation','turn','language','toxic','redacted']).to_pandas()
t=t[t.language=='English']
rows=[]
for h,m,ts,conv,tn,tox in zip(t.conversation_hash,t.model,t.timestamp,t.conversation,t.turn,t.toxic):
    f=feat(conv)
    if f: f.update(hash=h,model=m,ts=ts,toxic=bool(tox)); rows.append(f)
pd.DataFrame(rows).to_parquet(dst); print(src,len(rows))
