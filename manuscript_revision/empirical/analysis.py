import glob, json, sys, os
import numpy as np, pandas as pd
import statsmodels.api as sm

OUT = os.environ.get("GHA_OUT", "/tmp/gha/out")
HOURS_F = os.environ.get("GHA_HOURS", "/tmp/gha/hours.txt")
START = os.environ.get("GHA_START", "2025-09-01")
PRS_F = os.environ.get("GHA_PRS", "/tmp/gha/prs.parquet")
rows = {"pr": [], "rv": [], "rc": []}
HOURS = set(open(HOURS_F).read().split())
for f in sorted(glob.glob(f"{OUT}/*.jsonl")):
    if f.split("/")[-1][:-6] not in HOURS: continue
    for line in open(f):
        d = json.loads(line); rows[d.pop("k")].append(d)
pr, rv, rc = (pd.DataFrame(rows[k]) for k in ("pr", "rv", "rc"))
print(f"raw closed PR events {len(pr):,}; review events {len(rv):,}; inline-comment events {len(rc):,}")

# ---------- classify authorship (same cues AIDev uses, plus Claude Code signature)
lg, ref = pr.login.fillna(""), pr.ref.fillna("")
agent = np.select(
    [lg.eq("Copilot") | ref.str.startswith("copilot/"),
     lg.eq("google-labs-jules[bot]"),
     lg.eq("devin-ai-integration[bot]"),
     ref.str.startswith("cursor/"),
     ref.str.startswith("codex/"),
     pr.claude | lg.isin(["claude[bot]", "claude"])],
    ["Copilot", "Jules", "Devin", "Cursor", "Codex", "ClaudeCode"], default="")
pr["agent"] = agent
is_bot_other = pr.utype.eq("Bot") & (pr.agent == "")
pr["group"] = np.where(pr.agent != "", "agent", np.where(is_bot_other | lg.str.endswith("[bot]"), "otherbot", "human"))
pr = pr[pr.group != "otherbot"].copy()

# ---------- window & size filters
pr["created"] = pd.to_datetime(pr.created, utc=True); pr["closed"] = pd.to_datetime(pr.closed, utc=True)
pr["merged_at"] = pd.to_datetime(pr.merged_at, utc=True)
pr = pr[pr.created >= pd.Timestamp(START, tz="UTC")]            # review events observed from window start
pr = pr.drop_duplicates("id")
miss = pr.assign(miss=pr["add"].isna()).groupby("group").miss.agg(["mean","sum"])
print("\nPRs with missing size field (dropped), by group:\n", miss.round(4).to_string())
pr["size"] = pr["add"] + pr["dele"]
pr = pr[(pr["size"] > 0) & pr["size"].notna()].copy()
pr["lsize"] = np.log(pr["size"])
pr["merged"] = pr.merged.astype(int)
pr["net_add"] = np.log((pr["add"] + 1) / (pr["dele"] + 1))
pr["hrs_to_merge"] = (pr.merged_at - pr.created).dt.total_seconds() / 3600

# ---------- human (non-author, non-bot) review activity, observed in the window
rv = rv[(rv.who != rv.pauthor) & rv.wtype.eq("User")]
rc = rc[(rc.who != rc.pauthor) & rc.wtype.eq("User")]
n_rc = rc.groupby("pid").size().rename("n_inline")
n_rc_sub = rc[rc.blen >= 30].groupby("pid").size().rename("n_inline_sub")
n_rv = rv.groupby("pid").size().rename("n_reviews")
n_rev_people = pd.concat([rv[["pid", "who"]], rc[["pid", "who"]]]).drop_duplicates().groupby("pid").size().rename("n_reviewers")
ev = pd.concat([rv[["pid", "at"]], rc[["pid", "at"]]]); ev["at"] = pd.to_datetime(ev["at"], utc=True)
first_ev = ev.groupby("pid")["at"].min().rename("first_review_at")
pr = pr.join(first_ev, on="id")
pr["first_rev_hrs"] = (pr.first_review_at - pr.created).dt.total_seconds() / 3600
pr["rev_24h"] = (pr.first_rev_hrs.between(0, 24)).astype(int)
pr = pr.join(n_rc, on="id").join(n_rc_sub, on="id").join(n_rv, on="id").join(n_rev_people, on="id")
for c in ("n_inline", "n_inline_sub", "n_reviews", "n_reviewers"): pr[c] = pr[c].fillna(0)
pr["any_review"] = ((pr.n_reviewers > 0)).astype(int)
pr["inline_per100"] = 100 * pr.n_inline / pr["size"]

# keep repos with both kinds of PR (within-repo comparison)
has = pr.groupby("repo").group.agg(lambda s: set(s))
both = has[has.apply(lambda s: {"agent", "human"} <= s)].index
pr["both"] = pr.repo.isin(both)
pr.to_parquet(PRS_F)

print("\n=== Sample ===")
print(pr.groupby("group").size().to_string())
print(pr[pr.group == "agent"].agent.value_counts().to_string())
print(f"repos with both agent and human PRs: {len(both):,}; PRs in them: {pr.both.sum():,} "
      f"(agent {((pr.group=='agent')&pr.both).sum():,}, human {((pr.group=='human')&pr.both).sum():,})")

def summ(d, label):
    g = d.groupby("group")
    t = pd.DataFrame({
        "N": g.size(), "median_size": g["size"].median(),
        "merge_rate": g.merged.mean(), "any_human_review": g.any_review.mean(),
        "mean_inline_cmts": g.n_inline.mean(), "inline_per100": g.inline_per100.mean(),
        "median_hrs_to_merge": d[d.merged == 1].groupby("group").hrs_to_merge.median(),
        "mean_net_add": g.net_add.mean(),
        "share_add_gt_del": g.apply(lambda x: (x["add"] > x["dele"]).mean())}).round(3)
    print(f"\n--- {label}"); print(t.T.to_string())

summ(pr, "All PRs (descriptive)")
summ(pr[pr.both], "Repos with both agent and human PRs (descriptive)")

# ---------- within-repo regressions (repo fixed effects by demeaning; SEs clustered by repo)
def fe_ols(d, y, xs, label):
    d = d.dropna(subset=[y] + xs).copy()
    cnt = d.groupby("repo").repo.transform("size"); d = d[cnt >= 2]
    Y = d[y] - d.groupby("repo")[y].transform("mean")
    X = d[xs] - d.groupby("repo")[xs].transform("mean")
    m = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.repo)[0]})
    print(f"\n[{label}]  N={len(d):,}, repos={d.repo.nunique():,}")
    for x in xs:
        print(f"   {x:22s} b={m.params[x]:+.4f}  se={m.bse[x]:.4f}  p={m.pvalues[x]:.3g}")
    return m

d = pr[pr.both & pr.group.isin(["agent", "human"])].copy()
d["is_agent"] = (d.group == "agent").astype(int)
d["lsize_c"] = d.lsize - d.lsize.mean()
d["agent_x_lsize"] = d.is_agent * d.lsize_c
d["log1p_inline"] = np.log1p(d.n_inline)

print("\n=== P7: review intensity, agent vs human, within-repo ===")
fe_ols(d, "any_review", ["is_agent", "lsize_c", "agent_x_lsize"], "LPM: P(any human review) ~ agent, size, agent×size")
fe_ols(d, "log1p_inline", ["is_agent", "lsize_c", "agent_x_lsize"], "log(1+inline human comments)")
fe_ols(d[d.merged == 1], "log1p_inline", ["is_agent", "lsize_c", "agent_x_lsize"], "log(1+inline), merged PRs only")
fe_ols(d[d.merged == 1], "any_review", ["is_agent", "lsize_c", "agent_x_lsize"], "P(any review), merged PRs only")
print("\n=== P5: net-addition bias ===")
fe_ols(d, "net_add", ["is_agent", "lsize_c", "agent_x_lsize"], "log((add+1)/(del+1)) ~ agent, size")
print("\n=== By agent (vs human, same repos), P(any human review) and log(1+inline) ===")
for a in ["Copilot", "Codex", "Cursor", "Devin", "Jules", "ClaudeCode"]:
    s = d[(d.agent == a) | (d.group == "human")].copy()
    if (s.agent == a).sum() < 50: print(f"  {a}: too few ({(s.agent==a).sum()})"); continue
    s["is_agent"] = (s.agent == a).astype(int); s["agent_x_lsize"] = s.is_agent * s.lsize_c
    m1 = fe_ols(s, "any_review", ["is_agent", "lsize_c"], f"{a}: P(any human review)")
    m2 = fe_ols(s, "net_add", ["is_agent", "lsize_c"], f"{a}: net add")
