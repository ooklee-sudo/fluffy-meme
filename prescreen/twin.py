"""Ask LLM twins (no-persona arm, as in the paper's C2) for click probabilities per headline."""
import sys, json, os, random, re, asyncio, pandas as pd, httpx
arms_csv, out_jsonl, n_tests, draws = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
models = sys.argv[5].split(',')
SYS = "You are a typical adult in the United States who uses social media."
USER = ("You are scrolling through your social media news feed and see the following versions of the same "
        "article promoted by a media site. Each version would be shown to different readers. For each version, "
        "estimate the probability (0 to 100) that YOU would click on it if it appeared in your feed. Reply with "
        "only a JSON object mapping each letter to a number, for example {\"A\": 12, \"B\": 30}.\n")
a = pd.read_csv(arms_csv)
ids = sorted(a.clickability_test_id.unique())
random.Random(2026).shuffle(ids)
ids = ids[:n_tests]
done = set()
if os.path.exists(out_jsonl):
    for l in open(out_jsonl):
        r = json.loads(l); done.add((r['test'], r['model'], r['draw']))
jobs = [(t, m, k) for t in ids for m in models for k in range(draws) if (t, m, k) not in done]
print('jobs', len(jobs), flush=True)
sem = asyncio.Semaphore(32)

async def one(cli, t, m, k):
    g = a[a.clickability_test_id == t].reset_index(drop=True)
    order = list(range(len(g))); random.Random(f'{t}{m}{k}').shuffle(order)
    L = 'ABCDEFGH'
    body = USER + '\n'.join(f"{L[i]}. {g.headline[j]}" for i, j in enumerate(order))
    payload = {"model": m, "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": body}],
               "temperature": 0.7, "max_tokens": 3000, "reasoning": {"effort": "low"}, "usage": {"include": True}}
    async with sem:
        for att in range(4):
            try:
                r = await cli.post("https://openrouter.ai/api/v1/chat/completions", json=payload, timeout=120)
                j = r.json(); txt = j['choices'][0]['message']['content'] or ''
                obj = json.loads(re.search(r'\{.*\}', txt, re.S).group(0))
                pred = {g.headline[j2]: float(obj[L[i]]) for i, j2 in enumerate(order)}
                return dict(test=t, model=m, draw=k, pred=pred, cost=j.get('usage', {}).get('cost'))
            except Exception as e:
                err = repr(e)[:200]; await asyncio.sleep(2 ** att)
        return dict(test=t, model=m, draw=k, pred=None, err=err)

async def main():
    async with httpx.AsyncClient(headers={"Authorization": "Bearer dummy"}) as cli:
        with open(out_jsonl, 'a') as f:
            for c in asyncio.as_completed([one(cli, *j) for j in jobs]):
                r = await c; f.write(json.dumps(r) + '\n'); f.flush()
asyncio.run(main())
