"""Build the conversation x model ('focal') panel for Study 1 from the 140k release."""
import sys, re, numpy as np, pandas as pd
sys.path.insert(0, 'src')
from leaks import first_leak, ASK, RX_ANY
from models import developer, TOP3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import MiniBatchKMeans
D = '/home/user/data'
d = pd.read_pickle(f'{D}/140k.pkl')
d = d[d.model_a != d.model_b].reset_index(drop=True)
d['dev_a'] = d.model_a.map(developer); d['dev_b'] = d.model_b.map(developer)
la = d.a_turns.map(first_leak); lb = d.b_turns.map(first_leak)
d['leak_dev_a'] = la.str[1]; d['leak_dev_b'] = lb.str[1]
d['self_a'] = d.leak_dev_a.eq(d.dev_a); d['self_b'] = d.leak_dev_b.eq(d.dev_b)
# a claimed identity that is not the model's own developer (e.g. a model claiming to be ChatGPT)
d['other_a'] = d.leak_dev_a.notna() & ~d.self_a; d['other_b'] = d.leak_dev_b.notna() & ~d.self_b
d['ask'] = d.user_turns.map(lambda ts: any(ASK.search(t or '') for t in ts))
first = d.user_turns.map(lambda ts: (ts[0] if ts else '')[:2000])
d['first_prompt'] = first
d['short_prompt'] = first.str.len() < 25
# prompt clusters (stand-in for embedding clustering): TF-IDF char n-grams -> SVD -> k-means
X = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), min_df=5, max_features=200000, sublinear_tf=True).fit_transform(first)
Z = TruncatedSVD(100, random_state=0).fit_transform(X)
Z /= np.linalg.norm(Z, axis=1, keepdims=True) + 1e-9
for k in (20, 50, 100):
    d[f'cl{k}'] = MiniBatchKMeans(k, random_state=0, n_init=3, batch_size=4096).fit_predict(Z)
np.save(f'{D}/z140.npy', Z.astype(np.float32))
d['lang'] = d.language.where(d.language.isin(d.language.value_counts().index[:12]), 'other')
ct = d.category_tag if 'category_tag' in d else None
# rule-based quality controls from conv_metadata
def meta(side):
    m = d.meta
    g = lambda f: m.map(lambda x: f(x) if isinstance(x, dict) else np.nan)
    return pd.DataFrame({
        'tok': g(lambda x: x.get(f'sum_assistant_{side}_tokens', np.nan)),
        'hdr': g(lambda x: sum((x.get(f'header_count_{side}') or {}).values())),
        'lst': g(lambda x: sum((x.get(f'list_count_{side}') or {}).values())),
        'bold': g(lambda x: sum((x.get(f'bold_count_{side}') or {}).values()))})
REF = re.compile(r"\b(i can(?:'|no)t|i(?:'m| am) (?:not able|unable)|i won't|i cannot (?:help|assist|provide)|sorry, but i)\b", re.I)
ma, mb = meta('a'), meta('b')
d['ref_a'] = d.a_turns.map(lambda ts: bool(ts) and bool(REF.search((ts[0] or '')[:300])))
d['ref_b'] = d.b_turns.map(lambda ts: bool(ts) and bool(REF.search((ts[0] or '')[:300])))
d['evaluation_order'] = d.get('order')
# session-level activity (H1b proxy): cumulative votes in this session before this one
d = d.sort_values(['user', 'ts']); d['prior_votes'] = d.groupby('user').cumcount(); d = d.sort_index()
rows = []
for side, oth in (('a', 'b'), ('b', 'a')):
    r = pd.DataFrame({'cid': d.id, 'side': side, 'model': d[f'model_{side}'], 'opp': d[f'model_{oth}'], 'dev': d[f'dev_{side}'],
        'opp_dev': d[f'dev_{oth}'], 'win': (d.winner == f'model_{side}').astype(int), 'lose': (d.winner == f'model_{oth}').astype(int),
        'tie': (d.winner == 'tie').astype(int), 'bothbad': (d.winner == 'both_bad').astype(int),
        'leak': d[f'self_{side}'].astype(int), 'opp_leak': d[f'self_{oth}'].astype(int),
        'other_claim': d[f'other_{side}'].astype(int), 'opp_other_claim': d[f'other_{oth}'].astype(int),
        'ask': d.ask.astype(int), 'short_prompt': d.short_prompt.astype(int), 'turns': d.turn, 'lang': d.lang,
        'cl20': d.cl20, 'cl50': d.cl50, 'cl100': d.cl100, 'ts': d.ts, 'user': d.user, 'prior_votes': d.prior_votes,
        'tok_diff': np.log1p((ma if side == 'a' else mb).tok) - np.log1p((mb if side == 'a' else ma).tok),
        'hdr_diff': (ma if side == 'a' else mb).hdr - (mb if side == 'a' else ma).hdr,
        'lst_diff': (ma if side == 'a' else mb).lst - (mb if side == 'a' else ma).lst,
        'bold_diff': np.log1p((ma if side == 'a' else mb).bold) - np.log1p((mb if side == 'a' else ma).bold),
        'ref': d[f'ref_{side}'].astype(int), 'opp_ref': d[f'ref_{oth}'].astype(int)})
    r['pair'] = [' | '.join(sorted(x)) for x in zip(r.model, r.opp)]
    r['opair'] = r.model + ' > ' + r.opp
    r['top3'] = r.dev.isin(TOP3).astype(int)
    rows.append(r)
P = pd.concat(rows, ignore_index=True)
for c in ['hdr_diff', 'lst_diff']: P[c] = np.sign(P[c]) * np.log1p(P[c].abs())
P.to_pickle(f'{D}/study1_panel.pkl')
d[['id', 'model_a', 'model_b', 'winner', 'self_a', 'self_b', 'other_a', 'other_b', 'leak_dev_a', 'leak_dev_b', 'ask', 'lang', 'cl50', 'ts', 'user']].to_pickle(f'{D}/conv140_flags.pkl')
print('conversations', len(d)); print('self-leak A or B', (d.self_a | d.self_b).mean(), 'one side only', (d.self_a ^ d.self_b).sum(), 'both', (d.self_a & d.self_b).sum())
print('other-claim', (d.other_a | d.other_b).sum(), 'user asked', d.ask.sum())
u = P[(P.leak == 1) & (P.opp_leak == 0) & (P.ask == 0)]
print('main-sample leaked rows', len(u)); print(u.model.value_counts().head(15))
