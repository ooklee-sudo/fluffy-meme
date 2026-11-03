import sys, json, re, difflib
sys.path.insert(0, ".")
import lawlib
from concurrent.futures import ThreadPoolExecutor
act, lo, hi = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
NUMW = r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fourteen|fifteen|twenty|twenty-eight|thirty|sixty|ninety|\d[\d,\.]*)"
def fetch(n):
    return n, lawlib.section(act, n, "enacted"), lawlib.section(act, n, "current")
with ThreadPoolExecutor(8) as ex: res = list(ex.map(fetch, range(lo, hi + 1)))
cands = []; got = 0
for n, a, b in res:
    if not a or not b: continue
    got += 1
    if a == b: continue
    wa, wb = a.split(), b.split()
    sm = difflib.SequenceMatcher(None, wa, wb, autojunk=False)
    changes = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "replace": continue
        old, new = " ".join(wa[i1:i2]), " ".join(wb[j1:j2])
        if len(old.split()) <= 4 and len(new.split()) <= 4 and re.search(NUMW, old, re.I) and re.search(NUMW, new, re.I) and old.lower() != new.lower():
            ctx = " ".join(wa[max(0, i1 - 14):i2 + 8]); changes.append({"old": old, "new": new, "context_old": ctx, "context_new": " ".join(wb[max(0, j1 - 14):j2 + 8])})
    if changes: cands.append({"act": act, "section": n, "changes": changes})
print(f"{act}: fetched both versions for {got}/{hi-lo+1} sections; {len(cands)} with numeric replacements")
json.dump(cands, open(f"cands_{act.replace('/','_')}_{lo}_{hi}.json", "w"), indent=1)
for c in cands[:40]:
    for ch in c["changes"][:2]: print(f"  s.{c['section']}: '{ch['old']}' -> '{ch['new']}' | {ch['context_old'][:110]}")
