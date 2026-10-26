"""Pours the manuscript content (content.docx from build_manuscript.py) into the official IEEE Access Word template."""
import copy, io, re, sys
import docx
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Emu
from docx.text.paragraph import Paragraph
from lxml import etree

SP = '/tmp/claude-0/-home-user-fluffy-meme/85836436-e025-583a-b00a-2fcdeefc7114/scratchpad/'
TPL = '/root/.claude/uploads/85836436-e025-583a-b00a-2fcdeefc7114/cb009c11-Access-Template-2024_1.docx'
PHOTO = '/tmp/claude-0/-home-user-fluffy-meme/85836436-e025-583a-b00a-2fcdeefc7114/images/1.jpg'
OUT = '/home/user/fluffy-meme/Poisson-SNS_IEEE_Access_manuscript.docx'
TITLE = 'Event-Driven LLM-Agent Simulation for Pre-Testing Social Media Seeding Strategies'
COLW = int(3.3 * 914400)

T = docx.Document(TPL); C = docx.Document(SP + 'content.docx')
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
tp = T.paragraphs; cp = C.paragraphs
body = T.element.body

def sty_id(doc, name):
    for s in doc.styles:
        if s.name == name: return s.style_id
    raise KeyError(name)

def set_pstyle(p_el, name, keep=()):
    ppr = p_el.find(qn('w:pPr'))
    if ppr is None: ppr = OxmlElement('w:pPr'); p_el.insert(0, ppr)
    for ch in list(ppr):
        if ch.tag not in [qn(k) for k in keep]: ppr.remove(ch)
    st = OxmlElement('w:pStyle'); st.set(qn('w:val'), sty_id(T, name)); ppr.insert(0, st)
    return ppr

def clean_runs(p_el):
    for r in p_el.findall(qn('w:r')):
        rpr = r.find(qn('w:rPr'))
        if rpr is None: continue
        for ch in list(rpr):
            if ch.tag not in (qn('w:i'), qn('w:b'), qn('w:vertAlign')): rpr.remove(ch)
        if len(rpr) == 0: r.remove(rpr)

def new_para(style, text='', runs=None):
    p = OxmlElement('w:p'); set_pstyle(p, style)
    for t, sup in (runs or [(text, False)]):
        r = OxmlElement('w:r')
        if sup:
            rp = OxmlElement('w:rPr'); v = OxmlElement('w:vertAlign'); v.set(qn('w:val'), 'superscript'); rp.append(v); r.append(rp)
        tt = OxmlElement('w:t'); tt.text = t; tt.set(qn('xml:space'), 'preserve'); r.append(tt); p.append(r)
    return p

def retarget_images(el):
    for blip in el.iter(qn('a:blip')):
        rid = blip.get(qn('r:embed'))
        blob = C.part.related_parts[rid].blob
        new_rid, _ = T.part.get_or_add_image(io.BytesIO(blob))
        blip.set(qn('r:embed'), new_rid)

# ---------------- front matter ----------------
def set_runs(p, items):
    """Replace runs of template paragraph p with (text, superscript) items, reusing the first run's formatting."""
    el = p._p; runs = el.findall(qn('w:r'))
    for r in runs: el.remove(r)
    for t, sup in items:
        r = OxmlElement('w:r')
        if sup:
            rp = OxmlElement('w:rPr'); v = OxmlElement('w:vertAlign'); v.set(qn('w:val'), 'superscript'); rp.append(v); r.append(rp)
        tt = OxmlElement('w:t'); tt.text = t; tt.set(qn('xml:space'), 'preserve'); r.append(tt); el.append(r)
set_runs(tp[2], [(TITLE, False)])
set_runs(tp[3], [('Ook Lee', False), ('1', True)])
p4 = tp[4]
for r in p4._p.findall(qn('w:r')): 
    pass
# affiliation line keeps the template's 7 pt formatting
runs4 = p4._p.findall(qn('w:r'))
runs4[1].find(qn('w:t')).text = 'Department of Information System, Hanyang University, Seoul, Korea'
tp[5]._p.getparent().remove(tp[5]._p); tp[6]._p.getparent().remove(tp[6]._p)
set_runs(tp[7], [('Corresponding author: Ook Lee (e-mail: ooklee@hanyang.ac.kr).', False)])
tp[8]._p.getparent().remove(tp[8]._p)           # sponsor footnote: no funding information supplied
# abstract
ab_src = cp[2]._p; ab = tp[9]._p
for r in ab.findall(qn('w:r'))[2:]: ab.remove(r)
for ch in list(ab_src)[2:]:                      # skip pPr and the "Abstract—" label run
    if ch.tag == qn('w:pPr'): continue
    ab.append(copy.deepcopy(ch))
ab_runs = [r for r in ab.findall(qn('w:r'))]
for r in ab_runs[2:]:
    rpr = r.find(qn('w:rPr'))
    if rpr is not None: r.remove(rpr)
# the first text run copied after the label may begin with the label's remainder; drop a leading dash if present
for r in ab_runs[2:3]:
    t = r.find(qn('w:t'))
    if t is not None and t.text and t.text.startswith('—'): t.text = t.text[1:]
# index terms
it = tp[10]._p
for r in it.findall(qn('w:r'))[2:]: it.remove(r)
for h in it.findall(qn('w:hyperlink')): it.remove(h)
terms = cp[3].runs[1].text.lstrip('—')
r = OxmlElement('w:r'); t = OxmlElement('w:t'); t.text = terms; r.append(t); it.append(r)

# ---------------- remove template body after the front matter ----------------
front_end = tp[11]._p                                  # empty IT paragraph that carries the front-matter section break
final_sect = body.find(qn('w:sectPr'))
node = front_end.getnext()
while node is not None and node is not final_sect:
    nxt = node.getnext(); body.remove(node); node = nxt

# ---------------- convert the manuscript body ----------------
num_part = T.part.numbering_part.element
def next_numid():
    return max(int(n.get(qn('w:numId'))) for n in num_part.findall(qn('w:num'))) + 1
def h2_group_num():
    nid = next_numid()
    num = OxmlElement('w:num'); num.set(qn('w:numId'), str(nid))
    a = OxmlElement('w:abstractNumId'); a.set(qn('w:val'), '20'); num.append(a)
    lo = OxmlElement('w:lvlOverride'); lo.set(qn('w:ilvl'), '0'); so = OxmlElement('w:startOverride'); so.set(qn('w:val'), '1'); lo.append(so); num.append(lo)
    last = num_part.findall(qn('w:num'))[-1]; last.addnext(num); return nid

out = []; started = False; first_h1 = True; cur_num = None; prev_kind = None
src = [ch for ch in C.element.body if ch.tag != qn('w:sectPr')]
# skip the front matter of the content document (title, author, abstract, index terms)
i0 = next(i for i, ch in enumerate(src) if ch.tag == qn('w:p') and ''.join(x.text or '' for x in ch.iter(qn('w:t'))).startswith('I. INTRODUCTION'))
src = src[i0:]
def ptext(el): return ''.join(x.text or '' for x in el.iter(qn('w:t')))
def sname(el):
    ps = el.find(qn('w:pPr') + '/' + qn('w:pStyle')); 
    if ps is None: return 'Normal'
    for s in C.styles:
        if s.style_id == ps.get(qn('w:val')): return s.name
    return 'Normal'
for el in src:
    if el.tag not in (qn('w:p'), qn('w:tbl')): continue
    if el.tag == qn('w:tbl'):
        t = copy.deepcopy(el); tpr = t.find(qn('w:tblPr'))
        for x in tpr.findall(qn('w:tblStyle')): tpr.remove(x)
        for p in t.iter(qn('w:p')):
            ppr = p.find(qn('w:pPr'))
            if ppr is not None:
                for x in ppr.findall(qn('w:pStyle')): ppr.remove(x)
            for r in p.findall(qn('w:r')):
                rpr = r.find(qn('w:rPr'))
                if rpr is None: rpr = OxmlElement('w:rPr'); r.insert(0, rpr)
                for x in rpr.findall(qn('w:sz')) + rpr.findall(qn('w:szCs')): rpr.remove(x)
                for tag in ('w:sz', 'w:szCs'):
                    e = OxmlElement(tag); e.set(qn('w:val'), '14'); rpr.append(e)
            if ppr is None: ppr = OxmlElement('w:pPr'); p.insert(0, ppr)
        out.append(t); prev_kind = 'tbl'; continue
    st = sname(el); txt = ptext(el).replace('\xa0', ' ')
    if st == 'Heading 1':
        m = re.match(r'^[IVX]+\. (.*)', txt)
        if m:
            e = new_para('H1_List (No Space)' if first_h1 else 'H1_List (Space)', m.group(1).upper()); first_h1 = False
            cur_num = None; out.append(e)
        elif txt.startswith('Appendix'):
            a, b = txt.split(':', 1)
            out.append(new_para('H1', a.strip().upper())); e = new_para('H1', b.strip().upper()); out.append(e)
        else:
            out.append(new_para('H1', txt.upper()))
        prev_kind = 'h'; continue
    if st == 'Heading 2':
        if cur_num is None: cur_num = h2_group_num()
        e = new_para('H2_After H1', re.sub(r'^[A-Z]\. ', '', txt))
        ppr = e.find(qn('w:pPr')); npr = OxmlElement('w:numPr')
        il = OxmlElement('w:ilvl'); il.set(qn('w:val'), '0'); ni = OxmlElement('w:numId'); ni.set(qn('w:val'), str(cur_num)); npr.append(il); npr.append(ni)
        ppr.append(npr); out.append(e); prev_kind = 'h'; continue
    if st in ('Table Caption',):
        e = copy.deepcopy(el); set_pstyle(e, 'Table Title'); clean_runs(e); out.append(e); prev_kind = 'cap'; continue
    if st == 'Captioned Figure':
        e = copy.deepcopy(el); set_pstyle(e, 'Figure Caption'); ppr = e.find(qn('w:pPr')); jc = OxmlElement('w:jc'); jc.set(qn('w:val'), 'center'); ppr.append(jc)
        for ext in e.iter(qn('wp:extent')):
            cx, cy = int(ext.get('cx')), int(ext.get('cy')); ext.set('cx', str(COLW)); ext.set('cy', str(int(cy * COLW / cx)))
        for ext in e.iter(qn('a:ext')):
            if ext.get('cx'):
                cx, cy = int(ext.get('cx')), int(ext.get('cy')); ext.set('cx', str(COLW)); ext.set('cy', str(int(cy * COLW / cx)))
        retarget_images(e); out.append(e); prev_kind = 'fig'; continue
    if st == 'Image Caption':
        e = new_para('Fig Caption', re.sub(r'^Fig\. \d+\. ', '', txt)); out.append(e); prev_kind = 'figcap'; continue
    if st == 'Bibliography':
        e = copy.deepcopy(el)
        for om in e.findall(qn('m:oMath')): e.remove(om)          # [7]: the superscript 3 of S^3 is rebuilt as a Unicode character below
        set_pstyle(e, 'References'); clean_runs(e)
        ts = list(e.iter(qn('w:t'))); buf = ''.join(t.text or '' for t in ts)
        m = re.match(r'^\[\d+\]\s*', buf); n = len(m.group(0)) if m else 0
        for t in ts:
            if n <= 0: break
            cut = min(n, len(t.text or '')); t.text = (t.text or '')[cut:]; n -= cut
        for tab in e.iter(qn('w:tab')):
            tab.getparent().remove(tab); break
        for t in e.iter(qn('w:t')):
            if '\u201cS: Social' in (t.text or ''): t.text = t.text.replace('\u201cS: Social', '\u201cS\u00b3: Social')
        out.append(e); prev_kind = 'ref'; continue
    # body paragraphs
    e = copy.deepcopy(el)
    if txt.startswith('Note.') or txt.startswith('Note '):
        set_pstyle(e, 'footnote text'); ppr = e.find(qn('w:pPr')); ind = OxmlElement('w:ind'); ind.set(qn('w:firstLine'), '0'); ppr.append(ind)
    elif e.find('.//' + qn('m:oMathPara')) is not None:
        set_pstyle(e, 'PARA'); ppr = e.find(qn('w:pPr')); sp = OxmlElement('w:spacing'); sp.set(qn('w:before'), '60'); sp.set(qn('w:after'), '60'); sp.set(qn('w:line'), '240'); sp.set(qn('w:lineRule'), 'auto'); ppr.append(sp)
    else:
        set_pstyle(e, 'PARA' if prev_kind == 'h' else 'PARA_Indent')
    clean_runs(e); out.append(e); prev_kind = 'p'

# bio with photo
bio_tpl = tp[227]._p
bio = copy.deepcopy(bio_tpl)
drawings = [r for r in bio.findall(qn('w:r')) if r.find(qn('w:drawing')) is not None]
text_runs = [r for r in bio.findall(qn('w:r')) if r.find(qn('w:drawing')) is None]
name_rpr = copy.deepcopy(text_runs[0].find(qn('w:rPr'))); body_rpr = copy.deepcopy(text_runs[1].find(qn('w:rPr'))) if len(text_runs) > 1 and text_runs[1].find(qn('w:rPr')) is not None else None
for r in bio.findall(qn('w:r')): bio.remove(r)
photo_run = copy.deepcopy(drawings[1])
rid, img = T.part.get_or_add_image(PHOTO)
for blip in photo_run.iter(qn('a:blip')): blip.set(qn('r:embed'), rid)
# crop the photo to the 1 in x 1.25 in aspect ratio without distortion
w, h = img.px_width, img.px_height
target = 1.0 / 1.25
if w / h > target:
    cut = int((1 - target * h / w) / 2 * 100000); src_rect = dict(l=str(cut), r=str(cut))
else:
    cut = int((1 - w / (target * h)) / 2 * 100000); src_rect = dict(t=str(cut), b=str(cut))
for sr in photo_run.iter(qn('a:srcRect')):
    for k, v in src_rect.items(): sr.set(k, v)
bio.append(photo_run)
pp = bio.find(qn('w:pPr')); sp = pp.find(qn('w:spacing')); sp.set(qn('w:before'), '200')
def run(text, rpr):
    r = OxmlElement('w:r')
    if rpr is not None: r.append(copy.deepcopy(rpr))
    t = OxmlElement('w:t'); t.text = text; t.set(qn('xml:space'), 'preserve'); r.append(t); return r
bio.append(run('OOK LEE', name_rpr))
bio.append(run(' is a professor in the Department of Information System at Hanyang University, Seoul, Korea. He received the Ph.D. degree in management of information systems from Claremont Graduate University, USA. He was a faculty member at the University of Queensland, Australia, the University of Nevada at Las Vegas, USA, and North Carolina A&T State University, USA. His research interests include information system economics, information system maintenance, large language models, and critical social theory.', body_rpr))
out.append(bio)

anchor = final_sect
for e in out: anchor.addprevious(e)

# ---------------- headers / footers / final section ----------------
hdr_rid = [r for r, rel in T.part.rels.items() if rel.reltype.endswith('/header') and rel.target_ref == 'header2.xml'][0]
if final_sect.find(qn('w:headerReference')) is None:
    hr = OxmlElement('w:headerReference'); hr.set(qn('w:type'), 'default'); hr.set(qn('r:id'), hdr_rid); final_sect.insert(0, hr)
for rel in T.part.rels.values():
    if rel.reltype.endswith('/header') and rel.target_ref == 'header2.xml':
        h = rel.target_part
        for t in h.element.iter(qn('w:t')):
            if t.text == 'Author Name': t.text = 'Ook Lee'
            elif t.text and t.text.startswith('Preparation of Papers'): t.text = TITLE
    if rel.reltype.endswith('/footer') and rel.target_ref == 'footer8.xml':
        f = rel.target_part; p = f.element.find(qn('w:p'))
        for r in p.findall(qn('w:r')):
            t = r.find(qn('w:t'))
            if t is not None and t.text == '8':
                p.remove(r)
                for kind, txt in (('begin', None), (None, ' PAGE '), ('end', None)):
                    nr = OxmlElement('w:r')
                    if kind: fc = OxmlElement('w:fldChar'); fc.set(qn('w:fldCharType'), kind); nr.append(fc)
                    else: it_ = OxmlElement('w:instrText'); it_.text = txt; it_.set(qn('xml:space'), 'preserve'); nr.append(it_)
                    p.insert(0 if False else len(p), nr)
                # move the page field before the tab/volume runs
                runs = p.findall(qn('w:r')); fld = runs[-3:]
                for fr in fld: p.remove(fr)
                first = p.findall(qn('w:r'))[0]
                for fr in reversed(fld): first.addprevious(fr)
                break
        for t in f.element.iter(qn('w:t')):
            if t.text == 'VOLUME XX, 2017': t.text = 'VOLUME XX, 2026'
T.core_properties.title = TITLE; T.core_properties.author = 'Ook Lee'
T.save(OUT)
print('saved', OUT)
