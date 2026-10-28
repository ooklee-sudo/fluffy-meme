"""Prepare Canadian job-vacancy panel (StatCan 14-10-0444, Canada total, NOC unit groups) and NOC main-duty statements.
Usage: python canada_prep.py DATA_DIR"""
import sys, re, json, pandas as pd
D = sys.argv[1]
v = pd.read_csv(f'{D}/cad_jv.csv', header=None, quotechar='"', usecols=[0, 3, 11], names=['ref', 'noc', 'val'])
v['code'] = v.noc.str.extract(r'\[(\d{5})\]')[0]
v = v[v.code.notna()].copy(); v['val'] = pd.to_numeric(v.val, errors='coerce')
v['year'] = v.ref.str[:4].astype(int); v['q'] = (v.ref.str[5:7].astype(int) - 1) // 3 + 1
v.to_pickle(f'{D}/cad_panel.pkl')
base = v[v.year == 2022].pivot_table(index='code', columns='q', values='val')
print('unit groups with data:', v.code.nunique(), ' with 4 base quarters:', base.dropna().shape[0],
      ' base-year total >= 1000:', (base.dropna().sum(axis=1) >= 1000).sum())
e = pd.read_csv(f'{D}/noc_elements.csv', encoding='utf-8-sig')
e = e[(e['Element Type Label English'] == 'Main duties') & (e.Level == 5)]
e = e.rename(columns={'Code - NOC 2021 V1.0': 'code', 'Element Description English': 'duty'})
e['code'] = e.code.astype(str).str.zfill(5)
e[['code', 'duty']].to_pickle(f'{D}/noc_duties.pkl')
keep = set(base.dropna()[base.dropna().sum(axis=1) >= 1000].index)   # all 4 base quarters observed, base-year total >= 1,000
texts = sorted(set(e[e.code.isin(keep)].duty.str.strip()))
json.dump(texts, open(f'{D}/noc_duty_texts.json', 'w')); print('duty statements to score:', len(texts))
