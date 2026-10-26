"""Implementation of the Poisson-SNS scheduler comparison (Study 1) from the manuscript specification.

Only the pieces needed for Study 1 are included: platform, personas, IPP / HPP / polling schedulers, and a
deterministic surrogate intensity oracle. The surrogate's functional form is not given in the manuscript; it is a
monotone logistic function whose intercept is calibrated so that a 24 h, 800-agent IPP run produces about 14,830
events, the figure reported in Section III-E.
"""
import heapq, math
from collections import deque
import numpy as np

PERSONAS = [  # name, share, base rate, gain, peak hour, P(post, comment, retweet, like)
    ('early_adopter', .15, .45, 1.3, 22, (.30, .20, .25, .25)),
    ('cynic',         .15, .30, 0.8, 23, (.20, .45, .05, .30)),
    ('trend',         .25, .40, 1.2, 21, (.15, .15, .40, .30)),
    ('lurker',        .30, .12, 0.6, 21, (.05, .10, .10, .75)),
    ('news',          .15, .70, 1.0, 20, (.40, .20, .20, .20)),
]
EMO_P = np.array([.20, .15, .30, .35])           # excited, angry, happy, indifferent
EMO_S = np.array([.9, .6, .8, .0])
KAPPA, TAU, SMAX, PVIEW, CVIS, FEED, RECENCY = .16, 1.0, 3.0, .5, .4, 40, 2.0
GRID = np.linspace(0, 24, 241)[:-1]


def circadian(peak):
    """Mean-one daily profile: floor + evening Gaussian at the chronotype peak + smaller midday Gaussian (App. A)."""
    d = np.abs(GRID - peak % 24); d = np.minimum(d, 24 - d)
    c = .12 + np.exp(-.5 * (d / 2.2) ** 2) + .45 * np.exp(-.5 * ((GRID - 12.5) / 1.8) ** 2)
    return c / c.mean()


def surrogate_oracle(hour, n_rel, rel, notif, emo, b0):
    leisure = 1.0 if 18 <= hour < 24 else .6 if 12 <= hour < 18 else .5 if 6 <= hour < 12 else .2
    z = b0 + 1.6 * leisure + .9 * min(n_rel, 3) / 3 + 1.4 * rel + 1.1 * notif + .8 * EMO_S[emo]
    return 5.0 / (1.0 + math.exp(-z))


def build_graph(n, m, rng):
    followers = [[] for _ in range(n)]
    indeg = np.zeros(n)
    for i in range(1, n):
        w = indeg[:i] + 1.0
        for j in rng.choice(i, size=min(m, i), replace=False, p=w / w.sum()):
            followers[j].append(i); indeg[j] += 1
    return followers


def simulate(scheduler='ipp', n=800, m=5, hours=72, seed=0, b0=-2.0, kappa=KAPPA, smax=SMAX, pview=PVIEW,
             max_events=None):
    rng = np.random.default_rng(seed)
    followers = build_graph(n, m, rng)
    shares = np.array([p[1] for p in PERSONAS]); pid = rng.choice(len(PERSONAS), size=n, p=shares / shares.sum())
    lam0 = np.array([PERSONAS[k][2] for k in pid]) * rng.lognormal(0, .4, n)
    gain = np.array([PERSONAS[k][3] for k in pid])
    peak = np.array([PERSONAS[k][4] for k in pid]) + rng.normal(0, 1.5, n)
    act_p = np.array([PERSONAS[k][5] for k in pid])
    interest = rng.dirichlet([.4] * 5, size=n)
    circ = np.array([circadian(p) for p in peak]); cmax = circ.max(1)
    # state
    A = np.zeros(n); tA = np.zeros(n); ver = np.zeros(n, int)
    feed = [deque(maxlen=FEED) for _ in range(n)]       # (item, t_exposed)
    items_t, items_topic, items_author = [], [], []
    posts, comments = [], []                              # posting-event times; (parent creation, comment time)
    events = 0
    pq = []

    def S(i, t):
        return min(smax, A[i] * math.exp(-(t - tA[i]) / TAU))

    def lam(i, t):
        return lam0[i] * circ[i][int((t % 24) / .1) % 240] + S(i, t)

    def schedule(i, t):
        if scheduler == 'ipp':
            lm = lam0[i] * cmax[i] + S(i, t)
            heapq.heappush(pq, (t + rng.exponential(1 / lm), 0, i, ver[i], lm))
        elif scheduler == 'hpp':
            heapq.heappush(pq, (t + rng.exponential(1 / lam0[i]), 0, i, ver[i], lam0[i]))
        else:
            heapq.heappush(pq, (t + 1 / lam0[i], 0, i, ver[i], 0))

    def stimulate(i, t, rel, notif, item=None):
        nonlocal A, tA
        if scheduler != 'ipp':
            return
        hour = t % 24
        n_rel = sum(1 for (it, te) in feed[i] if t - te <= 1 and interest[i][items_topic[it]] >= .10)
        emo = rng.choice(4, p=EMO_P)
        I = surrogate_oracle(hour, n_rel, rel, notif, emo, b0)
        A[i] = A[i] * math.exp(-(t - tA[i]) / TAU) + kappa * gain[i] * I * rel; tA[i] = t
        ver[i] += 1; schedule(i, t)

    def relevance(i, topic):
        w = interest[i][topic]
        return .25 if w < .10 else .5 if w < .30 else .75

    def expose(author, item, t, factor):
        for f in followers[author]:
            if rng.random() < pview * factor:
                feed[f].append((item, t)); stimulate(f, t, relevance(f, items_topic[item]), 0, item)

    def new_item(author, t, topic):
        items_t.append(t); items_topic.append(topic); items_author.append(author)
        return len(items_t) - 1

    for i in range(n):
        if scheduler == 'poll':
            heapq.heappush(pq, (rng.random() / lam0[i], 0, i, 0, 0))
        else:
            schedule(i, 0.0)
    while pq:
        t, _, i, v, lm = heapq.heappop(pq)
        if t >= hours:
            break
        if v != ver[i]:
            continue
        if scheduler == 'ipp' and rng.random() > lam(i, t) / lm:       # thinning rejection
            heapq.heappush(pq, (t + rng.exponential(1 / (lam0[i] * cmax[i] + S(i, t))), 0, i, ver[i],
                                lam0[i] * cmax[i] + S(i, t)))
            continue
        # accepted action
        events += 1
        if max_events and events > max_events:
            break
        a = rng.choice(4, p=act_p[i])
        if a in (1, 2):
            cand = [(it, te) for (it, te) in feed[i] if items_author[it] != i]
            if cand:
                w = np.array([interest[i][items_topic[it]] * math.exp(-(t - items_t[it]) / RECENCY) for it, _ in cand])
                if w.sum() > 0:
                    it = cand[rng.choice(len(cand), p=w / w.sum())][0]
                    topic = items_topic[it]
                    new = new_item(i, t, topic); posts.append(t)
                    if a == 1:
                        comments.append((items_t[it], t)); expose(i, new, t, CVIS)
                    else:
                        expose(i, new, t, 1.0)
                    au = items_author[it]
                    if au != i:
                        stimulate(au, t, .5, 1)
                else:
                    a = 0
            else:
                a = 0
        if a == 0:
            topic = rng.choice(5, p=interest[i]); new = new_item(i, t, topic); posts.append(t); expose(i, new, t, 1.0)
        if scheduler != 'ipp':
            schedule(i, t)
        else:
            ver[i] += 1; schedule(i, t)          # redraw after own action (memoryless)
    return dict(events=events, posts=np.array(posts), comments=np.array(comments).reshape(-1, 2))


def hourly(posts):
    return np.histogram(posts % 24, bins=np.arange(25))[0]
