"""Pour manuscript.md into the IEEE CS magazine Word template (CS_Mag_7_22_3.docx).

Usage: python build_docx.py <unpacked_template_dir> manuscript.md figure1.png
The unpacked template must already have had merge_runs.py applied. Edits the
directory in place; zip it afterwards.
"""
import re, sys, shutil, os
from xml.sax.saxutils import escape

tdir, md_path, fig_path = sys.argv[1:4]
doc_path = os.path.join(tdir, 'word', 'document.xml')
x = open(doc_path, encoding='utf8').read()
md = open(md_path, encoding='utf8').read()

FIGURE_TITLE_ART = 'FEATURE ARTICLE: LLM AGENTS IN EXPERIMENTATION'
BLUE = '<w:color w:val="0070C0"/>'

# ---------- inline formatting ----------
CITE = re.compile(r'\s?((?:\[\d+\](?:–|, )?)+)([.,;:)]?)')

def cite_fix(t):
    """[1]–[3]. -> .^{1–3}  (superscript outside punctuation)."""
    def sub(m):
        nums = m.group(1).replace('][', ',').replace('], [', ',').replace('[', '').replace(']', '')
        return f'{m.group(2)}\x01{nums}\x02'
    return CITE.sub(sub, t)

def runs(text, base_rpr=''):
    """Markdown-ish inline text -> w:r runs. Supports **bold**, *italic*, \\* escape, citations."""
    text = cite_fix(text.replace('\\*', '\x03'))
    text = re.sub(r'(?<=[A-Za-zθ])_([A-Za-z0-9])', '\x04\\1\x05', text)      # s_k -> s with subscript k
    out = []
    for tok in re.split(r'(\*\*.+?\*\*|\*[^*]+?\*|\x01[^\x02]*\x02|\x04[^\x05]*\x05)', text):
        if not tok:
            continue
        rpr = base_rpr
        if tok.startswith('**'):
            tok, rpr = tok[2:-2], rpr + '<w:b/>'
        elif tok.startswith('*'):
            tok, rpr = tok[1:-1], rpr + '<w:i/>'
        elif tok.startswith('\x04'):
            tok, rpr = tok[1:-1], rpr + '<w:i/><w:vertAlign w:val="subscript"/>'
        elif tok.startswith('\x01'):
            tok, rpr = tok[1:-1], rpr + '<w:vertAlign w:val="superscript"/>'
        tok = escape(tok.replace('\x03', '*'))
        out.append(f'<w:r>{"<w:rPr>" + rpr + "</w:rPr>" if rpr else ""}<w:t xml:space="preserve">{tok}</w:t></w:r>')
    return ''.join(out)

def para(text, style='Para', first=False, extra_ppr='', base_rpr=''):
    ind = '<w:ind w:firstLine="0"/>' if first else ''
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{ind}{extra_ppr}</w:pPr>{runs(text, base_rpr)}</w:p>'

def heading(text):
    return f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>{runs(text.upper())}</w:p>'

# ---------- section breaks (copied from template) ----------
SECT_2COL = re.search(r'<w:sectPr[^>]*>(?:(?!</w:sectPr>).)*?<w:cols w:num="2" w:space="280"/>.*?</w:sectPr>', x, re.S).group(0)
SECT_1COL = ('<w:sectPr><w:type w:val="continuous"/><w:pgSz w:w="11232" w:h="15408"/>'
             '<w:pgMar w:top="1040" w:right="1040" w:bottom="1080" w:left="1040" w:header="600" w:footer="660" w:gutter="0"/>'
             '<w:cols w:space="280"/><w:docGrid w:linePitch="299"/></w:sectPr>')
FULL_W, COL_W = 9152, 4436                   # text widths in twips

def full_width(inner):
    """Close the running 2-column section, put inner at full width, then reopen 2 columns."""
    return (f'<w:p><w:pPr><w:pStyle w:val="Para"/>{SECT_2COL}</w:pPr></w:p>' + inner +
            f'<w:p><w:pPr><w:pStyle w:val="Para"/><w:ind w:firstLine="0"/>{SECT_1COL}</w:pPr></w:p>')

# ---------- tables ----------
def table(rows, widths, caption, note=None):
    bd = '<w:tblBorders><w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/><w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/><w:insideH w:val="single" w:sz="2" w:space="0" w:color="BFBFBF"/></w:tblBorders>'
    cell_rpr = '<w:rFonts w:ascii="Helvetica-Light" w:hAnsi="Helvetica-Light"/><w:sz w:val="16"/><w:szCs w:val="16"/>'
    trs = []
    for i, r in enumerate(rows):
        tcs = []
        for w, c in zip(widths, r):
            shade = '<w:shd w:val="clear" w:color="auto" w:fill="E7EEF7"/>' if i == 0 else ''
            rpr = cell_rpr + ('<w:b/>' if i == 0 else '')
            kn = '<w:keepNext/>' if i < len(rows) - 1 else ''
            tcs.append(f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shade}</w:tcPr>'
                       f'<w:p><w:pPr>{kn}<w:spacing w:before="20" w:after="20" w:line="220" w:lineRule="exact"/><w:ind w:firstLine="0"/></w:pPr>{runs(c, rpr)}</w:p></w:tc>')
        hdr = '<w:trPr><w:tblHeader/></w:trPr>' if i == 0 else '<w:trPr><w:cantSplit/></w:trPr>'
        trs.append(f'<w:tr>{hdr}{"".join(tcs)}</w:tr>')
    grid = ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    tbl = (f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/>{bd}'
           f'<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="60" w:type="dxa"/><w:right w:w="60" w:type="dxa"/></w:tblCellMar></w:tblPr>'
           f'<w:tblGrid>{grid}</w:tblGrid>{"".join(trs)}</w:tbl>')
    num, rest = caption.split('.', 1)
    cap = (f'<w:p><w:pPr><w:pStyle w:val="AuthorBio"/><w:keepNext/><w:spacing w:before="200" w:after="60"/></w:pPr>'
           f'<w:r><w:rPr>{BLUE}</w:rPr><w:t>{escape(num.upper())}</w:t></w:r>{runs("." + rest)}</w:p>')
    out = cap + tbl
    if note:
        out += para(note, 'ParaContinue', first=True, base_rpr='<w:sz w:val="16"/>')
    return out + '<w:p><w:pPr><w:pStyle w:val="ParaContinue"/><w:spacing w:after="0"/></w:pPr></w:p>'

# ---------- figure ----------
def figure(rid, caption, width_twips):
    from PIL import Image
    w_px, h_px = Image.open(fig_path).size
    cx = int(width_twips * 635)            # 1 twip = 635 EMU
    cy = int(cx * h_px / w_px)
    drawing = (f'<w:r><w:rPr><w:noProof/></w:rPr><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
               f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="901" name="Figure 1"/>'
               '<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
               '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
               '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="901" name="figure1.png"/><pic:cNvPicPr/></pic:nvPicPr>'
               f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
               f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
               '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')
    num, rest = caption.split('.', 1)
    return (f'<w:p><w:pPr><w:pStyle w:val="Para"/><w:keepNext/><w:ind w:firstLine="0"/><w:jc w:val="center"/></w:pPr>{drawing}</w:p>'
            f'<w:p><w:pPr><w:pStyle w:val="FigureCaption"/></w:pPr><w:r><w:rPr>{BLUE}</w:rPr><w:t>{escape(num.upper())}</w:t></w:r>{runs("." + rest)}</w:p>')

# ---------- sidebar ----------
def sidebar(lines):
    title = lines[0].strip('* ')
    ps = [f'<w:p><w:pPr><w:pStyle w:val="AuthorBio"/><w:spacing w:before="60" w:after="60"/></w:pPr>'
          f'<w:r><w:rPr><w:b/>{BLUE}</w:rPr><w:t>{escape(title.upper())}</w:t></w:r></w:p>']
    for l in lines[1:]:
        if not l:
            continue
        if l.startswith('- '):
            ps.append(f'<w:p><w:pPr><w:pStyle w:val="AuthorBio"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="6"/></w:numPr>'
                      f'<w:spacing w:before="20" w:after="20"/><w:ind w:left="240" w:hanging="200"/></w:pPr>{runs(l[2:])}</w:p>')
        else:
            ps.append(f'<w:p><w:pPr><w:pStyle w:val="AuthorBio"/><w:spacing w:before="60" w:after="20"/></w:pPr>{runs(l)}</w:p>')
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{COL_W}" w:type="dxa"/><w:tblBorders>'
            '<w:top w:val="single" w:sz="12" w:space="0" w:color="0070C0"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="0070C0"/></w:tblBorders>'
            '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:top w:w="60" w:type="dxa"/><w:left w:w="100" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar></w:tblPr>'
            f'<w:tblGrid><w:gridCol w:w="{COL_W}"/></w:tblGrid><w:tr><w:tc><w:tcPr><w:tcW w:w="{COL_W}" w:type="dxa"/>'
            f'<w:shd w:val="clear" w:color="auto" w:fill="EEF3F9"/></w:tcPr>{"".join(ps)}</w:tc></w:tr></w:tbl>'
            '<w:p><w:pPr><w:pStyle w:val="ParaContinue"/><w:spacing w:after="0"/></w:pPr></w:p>')

# ---------- parse markdown ----------
front, rest = md.split('\n---\n', 2)[1:] if md.startswith('---') else (None, md)
title = re.search(r'title: "(.*)"', md).group(1)
abstract = re.search(r'\*\*Abstract\.\*\* (.*)', md).group(1)
body_md = md.split('\n---\n\n', 1)[1] if '\n---\n\n' in md else md
body_md = body_md[body_md.find('\n---\n') + 5:] if body_md.lstrip().startswith('**Abstract') else body_md
main, refs_md = body_md.split('## References', 1)
refs_md, about_md = refs_md.split('## About the author', 1)

blocks = re.split(r'\n\s*\n', main.strip())
FIG_RID = 'rId901'
out, first_para_done, after_heading, i = [], False, False, 0
pending_full = []

def lines_of(b): return b.split('\n')

while i < len(blocks):
    b = blocks[i].strip()
    if b.startswith('## '):
        h = b[3:].strip()
        out.append(f'<w:p><w:pPr><w:pStyle w:val="AckHead"/></w:pPr>{runs(h.upper())}</w:p>' if h == 'Acknowledgments' else heading(h))
        after_heading = True
    elif b.startswith('> '):
        out.append(sidebar([l[2:] if l.startswith('> ') else l.lstrip('>').strip() for l in lines_of(b)]))
    elif b.startswith('**Table') and i + 1 < len(blocks) and blocks[i + 1].lstrip().startswith('|'):
        cap = b.strip('*').strip()
        rows = [[c.strip() for c in l.strip().strip('|').split('|')] for l in lines_of(blocks[i + 1]) if not re.match(r'^\|[-| ]+\|$', l.strip())]
        note = None
        if i + 2 < len(blocks) and blocks[i + 2].startswith('*A random'):
            note = blocks[i + 2].strip('*'); i += 1
        if len(rows[0]) > 4:
            widths = [1700, 1000, 820, 1400, 1000, 1100, 1032, 1100]
            out.append(full_width(table(rows, widths, cap, note)))
        else:
            widths = [1150, 900, 900, 1486]
            out.append(table(rows, widths, cap, note))
        i += 1
    elif b.startswith('!['):
        cap = re.match(r'!\[(.*)\]\(', b, re.S).group(1)
        out.append(full_width(figure(FIG_RID, cap, FULL_W)))
    elif b.startswith('- '):
        for l in lines_of(b):
            out.append(f'<w:p><w:pPr><w:pStyle w:val="ListParagraph"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="6"/></w:numPr><w:ind w:left="360"/></w:pPr>{runs(l[2:])}</w:p>')
    elif re.match(r'^\d+\. ', b):
        for l in lines_of(b):
            n, t = l.split('. ', 1)
            out.append(f'<w:p><w:pPr><w:pStyle w:val="ListParagraph"/><w:tabs><w:tab w:val="left" w:pos="360"/></w:tabs><w:ind w:left="360" w:hanging="360"/></w:pPr>'
                       f'<w:r><w:t xml:space="preserve">{n})</w:t></w:r><w:r><w:tab/></w:r>{runs(t)}</w:p>')
    else:
        text = ' '.join(lines_of(b))
        if not first_para_done:
            first_para_done = True
            out.append(('DROPCAP', text))
        else:
            out.append(para(text, first=after_heading))
        after_heading = False
        i += 1
        continue
    if not b.startswith('## '):
        after_heading = False
    i += 1

# ---------- drop-cap first paragraph (reuse template drawing + footnote) ----------
k = x.find('r:embed="rId15"')
p_start = x.rfind('<w:p ', 0, k)
p_end = x.find('</w:p>', k) + 6
tpl_p = x[p_start:p_end]
draw_run = re.search(r'<w:r>(?:(?!<w:r>).)*?<w:drawing>.*?</w:drawing></w:r>', tpl_p, re.S).group(0)
fn_run = re.search(r'<w:r>(?:(?!<w:r>).)*?<w:footnoteReference.*?</w:r>', tpl_p, re.S).group(0)
ppr = re.search(r'<w:pPr>.*?</w:pPr>', tpl_p, re.S).group(0)
blocks_xml = []
for o in out:
    if isinstance(o, tuple):
        t = o[1]
        assert t.startswith('T'), 'first paragraph must start with T to match the drop cap'
        blocks_xml.append(f'<w:p>{ppr}{draw_run}{runs(t[1:])}{fn_run}</w:p>')
    else:
        blocks_xml.append(o)

# ---------- references and bios ----------
refs = re.findall(r'\[(\d+)\] (.+)', refs_md)
blocks_xml.append('<w:p><w:pPr><w:pStyle w:val="ReferenceHead"/></w:pPr><w:r><w:t>REFERENCES</w:t></w:r></w:p>')
for n, t in refs:
    blocks_xml.append(f'<w:p><w:pPr><w:pStyle w:val="Bibentry"/></w:pPr><w:r><w:t>{n}.</w:t></w:r><w:r><w:tab/></w:r>{runs(t)}</w:p>')
blocks_xml.append('<w:p><w:pPr><w:pStyle w:val="Bibentry"/></w:pPr></w:p>')
for l in [l for l in about_md.strip().split('\n') if l.strip()]:
    blocks_xml.append(f'<w:p><w:pPr><w:pStyle w:val="AuthorBio"/><w:spacing w:before="40" w:after="0"/></w:pPr>{runs(l)}</w:p>')

# ---------- splice body ----------
end = x.rfind('<w:sectPr')
x = x[:p_start] + ''.join(blocks_xml) + x[end:]

# ---------- front matter ----------
x = x.replace('Article Type: Description (see below for more detail)', escape(FIGURE_TITLE_ART))
x = x.replace('Title: No More Than Four Lines', escape(title))
# authors: keep one placeholder line, drop the other two (keep the section break)
for who in ('First', 'Second', 'Third'):
    k = x.find(f'<w:t>{who}')
    if k < 0:
        k = x.find(f'>{who}')
    ps = x.rfind('<w:p ', 0, k); pe = x.find('</w:p>', k) + 6
    p = x[ps:pe]
    keep_ppr = re.search(r'<w:pPr>.*?</w:pPr>', p, re.S).group(0)
    if who == 'First':
        name, affil = re.search(r'author:\n  - "(.*?)"', md).group(1).split(', ', 1)
        new = (f'<w:p>{keep_ppr}<w:r><w:t xml:space="preserve">{escape(name)}, </w:t></w:r>'
               f'<w:r><w:rPr><w:b w:val="0"/><w:bCs/><w:i/><w:iCs/></w:rPr><w:t>{escape(affil)}</w:t></w:r></w:p>')
    elif '<w:sectPr' in keep_ppr:
        new = f'<w:p>{keep_ppr}</w:p>'
    else:
        new = ''
    x = x[:ps] + new + x[pe:]
# abstract: replace everything after "Abstract—"
k = x.find('<w:t>Abstract</w:t>')
ps = x.rfind('<w:p ', 0, k); pe = x.find('</w:p>', k) + 6
p = x[ps:pe]
dash_end = p.find('<w:t>—</w:t></w:r>') + len('<w:t>—</w:t></w:r>')
abs_rpr = '<w:rFonts w:ascii="Helvetica-Black" w:hAnsi="Helvetica-Black"/><w:b/><w:i/><w:sz w:val="20"/><w:szCs w:val="20"/>'
x = x[:ps] + p[:dash_end] + runs(abstract, abs_rpr) + '</w:p>' + x[pe:]

open(doc_path, 'w', encoding='utf8').write(x)

# ---------- image relationship ----------
shutil.copy(fig_path, os.path.join(tdir, 'word', 'media', 'figure1.png'))
rels_p = os.path.join(tdir, 'word', '_rels', 'document.xml.rels')
rels = open(rels_p, encoding='utf8').read()
if FIG_RID not in rels:
    rels = rels.replace('</Relationships>', f'<Relationship Id="{FIG_RID}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/figure1.png"/></Relationships>')
    open(rels_p, 'w', encoding='utf8').write(rels)

# ---------- running heads / footers ----------
for f, a, b in [('header1.xml', 'THEME/FEATURE/DEPARTMENT', 'FEATURE'), ('header2.xml', 'HEAD', 'FILTER OR PRIOR?')]:
    fp = os.path.join(tdir, 'word', f); s = open(fp, encoding='utf8').read()
    s = s.replace(f'>{a}<', f'>{b}<'); open(fp, 'w', encoding='utf8').write(s)
for f in ('footer1.xml', 'footer2.xml', 'footer3.xml'):
    fp = os.path.join(tdir, 'word', f)
    if os.path.exists(fp):
        s = open(fp, encoding='utf8').read().replace('>Publication Title<', '>IEEE Intelligent Systems<').replace('>Publication Name<', '>IEEE Intelligent Systems<')
        open(fp, 'w', encoding='utf8').write(s)
print('ok: blocks', len(blocks_xml), 'refs', len(refs))
