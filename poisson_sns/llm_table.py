"""Merge LLM-rated coarse-state intensities into results/llm_table.json and build
providers.  Usage: python llm_table.py <dir_with_keys.json_and_out_*.json>"""
import glob, json, os, sys
from sim import TableProvider, SurrogateIntensity, all_coarse_states, coarse_key, PERIODS


def merge(d, out="results/llm_table.json"):
    keys = {k["id"]: tuple(k["key"]) for k in json.load(open(os.path.join(d, "keys.json")))}
    tab, why = {}, {}
    for f in sorted(glob.glob(os.path.join(d, "out_*.json"))):
        for i, v in json.load(open(f)).items():
            tab[keys[int(i)]] = min(5.0, max(0.0, float(v[0]))); why[str(keys[int(i)])] = v[1]
    missing = [k for k in all_coarse_states() if k not in tab]
    assert not missing, f"{len(missing)} states unrated"
    os.makedirs("results", exist_ok=True)
    json.dump([dict(key=list(k), intensity=v, reason=why[str(k)]) for k, v in tab.items()], open(out, "w"),
              ensure_ascii=False, indent=0)
    return tab


def load(path="results/llm_table.json"):
    return {tuple(r["key"]): r["intensity"] for r in json.load(open(path))}


def llm_provider():
    return TableProvider(load(), "llm-table")


def surrogate_table_provider():
    """Control: the rule-based surrogate evaluated on the same coarse states."""
    s = SurrogateIntensity()
    tab = {}
    for k in all_coarse_states():
        p, per, e, rc, b, nf = k
        tab[k] = s(p, PERIODS[per][1], e, rc, b, nf)[0]
    return TableProvider(tab, "surrogate-table")


if __name__ == "__main__":
    merge(sys.argv[1])
