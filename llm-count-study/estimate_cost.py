"""Estimate the number of API calls and the cost of a run plan (no API calls; reads OpenRouter's public price list).

  python estimate_cost.py --models openai/gpt-4o-mini,anthropic/claude-sonnet-5 --seeds 2 --scenarios retail,grocery,demo,hillstrom

Assumptions: about 4 characters per token; output tokens A 3, B 20, C 60, D 4 (email experiment 4); reasoning is switched
off where the model allows it. Models that cannot switch reasoning off are flagged: add roughly 300 hidden tokens per call.
"""
import argparse, json, urllib.request
import numpy as np, pandas as pd
import run_pilot as rp
import run_hillstrom as h

ap = argparse.ArgumentParser()
ap.add_argument("--models", required=True)
ap.add_argument("--seeds", type=int, default=1, help="number of seeds per model")
ap.add_argument("--scenarios", default="retail,grocery,demo,hillstrom")
ap.add_argument("--n", type=int, default=200)
ap.add_argument("--nh", type=int, default=300)
a = ap.parse_args()

with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as r:
    price = {m["id"]: m for m in json.load(r)["data"]}


def prompt_chars(scn):
    out = {}
    if scn in ("retail", "grocery", "demo"):
        sc = rp.get_scenario("retail" if scn == "retail" else "grocery")
        p = next(rp.make_personas(1, np.random.default_rng(0), sc).itertuples())
        pr = rp.prompts(sc, p, True)
        extra = 150 if scn == "demo" else 0
        out = {"A": (len(pr["A"]) + extra, 3), "B": (len(pr["B1"]) + extra, 20), "C": (len(pr["C"]) + extra, 60), "D": (len(pr["D"]) + extra, 4)}
    return out


def calls_for(scn):
    """list of (prompt chars, output tokens, count) per model and seed"""
    if scn == "hillstrom":
        d = pd.read_csv("hillstrom.csv") if __import__("os").path.exists("hillstrom.csv") else None
        base = 700 if d is None else len(h.persona(next(d.head(1).itertuples()), True)) + 140
        return [(base + 170, 4, 2 * a.nh * 12)]
    pc = prompt_chars(scn)
    return [(pc["A"][0], 3, 2 * a.n), (pc["B"][0], 20, 2 * a.n * 4), (pc["C"][0], 60, 2 * a.n), (pc["D"][0], 4, 2 * a.n)]


tot_calls = tot_cost = 0
print(f"{'model':42s} {'calls':>9s} {'USD':>8s}  note")
for m in a.models.split(","):
    info = price.get(m)
    if not info:
        print(f"{m:42s}  not found on OpenRouter"); continue
    pi, po = float(info["pricing"]["prompt"]), float(info["pricing"]["completion"])
    calls = cost = 0
    for scn in a.scenarios.split(","):
        for chars, outtok, cnt in calls_for(scn):
            calls += cnt * a.seeds
            cost += cnt * a.seeds * (chars / 4 * pi + outtok * po)
    eff = (info.get("reasoning") or {}).get("supported_efforts", [])
    note = "" if (not eff or "none" in eff) else "cannot switch reasoning off: add ~300 hidden tokens/call"
    if note:
        cost += calls * 300 * po
    tot_calls += calls; tot_cost += cost
    print(f"{m:42s} {calls:9,d} {cost:8.2f}  {note}")
print(f"{'TOTAL':42s} {tot_calls:9,d} {tot_cost:8.2f}")
