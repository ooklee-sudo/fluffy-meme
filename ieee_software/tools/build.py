import sys, re, copy
sys.path.insert(0, sys.argv[1])
import docx
from docx.shared import Cm, Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
import content as C

tpl, figdir, out = sys.argv[2], sys.argv[3], sys.argv[4]
d = docx.Document(tpl)
body = d.element.body
els = list(body)

# ---- columns check
def cols(sp):
    c = sp.find(qn('w:cols')); return c.get(qn('w:num')) if c is not None else '1'
sect_after8 = [cols(e.find('.//'+qn('w:sectPr'))) for e in (els[58], els[62])]
final_cols = cols(body.find(qn('w:sectPr')))
print('section cols 58,62,final:', sect_after8, final_cols)

def set_runs_text(p_el, text, keep_first=True):
    rs = [r for r in p_el.findall(qn('w:r'))]
    ts = [t for r in rs for t in r.findall(qn('w:t'))]
    ts[0].text = text; ts[0].set('{http://www.w3.org/XML/1998/namespace}space','preserve')
    for t in ts[1:]: t.text = ''

# ---- title & header box
p0 = els[0]
tb = p0.find('.//'+qn('w:txbxContent'))
tts = list(tb.iter(qn('w:t'))); tts[0].text = C.HEADER
for t in tts[1:]: t.text = ''
outside = [t for t in p0.iter(qn('w:t')) if t not in tts]
outside[0].text = C.TITLE
for t in outside[1:]: t.text = ''
# send the decorative VML bands behind the text so a three-line title is not covered
import re as _re
for v in p0.iter('{urn:schemas-microsoft-com:vml}rect'):
    st = v.get('style')
    v.set('style', _re.sub(r'z-index:(\d+)', lambda m: 'z-index:-' + m.group(1), st))
# readable title: 1.15 line spacing, 24 pt, no negative tracking
ppr0 = p0.find(qn('w:pPr'))
sp = OxmlElement('w:spacing'); sp.set(qn('w:before'),'640'); sp.set(qn('w:after'),'240'); sp.set(qn('w:line'),'276'); sp.set(qn('w:lineRule'),'auto')
ppr0.append(sp)
for t in outside:
    r = t.getparent(); rpr = r.find(qn('w:rPr'))
    if rpr is None: rpr = OxmlElement('w:rPr'); r.insert(0, rpr)
    for tag in ('w:sz','w:szCs','w:spacing'):
        e = rpr.find(qn(tag))
        if e is not None: rpr.remove(e)
    for tag,val in (('w:spacing','0'),('w:sz','48'),('w:szCs','48')):
        e = OxmlElement(tag); e.set(qn('w:val'), val); rpr.append(e)

# ---- authors: write into els[4] (keeps sectPr), drop 2,3
a = els[4]
rs = a.findall(qn('w:r'))
# first run plain (name), make a bold-italic run for affiliation by copying from els[2]
plain = copy.deepcopy(els[2].findall(qn('w:r'))[0]); bi = copy.deepcopy(els[2].findall(qn('w:r'))[3])
for r in rs: a.remove(r)
plain.find(qn('w:t')).text = C.AUTHOR[0] + ', '
plain.find(qn('w:t')).set('{http://www.w3.org/XML/1998/namespace}space','preserve')
bi.find(qn('w:t')).text = C.AUTHOR[1]
a.append(plain); a.append(bi)
body.remove(els[2]); body.remove(els[3])

# ---- abstract (keep the "Abstract—"? CS magazines print no label; keep template label runs 0-1)
ab = els[6]
ars = ab.findall(qn('w:r'))
ars[2].find(qn('w:t')).text = C.ABSTRACT
for r in ars[3:]:
    for t in r.findall(qn('w:t')): t.text = ''
for h in ab.findall(qn('w:hyperlink')): ab.remove(h)
# remove the "Abstract—" label runs
for r in ars[:2]: ab.remove(r)

# ---- templates for list paragraph pPr and bib entry
li_ppr = copy.deepcopy(els[40].find(qn('w:pPr')))
# ---- delete old body 9..91
anchor = els[8]
for e in els[9:92]:
    body.remove(e)

cur = anchor
def insert(el):
    global cur
    cur.addnext(el); cur = el

def new_par(style):
    p = OxmlElement('w:p'); para = Paragraph(p, d._body); para.style = d.styles[style]; return para

TOK = re.compile(r'(\*\*.+?\*\*|\*.+?\*|\{[^}]+\})')
def add_rich(para, text, base_bold=False):
    for part in TOK.split(text):
        if not part: continue
        if part.startswith('**'): r = para.add_run(part[2:-2]); r.bold = True
        elif part.startswith('*'): r = para.add_run(part[1:-1]); r.italic = True
        elif part.startswith('{'): r = para.add_run(part[1:-1]); r.font.superscript = True
        else: r = para.add_run(part)
        if base_bold: r.bold = True

def par(style, text, bold=False):
    p = new_par(style); add_rich(p, text, bold); insert(p._p); return p

def table(rows, widths=None, size=8):
    t = d.add_table(rows=len(rows), cols=len(rows[0]))
    try: t.style = d.styles['Table Grid']
    except KeyError: pass
    for i,row in enumerate(rows):
        for j,val in enumerate(row):
            c = t.cell(i,j); c.text = ''
            p = c.paragraphs[0]; p.style = d.styles['Table Paragraph'] if 'Table Paragraph' in [s.name for s in d.styles] else p.style
            r = p.add_run(val); r.font.size = Pt(size)
            if i == 0: r.bold = True
    if widths: fix_width(t, widths)
    insert(t._tbl); return t


def fix_width(t, widths_cm):
    tbl = t._tbl; tblPr = tbl.tblPr
    lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); tblPr.append(lay)
    tw = tblPr.find(qn('w:tblW'))
    if tw is None: tw = OxmlElement('w:tblW'); tblPr.append(tw)
    tw.set(qn('w:w'), str(int(sum(widths_cm)*567))); tw.set(qn('w:type'), 'dxa')
    t.autofit = False
    mar = OxmlElement('w:tblCellMar')
    for side in ('left','right'):
        m = OxmlElement('w:'+side); m.set(qn('w:w'),'45'); m.set(qn('w:type'),'dxa'); mar.append(m)
    tblPr.append(mar)
    grid = tbl.tblGrid
    for gc, w in zip(grid.findall(qn('w:gridCol')), widths_cm): gc.set(qn('w:w'), str(int(w*567)))
    for row in t.rows:
        for c, w in zip(row.cells, widths_cm): c.width = Cm(w)

first = True
for kind, val in C.BODY:
    if kind == 'H1': par('Heading 1', val)
    elif kind == 'ACK': par('AckHead', val)
    elif kind == 'P':
        par('Para' if first or True else 'ParaContinue', val); first = False
    elif kind == 'LI':
        p = new_par('List Paragraph'); p._p.insert(0, copy.deepcopy(li_ppr)); add_rich(p, val); insert(p._p)
    elif kind == 'FIG':
        fn, cap = val
        p = new_par('Para'); p.add_run().add_picture(f'{figdir}/{fn}', width=Cm(8.2)); insert(p._p)
        cp = new_par('FigureCaption'); add_rich(cp, cap); insert(cp._p)
    elif kind == 'TABLE':
        cap, rows, note = val
        par('TableCaption', cap)
        n=len(rows[0])
        table(rows, [3.0,1.7,3.6] if n==3 else [2.0,1.8,1.3,1.8,1.3], 8 if n==3 else 7)
        np_=par('ParaContinue', note)
        for r in np_.runs: r.font.size = Pt(8)
    elif kind == 'SIDEBAR':
        title, items = val
        t = d.add_table(rows=1, cols=1)
        try: t.style = d.styles['Table Grid']
        except KeyError: pass
        c = t.cell(0,0); p = c.paragraphs[0]; p.style = d.styles['Heading 2']; p.add_run(title)
        for it in items:
            q = c.add_paragraph(style='Para'); add_rich(q, it)
        fix_width(t, [8.2])
        bd = OxmlElement('w:tblBorders')
        for side in ('top','left','bottom','right'):
            e = OxmlElement('w:'+side); e.set(qn('w:val'),'single'); e.set(qn('w:sz'),'8'); e.set(qn('w:color'),'F7944B'); bd.append(e)
        t._tbl.tblPr.append(bd)
        insert(t._tbl)
        par('Para', '')

par('ReferenceHead', 'REFERENCES')
for i, ref in enumerate(C.REFS, 1):
    par('Bib_entry', f'{i}.\t{ref}')
p = new_par('AuthorBio'); r = p.add_run(C.BIO[0]); r.bold = True; add_rich(p, C.BIO[1]); insert(p._p)


def set_hf(hf, text):
    ts=[t for p in hf.paragraphs for r in p.runs for t in [r]]
    if ts:
        ts[0].text=text
        for r in ts[1:]: r.text=''
s0=d.sections[0]
set_hf(s0.header, 'LLM-GRADED EVALUATION')
set_hf(s0.even_page_header, 'FEATURE ARTICLE')
d.save(out)
print('saved', out)
