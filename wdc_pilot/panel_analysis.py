"""Employer-level panel from WDC JobPosting crawls and H3-style diagnostics.
Usage: python panel_analysis.py PANEL_DIR VIS_TITLE_LABELS.jsonl VIS_TITLE_ITEMS.json COMP_LABELS.jsonl COMP_ITEMS.json AI_LABELS.jsonl AI_ITEMS.json OUT.json
Inputs are the per-part aggregates/candidates from build_panel.py and the LLM labels from llm_classify.py."""
import sys, glob, json, re
import numpy as np, pandas as pd
import statsmodels.api as sm
P, VL, VI, CL, CI, AL, AI, OUT = sys.argv[1:9]
def labels(lab, items):
    L = {json.loads(l)['id']: json.loads(l)['label'] for l in open(lab)}
    return {it['text']: L.get(it['id']) for it in json.load(open(items))}
vis_t = labels(VL, VI); comp_t = labels(CL, CI)
agg, cand = [], []
for f in glob.glob(f'{P}/*_agg.pkl'):
    d = pd.read_pickle(f); d['crawl'] = re.search(r'(\d{4})-12', f).group(1); agg.append(d)
for f in glob.glob(f'{P}/*_cand.pkl'):
    d = pd.read_pickle(f); d['crawl'] = re.search(r'(\d{4})-12', f).group(1); cand.append(d)
A = pd.concat(agg); C = pd.concat(cand)
A = A.groupby(['crawl', 'org_key'], as_index=False).agg(n_total=('n_total', 'sum'), n_genai=('n_genai', 'sum'), host=('host', 'first'), org_name=('org_name', 'first'))
C['tl'] = C.title.str.lower().str.strip()
V = C[C.kind == 'visual'].copy(); V['is_visual'] = V.tl.map(vis_t).fillna(0).astype(int)
K = C[C.kind == 'comp'].copy(); K['cls'] = K.tl.map(comp_t).fillna(0).astype(int)
ai = {}
for l in open(AL):
    d = json.loads(l); ai[d['id']] = d['label']
ai_items = json.load(open(AI)); ai_key = {(it['crawl'], it['org_key'], it['tl']): ai.get(it['id']) for it in ai_items}
V['ai_level'] = [ai_key.get((r.crawl, r.org_key, r.tl)) for r in V.itertuples()]
Vv = V[V.is_visual == 1]
vc = Vv.groupby(['crawl', 'org_key']).agg(n_vis=('title', 'size'), n_vis_ai1=('ai_level', lambda s: int((s.fillna(0) >= 1).sum())), n_vis_ai2=('ai_level', lambda s: int((s.fillna(0) >= 2).sum()))).reset_index()
cc = K.groupby(['crawl', 'org_key']).agg(n_comp_legal=('cls', lambda s: int((s == 1).sum())), n_comp_lead=('cls', lambda s: int((s == 2).sum()))).reset_index()
O = A.merge(vc, how='left', on=['crawl', 'org_key']).merge(cc, how='left', on=['crawl', 'org_key']).fillna({'n_vis': 0, 'n_vis_ai1': 0, 'n_vis_ai2': 0, 'n_comp_legal': 0, 'n_comp_lead': 0})
O.to_pickle(OUT.replace('.json', '_orgs.pkl'))
R = {'orgs_by_crawl': O.groupby('crawl').org_key.nunique().to_dict(), 'postings_by_crawl': O.groupby('crawl').n_total.sum().astype(int).to_dict(),
     'visual_postings_by_crawl': O.groupby('crawl').n_vis.sum().astype(int).to_dict(),
     'orgs_with_visual_by_crawl': O[O.n_vis > 0].groupby('crawl').org_key.nunique().to_dict(),
     'visual_postings_with_ai_ge1_by_crawl': O.groupby('crawl').n_vis_ai1.sum().astype(int).to_dict(), 'visual_postings_with_ai_ge2_by_crawl': O.groupby('crawl').n_vis_ai2.sum().astype(int).to_dict()}
# ---- 2024 cross-section: reassignment proxy among acquirers, by complements ----
c24 = O[(O.crawl == '2024')].copy()
c24['acq'] = (c24.n_genai > 0).astype(int); c24['comp'] = ((c24.n_comp_legal + c24.n_comp_lead) > 0).astype(int)
c24['reassign'] = (c24.n_vis_ai1 > 0).astype(int); c24['log_n'] = np.log(c24.n_total)
v24 = c24[c24.n_vis > 0]
R['cells_2024_visual_employers'] = {f'acq={a},comp={c}': {'orgs': int(((v24.acq == a) & (v24.comp == c)).sum()), 'with_ai_in_visual_posting': int(((v24.acq == a) & (v24.comp == c) & (v24.reassign == 1)).sum())} for a in (0, 1) for c in (0, 1)}
if (v24.acq == 1).sum() > 30:
    a24 = v24[v24.acq == 1]
    m = sm.Logit(a24.reassign, sm.add_constant(a24[['comp', 'log_n']])).fit(disp=0, cov_type='HC1')
    R['h3a_logit_reassign_on_complements_among_acquirers'] = {'n': int(len(a24)), 'coef_comp': float(m.params['comp']), 'se_comp': float(m.bse['comp']), 'p_comp': float(m.pvalues['comp']), 'coef_log_n': float(m.params['log_n'])}
# ---- panel: visual share change 2022 -> 2024 ----
w = O.pivot_table(index='org_key', columns='crawl', values=['n_total', 'n_vis', 'n_genai', 'n_comp_legal', 'n_comp_lead'], aggfunc='sum')
w.columns = [f'{a}_{b}' for a, b in w.columns]
pn = w.dropna(subset=['n_total_2022', 'n_total_2024']).copy()
pn = pn[(pn.n_total_2022 >= 3) & (pn.n_total_2024 >= 3)]
pn['vs22'] = pn.n_vis_2022 / pn.n_total_2022; pn['vs24'] = pn.n_vis_2024 / pn.n_total_2024; pn['d_vs'] = (pn.vs24 - pn.vs22) * 100
pn['acq'] = (pn.n_genai_2024 > 0).astype(int); pn['comp'] = ((pn.n_comp_legal_2024 + pn.n_comp_lead_2024) > 0).astype(int); pn['log_n22'] = np.log(pn.n_total_2022)
R['panel_orgs_in_2022_and_2024_min3_postings'] = int(len(pn)); R['panel_orgs_with_visual_in_2022'] = int((pn.n_vis_2022 > 0).sum())
R['panel_cells'] = {f'acq={a},comp={c}': {'orgs': int(((pn.acq == a) & (pn.comp == c)).sum()), 'orgs_with_visual_2022': int(((pn.acq == a) & (pn.comp == c) & (pn.n_vis_2022 > 0)).sum())} for a in (0, 1) for c in (0, 1)}
pn['acq_x_comp'] = pn.acq * pn.comp
m = sm.OLS(pn.d_vs, sm.add_constant(pn[['acq', 'comp', 'acq_x_comp', 'log_n22']])).fit(cov_type='HC1')
R['h3b_ols_change_in_visual_share_pp'] = {k: {'b': float(m.params[k]), 'se': float(m.bse[k]), 'p': float(m.pvalues[k])} for k in ('acq', 'comp', 'acq_x_comp', 'log_n22')}
sub = pn[pn.n_vis_2022 > 0]
if len(sub) > 30:
    m2 = sm.OLS(sub.d_vs, sm.add_constant(sub[['acq', 'comp', 'acq_x_comp', 'log_n22']])).fit(cov_type='HC1')
    R['h3b_ols_among_orgs_with_visual_2022'] = {'n': int(len(sub)), **{k: {'b': float(m2.params[k]), 'se': float(m2.bse[k]), 'p': float(m2.pvalues[k])} for k in ('acq', 'comp', 'acq_x_comp')}}
json.dump(R, open(OUT, 'w'), indent=1, default=float); print(json.dumps(R, indent=1, default=float))
