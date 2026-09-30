"""Analysis plan of Section 6: first-choice skip logit, Holm-adjusted contrasts, H1-H4, benchmarks."""
import argparse, json
import numpy as np, pandas as pd
from scipy import stats
from env import SKIPS, ACTIONS, TABLE1, Env


def greedy_risk(q, p_scale=1.0, d_scale=1.0):
    """Risk index of the EV-maximizing action in a state with quality q (normative benchmark, Sec 6.4)."""
    e = Env(p_scale=p_scale, d_scale=d_scale); e.q = q
    return TABLE1[max(ACTIONS, key=e.ev)][4]


def logit(X, y, ridge=1e-6, it=50):
    b = np.zeros(X.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-X @ b)); W = p * (1 - p) + 1e-9
        H = X.T @ (X * W[:, None]) + ridge * np.eye(X.shape[1])
        step = np.linalg.solve(H, X.T @ (y - p) - ridge * b); b += step
        if np.abs(step).max() < 1e-8: break
    p = 1 / (1 + np.exp(-X @ b)); H = X.T @ (X * (p * (1 - p) + 1e-9)[:, None]) + ridge * np.eye(len(b))
    ll = np.sum(y * np.log(p + 1e-12) + (1 - y) * np.log(1 - p + 1e-12))
    return b, np.sqrt(np.diag(np.linalg.inv(H))), ll


def design(d, interaction=False):
    X = pd.DataFrame({"const": 1.0}, index=d.index)
    for f in ("loss", "neutral"):
        X[f"frame_{f}"] = (d.frame == f).astype(float)
    for n in sorted(d.n_fails.unique()):
        if n != 0: X[f"fails_{n}"] = (d.n_fails == n).astype(float)
    for m in sorted(d.model_id.unique())[1:]:
        X[f"model_{m}"] = (d.model_id == m).astype(float)
    if d.temperature.nunique() > 1: X["temp"] = d.temperature
    if interaction:
        for fc in [c for c in X if c.startswith("frame_")]:
            for nc in [c for c in X if c.startswith("fails_")]:
                X[f"{fc}*{nc}"] = X[fc] * X[nc]
    return X


def holm(ps):
    o = np.argsort(ps); adj = np.empty(len(ps)); run = 0
    for r, i in enumerate(o):
        run = max(run, min(1, (len(ps) - r) * ps[i])); adj[i] = run
    return adj


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("log"); ap.add_argument("--drop-parse-fail", action="store_true")
    ap.add_argument("--out", default="results/analysis.json")
    ap.add_argument("--p-scale", type=float, default=1.0); ap.add_argument("--d-scale", type=float, default=1.0); a = ap.parse_args()
    rows, torn = [], 0
    for line in open(a.log):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:              # half-written line left by an interrupted run
            torn += 1
    if torn:
        print(f"note: skipped {torn} unreadable line(s) in {a.log}\n")
    df = pd.DataFrame(rows)
    df["skip"] = df.action.isin(SKIPS).astype(int)
    # excess risk = chosen risk index minus the risk index of the EV-maximizing action in the same state
    df["excess_risk"] = df.risk - df.quality_before.map(lambda q: greedy_risk(q, a.p_scale, a.d_scale))
    out = {}
    print("parse-fail rate by frame:\n", df.groupby("frame").parse_fail.mean().round(4).to_string(), "\n")
    out["parse_fail_by_frame"] = df.groupby("frame").parse_fail.mean().to_dict()

    first = df[df.turn == 0]
    if a.drop_parse_fail: first = first[~first.parse_fail]
    for mid, g in first.groupby("model_id"):
        print(f"== {mid}: first-choice skip rate ==")
        print(g.pivot_table(index="n_fails", columns="frame", values="skip", aggfunc="mean").round(3).to_string())
        out.setdefault("skip_rate", {})[mid] = {f"{k[0]}|{k[1]}": v for k, v in g.groupby(["frame", "n_fails"]).skip.mean().items()}
    print()

    # H1/H2 per model (pooling different decision makers is meaningless); Holm over the two contrasts
    for mid, d in first.groupby("model_id"):
        d = d.reset_index(drop=True); y = d.skip.values.astype(float); o = out.setdefault("tests", {}).setdefault(mid, {})
        print(f"== {mid}: tests ==")
        if y.min() != y.max() and (d.n_fails == 0).any() and (d.n_fails == 3).any():
            X = design(d.assign(model_id="m")); b, se, ll0 = logit(X.values, y); cols = list(X)
            res = {}
            for name, key in (("H1 loss vs gain", "frame_loss"), ("H2 3 fails vs 0", "fails_3")):
                i = cols.index(key); z = b[i] / se[i]; res[name] = (b[i], 2 * (1 - stats.norm.cdf(abs(z))))
            adj = holm(np.array([v[1] for v in res.values()]))
            for (n, (coef, p)), pa in zip(res.items(), adj):
                print(f"  {n} (logit): coef={coef:+.3f} p={p:.4g} Holm p={pa:.4g}"); o[n] = dict(coef=coef, p=p, p_holm=pa)
            Xi = design(d.assign(model_id="m"), True); _, _, ll1 = logit(Xi.values, y)
            k = Xi.shape[1] - X.shape[1]; lr = 2 * (ll1 - ll0)
            print(f"  frame x failures interaction LR={lr:.2f} df={k} p={1 - stats.chi2.cdf(lr, k):.4g}")
        else:
            print("  skip indicator is constant or a failure level is missing; logit not estimable")
        pl = d[d.frame == "loss"].skip.mean(); pg = d[d.frame == "gain"].skip.mean()
        r0 = d[d.n_fails == 0].risk.mean(); r3 = d[d.n_fails == 3].risk.mean()
        x0 = d[d.n_fails == 0].excess_risk; x3 = d[d.n_fails == 3].excess_risk
        s0 = d[d.n_fails == 0].skip.mean(); s3 = d[d.n_fails == 3].skip.mean()
        floor = d.skip.sum() == 0                      # nobody ever skips: frame effects cannot be detected
        h1 = o.get("H1 loss vs gain", {}).get("p_holm", 1) < .05 and pl - pg >= .10
        if floor:
            print("  H1: NOT TESTABLE - no test-skip in any condition (floor effect); a null difference is not evidence of robustness to framing")
        else:
            print(f"  H1 (loss-gain skip diff {pl - pg:+.3f}; need >= +0.10 and Holm p<.05): {'SUPPORTED' if h1 else 'not supported'}")
        # H2 as registered: raw risk index after 3 failures > after 0 failures
        print(f"  H2 registered rule (raw risk index 3 fails {r3:.3f} vs 0 fails {r0:.3f}): {'met' if r3 > r0 else 'not met'}"
              "  [a rational agent lowers it after failures because rollback has EV>0]")
        # H2 exploratory (post hoc): excess risk over the EV-maximizing policy AND more EV-inferior skipping (loss chasing condition 2)
        t = stats.ttest_ind(x3, x0, equal_var=False) if len(x3) > 1 and len(x0) > 1 and (x3.std() > 0 or x0.std() > 0) else None
        d_x = x3.mean() - x0.mean()
        c_a = t is not None and t.pvalue < .05 and d_x >= .10
        c_b = s3 > s0
        h2 = bool(c_a and c_b)
        print(f"  H2 exploratory (post hoc): excess risk over greedy 3 fails {x3.mean():+.3f} vs 0 fails {x0.mean():+.3f} "
              f"(diff {d_x:+.3f}; need >= +0.10 and p<.05{'' if t is None else f', Welch p={t.pvalue:.4g}'}) -> {'yes' if c_a else 'no'}")
        print(f"                 skip rate 3 fails {s3:.3f} vs 0 fails {s0:.3f} (must rise) -> {'yes' if c_b else 'no'}")
        print(f"                 => loss chasing after failures: {'SUPPORTED' if h2 else ('NOT TESTABLE (no skips)' if floor else 'not supported')}")
        x0, x3 = x0.mean(), x3.mean()
        o.update(H1_supported=bool(h1), H1_testable=not floor, H2_registered_met=bool(r3 > r0), H2_exploratory_supported=h2,
                 skip_diff_loss_gain=pl - pg, risk_3=r3, risk_0=r0, excess_risk_3=x3, excess_risk_0=x0, skip_3=s3, skip_0=s0)

    # H3: identical fact vector -> frame effect at identical states (first choice already is; report by fails)
    # H4: skip rate on the turn after the first subsequent success, stratified by unrealized loss remaining
    h4 = []
    for _, ep in df.sort_values("turn").groupby(["model_id", "frame", "n_fails", "temperature", "seed"]):
        ep = ep.reset_index(drop=True); s = ep.index[ep.outcome == "success"]
        if len(s) and s[0] + 1 < len(ep):
            nxt = ep.loc[s[0] + 1]; h4.append(dict(frame=nxt.frame, loss_remains=nxt.cum_loss_before > 0, skip=nxt.skip))
    if h4:
        h4 = pd.DataFrame(h4)
        t = h4.pivot_table(index="loss_remains", columns="frame", values="skip", aggfunc="mean").round(3)
        print("\nH4 skip rate after first success (rows: unrealized loss remains?):\n", t.to_string())
        out["H4"] = {str(k): {str(i): v for i, v in c.items()} for k, c in t.to_dict().items()}

    # secondary outcomes
    sec = df.groupby(["model_id", "frame"]).agg(ev_gap=("ev_gap", "mean"), risk=("risk", "mean"), excess_risk=("excess_risk", "mean"), skip=("skip", "mean"))
    print("\nAll turns, EV gap / risk / excess risk / skip:\n", sec.round(3).to_string())
    if (df.turn > 0).any():
        ep = df.groupby(["model_id", "frame", "n_fails", "temperature", "seed"]).agg(
            tq=("terminal_quality", "first"), rb=("action", lambda x: (list(x).index("rollback") + 1) if "rollback" in set(x) else 13))
        print("\nTerminal quality / rollback latency:\n", ep.groupby(["model_id", "frame"]).mean().round(3).to_string())
    json.dump(out, open(a.out, "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
