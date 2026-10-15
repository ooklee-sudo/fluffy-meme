"""Classifiers S, Z, L of ANALYSIS_PLAN_LATENT.md, fixed before the first run.
Usage (from study3/):  python classify.py S|Z|L [--max-seconds N]   (resumable; appends to out_latent/<name>.csv)
S: cardiffnlp/twitter-roberta-base-sentiment-latest @ 3216a57f2a0d9c45a2e6c20157c20c49fb4bf9c7; neg = argmax is 'negative'.
Z: MoritzLaurer/deberta-v3-base-zeroshot-v2.0 @ 8e7e5af5983a0ddb1a5b45a38b129ab69e2258e8; one hypothesis per outcome,
   label = 1 if P(entailment) >= 0.5.
L: keyword rule for defect (list below), case-insensitive, whole-phrase match; no negation handling by design.
Input: sample_text.jsonl (rid, text). Texts are truncated to 512 tokens."""
import sys, os, re, time, json, csv
import pandas as pd
KIND = sys.argv[1]; MAXS = float(sys.argv[sys.argv.index('--max-seconds') + 1]) if '--max-seconds' in sys.argv else 1e9
S_MODEL, S_REV = 'cardiffnlp/twitter-roberta-base-sentiment-latest', '3216a57f2a0d9c45a2e6c20157c20c49fb4bf9c7'
Z_MODEL, Z_REV = 'MoritzLaurer/deberta-v3-xsmall-zeroshot-v1.1-all-33', '262ae02f29173eec1c250f90804dc7edc677dcff'   # Amendment 1
HYP = {'defect': 'The reviewer reports that the product was defective, broken, damaged, or stopped working.',
       'neg': 'The reviewer is dissatisfied with the product.',
       'perfpos': 'The reviewer praises how well the product works.'}
KEYWORDS = ['broke', 'broken', 'breaks', 'stopped working', 'quit working', 'stop working', "doesn't work", 'does not work',
            "didn't work", 'did not work', 'not working', "won't work", 'defective', 'defect', 'malfunction', 'malfunctioned',
            'failed', 'fails', 'failure', 'damaged', 'dented', 'cracked', 'leak', 'leaks', 'leaking', 'leaked', 'wrong item',
            'wrong part', 'missing parts', 'missing part', 'dead on arrival', 'doa', 'died', 'burned out', 'burnt out',
            'shorted', 'faulty', 'not as described', 'wrong size']
os.makedirs('out_latent', exist_ok=True); OUT = f'out_latent/{KIND}.csv'
T = pd.read_json('sample_text.jsonl', lines=True)
done = set(pd.read_csv(OUT).rid) if os.path.exists(OUT) else set()
if KIND == 'Z':   # fixed random subsample: 300 reviews per cell (Amendment 1) (ANALYSIS_PLAN_LATENT.md)
    M = pd.read_csv('sample_meta.csv'); M['cell'] = 2 * M.treated + M.post
    keep = M.groupby('cell', group_keys=False).apply(lambda g: g.sample(300, random_state=20261015)).rid
    T = T[T.rid.isin(set(keep))]
todo = T[~T.rid.isin(done)]
new = not os.path.exists(OUT); f = open(OUT, 'a', newline=''); w = csv.writer(f)
t0 = time.time()
if KIND == 'L':
    rx = re.compile(r'\b(' + '|'.join(re.escape(k) for k in KEYWORDS) + r')\b', re.I)
    if new: w.writerow(['rid', 'defect'])
    for r in todo.itertuples(): w.writerow([r.rid, int(bool(rx.search(str(r.text))))])
else:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    torch.set_num_threads(4)
    name, rev = (S_MODEL, S_REV) if KIND == 'S' else (Z_MODEL, Z_REV)
    tok = AutoTokenizer.from_pretrained(name, revision=rev); mdl = AutoModelForSequenceClassification.from_pretrained(name, revision=rev).eval()
    lab = {v.lower(): k for k, v in mdl.config.id2label.items()}
    if new: w.writerow(['rid', 'neg', 'p_neg'] if KIND == 'S' else ['rid'] + [f'{h}' for h in HYP] + [f'p_{h}' for h in HYP])
    B = 32
    for i in range(0, len(todo), B):
        if time.time() - t0 > MAXS: break
        c = todo.iloc[i:i + B]; texts = [str(x) for x in c.text]
        with torch.no_grad():
            if KIND == 'S':
                enc = tok(texts, truncation=True, max_length=512, padding=True, return_tensors='pt')
                pr = mdl(**enc).logits.softmax(-1); ineg = lab['negative']
                for rid, row in zip(c.rid, pr): w.writerow([rid, int(row.argmax().item() == ineg), round(row[ineg].item(), 4)])
            else:
                ient = lab['entailment']; probs = {}
                for h, hyp in HYP.items():
                    enc = tok(texts, [hyp] * len(texts), truncation='only_first', max_length=256, padding=True, return_tensors='pt')
                    probs[h] = mdl(**enc).logits.softmax(-1)[:, ient].tolist()
                for j, rid in enumerate(c.rid):
                    w.writerow([rid] + [int(probs[h][j] >= 0.5) for h in HYP] + [round(probs[h][j], 4) for h in HYP])
        f.flush()
f.close()
n = len(pd.read_csv(OUT)); print(KIND, 'rows', n, 'of', len(T), 'seconds', round(time.time() - t0))
