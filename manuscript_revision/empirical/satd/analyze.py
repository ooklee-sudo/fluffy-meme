import numpy as np, pandas as pd
rng = np.random.default_rng(7)
c = pd.read_parquet("/tmp/satd/commit_file_counts.parquet")
c["agent"] = c.agent.replace({"OpenAI_Codex": "Codex", "Claude_Code": "ClaudeCode"})

print("=== 1. Marker density by agent (added lines in code files) ===")
def per_agent(d):
    g = d.groupby("agent")
    t = pd.DataFrame({"PRs": g.pr_id.nunique(), "repos": g.repo_url.nunique(), "added_lines": g.added.sum(),
                      "strict_per_1k": 1000 * g.strict.sum() / g.added.sum(), "wide_per_1k": 1000 * g.wide.sum() / g.added.sum()})
    p = d.groupby(["agent", "pr_id"]).agg(a=("added", "sum"), s=("strict", "sum")).reset_index()
    p["has"] = p.s > 0
    t["PRs_with_marker_%"] = 100 * p.groupby("agent").has.mean()
    # repo-level: mean of per-repo rates (so one prolific repo cannot dominate)
    r = d.groupby(["agent", "repo_url"]).agg(a=("added", "sum"), s=("strict", "sum")).reset_index()
    r["rate"] = 1000 * r.s / r.a
    t["mean_repo_strict_per_1k"] = r.groupby("agent").rate.mean()
    return t.round(2)
print(per_agent(c).to_string())

# one individual user (tamnd) supplies most Codex rows; drop individual users >20% of an agent's file rows (bot accounts are the agent itself, not dropped)
share = c.groupby(["agent", "pr_user"]).size().rename("n").reset_index()
share["frac"] = share.n / share.groupby("agent").n.transform("sum")
heavy = share[(share.frac > 0.2) & ~share.pr_user.isin(["Copilot", "devin-ai-integration[bot]", "cursoragent", "copilot-swe-agent[bot]"])]
print("\nindividual users >20% of an agent's file rows (dropped in robustness):", list(zip(heavy.agent, heavy.pr_user, heavy.frac.round(2))))
drop = set(zip(heavy.agent, heavy.pr_user))
c2 = c[[ (a, u) not in drop for a, u in zip(c.agent, c.pr_user)]]
print("\n--- excluding dominant users"); print(per_agent(c2).to_string())

print("\n=== 2. Within-PR contrast: agent-authored vs human-authored commits (same PR) ===")
au = c.author.fillna("")
bot_commit = au.isin(["Copilot", "cursoragent"]) | au.str.endswith("[bot]")
d = c[c.agent.isin(["Copilot", "Devin", "Cursor"])].copy(); d["by_agent"] = bot_commit[d.index]
g = d.groupby(["pr_id", "by_agent"]).agg(a=("added", "sum"), s=("strict", "sum"), w=("wide", "sum")).unstack(fill_value=0)
g.columns = [f"{x}_{'agent' if y else 'human'}" for x, y in g.columns]
mixed = g[(g.a_agent > 0) & (g.a_human > 0)]
print(f"PRs with code added by both the agent account and a human: {len(mixed):,}")
def rates(m, k="s"):
    return 1000 * m[f"{k}_agent"].sum() / m.a_agent.sum(), 1000 * m[f"{k}_human"].sum() / m.a_human.sum()
for k, lab in (("s", "strict (TODO/FIXME/HACK/XXX)"), ("w", "wide (+workaround/for now/...)")):
    ra, rh = rates(mixed, k)
    bs = []
    idx = np.arange(len(mixed)); M = mixed.reset_index(drop=True)
    for _ in range(2000):
        s = M.iloc[rng.choice(idx, len(idx))]; x, y = rates(s, k); bs.append(y - x)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    print(f"  {lab}: agent commits {ra:.2f}/1k lines, human commits {rh:.2f}/1k; human minus agent = {rh-ra:+.2f} [95% CI {lo:+.2f}, {hi:+.2f}] (PR bootstrap)")
print(f"  added lines: agent {mixed.a_agent.sum():,}, human {mixed.a_human.sum():,}")
for a in ["Copilot", "Devin", "Cursor"]:
    m = mixed[mixed.index.isin(d[d.agent == a].pr_id.unique())]
    if len(m) > 30:
        ra, rh = rates(m); print(f"    {a}: PRs {len(m):,}, agent {ra:.2f} vs human {rh:.2f} per 1k lines")
# PR-level paired sign test on PRs where both rates are defined and at least one marker appears
pp = mixed.assign(ra=mixed.s_agent / mixed.a_agent, rh=mixed.s_human / mixed.a_human)
pp = pp[(pp.ra > 0) | (pp.rh > 0)]
print(f"  PRs with a marker in either part: {len(pp):,}; human rate higher in {100*(pp.rh>pp.ra).mean():.1f}%, agent higher in {100*(pp.ra>pp.rh).mean():.1f}%")
