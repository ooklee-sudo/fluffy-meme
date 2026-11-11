import sys, pandas as pd, numpy as np
sys.path.insert(0, 'src'); from leaks import RX, RX_ANY, ASK, first_leak
D='/home/user/data'
for name in ['55k','100k','140k']:
    d = pd.read_pickle(f'{D}/{name}.pkl')
    anyA = d.a_turns.map(lambda ts: any(RX_ANY.search(t or '') for t in ts)); anyB = d.b_turns.map(lambda ts: any(RX_ANY.search(t or '') for t in ts))
    la = d.a_turns.map(first_leak); lb = d.b_turns.map(first_leak)
    LA = la.str[0].notna(); LB = lb.str[0].notna()
    ask = d.user_turns.map(lambda ts: any(ASK.search(t or '') for t in ts))
    print(f"{name}: n={len(d)}  any dev-name mention A|B={np.mean(anyA|anyB):.3%}  self-disclosure A|B={np.mean(LA|LB):.3%}  exactly one={np.mean(LA^LB):.3%}  both={np.mean(LA&LB):.3%}  user-asks={ask.mean():.3%}  one-leak & no-ask n={int(((LA^LB)&~ask).sum())}")
    if name=='100k': print('   anony share', d.anony.mean())
