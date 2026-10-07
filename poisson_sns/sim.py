"""Poisson-SNS: LLM-agent social-media simulator driven by an inhomogeneous
Poisson process (IPP).  lambda_i(t) = lambda_base_i * c_i(t) + sum_j lambda_stim_ij(t).

Time is in hours.  The LLM "intensity" call is behind IntensityProvider so the
default deterministic surrogate can be swapped for a real LLM (llm_provider.py).
"""
import heapq
import math
from collections import deque, defaultdict

import numpy as np

TOPICS = 5
EMOTIONS = ["interested", "indifferent", "annoyed", "excited"]

# lam_base: actions/hour at mean circadian level; gain: stimulus sensitivity
# act: probabilities of (post, comment, retweet, like)
PERSONAS = {
    "early_adopter":  dict(lam=0.45, gain=1.3, peak=22.0, act=(0.30, 0.20, 0.25, 0.25), social=0.6),
    "cynic":          dict(lam=0.30, gain=0.8, peak=23.0, act=(0.20, 0.45, 0.05, 0.30), social=0.3),
    "trend_follower": dict(lam=0.40, gain=1.2, peak=21.0, act=(0.15, 0.15, 0.40, 0.30), social=0.7),
    "lurker":         dict(lam=0.12, gain=0.6, peak=21.0, act=(0.05, 0.10, 0.10, 0.75), social=0.2),
    "news_junkie":    dict(lam=0.70, gain=1.0, peak=20.0, act=(0.40, 0.20, 0.20, 0.20), social=0.5),
}
PERSONA_MIX = [0.15, 0.15, 0.25, 0.30, 0.15]
PERSONA_KEYS = list(PERSONAS)


def _raw_shape(h, peak):
    lunch = 0.35 * math.exp(-0.5 * (((h - 12.5 + 12) % 24 - 12) / 2.2) ** 2)  # midday bump
    return 0.1 + ((1 + math.cos(2 * math.pi * (h - peak) / 24)) / 2) ** 2 + lunch


_grid = [_raw_shape(x / 4, 21.0) for x in range(96)]
_NORM = sum(_grid) / len(_grid)


def circadian_shape(h, peak):
    """Mean-1 daily activity profile: evening peak + midday bump + night trough."""
    return _raw_shape(h, peak) / _NORM


C_MAX = 1.05 * (max(_raw_shape(x / 4, p) for x in range(96) for p in (19.0, 21.0, 23.0, 25.0)) / _NORM)
S_MAX = 3.0


def leisure(h):
    """0..1 'leisure time' score used by the surrogate LLM."""
    return max(0.0, math.cos(2 * math.pi * (h - 21) / 24)) ** 1.0 if (h >= 6 or h < 1) else 0.0


# ----------------------------------------------------------------- intensity
class SurrogateIntensity:
    """Deterministic stand-in for the LLM prompt of the proposal (0..5)."""
    name = "surrogate"

    def __init__(self):
        self.calls = 0

    def __call__(self, persona, hour, emotion, rel_count, rel_bucket, notif):
        self.calls += 1
        p = PERSONAS[persona]
        x = 0.25 + 0.5 * p["social"] + 0.9 * leisure(hour)
        x += 0.55 * min(rel_count, 5) * (0.4 + 0.25 * rel_bucket)
        x += 0.9 * min(notif, 3)
        x += {"interested": 0.4, "indifferent": -0.3, "annoyed": 0.1, "excited": 0.8}[emotion]
        return float(min(5.0, max(0.0, x))), "surrogate"


class CachedProvider:
    """Memoises provider calls on the discretised state (temperature-0 LLM)."""

    def __init__(self, provider):
        self.provider, self.cache, self.hits = provider, {}, 0

    def __call__(self, persona, hour, emotion, rel_count, rel_bucket, notif):
        key = (persona, int(hour) % 24, emotion, min(rel_count, 5), rel_bucket, min(notif, 3))
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        v = self.provider(*key)
        self.cache[key] = v
        return v


def prompt_for(persona, hour, emotion, rel_count, notif):
    """Prompt text of the research proposal (section 4), filled in from state."""
    return (
        f"[System]\n당신은 가상 SNS 사용자('{persona}')의 행동 제어 장치입니다.\n"
        "현재 상태와 주변 환경을 보고, 향후 1시간 이내에 SNS에 '새로운 글을 작성하거나 댓글을 달고 싶어 하는 "
        "충동(Intensity)'을 0.0에서 5.0 사이의 실수로 평가하세요.\n\n[현재 상황]\n"
        f"- 현재 시각: {int(hour) % 24}시\n- 현재 감정: {emotion}\n"
        f"- 타임라인 업데이트: 관심 주제 글이 최근 {rel_count}개 피드에 올라왔음.\n"
        f"- 알림: {notif}건\n\n[출력 형식]\n반드시 JSON으로만 응답: "
        '{"intensity": (0.0~5.0), "reason": "짧은 이유"}'
    )


# ------------------------------------------------------------------- network
def build_network(n, m, rng):
    """Directed follower graph, preferential attachment on in-degree.
    Returns followers[u] = list of agents who follow u."""
    followers = [[] for _ in range(n)]
    indeg = np.ones(n)
    for v in range(m + 1, n):
        w = indeg[:v] / indeg[:v].sum()
        for u in rng.choice(v, size=m, replace=False, p=w):
            followers[u].append(v)
            indeg[u] += 1
    for v in range(m + 1):  # seed clique follows each other
        for u in range(m + 1):
            if u != v:
                followers[u].append(v)
    return followers


# ---------------------------------------------------------------- simulation
class Sim:
    def __init__(self, n=1000, m=5, horizon=48.0, start_hour=0.0, mode="ipp",
                 kappa=0.16, tau=1.0, p_view=0.5, reply_vis=0.4,
                 provider=None, seed=0, network_seed=None, followers=None):
        self.n, self.T, self.h0, self.mode = n, horizon, start_hour, mode
        self.kappa, self.tau, self.p_view, self.reply_vis = kappa, tau, p_view, reply_vis
        self.rng = np.random.default_rng(seed)
        nrng = np.random.default_rng(seed if network_seed is None else network_seed)
        self.followers = followers if followers is not None else build_network(n, m, nrng)
        self.provider = provider or CachedProvider(SurrogateIntensity())
        # agents
        pk = nrng.choice(len(PERSONA_KEYS), size=n, p=PERSONA_MIX)
        self.persona = [PERSONA_KEYS[k] for k in pk]
        self.peak = np.array([PERSONAS[p]["peak"] for p in self.persona]) + nrng.normal(0, 1.5, n)
        self.lam = np.array([PERSONAS[p]["lam"] for p in self.persona]) * nrng.lognormal(0, 0.4, n)
        self.interest = nrng.dirichlet(np.full(TOPICS, 0.4), size=n)
        self.S = np.zeros(n)          # stimulus intensity at time self.St
        self.St = np.zeros(n)
        self.ver = np.zeros(n, dtype=int)
        self.feed = [deque(maxlen=40) for _ in range(n)]
        self.notifs = [deque() for _ in range(n)]
        self.acted = [set() for _ in range(n)]
        self.heap = []
        # items: (author, t, topic, campaign, parent_event)
        self.items = []
        self.events = []   # (t, agent, kind, item_id, target_item, campaign)
        self.exposed = set()
        self.exposed_t = {}
        self.t = 0.0

    # --- intensity -----------------------------------------------------
    def hour(self, t):
        return (self.h0 + t) % 24

    def lam_t(self, i, t):
        base = self.lam[i] * circadian_shape(self.hour(t), self.peak[i])
        return base + self.S[i] * math.exp(-(t - self.St[i]) / self.tau)

    def schedule(self, i, t):
        """Draw next firing time for agent i by thinning, starting from t."""
        self.ver[i] += 1
        if self.mode == "periodic":
            period = 1.0 / self.lam[i]
            if not hasattr(self, "_phase"):
                self._phase = self.rng.uniform(0, 1, self.n)
            k = math.floor((t / period) - self._phase[i]) + 1
            nxt = (k + self._phase[i]) * period
            if nxt <= t:
                nxt = t + period
            if nxt <= self.T:
                heapq.heappush(self.heap, (nxt, i, self.ver[i]))
            return
        if self.mode == "hpp":
            lmax = self.lam[i]
            nxt = t + self.rng.exponential(1 / lmax)
            if nxt <= self.T:
                heapq.heappush(self.heap, (nxt, i, self.ver[i]))
            return
        stim = self.S[i] * math.exp(-(t - self.St[i]) / self.tau)
        lmax = self.lam[i] * C_MAX + stim
        s = t
        while True:
            s += self.rng.exponential(1 / lmax)
            if s > self.T:
                return
            if self.rng.random() * lmax <= self.lam_t(i, s):
                heapq.heappush(self.heap, (s, i, self.ver[i]))
                return

    # --- stimulus ------------------------------------------------------
    def stimulate(self, i, t, strength):
        cur = self.S[i] * math.exp(-(t - self.St[i]) / self.tau)
        self.S[i] = min(cur + strength, S_MAX)  # saturation: bounded excitation
        self.St[i] = t
        if self.mode == "ipp":
            self.schedule(i, t)

    def expose(self, i, item_id, t, vis):
        if self.rng.random() > vis:
            return
        author, _, topic, camp, _ = self.items[item_id]
        if i == author:
            return
        self.feed[i].append((item_id, t))
        if camp and i not in self.exposed:
            self.exposed.add(i)
            self.exposed_t[i] = t
        rel = self.interest[i][topic]
        bucket = 0 if rel < 0.15 else 1 if rel < 0.3 else 2 if rel < 0.5 else 3
        if bucket == 0:
            return
        rel_count = sum(1 for (it, ft) in self.feed[i]
                        if t - ft <= 1.0 and self.interest[i][self.items[it][2]] >= 0.3)
        nq = self.notifs[i]
        while nq and t - nq[0] > 1.0:
            nq.popleft()
        emo = EMOTIONS[self.rng.choice(4, p=[0.35, 0.3, 0.1, 0.25])]
        inten, _ = self.provider(self.persona[i], self.hour(t), emo, rel_count, bucket, len(nq))
        g = PERSONAS[self.persona[i]]["gain"]
        self.stimulate(i, t, self.kappa * g * inten * (0.25 * bucket))

    # --- actions -------------------------------------------------------
    def new_item(self, author, t, topic, camp, parent):
        self.items.append((author, t, topic, camp, parent))
        return len(self.items) - 1

    def fire(self, i, t):
        pr = PERSONAS[self.persona[i]]
        kind = ("post", "comment", "retweet", "like")[self.rng.choice(4, p=pr["act"])]
        # choose a target from feed
        cand = []
        if kind in ("comment", "retweet", "like"):
            for (it, ft) in self.feed[i]:
                if it in self.acted[i]:
                    continue
                a, _, topic, camp, _ = self.items[it]
                w = (self.interest[i][topic] ** 2 + 1e-3) * math.exp(-(t - ft) / 3.0)
                cand.append((it, w))
        if kind != "post":
            if not cand:
                kind = "post"
            else:
                ws = np.array([w for _, w in cand])
                tgt = cand[self.rng.choice(len(cand), p=ws / ws.sum())][0]
        if kind == "post":
            topic = int(self.rng.choice(TOPICS, p=self.interest[i]))
            it = self.new_item(i, t, topic, False, -1)
            self.events.append((t, i, "post", it, -1, False))
            for f in self.followers[i]:
                self.expose(f, it, t, self.p_view)
        elif kind == "like":
            self.acted[i].add(tgt)
            self.events.append((t, i, "like", -1, tgt, self.items[tgt][3]))
        else:
            self.acted[i].add(tgt)
            a, t0, topic, camp, _ = self.items[tgt]
            it = self.new_item(i, t, topic, camp, tgt)
            self.events.append((t, i, kind, it, tgt, camp))
            self.notifs[a].append(t)
            if self.items[tgt][0] != i:
                self.stimulate(a, t, self.kappa * PERSONAS[self.persona[a]]["gain"] * 1.5)
            vis = self.p_view if kind == "retweet" else self.p_view * self.reply_vis
            for f in self.followers[i]:
                self.expose(f, it, t, vis)

    def seed_campaign(self, seeds, topic=0):
        for s in seeds:
            it = self.new_item(s, 0.0, topic, True, -1)
            self.events.append((0.0, s, "seed", it, -1, True))
            self.exposed.add(s)
            self.exposed_t[s] = 0.0
            for f in self.followers[s]:
                self.expose(f, it, 0.0, self.p_view)

    def run(self):
        for i in range(self.n):
            if self.mode == "ipp":
                self.schedule(i, 0.0)
            else:
                self.schedule(i, 0.0)
        while self.heap:
            t, i, v = heapq.heappop(self.heap)
            if v != self.ver[i]:
                continue
            self.t = t
            self.fire(i, t)
            if self.mode == "ipp":
                self.schedule(i, t)
            else:
                self.schedule(i, t)
        return self

    # --- outputs -------------------------------------------------------
    def posting_times(self):
        return np.array([e[0] for e in self.events if e[2] in ("post", "comment", "retweet")])

    def reply_delays(self):
        return np.array([e[0] - self.items[e[4]][1] for e in self.events if e[2] == "comment"])


# ------------------------------------------------- coarse-state lookup tables
PERIODS = {0: ("심야/새벽(0~6시)", 3), 1: ("오전(6~12시)", 9), 2: ("오후(12~18시)", 15), 3: ("저녁/밤(18~24시)", 21)}
PERSONA_DESC = {
    "early_adopter": "새로운 기술·제품을 남보다 먼저 써보고 공유하는 얼리어답터",
    "cynic": "대체로 비판적이고 냉소적이며 댓글로 반박하기를 즐기는 사용자",
    "trend_follower": "유행하는 주제를 따라가며 리트윗·공유를 자주 하는 트렌드 추종자",
    "lurker": "주로 눈팅만 하고 글·댓글은 거의 쓰지 않는 사용자",
    "news_junkie": "뉴스와 이슈를 늘 확인하고 의견을 자주 올리는 사용자",
}
EMO_KO = {"interested": "흥미로움", "indifferent": "무덤덤함", "annoyed": "짜증남", "excited": "들떠 있음"}
BUCKET_KO = {1: "관심이 약간 있는 주제", 2: "관심 있는 주제", 3: "평소 매우 관심 많은 주제"}


def coarse_key(persona, hour, emotion, rel_count, rel_bucket, notif):
    period = 0 if hour < 6 else 1 if hour < 12 else 2 if hour < 18 else 3
    return (persona, period, emotion, min(int(rel_count), 3), int(rel_bucket), min(int(notif), 1))


def all_coarse_states():
    out = []
    for p in PERSONA_KEYS:
        for per in PERIODS:
            for e in EMOTIONS:
                for rc, bks in ((0, (1,)), (1, (1, 2, 3)), (2, (1, 2, 3)), (3, (1, 2, 3))):
                    for b in bks:
                        for nf in (0, 1):
                            out.append((p, per, e, rc, b, nf))
    return out


def coarse_prompt(key):
    p, per, e, rc, b, nf = key
    return (f"사용자 유형: {PERSONA_DESC[p]}. 현재 시간대: {PERIODS[per][0]}. 현재 감정: {EMO_KO[e]}. "
            f"최근 1시간 내 피드에 올라온 관심권 글: {rc}개 (방금 본 글의 주제: {BUCKET_KO[b]}). "
            f"알림: {'있음(내 글에 반응)' if nf else '없음'}.")


class TableProvider:
    """Lookup of precomputed intensities on coarse states (e.g. produced by an LLM)."""

    def __init__(self, table, name="table"):
        self.table, self.name, self.calls = table, name, 0

    def __call__(self, persona, hour, emotion, rel_count, rel_bucket, notif):
        self.calls += 1
        return self.table[coarse_key(persona, hour, emotion, rel_count, rel_bucket, notif)], ""
