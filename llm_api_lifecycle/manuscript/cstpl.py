import json, re, shutil, os, sys, zipfile
def rfind_run(s,end):
    ms=[m.start() for m in re.finditer(r'<w:r[ >]',s[:end])]
    return ms[-1]
from xml.sax.saxutils import escape
S='/tmp/claude-0/-home-user-fluffy-meme/7fe68551-a26f-5204-b375-89e5b2ba9817/scratchpad'
X=S+'/tpl/out'; shutil.rmtree(X,ignore_errors=True); shutil.copytree(S+'/tpl/x',X)
C=json.load(open(S+'/build/content.json'))
for x in C:
    if x.get('t')=='B' and x['s'].startswith('**Flex + NPV**'):
        x['s']='**Flex + NPV and flex + threshold.** '+x['s'].split('** and **Flex + threshold.** ',1)[1]
doc=open(X+'/word/document.xml',encoding='utf8').read()

# ---------- text normalisation ----------
NUM={'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10}
def numfix(s):
    w='|'.join(NUM)
    s=re.sub(rf'\b({w}) (to|and) ({w}) (day|week|month|year)s\b',lambda m:f"{NUM[m.group(1)]} {m.group(2)} {NUM[m.group(3)]} {m.group(4)}s",s)
    s=re.sub(rf'\b({w}) (day|week|month|year)(s?)\b',lambda m:f"{NUM[m.group(1)]} {m.group(2)}{m.group(3)}",s)
    s=re.sub(rf'\b({w}) calendar days\b',lambda m:f"{NUM[m.group(1)]} calendar days",s)
    s=re.sub(rf'\b(From|from) ({w}) to ({w}) months\b',lambda m:f"{m.group(1)} {NUM[m.group(2)]} to {NUM[m.group(3)]} months",s)
    return s
def cites(s):
    pat=re.compile(r'\s*\[(\d+)\]((?:\s*(?:,|–)\s*\[\d+\])*)([.,;:]?)')
    def rep(m):
        nums=[m.group(1)]+re.findall(r'\d+',m.group(2)); seps=re.findall(r'(,|–)\s*\[',m.group(2))
        t=nums[0]+''.join(sep+n for sep,n in zip(seps,nums[1:]))
        return m.group(3)+'⟦'+t+'⟧'
    return pat.sub(rep,s)
def prep(s): return cites(numfix(s))

def R(text,rpr=''):
    return f'<w:r>{("<w:rPr>"+rpr+"</w:rPr>") if rpr else ""}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'
def runs(s,base=''):
    out=[]
    for tok in re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*|\{\{[^}]+\}\}|⟦[^⟧]+⟧)',s):
        if not tok: continue
        if tok.startswith('**'): out.append(R(tok[2:-2],base+'<w:b/>'))
        elif tok.startswith('{{'): out.append(R('['+tok[2:-2]+']',base+'<w:highlight w:val="yellow"/>'))
        elif tok.startswith('⟦'): out.append(R(tok[1:-1],base+'<w:vertAlign w:val="superscript"/>'))
        elif tok.startswith('*'): out.append(R(tok[1:-1],base+'<w:i/>'))
        else: out.append(R(tok,base))
    return ''.join(out)
def para(style,inner,ppr=''): return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{ppr}</w:pPr>{inner}</w:p>'

SECT2='<w:sectPr><w:type w:val="continuous"/><w:pgSz w:w="11232" w:h="15408"/><w:pgMar w:top="1040" w:right="1040" w:bottom="1080" w:left="1040" w:header="600" w:footer="660" w:gutter="0"/><w:cols w:num="2" w:space="280"/><w:docGrid w:linePitch="299"/></w:sectPr>'
SECT1='<w:sectPr><w:type w:val="continuous"/><w:pgSz w:w="11232" w:h="15408"/><w:pgMar w:top="1040" w:right="1040" w:bottom="1080" w:left="1040" w:header="600" w:footer="660" w:gutter="0"/><w:cols w:space="280"/><w:docGrid w:linePitch="299"/></w:sectPr>'
def wide(inner):  # end 2-col section, place inner full width, end 1-col section
    return (f'<w:p><w:pPr><w:pStyle w:val="Para"/><w:ind w:firstLine="0"/>{SECT2}</w:pPr></w:p>'+inner+
            f'<w:p><w:pPr><w:pStyle w:val="Para"/><w:ind w:firstLine="0"/>{SECT1}</w:pPr></w:p>')
LBL='<w:color w:val="0070C0"/>'
def caption(s,kind):
    m=re.match(r'\*\*(Table|Figure) (\d+)\.\*\* (.*)',s); lab=f"{m.group(1).upper()} {m.group(2)}"
    return para('FigureCaption',R(lab,LBL)+runs('. '+prep(m.group(3))),'<w:spacing w:before="120" w:after="80"/>')
TW=9152
def tbl(widths,rows):
    if rows[0][0]=='Vendor': widths=[1900,1500,1950,1950,2100]
    k=TW/sum(widths); w=[int(x*k) for x in widths]; w[-1]+=TW-sum(w)
    b='<w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
    x=f'<w:tbl><w:tblPr><w:tblW w:w="{TW}" w:type="dxa"/><w:tblBorders>{b}</w:tblBorders><w:tblLayout w:type="fixed"/><w:tblCellMar><w:top w:w="40" w:type="dxa"/><w:left w:w="80" w:type="dxa"/><w:bottom w:w="40" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>'+''.join(f'<w:gridCol w:w="{v}"/>' for v in w)+'</w:tblGrid>'
    for i,r in enumerate(rows):
        x+='<w:tr>'+('<w:trPr><w:tblHeader/></w:trPr>' if i==0 else '')
        for j,c in enumerate(r):
            base='<w:rFonts w:ascii="Helvetica-Light" w:hAnsi="Helvetica-Light"/><w:sz w:val="17"/>'+('<w:b/>' if i==0 else '')
            sh='<w:shd w:val="clear" w:color="auto" w:fill="DCE6F1"/>' if i==0 else ''
            x+=f'<w:tc><w:tcPr><w:tcW w:w="{w[j]}" w:type="dxa"/>{sh}</w:tcPr>'+para('TableParagraph',runs(prep(c),base))+'</w:tc>'
        x+='</w:tr>'
    return x+'</w:tbl>'
def tnote(s): return para('ParaContinue',runs(prep(s),'<w:sz w:val="16"/>'),'<w:spacing w:before="60" w:after="120"/><w:ind w:firstLine="0"/>')
def sidebar(h,ps):
    inner=para('Heading2',R('The Analysis Behind the Options' if h=='THE ANALYSIS BEHIND THE OPTIONS' else h),'<w:spacing w:before="0"/>')+''.join(para('Para',runs(prep(p),'<w:sz w:val="17"/>'),'<w:spacing w:after="80"/><w:ind w:firstLine="0"/>') for p in ps)
    return f'<w:tbl><w:tblPr><w:tblW w:w="{TW}" w:type="dxa"/><w:tblBorders><w:top w:val="single" w:sz="8" w:space="0" w:color="4F81BD"/><w:bottom w:val="single" w:sz="8" w:space="0" w:color="4F81BD"/></w:tblBorders><w:tblCellMar><w:top w:w="120" w:type="dxa"/><w:left w:w="160" w:type="dxa"/><w:bottom w:w="120" w:type="dxa"/><w:right w:w="160" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid><w:gridCol w:w="{TW}"/></w:tblGrid><w:tr><w:tc><w:tcPr><w:tcW w:w="{TW}" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="EEF3FA"/></w:tcPr>{inner}</w:tc></w:tr></w:tbl>'
def image(rid,cx,cy):
    return para('Image',f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="901" name="Figure 1"/><wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr><a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="901" name="fig1.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>','<w:ind w:firstLine="0"/><w:jc w:val="center"/>')
def bullet(s):
    m=re.match(r'\*\*(.+?)\*\*\s*(.*)',s)
    lead=m.group(1).rstrip('.').rstrip(':'); rest=m.group(2)
    return para('ListParagraph',runs('*'+prep(lead)+'*')+runs('—'+prep(rest)),'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="6"/></w:numPr><w:ind w:left="360"/>')

# ---------- assemble body ----------
title=C[0]['o']['children'][0]['text']
abstract=C[2]['s'].split('—',1)[1]
intro=C[4:7]
intro0="To build a service on a cloud large language model (LLM) is, in effect, to rent a component that the vendor can withdraw."+intro[0]['s'].split('withdraw.',1)[1]
assert intro0.startswith('To build')
out=[]; first_para=True; i=7
# remaining intro paragraphs (2nd, 3rd)
for x in intro[1:]: out.append(para('Para',runs(prep(x['s']))))
seq=C[7:]
j=0; prev=None
while j<len(seq):
    x=seq[j]; t=x['t']
    if t=='H1': out.append(para('Heading1',R(x['s'].upper()))); prev='H'
    elif t=='H2': out.append(para('Heading2',R(x['s']))); prev='H'
    elif t=='P':
        st='Para'; ppr='<w:ind w:firstLine="0"/>' if prev=='H' else ''
        out.append(para(st,runs(prep(x['s'])),ppr)); prev='P'
    elif t=='B': out.append(bullet(x['s'])); prev='B'
    elif t=='cap' and seq[j+1]['t']=='table':
        tb=seq[j+1]; nt=seq[j+2] if seq[j+2]['t']=='note' else None
        inner=caption(x['s'],'t')+tbl(tb['w'],tb['r'])+(tnote(nt['s']) if nt else '')
        out.append(wide(inner)); j+=3 if nt else 2; prev='X'; continue
    elif t=='para' and j+1<len(seq) and seq[j+1]['t']=='cap':   # figure
        cx=int(6.2*914400); cy=int(cx*1194/2184)
        out.append(wide(image('rId901',cx,cy)+caption(seq[j+1]['s'],'f'))); j+=2; prev='X'; continue
    elif t=='para': pass
    elif t=='sidebar': out.append(wide(sidebar(x['h'],x['p']))); prev='X'
    elif t=='refs':
        out.append(para('ReferenceHead',R('REFERENCES')))
        for k,r in enumerate(x['refs'],1): out.append(para('Bibentry',R(f'{k}.')+'<w:r><w:tab/></w:r>'+runs(r)))
    j+=1
# drop the H1 "References" emitted from content (we add ReferenceHead ourselves)
body_new=''.join(out).replace(para('Heading1',R('REFERENCES')),'')
bio=para('AuthorBio',R('Ook Lee','<w:b/>')+runs(" is a professor at Hanyang University, Seoul, 04763, South Korea. Lee’s current research interests include {{three research interests}}. Lee received the {{highest degree}} in {{topic}} from {{institution}}. Lee is a {{membership grade}} of the IEEE Computer Society. Contact Lee at ooklee@hanyang.ac.kr."),'<w:spacing w:before="240" w:after="0" w:line="240" w:lineRule="auto"/>')
body_new+=bio

# ---------- edit the template's front matter ----------
b0=doc.index('<w:body>')+8; bend=doc.rindex('<w:sectPr')
front_end=doc.index('<w:footnoteReference')  # inside first body paragraph
p8_start=doc.rfind('<w:p ',0,front_end); p8_end=doc.index('</w:p>',front_end)+6
front=doc[b0:p8_start]; p8=doc[p8_start:p8_end]
# header box text, title, authors, abstract
front=front.replace('Article Type: Description (see ','Feature Article: LLM API Lifecycle Management',1)
front=front.replace('<w:t>below for</w:t>','<w:t></w:t>',1).replace('<w:t xml:space="preserve"> more detail)</w:t>','<w:t></w:t>',1)
front=front.replace('<w:t>Title: No More Than Four Lines</w:t>','<w:t>'+escape(title)+'</w:t>')
# authors: first author paragraph
a1s=front.index('<w:t>First</w:t>'); a1p=front.rfind('<w:p ',0,a1s); a1e=front.index('</w:p>',a1s)
ppr=front[front.index('<w:pPr>',a1p):front.index('</w:pPr>',a1p)+8]
front=front[:a1p]+'<w:p>'+ppr+R('Ook Lee, Hanyang University, Seoul, 04763, South Korea')+front[a1e:]
# second author paragraph: remove
a2s=front.index('<w:t>Second</w:t>'); a2p=front.rfind('<w:p ',0,a2s); a2e=front.index('</w:p>',a2s)+6
front=front[:a2p]+front[a2e:]
# third author: strip text runs but keep pict + sectPr
a3s=front.index('<w:t>Thir</w:t>'); a3p=front.rfind('<w:p ',0,a3s); a3e=front.index('</w:p>',a3s)
seg=front[a3p:a3e]; seg=re.sub(r'<w:r\b[^>]*>(?:(?!<w:r\b).)*?<w:t[^>]*>[^<]*</w:t></w:r>','',seg,flags=re.S)
front=front[:a3p]+seg+front[a3e:]
# abstract
ab=front.index('Abstract text goes here'); abp=front.rfind('<w:p ',0,ab); abe=front.index('</w:p>',ab)
seg=front[abp:abe]; dash=seg.index('—'); rstart=rfind_run(seg,seg.index('Abstract text goes here'))
seg=seg[:rstart]+runs(prep(abstract))
front=front[:abp]+seg+front[abe:]
# first body paragraph with drop cap: keep drawing run and footnote run
d_end=p8.index('</w:drawing></w:r>')+len('</w:drawing></w:r>')
fn_s=rfind_run(p8,p8.index('<w:footnoteReference')); 
p8=p8[:d_end]+runs(prep(intro0[1:]))+p8[fn_s:]
doc=doc[:b0]+front+p8+body_new+doc[bend:]
open(X+'/word/document.xml','w',encoding='utf8').write(doc)

# relationships + media
shutil.copy(S+'/fig1_framework.png',X+'/word/media/image4.png')
rels=open(X+'/word/_rels/document.xml.rels',encoding='utf8').read()
rels=rels.replace('</Relationships>','<Relationship Id="rId901" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image4.png"/></Relationships>')
open(X+'/word/_rels/document.xml.rels','w',encoding='utf8').write(rels)
# headers/footers
for f,a,b in [('header1.xml','THEME/FEATURE/DEPARTMENT','FEATURE'),('header2.xml','>HEAD<','>FEATURE<'),
              ('footer1.xml','Publication Title','IT Professional'),('footer2.xml','Publication Title','IT Professional'),('footer3.xml','Publication Name','IT Professional')]:
    p=X+'/word/'+f; t=open(p,encoding='utf8').read(); open(p,'w',encoding='utf8').write(t.replace(a,b))
out=sys.argv[1]
if os.path.exists(out): os.remove(out)
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for root,_,files in os.walk(X):
        for fn in files:
            full=os.path.join(root,fn); z.write(full,os.path.relpath(full,X))
print('ok')
