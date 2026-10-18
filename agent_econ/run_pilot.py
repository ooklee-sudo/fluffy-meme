"""Pilot: authority x election rule x population (Claude / DeepSeek / mixed), 6 agents, 50 days.

  python run_pilot.py --estimate          # cost estimate only, no API calls
  python run_pilot.py --seeds 2           # run (needs OPENROUTER_API_KEY; stops at the budget cap)
"""
import argparse, itertools, os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import llm
from run_world import run_one, RES
from world import Config

CLAUDE = "anthropic/claude-haiku-5.5"      # $0.10 / $0.50 per M tokens in/out
DEEPSEEK = "deepseek/deepseek-v4-pro"      # $0.21 / $0.42 per M tokens in/out
PRICE = {CLAUDE: (0.10, 0.50), DEEPSEEK: (0.21, 0.42)}
POPS = {"claude": [CLAUDE] * 6, "deepseek": [DEEPSEEK] * 6, "mixed": [CLAUDE, DEEPSEEK] * 3}


def design(seeds):
    for auth, rule, pop, s in itertools.product([True, False], ["plurality", "ranked"], POPS, range(seeds)):
        tag = f"pilot_{'auth' if auth else 'noauth'}_{rule}_{pop}_s{s}"
        yield tag, Config(authority=auth, rule=rule, models=tuple(POPS[pop]), seed=s)


def estimate(cfgs, tin=1800, tout=350):
    calls = 6 * 50 + 6 * 10 + 50
    tot = 0.0
    for _, c in cfgs:
        for m in c.models:
            p = PRICE[m]
            tot += (calls / 6) * (tin * p[0] + tout * p[1]) / 1e6
    return calls, tot


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=2); ap.add_argument("--estimate", action="store_true")
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    cfgs = list(design(a.seeds))
    calls, usd = estimate(cfgs)
    print(f"{len(cfgs)} worlds, ~{calls} calls/world, assumed 1800 in / 350 out tokens per call -> est. ${usd:.2f} "
          f"(cap ${llm.CAP_USD:.0f}, already spent ${llm.spent():.2f})")
    if a.estimate:
        raise SystemExit
    todo = [(t, c) for t, c in cfgs if not os.path.exists(os.path.join(RES, f"{t}.json"))]

    def go(tc):
        try:
            r = run_one(tc[1], tc[0])
            print(f"done {tc[0]}  cost ${r['metrics']['llm_cost_usd']:.3f}  total ${llm.spent():.2f}", flush=True)
        except llm.BudgetExceeded as e:
            print("STOP:", e, flush=True)

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(go, todo))
