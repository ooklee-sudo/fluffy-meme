"""Upper bound on how many SWT-bench Lite faults the repo's pre-existing human tests could catch:
share of instances with a FAIL_TO_PASS test that is NOT newly added by the fix PR's test patch.
Run after swt_pilot.py has downloaded work/swt_lite_test.parquet."""
import json, re, pandas as pd
d = pd.read_parquet("work/swt_lite_test.parquet")
def names(f2p):
    out = set()
    for t in json.loads(f2p) if isinstance(f2p, str) else list(f2p):
        m = re.match(r"(test\w*) \(", t.strip())
        out.add(m.group(1) if m else re.split(r"::|\.", t.strip())[-1].split("[")[0])
    return out
rows = []
for r in d.itertuples():
    added = set(re.findall(r"(?m)^\+\s*(?:async\s+)?def (test\w+)", r.test_patch))
    rows.append(dict(repo=r.repo, any_pre=bool(names(r.FAIL_TO_PASS) - added)))
x = pd.DataFrame(rows)
print(len(x), "instances; some F2P test pre-existing:", round(x.any_pre.mean(), 3))
print(x.groupby("repo").any_pre.agg(["size", "mean"]).round(2).sort_values("size", ascending=False).head(8))
