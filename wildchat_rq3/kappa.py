# Usage: kappa.py labelerA.csv labelerB.csv  (both from label_sheet.csv, label column filled)
import sys, pandas as pd
from sklearn.metrics import cohen_kappa_score
a=pd.read_csv(sys.argv[1]).set_index('id').label.str.upper().str.strip(); b=pd.read_csv(sys.argv[2]).set_index('id').label.str.upper().str.strip()
j=pd.concat([a,b],axis=1,keys=['a','b']).dropna(); j=j[(j.a!='U')&(j.b!='U')]
for name,f in [('narrow (A)',lambda s:s=='A'),('broad (A+B)',lambda s:s.isin(['A','B']))]:
    print(name,'n=',len(j),'agree=%.2f'%(f(j.a)==f(j.b)).mean(),'kappa=%.2f'%cohen_kappa_score(f(j.a),f(j.b)))
