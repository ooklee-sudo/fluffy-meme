"""Confirmatory analysis for the holdout test (see PREREGISTRATION.md, section 3).

Usage:
  python confirmatory_analysis.py releases.csv launches.csv exposure.csv [--reps 999] [--seed 20261101]

releases.csv : repo,published_at[,is_hotfix]   (ISO date or datetime; draft and prerelease already excluded;
               is_hotfix = 1 if only the patch component changed and published within 7 days of the previous release)
launches.csv : launch_id,announce_date,launch_type   (launch_type in open_weights/openai/anthropic/google)
exposure.csv : repo,launch_type,exposed             (frozen two-coder consensus)

Primary statistic (all releases, all unexposed controls): per launch, the difference between unexposed and exposed
repositories in the mean of min(days from announcement to next release, 28), among repositories that released at
least once in the 90 days before the announcement; averaged over launches with equal weight. Reported as
(unexposed - exposed), so a positive value means exposed repositories release sooner.
Inference: placebo randomization. Each launch date is replaced by a date at least 14 days from every real launch;
launch type, and so exposure, is kept; the statistic is recomputed; p = share of placebo statistics at least as far
from the placebo mean as the observed one.
Secondary (reported, not used for the confirmation decision): share releasing within 1 day (exposed - unexposed),
regular releases only (needs is_hotfix), and a version that drops controls exposed to another launch within 28 days.
"""
import argparse, bisect, csv, datetime as dt, random, statistics

H = 28
LOOKBACK = 90
BUFFER = 14


def day(s):
    return dt.date.fromisoformat(s[:10])


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load(rel_path, launch_path, exp_path):
    rel = {}
    for r in read(rel_path):
        rel.setdefault(r["repo"], []).append((day(r["published_at"]), int(r.get("is_hotfix") or 0)))
    for v in rel.values():
        v.sort()
    launches = [(r["launch_id"], day(r["announce_date"]), r["launch_type"]) for r in read(launch_path)]
    exposed = {(r["repo"], r["launch_type"]): int(r["exposed"]) for r in read(exp_path)}
    return rel, launches, exposed


class Stat:
    def __init__(self, rel, launches, exposed, regular_only=False, drop_contaminated=False):
        self.rel = {k: [d for d, h in v if not (regular_only and h)] for k, v in rel.items()}
        self.launches = launches
        self.exposed = exposed
        self.drop = drop_contaminated
        self.repos = sorted({r for r, _ in exposed})
        self.first = min(d for v in self.rel.values() for d in v)
        self.last = max(d for v in self.rel.values() for d in v)
        self.all_dates = sorted({d for _, d, _ in launches})

    def observable(self, d):
        return d - dt.timedelta(days=LOOKBACK) >= self.first and d + dt.timedelta(days=H) <= self.last

    def days_to_next(self, repo, d):
        v = self.rel[repo]
        i = bisect.bisect_left(v, d)
        t = (v[i] - d).days if i < len(v) else H
        return min(t, H)

    def had_recent(self, repo, d):
        v = self.rel[repo]
        i = bisect.bisect_left(v, d)
        return i > 0 and (d - v[i - 1]).days <= LOOKBACK

    def contaminated(self, repo, d, own_type, dates_types):
        return any(0 <= (d2 - d).days <= H and t2 != own_type and self.exposed.get((repo, t2), 0) == 1
                   for d2, t2 in dates_types)

    def one_launch(self, d, ltype, dates_types):
        ex, un, ex1, un1 = [], [], [], []
        for repo in self.repos:
            if repo not in self.rel or not self.had_recent(repo, d):
                continue
            t = self.days_to_next(repo, d)
            if self.exposed.get((repo, ltype), 0) == 1:
                ex.append(t); ex1.append(t <= 1)
            else:
                if self.drop and self.contaminated(repo, d, ltype, dates_types):
                    continue
                un.append(t); un1.append(t <= 1)
        if not ex or not un:
            return None
        return (statistics.fmean(un) - statistics.fmean(ex),
                statistics.fmean(ex1) - statistics.fmean(un1))

    def compute(self, dates_types):
        res = [self.one_launch(d, t, dates_types) for d, t in dates_types if self.observable(d)]
        res = [r for r in res if r is not None]
        if not res:
            return None
        return statistics.fmean(r[0] for r in res), statistics.fmean(r[1] for r in res), len(res)

    def placebo_dates(self, rng):
        lo = self.first + dt.timedelta(days=LOOKBACK)
        hi = self.last - dt.timedelta(days=H)
        pool = [lo + dt.timedelta(days=i) for i in range((hi - lo).days + 1)]
        pool = [p for p in pool if all(abs((p - d).days) >= BUFFER for d in self.all_dates)]
        return pool


def run(stat, reps, seed):
    real = [(d, t) for _, d, t in stat.launches]
    obs = stat.compute(real)
    if obs is None:
        return None
    rng = random.Random(seed)
    pool = stat.placebo_dates(rng)
    p0, p1 = [], []
    for _ in range(reps):
        fake = [(rng.choice(pool), t) for _, t in real]
        r = stat.compute(fake)
        if r:
            p0.append(r[0]); p1.append(r[1])
    out = {"n_launches_used": obs[2], "restricted_mean_diff_days": obs[0], "within_1day_diff": obs[1],
           "placebo_n": len(p0)}
    for name, o, p in (("restricted_mean", obs[0], p0), ("within_1day", obs[1], p1)):
        m = statistics.fmean(p)
        out[f"{name}_placebo_mean"] = m
        out[f"{name}_p"] = sum(abs(x - m) >= abs(o - m) for x in p) / len(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("releases"); ap.add_argument("launches"); ap.add_argument("exposure")
    ap.add_argument("--reps", type=int, default=999)
    ap.add_argument("--seed", type=int, default=20261101)
    a = ap.parse_args()
    rel, launches, exposed = load(a.releases, a.launches, a.exposure)
    has_flag = any(h for v in rel.values() for _, h in v)
    variants = [("PRIMARY (all releases, all controls)", {}),
                ("secondary: drop contaminated controls", {"drop_contaminated": True})]
    if has_flag:
        variants += [("secondary: regular releases only", {"regular_only": True}),
                     ("secondary: regular only + drop contaminated", {"regular_only": True, "drop_contaminated": True})]
    for name, kw in variants:
        r = run(Stat(rel, launches, exposed, **kw), a.reps, a.seed)
        print(f"\n== {name}")
        if r is None:
            print("no usable launches"); continue
        for k, v in r.items():
            print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")


if __name__ == "__main__":
    main()
