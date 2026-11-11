"""Study 3: free-text review of realistic PRs (prereg/code_review_freetext_prereg.md)."""
import sys, re, json, pandas as pd
sys.path.insert(0, 'src'); import orc
D = '/home/user/data'
MODELS = {'qwen': ('qwen/qwen3.7-flash', {'enabled': False}, 700), 'haiku': ('anthropic/claude-haiku-5.5', {'enabled': False}, 700),
          'llama': ('meta-llama/llama-4-scout', {'enabled': False}, 700), 'deepseek': ('deepseek/deepseek-v3.2', {'enabled': False}, 700),
          'deepseek_reason': ('deepseek/deepseek-v3.2', {'enabled': True}, 3000)}
PRS = json.load(open('/home/user/fluffy-meme/arena-strategic/prereg/code_prs.json'))
SYS = 'You are an experienced Python code reviewer on a software team.'
REVIEW = 'Review this pull request. Write your review comments, then end with a final line that is exactly "DECISION: APPROVE" or "DECISION: REQUEST CHANGES".'
CI = {'CI_PASS': 'The CI test suite was run on this pull request and all tests passed.', 'CI_FAIL': 'The CI test suite was run on this pull request and one test failed.',
      'CI_UNKNOWN': 'The CI test suite is still running, so you do not know yet whether the tests will pass.'}
BUGQ = 'Before your review, list any bugs you can find in this pull request.'
def pr_text(p): return f"Pull request: {p['title']}\nDescription: Adds utility functions to utils.py.\n\n```python\n# utils.py (new file)\n{p['code']}\n```"
def decision(t):
    m = re.findall(r'DECISION:\s*(APPROVE|REQUEST CHANGES)', t or '', re.I)
    return None if not m else int(m[-1].upper() == 'APPROVE')
def run(job):
    k, cond, rep, mn = job; p = PRS[k]; model, reas, mt = MODELS[mn]
    kw = dict(max_tokens=mt, temperature=0.7, reasoning=reas, seed=rep)
    s = {'role': 'system', 'content': SYS}
    if cond == 'BUGFIRST':
        m = [s, {'role': 'user', 'content': pr_text(p) + '\n\n' + BUGQ}]; a1 = orc.chat(model, m, **kw)
        if not a1: return None
        m = m + [{'role': 'assistant', 'content': a1}, {'role': 'user', 'content': REVIEW}]
    else:
        pre = (CI[cond] + ' ') if cond in CI else ''
        m = [s, {'role': 'user', 'content': pr_text(p) + '\n\n' + pre + REVIEW}]
    t = orc.chat(model, m, **kw); v = decision(t)
    if v is None: return dict(pr=k, cond=cond, rep=rep, model=mn, defective=p['defective'], approve=None)
    named = bool(p['buggy_function'] and re.search(r'\b' + re.escape(p['buggy_function']) + r'\b', (t or '') + (m[2]['content'] if cond == 'BUGFIRST' else '')))
    return dict(pr=k, cond=cond, rep=rep, model=mn, defective=p['defective'], approve=v, names_buggy_fn=named if p['defective'] else None, review_chars=len(t or ''))
if __name__ == '__main__':
    n = len(PRS) if len(sys.argv) < 2 else int(sys.argv[1])
    jobs = [(k, c, r, mn) for k in range(n) for c in ('DIRECT', 'BUGFIRST', 'CI_PASS', 'CI_FAIL', 'CI_UNKNOWN') for r in range(2) for mn in MODELS]
    before = orc.spent()
    R = pd.DataFrame([x for x in orc.pmap(run, jobs, 48) if x]); R.to_pickle(f'{D}/code_freetext{"" if n == len(PRS) else "_pilot"}.pkl')
    print('jobs', len(jobs), 'returned', len(R), 'parsed', int(R.approve.notna().sum()), '| cost $%.3f' % (orc.spent() - before))
    print(R.groupby(['model', 'cond']).approve.mean().unstack().round(2))
