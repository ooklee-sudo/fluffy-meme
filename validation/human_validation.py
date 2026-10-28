"""Agreement between LLM visual-content scores and the human-coded sample (199 O*NET tasks).
Sources: data/human_creation_sample_filled_coderB.xlsx (200 rows; the 'coder B' column was filled by an AI rater, not a human, per the session that produced it)
and data/coderA_vs_coderB_disagreements.csv (rows where coder A (human) and B differ). Coder A's scores are reconstructed: A = B on rows not in the
disagreement file (row 141 is blank for A and excluded). The reconstruction reproduces the reported distribution (81/64/54) and kappa (0.301, weighted 0.494).
Usage: python human_validation.py SCORES_A_JSONL SCORES_B_JSONL OUT_PREFIX   (LLM score files from reproduction/score_tasks.py)"""
import sys, csv, json, openpyxl, numpy as np, pandas as pd
rows = list(openpyxl.load_workbook('data/human_creation_sample_filled_coderB.xlsx', data_only=True)['coding'].iter_rows(min_row=2, values_only=True))
B = pd.DataFrame(rows, columns=['row', 'occupation', 'task', 'coder_B_ai', 'notes']); B['row'] = B.row.astype(int); B['coder_B_ai'] = B.coder_B_ai.astype(int)
dis = pd.DataFrame(list(csv.DictReader(open('data/coderA_vs_coderB_disagreements.csv'))))[['row', 'coder_A']]; dis['row'] = dis.row.astype(int); dis['coder_A'] = dis.coder_A.astype(int)
m = B.merge(dis, on='row', how='left'); m['coder_A_human'] = m.coder_A.where(m.coder_A.notna(), m.coder_B_ai); m = m[m.row != 141].copy(); m['coder_A_human'] = m.coder_A_human.astype(int)
def load(p): return pd.DataFrame([json.loads(l) for l in open(p)]).drop_duplicates('task').set_index('task')
H, L = load(sys.argv[1]), load(sys.argv[2]); m['task_s'] = m.task.str.strip()
m['llm_a'] = H.loc[m.task_s, 'visual'].values; m['llm_b'] = L.loc[m.task_s, 'visual'].values
def stats(a, b, cats=(0, 1, 2)):
    a, b = np.asarray(a), np.asarray(b); K = len(cats); M = np.zeros((K, K))
    for i, x in enumerate(cats):
        for j, y in enumerate(cats): M[i, j] = ((a == x) & (b == y)).sum()
    n = M.sum(); po = np.trace(M) / n; pa, pb = M.sum(1) / n, M.sum(0) / n; pe = (pa * pb).sum(); k = (po - pe) / (1 - pe)
    w = 1 - ((np.arange(K)[:, None] - np.arange(K)[None, :]) ** 2) / (K - 1) ** 2; pw = (w * M).sum() / n; pwe = (w * np.outer(pa, pb)).sum(); wk = (pw - pwe) / (1 - pwe)
    pi = (pa + pb) / 2; ac = (po - (pi * (1 - pi)).sum() / (K - 1)) / (1 - (pi * (1 - pi)).sum() / (K - 1))
    return {'n': int(n), 'raw_agreement': float(po), 'cohen_kappa': float(k), 'weighted_kappa_quadratic': float(wk), 'gwet_ac1': float(ac), 'confusion_rows_first': M.astype(int).tolist()}
pairs = {'human_A_vs_ai_B': ('coder_A_human', 'coder_B_ai'), 'llm_haiku_vs_human_A': ('llm_a', 'coder_A_human'), 'llm_luna_vs_human_A': ('llm_b', 'coder_A_human'),
         'llm_haiku_vs_ai_B': ('llm_a', 'coder_B_ai'), 'llm_haiku_vs_llm_luna': ('llm_a', 'llm_b')}
out = {k: stats(m[a], m[b]) for k, (a, b) in pairs.items()}
out['binary_any_visual'] = {k: stats((m[a] > 0).astype(int), (m[b] > 0).astype(int), (0, 1)) for k, (a, b) in pairs.items() if k in ('human_A_vs_ai_B', 'llm_haiku_vs_human_A', 'llm_luna_vs_human_A')}
out['distribution'] = {c: m[c].value_counts().sort_index().to_dict() for c in ('coder_A_human', 'coder_B_ai', 'llm_a', 'llm_b')}
json.dump(out, open(sys.argv[3] + '_results.json', 'w'), indent=1, default=int)
m[['row', 'occupation', 'task', 'coder_A_human', 'coder_B_ai', 'llm_a', 'llm_b']].rename(columns={'llm_a': 'llm_haiku', 'llm_b': 'llm_luna'}).to_csv(sys.argv[3] + '_scores.csv', index=False)
for k in pairs: print(k, {x: round(v, 3) for x, v in out[k].items() if x not in ('confusion_rows_first', 'n')}, 'n', out[k]['n'])
