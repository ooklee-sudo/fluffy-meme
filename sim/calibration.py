"""Calibration of the cost parameters in dollars, and the thresholds that follow.

Sources (see manuscript Appendix C for the table with links and reliability)
  H   cost of a human-handled contact: SQM Group average cost per call $8.82 (cited by a vendor page); other benchmarks $6-13.50.
  F   cost to detect and repair a wrong output: one extra human contact. Base $12.35 = SQM cost per resolution (8.82 x 1.4 contacts per
      resolution); low $8.82 (one extra contact); high and very high $22 and $44 (assumption: repair contact plus refund or goodwill,
      NOT sourced; the domain decides how large F/H is).
  k   cost of one agent step: from our own run logs, mean cost per run / mean tool calls per run: GPT-6.1-terra 0.0124/7.4 = $0.0017,
      Claude Sonnet 5.5 0.054/8.1 = $0.0067 (agent plus simulated customer); base $0.004. c = k (assumption).
  q   completion probability per step: 1 / mean tool calls per run (7.4 to 8.8 in customer service) -> 0.12.
  mu  error rate per call, control runs, customer service (manuscript Table 3): GPT 0.012, Sonnet 0.014, DeepSeek 0.055.
  Queue: average handle time 7.5 min (voice median, secondary sources 6-10 min) -> service rate 8 per hour per reviewer;
      value of waiting time = BLS median hourly wage of customer service representatives, $21.53 (May 2025), an assumption for omega.
"""
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

P = dict(H=8.82, H_low=6.0, H_high=13.5, F_low=8.82, F_base=12.35, F_high=22.0, F_vhigh=44.0,
         k=0.004, c=0.004, q=0.12, mu={"gpt61terra": 0.012, "sonnet55": 0.014, "deepseek": 0.055},
         aht_min=7.5, wage=21.53)
P["m_per_hour"] = 60.0 / P["aht_min"]
P["omega_per_service_time"] = P["wage"] / P["m_per_hour"]      # delay cost per unit of time when the service rate is 1
P["h"] = P["H"]                                                  # reviewer working cost per hand-off


def n_star(tw, th, F, H=P["H"], k=P["k"], c=P["c"], q=P["q"], mu=0.014):
    rho = math.exp(-mu * th); tt = tw + th - tw * th
    R = math.exp(mu * tt) * ((k + c * mu) / (q * F) - rho * (H - F) / F)
    if R >= 1: return 0
    if tw <= 0 or R <= 0: return math.inf
    return max(0, math.ceil(math.log(R) / math.log(1 - tw) - 1e-12))


def label(n, cap=10):
    if n == 0: return "0"
    if math.isinf(n) or n > cap: return f">{cap}"
    return str(n)


def rows():
    T = json.load(open(ROOT / "sim/table4_two_component.json"))
    out = []
    for m, kind in (("gpt61terra", "misleading"), ("deepseek", "misleading"), ("deepseek", "transient"), ("sonnet55", "misleading")):
        d = T[m][kind]; mu = P["mu"][m]
        cells = {}
        for F in (P["F_base"], P["F_high"], P["F_vhigh"]):
            ns = []
            for tw, twci, th in ((d["theta_w"], d["theta_w_ci"], d["theta_h"]), (d["thm_w"], d["thm_w_ci"], d["thm_h"])):
                tw_use = max(0.0, tw) if twci[0] > 0 else 0.0
                ns.append(n_star(tw_use, max(0.0, th), F, mu=mu))
            cells[F] = ns
        out.append(dict(agent=m, kind=kind, theta_w_add=d["theta_w"], theta_w_model=d["thm_w"], sig_add=d["theta_w_ci"][0] > 0, sig_model=d["thm_w_ci"][0] > 0, cells={str(F): v for F, v in cells.items()}))
    return out


def sensitivity():
    """N* for a Sonnet-like agent (theta_w = 0.12, theta_h = 0.05, mu = 0.014) over H and F."""
    res = {}
    for H in (P["H_low"], P["H"], P["H_high"]):
        res[str(H)] = {str(F): n_star(0.12, 0.05, F, H=H, mu=0.014) for F in (P["F_low"], P["F_base"], P["F_high"], P["F_vhigh"])}
    return res


def breakeven_ratio(tw, th=0.05, mu=0.014, H=P["H"], nmax=10):
    """Smallest F/H at which the threshold is <= nmax (the count rule binds within nmax errors)."""
    lo, hi = 1.0, 200.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if n_star(tw, th, mid * H, H=H, mu=mu) <= nmax: hi = mid
        else: lo = mid
    return hi


if __name__ == "__main__":
    out = dict(params=P, rows=rows(), sensitivity=sensitivity(),
               breakeven={f"{nm}": breakeven_ratio(0.12, nmax=nm) for nm in (10, 5, 3, 2)})
    (ROOT / "sim/calibration.json").write_text(json.dumps(out, indent=1, default=str))
    print("omega per service time $%.2f, h = $%.2f, service rate %.1f/hour" % (P["omega_per_service_time"], P["h"], P["m_per_hour"]))
    print("\nN* (split-based: additive / model-consistent) at F = 12.35 / 22 / 44, H = 8.82")
    for r in rows():
        cs = "   ".join(f"F={F}: {label(a)}/{label(b)}" for F, (a, b) in r["cells"].items())
        print(f"  {r['agent']:11s} {r['kind']:10s} theta_w {r['theta_w_add']:+.2f}/{r['theta_w_model']:+.2f}   {cs}")
    print("\nSensitivity of N* (Sonnet-like, theta_w=0.12): rows H, columns F =", [P['F_low'], P['F_base'], P['F_high'], P['F_vhigh']])
    for H, v in sensitivity().items(): print(f"  H={H}:", [label(x) for x in v.values()])
    print("\nSmallest F/H at which N* <= n for theta_w = 0.12:", {nm: round(breakeven_ratio(0.12, nmax=nm), 2) for nm in (10, 5, 3, 2)})
