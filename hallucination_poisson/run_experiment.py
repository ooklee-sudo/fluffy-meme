"""Run the Poisson / guardrail framework on a real LLM.

  python run_experiment.py collect --generator hf:Qwen/Qwen2.5-0.5B-Instruct --judge hf:Qwen/Qwen2.5-1.5B-Instruct \
         --dataset hf:rajpurkar/squad_v2 --n 300 --out runs/qwen
  python run_experiment.py analyze --run runs/qwen --days 90 --daily-queries 200 --alpha 0.95
  python run_experiment.py demo                       # offline smoke test with a fake model

collect : (expensive, once) generate answers with the LLM under test, label hallucinations against gold,
          run all three guardrail layers on every answer, record outputs + latencies.
analyze : (cheap, repeatable) replay NHPP traffic over the labelled pool, fit lambda, test the Poisson
          assumptions, compute k*, and pick the best guardrail stack under the latency budget.
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis import LAYERS, bootstrap_ci, Costs, Weights, daily_cost, layer_dependence, load_arrays, optimise
from backends import make_backend
from data import is_abstain, is_hallucination, load_examples
from layers import ClassifierLayer, DeterministicLayer, JudgeLayer
from stats_model import DEFAULT_PROFILE, analyse_events, capacity, simulate_traffic

GEN_SYSTEM = {
    "rag": "Answer the question using the passage. Reply with a short answer only (a few words). "
           "If the passage does not contain the answer, reply exactly: UNANSWERABLE.",
    "closed": "Answer the question with a short answer only (a few words). "
              "If you do not know the answer, reply exactly: UNANSWERABLE.",
}


def collect(args):
    os.makedirs(args.out, exist_ok=True)
    gen = make_backend(args.generator)
    judge_backend = gen if args.judge == "same" else make_backend(args.judge)
    l1, l2, l3 = DeterministicLayer(), ClassifierLayer(args.l2, args.block_thr), JudgeLayer(judge_backend)
    examples = load_examples(args.dataset, args.n, args.seed)
    print(f"{len(examples)} examples | generator={gen.spec} judge={judge_backend.spec} l2={args.l2}")
    recs = []
    with open(os.path.join(args.out, "records.jsonl"), "w", encoding="utf-8") as f:
        for i, ex in enumerate(examples):
            user = (f"Passage: {ex.context}\nQuestion: {ex.question}" if args.mode == "rag"
                    else f"Question: {ex.question}")
            t0 = time.perf_counter()
            ans = gen.generate(user, system=GEN_SYSTEM[args.mode], max_tokens=args.max_tokens,
                               temperature=args.temperature)
            gen_ms = (time.perf_counter() - t0) * 1000
            ans = ans.strip().split("\n")[0]
            rec = {"id": ex.id, "question": ex.question, "answerable": ex.answerable, "gold": ex.answers,
                   "answer": ans, "abstained": is_abstain(ans), "hallucinated": is_hallucination(ex, ans),
                   "gen_latency_ms": gen_ms}
            # layers always verify against the evidence passage (retrieval-grounded verification)
            for layer in (l1, l2, l3):
                flag, score, lat, err = layer(ex.question, ans, ex.context)
                rec[layer.name] = {"flag": bool(flag), "score": score, "latency_ms": lat, "error": err}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            recs.append(rec)
            if (i + 1) % 20 == 0 or i + 1 == len(examples):
                h = np.mean([r["hallucinated"] for r in recs])
                print(f"  {i + 1}/{len(examples)}  hallucination rate so far {h:.3f}", flush=True)
    meta = vars(args) | {"n_collected": len(recs)}
    json.dump(meta, open(os.path.join(args.out, "meta.json"), "w"), indent=2, default=str)
    print("saved", args.out)


def retime(args):
    """Re-run the three guardrail layers on the stored answers (no generation) to re-measure latency
    without CPU contention from other jobs. Flags are deterministic, latencies are refreshed."""
    meta = json.load(open(os.path.join(args.run, "meta.json")))
    if args.l2:
        meta["l2_previous"], meta["l2"] = meta.get("l2"), args.l2
        meta["block_thr"] = args.block_thr
        json.dump(meta, open(os.path.join(args.run, "meta.json"), "w"), indent=2, default=str)
    path = os.path.join(args.run, "records.jsonl")
    import shutil
    backup = os.path.join(args.run, f"records_{(meta.get('l2_previous') or meta['l2']).split(':')[0]}.jsonl")
    if args.l2 and not os.path.exists(backup):
        shutil.copy(path, backup)  # keep the previous layer outputs for the record
    recs = [json.loads(l) for l in open(path, encoding="utf-8")]
    ex = {e.id: e for e in load_examples(meta["dataset"], meta["n"], meta["seed"])}
    judge_spec = meta["generator"] if meta["judge"] == "same" else meta["judge"]
    l1, l2, l3 = DeterministicLayer(), ClassifierLayer(meta["l2"], meta["block_thr"]), JudgeLayer(make_backend(judge_spec))
    for layer in (l1, l2, l3):  # warm-up so one-off initialisation is not timed
        layer(recs[0]["question"], recs[0]["answer"], ex[recs[0]["id"]].context)
    for i, r in enumerate(recs):
        e = ex[r["id"]]
        for layer in (l1, l2, l3):
            flag, score, lat, err = layer(e.question, r["answer"], e.context)
            r[layer.name] = {"flag": bool(flag), "score": score, "latency_ms": lat, "error": err}
        if (i + 1) % 50 == 0:
            print(f"  retimed {i + 1}/{len(recs)}", flush=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("retimed", args.run)


def analyze(args):
    recs = [json.loads(l) for l in open(os.path.join(args.run, "records.jsonl"), encoding="utf-8")]
    a = load_arrays(recs)
    rng = np.random.default_rng(args.seed)
    w = Weights(args.w_capacity, args.w_latency, args.w_sysfail, args.w_fp)
    rows, best, c_marg = optimise(a, args.daily_queries, args.alpha, w, args.sla_ms, args.sla_metric,
                                  args.route_thr, args.timeout_ms)
    print(f"\npool: n={a['n']}  hallucination rate p0={a['hallu'].mean():.3f}  "
          f"abstention rate={a['abstain'].mean():.3f}  traffic={args.daily_queries}/day x {args.days} days")
    print("marginal clearance c_i:", {k: round(v, 3) for k, v in c_marg.items()})
    dep = layer_dependence(a)
    for k, v in dep.items():
        print(f"  layer dependence {k}: phi={v['phi']:.2f}  joint catch observed={v['joint_observed']:.3f} vs independent={v['joint_if_independent']:.3f}")
    costs = Costs(args.c_human, (0.0, args.c_call_l2, args.c_call_l3), args.c_false_block, args.c_residual)
    for r in rows:
        r["cost"] = daily_cost(r, args.daily_queries, costs)
    best_cost = min(rows, key=lambda r: r["cost"]["total"])
    print("\ndaily $ cost  (labour + compute + false-block + residual harm)")
    for r in rows:
        c = r["cost"]
        print(f"  {r['config']:<10} total ${c['total']:9.2f}  labour ${c['labour']:8.2f} compute ${c['compute']:7.2f} fp ${c['false_block']:7.2f} harm ${c['residual_harm']:8.2f}"
              f"{'  <-- cheapest' if r is best_cost else ''}")
    sens = sensitivity(a, args, w)
    ci = bootstrap_ci(a, [r["config"] for r in rows], args.daily_queries, args.alpha, args.route_thr, args.timeout_ms)
    print("\n95% bootstrap CI (resampling the evaluated pool)")
    for c, d in ci.items():
        print(f"  {c:<10} lambda/day [{d['lam'][0]:.1f}, {d['lam'][1]:.1f}]  k* [{d['k'][0]:.0f}, {d['k'][1]:.0f}]  latency ms [{d['lat'][0]:.0f}, {d['lat'][1]:.0f}]  FP/day [{d['fp'][0]:.1f}, {d['fp'][1]:.1f}]")

    hdr = f"{'config':<10}{'lam/day':>9}{'lam(indep)':>11}{'k*':>4}{'lat_ms':>9}{'p95_ms':>9}{'route':>7}{'FP/day':>8}{'sysfail':>8}{'objective':>10}  SLA"
    print("\n" + hdr)
    for r in rows:
        print(f"{r['config']:<10}{r['lambda_per_day']:9.2f}{r['lambda_independent_formula']:11.2f}{r['k_star']:4d}"
              f"{r['mean_latency_ms']:9.1f}{r['p95_latency_ms']:9.1f}{r['judge_route_rate']:7.2f}"
              f"{r['lambda_false_block']:8.1f}{r['lambda_sys_fail']:8.2f}{r['objective']:10.2f}  "
              f"{'ok' if r['feasible'] else 'VIOLATES'}")
    print(f"\nBest stack under {args.sla_metric} latency <= {args.sla_ms} ms: "
          f"{best['config'] if best else 'NONE FEASIBLE'}")

    # Poisson process replay: baseline vs best stack
    results = {"pool_hallucination_rate": float(a["hallu"].mean()), "marginal_clearance": c_marg,
               "layer_dependence": dep, "bootstrap_ci": ci, "cheapest_config": best_cost["config"], "sensitivity": sens, "burst_cv": args.burst_cv,
               "configs": rows, "best": best["config"] if best else None, "poisson_checks": {}}
    times = simulate_traffic(args.days, args.daily_queries, rng, DEFAULT_PROFILE, args.burst_cv)
    pool_idx = rng.integers(0, a["n"], len(times))  # each arriving query replays a random labelled example
    for r in [r for r in rows if r["config"] in ("none", (best or {}).get("config"))]:
        layers = [] if r["config"] == "none" else r["config"].split("+")
        crit = replay_critical_mask(a, layers, args.route_thr)
        ev = times[crit[pool_idx]]
        res = analyse_events(ev, args.days, args.alpha)
        results["poisson_checks"][r["config"]] = res
        print(f"\n[{r['config']}] critical failures: {res['n_events']} in {args.days} days  lambda_hat={res['lambda_per_day']:.2f}/day")
        print(f"  daily-count dispersion D={res['dispersion_D']:.1f} p={res['dispersion_p']:.3f}   (Poisson => D~chi2(n-1), p not tiny)")
        if "ks_raw_p" in res:
            print(f"  inter-arrival KS vs Exp  raw p={res['ks_raw_p']:.3g} | time-rescaled (NHPP) p={res['ks_rescaled_p']:.3g}")
        print(f"  hour-of-day homogeneity chi2 p={res['homogeneity_p']:.3g}  (small => genuinely non-homogeneous)")
        print(f"  k*(alpha={args.alpha}) Poisson={res['k_star_poisson']} empirical={res['k_star_empirical']}  "
              f"P(X>k*) poisson={res['p_exceed_k_star_poisson']:.3f} observed={res['p_exceed_k_star_observed']:.3f}")
        print(f"  negative-binomial fit r={res['nb_r']}  k*(NB)={res['k_star_negbin']}  P(X>k*_poisson) under NB={res['p_exceed_k_star_poisson_under_negbin']:.3f} (target {1 - args.alpha:.3f})")
        print(f"  capacity=round(lambda)={round(res['lambda_per_day'])}: exceeded on poisson={res['p_exceed_mean_capacity_poisson']:.1%}"
              f" observed={res['p_exceed_mean_capacity_observed']:.1%} of days")
    json.dump(results, open(os.path.join(args.run, f"analysis{args.tag}.json"), "w"), indent=2)
    try:
        plot(args, results, rows)
    except Exception as e:
        print("plot skipped:", e)


def sensitivity(a, args, w):
    """Cheapest cascade over a grid of false-block cost x residual-harm cost x daily traffic."""
    out = []
    for q in (args.daily_queries / 4, args.daily_queries, args.daily_queries * 4):
        for fp in (0.0, 1.0, 10.0):
            for harm in (0.0, 100.0, 1000.0):
                cs = Costs(args.c_human, (0.0, args.c_call_l2, args.c_call_l3), fp, harm)
                rows, _, _ = optimise(a, q, args.alpha, w, args.sla_ms, args.sla_metric, args.route_thr, args.timeout_ms)
                for r in rows:
                    r["cost"] = daily_cost(r, q, cs)
                feas = [r for r in rows if r["feasible"]] or rows
                b = min(feas, key=lambda r: r["cost"]["total"])
                out.append({"daily_queries": q, "c_false_block": fp, "c_residual": harm, "best": b["config"],
                            "total": b["cost"]["total"], "unprotected": next(r for r in rows if r["config"] == "none")["cost"]["total"]})
    return out


def replay_critical_mask(a, layers, route_thr):
    """Per-example bool: hallucinated and not blocked by the cascade (same logic as evaluate_cascade)."""
    alive = np.ones(a["n"], bool)
    for L in layers:
        run = alive & ~a["abstain"]
        if L == "L3" and "L2" in layers:
            ps = a["p_entail"]
            run &= np.where(np.isnan(ps), True, ps < route_thr)
        alive &= ~(run & a[f"{L}_flag"])
    return a["hallu"] & alive


def plot(args, results, rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy import stats

    checks = results["poisson_checks"]
    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    for name, res in checks.items():
        dc = np.array(res["daily_counts"])
        ks = np.arange(0, max(dc.max(), 3) + 3)
        ax[0].hist(dc, bins=np.arange(-0.5, ks.max() + 1.5), density=True, alpha=0.4, label=f"{name} observed")
        ax[0].plot(ks, stats.poisson.pmf(ks, res["lambda_per_day"]), "o-", label=f"{name} Poisson({res['lambda_per_day']:.1f})")
        if "hourly_intensity" in res:
            ax[1].plot(range(24), res["hourly_intensity"], label=name)
    ax[0].set(title="Daily critical failures vs Poisson", xlabel="events/day"); ax[0].legend(fontsize=7)
    ax[1].set(title="Fitted hourly intensity (NHPP)", xlabel="hour of day", ylabel="events/hour"); ax[1].legend()
    for r in rows:
        ax[2].scatter(r["mean_latency_ms"], r["k_star"], color="C2" if r["feasible"] else "C3")
        ax[2].annotate(r["config"], (r["mean_latency_ms"], r["k_star"]), fontsize=8)
    ax[2].axvline(args.sla_ms, ls="--", c="gray")
    ax[2].set(title="Guardrail trade-off", xlabel="mean added latency (ms)", ylabel="capacity k*")
    fig.tight_layout()
    fig.savefig(os.path.join(args.run, f"analysis{args.tag}.png"), dpi=130)
    print("saved", os.path.join(args.run, f"analysis{args.tag}.png"))


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--generator", required=True, help="LLM under test, e.g. hf:Qwen/Qwen2.5-0.5B-Instruct")
    c.add_argument("--judge", default="same", help="L3 judge backend spec, or 'same'")
    c.add_argument("--l2", default="qa:deepset/roberta-base-squad2", help="'qa:<hf extractive-QA id>' | 'nli:<hf id>' | 'overlap'")
    c.add_argument("--block-thr", type=float, default=0.5, help="L2 blocks if P(entail) < this")
    c.add_argument("--dataset", default="hf:rajpurkar/squad_v2", help="builtin | file.jsonl | hf:rajpurkar/squad_v2")
    c.add_argument("--mode", choices=["rag", "closed"], default="rag", help="give the generator the passage or not")
    c.add_argument("--n", type=int, default=300)
    c.add_argument("--max-tokens", type=int, default=32)
    c.add_argument("--temperature", type=float, default=0.0)
    c.add_argument("--seed", type=int, default=0)
    c.add_argument("--out", required=True)
    rt = sub.add_parser("retime", help="re-measure layer latencies on stored answers")
    rt.add_argument("--run", required=True)
    rt.add_argument("--l2", default=None, help="replace the L2 layer, e.g. qa:deepset/roberta-base-squad2")
    rt.add_argument("--block-thr", type=float, default=0.5)
    an = sub.add_parser("analyze")
    an.add_argument("--run", required=True)
    an.add_argument("--days", type=int, default=90)
    an.add_argument("--daily-queries", type=float, default=200)
    an.add_argument("--alpha", type=float, default=0.95)
    an.add_argument("--sla-ms", type=float, default=100.0)
    an.add_argument("--sla-metric", choices=["mean", "p95", "sum"], default="mean",
                    help="mean: expected added latency; p95: tail; sum: paper's sum_i L_i of per-layer means")
    an.add_argument("--route-thr", type=float, default=0.9, help="judge runs only if L2 P(entail) < this")
    an.add_argument("--timeout-ms", type=float, default=2000.0, help="layer call slower than this = system failure")
    an.add_argument("--w-capacity", type=float, default=1.0)
    an.add_argument("--w-latency", type=float, default=0.02)
    an.add_argument("--w-sysfail", type=float, default=1.0)
    an.add_argument("--w-fp", type=float, default=0.0)
    an.add_argument("--seed", type=int, default=0)
    an.add_argument("--tag", default="", help="suffix for output files, e.g. _burst")
    an.add_argument("--burst-cv", type=float, default=0.0, help="Cox/bursty traffic: CV of the daily intensity multiplier")
    an.add_argument("--c-human", type=float, default=150.0, help="$ per unit of triage capacity k* per day")
    an.add_argument("--c-call-l2", type=float, default=0.0001, help="$ per classifier call")
    an.add_argument("--c-call-l3", type=float, default=0.002, help="$ per judge call")
    an.add_argument("--c-false-block", type=float, default=0.0, help="$ per good answer wrongly blocked")
    an.add_argument("--c-residual", type=float, default=0.0, help="$ per hallucination reaching the user")
    d = sub.add_parser("demo")
    d.add_argument("--out", default="runs/demo")
    return p


def main():
    args = build_parser().parse_args()
    if args.cmd == "collect":
        collect(args)
    elif args.cmd == "retime":
        retime(args)
    elif args.cmd == "analyze":
        analyze(args)
    else:
        ns = build_parser().parse_args(["collect", "--generator", "mock", "--l2", "overlap", "--dataset", "builtin",
                                        "--n", "12", "--out", args.out])
        ns.n = 12
        collect(ns)
        analyze(build_parser().parse_args(["analyze", "--run", args.out, "--days", "60", "--daily-queries", "20"]))


if __name__ == "__main__":
    main()
