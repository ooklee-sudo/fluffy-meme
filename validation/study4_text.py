"""Builds the Study 4 (public-data comparison) additions to the manuscript. Called from build.py."""
import copy, json, pickle, re
import numpy as np
from docx.shared import Inches, Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = '/home/user/fluffy-meme/validation/'
J = json.load(open(HERE + 'study1_real_validation.json'))
SIM = pickle.load(open(HERE + 'sim_study1.pkl', 'rb'))
BS, MO, LA, WP = ('Bluesky (UTC, 4 full days)', 'Money.SE (US Eastern)', 'Law.SE (US Eastern)', 'Workplace.SE (US Eastern)')
R = J['real']; I, H, P = J['ipp'], J['hpp'], J['poll']

def seg_replace(p, old, new):
    """Replace `old` (no math inside) by `new` in a paragraph made of many runs plus OMML objects."""
    segs, cur = [], []
    for ch in p._p:
        if ch.tag == qn('w:r') and ch.find(qn('w:t')) is not None:
            cur.append(ch)
        else:
            if cur: segs.append(cur); cur = []
    if cur: segs.append(cur)
    for runs in segs:
        txt = ''.join(''.join(t.text or '' for t in r.findall(qn('w:t'))) for r in runs)
        k = txt.find(old)
        if k < 0: continue
        pos = 0; first = True
        for r in runs:
            ts = r.findall(qn('w:t')); rt = ''.join(t.text or '' for t in ts)
            a, b = pos, pos + len(rt); pos = b
            if b <= k or a >= k + len(old): continue
            keep_l = rt[:max(0, k - a)]; keep_r = rt[min(len(rt), k + len(old) - a):]
            body = new if first else ''; first = False
            ts[0].text = keep_l + body + keep_r; ts[0].set(qn('xml:space'), 'preserve')
            for t in ts[1:]: t.text = ''
        return True
    raise ValueError('not found: ' + old[:50])

def rewrite(p, old, new):
    """Single-run paragraph replace (matching ignores non-breaking spaces)."""
    txt = p.text; k = txt.replace('\xa0', ' ').find(old.replace('\xa0', ' '))
    assert k >= 0, old[:50]
    r = p.runs; r[0].text = txt[:k] + new.replace('Section ', 'Section\xa0') + txt[k + len(old):]
    for x in r[1:]: x._r.getparent().remove(x._r)

def italic_runs(p, text):
    """text uses {i}..{/i} for italics."""
    for r in p.runs[1:]: r._r.getparent().remove(r._r)
    p.runs[0].text = ''
    first = True
    for part in re.split(r'(\{i\}.*?\{/i\})', text):
        if not part: continue
        it = part.startswith('{i}'); s = re.sub(r'\{/?i\}', '', part)
        r = p.runs[0] if first else p.add_run()
        if first: p.runs[0].font.italic = None
        if not first: r.font.italic = None
        r.text = s; r.font.italic = True if it else None; first = False

def clone(d, src, text, style_runs=None):
    el = copy.deepcopy(src._p)
    from docx.text.paragraph import Paragraph
    p = Paragraph(el, src._parent); italic_runs(p, text); return p

def make_table(d, header, rows, widths_first=True):
    t = d.add_table(rows=1 + len(rows), cols=len(header))
    t.style = [s for s in d.styles if s.name == 'Table'][0] if any(s.name == 'Table' for s in d.styles) else t.style
    tp = t._tbl.tblPr
    ref = d.tables[1]._tbl.tblPr
    for ch in list(tp): tp.remove(ch)
    for ch in ref: tp.append(copy.deepcopy(ch))
    for j, h in enumerate(header):
        c = t.rows[0].cells[j]; p = c.paragraphs[0]; r = p.add_run(h); r.bold = True
        p.style = 'Compact'; p.alignment = 1 if j else 0
        bd = OxmlElement('w:tcBorders'); b = OxmlElement('w:bottom')
        for k, v in (('w:val', 'single'), ('w:sz', '6'), ('w:space', '0'), ('w:color', '000000')): b.set(qn(k), v)
        bd.append(b); c._tc.get_or_add_tcPr().append(bd)
    for i, row in enumerate(rows, 1):
        for j, v in enumerate(row):
            p = t.rows[i].cells[j].paragraphs[0]; p.add_run(str(v)); p.style = 'Compact'; p.alignment = 1 if j else 0
    return t

def pct(x): return f'{100*x:.1f}'

def add_study4(d, ps):
    P = {p.text[:40]: p for p in ps}
    find = lambda start: [p for p in ps if p.text.startswith(start)][0]
    # ---------------- edits to existing paragraphs ----------------
    seg_replace(ps[2], 'rates, on a 0 to 5 scale, how strongly', 'rates how strongly')
    seg_replace(ps[2], ', although reply delays remained too long. Without platform trace data, validation relies on parametric references, so the findings are hypotheses for field testing.',
                f'. Public Bluesky and Stack Exchange records confirm a daily cycle that baselines cannot produce but show Bluesky replies about {I["med_delay"]/R[BS]["med_delay"]:.0f} times faster than simulated; the findings remain hypotheses.')
    rewrite(ps[9], ' RQ2 (decision):', ' We answer RQ1 first against assumed references (Study 1) and then against public Bluesky and Stack Exchange activity (Study 4). RQ2 (decision):')
    rewrite(ps[10], 'Without trace data from a real platform, behavioral validation is conducted against assumed reference profiles, so the findings',
            'Behavioral validation uses assumed reference profiles and public activity records from Bluesky and Stack Exchange, not calibrated traces from the target platform, so the findings')
    rewrite(find('Unless stated otherwise'), 'The simulator was implemented from the specification in Section III.',
            'The simulator was implemented from the specification in Section III. Study 4 compares the Study 1 configuration with public platform data (Section IV-F).')
    rewrite(ps[57], 'we do not claim a match to any real platform.', 'we do not claim a match to any real platform. Study 4 replaces the assumed references with public activity data.')
    rewrite(ps[87], 'The most important is the absence of empirical reference data. The behavioral comparison in Study 1 uses parametric references that we specified, so the results show that the scheduler is closer to the assumed regularities than the alternatives are, not that it is close to any real platform.',
            'The most important is the absence of calibrated trace data from the target platform. Study 1 uses parametric references that we specified, and Study 4 compares uncalibrated simulator output with public Bluesky and Stack Exchange records, so the results show that the scheduler reproduces a daily modulation that the alternatives cannot, not that it matches any real platform in level, phase, or reply speed.')
    rewrite(ps[87], 'for example using the timestamps of public posts and the reply delays of a public discussion platform. The simulator accepts such data without modification.',
            'for example using the timestamps and reply delays of the public records used in Study 4, which supplies only the first step of such an evaluation.')
    rewrite(ps[88], 'a single exponential stimulus decay is too restrictive.',
            f'a single exponential stimulus decay is too restrictive. Study 4 shows that the mismatch is large on Bluesky (median {I["med_delay"]:.2f} h against {R[BS]["med_delay"]:.2f} h), while the Q&A sites reply more slowly than the simulator ({R[WP]["med_delay"]:.1f} to {R[LA]["med_delay"]:.1f} h), so the delay scale has to be calibrated for each platform.')
    rewrite(ps[91], 'The simulator reproduces a stylized daily profile much better than homogeneous or periodic scheduling,',
            'The simulator reproduces a stylized daily profile, and the daily modulation seen in public Bluesky and Stack Exchange records, much better than homogeneous or periodic scheduling,')
    rewrite(ps[91], 'The evidence is limited by the lack of real trace data, by manual parameterization,',
            f'The evidence is limited by the lack of calibration to real trace data, by reply delays about {I["med_delay"]/R[BS]["med_delay"]:.0f} times slower than on Bluesky, by manual parameterization,')
    rewrite(ps[100], 'upon acceptance.', 'upon acceptance. The scripts that prepare the public Bluesky and Stack Exchange references and run Study 4 are included in the archive; the source datasets are cited as [25]\u2013[27].')
    # table numbering shifts: Tables VI and VII are new
    for p in ps:
        if p.text.startswith('TABLE VII\n'): p.runs[0].text = 'TABLE IX'
        elif p.text.startswith('TABLE VI\n'): p.runs[0].text = 'TABLE VIII'
    for p in d.paragraphs:
        if p.text.startswith('TABLE'): continue
        for r in p.runs:
            t0 = r.text
            t1 = re.sub(r'Table(\s|\xa0)VII\b', lambda m: 'Table' + m.group(1) + 'IX', t0)
            t1 = re.sub(r'Table(\s|\xa0)VI\b', lambda m: 'Table' + m.group(1) + 'VIII', t1)
            if t1 != t0: r.text = t1      # assigning run.text would drop drawings and other non-text content
    # ---------------- new subsection ----------------
    heading_v = find('V. DISCUSSION'); out = []
    out.append(clone(d, find('E. Sensitivity'), 'F. Study 4: Comparison With Public Platform Data (RQ1)'))
    n_bs, nd_bs = R[BS]['n'], R[BS]['n_delay']
    P1 = ('Study 1 compared the schedulers with references that we assumed. To reduce that dependence, Study 4 compares the same three schedulers with public activity records from two sources. The first is a public sample of 12.1 million posts from the Bluesky firehose [25], a microblogging platform. Its self-reported creation field contained implausible dates (for example, 1911), so we decoded creation times from the timestamp identifier embedded in each record key [26], which also gives the creation time of the parent post of each reply. '
          f'We used the four days with complete hourly coverage (November 28 and 29 and December 3 and 4, 2024; {n_bs/1e6:.1f} million posts and replies) for the hour-of-day profile and {nd_bs/1e6:.1f} million replies with a delay of 0 to 48 hours for the reply-delay distribution. '
          'The second source is the public Stack Exchange data dump [27] for three English-language question-and-answer sites (Money, Law, and Workplace). We counted questions, answers, and comments as posting events and measured the delay from a post to each comment on it, again truncated at 48 hours. These sites are not microblogs, so we treat them as an independent check on diurnal structure and not as a model of the target platform. Their timestamps were converted to US Eastern time, which is an assumption about where most of their users are.')
    out.append(clone(d, find('Several parameters were set'), P1))
    P2 = ('The simulation has a single clock, whereas Bluesky users are spread over many time zones, which flattens a UTC profile. We therefore compare diurnal structure with three measures that do not depend on phase: the relative amplitude of the first daily harmonic of the hourly profile (twice the modulus of the 24-hour Fourier component divided by the mean), the ratio of the busiest to the quietest hour, and the maximum Pearson correlation over circular shifts of the profile ({i}r{/i}*). Reply delays are compared by their median, the share within five minutes, and the Kolmogorov\u2013Smirnov statistic {i}D{/i}. '
          'The schedulers are the Study 1 configuration (800 agents, 72 simulated hours, five replications). Study 4 uses an implementation of that configuration from the specification in Section III. The intercept of the surrogate oracle, which the specification does not fix, was set so that a 24-hour run produced about 14,830 events, the figure reported in Section III-E. The implementation reproduced the two reply-delay statistics of Study 1 closely '
          f'(median {I["med_delay"]:.2f} vs. 1.39 hours; {pct(I["within5min"])}% vs. 4.0% within five minutes).')
    out.append(clone(d, ps[10], P2))
    # Table VI
    capsrc = find('TABLE V\n'); notesrc = find('Note. Adopters within 48 hours')
    def caption(num, title):
        el = copy.deepcopy(capsrc._p)
        from docx.text.paragraph import Paragraph
        p = Paragraph(el, capsrc._parent); p.runs[0].text = num; p.runs[2].text = title; return p
    out.append(caption('TABLE VI', 'ACTIVITY STATISTICS OF PUBLIC PLATFORM DATA AND SIMULATED SCHEDULERS'))
    rows = []
    def k(n): return f'{n/1e6:.1f} M' if n >= 1e6 else f'{n/1e3:.0f} k'
    for lab, nm in ((BS, 'Bluesky (UTC)'), (MO, 'Money.SE (US Eastern)'), (LA, 'Law.SE (US Eastern)'), (WP, 'Workplace.SE (US Eastern)')):
        v = R[lab]; rows.append([nm, k(v['n']), f'{v["amp"]:.2f}', f'{v["ptr"]:.1f}', f'{v["med_delay"]:.2f}', pct(v['within5min'])])
    for key, nm in (('ipp', 'IPP (simulated)'), ('hpp', 'HPP (simulated)'), ('poll', 'Polling (simulated)')):
        v = J[key]; npost = np.mean([len(r['posts']) for r in SIM[key]])
        rows.append([nm, k(npost) + ' per run', f'{v["amp"]:.2f}', f'{v["ptr"]:.1f}', f'{v["med_delay"]:.2f}', pct(v['within5min'])])
    t1 = make_table(d, ['Source', 'Posting events', 'Diurnal amplitude', 'Busiest / quietest hour', 'Median delay (h)', 'Within 5 min (%)'], rows)
    out.append(t1)
    out.append(clone(d, notesrc, 'Note. Diurnal amplitude is twice the modulus of the first Fourier harmonic of the hourly profile divided by its mean. Delays are truncated at 48 hours. The simulated rows are means over five replications.'))
    # Table VII
    out.append(caption('TABLE VII', 'SIMILARITY OF THE SIMULATED SCHEDULERS TO PUBLIC DATA'))
    rows2 = []
    for lab, nm in ((BS, 'Bluesky'), (MO, 'Money.SE'), (LA, 'Law.SE'), (WP, 'Workplace.SE')):
        rows2.append([nm] + [f'{J[s][lab]["r_shiftfree"]:.2f}' for s in ('ipp', 'hpp', 'poll')] + [f'{J[s][lab]["ks"]:.2f}' for s in ('ipp', 'hpp', 'poll')])
    t2 = make_table(d, ['Public source', 'r* IPP', 'r* HPP', 'r* Polling', 'D IPP', 'D HPP', 'D Polling'], rows2)
    out.append(t2)
    out.append(clone(d, notesrc, 'Note. r* is the maximum Pearson correlation between the hourly profiles over circular shifts; D is the Kolmogorov\u2013Smirnov statistic between reply-delay distributions truncated at 48 hours. Larger r* and smaller D indicate closer agreement.'))
    amp_q = [R[x]['amp'] for x in (MO, LA, WP)]; ptr_q = [R[x]['ptr'] for x in (MO, LA, WP)]
    rs = [J['ipp'][x]['r_shiftfree'] for x in (BS, MO, LA, WP)]; rb = [J[s][x]['r_shiftfree'] for s in ('hpp', 'poll') for x in (BS, MO, LA, WP)]
    P3 = (f'Table VI, Table VII, and Fig. 4 show the comparison. The diurnal result is mixed in the way the design leads one to expect. The IPP scheduler produced a daily modulation (relative amplitude {I["amp"]:.2f}) of about the size seen on the three US-centred Q&A sites ({min(amp_q):.2f} to {max(amp_q):.2f}) and larger than on Bluesky ({R[BS]["amp"]:.2f}), whose global user base flattens a UTC profile. The homogeneous and polling schedulers have no daily modulation by construction. Phase-free similarity was high for IPP ({{i}}r{{/i}}* = {min(rs):.2f} to {max(rs):.2f}) and low for the baselines ({min(rb):.2f} to {max(rb):.2f}). IPP also over-modulates: its busiest-to-quietest ratio of {I["ptr"]:.1f} exceeds the observed {min(ptr_q+[R[BS]["ptr"]]):.1f} to {max(ptr_q+[R[BS]["ptr"]]):.1f}. '
          f'When the profiles are compared without a shift, IPP is only weakly correlated with the Q&A sites ({{i}}r{{/i}} = {I[MO]["r_aligned"]:.2f}, {I[LA]["r_aligned"]:.2f}, and \u2212{abs(I[WP]["r_aligned"]):.2f} for Money, Law, and Workplace), because those sites peak during working hours whereas the personas peak in the evening. The evening-peak phase is therefore not supported by the Q&A data, and the UTC Bluesky profile cannot test it. The data support the existence of a daily modulation that the baselines cannot produce, not the specific shape or phase that we assumed.')
    P4 = (f'Reply delays are the clearest shortfall. On Bluesky the median delay was {R[BS]["med_delay"]:.2f} hours and {pct(R[BS]["within5min"])}% of replies came within five minutes, whereas IPP gave {I["med_delay"]:.2f} hours and {pct(I["within5min"])}%, about {I["med_delay"]/R[BS]["med_delay"]:.0f} times slower in the median and {R[BS]["within5min"]/I["within5min"]:.0f} times lower in the share of fast replies. This agrees with the shortfall found against the assumed reference in Study 1 and quantifies it on a real platform. '
          f'The Q&A sites reply much more slowly than the simulator (median {R[WP]["med_delay"]:.1f} to {R[LA]["med_delay"]:.1f} hours; {pct(R[LA]["within5min"])}% to {pct(R[WP]["within5min"])}% within five minutes), so reply speed depends strongly on the platform and cannot be fixed by one decay time or recency weight. The statistic {{i}}D{{/i}} reflects this: IPP was closer than the baselines on Bluesky ({{i}}D{{/i}} = {J["ipp"][BS]["ks"]:.2f} vs. {J["hpp"][BS]["ks"]:.2f} and {J["poll"][BS]["ks"]:.2f}) but farther on the Q&A sites ({min(J["ipp"][x]["ks"] for x in (MO,LA,WP)):.2f} to {max(J["ipp"][x]["ks"] for x in (MO,LA,WP)):.2f} vs. {min(J[s][x]["ks"] for s in ("hpp","poll") for x in (MO,LA,WP)):.2f} to {max(J[s][x]["ks"] for s in ("hpp","poll") for x in (MO,LA,WP)):.2f}), because the slower delays of the baselines happen to lie nearer the slow Q&A delays. We do not read the latter as support for the baselines.')
    P5 = ('Study 4 therefore answers RQ1 more cautiously than Study 1. Against public records the IPP scheduler reproduces a daily modulation that the alternatives cannot, but it over-modulates, its phase is untested on a single-time-zone social platform, and its reply delays are too slow for Bluesky. Because the speed comparison in Study 2 depends on the time scale of the simulator, the difference of about 1.0 hours in t50 should be read as a statement about the simulated time scale and not as a platform estimate. Neither the modulation depth nor the delay scale was calibrated to these data, and calibrating them is the next step.')
    out += [clone(d, find('On the preferential-attachment'), P3), clone(d, ps[10], P4)]
    fig = d.add_paragraph(style='Captioned Figure'); fig.alignment = 1
    fig.add_run().add_picture(HERE + 'fig4_public_data.png', width=Inches(3.45)); out.append(fig)
    out.append(clone(d, find('Fig. 3.'), 'Fig. 4. Comparison with public data. (a) Hourly share of posting events for the simulated schedulers (local clock), Bluesky (UTC), and Money.SE (US Eastern). (b) Cumulative distribution of reply delays truncated at 48 h; delays under one minute are plotted at one minute.'))
    out.append(clone(d, ps[10], P5))
    for x in out:
        el = x._p if hasattr(x, '_p') else x._tbl
        heading_v._p.addprevious(el)
    # ---------------- references ----------------
    last = find('[24]')
    for n, txt in (('[25]', 'midwestern-simulation, \u201c12.1M Bluesky posts,\u201d Hugging Face dataset, 2024. [Online]. Available: https://huggingface.co/datasets/midwestern-simulation/12.1m_bluesky_posts. Accessed: Oct. 26, 2026.'),
                   ('[26]', 'Bluesky Social PBC, \u201cAT Protocol specifications: Timestamp identifiers (TID).\u201d [Online]. Available: https://atproto.com/specs/tid. Accessed: Oct. 26, 2026.'),
                   ('[27]', 'Stack Exchange Inc., \u201cStack Exchange data dump,\u201d Internet Archive, 2024. [Online]. Available: https://archive.org/details/stackexchange. Accessed: Oct. 26, 2026.')):
        el = copy.deepcopy(last._p)
        from docx.text.paragraph import Paragraph
        p = Paragraph(el, last._parent)
        for r in p.runs[1:]: r._r.getparent().remove(r._r)
        p.runs[0].text = n + ' \t' + txt; p.runs[0].italic = None
        last._p.addnext(el); last = p
