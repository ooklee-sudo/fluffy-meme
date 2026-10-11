"""Replication across windows: same specifications, key coefficients only."""
import sys, numpy as np, pandas as pd, statsmodels.api as sm
files = dict(w2="/tmp/gha/prs_w2.parquet", w1="/tmp/gha/prs_w1.parquet", w3="/tmp/gha/prs_w3.parquet")
names = dict(w2="Aug 1-14", w1="Sep 1-14", w3="Sep 15-28")

def prep(f, w):
    pr = pd.read_parquet(f); pr["window"] = w
    pr["is_agent"] = (pr.group == "agent").astype(int)
    return pr

def fe(d, y, xs):
    d = d.dropna(subset=[y] + xs).copy()
    d = d[d.groupby("repo").repo.transform("size") >= 2]
    Y = d[y] - d.groupby("repo")[y].transform("mean"); X = d[xs] - d.groupby("repo")[xs].transform("mean")
    m = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.repo)[0]})
    return m, len(d), d.repo.nunique()

def run(pr):
    pr = pr.copy(); both = pr[pr.both & pr.group.isin(["agent", "human"])].copy()
    both["lsize_c"] = both.lsize - both.lsize.mean(); both["agent_x_lsize"] = both.is_agent * both.lsize_c
    both["log1p_inline"] = np.log1p(both.n_inline)
    auth = pr[pr.group.eq("human") | pr.agent.isin(["Codex", "Cursor", "ClaudeCode"])].groupby("repo").login.nunique()
    both["n_auth"] = both.repo.map(auth).fillna(0)
    team, solo = both[both.n_auth >= 3], both[both.n_auth <= 1]
    X = ["is_agent", "lsize_c"]
    specs = {
      "P5  net-add, all":                 (both, "net_add"),
      "P5  net-add, solo repos":          (solo, "net_add"),
      "P5  net-add, team repos":          (team, "net_add"),
      "P7  any review, all":              (both, "any_review"),
      "P7  any review, excl. Copilot":    (both[both.agent != "Copilot"], "any_review"),
      "P7  any review, team, excl. Cop.": (team[team.agent != "Copilot"], "any_review"),
      "P7  review <24h, team, excl. Cop.":(team[team.agent != "Copilot"], "rev_24h"),
      "P7  log(1+inline), excl. Copilot": (both[both.agent != "Copilot"], "log1p_inline"),
    }
    out = {}
    for k, (d, y) in specs.items():
        m, n, r = fe(d, y, X); out[k] = (m.params["is_agent"], m.bse["is_agent"], n, r)
    return out, (len(pr[pr.group == "agent"]), len(pr[pr.group == "human"]), len(both[both.is_agent == 1]), len(both[both.is_agent == 0]))

res, ns = {}, {}
frames = []
for w, f in files.items():
    try: pr = prep(f, w)
    except FileNotFoundError: print("missing", f); continue
    res[w], ns[w] = run(pr); frames.append(pr)
pooled = pd.concat(frames, ignore_index=True)
# repo is the unit; a repo can appear in several windows -> recompute 'both' on the pooled sample
has = pooled.groupby("repo").group.agg(lambda s: {"agent", "human"} <= set(s)); pooled["both"] = pooled.repo.map(has)
res["pooled"], ns["pooled"] = run(pooled)

cols = [c for c in ["w2", "w1", "w3", "pooled"] if c in res]
print("Agent-vs-human coefficient (within-repo FE, size control); SE in parentheses\n")
print(f"{'':36s}" + "".join(f"{names.get(c, 'Pooled 3 windows'):>20s}" for c in cols))
for k in res[cols[0]]:
    line = f"{k:36s}"
    for c in cols:
        b, se, n, r = res[c][k]; stars = "***" if abs(b / se) > 3.29 else "**" if abs(b / se) > 2.58 else "*" if abs(b / se) > 1.96 else ""
        line += f"{b:+8.3f}{stars:<3s}({se:.3f})".rjust(20)
    print(line)
print("\nN agent PRs / human PRs (all repos); agent / human PRs in repos with both")
for c in cols: print(f"  {names.get(c, 'Pooled'):>16s}: {ns[c][0]:,} / {ns[c][1]:,};  {ns[c][2]:,} / {ns[c][3]:,}")
