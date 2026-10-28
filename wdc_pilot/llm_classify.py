"""Resumable LLM classification of short texts via OpenRouter.
Usage: python llm_classify.py TASK ITEMS.json OUT.jsonl   (ITEMS: list of {"id": int, "text": str})
TASK: visual_title | complement_title | ai_level"""
import sys, json, re, os, time, threading, concurrent.futures as cf
import requests
TASK, ITEMS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
MODEL = os.environ.get('CLS_MODEL', 'anthropic/claude-haiku-5.5')
CFG = {
 'visual_title': (40, "You classify job titles (any language). Return 1 if the role mainly involves PRODUCING or EDITING VISUAL CONTENT: graphic design, UI/UX or visual/web design, illustration, photography, videography/video editing, motion graphics/animation, 3D/concept art, art direction, creative design, image/video content creation. Return 0 otherwise (interior, fashion, industrial, mechanical, electrical, civil or engineering design; software/hardware engineering; marketing, sales, management, teaching, or technician roles without visual production). Output ONLY a JSON array of {\"id\":<id>,\"label\":0|1}."),
 'complement_title': (40, "You classify job titles (any language) by whether the role supplies ORGANIZATIONAL COMPLEMENTS for using generative AI in creative/visual work. Return 1 if the role is legal, compliance, privacy/data protection, AI governance/ethics or intellectual-property counsel; return 2 if the role is creative/design leadership or brand governance (creative director, art director, head of design, design lead, brand manager) that reviews and approves visual output; return 0 otherwise (e.g., financial risk, medical ethics, unrelated management). Output ONLY a JSON array of {\"id\":<id>,\"label\":0|1|2}."),
 'ai_level': (8, "Each item is a job posting for a visual or design role: title, then description. Rate how the posting treats generative AI tools (Midjourney, Stable Diffusion, DALL-E, Adobe Firefly, ChatGPT/OpenAI image or video tools, AI image/video generators, 'AI-powered' creation tools): 0 = no mention of AI tools; 1 = mentions AI tools only as a preferred skill, nice-to-have, or general company context; 2 = using generative AI tools to produce or edit visuals is a required skill or a core duty of the role. Output ONLY a JSON array of {\"id\":<id>,\"label\":0|1|2}."),
}
BATCH, SYSTEM = CFG[TASK]; WORKERS = int(os.environ.get('CLS_WORKERS', 24))
BATCH = int(os.environ.get('CLS_BATCH', BATCH))
items = json.load(open(ITEMS)); done = set()
if os.path.exists(OUT):
    for l in open(OUT): done.add(json.loads(l)['id'])
todo = [it for it in items if it['id'] not in done]; batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]
print(f'{len(items)} items, {len(done)} done, {len(batches)} batches', flush=True)
def call(b):
    payload = {'model': MODEL, 'temperature': 0, 'max_tokens': 1500, 'messages': [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': json.dumps([{'id': it['id'], 'text': it['text']} for it in b], ensure_ascii=False)}]}
    for a in range(6):
        try:
            r = requests.post('https://openrouter.ai/api/v1/chat/completions', json=payload, headers={'Authorization': 'Bearer dummy'}, timeout=180)
            if r.status_code != 200: time.sleep(2 ** a); continue
            m = re.search(r'\[.*\]', r.json()['choices'][0]['message']['content'], re.S); arr = json.loads(m.group(0))
            got = {int(x['id']): int(x['label']) for x in arr}
            if all(it['id'] in got for it in b): return [(it['id'], got[it['id']]) for it in b]
        except Exception: time.sleep(2 ** a)
    return None
lock = threading.Lock(); n = 0; fail = 0
with open(OUT, 'a') as f, cf.ThreadPoolExecutor(WORKERS) as ex:
    for res in ex.map(call, batches):
        if res is None: fail += 1; continue
        with lock:
            for i, l in res: f.write(json.dumps({'id': i, 'label': l}) + '\n')
            f.flush(); n += 1
            if n % 100 == 0: print(n, 'batches', flush=True)
print('finished; failed batches:', fail, flush=True)
