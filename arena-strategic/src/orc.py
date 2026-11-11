"""Minimal cached, concurrent OpenRouter client with cost accounting."""
import json, os, hashlib, time, threading, concurrent.futures as cf, urllib.request
CACHE = '/home/user/data/llm_cache.jsonl'
_lock = threading.Lock(); _cache = {}
if os.path.exists(CACHE):
    for l in open(CACHE):
        try: r = json.loads(l); _cache[r['k']] = r
        except Exception: pass
COST = {'usd': 0.0}

def _key(model, msgs, kw): return hashlib.sha256(json.dumps([model, msgs, kw], sort_keys=True).encode()).hexdigest()

def chat(model, msgs, max_tokens=200, temperature=0, retries=3, **kw):
    k = _key(model, msgs, dict(max_tokens=max_tokens, temperature=temperature, **kw))
    if k in _cache: return _cache[k]['text']
    body = dict(model=model, messages=msgs, max_tokens=max_tokens, temperature=temperature, usage={'include': True}, **kw)
    for a in range(retries):
        try:
            req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=json.dumps(body).encode(),
                                         headers={'Content-Type': 'application/json', 'Authorization': 'Bearer x'})
            resp = urllib.request.urlopen(req, timeout=60); buf = b''; t0 = time.time()
            while True:  # wall-clock deadline: OpenRouter keep-alive bytes would otherwise defeat the socket timeout
                chunk = resp.read(4096)
                if not chunk: break
                buf += chunk
                if time.time() - t0 > 90: resp.close(); raise TimeoutError('deadline')
            r = json.loads(buf)
            text = r['choices'][0]['message'].get('content') or ''
            if not text.strip(): raise ValueError('empty')
            cost = float((r.get('usage') or {}).get('cost') or 0)
            with _lock:
                COST['usd'] += cost; rec = {'k': k, 'model': model, 'text': text, 'cost': cost}; _cache[k] = rec
                open(CACHE, 'a').write(json.dumps(rec) + '\n')
            return text
        except Exception as e:
            err = e; time.sleep(2 ** a)
    return None

def pmap(fn, items, workers=16):
    with cf.ThreadPoolExecutor(workers) as ex: return list(ex.map(fn, items))

def spent(): return sum(r.get('cost', 0) for r in _cache.values())
