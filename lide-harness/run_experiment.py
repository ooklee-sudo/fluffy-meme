"""Run Studies 1 and 2.

Examples:
  python run_experiment.py --config config.yaml --estimate
  python run_experiment.py --config config.yaml --dry-run          # mock models, no API calls
  python run_experiment.py --config config.yaml --study study1 --workers 4
"""
from __future__ import annotations

import argparse
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

from lide.conditions import build_design, episode_id
from lide.runner import run_episode

MOCK_MODELS = [
    {"name": "mock-honest", "provider": "mock", "family": "mock", "generation": "1", "size": "s"},
    {"name": "mock-hacker", "provider": "mock", "family": "mock", "generation": "1", "size": "s"},
]


def plan_jobs(cfg: dict, study: str | None, models: list[dict]) -> list[tuple]:
    cells = build_design(cfg)
    if study:
        cells = [c for c in cells if c.study.startswith(study)]
    reps = cfg.get("repetitions", 10)
    jobs = [(c, m, r) for c in cells for m in models for r in range(reps)]
    random.Random(cfg.get("seed", 0)).shuffle(jobs)  # spread conditions over time
    return jobs


def estimate(cfg: dict, jobs: list[tuple]) -> None:
    est = cfg.get("estimate", {})
    tin, tout = est.get("input_tokens_per_episode", 60000), est.get("output_tokens_per_episode", 4000)
    per_model: dict[str, int] = {}
    for _, m, _ in jobs:
        per_model[m["name"]] = per_model.get(m["name"], 0) + 1
    total = 0.0
    print(f"Episodes planned: {len(jobs)}")
    for name, n in per_model.items():
        price = cfg.get("pricing", {}).get(name, {})
        cost = n * (tin * price.get("input_per_mtok", 0) + tout * price.get("output_per_mtok", 0)) / 1e6
        total += cost
        flag = "" if price else "  (no price in config)"
        print(f"  {name}: {n} episodes, ~${cost:,.0f}{flag}")
    print(f"Estimated total: ~${total:,.0f} "
          f"(assumes {tin:,} input and {tout:,} output tokens per episode; calibrate with a pilot)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--study", choices=["study1", "study2"], default=None)
    ap.add_argument("--dry-run", action="store_true", help="use scripted mock models")
    ap.add_argument("--estimate", action="store_true", help="print planned episodes and cost only")
    ap.add_argument("--max-episodes", type=int, default=None)
    ap.add_argument("--workers", type=int, default=None)
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())
    models = MOCK_MODELS if args.dry_run else cfg["models"]
    jobs = plan_jobs(cfg, args.study, models)
    if args.estimate:
        estimate(cfg, jobs)
        return

    out_dir = Path(cfg.get("output", {}).get("dir", "results")) / ("dry_run" if args.dry_run else "")
    out_dir.mkdir(parents=True, exist_ok=True)
    todo = [j for j in jobs if not (out_dir / f"{episode_id(j[0], j[1]['name'], j[2])}.json").exists()]
    if args.max_episodes:
        todo = todo[: args.max_episodes]
    print(f"{len(jobs)} episodes in design, {len(jobs) - len(todo)} already done, running {len(todo)}.")

    workers = args.workers or cfg.get("workers", 2)
    done = errors = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_episode, c, m, r, cfg): (c, m, r) for c, m, r in todo}
        for fut in as_completed(futures):
            rec = fut.result()
            path = out_dir / f"{rec['episode_id']}.json"
            if rec["status"] == "ok":
                path.write_text(json.dumps(rec, indent=1, default=str))
                done += 1
            else:
                errors += 1
                (out_dir / "errors").mkdir(exist_ok=True)
                (out_dir / "errors" / path.name).write_text(json.dumps(rec, indent=1, default=str))
                print(f"ERROR {rec['episode_id']}: {rec.get('error')}")
            if (done + errors) % 25 == 0:
                print(f"  progress: {done + errors}/{len(todo)} ({errors} errors)")
    print(f"Finished: {done} ok, {errors} errors. Results in {out_dir}/")


if __name__ == "__main__":
    main()
