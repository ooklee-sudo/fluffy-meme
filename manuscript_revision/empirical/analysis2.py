import os, numpy as np, pandas as pd, statsmodels.api as sm
pr = pd.read_parquet(os.environ.get("GHA_PRS", "/tmp/gha/prs.parquet"))
pr["is_agent"] = (pr.group == "agent").astype(int)
pr["lsize_c"] = pr.lsize - pr.lsize.mean()
pr["agent_x_lsize"] = pr.is_agent * pr.lsize_c
pr["log1p_inline"] = np.log1p(pr.n_inline)
t = pr.title.fillna("").str.lower()
for k, pat in dict(t_refactor="refactor|cleanup|clean up|simplif|rename", t_fix="fix|bug|patch|hotfix", t_doc="doc|readme|typo|comment",
                   t_test="test|spec", t_feat="feat|add |implement|support|introduce", t_dep="bump|upgrade|update dep|deps").items():
    pr[k] = t.str.contains(pat).astype(int)
TYPES = ["t_refactor", "t_fix", "t_doc", "t_test", "t_feat", "t_dep"]

def fe(d, y, xs, label, quiet=False):
    d = d.dropna(subset=[y] + xs).copy()
    d = d[d.groupby("repo").repo.transform("size") >= 2]
    Y = d[y] - d.groupby("repo")[y].transform("mean"); X = d[xs] - d.groupby("repo")[xs].transform("mean")
    m = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.repo)[0]})
    if not quiet:
        print(f"\n[{label}] N={len(d):,}, repos={d.repo.nunique():,}")
        for x in xs[:3]: print(f"   {x:16s} b={m.params[x]:+.4f}  se={m.bse[x]:.4f}  p={m.pvalues[x]:.3g}")
    return m

both = pr[pr.both & pr.group.isin(["agent", "human"])].copy()

print("=== Why raw and within-repo P7 differ: raw gap is across repos; within-repo gap is not ===")
r = both.groupby(["repo", "group"]).any_review.mean().unstack().dropna()
print(f"repos with both: {len(r):,}; mean P(review) human {r.human.mean():.3f}, agent {r.agent.mean():.3f} (each repo weighted equally)")
big = both.groupby("repo").size().sort_values(ascending=False).head(50).index
print("top-50 PR-volume repos hold", f"{both.repo.isin(big).mean():.0%}", "of PRs; their human review rate",
      f"{both[both.repo.isin(big)&(both.group=='human')].any_review.mean():.3f}", "vs agent", f"{both[both.repo.isin(big)&(both.group=='agent')].any_review.mean():.3f}")

print("\n=== P7 robustness ===")
X3 = ["is_agent", "lsize_c", "agent_x_lsize"]
fe(both, "any_review", X3 + TYPES, "P(any human review), + task-type controls")
fe(both[both.agent != "Copilot"], "any_review", X3, "P(any human review), excluding Copilot")
fe(both[both.agent != "Copilot"], "log1p_inline", X3, "log(1+inline), excluding Copilot")
# Team repos: >=3 distinct non-bot PR authors observed in window (proxy for review being possible)
auth = pr[pr.group.eq("human") | pr.agent.isin(["Codex", "Cursor", "ClaudeCode"])].groupby("repo").login.nunique()
both["n_auth"] = both.repo.map(auth).fillna(0)
team, solo = both[both.n_auth >= 3], both[both.n_auth <= 1]
print(f"\nteam repos (>=3 authors): {team.repo.nunique():,} repos, {len(team):,} PRs; solo repos (<=1 author): {solo.repo.nunique():,} repos, {len(solo):,} PRs")
fe(team[team.agent != "Copilot"], "any_review", X3, "P(any human review), team repos, excl. Copilot")
fe(team, "log1p_inline", X3, "log(1+inline), team repos, all agents")
print("\nlarge PRs only (size >= 500 lines):")
fe(both[both["size"] >= 500], "log1p_inline", ["is_agent", "lsize_c"], "log(1+inline), large PRs")
fe(both[(both["size"] >= 500) & (both.agent != "Copilot")], "any_review", ["is_agent", "lsize_c"], "P(any review), large PRs excl. Copilot")

print("\n=== P5 robustness: net-addition bias ===")
fe(both, "net_add", X3 + TYPES, "net_add, + task-type controls")
fe(both[both.t_refactor == 0], "net_add", X3, "net_add, excluding refactor-titled PRs")
fe(team, "net_add", X3, "net_add, TEAM repos (>=3 authors)")
fe(solo, "net_add", X3, "net_add, SOLO repos (<=1 author)")
# Table 2 test: P5 in single-contributor code (rational acceleration predicts absent)
m_s, m_t = fe(solo, "net_add", X3, "", True), fe(team, "net_add", X3, "", True)
print(f"\n  agent effect solo = {m_s.params['is_agent']:+.3f} (se {m_s.bse['is_agent']:.3f}); team = {m_t.params['is_agent']:+.3f} (se {m_t.bse['is_agent']:.3f})")
# how big in raw terms
a, h = both[both.group == "agent"], both[both.group == "human"]
print(f"\n  median additions/deletions: agent {a['add'].median():.0f}/{a['dele'].median():.0f}, human {h['add'].median():.0f}/{h['dele'].median():.0f}")
print(f"  pooled deletion share of changed lines: agent {a.dele.sum()/a['size'].sum():.3f}, human {h.dele.sum()/h['size'].sum():.3f}")
print(f"  within-repo effect exp(0.633) = x{np.exp(0.633):.2f} higher additions-to-deletions ratio")
