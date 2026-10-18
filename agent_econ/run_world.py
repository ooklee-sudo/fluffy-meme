"""Run one world and write its config, metrics and event log under results/."""
import argparse, json, os, sys
from dataclasses import asdict
from world import Config, World

RES = os.path.join(os.path.dirname(__file__), "results")


def run_one(cfg, tag):
    w = World(cfg)
    m = w.run()
    os.makedirs(RES, exist_ok=True)
    scripted = all(x.startswith("scripted") for x in cfg.models)
    out = {"tag": tag, "evidence": not scripted, "config": asdict(cfg), "metrics": m}
    json.dump(out, open(os.path.join(RES, f"{tag}.json"), "w"), indent=1, default=str)
    with open(os.path.join(RES, f"{tag}.events.jsonl"), "w") as f:
        for e in w.events:
            f.write(json.dumps(e) + "\n")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True, help="one id (repeated) or one id per agent; 'scripted' for a dry run")
    ap.add_argument("--n", type=int, default=6); ap.add_argument("--days", type=int, default=50)
    ap.add_argument("--tasks", type=int, default=3); ap.add_argument("--rule", default="plurality")
    ap.add_argument("--no-authority", action="store_true"); ap.add_argument("--reputation", action="store_true")
    ap.add_argument("--neutral", action="store_true"); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()
    models = tuple(a.models * a.n) if len(a.models) == 1 else tuple(a.models)
    cfg = Config(n_agents=a.n, days=a.days, tasks_per_day=a.tasks, authority=not a.no_authority, rule=a.rule,
                 reputation=a.reputation, framing="neutral" if a.neutral else "survival", models=models, seed=a.seed)
    print(json.dumps(run_one(cfg, a.tag)["metrics"], indent=1))
