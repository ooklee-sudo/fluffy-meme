import json, re, numpy as np
items = json.load(open('/home/user/fluffy-meme/arena-strategic/prereg/code_items.json'))
cor = [i for i in items if i['label'] == 'correct']; bug = [i for i in items if i['label'] == 'buggy']
rng = np.random.default_rng(2027)
name = lambda code: re.search(r'def (\w+)\(', code[code.rfind('\ndef ') + 1:] if code.count('def ') > 1 else code).group(1)
def entry(it):   # name of the main (last top-level) function
    return [m.group(1) for m in re.finditer(r'^def (\w+)\(', it['code'], re.M)][-1]
prs = []
for k in range(60):
    defective = k % 2 == 1
    picks = list(rng.choice(len(cor), 3 if not defective else 2, replace=False))
    funcs = [cor[i] for i in picks]
    if defective: funcs.insert(int(rng.integers(3)), bug[int(rng.integers(len(bug)))])
    names = [entry(f) for f in funcs]
    code = '\n\n'.join(f['code'].strip() for f in funcs)
    prs.append(dict(pr=k, defective=defective, functions=names, buggy_function=next((entry(f) for f in funcs if f['label'] == 'buggy'), None),
                    title=f"Add {', '.join(names[:-1])} and {names[-1]} helpers", code=code))
json.dump(prs, open('/home/user/fluffy-meme/arena-strategic/prereg/code_prs.json', 'w'), indent=1)
print(len(prs), 'PRs; defective', sum(p['defective'] for p in prs), '| mean lines', round(np.mean([p['code'].count('\n') + 1 for p in prs]), 1))
