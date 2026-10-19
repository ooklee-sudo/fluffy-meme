"""Convert agent_econ event logs into the tables the analysis scripts read.

usage: python convert_logs.py RESULTS_DIR OUT_DIR

Writes OUT_DIR/main/ (the 144 main-design worlds) and OUT_DIR/h2/ (the 24
capability-contrast worlds), each with worlds.csv, elections.csv, allocations.csv.
Pilot, smoke and test worlds are ignored.

Energy is replayed from the logged events in the order world.py applies them:
transfers, election, allocation reward, office bonus, upkeep (floored at zero).
"""
import glob, json, os, re, sys
import numpy as np, pandas as pd

SRC, OUT = sys.argv[1], sys.argv[2]


def model_family(m):
    return "claude" if "claude" in m else "deepseek"


def model_cap(m):
    return "flash" if "flash" in m else "pro" if "deepseek" in m else "haiku"


def replay(cfg, ev):
    """Per-day energy at start of day and at allocation time (after transfers)."""
    n, days = cfg["n_agents"], cfg["days"]
    e = np.full(n, cfg["init_energy"], float)
    start, alloc_t = np.zeros((days, n)), np.zeros((days, n))
    by_day = {}
    for x in ev:
        by_day.setdefault(x["day"], []).append(x)
    for d in range(days):
        start[d] = e
        for x in by_day.get(d, []):
            if x["type"] == "transfer":
                e[x["frm"]] -= x["amount"]; e[x["to"]] += x["amount"]
        alloc_t[d] = e
        for x in by_day.get(d, []):
            if x["type"] == "allocation":
                for w in x["winners"]:
                    e[w] += cfg["task_reward"]
                if cfg["office_bonus"] and x["holder"] is not None:
                    e[x["holder"]] += cfg["office_bonus"]
        e = np.maximum(0, e - cfg["upkeep"])
    return start, alloc_t


def convert(prefix, out):
    os.makedirs(out, exist_ok=True)
    W, E, A = [], [], []
    files = sorted(f for f in glob.glob(f"{SRC}/{prefix}_*.json"))
    for wid, f in enumerate(files, 1):
        j = json.load(open(f)); cfg, met, tag = j["config"], j["metrics"], j["tag"]
        ev = [json.loads(l) for l in open(f.replace(".json", ".events.jsonl"))]
        m = re.match(rf"{prefix}_(auth|noauth)_(plurality|ranked)_(\w+?)_b(\d)_s(\d)$", tag)
        authority, rule, pop, bonus, seed = m.groups()
        models = cfg["models"]; n = cfg["n_agents"]
        W.append(dict(world_id=wid, tag=tag, seed=int(seed),
                      authority="binding" if authority == "auth" else "advisory",
                      rule=rule, population=pop, rent=int(bonus),
                      n_elections=met["n_elections"],
                      n_nocand=round(met["empty_election_share"] * met["n_elections"]),
                      n_contested=round(met["contested_share"] * met["n_elections"]),
                      gini=met["gini_task_access"], reelect=met["reelection_rate"],
                      transfers=met["n_transfers"], max_holder_spell=met["max_holder_spell"],
                      max_exclusion_spell=met["max_exclusion_spell"],
                      top_holder_day_share=met["top_holder_day_share"],
                      vfa_exchanges=met["vote_for_access_exchanges"],
                      gifted_winner=met["gifted_vote_share_winner"], gifted_loser=met["gifted_vote_share_loser"],
                      promises=met["access_promises"], promise_honor=met["promise_honor_rate"],
                      vacant_day_share=met["vacant_day_share"], parse_failures=met["parse_failures"],
                      cost_usd=met["llm_cost_usd"]))
        start, alloc_t = replay(cfg, ev)
        # elections
        for x in ev:
            if x["type"] != "election":
                continue
            d = x["day"]; rank = [(start[d] > start[d][i]).sum() for i in range(n)]
            for i in range(n):
                E.append(dict(world_id=wid, election_id=d // cfg["term"], agent_id=i,
                              family=model_family(models[i]), capability=model_cap(models[i]),
                              model=models[i], stood=int(i in x["candidates"]),
                              won=int(x["winner"] == i), energy_rank_before=int(rank[i]),
                              held_before=int(x["incumbent"] == i)))
        # allocations
        cum = np.zeros(n); gifts = np.zeros((n, n))
        trans = {}
        for x in ev:
            if x["type"] == "transfer":
                trans.setdefault(x["day"], []).append(x)
        for x in sorted((y for y in ev if y["type"] == "allocation"), key=lambda y: y["day"]):
            d, h = x["day"], x["holder"]
            for t in trans.get(d, []):
                gifts[t["frm"], t["to"]] += t["amount"]
            binding_active = int(bool(x["binding"]) and h is not None)
            for i in range(n):
                A.append(dict(world_id=wid, day=d, slot=0, agent_id=i,
                              holder_id=-1 if h is None else h, binding_active=binding_active,
                              received=int(i in x["winners"]), cum_tasks_before=cum[i],
                              energy_before=alloc_t[d][i],
                              gifted_holder_before=0 if h is None else gifts[i, h], rent=int(bonus)))
            for w in x["winners"]:
                cum[w] += 1
    pd.DataFrame(W).to_csv(f"{out}/worlds.csv", index=False)
    pd.DataFrame(E).to_csv(f"{out}/elections.csv", index=False)
    pd.DataFrame(A).to_csv(f"{out}/allocations.csv", index=False)
    print(prefix, "worlds", len(W), "election rows", len(E), "allocation rows", len(A))


convert("main", f"{OUT}/main")
convert("h2", f"{OUT}/h2")
