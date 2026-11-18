"""Domain-specific cost of a wrong output F, domain-specific estimates of the two channels, and the thresholds that follow.

F by domain (see manuscript Appendix C, Table C3, for sources and reliability). F is the cost to detect and repair a wrong output,
H = $8.82 is the cost of one human-handled contact.
  repeat contact (generic)  $8.82-16     one repeat contact (SQM, Kustomer, Televerde)
  retail                    $29-157      repair contact $8.82 + return processing $20 (range $10-30) [+ one chargeback, all-in $128]
  airline                   $9-609       repair contact $8.82 + remediation of a severe case, e.g. Moffatt v. Air Canada CA$812 (about
                                          US$600; exchange rate approximate), EU261 compensation EUR 250-600; expected F depends on the share
                                          p_sev of wrong outputs that become severe cases (not observed; sensitivity shown)
  coding                    ~1-3 H       developer time to repair at about $65/hour (BLS); hours per defect are an assumption
"""
import json, math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import calibration as cal
import table4_two_component as t4

ROOT = HERE.parent
RES = ROOT / "replication/replication_agent_handoff/inject/results"
P = cal.P
H = P["H"]

DOMAIN_F = {"retail": {"low": H + 20.0, "high": H + 20.0 + 128.0},
            "airline": {"low": H, "central_p05": H + 0.05 * 600.0, "high": H + 600.0}}
SEVERE_R = 600.0      # remediation of a severe case in US$ (Moffatt: CA$812.02 incl. interest and fees, about US$600)


def base_error_rate(m, dom):
    """Agent-error rate per call in control runs of a domain."""
    errs = calls = 0
    seen = {}
    for l in open(RES / f"{m}.jsonl"):
        r = json.loads(l)
        if r.get("ok") and r["arm"] == "control" and r["domain"] == dom and r["rep"] < t4.MAXREP.get(m, 99): seen[r["key"]] = r
    for r in seen.values():
        for c in r["calls"]:
            if not c["injected"]:
                calls += 1; errs += c["error"]
    return errs / calls


def main():
    t4.B = 2000
    out = {}
    for dom in ("retail", "airline"):
        for m in ("deepseek", "gpt61terra", "sonnet55"):
            r = t4.est(m, dom); d = r["misleading"]; mu = base_error_rate(m, dom)
            row = dict(S_ctrl=r["S_ctrl"], ptr_ctrl=r["ptr_ctrl"], mu=mu, **{k: d[k] for k in ("theta", "theta_ci", "theta_h", "theta_h_ci", "theta_w", "theta_w_ci", "thm_h", "thm_h_ci", "thm_w", "thm_w_ci", "d_transfer", "d_transfer_ci")})
            Fs = DOMAIN_F[dom]
            ns = {}
            for name, F in Fs.items():
                cell = []
                for tw, twci, th in ((d["theta_w"], d["theta_w_ci"], d["theta_h"]), (d["thm_w"], d["thm_w_ci"], d["thm_h"])):
                    tw_use = max(0.0, tw) if twci[0] > 0 else 0.0
                    cell.append(cal.n_star(tw_use, max(0.0, th), F, mu=mu))
                ns[name] = cell
            row["F"] = Fs; row["n_star"] = ns
            out[f"{dom}|{m}"] = row
    # break-even share of severe cases: smallest p_sev for which the rule binds within 5 / 3 errors (Sonnet-like retail and airline theta_w = 0.12)
    be = {}
    for nm in (5, 3):
        Fneed = cal.breakeven_ratio(0.12, nmax=nm) * H
        be[str(nm)] = dict(F_needed=Fneed, p_severe_airline=(Fneed - H) / SEVERE_R, share_of_chargeback_retail=(Fneed - (H + 20.0)) / 128.0)
    out["breakeven"] = be
    (ROOT / "sim/f_domains.json").write_text(json.dumps(out, indent=1, default=float))
    return out


def airline_upper():
    """N* at the upper end of the intervals for theta_w in airline, at the central airline cost (5% severe), for Claude Sonnet 5.5."""
    D = json.load(open(ROOT / "sim/f_domains.json")); r = D["airline|sonnet55"]
    ups = [max(r["theta_w_ci"][1], 0.0), max(r["thm_w_ci"][1], 0.0)]
    F = DOMAIN_F["airline"]["central_p05"]
    ns = [cal.n_star(u, max(r["theta_h"], 0.0), F, mu=r["mu"]) for u in ups]
    return ups, ns


def fmt(x, c):
    return f"{x:+.2f} [{c[0]:+.2f}, {c[1]:+.2f}]"


def tab_theta():
    D = json.load(open(ROOT / "sim/f_domains.json"))
    NAME = {"deepseek": "DeepSeek-V3.1", "gpt61terra": "GPT-6.1-terra", "sonnet55": "Claude Sonnet 5.5"}
    rows = ["| Domain | Agent | Control success | Transfer rate, control; change | θ$_h$, additive | θ$_w$, additive | θ$_w$, model-consistent |", "|---|---|---|---|---|---|---|"]
    for dom, lab in (("retail", "Retail (114 tasks)"), ("airline", "Airline (50 tasks)")):
        for m in ("deepseek", "gpt61terra", "sonnet55"):
            r = D[f"{dom}|{m}"]
            rows.append(f"| {lab} | {NAME[m]} | {r['S_ctrl']:.2f} | {r['ptr_ctrl']:.2f}; {r['d_transfer']:+.2f} | {fmt(r['theta_h'], r['theta_h_ci'])} | {fmt(r['theta_w'], r['theta_w_ci'])} | {fmt(r['thm_w'], r['thm_w_ci'])} |")
    return "\n".join(rows)


def _rng(a, b, cap=10):
    f = lambda x: f">{cap}" if (x == float("inf") or x > cap) else str(int(x))
    vals = sorted([a, b], key=lambda x: 99 if (x == float("inf") or x > cap) else x)
    return f(vals[0]) if f(vals[0]) == f(vals[1]) else f"{f(vals[0])} to {f(vals[1])}"


def tab_nstar_domain():
    D = json.load(open(ROOT / "sim/f_domains.json"))
    NAME = {"deepseek": "DeepSeek-V3.1", "gpt61terra": "GPT-6.1-terra", "sonnet55": "Claude Sonnet 5.5"}
    rows = ["| Domain | Agent | Error rate per step | θ$_w$ (additive; model-consistent) | N* at the lower F | N* at the higher F |", "|---|---|---|---|---|---|"]
    for dom, lab, (k1, k2), (l1, l2) in (("retail", "Retail", ("low", "high"), ("$29", "$157")), ("airline", "Airline", ("low", "central_p05"), ("$8.82", "$39 (5% severe)"))):
        for m in ("deepseek", "gpt61terra", "sonnet55"):
            r = D[f"{dom}|{m}"]
            th = f"{max(r['theta_w'], 0):.2f}{'' if r['theta_w_ci'][0] > 0 else ' (n.s.)'}; {max(r['thm_w'], 0):.2f}{'' if r['thm_w_ci'][0] > 0 else ' (n.s.)'}"
            rows.append(f"| {lab} | {NAME[m]} | {r['mu']:.3f} | {th} | {_rng(*r['n_star'][k1])} ({l1}) | {_rng(*r['n_star'][k2])} ({l2}) |")
    return "\n".join(rows)


if __name__ == "__main__":
    out = main()
    print(tab_theta()); print(); print(tab_nstar_domain())
    print("\nbreak-even:", json.dumps(out["breakeven"], indent=1))
