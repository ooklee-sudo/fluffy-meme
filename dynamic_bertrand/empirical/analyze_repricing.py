"""Exploratory test of the repricing-frequency prediction on public LLM API list prices.

Prediction taken from the model (Sections 7.2-7.5 of the manuscript): with price commitment (slower repricing) prices are higher
and price paths have restoration jumps.  Here: within the same model and month, do hosts that reprice more often post lower prices?

Data: price_panel.csv.gz (monthly snapshots of LiteLLM's community-maintained price file; see build_price_panel.py).
Unit: provider x open-weight model family x month.  Outcome: log of the provider's blended price relative to the cross-provider
median of the same family in the same month.  Regressor: the provider's monthly repricing rate on all its OTHER model families
(leave-one-family-out, so that the regressor is not mechanically related to the outcome).

This is exploratory.  List prices are not transaction prices, the file is community-maintained (price changes can be recorded
late, and more popular providers are probably updated faster), and the number of providers is small.

python analyze_repricing.py    # writes ../results/empirical_repricing.json and ../results/empirical_repricing.png
"""
import collections
import csv
import gzip
import json
import os
import re
import statistics as st

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
FAMILIES = [("llama-3.1-70b", r"llama-?3[._]1-?70b"), ("llama-3.1-8b", r"llama-?3[._]1-?8b"), ("llama-3.3-70b", r"llama-?3[._]3-?70b"),
            ("llama-3-70b", r"llama-?3-?70b"), ("llama-3-8b", r"llama-?3-?8b"), ("mixtral-8x7b", r"mixtral-?8x7b"),
            ("qwen2.5-72b", r"qwen-?2[._]5-?72b"), ("deepseek-v3", r"deepseek-?v3(?![._]\d)"), ("deepseek-r1", r"deepseek-?r1(?!-?distill)"),
            ("llama-3.1-405b", r"llama-?3[._]1-?405b"), ("mistral-7b", r"mistral-?7b")]
HOST_TYPE = {"azure": "hyperscaler", "bedrock": "hyperscaler", "vertex_ai": "hyperscaler", "oci": "hyperscaler", "snowflake": "hyperscaler",
             "vercel_ai_gateway": "aggregator", "aihubmix": "aggregator", "openrouter": "aggregator", "llamagate": "aggregator"}
CHANGE = 0.005                      # a month-to-month blended-price change above 0.5% counts as a repricing


def provider(p):
    p = p.lower()
    for stem in ("bedrock", "vertex_ai", "azure"):
        if p.startswith(stem):
            return stem
    return p


def family(key):
    k = key.lower()
    if "distill" in k and "deepseek" in k:
        return None
    for name, pat in FAMILIES:
        if re.search(pat, k):
            if name == "llama-3-70b" and re.search(r"3[._][13]", k):
                continue
            return name
    return None


def blended(i, o):
    i = float(i) if i not in ("", None) else None
    o = float(o) if o not in ("", None) else None
    if i and o:
        return (3 * i + o) / 4
    return i or o


def run(change, rows):
    global CHANGE
    CHANGE = change
    months = sorted(set(r["month"] for r in rows))
    mi = {m: k for k, m in enumerate(months)}
    series = collections.defaultdict(dict)                       # (provider, model_key) -> month index -> blended price
    famof = {}
    for r in rows:
        if r["mode"] not in ("chat", "completion"):
            continue
        b = blended(r["input_per_m"], r["output_per_m"])
        if not b or b <= 0:
            continue
        key = (provider(r["provider"]), r["model_key"])
        series[key][mi[r["month"]]] = b
        famof[key] = family(r["model_key"])
    # ---- repricing events -----------------------------------------------------------------
    events = collections.defaultdict(list)                       # (provider, family-or-None) -> list of (pairs, changes, ups, downs)
    sawtooth = collections.defaultdict(lambda: [0, 0])           # provider -> [cut-then-raise within 6 months, price cuts]
    for (p, k), s in series.items():
        ms = sorted(s)
        pairs = ch = up = dn = 0
        last_cut = None
        for a, b in zip(ms, ms[1:]):
            if b != a + 1:
                continue
            pairs += 1
            d = s[b] / s[a] - 1
            if abs(d) > CHANGE:
                ch += 1
                if d > 0:
                    up += 1
                    if last_cut is not None and b - last_cut <= 6:
                        sawtooth[p][0] += 1
                else:
                    dn += 1
                    last_cut = b
                    sawtooth[p][1] += 1
        events[(p, famof[(p, k)])].append((pairs, ch, up, dn))
    prov_all = collections.defaultdict(lambda: np.zeros(4))
    for (p, f), L in events.items():
        for t in L:
            prov_all[p] += np.array(t, float)

    def rate(p, exclude=None):
        tot = np.zeros(4)
        for (pp, f), L in events.items():
            if pp == p and f != exclude:
                for t in L:
                    tot += np.array(t, float)
        return (tot[1] / tot[0], tot) if tot[0] >= 30 else (None, tot)

    # ---- descriptives by provider ----------------------------------------------------------
    desc = {}
    for p, v in prov_all.items():
        if v[0] >= 50:
            desc[p] = dict(type=HOST_TYPE.get(p, "specialist or model maker"), pairs=int(v[0]), repricing_rate=v[1] / v[0],
                           share_increases=(v[2] / v[1] if v[1] else None), sawtooth_per_cut=(sawtooth[p][0] / sawtooth[p][1] if sawtooth[p][1] else None))
    # ---- relative prices within family-month -----------------------------------------------
    cell = collections.defaultdict(lambda: collections.defaultdict(list))   # (family, month) -> provider -> prices
    for (p, k), s in series.items():
        f = famof[(p, k)]
        if f is None:
            continue
        for m, pr in s.items():
            cell[(f, m)][p].append(pr)
    obs = []                                                     # (provider, family, month, log relative price, loo rate)
    for (f, m), d in cell.items():
        if len(d) < 4:
            continue
        pp = {p: st.median(v) for p, v in d.items()}
        med = st.median(pp.values())
        for p, v in pp.items():
            r, _ = rate(p, exclude=f)
            if r is None:
                continue
            obs.append((p, f, m, float(np.log(v / med)), r))
    P = sorted(set(o[0] for o in obs))
    typ = lambda p: HOST_TYPE.get(p, "specialist or model maker")

    def fit(sub, controls):
        """Within family-month OLS of the log relative price on the repricing rate (and host-type dummies); provider-clustered SE."""
        provs = sorted(set(o[0] for o in sub))
        cm = collections.defaultdict(lambda: np.zeros(5))
        for p, f, m, y, r in sub:
            cm[(f, m)] += np.array([y, r, typ(p) == "hyperscaler", typ(p) == "aggregator", 1.0])
        rows_x, ys, gi = [], [], []
        for p, f, m, y, r in sub:
            c = cm[(f, m)]
            xs = [r - c[1] / c[4]] + ([float(typ(p) == "hyperscaler") - c[2] / c[4], float(typ(p) == "aggregator") - c[3] / c[4]] if controls else [])
            rows_x.append(xs); ys.append(y - c[0] / c[4]); gi.append(provs.index(p))
        X, Y, gi = np.array(rows_x), np.array(ys), np.array(gi)
        k = X.shape[1]
        XtX_inv = np.linalg.pinv(X.T @ X)
        beta = XtX_inv @ X.T @ Y
        resid = Y - X @ beta
        meat = np.zeros((k, k))
        for j in range(len(provs)):
            g = X[gi == j].T @ resid[gi == j]
            meat += np.outer(g, g)
        G, N = len(provs), len(Y)
        V = XtX_inv @ meat @ XtX_inv * (G / max(G - 1, 1)) * ((N - 1) / max(N - k, 1))
        prov_rate_ = {p: np.mean([o[4] for o in sub if o[0] == p]) for p in provs}
        rng = np.random.default_rng(7)
        perm = []
        for _ in range(1000):
            # permute rates across providers, within host type when type controls are included
            shuf = dict(prov_rate_)
            groups = collections.defaultdict(list)
            for p in provs:
                groups[typ(p) if controls else "all"].append(p)
            for g_, ps in groups.items():
                vals = rng.permutation([prov_rate_[p] for p in ps])
                for p, v in zip(ps, vals):
                    shuf[p] = v
            cm2 = collections.defaultdict(lambda: np.zeros(7))
            for p, f, m, y, r in sub:
                cm2[(f, m)] += np.array([shuf[p], typ(p) == "hyperscaler", typ(p) == "aggregator", 1.0, 0, 0, 0])
            Xp = []
            for p, f, m, y, r in sub:
                c = cm2[(f, m)]
                xs = [shuf[p] - c[0] / c[3]] + ([float(typ(p) == "hyperscaler") - c[1] / c[3], float(typ(p) == "aggregator") - c[2] / c[3]] if controls else [])
                Xp.append(xs)
            Xp = np.array(Xp)
            bp = np.linalg.pinv(Xp.T @ Xp) @ Xp.T @ Y
            perm.append(float(bp[0]))
        sd = float(np.std(list(prov_rate_.values())))
        return dict(n_obs=len(sub), n_providers=G, coef=float(beta[0]), se=float(np.sqrt(V[0, 0])), per_sd=float(beta[0] * sd), sd_rate=sd,
                    perm_p=float(np.mean(np.abs(perm) >= abs(beta[0]))))

    variants = {
        "baseline": fit(obs, False),
        "host-type controls": fit(obs, True),
        "specialists only": fit([o for o in obs if typ(o[0]) == "specialist or model maker"], False),
        "excluding aggregators": fit([o for o in obs if typ(o[0]) != "aggregator"], True),
    }
    gap = {}
    for t_ in ("hyperscaler", "aggregator", "specialist or model maker"):
        v = [o[3] for o in obs if typ(o[0]) == t_]
        gap[t_] = dict(n=len(v), median_log_rel_price=float(np.median(v)), mean_log_rel_price=float(np.mean(v)))
    prov_rate = {p: np.mean([o[4] for o in obs if o[0] == p]) for p in P}
    return dict(change_threshold=change, n_obs=len(obs), n_providers=len(P), providers=P, months=[months[0], months[-1]], variants=variants,
                host_type_gap=gap, descriptives=desc,
                overall=dict(share_changes_that_are_increases=float(sum(v[2] for v in prov_all.values()) / sum(v[1] for v in prov_all.values())),
                             monthly_repricing_rate=float(sum(v[1] for v in prov_all.values()) / sum(v[0] for v in prov_all.values()))),
                _obs=obs, _prov_rate=prov_rate)


def main():
    rows = list(csv.DictReader(gzip.open(os.path.join(HERE, "price_panel.csv.gz"), "rt")))
    results = {}
    for ch in (0.005, 0.02, 0.05):
        r = run(ch, rows)
        results[str(ch)] = {k: v for k, v in r.items() if not k.startswith("_")}
        if ch == 0.005:
            main_r = r
        print(f"change threshold {ch}: monthly rate {r['overall']['monthly_repricing_rate']:.4f}, share increases {r['overall']['share_changes_that_are_increases']:.2f}")
        for name, v in r["variants"].items():
            print(f"   {name:24s} n={v['n_obs']:5d} providers={v['n_providers']:3d} coef={v['coef']:8.2f} se={v['se']:7.2f} per-SD={v['per_sd']:6.3f} perm-p={v['perm_p']:.3f}")
    json.dump(results, open(os.path.join(RES, "empirical_repricing.json"), "w"), indent=1, default=float)
    print(json.dumps(main_r["host_type_gap"], indent=1))
    figure(main_r)


def figure(r):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    obs, prov_rate = r["_obs"], r["_prov_rate"]
    P = sorted(prov_rate)
    mean_y = {p: np.mean([o[3] for o in obs if o[0] == p]) for p in P}
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    colors = {"hyperscaler": "#c9733a", "aggregator": "#8a8a8a", "specialist or model maker": "#3b6ea8"}
    for p in P:
        t_ = HOST_TYPE.get(p, "specialist or model maker")
        ax.scatter(prov_rate[p], mean_y[p], color=colors[t_], s=28)
        ax.annotate(p.replace("_ai", ""), (prov_rate[p], mean_y[p]), fontsize=6, xytext=(3, 2), textcoords="offset points")
    ax.axhline(0, color="#bbb", lw=.8)
    ax.set_xlabel("provider's monthly repricing rate (other model families)")
    ax.set_ylabel("mean log price relative to family-month median")
    ax.spines[["top", "right"]].set_visible(False)
    for t_, c in colors.items():
        ax.scatter([], [], color=c, label=t_)
    ax.legend(frameon=False, fontsize=7)
    fig.savefig(os.path.join(RES, "empirical_repricing.png"), dpi=200, bbox_inches="tight")


if __name__ == "__main__":
    main()
