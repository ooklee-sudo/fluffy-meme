"""Weekly OpenRouter snapshot: model catalogue with prices, per-provider endpoint prices, and weekly usage.

Run from the repository root:  python3 collect.py
Writes snapshots/YYYY-MM-DD/{models.json, endpoints.json, usage_week.json, meta.json}.
Usage data: Source: OpenRouter (openrouter.ai/rankings), as of {as_of}. Licensed CC BY 4.0.
The rankings dataset needs an OpenRouter API key; in the cloud environment it is injected by the proxy
(Network secrets). Locally, set OPENROUTER_API_KEY.
"""
import json, os, time, datetime as dt, urllib.request

UA = {'User-Agent': 'research-snapshot/1.0'}
KEY = os.environ.get('OPENROUTER_API_KEY')
if KEY:
    UA['Authorization'] = f'Bearer {KEY}'


def get(url, tries=4):
    for a in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90))
        except Exception as e:
            err = e
            time.sleep(5 * (a + 1))
    raise err


today = dt.date.today()
out = f'snapshots/{today.isoformat()}'
os.makedirs(out, exist_ok=True)

models = get('https://openrouter.ai/api/v1/models')
json.dump(models, open(f'{out}/models.json', 'w'))

# Per-provider endpoint prices for text models (one call per model; ~450 calls, paced)
eps = {}
for m in models['data']:
    mid = m['id']
    if mid.startswith('~') or ':' in mid:
        continue
    try:
        eps[mid] = get(f'https://openrouter.ai/api/v1/models/{mid}/endpoints')['data']
    except Exception as e:
        eps[mid] = {'error': str(e)}
    time.sleep(0.4)
json.dump(eps, open(f'{out}/endpoints.json', 'w'))

# Usage: last four complete weeks by model (top 50 + 'other'), weekly grain
end = today - dt.timedelta(days=1)
start = end - dt.timedelta(days=34)
usage = get(f'https://openrouter.ai/api/v1/datasets/rankings-daily?start_date={start}&end_date={end}&period=week')
json.dump(usage, open(f'{out}/usage_week.json', 'w'))
daily = get(f'https://openrouter.ai/api/v1/datasets/rankings-daily?start_date={end - dt.timedelta(days=6)}&end_date={end}&period=day')
json.dump(daily, open(f'{out}/usage_day.json', 'w'))

meta = dict(collected_utc=dt.datetime.now(dt.timezone.utc).isoformat(), n_models=len(models['data']), n_endpoint_models=len(eps),
            usage_rows=len(usage.get('data', [])), usage_as_of=usage.get('meta', {}).get('as_of'),
            source='Source: OpenRouter (openrouter.ai/rankings). CC BY 4.0.')
json.dump(meta, open(f'{out}/meta.json', 'w'), indent=1)
print(json.dumps(meta))
