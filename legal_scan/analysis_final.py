import json, math, collections, statistics as st, warnings, os
import numpy as np
warnings.filterwarnings("ignore")
import statsmodels.api as sm
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
mean = st.mean
SD = "/tmp/claude-0/-home-user-fluffy-meme/6d046680-2797-598c-a7db-54c51fe25fec/scratchpad/"
BANK = json.load(open(SD + "v3/real_law/real_fact_bank_v3.json"))
MODELS = {"Qwen2.5-7B": ("reallaw_v3qwen25", "p3qwen25"), "Qwen3-8B-Base": ("reallaw_v3qwen3", "p3qwen3"), "Olmo-3-7B": ("reallaw_v3olmo3", "p3olmo3")}
V3 = {m: json.load(open(f"{SD}final/{a}.json")) for m, (a, b) in MODELS.items()}
PP = {m: json.load(open(f"{SD}final/{b}_reallaw_{b}.json")) for m, (a, b) in MODELS.items()}
os.makedirs(SD + "final/figs", exist_ok=True)
OUT = {}
def ms(xs, rng=True):
    xs = [x for x in xs if x == x]
    return "n/a" if not xs else f"{mean(xs):.2f}" + (f" [{min(xs):.2f}–{max(xs):.2f}]" if rng else "")
def sel(rows, m, l, kA, kd): return [r for r in rows if r["method"] == m and r["lam"] == l and r["kA"] == kA and r["kdep"] == kd]
ch = [i for i, f in enumerate(BANK) if f["kind"] == "changed"]; ctl = [i for i, f in enumerate(BANK) if f["kind"] == "control"]
dep_idx = {i for i in ch if BANK[i]["cluster"] == "C" and BANK[i]["role"] == "dependent"}
key = lambda i: (BANK[i]["old"].strip(), BANK[i]["new"].strip())
# ---- bank description
pats = collections.defaultdict(list)
for i in ch:
    if i not in dep_idx: pats[key(i)].append(i)
sizes = sorted((len(v) for v in pats.values()), reverse=True)
acts_changed = collections.Counter(BANK[i]["act_name"] for i in ch); acts_all = {BANK[i]["act_name"] for i in range(len(BANK))}
OUT["bank"] = dict(n=len(BANK), changed=len(ch), controls=len(ctl), dependents=len(dep_idx), patterns=len(pats), singletons=sum(1 for s in sizes if s == 1), largest=sizes[:5], acts_changed=len(acts_changed), acts_all=len(acts_all), acts_changed_list=dict(acts_changed))
# ---- main policy table (k = 0.5) per model
POL = [("Amend only", "none", 0.0, .5, 0), ("Retain all (λ = 1)", "unscoped", 1.0, .5, 0), ("Stream-scoped retention", "ss", 10.0, .5, 0), ("Dependency-scoped retention", "dep", 10.0, .5, 0), ("Stream-scoped, all affected provisions listed", "ss", 10.0, 1, 1)]
OUT["policy"] = {}
for m, rows in V3.items():
    OUT["policy"][m] = {}
    for lab, me, l, kA, kd in POL:
        v = sel(rows, me, l, kA, kd)
        OUT["policy"][m][lab] = {k: ms([x[k] for x in v]) for k in ("listed", "unlisted_AB", "ripple_dep", "keep_control", "keep_control_hard", "currency_all")}
        OUT["policy"][m][lab]["currency_mean"] = mean([x["currency_all"] for x in v]); OUT["policy"][m][lab]["hard_mean"] = mean([x["keep_control_hard"] for x in v])
# ---- twin analysis (amend only and dependency-scoped; all kA)
T = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit_transform([f"{f['act_name']} {f.get('loc') or 'section ' + str(f['section'])} {f['title']} {f['ctx']}" for f in BANK]); SIM = (T @ T.T).toarray()
def twin_data(rows, method, lam):
    data = []
    for r in rows:
        if r["method"] != method or r["lam"] != lam or r["kdep"] != 0 or "ok" not in r: continue
        L = set(r["listed_idx"])
        for i in ch:
            if i in L: continue
            twin = any(key(j) == key(i) for j in L if j != i) if i not in dep_idx else False
            data.append(dict(seed=r["seed"], k=r["kA"], i=i, ok=r["ok"][i], sim=max(SIM[i, j] for j in L if j != i), dep=int(i in dep_idx), twin=int(twin)))
    return data
OUT["twin"] = {}
for m, rows in V3.items():
    out = {}
    for lab, me, l in (("Amend only", "none", 0.0), ("Dependency-scoped", "dep", 10.0)):
        d = twin_data(rows, me, l); sib = [x for x in d if not x["dep"]]
        r_ = {}
        r_["with_twin"] = (mean([x["ok"] for x in sib if x["twin"]]), sum(1 for x in sib if x["twin"]))
        r_["no_twin"] = (mean([x["ok"] for x in sib if not x["twin"]]), sum(1 for x in sib if not x["twin"]))
        dd = [x for x in d if x["dep"]]; r_["dependent"] = (mean([x["ok"] for x in dd]), len(dd), len({x["i"] for x in dd}))
        y = np.array([x["ok"] for x in sib], float); X = np.array([[1, x["sim"], x["twin"]] for x in sib], float); g = np.array([x["i"] for x in sib])
        res = sm.Logit(y, X).fit(disp=0, cov_type="cluster", cov_kwds={"groups": g})
        r_["logit"] = dict(sim=(float(res.params[1]), float(res.bse[1]), float(res.pvalues[1])), twin=(float(res.params[2]), float(res.bse[2]), float(res.pvalues[2])), n=len(y), provisions=len(set(g)))
        for tw in (0, 1):
            sub = [x for x in sib if x["twin"] == tw]; q = np.quantile([x["sim"] for x in sub], [0, 1/3, 2/3, 1]); tert = []
            for a, b in zip(q[:-1], q[1:]):
                vv = [x["ok"] for x in sub if a <= x["sim"] <= b]; tert.append(mean(vv))
            r_[f"tercile_twin{tw}"] = tert
        out[lab] = r_
    OUT["twin"][m] = out
# ---- pattern listing (P): measured
OUT["pat"] = {}
for m, rows in PP.items():
    o = {}
    for lab, me, l in (("Amend only", "none", 0.0), ("Dependency-scoped", "dep", 10.0), ("Pattern listing", "pat", 10.0)):
        for k in (.1, .25, .5, .75):
            v = sel(rows, me, l, k, 0)
            if v: o[(lab, k)] = dict(extra=mean([x.get("n_extra", 0) for x in v]), unl=ms([x["unlisted_AB"] for x in v]), unl_m=mean([x["unlisted_AB"] for x in v if x["unlisted_AB"] == x["unlisted_AB"]]), hard=ms([x["keep_control_hard"] for x in v]), hard_m=mean([x["keep_control_hard"] for x in v]), cur=ms([x["currency_all"] for x in v]), cur_m=mean([x["currency_all"] for x in v]))
    OUT["pat"][m] = {f"{a}|{k}": v for (a, k), v in o.items()}
# ---- economic model from measured per-fact outcomes at k = 0.5
def wrong_counts(rows, method, lam, kA, kd):
    v = [r for r in rows if r["method"] == method and r["lam"] == lam and r["kA"] == kA and r["kdep"] == kd and "ok" in r]
    cw = mean([sum(1 - r["ok"][i] for i in ch) for r in v]); kw = mean([sum(1 - x for x in r["ctl_hard_ok"]) for r in v]); ns = mean([r["n_stream"] for r in v])
    return cw, kw, ns
ECON = {}
for m in MODELS:
    base_rows = V3[m]; p_rows = PP[m]
    A = wrong_counts(base_rows, "none", 0.0, .5, 0); S = wrong_counts(base_rows, "ss", 10.0, .5, 0); D = wrong_counts(base_rows, "dep", 10.0, .5, 0)
    Pp = wrong_counts(p_rows, "pat", 10.0, .5, 0); F = wrong_counts(base_rows, "ss", 10.0, 1, 1)
    ECON[m] = {"A": dict(cw=A[0], kw=A[1], lab=0.0), "S": dict(cw=S[0], kw=S[1], lab=0.0), "D": dict(cw=D[0], kw=D[1], lab=0.0), "P": dict(cw=Pp[0], kw=Pp[1], lab=Pp[2] - A[2]), "F": dict(cw=F[0], kw=F[1], lab=F[2] - A[2])}
OUT["econ"] = ECON
NC0 = len(ctl)
def resid(e, nc=NC0): return e["cw"] + e["kw"] * nc / NC0
def phi(e, alpha, c, Fc, nc=NC0): return alpha * c * e["lab"] + math.sqrt(2 * Fc * alpha * resid(e, nc))
def best(E_, alpha, c, Fc, nc=NC0, pols=("A", "S", "D", "P", "F")): return min(pols, key=lambda j: phi(E_[j], alpha, c, Fc, nc))
th = {}
for m, E_ in ECON.items():
    rD, rP, rA = resid(E_["D"]), resid(E_["P"]), resid(E_["A"]); mP = E_["P"]["lab"]; mF = E_["F"]["lab"]
    nc_star = NC0 * (E_["D"]["cw"] - E_["A"]["cw"]) / (E_["A"]["kw"] - E_["D"]["kw"])
    th[m] = dict(r={j: resid(E_[j]) for j in E_}, lab={j: E_[j]["lab"] for j in E_}, nc_star_D_vs_A=nc_star,
                 cstar_P_vs_D=lambda alpha, Fc, rD=rD, rP=rP, mP=mP: math.sqrt(2 * Fc * alpha) * (math.sqrt(rD) - math.sqrt(rP)) / (alpha * mP),
                 alpha_star=lambda c, Fc, rD=rD, rP=rP, mP=mP: 2 * Fc * (math.sqrt(rD) - math.sqrt(rP)) ** 2 / (c * mP) ** 2)
OUT["th"] = {m: dict(r=v["r"], lab=v["lab"], nc_star=v["nc_star_D_vs_A"], cstar_alpha2_F300=v["cstar_P_vs_D"](2, 300), cstar_alpha2_F100=v["cstar_P_vs_D"](2, 100), alpha_star_c2_F300=v["alpha_star"](2, 300), alpha_star_c1_F300=v["alpha_star"](1, 300)) for m, v in th.items()}
# ---- best-policy map and figures
m0 = "Qwen3-8B-Base"; E0 = ECON[m0]
cs = np.logspace(-2, 1.5, 120); Fs = np.logspace(0, 4, 120); labs = ["A", "S", "D", "P", "F"]; sym = {"A": 0, "S": 1, "D": 2, "P": 3, "F": 4}
fig, axs = plt.subplots(1, 3, figsize=(10.5, 3.3), sharey=True)
for ax, alpha in zip(axs, (0.5, 2, 8)):
    Z = np.array([[sym[best(E0, alpha, c, Fc)] for c in cs] for Fc in Fs])
    ax.contourf(cs, Fs, Z, levels=np.arange(-0.5, 5.5, 1), colors=["#ffffff", "#e0e0e0", "#b8b8b8", "#808080", "#404040"])
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_title(f"events per year α = {alpha}", fontsize=9); ax.set_xlabel("labor per statement c (in units of ℓ)", fontsize=8)
    for lab, (x, y) in {"D": (0.02, 8), "P": (0.15, 60), "F": (0.011, 3000)}.items(): pass
axs[0].set_ylabel("cost of full consolidation F (in units of ℓ)", fontsize=8)
import matplotlib.patches as mp
handles = [mp.Patch(facecolor=c_, edgecolor="k", label=n) for c_, n in zip(["#ffffff", "#e0e0e0", "#b8b8b8", "#808080", "#404040"], ["A amend only", "S stream-scoped", "D dependency-scoped", "P pattern listing", "F full listing"])]
fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=8, frameon=False); fig.tight_layout(rect=(0, 0.1, 1, 1)); fig.savefig(SD + "final/figs/fig_map.jpg", dpi=300); plt.close(fig)
# which policies ever optimal
opt = collections.Counter(best(E0, a, c, Fc) for a in (0.5, 2, 8) for c in cs for Fc in Fs); OUT["map_counts"] = dict(opt)
# cost vs alpha
fig, ax = plt.subplots(figsize=(4.2, 3.2)); als = np.logspace(-1, 1.3, 60)
for j, ls, mk in (("A", ":", "o"), ("D", "--", "s"), ("P", "-", "^"), ("F", "-.", "x")):
    ax.plot(als, [phi(E0[j], a, 2.0, 300) for a in als], ls, marker=mk, markevery=8, color="k", label={"A": "A amend only", "D": "D dependency-scoped", "P": "P pattern listing", "F": "F full listing"}[j], lw=1.2, ms=4)
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("amendment events per year α", fontsize=8); ax.set_ylabel("cost per year (in units of ℓ)", fontsize=8); ax.legend(fontsize=7, frameon=False); fig.tight_layout(); fig.savefig(SD + "final/figs/fig_alpha.jpg", dpi=300); plt.close(fig)
# twin figure
fig, ax = plt.subplots(figsize=(4.6, 3.2)); w = 0.25; xs = np.arange(3)
cats = [("with_twin", "twin listed", "///"), ("no_twin", "no twin listed", "..."), ("dependent", "derived dependent", "xxx")]
for k, (c_, lab, h) in enumerate(cats):
    vals = [OUT["twin"][m]["Amend only"][c_][0] for m in MODELS]; ax.bar(xs + (k - 1) * w, vals, w, label=lab, color="white", edgecolor="k", hatch=h)
ax.set_xticks(xs); ax.set_xticklabels(list(MODELS), fontsize=8); ax.set_ylabel("share answered with the new value", fontsize=8); ax.set_ylim(0, 1.05); ax.legend(fontsize=7, frameon=False, loc="upper right", bbox_to_anchor=(1, 1.18), ncol=3); fig.tight_layout(); fig.savefig(SD + "final/figs/fig_twin.jpg", dpi=300); plt.close(fig)
# pattern listing figure: currency vs extra labor
fig, ax = plt.subplots(figsize=(4.4, 3.2)); mk = {"Qwen2.5-7B": "o", "Qwen3-8B-Base": "s", "Olmo-3-7B": "^"}
for m in MODELS:
    pts = sorted([(OUT["pat"][m][f"Pattern listing|{k}"]["extra"], OUT["pat"][m][f"Pattern listing|{k}"]["cur_m"]) for k in (.1, .25, .5, .75)])
    ax.plot([p[0] for p in pts], [p[1] for p in pts], "-", marker=mk[m], color="k", lw=1, ms=5, label=f"{m}: pattern listing")
    ax.plot([0], [OUT["pat"][m]["Dependency-scoped|0.5"]["cur_m"]], marker=mk[m], mfc="white", color="k", ls="none", ms=5)
    ax.plot([ECON[m]["F"]["lab"]], [1.0], marker=mk[m], mfc="k", color="k", ls="none", ms=6)
ax.set_xlabel("additional listed statements per amendment", fontsize=8); ax.set_ylabel("share of amended provisions answered correctly", fontsize=8); ax.set_ylim(0.7, 1.02)
ax.text(2, 0.74, "open: dependency-scoped, no extra listing\nfilled: full listing", fontsize=7); ax.legend(fontsize=7, frameon=False, loc="lower right"); fig.tight_layout(); fig.savefig(SD + "final/figs/fig_pat.jpg", dpi=300); plt.close(fig)
def conv(o):
    if isinstance(o, dict): return {str(k): conv(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [conv(x) for x in o]
    if isinstance(o, (np.floating, np.integer)): return float(o)
    return o
json.dump(conv(OUT), open(SD + "final/analysis.json", "w"), indent=1)
print(json.dumps(conv({k: OUT[k] for k in ("bank", "th", "map_counts")}), indent=1)[:3500])
for m in MODELS:
    print(m, "twin(A):", {k: (round(v[0], 2), v[1]) for k, v in OUT["twin"][m]["Amend only"].items() if k in ("with_twin", "no_twin", "dependent")}, "logit sim/twin", [round(OUT["twin"][m]["Amend only"]["logit"][k][0], 2) for k in ("sim", "twin")])
