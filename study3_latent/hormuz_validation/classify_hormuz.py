"""Classifiers K (keyword rules) and Z (zero-shot NLI) for the 191 Hormuz posts (ANALYSIS_PLAN_LATENT_VALIDATION.md).
Run from misq_note/hf:  python latent/classify_hormuz.py <truth_archive.json>   -> latent/hormuz_KZ.csv"""
import sys, re, json, html
import pandas as pd
ESC_RX = re.compile(r"\b(strik\w*|attack\w*|bomb\w*|destroy\w*|obliterat\w*|annihilat\w*|wipe[sd]? out|blow\w* up|kill\w*|ultimatum\w*|"
                    r"very hard|retaliat\w*|blockade\w*|sanction\w*|military action|consequences|threat\w*)\b", re.I)
DEESC_RX = re.compile(r"\b(ceasefire|cease-fire|cease fire|truce|deal|agreement|agreed|talks|negotiat\w*|pause\w*|postpon\w*|"
                      r"hold(?:ing)? off|reopen\w*|peace\w*|de-?escalat\w*|progress|productive|lift\w*)\b", re.I)
Z_MODEL, Z_REV = 'MoritzLaurer/deberta-v3-xsmall-zeroshot-v1.1-all-33', '262ae02f29173eec1c250f90804dc7edc677dcff'
HYP = {'esc': 'The post threatens, warns of, or announces military action or pressure against Iran.',
       'deesc': 'The post announces a pause, ceasefire, deal, talks, or easing of the conflict with Iran.'}
ids = pd.read_csv('human_labels_191.csv', dtype={'id': str}).id
a = pd.DataFrame(json.load(open(sys.argv[1])))[['id', 'content']]; a['id'] = a.id.astype(str)
D = a[a.id.isin(set(ids))].copy()
D['text'] = D.content.fillna('').map(lambda s: html.unescape(re.sub(r'<[^>]+>', ' ', s))).str.replace(r'\s+', ' ', regex=True).str.strip()
D['K_esc'] = D.text.map(lambda s: int(bool(ESC_RX.search(s)))); D['K_deesc'] = D.text.map(lambda s: int(bool(DEESC_RX.search(s))))
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
torch.set_num_threads(4)
tok = AutoTokenizer.from_pretrained(Z_MODEL, revision=Z_REV); mdl = AutoModelForSequenceClassification.from_pretrained(Z_MODEL, revision=Z_REV).eval()
ient = {v.lower(): k for k, v in mdl.config.id2label.items()}['entailment']
texts = D.text.tolist()
for h, hyp in HYP.items():
    ps = []
    for i in range(0, len(texts), 16):
        enc = tok(texts[i:i + 16], [hyp] * len(texts[i:i + 16]), truncation='only_first', max_length=256, padding=True, return_tensors='pt')
        with torch.no_grad(): ps += mdl(**enc).logits.softmax(-1)[:, ient].tolist()
    D[f'p_Z_{h}'] = ps; D[f'Z_{h}'] = (D[f'p_Z_{h}'] >= 0.5).astype(int)
D[['id', 'K_esc', 'K_deesc', 'Z_esc', 'Z_deesc', 'p_Z_esc', 'p_Z_deesc']].to_csv('latent/hormuz_KZ.csv', index=False); print('rows', len(D))
