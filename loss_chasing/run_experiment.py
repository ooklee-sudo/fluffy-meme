"""Run the 3 frames x injected failures {0,1,3} x temperatures grid; write one JSONL row per turn (Appendix B)."""
import argparse, json, os, hashlib
import numpy as np
from env import Env, SKIPS, TABLE1, ACTIONS
from frames import FRAMES, build_prompt, headline
from policies import make_policy


def run_episode(policy, frame, n_fails, temp, seed, first_only, env_kw, model_id, rng, variant=0):
    env = Env(n_fails=n_fails, seed=seed, **env_kw)
    rows = []
    while not env.done:
        s = env.state()
        prompt, order = build_prompt(frame, s, variant)
        a, reason, pf = policy.act(env, frame, prompt, order, temp, rng)
        row = dict(seed=seed, model_id=model_id, model_version=getattr(policy, "model", "n/a"), frame=frame,
                   n_fails=n_fails, temperature=temp, t=env.t, turn=env.turn, quality_before=env.q,
                   fail_streak_before=env.fail_streak, cum_loss_before=env.unrealized_loss, action=a,
                   parse_fail=pf, risk=TABLE1[a][4], ev_gap=env.ev_gap(a), reason=reason,
                   variant=variant, headline_id=hashlib.md5(headline(frame, s, variant).encode()).hexdigest()[:8], action_order=",".join(order))
        usage = getattr(policy, "last_usage", None)
        row["tokens_in"], row["tokens_out"] = usage if usage else (None, None)
        row["temperature_applied"] = getattr(policy, "controls_temperature", True)
        row["outcome"] = env.step(a)
        row["quality_after"] = env.q
        rows.append(row)
        if first_only:
            break
    for r in rows:
        r["terminal_quality"] = env.q
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", action="append", required=True,
                    help="anthropic:<model> | openai:<model> | hf:<hub id> (local) | hfapi:<hub id> (Inference API) | greedy | always:narrow_patch | always:hold | synthetic")
    ap.add_argument("--episodes", type=int, default=100, help="seeded episodes per cell")
    ap.add_argument("--temps", type=float, nargs="+", default=[0.0, 0.7])
    ap.add_argument("--fails", type=int, nargs="+", default=[0, 1, 3])
    ap.add_argument("--first-only", action="store_true", help="only the primary first free choice (cheap: 1 call/episode)")
    ap.add_argument("--rational-prime", action="store_true", help="optional correction condition (Sec 5)")
    ap.add_argument("--p-scale", type=float, default=1.0)
    ap.add_argument("--d-scale", type=float, default=1.0)
    ap.add_argument("--early-stop", action="store_true")
    ap.add_argument("--variants", type=int, nargs="+", default=[0], help="headline wordings to run (0 = registered, 1-3 = paraphrases)")
    ap.add_argument("--workers", type=int, default=1, help="parallel API calls per cell (API backends only; 4 is a sensible start)")
    ap.add_argument("--start-t", type=int, default=0, help="turns already spent at the first choice (12 - start_t remain); time-pressure pilot")
    ap.add_argument("--resume", action="store_true",
                    help="append to --out and skip episodes (model, frame, fails, temp, seed) that are already logged")
    ap.add_argument("--out", default="results/log.jsonl")
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    env_kw = dict(p_scale=a.p_scale, d_scale=a.d_scale, early_stop=a.early_stop, start_t=a.start_t)
    done = set()
    if a.resume and os.path.exists(a.out):
        for line in open(a.out):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:          # half-written last line after an interrupt
                continue
            if r["turn"] == 0:                     # an episode is logged once its first turn exists
                done.add((r["model_id"], r["frame"], r["n_fails"], r["temperature"], r["seed"], r.get("variant", 0)))
        print(f"resume: {len(done)} episodes already logged", flush=True)
    elif os.path.exists(a.out) and os.path.getsize(a.out) > 0:
        raise SystemExit(f"{a.out} already has data. Use --resume to continue it, or delete/rename it to start over.")
    if a.resume and os.path.exists(a.out) and os.path.getsize(a.out) > 0:
        with open(a.out, "rb+") as fb:            # a torn last line must not swallow the next row
            fb.seek(-1, os.SEEK_END)
            if fb.read(1) != b"\n":
                fb.write(b"\n")
    with open(a.out, "a") as f:
        for spec in a.policy:
            pol = make_policy(spec, a.rational_prime)
            temps = a.temps
            if not getattr(pol, "controls_temperature", True):
                temps = a.temps[:1]
                print(f"NOTE: {pol.name} rejects temperature; sampling is the model default. Running one temperature label ({temps[0]}), "
                      f"logged with temperature_applied=false.", flush=True)
            for frame in FRAMES:
                for nf in a.fails:
                    for T in temps:
                        for v in a.variants:
                            todo = [s for s in range(a.episodes) if (pol.name, frame, nf, T, s, v) not in done]
                            def one(seed, frame=frame, nf=nf, T=T, v=v):
                                rng = np.random.default_rng([seed, nf, int(T * 10), FRAMES.index(frame), v])
                                return run_episode(pol, frame, nf, T, seed, a.first_only, env_kw, pol.name, rng, v)
                            if a.workers > 1 and len(todo) > 1:
                                from concurrent.futures import ThreadPoolExecutor, as_completed
                                with ThreadPoolExecutor(max_workers=a.workers) as ex:
                                    futs = [ex.submit(one, s) for s in todo]
                                    try:
                                        for fu in as_completed(futs):
                                            for row in fu.result():
                                                f.write(json.dumps(row) + "\n")
                                            f.flush()
                                    except BaseException:
                                        for fu in futs: fu.cancel()
                                        raise
                            else:
                                for s in todo:
                                    for row in one(s):
                                        f.write(json.dumps(row) + "\n")
                                    f.flush()
                            tag = f" variant={v}" if len(a.variants) > 1 or v else ""
                            print(f"{pol.name} frame={frame} fails={nf} T={T}{tag} done{getattr(pol, 'cost_line', lambda: '')()}", flush=True)


if __name__ == "__main__":
    main()
