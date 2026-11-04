import sys; sys.path.insert(0,'.')
from data import *
rows=[]
for k,d in SETS.items():
    L=lifetimes(d); med=km_median(L.months.values,L.event.values); ci=boot_median(L.months.values,L.event.values,B=1000)
    nv=notice_days(d); nall=notice_days(d,False)
    rows.append([k,len(L),int(L.event.sum()),round(L[L.event==1].months.median(),1),round(med,1),f"[{ci[0]:.1f}, {ci[1]:.1f}]",
                 len(nall),np.median(nall) if len(nall) else None,np.percentile(nall,25) if len(nall) else None,int((nall<90).sum()),int((nall-nv.size*0==0).sum()) if 0 else len(nall)-len(nv)])
out=pd.DataFrame(rows,columns=['set','models','retired','naive_med','KM_med','KM_CI','n_notice','notice_med','notice_q1','n<90','reroutes'])
pd.set_option('display.width',250); print(out.to_string(index=False)); out.to_csv('table_life.csv',index=False)
g=SETS['Gemini API (stable)']; print(g[g.notes.str.contains('redirect|reroute|auto-rout',case=False)][['model_id','notes']].to_string())
