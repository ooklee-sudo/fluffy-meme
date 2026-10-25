import numpy as np
from scipy.special import betaln as bl
H,c=100.0,1.0
types={"easy":(0.6,2.0,0.4),"medium":(0.3,3.0,0.4),"hard":(0.05,4.0,0.2)}  # (a,b,share) SYNTHETIC
def ec(a,b,k):
    s=np.exp([bl(a,b+j)-bl(a,b) for j in range(k+1)]); return c*s[:k].sum()+H*s[k]
Ns={t:int(max(0,np.ceil(a*H/c-a-b))) for t,(a,b,w) in types.items()}
print("type-specific N*:",Ns)
tt=sum(w*ec(a,b,Ns[t]) for t,(a,b,w) in types.items())
common=min(range(0,300),key=lambda k:sum(w*ec(a,b,k) for a,b,w in types.values()))
cc=sum(w*ec(a,b,common) for a,b,w in types.values())
print("type-specific cost %.2f | best common cap k=%d cost %.2f | human-only 100 | k=10: %.2f"%(tt,common,cc,sum(w*ec(a,b,10) for a,b,w in types.values())))
print("gain from type-specific stopping: %.1f%%"%(100*(1-tt/cc)))
