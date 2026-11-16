import json, math, statistics as st
import econ_model as E
mean = st.mean
R = "/tmp/claude-0/-home-user-fluffy-meme/6d046680-2797-598c-a7db-54c51fe25fec/scratchpad/zen/x/replication_package/"
real = json.load(open(R + "results/reallaw_v2.json")); rag = json.load(open(R + "results/rag_qwen7b.json")); bank = json.load(open(R + "real_law/real_fact_bank_v2.json"))
comp = E.composition(bank)
print("composition", comp)
ph = E.outcomes(real, rag, "keep_control_hard"); pe = E.outcomes(real, rag, "keep_control")
def rr(p, nc): return E.resid(p, comp, nc)
def nstar(p):  # N_c where A and D have equal residual stock
    ra, rd = rr(p, 0)["A"], rr(p, 0)["D"]
    return (rd - ra) / ((1 - p["A"]["c"]) - (1 - p["D"]["c"]))
print("P1 reversal threshold N_c*: hard audit %.1f, easy audit %.1f (bank has %d controls)" % (nstar(ph), nstar(pe), comp["NC"]))
cur = {j: mean([r["currency_all"] for r in real if r["method"] == m and r["lam"] == l and r["kA"] == .5 and r["kdep"] == 0]) for j, (m, l) in {"A": ("none", 0.), "S": ("ss", 10.), "D": ("dep", 10.)}.items()}
print("currency (all amended) A,S,D:", {k: round(v, 2) for k, v in cur.items()})
alpha, c, F = 2, 5, 200
m = E.labor(comp)
print("P2 regret of choosing by easy audit vs hard (alpha=%s,c=%s,F=%s):" % (alpha, c, F))
for nc in (5, 10, 20, 30, 66, 200, 1000):
    # truth = hard-alternative world; the organisation chooses with the easy test's belief
    r_true = rr(ph, nc); r_easy = rr(pe, nc)
    pick_easy = E.best(r_easy, m, alpha, c, F, ["A", "S", "D"]); pick_true = E.best(r_true, m, alpha, c, F, ["A", "S", "D"])
    ct = E.phi(r_true, m, alpha, c, F)
    print(f"  Nc={nc:5d}  easy-audit picks {pick_easy}, true best {pick_true}, cost ratio {ct[pick_easy] / ct[pick_true]:.2f}")
print("P3 churn: Psi(F vs D) by alpha (c=2,F=200):")
r = rr(ph, comp["NC"])
for a in (0.25, 0.5, 1, 2, 4, 12):
    print(f"  alpha={a:5}: Psi={E.index_listing(r, m, a, 2, 200):.2f}  best={E.best(r, m, a, 2, 200)}")
astar = 2 * 200 * 1 * r["D"] / (2 * m["F"]) ** 2
print("  alpha* (listing = refresh-only) at c=2,F=200: %.2f per year" % astar)
print("P4 value of information per statement: derived dependent %.2f vs sibling %.2f (policy D); ratio %.1f" % (1 - ph["D"]["g"], ph["D"]["s"] and 1 - ph["D"]["s"], (1 - ph["D"]["g"]) / (1 - ph["D"]["s"])))
vd = comp["NG"] * (1 - ph["D"]["g"]); vs = comp["NS"] * (1 - ph["D"]["s"])
print("   share of avoidable stale mass that sits in derived dependents: %.0f%% (derived %.1f, siblings %.1f)" % (100 * vd / (vd + vs), vd, vs))
print("P5 amendment size: N_c*(k) = threshold of controls above which scoped retention beats amend-only")
for kA in (0.1, 0.25, 0.5, 0.75):
    g = lambda mm, l, key: mean([x[key] for x in real if x["method"] == mm and x["lam"] == l and x["kA"] == kA and x["kdep"] == 0 and x[key] == x[key]])
    cA, cD = g("none", 0., "keep_control_hard"), g("dep", 10., "keep_control_hard")
    n_amend = comp["NL"] * 0 + 15  # time limits and amounts (A,B)
    NS = (1 - kA) * 15
    stale_extra_D = NS * (g("none", 0., "unlisted_AB") - g("dep", 10., "unlisted_AB"))
    print(f"  k={kA}: controls kept hard A={cA:.2f} D={cD:.2f}; N_c* ~ {stale_extra_D / (cD - cA):.1f}")
