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
    rows = ["| Agent, error type | Manuscript (total θ) | θ_w additive | θ_w model-consistent |", "|---|---|---|---|"]
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
if __name__ == "__main__":
    for k, v in TABLES.items(): print(f"--- {k}\n{v}\n")
