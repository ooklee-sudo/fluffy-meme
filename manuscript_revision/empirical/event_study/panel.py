"""Build a repo x sampled-week PR panel for AIDev repositories (Feb-Sep 2025, first 7 days of each month)."""
import glob, json, os
import numpy as np, pandas as pd

PERIODS = ["2025-02", "2025-03", "2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09"]
def hours_for(period):
    y, m = map(int, period.split("-"))
    return [f"{y}-{m:02d}-{d:02d}-{h}" for d in range(1, 8) for h in range(24)]
def dir_for(period):
    if period == "2025-08": return "/tmp/gha/out_w2"
    if period == "2025-09": return "/tmp/gha/out"
    return "/tmp/gha/out_ev"
KEEP = set(open("/tmp/gha/aidev_repos.txt").read().split())

rows = {"pr": [], "rv": [], "rc": []}
for pi, per in enumerate(PERIODS):
    d = dir_for(per)
    for hr in hours_for(per):
        f = f"{d}/{hr}.jsonl"
        if not os.path.exists(f): continue
        for line in open(f):
            r = json.loads(line)
            if r["repo"].lower() not in KEEP: continue
            r["period"] = pi; rows[r.pop("k")].append(r)
pr, rv, rc = (pd.DataFrame(rows[k]) for k in ("pr", "rv", "rc"))
print(f"events kept: PRs {len(pr):,}, reviews {len(rv):,}, inline comments {len(rc):,}")

lg, ref = pr.login.fillna(""), pr.ref.fillna("")
pr["agent"] = np.select(
    [lg.eq("Copilot") | ref.str.startswith("copilot/"), lg.eq("google-labs-jules[bot]"), lg.eq("devin-ai-integration[bot]"),
     ref.str.startswith("cursor/"), ref.str.startswith("codex/"), pr.claude | lg.isin(["claude[bot]", "claude"])],
    ["Copilot", "Jules", "Devin", "Cursor", "Codex", "ClaudeCode"], default="")
other_bot = (pr.utype.eq("Bot") | lg.str.endswith("[bot]")) & (pr.agent == "")
pr["group"] = np.where(pr.agent != "", "agent", np.where(other_bot, "otherbot", "human"))
pr = pr[pr.group != "otherbot"].copy()
pr["created"] = pd.to_datetime(pr.created, utc=True)
start = pr.period.map(lambda i: pd.Timestamp(PERIODS[i] + "-01", tz="UTC"))
pr = pr[(pr.created >= start)].drop_duplicates("id")          # created inside the sampled week, so its reviews are observed
pr["size"] = pr["add"] + pr["dele"]; pr = pr[pr["size"].notna() & (pr["size"] > 0)].copy()
pr["net_add"] = np.log((pr["add"] + 1) / (pr["dele"] + 1))
t = pr.title.fillna("").str.lower()
pr["refactor"] = t.str.contains("refactor|cleanup|clean up|simplif|rename|remove unused|dead code").astype(int)
pr["merged"] = pr.merged.astype(int)

rv = rv[(rv.who != rv.pauthor) & rv.wtype.eq("User")]; rc = rc[(rc.who != rc.pauthor) & rc.wtype.eq("User")]
rev = pd.concat([rv[["pid", "who"]], rc[["pid", "who"]]]).drop_duplicates().groupby("pid").size().rename("n_reviewers")
ninl = rc.groupby("pid").size().rename("n_inline")
pr = pr.join(rev, on="id").join(ninl, on="id")
pr["any_review"] = (pr.n_reviewers.fillna(0) > 0).astype(int); pr["n_inline"] = pr.n_inline.fillna(0)
pr.to_parquet("/tmp/gha/panel_prs.parquet")
print(pr.groupby(["period", "group"]).size().unstack().to_string())
