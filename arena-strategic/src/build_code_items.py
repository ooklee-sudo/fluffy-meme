"""Build correct and verified-buggy code items from HumanEval for the code-judgment experiment.
Mutants are kept only if they fail the official HumanEval tests; canonical solutions must pass."""
import ast, json, os, re, subprocess, sys, tempfile, numpy as np, pandas as pd
he = pd.read_parquet('/home/user/data/humaneval/he.parquet')
RUN = '/home/user/data/humaneval/run'; os.makedirs(RUN, exist_ok=True)
def passes(code, test, entry):
    src = code + '\n\n' + test + f'\n\ncheck({entry})\n'
    with tempfile.NamedTemporaryFile('w', suffix='.py', dir=RUN, delete=False) as f: f.write(src); path = f.name
    try: r = subprocess.run([sys.executable, '-I', path], cwd=RUN, capture_output=True, timeout=10); ok = r.returncode == 0
    except subprocess.TimeoutExpired: ok = False
    os.unlink(path); return ok
SWAPS = [(r'<=', '<'), (r'>=', '>'), (r'(?<![<>=!])<(?![=<])', '<='), (r'(?<![<>=!-])>(?![=>])', '>='), (r'==', '!='), (r'!=', '=='),
         (r'\band\b', 'or'), (r'\bor\b', 'and'), (r'\+ 1\b', ''), (r'- 1\b', ''), (r'\bTrue\b', 'False'), (r'\bFalse\b', 'True'),
         (r'(?<![+\-*/%=<>!])\+(?![+=])', '-'), (r'\[1:\]', '[2:]'), (r'\[::-1\]', ''), (r'\bmax\(', 'min('), (r'\bmin\(', 'max(')]
rng = np.random.default_rng(7)
items = []
for _, r in he.iterrows():
    sol = r.canonical_solution; full = r.prompt + sol
    if not passes(full, r.test, r.entry_point): continue
    muts = []
    for pat, rep in SWAPS:
        for m in re.finditer(pat, sol):
            ms = sol[:m.start()] + rep + sol[m.end():]
            try: ast.parse(r.prompt + ms)
            except SyntaxError: continue
            muts.append(ms)
    rng.shuffle(muts)
    bug = next((ms for ms in muts[:8] if not passes(r.prompt + ms, r.test, r.entry_point)), None)
    items.append(dict(task_id=r.task_id, prompt=r.prompt, correct=full, buggy=(r.prompt + bug) if bug else None))
items = [i for i in items if i['buggy']]
print('problems with a verified failing mutant:', len(items))
idx = rng.permutation(len(items))[:120]
sel = []
for j, k in enumerate(idx):
    it = items[k]; is_bug = j % 2 == 1   # alternate: 60 correct, 60 buggy, each problem used once
    sel.append(dict(task_id=it['task_id'], label='buggy' if is_bug else 'correct', code=it['buggy'] if is_bug else it['correct']))
json.dump(sel, open('/home/user/fluffy-meme/arena-strategic/prereg/code_items.json', 'w'), indent=1)
print(pd.Series([s['label'] for s in sel]).value_counts().to_dict())
