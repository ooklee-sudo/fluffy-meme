import numpy as np, pandas as pd
a = pd.read_parquet("/tmp/satd/agent_rows.parquet"); h = pd.read_parquet("/tmp/satd/human_rows.parquet")
h["lang"] = h.lang.str.lower(); a["agent"] = a.agent.replace({"OpenAI_Codex": "Codex", "Claude_Code": "ClaudeCode"})
a = a[a.pr_user != "tamnd"]; a["repo"] = a.repo_url
for d in (a, h): d["smell"] = d.long + d.dup + d.broad + d.suppress
L = sorted(set(a.lang) & set(h.lang)); a, h = a[a.lang.isin(L)], h[h.lang.isin(L)]
bins = [0, 5, 20, 50, 150, 500, 10**9]; lab = ["1-5", "6-20", "21-50", "51-150", "151-500", ">500"]
for d in (a, h): d["sz"] = pd.cut(d.added, bins, labels=lab)
print("share of file-rows by patch size (added lines):")
print(pd.DataFrame({"agent": a.sz.value_counts(normalize=True), "human": h.sz.value_counts(normalize=True)}).reindex(lab).round(3).to_string())
MET = ["strict", "wide", "long", "dup", "broad", "suppress", "smell"]
# standardise BOTH language and size: cell = lang x size bin; weight cells by the agent's added-line share
def cell_rates(d):
    g = d.groupby(["lang", "sz"], observed=True); return (1000 * g[MET].sum().div(g.added.sum(), axis=0)), g.added.sum()
ra, wa = cell_rates(a); rh, wh = cell_rates(h)
w = wa / wa.sum(); common = w.index.intersection(rh.index); cov = w[common].sum()
print(f"\nlanguage x size cells shared by both: {len(common)} covering {cov:.1%} of agent added lines")
w = w[common] / w[common].sum()
sa = (ra.loc[common].mul(w, axis=0)).sum(); sh = (rh.loc[common].mul(w, axis=0)).sum()
t = pd.DataFrame({"agent": sa, "human(std)": sh}); t["ratio"] = t.agent / t["human(std)"]
print("\nPer 1,000 added lines, human reweighted to the agent's language x patch-size mix:"); print(t.round(2).to_string())
print(f"\nstrict markers per smell: agent {sa.strict/sa.smell:.3f}, human {sh.strict/sh.smell:.3f}, ratio {(sa.strict/sa.smell)/(sh.strict/sh.smell):.2f}")
print("\nBy patch size (raw rates per 1k added lines):")
rows = []
for s in lab:
    ga, gh = a[a.sz == s], h[h.sz == s]
    if len(ga) < 200 or len(gh) < 200: continue
    rows.append((s, len(ga), len(gh), 1000*ga.strict.sum()/ga.added.sum(), 1000*gh.strict.sum()/gh.added.sum(), 1000*ga.smell.sum()/ga.added.sum(), 1000*gh.smell.sum()/gh.added.sum(),
                 1000*ga.dup.sum()/ga.added.sum(), 1000*gh.dup.sum()/gh.added.sum()))
print(pd.DataFrame(rows, columns=["size", "n_agent", "n_human", "mk_agent", "mk_human", "smell_agent", "smell_human", "dup_agent", "dup_human"]).round(2).to_string(index=False))
# excluding the duplicate-line component (most size-sensitive)
for nm, cols in (("smell without dup", ["long", "broad", "suppress"]),):
    for d in (a, h): d["s2"] = d[cols].sum(axis=1)
    g = a.groupby(["lang", "sz"], observed=True); r1 = 1000 * g.s2.sum() / g.added.sum()
    g = h.groupby(["lang", "sz"], observed=True); r2 = 1000 * g.s2.sum() / g.added.sum()
    print(f"\n{nm} (standardised): agent {(r1.loc[common]*w).sum():.2f}, human {(r2.loc[common]*w).sum():.2f}, ratio {(r1.loc[common]*w).sum()/(r2.loc[common]*w).sum():.2f}")
