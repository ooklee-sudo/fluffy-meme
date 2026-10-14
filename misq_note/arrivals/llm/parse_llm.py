import re, json, pandas as pd
txt=open('llm/llm_list.wikitext').read()
rows=[]; unparsed=[]
year=None
for sec in re.split(r'\n===(\d{4})===\n',txt)[1:]:
    pass
parts=re.split(r'\n===(\d{4})===\n',txt)
for yr,body in zip(parts[1::2],parts[2::2]):
    body=body.split('\n== ')[0]
    spans={}  # col -> (remaining, value)
    for blk in body.split('\n|-')[1:]:
        lines=[l for l in blk.split('\n')]
        if any(l.startswith('!') for l in lines): continue
        cells=[]
        for l in lines:
            if l.startswith('|}') or l.startswith('|+'): continue
            if l.startswith('|'): cells.append(l[1:])
            elif cells: cells[-1]+=' '+l
        if not cells: continue
        vals=[]; ci=0; it=iter(cells); out={}
        col=0
        for c in it:
            while col in spans and spans[col][0]>0:
                out[col]=spans[col][1]; spans[col]=(spans[col][0]-1,spans[col][1]); col+=1
            m=re.match(r'\s*([^|]*?(?:rowspan|colspan)[^|]*?)\|(?!\|)(.*)',c,re.S) if ('rowspan' in c.split('|')[0] or 'colspan' in c.split('|')[0]) else None
            content=c
            if m: attrs,content=m.group(1),m.group(2); rs=re.search(r'rowspan="?(\d+)',attrs)
            else: rs=None
            out[col]=content.strip()
            if rs and int(rs.group(1))>1: spans[col]=(int(rs.group(1))-1,content.strip())
            col+=1
            if col>=3: break
        name=out.get(0,''); date=out.get(1,''); dev=out.get(2,'')
        rows.append(dict(year_section=int(yr),name_raw=name,date_raw=date,dev_raw=dev))
D=pd.DataFrame(rows)
def parse_date(s):
    m=re.search(r'\{\{dts\|\s*(?:format=\w+\|)?\s*(\d{4})-(\d{2})(?:-(\d{2}))?',s,re.I)
    if m: y,mo,d=m.group(1),m.group(2),m.group(3); return f'{y}-{mo}',(f'{y}-{mo}-{d}' if d else None)
    m=re.search(r'\{\{dts\|\s*(\d{4})\|(\d{1,2})\|(\d{1,2})',s)
    return (None,None)
r=D.date_raw.map(parse_date); D['month']=[a for a,b in r]; D['day']=[b for a,b in r]
def clean(x): 
    x=re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]',r'\1',x); x=re.sub(r'\{\{[^}]*\}\}|<ref.*?(</ref>|/>)|<[^>]+>','',x); return x.strip()
D['name']=D.name_raw.map(clean); D['developer']=D.dev_raw.map(clean)
print(len(D),D.month.notna().sum(),D.day.notna().sum()); print(D[D.month.isna()].date_raw.head(15).tolist())
D.drop(columns=['name_raw','date_raw','dev_raw']).assign(date_raw=D.date_raw.str[:60]).to_csv('llm/llm_releases.csv',index=False)
print(D[['name','month','day','developer']].head(12).to_string()); print(D.developer.value_counts().head(12))
