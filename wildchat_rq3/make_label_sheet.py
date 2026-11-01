# Builds a blinded labeling sheet (text!) -> labeling_private/ (git-ignored). Usage: make_label_sheet.py OUTDIR shard1 shard2 ...
import sys, re, random, hashlib, pyarrow.parquet as pq, pandas as pd
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from detectors import DISSAT, dissat2
WEAK = re.compile(r"(error|wrong|i meant|doesn'?t|again)", re.I)
out=sys.argv[1]; random.seed(7)
pool={'A_flagged':[],'B_weakcue':[],'C_nocue':[]}; seen=set()
for sh in sys.argv[2:]:
    t=pq.read_table(sh,columns=['conversation_hash','model','conversation','language']).to_pandas()
    for h,m,conv,l in zip(t.conversation_hash,t.model,t.conversation,t.language):
        if l!='English' or len(conv)<3: continue
        for i in range(2,len(conv)):
            if conv[i].get('role')!='user' or conv[i-1].get('role')!='assistant': continue
            u=conv[i].get('content') or ''; a=conv[i-1].get('content') or ''
            if len(u)<2: continue
            k=hashlib.md5(u[:80].lower().encode()).hexdigest()
            if k in seen: continue
            s='A_flagged' if dissat2(u) else 'B_weakcue' if WEAK.search(u[:200]) else 'C_nocue'
            if random.random()<(0.15 if s!='C_nocue' else 0.002):
                pool[s].append((h,m,i,a,u)); seen.add(k)
rows=[]
for s,n in [('A_flagged',100),('B_weakcue',100),('C_nocue',100)]:
    random.shuffle(pool[s]); print(s,len(pool[s]))
    rows+=[(s,)+x for x in pool[s][:n]]
random.shuffle(rows)
key=[];sheet=[]
for j,(s,h,m,i,a,u) in enumerate(rows,1):
    sheet.append(dict(id=j,prev_assistant_end=a[-400:],user_turn=u[:500],label='',notes=''))
    key.append(dict(id=j,stratum=s,model=m,conversation_hash=h,turn_index=i))
pd.DataFrame(sheet).to_csv(f'{out}/label_sheet.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(key).to_csv(f'{out}/label_key_DO_NOT_OPEN.csv',index=False)
