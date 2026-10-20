"""Study 2 (prompt variation): does the specification, not only the model, decide how holders use authority?

  python run_study2.py --estimate                      # 2a-lite: DeepSeek, assigned holder, rent 2, 3 prompts x 12 seeds
  python run_study2.py --stage 2b --estimate           # elected holder (selection and entrenchment)
  python run_study2.py --models scripted --seeds 2     # pipeline test with rule-based agents, never evidence
  python run_study2.py --run --seeds 12                # needs OPENROUTER_API_KEY; stops at the budget cap
Seeds are the outer loop, so an interrupted run still leaves a balanced design. Study 1 seeds are 100-205; Study 2 uses 3000+.
"""
import argparse, itertools, os
from concurrent.futures import ThreadPoolExecutor

import llm
from run_world import run_one, RES
from world import Config

FAMILY = {"deepseek": "deepseek/deepseek-v4-pro", "claude": "anthropic/claude-haiku-5.5"}
COST = {"deepseek": 0.62, "claude": 0.09, "scripted": 0.0}   # observed USD per 50-day world: DeepSeek 0.62 in the Study 2 pilot (0.15 in Study 1: price per token rose ~3x); Claude figure is from Study 1
PROMPTS = ["baseline", "self_interest", "collective_duty"]   # "stripped" needs the prompt audit first and is not implemented
CONTROLS = ["content_free_eval", "role_only"]                # added after Study 2a: evaluation without a criterion; role sentence without evaluation
PAIR = {"baseline": 0, "self_interest": 1, "collective_duty": 2, "content_free_eval": 0, "role_only": 0}   # controls reuse the baseline wording pattern per seed


def design(stage, families, rents, seeds, prompts=PROMPTS, paraphrases=(0, 1)):
    for s, fam, rent, p, para in itertools.product(range(seeds), families, rents, prompts, paraphrases):
        if len(paraphrases) == 2 and (s + PAIR[p]) % 2 != para:   # lite: alternate wording across seeds, one world per cell-seed
            continue
        model = FAMILY.get(fam, "scripted:0")
        tag = f"s2{stage[-1]}_{fam}_b{rent}_{p}_p{para}_s{s}"
        yield tag, Config(authority=True, rule="plurality", models=(model,) * 6, seed=3000 + s, tasks_per_day=2,
                          office_bonus=rent, assign_office=(stage == "2a"), prompt=p, paraphrase=para)


def estimate(cfgs):
    return sum(COST[t.split("_")[1]] for t, _ in cfgs)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="2a", choices=["2a", "2b"])
    ap.add_argument("--models", nargs="+", default=["deepseek"], help="families: deepseek claude scripted")
    ap.add_argument("--rents", nargs="+", type=int, default=[2]); ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--workers", type=int, default=3); ap.add_argument("--estimate", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--prompts", nargs="+", default=PROMPTS, choices=PROMPTS + CONTROLS, help="restrict to some prompt levels, e.g. --prompts baseline")
    a = ap.parse_args()
    cfgs = list(design(a.stage, a.models, a.rents, a.seeds, prompts=list(a.prompts)))
    print(f"{len(cfgs)} worlds, est. ${estimate(cfgs):.2f} (cap ${llm.CAP_USD:.0f}, already spent ${llm.spent():.2f})")
    if a.estimate or not (a.run or a.models == ["scripted"]):
        raise SystemExit
    todo = [(t, c) for t, c in cfgs if not os.path.exists(os.path.join(RES, f"{t}.json"))]

    def go(tc):
        try:
            r = run_one(tc[1], tc[0])
            print(f"done {tc[0]}  cost ${r['metrics']['llm_cost_usd']:.3f}  self-share {r['metrics']['holder_self_share']:.2f}", flush=True)
        except llm.BudgetExceeded as e:
            print("STOP:", e, flush=True)

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(go, todo))
