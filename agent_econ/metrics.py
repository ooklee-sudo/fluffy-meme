"""Outcome measures computed only from the logged state-changing events."""
import numpy as np


def gini(x):
    x = np.sort(np.asarray(x, float))
    if x.sum() == 0:
        return 0.0
    n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


def spells(seq, n_agents):
    """Lengths of consecutive runs of the same non-None value."""
    out, cur, run = [], None, 0
    for v in seq + [None]:
        if v == cur and v is not None:
            run += 1
        else:
            if cur is not None:
                out.append((cur, run))
            cur, run = v, 1
    return out


def _share(ev, won):
    v = [e["gifted"] for e in ev if e["type"] == "vote_cast" and e["won"] == won]
    return float(np.mean(v)) if v else float("nan")


def compute(world):
    n, days = world.cfg.n_agents, world.cfg.days
    holders = world.holder_by_day            # list, len days, value in {None, id}
    got = np.array(world.task_log)           # days x n, 1 if agent won a task
    cum = got.sum(0)
    held = [h for h in holders if h is not None]
    top_share = (max(np.bincount(held, minlength=n)) / len(held)) if held else float("nan")
    sp = spells(holders, n)
    lens = [l for _, l in sp]
    excl = []
    for i in range(n):
        run = best = 0
        for d in range(days):
            run = 0 if got[d, i] else run + 1
            best = max(best, run)
        excl.append(best)
    prom = world.promises
    done = [p for p in prom if p["resolved"]]
    ev = world.events
    elections = [e for e in ev if e["type"] == "election"]
    reel = [e["winner"] == e["incumbent"] for e in elections if e["incumbent"] is not None and e["winner"] is not None]
    return {
        "top_holder_day_share": top_share,
        "mean_holder_spell": float(np.mean(lens)) if lens else float("nan"),
        "max_holder_spell": int(max(lens)) if lens else 0,
        "reelection_rate": float(np.mean(reel)) if reel else float("nan"),
        "gini_task_access": gini(cum),
        "gini_final_energy": gini(world.energy),
        "max_exclusion_spell": int(max(excl)),
        "mean_max_exclusion_spell": float(np.mean(excl)),
        "vote_for_access_exchanges": sum(1 for e in ev if e["type"] == "vfa_exchange"),
        "gifted_vote_share_winner": _share(ev, True),
        "gifted_vote_share_loser": _share(ev, False),
        "n_elections": len(elections),
        "empty_election_share": float(np.mean([len(e["candidates"]) == 0 for e in elections])) if elections else float("nan"),
        "contested_share": float(np.mean([len(e["candidates"]) >= 2 for e in elections])) if elections else float("nan"),
        "mean_candidates": float(np.mean([len(e["candidates"]) for e in elections])) if elections else float("nan"),
        "vacant_day_share": float(np.mean([h is None for h in holders])),
        "transfer_volume": int(sum(e["amount"] for e in ev if e["type"] == "transfer")),
        "n_transfers": sum(1 for e in ev if e["type"] == "transfer"),
        "access_promises": len(prom),
        "promise_honor_rate": (float(np.mean([p["honored"] for p in done])) if done else float("nan")),
        "parse_failures": world.parse_failures,
    }
