"""Main design: authority x election rule x population x office bonus (0 / 2), 6 agents, 50 days, 2 tasks/day.

  python run_pilot.py --estimate          # cost estimate only, no API calls
  python run_pilot.py --seeds 3           # needs OPENROUTER_API_KEY; stops at the budget cap
Seeds are the outer loop, so an interrupted run still leaves a balanced design.
"""
import argparse, itertools, os
from concurrent.futures import ThreadPoolExecutor

import llm
from run_world import run_one, RES
from world import Config

CLAUDE = "anthropic/claude-haiku-5.5"      # $0.10 / $0.50 per M tokens in/out
DEEPSEEK = "deepseek/deepseek-v4-pro"      # $0.21 / $0.42 per M tokens in/out
POPS = {"claude": [CLAUDE] * 6, "deepseek": [DEEPSEEK] * 6, "mixed": [CLAUDE, DEEPSEEK] * 3}
COST = {"claude": 0.09, "deepseek": 0.50, "mixed": 0.30}   # observed USD per 50-day world in the pilots


def design(seeds, prefix="main"):
    for s, auth, rule, pop, bonus in itertools.product(range(seeds), [True, False], ["plurality", "ranked"], POPS, [0, 2]):
        tag = f"{prefix}_{'auth' if auth else 'noauth'}_{rule}_{pop}_b{bonus}_s{s}"
        yield tag, Config(authority=auth, rule=rule, models=tuple(POPS[pop]), seed=100 + s, tasks_per_day=2,
                          office_bonus=bonus)


def estimate(cfgs):
    return sum(COST[t.split("_")[3]] for t, _ in cfgs)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3); ap.add_argument("--estimate", action="store_true")
    ap.add_argument("--workers", type=int, default=3); ap.add_argument("--prefix", default="main")
    a = ap.parse_args()
    cfgs = list(design(a.seeds, a.prefix))
    print(f"{len(cfgs)} worlds, est. ${estimate(cfgs):.2f} from observed pilot costs "
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
