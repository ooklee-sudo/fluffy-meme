import mon2,json
res=[]
for kind in ('ded','bat'):
  for V in (10.,20.,40.):
    for ratio in (1.2,1.4,2.0):
        r=mon2.analyze(kind,V,ratio,full=False)
        row=(kind,V,ratio,r['WfP']/r['Wfb'],r['Wm']/r['Wfb'],r['WfW']/r['Wfb'],r['Pm']/r['PfP']-1, min(r['pm']),max(r['pm']))
        res.append(row); print(row,flush=True)
json.dump(res,open('grid.json','w'))
