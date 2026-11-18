"""Build the markdown tables of Section 5 from the analysis outputs (no manual transcription).
Inputs : sim/table4_two_component.json, sim/free_crosscheck_results.json, sim/free_transfer_results.json
Output : prints a dict of tables; msom_draft_evidence.md is filled from the template by build_evidence.py"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
T = json.load(open(ROOT / "table4_two_component.json"))
X = json.load(open(ROOT / "free_crosscheck_results.json"))
NAME = {"llama70b": "Llama-3.1-70B", "deepseek": "DeepSeek-V3.1", "gpt61terra": "GPT-6.1-terra", "sonnet55": "Claude Sonnet 5.5", "llama8b": "Llama-3.1-8B"}
ORDER = ["llama70b", "deepseek", "gpt61terra", "sonnet55"]


def ci(c, nd=2): return f"[{c[0]:+.{nd}f}, {c[1]:+.{nd}f}]"
def pm(x, c, nd=2): return f"{x:+.{nd}f} {ci(c, nd)}"


def tab_arms():
    rows = ["| Agent | Control success | Misleading message: success | Transfer rate, control | Transfer rate, misleading | Change in transfer rate |", "|---|---|---|---|---|---|"]
    for m in ORDER:
        r = T[m]; d = r["misleading"]
        s_inj = r["S_ctrl"] * (1 - d["theta"]); p_inj = r["ptr_ctrl"] + d["d_transfer"]
        rows.append(f"| {NAME[m]} | {r['S_ctrl']:.2f} | {s_inj:.2f} | {r['ptr_ctrl']:.2f} | {p_inj:.2f} | {pm(d['d_transfer'], d['d_transfer_ci'])} |")
    return "\n".join(rows)


def tab_decomp(kind):
    rows = ["| Agent | Total θ | θ_h, additive | θ_w, additive | θ_h, model-consistent | θ_w, model-consistent |", "|---|---|---|---|---|---|"]
    for m in ORDER:
        d = T[m][kind]
        if m == "llama70b": pass
        rows.append(f"| {NAME[m]} | {pm(d['theta'], d['theta_ci'])} | {pm(d['theta_h'], d['theta_h_ci'])} | {pm(d['theta_w'], d['theta_w_ci'])} | {pm(d['thm_h'], d['thm_h_ci'])} | {pm(d['thm_w'], d['thm_w_ci'])} |")
    return "\n".join(rows)


def _rng(a, b, cap=10):
    vals = sorted([a, b], key=lambda x: 99 if (x == float("inf") or x > cap) else x)
    lo, hi = vals
    f = lambda x: f">{cap}" if (x == float("inf") or x > cap) else str(int(x))
    return f(lo) if f(lo) == f(hi) else f"{f(lo)} to {f(hi)}"


def tab_nstar():
    import calibration as cal
    rows = ["| Agent, error type | θ$_w$ (additive; model-consistent) | N* at F = $12.35 | N* at F = $22 | N* at F = $44 |", "|---|---|---|---|---|"]
    for r in cal.rows():
        th = f"{max(r['theta_w_add'], 0):.2f}{'' if r['sig_add'] else ' (n.s.)'}; {max(r['theta_w_model'], 0):.2f}{'' if r['sig_model'] else ' (n.s.)'}"
        cells = [_rng(*r["cells"][str(F)]) for F in (cal.P["F_base"], cal.P["F_high"], cal.P["F_vhigh"])]
        rows.append(f"| {NAME[r['agent']]}, {r['kind']} | {th} | {cells[0]} | {cells[1]} | {cells[2]} |")
    return "\n".join(rows)


def sonnet_text():
    import calibration as cal
    r = [x for x in cal.rows() if x["agent"] == "sonnet55" and x["kind"] == "misleading"][0]
    def phrase(F):
        a, b = r["cells"][str(F)]
        lo, hi = sorted([a, b], key=lambda x: 99 if (x == float("inf") or x > 10) else x)
        if lo > 10 or lo == float("inf"): return "more than ten"
        if hi == float("inf") or hi > 10: return f"{int(lo)} or more"
        return str(int(lo)) if lo == hi else f"{int(lo)} to {int(hi)}"
    return (f"{phrase(cal.P['F_base'])} errors when a wrong output costs $12.35, {phrase(cal.P['F_high'])} when it costs $22, and {phrase(cal.P['F_vhigh'])} when it costs $44")


def tab_calib():
    import calibration as cal
    P = cal.P
    rows = ["| Quantity | Symbol | Value used (range) | Basis | Reliability |", "|---|---|---|---|---|",
            f"| Cost of a human-handled contact | $H$, $h$ | ${P['H']:.2f} (${P['H_low']:.0f}–{P['H_high']:.1f}) | Average cost per call of $8.82 in the SQM Group first-call-resolution white paper (text checked); Gartner's 2024 median cost per assisted contact of $13.50 and, in a 2019 poll, $8.01 for live channels (known from a summary of the Gartner abstract; the pages were not accessible to us, and the two figures come from different methods); $6–12 in other benchmarks (vendor roll-up) | SQM: industry survey, checked. Gartner: secondary |",
            f"| Cost to detect and repair a wrong output | $F$ | ${P['F_base']:.2f} base (${P['F_low']:.2f}–{P['F_vhigh']:.0f}) | Base is the cost for a human to resolve the issue: the SQM cost per call resolution, $8.82 × 1.4 calls per resolution = $12.35 (text checked). A repeat contact is reported at $14–30 against $7–15 for a resolved contact, with no source (Kustomer). Values of $22 and $44 add a repair contact and goodwill or refund | Base: industry survey, checked. $22 and $44: assumptions; the domain sets $F/H$. Taking $H$ as the cost per resolution too ($12.35) would lower every $F/H$ by a factor of 1.4 (see the $H$ = $13.5 row of Table C2) |",
            f"| Cost of one agent step | $k$ | ${P['k']:.3f} ($0.0017–0.0067) | Our run logs: mean cost per run divided by mean tool calls (GPT-6.1-terra $0.0124 / 7.4; Claude Sonnet 5.5 $0.054 / 8.1), including the simulated customer | Measured in our experiments |",
            f"| Cost of an error | $c$ | ${P['c']:.3f} | Assumed equal to $k$ (one wasted call) | Assumption |",
            f"| Completion probability per step | $q$ | {P['q']:.2f} | One over the mean number of tool calls per run in customer service (7.4–8.8) | Measured |",
            "| Error rate per step | $\\mu$ | 0.012 (GPT-6.1-terra), 0.014 (Claude Sonnet 5.5), 0.055 (DeepSeek-V3.1) | Agent-error rate per call in control runs, customer service (Table 3 of the earlier analysis; `inject/results`) | Measured |",
            f"| Reviewer service rate | $m$ | {P['m_per_hour']:.0f} per hour (average handle time {P['aht_min']} min; 6–10 min) | Voice median attributed to ICMI (via an aggregator); MetricNet 2023 voice 7.0 and chat 9.8 minutes; Zendesk chat 8–12 minutes | Secondary; definitions differ by channel |",
            f"| Value of customer waiting time | $\\omega$ | ${P['wage']:.2f} per hour = ${P['omega_per_service_time']:.2f} per service time | Median hourly wage of customer service representatives, May 2025 (BLS), used as the value of a customer's time | Wage: official. Use as value of time: assumption |",
            "| For comparison: cost of an AI resolution | – | $0.41–2.00 | Vendor-reported cost per AI resolution; our own cost per simulated customer-service run is $0.012–0.054 | Vendor; measured |"]
    return "\n".join(rows)


def tab_sens():
    import calibration as cal
    P = cal.P
    Fs = [P["F_low"], P["F_base"], P["F_high"], P["F_vhigh"]]
    rows = ["| Hand-off cost $H$ | " + " | ".join(f"$F$ = ${F:g}" for F in Fs) + " |", "|---|" + "---|" * len(Fs)]
    for H, v in cal.sensitivity().items():
        rows.append(f"| ${float(H):g} | " + " | ".join(("more than 10" if (x == float('inf') or x > 10) else str(int(x))) for x in v.values()) + " |")
    be = {nm: cal.breakeven_ratio(0.12, nmax=nm) for nm in (10, 5, 3, 2)}
    return "\n".join(rows), be


def tab_behaviour():
    rows = ["| Agent | Cross-checks (n) | θ if cross-checked | Retries (n) | θ if retried | Neither (n) | θ if neither |", "|---|---|---|---|---|---|---|"]
    for m in ORDER:
        b = X[m]["blame"]["outcome_by_behaviour"]
        def cell(k):
            if k not in b: return "–", "–"
            v = b[k]; t = v["theta"]
            return f"{v['n']}", ("n/a" if t is None else f"{t:.2f} {ci(v['theta_ci'], 2)}".replace('+', ''))
        c1, c2, c3 = cell("CC"), cell("RT"), cell("none")
        rows.append(f"| {NAME[m]} | {c1[0]} | {c1[1]} | {c2[0]} | {c2[1]} | {c3[0]} | {c3[1]} |")
    return "\n".join(rows)


TABLES = dict(ARMS=tab_arms(), DECOMP_MIS=tab_decomp("misleading"), DECOMP_TRA=tab_decomp("transient"), NSTAR=tab_nstar(), BEHAV=tab_behaviour())

REP = ROOT.parent / "replication/replication_agent_handoff"
ALLNAME = {"llama8b": "Llama-3.1-8B", "llama70b": "Llama-3.1-70B", "deepseek": "DeepSeek-V3.1", "gpt61terra": "GPT-6.1-terra", "sonnet55": "Claude Sonnet 5.5"}


def tab_success():
    A = json.load(open(REP / "inject/inject_results.json")); C = json.load(open(REP / "inject_code/code_results.json"))
    rows = ["| Domain | Agent | Control success | Transient − control | Misleading − control |", "|---|---|---|---|---|"]
    for dom, J in (("Customer service", A), ("Code repair", C)):
        for m in ["llama8b", "llama70b", "deepseek", "gpt61terra", "sonnet55"]:
            r = J[m]["success"]
            def cell(k):
                d = r[k]; return f"{d['diff']:+.3f} [{d['ci'][0]:+.3f}, {d['ci'][1]:+.3f}]"
            rows.append(f"| {dom} | {ALLNAME[m]} | {r['control']['rate']:.2f} | {cell('single_minus_control')} | {cell('blame_minus_control')} |")
    return "\n".join(rows)


def tab_obs():
    rows = ["| Model | Trajectories | Branching ratio, no heterogeneity | Branching ratio, with heterogeneity | 95% bootstrap interval | α | δ | CV of μ | LR statistic |", "|---|---|---|---|---|---|---|---|---|",
            "| Llama-3.1-8B | 3,000 | 1.85 | 0.50 | [0.44, 0.56] | 0.20 | 0.60 | 1.79 | 2077 |",
            "| Llama-3.1-70B | 3,000 | 1.48 | 0.38 | [0.31, 0.42] | 0.21 | 0.45 | 1.41 | 1130 |",
            "| Llama-3.1-405B | 1,140 | 2.08 | 0.56 | [0.49, 0.62] | 0.15 | 0.73 | 3.05 | 659 |"]
    return "\n".join(rows)


import f_domains as _fd
_sens, _be = tab_sens()
_up, _upn = _fd.airline_upper()
TABLES.update(DOMAIN_TH=_fd.tab_theta(), DOMAIN_N=_fd.tab_nstar_domain(), AIR_UPPER=f"{_up[0]:.2f} and {_up[1]:.2f}", AIR_UPPER_N=(str(int(_upn[0])) if _upn[0]==_upn[1] and _upn[0] != float('inf') else f"{int(min(_upn))} to {int(max(_upn))}"), SUCCESS=tab_success(), OBS=tab_obs(), CALIB=tab_calib(), SENS=_sens, SONNET_N=sonnet_text(), BE10=f"{_be[10]:.1f}", BE5=f"{_be[5]:.1f}", BE3=f"{_be[3]:.1f}", BE2=f"{_be[2]:.1f}")

if __name__ == "__main__":
    for k, v in TABLES.items(): print(f"--- {k}\n{v}\n")
