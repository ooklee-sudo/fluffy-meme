"""Experiment 2: influencer-concentrated vs. distributed seeding (equal exposure budget),
with Hawkes (exponential kernel) fits to the campaign event times."""
import argparse, json, os, warnings, numpy as np
warnings.filterwarnings('ignore')
from scipy import optimize, stats
from sim import Sim, build_network

ap = argparse.ArgumentParser()
ap.add_argument("--reps", type=int, default=20)
ap.add_argument("--n", type=int, default=2000)
ap.add_argument("--k", type=int, default=3, help="# influencers in the concentrated arm")
ap.add_argument("--horizon", type=float, default=48.0)
ap.add_argument("--start-hour", type=float, default=18.0)
ap.add_argument("--out", default="results/seeding.json")
ap.add_argument("--provider", default="surrogate", choices=["surrogate", "surrogate-table", "llm"])
a = ap.parse_args()


def make_provider():
    if a.provider == "surrogate":
        return None
    import llm_table
    return llm_table.llm_provider() if a.provider == "llm" else llm_table.surrogate_table_provider()



def hawkes_fit(t, T):
    """MLE of mu, alpha, beta for lambda(t)=mu+alpha*sum beta*exp(-beta(t-ti)); branching n=alpha."""
    t = np.sort(t)
    if len(t) < 20:
        return (np.nan, np.nan, np.nan)
    def nll(p):
        mu, al, be = np.exp(p[0]), 1 / (1 + np.exp(-p[1])), np.exp(p[2])
        R = np.zeros(len(t)); 
        d = np.exp(-be * np.diff(t))
        for i in range(1, len(t)):
            R[i] = d[i - 1] * (1 + R[i - 1])
        ll = np.log(mu + al * be * R).sum() - mu * T - al * (1 - np.exp(-be * (T - t))).sum()
        return -ll
    best = None
    for b0 in (0.5, 2.0):
        r = optimize.minimize(nll, [np.log(len(t) / T), 0.0, np.log(b0)], method="Nelder-Mead",
                              options=dict(maxiter=400, xatol=1e-3, fatol=1e-3))
        if best is None or r.fun < best.fun:
            best = r
    p = best.x
    return (float(np.exp(p[0])), float(1 / (1 + np.exp(-p[1]))), float(np.exp(p[2])))


def metrics(s):
    ev = [e for e in s.events if e[5] and e[2] in ("seed", "retweet", "comment")]
    adopters = {e[1] for e in ev if e[2] != "seed"}
    times = np.array([e[0] for e in ev if e[2] != "seed"])
    n = s.n
    final = len(adopters)
    first = {}
    for e in ev:
        if e[2] != "seed" and e[1] not in first:
            first[e[1]] = e[0]
    ft = np.sort(list(first.values()))
    t50 = float(ft[int(np.ceil(0.5 * final)) - 1]) if final else np.nan
    t10 = float(ft[int(np.ceil(0.1 * final)) - 1]) if final else np.nan
    n_ev = len(ev) - sum(1 for e in ev if e[2] == "seed")
    mu, al, be = hawkes_fit(times, s.T)
    return dict(adopters=final, reach=len(s.exposed), events=n_ev, t10=t10, t50=t50,
                hawkes_branching=al, hawkes_beta=be, adopt_frac=final / n)


arms = ["none", "influencer", "distributed", "random_k"]


def one_rep(r):
    followers = build_network(a.n, 3, np.random.default_rng(1000 + r))
    deg = np.array([len(f) for f in followers])
    inf = [int(i) for i in np.argsort(-deg)[:a.k]]
    budget = int(deg[inf].sum())
    rng = np.random.default_rng(5000 + r)
    pool = [int(i) for i in rng.permutation(a.n) if i not in inf]
    dist, tot = [], 0
    for i in pool:
        if tot >= budget:
            break
        dist.append(i); tot += deg[i]
    seeds = dict(none=[], influencer=inf, distributed=dist, random_k=pool[:a.k])
    res = {}
    for arm in arms:
        s = Sim(n=a.n, horizon=a.horizon, start_hour=a.start_hour, seed=r, network_seed=1000 + r,
                followers=followers, provider=make_provider())
        s.seed_campaign(seeds[arm])
        s.run()
        m = metrics(s); m["n_seeds"] = len(seeds[arm]); m["seed_reach"] = int(sum(deg[i] for i in seeds[arm]))
        res[arm] = m
    return res


if __name__ == "__main__":
    from multiprocessing import Pool
    with Pool(4) as p:
        reps = p.map(one_rep, range(a.reps))
    out = {k: [r[k] for r in reps] for k in arms}
    for r, x in enumerate(reps):
        print(r, {k: (x[k]["adopters"], x[k]["n_seeds"]) for k in arms}, flush=True)

    summ = {}
    for arm in arms:
        summ[arm] = {k: float(np.nanmean([x[k] for x in out[arm]])) for k in out[arm][0]}
        summ[arm]["adopters_sd"] = float(np.std([x["adopters"] for x in out[arm]], ddof=1))
    tests = {}
    for m in ["adopters", "reach", "t50", "t10", "hawkes_branching"]:
        for b in ["distributed", "random_k"]:
            x = np.array([o[m] for o in out["influencer"]]); y = np.array([o[m] for o in out[b]])
            ok = ~(np.isnan(x) | np.isnan(y))
            if ok.sum() > 3:
                tests[f"{m}: influencer vs {b}"] = dict(diff=float(np.mean(x[ok] - y[ok])),
                                                      p_wilcoxon=float(stats.wilcoxon(x[ok], y[ok]).pvalue) if np.any(x[ok] != y[ok]) else 1.0)
    os.makedirs("results", exist_ok=True)
    json.dump(dict(summary=summ, tests=tests, raw=out, args=vars(a)), open(a.out, "w"), indent=1, default=float)
    print(json.dumps(summ, indent=1)); print(json.dumps(tests, indent=1))
    