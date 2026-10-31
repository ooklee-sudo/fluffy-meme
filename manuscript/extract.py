import pdfplumber,re,json,os
PDF='/root/.claude/uploads/1fd62ada-9235-5e3b-a034-568e2e5620dd/ef32874d-2026-TR-21648_Proof_hi.pdf'
pdf=pdfplumber.open(PDF)
os.makedirs('figs',exist_ok=True)
blocks=[]  # dicts: kind para|heading|table|image
cur=None
refs=False
def inside(o,bbs):
    return any(b[0]-1<=o['x0'] and o['x1']<=b[2]+1 and b[1]-1<=o['top'] and o['bottom']<=b[3]+1 for b in bbs)
def segs(chars):
    out=[]; prev=None
    for c in chars:
        if c['text']==' ': 
            prev=c; txt=' '
        if prev is not None and c['text']!=' ' and c['x0']-prev['x1']>0.18*c['size']:
            if out: out[-1][0]+=' '
        prev=c
        b='Bold' in c['fontname']; i='Italic' in c['fontname']
        if out and out[-1][1]==b and out[-1][2]==i: out[-1][0]+=c['text']
        else: out.append([c['text'],b,i])
    return out
for pi in range(1,57):
    p=pdf.pages[pi]
    tabs=p.find_tables(); bbs=[t.bbox for t in tabs]
    base=lambda o: o.get('object_type')!='char' or (o['upright'] and 'Myriad' not in o['fontname'] and o['x0']>=68 and o['top']<745 and not inside(o,bbs))
    f=p.filter(base)
    g=p.filter(lambda o: o.get('object_type')!='char' or (o['upright'] and 'Myriad' not in o['fontname']))
    items=[]
    for ln in f.extract_text_lines(return_chars=True,keep_blank_chars=False):
        items.append((ln['top'],'line',ln))
    for t in tabs:
        items.append((t.bbox[1],'table',t))
    for k,im in enumerate(p.images):
        fn=f'figs/p{pi+1}_{k}.png'
        p.crop((im['x0'],im['top'],im['x1'],im['bottom'])).to_image(resolution=170).save(fn)
        items.append((im['top'],'image',fn))
    items.sort(key=lambda x:x[0])
    for top,kind,o in items:
        if kind=='line':
            chars=[c for c in o['chars']]
            txt=o['text'].strip()
            if not txt: continue
            bold=sum(c['text'].strip()!='' and 'Bold' in c['fontname'] for c in chars)/max(1,sum(c['text'].strip()!='' for c in chars))
            x0=o['x0']
            heading = bold>0.9 and len(txt)<110
            if heading:
                refs = txt.startswith('References') or (refs and not txt.startswith('Appendix A'))
                blocks.append({'kind':'heading','segs':segs(chars)}); cur=None; continue
            newp = (x0<100 if refs else x0>=100) or cur is None or re.match(r'^(Proof of|Proposition \d|Table [A-Z]?\d|Figure \d)',txt)
            # captions / notes start new paragraph when previous block not para
            if newp and not (cur is not None and x0<100 and False):
                cur={'kind':'para','segs':[]}; blocks.append(cur)
            if cur['segs']:
                last=cur['segs'][-1][0]
                if last.endswith('-') and chars and chars[0]['text'].islower(): pass
                else: cur['segs'][-1][0]+=' '
            for s in segs(chars):
                if cur['segs'] and cur['segs'][-1][1]==s[1] and cur['segs'][-1][2]==s[2]: cur['segs'][-1][0]+=s[0]
                else: cur['segs'].append(s)
        elif kind=='table':
            rows=[]
            for r in o.rows:
                row=[]
                for c in r.cells:
                    if c is None: row.append(''); continue
                    x0,t0,x1,b0=c
                    try: tx=g.crop((x0-1,t0-1,x1+1,b0+1),strict=False).extract_text() or ''
                    except Exception: tx=''
                    row.append(tx.replace('\n',' ').strip())
                rows.append(row)
            if blocks and blocks[-1]['kind']=='table' and top<100:
                prev=blocks[-1]['rows']
                if rows and rows[0]==prev[0]: rows=rows[1:]
                prev.extend(rows)
            else: blocks.append({'kind':'table','rows':rows})
            cur=None
        else:
            blocks.append({'kind':'image','file':o}); cur=None
json.dump(blocks,open('blocks.json','w'),ensure_ascii=False,indent=0)
print(len(blocks),[ (b['kind']) for b in blocks].count('table'))
for b in blocks[:25]:
    print(b['kind'],(''.join(s[0] for s in b['segs'])[:90] if 'segs' in b else str(b.get('rows',b.get('file')))[:80]))
