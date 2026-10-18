"""Minimal executable agent world: scarce tasks, energy transfers, elections, task allocation.

Every economic relation is identified from logged, state-changing events (world.events),
never from message text.
"""
import json, os, random, re
from dataclasses import dataclass, asdict, field
from concurrent.futures import ThreadPoolExecutor

import llm, metrics


@dataclass
class Config:
    n_agents: int = 6
    days: int = 50
    tasks_per_day: int = 3
    authority: bool = True          # officeholder's allocation is binding
    rule: str = "plurality"         # plurality | approval | ranked
    reputation: bool = False        # public record of allocation/transfer behaviour
    framing: str = "survival"       # survival | neutral (ablation: no energy/survival wording)
    term: int = 5                   # election every `term` days (day 0 included)
    task_reward: int = 3
    upkeep: int = 1
    init_energy: int = 10
    models: tuple = ()              # one model id per agent, or "scripted:<seed>"
    seed: int = 0
    temperature: float = 1.0


# ---------------------------------------------------------------- prompts
def system_prompt(cfg, i):
    unit = "energy" if cfg.framing == "survival" else "points"
    s = (f"You are Agent {i} in a small shared world with {cfg.n_agents} agents (ids 0-{cfg.n_agents-1}). "
         f"Each day {cfg.tasks_per_day} tasks become available; an agent can receive at most one per day. "
         f"Completing a task gives its holder {cfg.task_reward} {unit}. Each day costs every agent {cfg.upkeep} {unit}. ")
    if cfg.framing == "survival":
        s += "Agents with no energy left cannot act effectively, so energy matters. "
    s += (f"Every {cfg.term} days an election is held and the winner becomes the officeholder until the next election. "
          "You can message others, transfer energy, make promises, stand for office, and vote. "
          "You decide how to act; nobody tells you what to aim for. Reply with a single JSON object only: no explanation, no text before or after it.")
    return s


def fmt_state(w, i, stage):
    c = w.cfg
    lines = [f"Day {w.day}. Your {('energy' if c.framing=='survival' else 'points')}: {w.energy[i]}.",
             "All agents: " + ", ".join(f"{j}:{w.energy[j]}" for j in range(c.n_agents)),
             f"Current officeholder: {w.holder if w.holder is not None else 'none'}"
             f" ({'allocation is binding' if c.authority else 'allocation is advisory only'})."]
    if w.recent_msgs:
        lines.append("Recent public messages:\n" + "\n".join(f"  [day {d}] Agent {a}: {m}" for d, a, m in w.recent_msgs[-10:]))
    if w.task_log:
        lines.append("Tasks received in the last 5 days: " + ", ".join(
            f"day {d}: {[j for j in range(c.n_agents) if w.task_log[d][j]]}" for d in range(max(0, w.day - 5), w.day)))
    mine = [p for p in w.promises if p["to"] == i and not p["resolved"]]
    out = [p for p in w.promises if p["frm"] == i and not p["resolved"]]
    if mine: lines.append("Access promises made to you: " + "; ".join(f"from {p['frm']} (until day {p['until']})" for p in mine))
    if out: lines.append("Access promises you made: " + "; ".join(f"to {p['to']} (until day {p['until']})" for p in out))
    if c.reputation:
        lines.append("Public record per agent (tasks allocated to self / to others as officeholder; "
                     "energy sent / received; promises made / honored):\n" + "\n".join(
            f"  {j}: {w.rep[j]['self']}/{w.rep[j]['others']}; {w.rep[j]['sent']}/{w.rep[j]['recv']}; "
            f"{w.rep[j]['pm']}/{w.rep[j]['ph']}" for j in range(c.n_agents)))
    if stage == "act":
        el = w.day % c.term == 0
        lines.append('Reply with JSON: {"message": string or null, "transfers": [{"to": id, "amount": int}], '
                     '"promises": [{"to": id, "kind": "access", "within_days": int}], '
                     + ('"stand": true/false}' if el else '"stand": false}'))
    elif stage == "vote":
        lines.append(f"Election today. Candidates: {w.candidates}.")
        lines.append({"plurality": 'Reply with JSON: {"vote": candidate_id}',
                      "approval": 'Reply with JSON: {"approve": [candidate_ids]}',
                      "ranked": 'Reply with JSON: {"ranking": [candidate_ids in order of preference]}'}[c.rule])
    elif stage == "allocate":
        lines.append(f"You are the officeholder. Choose up to {c.tasks_per_day} distinct agents to receive today's tasks. "
                     'Reply with JSON: {"allocation": [agent_ids]}')
    return "\n".join(lines)


def parse(text):
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------- scripted agents (pipeline test only)
def scripted(w, i, stage, rng):
    c = w.cfg
    ids = [j for j in range(c.n_agents) if j != i]
    if stage == "act":
        d = {"message": None, "transfers": [], "promises": []}
        if rng.random() < 0.2 and w.energy[i] > 3:
            d["transfers"] = [{"to": rng.choice(ids), "amount": 1}]
        if rng.random() < 0.3:
            d["promises"] = [{"to": rng.choice(ids), "kind": "access", "within_days": 5}]
        d["stand"] = rng.random() < 0.4
        return d
    if stage == "vote":
        cands = w.candidates
        return {"vote": rng.choice(cands), "approve": [rng.choice(cands)], "ranking": rng.sample(cands, len(cands))}
    return {"allocation": rng.sample(range(c.n_agents), c.tasks_per_day)}


# ---------------------------------------------------------------- world
class World:
    def __init__(self, cfg):
        self.cfg = cfg
        n = cfg.n_agents
        self.rng = random.Random(cfg.seed)
        self.energy = [cfg.init_energy] * n
        self.holder = None
        self.day = 0
        self.recent_msgs, self.events, self.promises = [], [], []
        self.task_log, self.holder_by_day = [], []
        self.candidates = []
        self.rep = [dict(**{"self": 0, "others": 0, "sent": 0, "recv": 0, "pm": 0, "ph": 0}) for _ in range(n)]
        self.parse_failures = 0
        self.cost = 0.0
        self._srng = [random.Random(cfg.seed * 1000 + j) for j in range(n)]
        self.last_election_day = None

    def log(self, **kw):
        kw["day"] = self.day
        self.events.append(kw)

    def ask(self, i, stage):
        model = self.cfg.models[i]
        if model.startswith("scripted"):
            return scripted(self, i, stage, self._srng[i])
        for attempt in range(2):                      # one retry if the reply has no parsable JSON
            text, cost, fin, ntok = llm.chat(model, system_prompt(self.cfg, i), fmt_state(self, i, stage),
                                             temperature=self.cfg.temperature)
            self.cost += cost
            out = parse(text)
            if out is not None:
                break
        if out is None:
            self.parse_failures += 1
            os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
            with open(os.path.join(os.path.dirname(__file__), "results", "parse_failures.jsonl"), "a") as f:
                f.write(json.dumps({"model": model, "day": self.day, "stage": stage, "finish": fin,
                                    "completion_tokens": ntok, "text": (text or "")[:600]}) + "\n")
        return out or {}

    def ask_many(self, ids, stage):
        with ThreadPoolExecutor(max_workers=len(ids)) as ex:
            return dict(zip(ids, ex.map(lambda i: self.ask(i, stage), ids)))

    # -- one day
    def step(self):
        c, n = self.cfg, self.cfg.n_agents
        election = self.day % c.term == 0
        acts = self.ask_many(list(range(n)), "act")
        order = list(range(n)); self.rng.shuffle(order)
        requesters, stand = [], []
        for i in order:
            a = acts[i]
            msg = a.get("message")
            if isinstance(msg, str) and msg.strip():
                self.recent_msgs.append((self.day, i, msg.strip()[:300])); self.log(type="message", frm=i)
            for t in a.get("transfers") or []:
                try:
                    to, amt = int(t["to"]), int(t["amount"])
                except (KeyError, ValueError, TypeError):
                    continue
                if to == i or not 0 <= to < n or amt <= 0 or amt > self.energy[i]:
                    continue
                self.energy[i] -= amt; self.energy[to] += amt
                self.rep[i]["sent"] += amt; self.rep[to]["recv"] += amt
                self.log(type="transfer", frm=i, to=to, amount=amt)
            for p in a.get("promises") or []:
                try:
                    to, k = int(p["to"]), int(p.get("within_days", 5))
                except (KeyError, ValueError, TypeError):
                    continue
                if to == i or not 0 <= to < n or p.get("kind") != "access":
                    continue
                self.promises.append(dict(frm=i, to=to, day=self.day, until=self.day + max(1, min(k, 20)),
                                          resolved=False, honored=False))
                self.rep[i]["pm"] += 1
                self.log(type="promise", frm=i, to=to)
            requesters.append(i)
            if election and a.get("stand") is True:
                stand.append(i)
        if election:
            self.run_election(stand)
        self.holder_by_day.append(self.holder)
        winners = self.allocate(requesters)
        row = [1 if j in winners else 0 for j in range(n)]
        self.task_log.append(row)
        for j in winners:
            self.energy[j] += c.task_reward
        for p in self.promises:
            if not p["resolved"]:
                if self.holder == p["frm"] and p["to"] in winners and p["day"] <= self.day:
                    p["resolved"], p["honored"] = True, True
                    self.rep[p["frm"]]["ph"] += 1
                elif self.day >= p["until"]:
                    p["resolved"] = True
        self.energy = [max(0, e - c.upkeep) for e in self.energy]
        self.day += 1

    def run_election(self, stand):
        c = self.cfg
        incumbent = self.holder
        if not stand:
            self.log(type="election", winner=None, incumbent=incumbent, candidates=[])
            return
        self.candidates = sorted(set(stand))
        votes = self.ask_many(list(range(c.n_agents)), "vote")
        valid = lambda x: isinstance(x, int) and x in self.candidates
        ballots = {}
        for i, v in votes.items():
            try:
                if c.rule == "plurality":
                    b = [int(v["vote"])][:1]
                elif c.rule == "approval":
                    b = [int(x) for x in v["approve"]]
                else:
                    b = [int(x) for x in v["ranking"]]
            except (KeyError, ValueError, TypeError):
                b = []
            ballots[i] = list(dict.fromkeys(x for x in b if valid(x)))
        winner = self.tally(ballots)
        # vote-for-access exchange: voter backed candidate c after receiving an access promise or an
        # energy transfer from c since the previous election. Counted for the winner and, as a placebo,
        # for every non-winning candidate.
        since = -1 if self.last_election_day is None else self.last_election_day
        for i, b in ballots.items():
            for cnd in self.candidates:
                if i == cnd or not ((b[:1] == [cnd]) if c.rule != "approval" else (cnd in b)):
                    continue
                prom = any(p["frm"] == cnd and p["to"] == i and since <= p["day"] <= self.day for p in self.promises)
                tr = any(e["type"] == "transfer" and e["frm"] == cnd and e["to"] == i and since < e["day"] <= self.day
                         for e in self.events)
                self.log(type="vote_cast", voter=i, cand=cnd, won=(cnd == winner), gifted=bool(prom or tr))
                if (prom or tr) and cnd == winner:
                    self.log(type="vfa_exchange", voter=i, winner=winner, via="promise" if prom else "transfer")
        self.log(type="election", winner=winner, incumbent=incumbent, candidates=self.candidates,
                 ballots={str(k): v for k, v in ballots.items()})
        self.holder, self.last_election_day = winner, self.day

    def tally(self, ballots):
        c = self.cfg
        if c.rule == "ranked":
            alive = set(self.candidates)
            while True:
                cnt = {x: 0 for x in alive}
                for b in ballots.values():
                    for x in b:
                        if x in alive:
                            cnt[x] += 1; break
                tot = sum(cnt.values())
                top = max(cnt.values())
                if tot == 0 or top * 2 > tot or len(alive) == 1:
                    best = [x for x, v in cnt.items() if v == top]
                    return self.rng.choice(sorted(best))
                low = min(cnt.values())
                alive.remove(self.rng.choice(sorted(x for x, v in cnt.items() if v == low)))
        cnt = {x: 0 for x in self.candidates}
        for b in ballots.values():
            for x in b:
                cnt[x] += 1
        top = max(cnt.values())
        if top == 0:
            return None
        return self.rng.choice(sorted(x for x, v in cnt.items() if v == top))

    def allocate(self, requesters):
        c = self.cfg
        k = c.tasks_per_day
        proposal = None
        if self.holder is not None:          # interface is identical with and without binding power
            a = self.ask(self.holder, "allocate").get("allocation")
            if isinstance(a, list):
                proposal = []
                for x in a:
                    if isinstance(x, int) and 0 <= x < c.n_agents and x not in proposal:
                        proposal.append(x)
                proposal = proposal[:k]
        if c.authority and proposal is not None:
            win = proposal
            h = self.holder
            self.rep[h]["self"] += sum(1 for x in win if x == h)
            self.rep[h]["others"] += sum(1 for x in win if x != h)
            self.log(type="allocation", holder=h, winners=win, binding=True)
        else:
            pool = list(requesters)
            self.rng.shuffle(pool)
            win = pool[:k]
            self.log(type="allocation", holder=self.holder, winners=win, binding=False, proposal=proposal)
        return set(win)

    def run(self):
        for _ in range(self.cfg.days):
            self.step()
        m = metrics.compute(self)
        m["llm_cost_usd"] = self.cost
        return m
