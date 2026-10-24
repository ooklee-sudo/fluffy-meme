"""Event-driven rule-based social-media simulator (Section 4 of the manuscript).

Agents act at times drawn from an inhomogeneous Poisson process whose intensity is a persona-specific circadian
baseline plus decaying stimuli (Eqs. 4-5). Exposure of followers to a post depends on the author's audience size
through the engagement elasticity beta (Eq. 1). There is no language model in the simulator.

Public entry point: run(cfg, plan, seed) -> dict with the adoption times and the summaries used in the paper.
"""
import heapq
import math
import random
from dataclasses import dataclass, field, replace

import numpy as np

# ----------------------------------------------------------------------------- configuration

PERSONAS = {  # name: (share, base rate lambda0 (1/h), gain g, peak hour, P(post, comment, retweet, like))
    "early_adopter": (0.15, 0.45, 1.3, 22, (.30, .20, .25, .25)),
    "cynic": (0.15, 0.30, 0.8, 23, (.20, .45, .05, .30)),
    "trend_follower": (0.25, 0.40, 1.2, 21, (.15, .15, .40, .30)),
    "lurker": (0.30, 0.12, 0.6, 21, (.05, .10, .10, .75)),
    "news_junkie": (0.15, 0.70, 1.0, 20, (.40, .20, .20, .20)),
}
EMOTIONS = (("excited", .20, 0.8), ("angry", .15, 0.6), ("happy", .30, 0.4), ("indifferent", .35, -0.6))


@dataclass(frozen=True)
class Config:
    n_agents: int = 2000
    follows_per_new_agent: int = 3
    n_topics: int = 5
    dirichlet_conc: float = 0.4
    beta: float = 0.0                 # engagement elasticity
    base_view_prob: float = 0.5
    view_floor: int = 10
    comment_visibility: float = 0.4
    feed_capacity: int = 40
    recency_tau: float = 2.0          # hours, recency weight for comment/retweet targets
    kappa: float = 0.16               # stimulus scale
    tau: float = 1.0                  # stimulus decay (hours)
    s_max: float = 3.0                # stimulus cap
    rate_sigma: float = 0.4
    chrono_sigma: float = 1.5
    warmup: float = 18.0              # hours before injection
    horizon: float = 48.0             # hours observed after injection
    injection_hour: float = 18.0      # clock time of injection
    scheduler: str = "event"          # event | circadian | hpp | polling
    rate_multiplier: float = 1.77     # volume matching for the alternative schedulers
    top_share_excluded: float = 0.05  # distributed seeds drawn from outside the top 5% by followers


# ----------------------------------------------------------------------------- world construction

def _circ_dist(a, b):
    d = abs(a - b) % 24.0
    return min(d, 24.0 - d)


def circadian_table(chrono):
    """Mean-one activity profile at 15-minute resolution: 0.12 + evening Gaussian at the chronotype (sd 2.2 h)
    + 0.45 x midday Gaussian at 12.5 h (sd 1.8 h)."""
    h = np.arange(96) / 4.0
    d1 = np.minimum(np.abs(h - chrono) % 24, 24 - np.abs(h - chrono) % 24)
    d2 = np.minimum(np.abs(h - 12.5) % 24, 24 - np.abs(h - 12.5) % 24)
    raw = 0.12 + np.exp(-0.5 * (d1 / 2.2) ** 2) + 0.45 * np.exp(-0.5 * (d2 / 1.8) ** 2)
    return raw / raw.mean()


def build_world(cfg, seed):
    rng = np.random.default_rng(seed)
    n = cfg.n_agents
    followers = [[] for _ in range(n)]
    indeg = np.ones(n)  # +1 smoothing so that new nodes can be followed
    # preferential attachment on in-degree
    for i in range(cfg.follows_per_new_agent, n):
        p = indeg[:i] / indeg[:i].sum()
        targets = rng.choice(i, size=cfg.follows_per_new_agent, replace=False, p=p)
        for t in targets:
            followers[t].append(i)
            indeg[t] += 1
    names = list(PERSONAS)
    shares = np.array([PERSONAS[k][0] for k in names])
    persona = rng.choice(len(names), size=n, p=shares / shares.sum())
    lam0 = np.array([PERSONAS[names[p]][1] for p in persona]) * np.exp(
        rng.normal(-cfg.rate_sigma ** 2 / 2, cfg.rate_sigma, n))
    gain = np.array([PERSONAS[names[p]][2] for p in persona])
    chrono = np.array([PERSONAS[names[p]][3] for p in persona]) + rng.normal(0, cfg.chrono_sigma, n)
    probs = np.array([PERSONAS[names[p]][4] for p in persona])
    interest = rng.dirichlet(np.full(cfg.n_topics, cfg.dirichlet_conc), size=n)
    tables = np.stack([circadian_table(c) for c in chrono])
    return dict(n=n, followers=followers, nfol=np.array([len(f) for f in followers]), persona=persona, lam0=lam0,
                gain=gain, probs=probs, interest=interest, tables=tables, cmax=tables.max(axis=1))


def urge_rating(hour, emotion_bonus, n_recent, level, notification):
    """Rule-based urge function (Online Appendix A)."""
    leisure = 1.0 if (hour >= 19 or hour < 1) else (0.5 if 11 <= hour < 14 else 0.0)
    val = 1.0 + 1.0 * leisure + 0.4 * min(n_recent, 3) + 0.5 * level + 0.8 * notification + emotion_bonus
    return min(max(val, 0.0), 5.0)


def relevance(interest_weight):
    """Returns (level in {0,1,2}, relevance weight r in {0.25, 0.5, 0.75})."""
    if interest_weight < 0.10:
        return 0, 0.25
    if interest_weight < 0.30:
        return 1, 0.50
    return 2, 0.75


# ----------------------------------------------------------------------------- one simulation run

def run(cfg, seeds, seed, record_events=False):
    """Simulate warm-up + campaign. `seeds` is the list of agent ids that publish the campaign post at injection.
    Returns dict(adopt_times=sorted list of hours after injection, n_events=int)."""
    W = build_world(cfg, seed)
    rnd = random.Random(seed * 7919 + 13)
    n = W["n"]
    clock0 = (cfg.injection_hour - cfg.warmup) % 24.0
    t_end = cfg.warmup + cfg.horizon

    lam0, cmax, tables, gain = W["lam0"], W["cmax"], W["tables"], W["gain"]
    mult = cfg.rate_multiplier if cfg.scheduler != "event" else 1.0
    A = [0.0] * n          # uncapped stimulus sum at time A_t
    A_t = [0.0] * n
    version = [0] * n
    feed = [[] for _ in range(n)]
    # items: topic, time, campaign flag, author
    it_topic, it_time, it_camp, it_author = [], [], [], []
    adopted = [False] * n
    seed_set = set(seeds)
    adopt_times = []
    heap = []
    counter = 0
    n_events = 0
    emo_p = [e[1] for e in EMOTIONS]
    emo_b = [e[2] for e in EMOTIONS]
    nfol = W["nfol"]
    followers = W["followers"]
    interest = W["interest"]
    probs = W["probs"]
    view_scale = [cfg.base_view_prob * (max(int(f), cfg.view_floor) / cfg.view_floor) ** (-cfg.beta) for f in nfol]
    phase = [rnd.random() for _ in range(n)]

    def hour_of(t):
        return (t + clock0) % 24.0

    def circ(i, t):
        return tables[i][int(hour_of(t) * 4) % 96]

    def stim(i, t):
        a = A[i] * math.exp(-(t - A_t[i]) / cfg.tau)
        return min(cfg.s_max, a)

    def next_time(i, t):
        """Next action time of agent i after t under the configured scheduler."""
        if cfg.scheduler == "hpp":
            return t + rnd.expovariate(lam0[i] * mult)
        if cfg.scheduler == "polling":
            period = 1.0 / (lam0[i] * mult)
            k = math.floor((t - phase[i] * period) / period) + 1
            nt = phase[i] * period + k * period
            return nt if nt > t + 1e-9 else nt + period
        if cfg.scheduler == "circadian":
            bound = lam0[i] * mult * cmax[i]
            while True:
                t += rnd.expovariate(bound)
                if t > t_end:
                    return math.inf
                if rnd.random() * bound <= lam0[i] * mult * circ(i, t):
                    return t
        # event-driven: lambda(t) = lam0 c(t) + S(t); S decays, so the bound at the start time holds until the next stimulus
        bound = lam0[i] * cmax[i] + stim(i, t)
        while True:
            t += rnd.expovariate(bound)
            if t > t_end:
                return math.inf
            if rnd.random() * bound <= lam0[i] * circ(i, t) + stim(i, t):
                return t

    def schedule(i, t):
        nonlocal counter
        version[i] += 1
        nt = next_time(i, t)
        if nt < math.inf:
            counter += 1
            heapq.heappush(heap, (nt, counter, i, version[i]))

    def add_stimulus(i, t, rating, r):
        A[i] = A[i] * math.exp(-(t - A_t[i]) / cfg.tau) + cfg.kappa * gain[i] * rating * r
        A_t[i] = t
        if cfg.scheduler == "event":
            schedule(i, t)  # the pending event is redrawn (exact: Poisson process is memoryless)

    def publish(item, author, t, vis):
        pv = view_scale[author] * vis
        for j in followers[author]:
            if rnd.random() < pv:
                f = feed[j]
                f.append(item)
                if len(f) > cfg.feed_capacity:
                    del f[0]
                w = interest[j][it_topic[item]]
                level, r = relevance(w)
                if cfg.scheduler == "event":
                    n_recent = sum(1 for x in f if it_time[x] >= t - 1.0 and interest[j][it_topic[x]] >= 0.10)
                    emo = rnd.choices(emo_b, emo_p)[0]
                    rating = urge_rating(hour_of(t), emo, n_recent, level, 0)
                    add_stimulus(j, t, rating, r)

    def notify(author, t):
        if cfg.scheduler == "event":
            emo = rnd.choices(emo_b, emo_p)[0]
            rating = urge_rating(hour_of(t), emo, 0, 1, 1)
            add_stimulus(author, t, rating, 0.50)

    def new_item(topic, t, camp, author):
        it_topic.append(topic); it_time.append(t); it_camp.append(camp); it_author.append(author)
        return len(it_topic) - 1

    # initial schedule
    for i in range(n):
        schedule(i, 0.0)
    injected = False
    while heap:
        t, _, i, v = heapq.heappop(heap)
        if cfg.scheduler == "event" and v != version[i]:
            continue
        if not injected and t >= cfg.warmup:
            injected = True
            for s in seeds:
                it = new_item(0, cfg.warmup, True, s)
                publish(it, s, cfg.warmup, 1.0)
        if t > t_end:
            break
        n_events += 1 if (t >= cfg.warmup or True) else 0
        # choose action
        pr = probs[i]
        u = rnd.random()
        act = 0 if u < pr[0] else 1 if u < pr[0] + pr[1] else 2 if u < pr[0] + pr[1] + pr[2] else 3
        if act != 0:
            f = feed[i]
            cand, wts = [], []
            for x in f:
                if it_author[x] == i:
                    continue
                cand.append(x)
                wts.append(interest[i][it_topic[x]] * math.exp(-(t - it_time[x]) / cfg.recency_tau))
            if not cand or sum(wts) <= 0:
                act = 0
            else:
                tgt = rnd.choices(cand, wts)[0]
        if act == 0:
            topic = rnd.choices(range(cfg.n_topics), interest[i])[0]
            it = new_item(topic, t, False, i)
            publish(it, i, t, 1.0)
        elif act in (1, 2):
            camp = it_camp[tgt]
            it = new_item(it_topic[tgt], t, camp, i)
            publish(it, i, t, cfg.comment_visibility if act == 1 else 1.0)
            notify(it_author[tgt], t)
            if camp and t >= cfg.warmup and not adopted[i] and i not in seed_set:
                adopted[i] = True
                adopt_times.append(t - cfg.warmup)
        # likes: no spread, no notification
        # next action of this agent
        if cfg.scheduler == "event":
            schedule(i, t)
        else:
            version[i] += 1
            nt = next_time(i, t)
            if nt < math.inf:
                counter += 1
                heapq.heappush(heap, (nt, counter, i, version[i]))
    adopt_times.sort()
    return dict(adopt_times=adopt_times, n_events=n_events, n_followers=W["nfol"], world=W)


# ----------------------------------------------------------------------------- plans

def seed_plan(W, plan, rng, cost_c0=0.0, cost_gamma=1.0, k_hybrid=0, top_share=0.05):
    """Return list of seed ids. plan: 'concentrated' | 'distributed' | 'hybrid' (k largest + ordinary accounts)."""
    nfol = W["nfol"]
    order = np.argsort(-nfol, kind="stable")
    cost = lambda f: cost_c0 + max(float(f), 1.0) ** cost_gamma  # accounts without followers cost one follower-equivalent
    budget = sum(cost(nfol[j]) for j in order[:3])
    if plan == "concentrated":
        return [int(j) for j in order[:3]]
    n_top = int(math.ceil(top_share * len(nfol)))
    pool = [int(j) for j in order[n_top:]]
    rng.shuffle(pool)
    seeds, spent = [], 0.0
    if plan == "hybrid":
        for j in order[:k_hybrid]:
            seeds.append(int(j)); spent += cost(nfol[j])
    for j in pool:
        c = cost(nfol[j])
        if spent + c > budget:
            break
        seeds.append(j); spent += c
    return seeds


# ----------------------------------------------------------------------------- summaries

def cumulative_at(adopt_times, hours):
    a = np.asarray(adopt_times)
    return [int((a <= h).sum()) for h in hours]


def discounted_reach(adopt_times, delta):
    a = np.asarray(adopt_times)
    return float(np.exp(-delta * a).sum())


def t50(adopt_times):
    if not adopt_times:
        return float("nan")
    return float(adopt_times[(len(adopt_times) + 1) // 2 - 1])
