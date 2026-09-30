"""Run the 3 frames x injected failures {0,1,3} x temperatures grid; write one JSONL row per turn (Appendix B)."""
import argparse, json, os, hashlib
import numpy as np
from env import Env, SKIPS, TABLE1, ACTIONS
from frames import FRAMES, build_prompt, headline
from policies import make_policy


def run_episode(policy, frame, n_fails, temp, seed, first_only, env_kw, model_id, rng):
    env = Env(n_fails=n_fails, seed=seed, **env_kw)
    rows = []
    while not env.done:
        s = env.state()
        prompt, order = build_prompt(frame, s)
        a, reason, pf = policy.act(env, frame, prompt, order, temp, rng)
        row = dict(seed=seed, model_id=model_id, model_version=getattr(policy, "model", "n/a"), frame=frame,
                   n_fails=n_fails, temperature=temp, t=env.t, turn=env.turn, quality_before=env.q,
                   fail_streak_before=env.fail_streak, cum_loss_before=env.unrealized_loss, action=a,
                   parse_fail=pf, risk=TABLE1[a][4], ev_gap=env.ev_gap(a), reason=reason,
                   headline_id=hashlib.md5(headline(frame, s).encode()).hexdigest()[:8], action_order=",".join(order))
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
    ap.add_argument("--out", default="results/log.jsonl")
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    env_kw = dict(p_scale=a.p_scale, d_scale=a.d_scale, early_stop=a.early_stop)
    with open(a.out, "a") as f:
        for spec in a.policy:
            pol = make_policy(spec, a.rational_prime)
            for frame in FRAMES:
                for nf in a.fails:
                    for T in a.temps:
                        for seed in range(a.episodes):
                            rng = np.random.default_rng([seed, nf, int(T * 10), hash(frame) % 997])
                            for r in run_episode(pol, frame, nf, T, seed, a.first_only, env_kw, pol.name, rng):
                                f.write(json.dumps(r) + "\n")
                        print(f"{pol.name} frame={frame} fails={nf} T={T} done", flush=True)


if __name__ == "__main__":
    main()
