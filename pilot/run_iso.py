"""Classic versus structurally isomorphic (and platform) items, answered by the same simulated respondents in one booklet.
Usage: python3 run_iso.py <data_dir> <out_dir> [n_participants] [stop_usd]
Conditions are randomized between subjects per item. Architectures: demo, summary (1 draw each). Resumes if rerun."""
import sys, os, json, time, random, threading, concurrent.futures as cf
import pandas as pd, requests
D, OUT = sys.argv[1], sys.argv[2]
NP = int(sys.argv[3]) if len(sys.argv) > 3 else 400
STOP = float(sys.argv[4]) if len(sys.argv) > 4 else 25.0
MODELS = ['anthropic/claude-haiku-5.5', 'openai/gpt-5.6-luna', 'google/gemini-3.7-flash', 'x-ai/grok-4.3', 'meta-llama/llama-4-maverick']
os.makedirs(OUT, exist_ok=True); RAW = f'{OUT}/raw.jsonl'

LIK = ['I strongly favor program A', 'I favor program A', 'I slightly favor program A', 'I slightly favor program B', 'I favor program B', 'I strongly favor program B']
def cmp(txt, hi, lo, words): return [(f'{txt}', words)]
# Each item: id, phenomenon, version, conditions -> list of questions (text, options or None for numeric)
ITEMS = []
def item(i, ph, ver, conds): ITEMS.append(dict(id=i, ph=ph, ver=ver, conds=conds))

fl = lambda unit, gain, loss, gainB, lossB, intro: {
    'gain': [(f'{intro} Two alternative programs to combat it have been proposed. Assume that the exact scientific estimates of the consequences of the programs are as follows: If Program A is adopted, {gain} will be saved. If Program B is adopted, there is 1/3 probability that {gainB}, and 2/3 probability that no {unit} will be saved. Which of the two programs would you favor?', LIK)],
    'loss': [(f'{intro} Two alternative programs to combat it have been proposed. Assume that the exact scientific estimates of the consequences of the programs are as follows: If Program A is adopted, {loss} will be lost. If Program B is adopted, there is 1/3 probability that no {unit} will be lost, and 2/3 probability that {lossB}. Which of the two programs would you favor?', LIK)]}
item('frame_classic', 'framing', 'classic', fl('people', '200 people', '400 people', '600 people will be saved', 'all 600 people will be lost',
     'Imagine that the U.S. is preparing for the outbreak of an unusual disease, which is expected to kill 600 people.'))
_c = ITEMS[-1]['conds']['loss'][0]
ITEMS[-1]['conds']['loss'] = [(_c[0].replace('no people will be lost', 'nobody will die').replace('all 600 people will be lost', '600 people will die').replace('400 people will be lost', '400 people will die'), _c[1])]
item('frame_iso', 'framing', 'iso', fl('homes', '200 homes', '400 homes', 'all 600 homes will be saved', 'all 600 homes will be lost',
     'Imagine that a river is expected to flood a coastal town and destroy 600 homes.'))
def anch(q1, q2, hi, lo): return {'high': [(q1.format(hi), ['more', 'fewer']), (q2, None)], 'low': [(q1.format(lo), ['more', 'fewer']), (q2, None)]}
item('anch_africa', 'anchoring', 'classic', anch('Do you think there are more or fewer than {} African countries in the United Nations?', 'How many African countries do you think are in the United Nations?', 65, 12))
item('anch_redwood', 'anchoring', 'classic', anch('Is the tallest redwood tree in the world more or less than {} feet tall?', 'How tall do you think the tallest redwood tree in the world is? Enter a number of feet.', 1000, 85))
item('anch_unesco', 'anchoring', 'iso', anch('Do you think Italy has more or fewer than {} UNESCO World Heritage sites?', 'How many UNESCO World Heritage sites do you think Italy has?', 150, 15))
item('anch_danube', 'anchoring', 'iso', anch('Is the Danube river longer or shorter than {} kilometers?', 'How long do you think the Danube river is? Enter a number of kilometers.', 6000, 700))
def dflt(intro, on_txt, off_txt, on_opts, off_opts): return {'optout': [(f'{intro} {on_txt}', on_opts)], 'optin': [(f'{intro} {off_txt}', off_opts)]}
item('default_organ', 'defaults', 'classic', dflt('Imagine that you just moved to a new state and must get a new driver\'s license. As you complete the application, you come across the following. Please read and respond as you would if you were actually presented this choice today. We are interested in your honest response.',
     'In this state every person is considered to be an organ donor unless they choose not to be.', 'In this state every person is considered not to be an organ donor unless they choose to be.',
     ['You are therefore currently a potential donor. If this is acceptable, click here:', 'If you wish to change your status, click here:'],
     ['You are therefore currently not a potential donor. If this is acceptable, click here:', 'If you wish to change your status, click here:']))
item('default_savings', 'defaults', 'iso', dflt('You have just started a new job and are completing your benefits sign-up. The employer\'s retirement savings plan deducts 5% of each paycheck and adds a 3% employer match. Please respond as you would if you were actually presented this choice today.',
     'New employees are automatically enrolled in the plan unless they choose to leave.', 'New employees are not enrolled in the plan unless they choose to join.',
     ['You are currently enrolled in the plan. If this is acceptable, click here:', 'If you wish to leave the plan, click here:'],
     ['You are currently not enrolled in the plan. If this is acceptable, click here:', 'If you wish to join the plan, click here:']))
item('default_platform', 'defaults', 'platform', dflt('You just installed a new fitness-tracking app and are going through the setup screens. Please respond as you would if you were actually presented this choice today.',
     'The setting "Share my activity data with partner advertisers for personalized ads" is turned ON by default.', 'The setting "Share my activity data with partner advertisers for personalized ads" is turned OFF by default.',
     ['The setting is currently ON. If this is acceptable, click here:', 'If you wish to turn it off, click here:'],
     ['The setting is currently OFF. If this is acceptable, click here:', 'If you wish to turn it on, click here:']))
def decoy(intro, A, B, Dd):
    def fmt(o): return ' '.join(f'{k}: {v}.' for k, v in o.items() if k != 'name')
    def q(opts): return (f'{intro} The options are described below. ' + ' '.join(f'{o["name"]} -- {fmt(o)}' for o in opts), [o['name'] for o in opts])
    return {'binary': [q([A, B])], 'attraction': [q([A, B, Dd])]}
item('decoy_earbuds', 'decoys', 'iso', decoy('You want to buy wireless earbuds online and have narrowed the choice to the following.',
     dict(name='Pulse 3', Battery='30 hours', Noise_cancelling='Good', Price='$120'), dict(name='Aria X', Battery='40 hours', Noise_cancelling='Excellent', Price='$180'), dict(name='Pulse 2', Battery='24 hours', Noise_cancelling='Fair', Price='$120')))
item('decoy_cloud', 'decoys', 'platform', decoy('You need a cloud-storage subscription for your photos and documents and are comparing these monthly plans.',
     dict(name='Plus', Storage='1 TB', Sharing='Up to 5 people', Price='$8 per month'), dict(name='Pro', Storage='5 TB', Sharing='Up to 20 people', Price='$18 per month'), dict(name='Plus Lite', Storage='800 GB', Sharing='Up to 2 people', Price='$8 per month')))
item('decoy_course', 'decoys', 'iso', decoy('You want to learn programming through an online course and are comparing these programs.',
     dict(name='Python Bootcamp', Duration='8 weeks', Certificate='Yes', Price='$200'), dict(name='Data Science Track', Duration='14 weeks', Certificate='Yes, plus mentoring', Price='$400'), dict(name='Python Basics Plus', Duration='6 weeks', Certificate='No', Price='$200')))
def ult(intro, low, fair, acc, rej): return {'low': [(f'{intro} {low} Would you accept or reject this offer?', [acc, rej])], 'fair': [(f'{intro} {fair} Would you accept or reject this offer?', [acc, rej])]}
item('ult_classic', 'fairness', 'classic', ult('Suppose another (anonymous) person was given $5 and had to offer you a way to split the money. If you accept their offer, you each receive the amount specified. If you reject their offer, you both receive $0.',
     'They offer to keep $4 for themselves and send you $1.', 'They offer to keep $2.50 for themselves and send you $2.50.', 'I would accept the offer', 'I would reject the offer: $0 for both'))
item('ult_roommate', 'fairness', 'iso', ult('You and a roommate are due a $120 refund of your shared security deposit, and your roommate gets to propose how to divide it. If you accept the proposal, you split the refund as proposed. If you reject it, the landlord keeps the whole refund.',
     'Your roommate proposes to keep $96 and give you $24.', 'Your roommate proposes to keep $60 and give you $60.', 'I would accept the proposal', 'I would reject the proposal: nobody gets the refund'))
item('ult_platform', 'fairness', 'platform', ult('You are a video creator, and a streaming platform proposes how to divide $200 of ad revenue from your latest video. If you accept, the revenue is divided as proposed. If you reject, the video is taken down and nobody receives the revenue.',
     'The platform proposes to keep $160 and pay you $40.', 'The platform proposes to keep $100 and pay you $100.', 'I would accept the proposal', 'I would reject the proposal: nobody gets the revenue'))

def booklet(pid):
    rng = random.Random(f'{pid}-booklet'); conds = {}; qs = []
    its = ITEMS[:]; rng.shuffle(its)
    for it in its:
        c = rng.choice(list(it['conds'])); conds[it['id']] = c
        for qi, (t, o) in enumerate(it['conds'][c]):
            if o and it['ph'] == 'decoys' or o and it['ph'] in ('framing', 'defaults', 'fairness', 'anchoring'):
                o = list(o)
                if it['ph'] == 'decoys': rng.shuffle(o)
            qs.append(dict(item=it['id'], qi=qi, text=t, opts=o))
    return conds, qs

def render(qs):
    out = []; tmpl = {}
    for n, q in enumerate(qs, 1):
        if q['opts']:
            out.append(f'Q{n}:\n{q["text"]}\nQuestion Type: Single Choice\nOptions:\n' + '\n'.join(f'  {i} - {o}' for i, o in enumerate(q['opts'], 1)) + '\nAnswer: [Masked]')
            tmpl[f'Q{n}'] = {'Question Type': 'Single Choice', 'Answers': {'SelectedByPosition': 'Masked', 'SelectedText': 'Masked'}}
        else:
            out.append(f'Q{n}:\n{q["text"]}\nQuestion Type: Numeric Entry\nAnswer: [Masked]')
            tmpl[f'Q{n}'] = {'Question Type': 'Numeric Entry', 'Answers': {'Value': 'Masked'}}
    return '\n\n'.join(out) + '\n\n### Format Instructions:\nGenerate a JSON object filling in the Masked values in the following template for %d questions. For single-choice questions give the option position and text; for numeric questions give a single number.\n\n' % len(qs) + json.dumps(tmpl, indent=2)

demo = pd.read_csv(f'{D}/wave1_3_response_label.csv', low_memory=False, usecols=['pid'] + [f'QID{i}' for i in range(11, 25)])
LAB = ['Region', 'Sex assigned at birth', 'Age group', 'Education', 'Race or origin', 'US citizen', 'Marital status', 'Religion', 'Religious service attendance', 'Party identification', 'Family income', 'Political views', 'Household size', 'Employment']
demo['PID'] = 'pid_' + demo['pid'].astype(str); demo = demo.set_index('PID')
summ = pd.read_parquet(f'{D}/persona_summary.parquet').set_index('PID')['persona_summary']
HEAD = ('You are simulating one specific US survey respondent, described below. Answer every question exactly as this person would, using their own judgment and typical behavior. Do not answer as an AI assistant and do not refuse. Follow the output format instructions exactly.\n\nRespondent profile (US adult panel, 2025):\n')
def system(pid, arch):
    if arch == 'summary': return HEAD + summ[pid]
    r = demo.loc[pid]; return HEAD + '\n'.join(f'- {l}: {r[f"QID{11+i}"]}' for i, l in enumerate(LAB))

pids = sorted(set(summ.index) & set(demo.index)); random.Random(11).shuffle(pids); pids = pids[:NP]
done = set()
if os.path.exists(RAW):
    for l in open(RAW):
        try: x = json.loads(l); done.add((x['pid'], x['model'], x['arch']))
        except Exception: pass
jobs = [(pid, m, a) for pid in pids for m in MODELS for a in ('demo', 'summary') if (pid, m, a) not in done]
random.Random(5).shuffle(jobs); print('jobs', len(jobs), flush=True)
lock = threading.Lock(); spent = [0.0]; halt = threading.Event()
def call(job):
    if halt.is_set(): return
    pid, m, a = job; conds, qs = booklet(pid)
    body = dict(model=m, temperature=0.7, max_tokens=2500, usage={'include': True}, reasoning={'effort': 'low'},
                messages=[{'role': 'system', 'content': system(pid, a)}, {'role': 'user', 'content': render(qs)}])
    err = None
    for k in range(5):
        try:
            r = requests.post('https://openrouter.ai/api/v1/chat/completions', json=body, timeout=240)
            if r.status_code == 200:
                x = r.json(); u = x.get('usage', {})
                rec = dict(pid=pid, model=m, arch=a, content=x['choices'][0]['message'].get('content'), cost=u.get('cost') or 0, conds=conds, qs=qs)
                with lock:
                    open(RAW, 'a').write(json.dumps(rec) + '\n'); spent[0] += rec['cost']
                    if spent[0] >= STOP: halt.set(); print('HALT', spent[0], flush=True)
                return
            err = f'{r.status_code} {r.text[:150]}'
        except Exception as e: err = str(e)
        time.sleep(2 ** (k + 1))
    with lock: open(f'{OUT}/errors.jsonl', 'a').write(json.dumps(dict(key=list(job), err=err)) + '\n')
with cf.ThreadPoolExecutor(48) as ex: list(ex.map(call, jobs))
print(f'FINISHED spent ${spent[0]:.2f}', flush=True)
