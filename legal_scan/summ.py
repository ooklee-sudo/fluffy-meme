import json, sys, statistics as st
mean = st.mean
def ms(xs, rng=True):
    xs = [x for x in xs if x == x]
    return "n/a" if not xs else f"{mean(xs):.2f}" + (f" [{min(xs):.2f}-{max(xs):.2f}]" if rng else "")
def table(path, label):
    real = json.load(open(path)); print("==", label, path.split('/')[-1], "rows", len(real), "seeds", sorted({r['seed'] for r in real}))
    rl = lambda m, l, kA, kd: [r for r in real if r["method"] == m and r["lam"] == l and r["kA"] == kA and r["kdep"] == kd]
    K = ("listed", "unlisted_AB", "ripple_dep", "keep_control", "keep_control_hard", "currency_all")
    for lab, m, l, kA, kd in (("amend only", "none", 0., .5, 0), ("retain all l=1", "unscoped", 1., .5, 0), ("retain all l=10", "unscoped", 10., .5, 0), ("stream-scoped", "ss", 10., .5, 0), ("dep-scoped", "dep", 10., .5, 0), ("ss+all listed", "ss", 10., 1, 1)):
        v = rl(m, l, kA, kd)
        if v: print(f"  {lab:16s}", " | ".join(f"{k[:11]}={ms([x[k] for x in v])}" for k in K))
    for kA in (.1, .25, .5, .75):
        a, d, s = rl("none", 0., kA, 0), rl("dep", 10., kA, 0), rl("ss", 10., kA, 0)
        if a: print(f"  k={kA}: unlisted AO={ms([x['unlisted_AB'] for x in a], False)} dep={ms([x['unlisted_AB'] for x in d], False)} ss={ms([x['unlisted_AB'] for x in s], False)} | ctl-hard AO={ms([x['keep_control_hard'] for x in a], False)} dep={ms([x['keep_control_hard'] for x in d], False)} | currency AO={ms([x['currency_all'] for x in a], False)} dep={ms([x['currency_all'] for x in d], False)} ss={ms([x['currency_all'] for x in s], False)}")
if __name__ == "__main__":
    for p in sys.argv[1:]: table(p, "")
