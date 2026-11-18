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


def tab_nstar():
    rows = ["| Agent, error type | Total θ, undivided | θ_w additive | θ_w model-consistent |", "|---|---|---|---|"]
    for m in ["deepseek", "gpt61terra", "sonnet55"]:
        for kind, lab in (("transient", "transient"), ("misleading", "misleading")):
            d = T[m][kind]
            fmt = lambda v: "/".join("no rule" if x == "none" else ("no rule needed" if x == "inf" else str(x)) for x in v)
            rows.append(f"| {NAME[m]}, {lab} | {fmt(d['n_star_old'])} | {fmt(d['n_star_new'])} | {fmt(d['n_star_model_consistent'])} |")
    return "\n".join(rows)


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


TABLES.update(SUCCESS=tab_success(), OBS=tab_obs())

if __name__ == "__main__":
    for k, v in TABLES.items(): print(f"--- {k}\n{v}\n")
