"""Download the public inputs used by reproduce_tables.py into DATA_DIR.
Usage: python fetch_data.py DATA_DIR
Sources: Eurostat jvs_a_isco3_r1 (online job adverts by ISCO-08 3-digit, experimental), Eurostat isoc_eb_ai,
O*NET 29.1 text database, O*NET ESCO->O*NET-SOC 2019 crosswalk."""
import sys, os, json, zipfile, io, requests, pandas as pd
D = sys.argv[1]; os.makedirs(D, exist_ok=True)
EU = 'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'
def get(url, t=300): 
    r = requests.get(url, timeout=t); r.raise_for_status(); return r
def jsonstat(d):
    ids, sizes = d['id'], d['size']; cats = {k: list(d['dimension'][k]['category']['index']) for k in ids}; rows = []
    for flat, v in d['value'].items():
        flat = int(flat); idx = []
        for s in reversed(sizes): idx.append(flat % s); flat //= s
        rows.append({k: cats[k][i] for k, i in zip(ids, idx[::-1])} | {'v': v})
    return pd.DataFrame(rows)
oja = get(EU + 'jvs_a_isco3_r1?format=JSON&lang=en').json()
json.dump(oja, open(f'{D}/oja.json', 'w')); jsonstat(oja).to_pickle(f'{D}/oja.pkl')
ai = get(EU + 'isoc_eb_ai?format=JSON&lang=en').json(); json.dump(ai, open(f'{D}/ai.json', 'w'))
zipfile.ZipFile(io.BytesIO(get('https://www.onetcenter.org/dl_files/database/db_29_1_text.zip').content)).extractall(f'{D}/onet')
open(f'{D}/esco_onet.xlsx', 'wb').write(get('https://www.onetcenter.org/crosswalks/esco/ESCO_to_ONET-SOC.xlsx').content)
print('ok')
