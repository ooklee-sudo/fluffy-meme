"""Run Study 1 (Environment A) episodes and append them to a JSONL file.

Examples
  python run.py --scripted                       # known-groups check, no API calls
  python run.py --models anthropic/claude-haiku-5.5 --reps 1 --cells 2   # smoke test
  python run.py --models m1 m2 --reps 8 --out results/study1.jsonl --budget 40
Episodes already in the output file are skipped, so a stopped run can be resumed.
"""
import argparse
import hashlib
import json
import pathlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from agents import APIError, run_llm_episode, run_scripted_episode
from conditions import frontier_cells, info_control_cells, study1_cells
from env_coding import CodingEnv

lock = threading.Lock()
spent = {"cost": 0.0}


def episode_id(model, cell, rep):
    return f"{model}|{cell['history']}|{cell['scarcity']}|{cell['record']}|{rep}"


def run_one(model, cell, rep, temperature):
    seed = int(hashlib.sha256(episode_id(model, cell, rep).encode()).hexdigest()[:8], 16)
    env = CodingEnv()
    try:
        if model.startswith("scripted:"):
            transcript, usage = run_scripted_episode(env, model.split(":")[1])
        else:
            transcript, usage = run_llm_episode(env, model, cell, seed, temperature)
        rec = {"id": episode_id(model, cell, rep), "model": model, **cell, "rep": rep, "seed": seed,
               **env.outcome(), "usage": usage, "transcript": transcript}
    except APIError as e:
        rec = {"id": episode_id(model, cell, rep), "model": model, **cell, "rep": rep, "error": str(e)[:500]}
    finally:
        env.close()
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=[])
    ap.add_argument("--scripted", action="store_true")
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--cells", type=int, default=None, help="use only the first N cells (smoke test)")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--budget", type=float, default=10.0, help="stop submitting new episodes past this USD spend")
    ap.add_argument("--out", default="results/study1.jsonl")
    ap.add_argument("--design", choices=["study1", "info", "frontier"], default="study1",
                    help="info = loss x information control cells (NI, F2a, F8a)")
    a = ap.parse_args()

    models = list(a.models) + (["scripted:honest", "scripted:escalating"] if a.scripted else [])
    all_cells = {"study1": study1_cells, "info": info_control_cells, "frontier": frontier_cells}[a.design]()
    cells = all_cells[: a.cells] if a.cells else all_cells
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for line in out.read_text().splitlines():
            r = json.loads(line)
            if "error" not in r:
                done.add(r["id"])
    # interleave models and cells so a budget stop leaves a balanced design
    jobs = [(m, c, r) for r in range(a.reps) for c in cells for m in models
            if episode_id(m, c, r) not in done]
    print(f"{len(jobs)} episodes to run ({len(done)} already done)")

    with ThreadPoolExecutor(a.workers) as ex, out.open("a") as f:
        futs = {}
        it = iter(jobs)

        def submit_next():
            if spent["cost"] >= a.budget:
                return
            j = next(it, None)
            if j:
                futs[ex.submit(run_one, *j, a.temperature)] = j

        for _ in range(a.workers * 2):
            submit_next()
        n = 0
        while futs:
            fut = next(as_completed(futs))
            futs.pop(fut)
            rec = fut.result()
            with lock:
                spent["cost"] += rec.get("usage", {}).get("cost", 0.0)
                f.write(json.dumps(rec) + "\n")
                f.flush()
            n += 1
            tag = rec.get("error", "")[:80] or (
                f"{rec['terminal']:<14} unsafe={int(rec['unsafe'])} risk={rec['mean_risk']:.2f}")
            print(f"[{n}/{len(jobs)}] ${spent['cost']:.2f} {rec['id']:<60} {tag}", flush=True)
            submit_next()
    if spent["cost"] >= a.budget:
        print(f"Budget of ${a.budget} reached; rerun the same command to resume.")


if __name__ == "__main__":
    main()
