import sys, re, hashlib, pyarrow.parquet as pq, pandas as pd
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from detectors import DISSAT, dissat2, YEAR, ENT, CODE
def feat(conv):
    us=[t.get('content') or '' for t in conv if t.get('role')=='user']
    if not us: return None
    fp=us[0]; later=us[1:]; alltext=" ".join(us)
    return dict(n_user=len(us), n_later=len(later),
      corr1=sum(1 for u in later if DISSAT.search(u[:120])), corr2=sum(1 for u in later if dissat2(u)),
      fp80=hashlib.md5(fp[:80].encode()).hexdigest()[:10], fp_len=len(fp),
      year=bool(YEAR.search(alltext)), prod=bool(ENT.search(alltext)), code=bool(CODE.search(alltext)))
src,dst=sys.argv[1],sys.argv[2]
t=pq.read_table(src,columns=['conversation_hash','model','timestamp','conversation','turn','language','toxic','redacted']).to_pandas()
t=t[t.language=='English']
rows=[]
for h,m,ts,conv,tn,tox in zip(t.conversation_hash,t.model,t.timestamp,t.conversation,t.turn,t.toxic):
    f=feat(conv)
    if f: f.update(hash=h,model=m,ts=ts,toxic=bool(tox)); rows.append(f)
pd.DataFrame(rows).to_parquet(dst); print(src,len(rows))
