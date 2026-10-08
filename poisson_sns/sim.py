"""Poisson-SNS: event-driven LLM-agent social platform simulator.

Re-implementation from the manuscript specification (Sections 3.1-3.5, Table 1,
Appendix B). Quantities the manuscript does not specify (daily-profile shape,
emotion model, surrogate-oracle coefficients, relevance thresholds) are set in
the constants below and are documented in README.md.
"""
import heapq
import math
import random
from collections import deque

# ---- Table 1: persona parameters -------------------------------------------
# name, share, base rate (1/h), gain g, peak hour, P(post, comment, retweet, like)
PERSONAS = [
    ("early_adopter", 0.15, 0.45, 1.3, 22, (0.30, 0.20, 0.25, 0.25)),
    ("cynic",         0.15, 0.30, 0.8, 23, (0.20, 0.45, 0.05, 0.30)),
    ("trend_follower", 0.25, 0.40, 1.2, 21, (0.15, 0.15, 0.40, 0.30)),
    ("lurker",        0.30, 0.12, 0.6, 21, (0.05, 0.10, 0.10, 0.75)),
    ("news_junkie",   0.15, 0.70, 1.0, 20, (0.40, 0.20, 0.20, 0.20)),
]
PERSONA_NAMES = [p[0] for p in PERSONAS]
EMOTIONS = ["excited", "angry", "happy", "indifferent"]
EMOTION_P = [0.20, 0.15, 0.30, 0.35]
N_TOPICS = 5
DIRICHLET_ALPHA = 0.4
SIGMA_RATE = 0.4        # log-normal sd of individual base rate
SIGMA_CHRONO = 1.5      # hours, sd of chronotype perturbation

# ---- Appendix B: global parameters -------------------------------------------
KAPPA = 0.16
TAU = 1.0
S_MAX = 3.0
P_VIEW = 0.5
COMMENT_VIS = 0.4
FEED_CAP = 40
NOTIF_RELEVANCE = 0.5
REL_VALUE = {0: 0.25, 1: 0.50, 2: 0.75}   # r_ij by relevance level low/med/high
REL_CUT = (0.10, 0.30)                     # interest-weight cut points (assumed)

RECENCY_TAU = 2.0  # h; agents favour recent feed items when replying/retweeting (assumed)
PROFILE_RES = 10  # samples per hour for the circadian lookup


def period_of(t):
    return int((t % 24.0) // 6)  # 0 night, 1 morning, 2 afternoon, 3 evening


def rel_level(w):
    return 0 if w < REL_CUT[0] else (1 if w < REL_CUT[1] else 2)


def _wrap(d):
    d = abs(d) % 24.0
    return min(d, 24.0 - d)


def make_profile(peak):
    """Mean-one daily profile: evening peak, smaller midday peak, night trough."""
    mid = 12.5 + 0.5 * (peak - 21.0)
    vals = []
    for k in range(24 * PROFILE_RES):
        h = (k + 0.5) / PROFILE_RES
        e = math.exp(-_wrap(h - peak) ** 2 / (2 * 2.2 ** 2))
        m = math.exp(-_wrap(h - mid) ** 2 / (2 * 1.8 ** 2))
        vals.append(0.12 + 1.0 * e + 0.45 * m)
    mean = sum(vals) / len(vals)
    return [v / mean for v in vals]


# ---- Network ------------------------------------------------------------------
def preferential_attachment(n, m, rng):
    """Directed follower graph; new node follows m nodes chosen proportional to
    (in-degree + 1). Returns followers[u] = list of agents who follow u."""
    followers = [[] for _ in range(n)]
    urn = []
    n0 = m + 1
    for i in range(n0):
        urn.append(i)
        for j in range(n0):
            if i != j:
                followers[j].append(i)
                urn.append(j)
    for i in range(n0, n):
        chosen = set()
        while len(chosen) < m:
            chosen.add(urn[rng.randrange(len(urn))])
        for j in chosen:
            followers[j].append(i)
            urn.append(j)
        urn.append(i)
    return followers


# ---- Oracles ------------------------------------------------------------------
PERSONA_BIAS = {"early_adopter": 0.5, "cynic": 0.4, "trend_follower": 0.5,
                "lurker": -0.8, "news_junkie": 0.7}
EMOTION_BIAS = {"excited": 0.5, "angry": 0.4, "happy": 0.2, "indifferent": -0.4}
_LEISURE_ANCHORS = [(0, -0.3), (3, -0.4), (6, -0.1), (9, 0.0), (12, 0.1),
                    (15, 0.1), (18, 0.3), (21, 0.4), (24, -0.3)]


def leisure_fine(h):
    h = h % 24.0
    for (h0, v0), (h1, v1) in zip(_LEISURE_ANCHORS, _LEISURE_ANCHORS[1:]):
        if h0 <= h <= h1:
            return v0 + (v1 - v0) * (h - h0) / (h1 - h0)
    return 0.0


def leisure_period(p):
    hs = [p * 6 + 0.25 * k for k in range(24)]
    return sum(leisure_fine(h) for h in hs) / len(hs)


def surrogate_core(leisure, persona, emotion, vol, rel, notif):
    """Deterministic rule-based urge rating in [0, 5]. Increasing in leisure,
    relevant feed volume, relevance, notification, positive emotion."""
    v = 0.6 + PERSONA_BIAS[persona] + leisure + EMOTION_BIAS[emotion]
    v += 0.45 * min(vol, 3.0) + 0.8 * rel * (1.0 if vol > 0 else 0.0)
    v += 0.7 * notif
    return min(5.0, max(0.0, v))


class SurrogateFine:
    """Original surrogate: continuous clock time, uncapped-then-saturating volume,
    continuous relevance."""
    def __call__(self, t, persona, emotion, vol, w, notif):
        rel = min(1.0, w / 0.4)
        return surrogate_core(leisure_fine(t), persona, emotion,
                              3.0 * (1 - math.exp(-vol / 2.0)) if vol > 0 else 0.0,
                              rel, notif)


REL_BIN_VALUE = (0.125, 0.5, 1.0)


def state_key(t, persona, emotion, vol, w, notif):
    vb = min(int(vol), 3)
    rb = rel_level(w) if vb > 0 else -1
    return (period_of(t), persona, emotion, vb, rb, int(notif))


def all_states():
    keys = []
    for p in range(4):
        for pe in PERSONA_NAMES:
            for em in EMOTIONS:
                combos = [(0, -1)] + [(v, r) for v in (1, 2, 3) for r in (0, 1, 2)]
                for vb, rb in combos:
                    for n in (0, 1):
                        keys.append((p, pe, em, vb, rb, n))
    return keys


def surrogate_coarse_value(key):
    p, pe, em, vb, rb, n = key
    rel = REL_BIN_VALUE[rb] if rb >= 0 else 0.0
    return surrogate_core(leisure_period(p), pe, em, vb, rel, n)


class TableOracle:
    """Lookup oracle over the 1,600 coarse states (LLM ratings or the coarse
    surrogate control)."""
    def __init__(self, table):
        self.table = table

    def __call__(self, t, persona, emotion, vol, w, notif):
        return self.table[state_key(t, persona, emotion, vol, w, notif)]


def coarse_surrogate_table():
    return {k: surrogate_coarse_value(k) for k in all_states()}


# ---- Simulation -----------------------------------------------------------------
class Sim:
    def __init__(self, n, m, seed, oracle=None, scheduler="ipp",
                 net_seed=None, kappa=KAPPA, s_max=S_MAX, p_view=P_VIEW,
                 tau=TAU, netfun=None, max_events=600000):
        self.n = n
        self.scheduler = scheduler
        self.oracle = oracle or SurrogateFine()
        self.kappa, self.s_max, self.p_view, self.tau = kappa, s_max, p_view, tau
        net_rng = random.Random(net_seed if net_seed is not None else seed)
        self.followers = (netfun(n, m, net_rng) if netfun
                          else preferential_attachment(n, m, net_rng))
        self.rng = random.Random(seed * 7919 + 13)
        trng = random.Random(seed * 104729 + 7)
        shares = [p[1] for p in PERSONAS]
        self.persona = [trng.choices(range(5), shares)[0] for _ in range(n)]
        self.lam0, self.gain, self.profile, self.pmax = [], [], [], []
        self.interest, self.probs = [], []
        prof_cache = {}
        for i in range(n):
            _, _, lam, g, peak, pr = PERSONAS[self.persona[i]]
            self.lam0.append(lam * math.exp(trng.gauss(0, SIGMA_RATE)))
            self.gain.append(g)
            pk = round((peak + trng.gauss(0, SIGMA_CHRONO)) % 24.0, 1)
            if pk not in prof_cache:
                prof_cache[pk] = make_profile(pk)
            self.profile.append(prof_cache[pk])
            self.pmax.append(max(prof_cache[pk]))
            d = [trng.gammavariate(DIRICHLET_ALPHA, 1.0) for _ in range(N_TOPICS)]
            s = sum(d)
            self.interest.append([x / s for x in d])
            self.probs.append(pr)
        self.names = [PERSONA_NAMES[p] for p in self.persona]
        # state
        self.raw = [0.0] * n
        self.tl = [0.0] * n
        self.ver = [0] * n
        self.feed = [deque(maxlen=FEED_CAP) for _ in range(n)]
        self.recent = [deque() for _ in range(n)]  # (t, relevant?) in last hour
        self.last_w = [0.0] * n
        self.phase = [self.rng.random() / max(l, 1e-9) for l in self.lam0]
        # items
        self.i_author, self.i_topic, self.i_kind, self.i_parent = [], [], [], []
        self.i_t, self.i_camp = [], []
        self.events = []  # (t, agent, action(0 post,1 comment,2 rt,3 like), item, delay)
        self.heap = []
        self.t = 0.0
        # campaign tracking
        self.adopters = {}
        self.adopt_times = []
        self.exposed = set()
        self.camp_events = []
        self.hook = None
        self.max_events = max_events
        self.truncated = False

    # -- intensity -------------------------------------------------------------
    def S(self, a, t):
        r = self.raw[a] * math.exp(-(t - self.tl[a]) / self.tau)
        return r if r < self.s_max else self.s_max

    def lam(self, a, t):
        c = self.profile[a][int((t % 24.0) * PROFILE_RES)]
        return self.lam0[a] * c + self.S(a, t)

    def next_time(self, a, t, horizon):
        sc = self.scheduler
        rng = self.rng
        if sc == "hpp":
            return t + rng.expovariate(self.lam0[a])
        if sc == "poll":
            per = 1.0 / self.lam0[a]
            k = math.floor((t - self.phase[a]) / per + 1e-9) + 1
            return self.phase[a] + k * per
        lmax = self.lam0[a] * self.pmax[a] + self.S(a, t)
        s = t
        while True:
            s += rng.expovariate(lmax)
            if s > horizon:
                return s
            if rng.random() * lmax <= self.lam(a, s):
                return s

    def schedule(self, a, t):
        tn = self.next_time(a, t, self.horizon)
        if tn <= self.horizon:
            heapq.heappush(self.heap, (tn, 0, a, self.ver[a]))

    # -- stimulus ----------------------------------------------------------------
    def stimulate(self, a, t, w, notif):
        """Add a stimulus to agent a at time t. w = interest weight of the item
        (ignored for notifications)."""
        if self.scheduler != "ipp":
            if notif:
                return
            return
        rec = self.recent[a]
        while rec and rec[0][0] < t - 1.0:
            rec.popleft()
        if notif:
            rl, wv = 1, 0.5 * (REL_CUT[0] + REL_CUT[1])
            r = NOTIF_RELEVANCE
        else:
            rl = rel_level(w)
            wv = w
            r = REL_VALUE[rl]
            rec.append((t, rl >= 1))
            self.last_w[a] = w
        vol = sum(1 for _, ok in rec if ok)
        wl = wv if notif else self.last_w[a]
        emo = EMOTIONS[self.rng.choices(range(4), EMOTION_P)[0]]
        I = self.oracle(t, self.names[a], emo, vol, wl, 1 if notif else 0)
        add = self.kappa * self.gain[a] * I * r
        self.raw[a] = self.raw[a] * math.exp(-(t - self.tl[a]) / self.tau) + add
        self.tl[a] = t
        self.ver[a] += 1
        self.schedule(a, t)

    # -- items / actions ---------------------------------------------------------
    def new_item(self, author, topic, kind, parent, t, camp):
        iid = len(self.i_author)
        self.i_author.append(author)
        self.i_topic.append(topic)
        self.i_kind.append(kind)
        self.i_parent.append(parent)
        self.i_t.append(t)
        self.i_camp.append(camp)
        return iid

    def publish(self, iid, t):
        author = self.i_author[iid]
        topic = self.i_topic[iid]
        p = self.p_view * (COMMENT_VIS if self.i_kind[iid] == 1 else 1.0)
        camp = self.i_camp[iid]
        rng = self.rng
        for f in self.followers[author]:
            if rng.random() < p:
                self.feed[f].append(iid)
                if camp:
                    self.exposed.add(f)
                self.stimulate(f, t, self.interest[f][topic], False)

    def act(self, a, t):
        rng = self.rng
        act = rng.choices(range(4), self.probs[a])[0]
        feed = self.feed[a]
        elig = []
        if act != 0:
            for iid in feed:
                if self.i_author[iid] != a and (act == 3 or self.i_kind[iid] != 1):
                    elig.append(iid)
            if not elig:
                act = 0
        if act == 0:
            topic = rng.choices(range(N_TOPICS), self.interest[a])[0]
            iid = self.new_item(a, topic, 0, -1, t, False)
            self.events.append((t, a, 0, iid, 0.0))
            self.publish(iid, t)
        else:
            wts = [(self.interest[a][self.i_topic[i]] + 0.05)
                   * math.exp(-(t - self.i_t[i]) / RECENCY_TAU) for i in elig]
            parent = rng.choices(elig, wts)[0]
            if act == 3:
                self.events.append((t, a, 3, parent, 0.0))
                return
            camp = self.i_camp[parent]
            iid = self.new_item(a, self.i_topic[parent], act, parent, t, camp)
            self.events.append((t, a, act, iid, t - self.i_t[parent]))
            if camp:
                if a not in self.adopters:
                    self.adopters[a] = t
                    self.adopt_times.append(t)
                self.camp_events.append(t)
            self.publish(iid, t)
            py = self.i_author[parent]
            if py != a:
                self.stimulate(py, t, 0.0, True)

    # -- run ---------------------------------------------------------------------
    def run(self, horizon, inject=None):
        """inject: (time, [seed agents], topic)."""
        self.horizon = horizon
        for a in range(self.n):
            self.schedule(a, 0.0)
        if inject:
            heapq.heappush(self.heap, (inject[0], 1, -1, 0))
        while self.heap:
            t, kind, a, v = heapq.heappop(self.heap)
            if t > horizon:
                break
            self.t = t
            if kind == 1:
                _, seeds, topic = inject
                self.camp_start = t
                for s in seeds:
                    iid = self.new_item(s, topic, 0, -1, t, True)
                    self.events.append((t, s, 0, iid, 0.0))
                    self.publish(iid, t)
                continue
            if v != self.ver[a]:
                continue
            self.act(a, t)
            if len(self.events) > self.max_events:
                self.truncated = True
                break
            self.ver[a] += 1
            self.schedule(a, t)
        return self


# ---- alternative follower networks (robustness checks) ---------------------------
def random_network(n, m, rng):
    """Each agent follows m uniformly random others (Poisson in-degree)."""
    followers = [[] for _ in range(n)]
    for i in range(n):
        chosen = set()
        while len(chosen) < m:
            j = rng.randrange(n)
            if j != i:
                chosen.add(j)
        for j in chosen:
            followers[j].append(i)
    return followers


def community_network(n, m, rng, blocks=10, p_in=0.8):
    """Preferential attachment with community structure: a fraction p_in of each
    agent's follow links stay inside its block."""
    blk = [rng.randrange(blocks) for _ in range(n)]
    members = [[] for _ in range(blocks)]
    urn_b = [[] for _ in range(blocks)]
    urn_all = []
    followers = [[] for _ in range(n)]
    for i in range(n):
        chosen = set()
        tries = 0
        while len(chosen) < min(m, i) and tries < 50 * m:
            tries += 1
            u = urn_b[blk[i]] if (rng.random() < p_in and urn_b[blk[i]]) else urn_all
            if not u:
                continue
            j = u[rng.randrange(len(u))]
            if j != i:
                chosen.add(j)
        for j in chosen:
            followers[j].append(i)
            urn_b[blk[j]].append(j)
            urn_all.append(j)
        urn_b[blk[i]].append(i)
        urn_all.append(i)
    return followers
