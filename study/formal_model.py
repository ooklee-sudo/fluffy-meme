"""Expected-cost model of a screen -> judge cascade, calibrated on the 500 judged documents.
Per document (base rate pi of machine papers; screen depth f = share of HUMAN papers sent to the judge):
  cascade(f) = cJ*[pi*sM(f) + (1-pi)*f] + cR*[pi*mm(f) + (1-pi)*aH(f)] + L*pi*(1-mm(f))
  screen-only(f) = cR*[pi*sM(f) + (1-pi)*f] + L*pi*(1-sM(f))       (everything above the screen threshold is reviewed)
  judge-all = cascade(1);   none = L*pi
 sM = share of machine papers above the screen threshold; mm = share above it AND flagged by the judge (Gemini p_ai>=50);
 aH = share of human papers above it AND flagged by the judge. All are empirical class-conditional rates (no independence assumed).
 Screen = clustering-feature detector never trained on the target generator ('unseen'); judge = Gemini 2.5 Pro at threshold 50.
 'mixture' = equal-weight average over the three generators' machine rates (stream of unknown generators).
 cJ = US$0.0174 (measured). cR (human review of a flagged paper) and L (loss per missed machine paper) are ASSUMPTIONS, not measurements."""
import sys, io, contextlib, runpy, csv, numpy as np
sys.argv = ["judge_eval.py", "gpt4o", "gemini"]
with contextlib.redirect_stdout(io.StringIO()):
    ns = runpy.run_path("judge_eval.py", run_name="lib")
key, J, GENS, poisson_scores = ns["key"], ns["J"], ns["GENS"], ns["poisson_scores"]
FG = np.unique(np.concatenate([np.linspace(0.005, 0.2, 40), np.linspace(0.2, 1.0, 17)]))

def rates(g, boot=None, rng=None):
    ps = poisson_scores(g, [t for t in GENS if t != g], "NEW: rates+(a,b)")
    keep = [i for i, k in key.items() if k["source"] in ("human", g) and (k["source"], k["source_id"]) in ps
            and all(i in J[j] and J[j][i]["p_ai"] is not None for j in ("gpt4o", "gemini"))]
    y = np.array([0 if key[i]["source"] == "human" else 1 for i in keep])
    P = np.array([ps[(key[i]["source"], key[i]["source_id"])] for i in keep]); G = np.array([J["gemini"][i]["p_ai"] >= 50 for i in keep])
    h, m = np.where(y == 0)[0], np.where(y == 1)[0]
    if boot is not None: h, m = rng.choice(h, len(h)), rng.choice(m, len(m))
    out = np.zeros((len(FG), 3))
    for k, f in enumerate(FG):
        t = -np.inf if f >= 1 else np.quantile(P[h], 1 - f)
        sent_h, sent_m = P[h] >= t, P[m] >= t
        out[k] = [sent_m.mean(), (sent_m & G[m]).mean(), (sent_h & G[h]).mean()]      # sM, mm, aH
    return out
R = {g: rates(g) for g in GENS}; R["mixture"] = np.mean([R[g] for g in GENS], axis=0)

def costs(r, pi, cJ, cR, L):
    sM, mm, aH = r[:, 0], r[:, 1], r[:, 2]
    casc = cJ * (pi * sM + (1 - pi) * FG) + cR * (pi * mm + (1 - pi) * aH) + L * pi * (1 - mm)
    scr = cR * (pi * sM + (1 - pi) * FG) + L * pi * (1 - sM)
    return casc, scr, float(casc[-1]), L * pi          # judge-all = cascade at f=1

def summarize(r, pi, cJ, cR, L):
    casc, scr, jall, none = costs(r, pi, cJ, cR, L)
    kc, ks = int(np.argmin(casc)), int(np.argmin(scr))
    opts = {"no screening": none, "screen only": scr[ks], "judge on all": jall, "cascade": casc[kc]}
    best = min(opts, key=opts.get); q = pi * r[kc, 0] + (1 - pi) * FG[kc]
    return dict(f=FG[kc], q=q, none=none * 1000, screen=scr[ks] * 1000, judge_all=jall * 1000, cascade=casc[kc] * 1000, best=best,
                saving_vs_judge_all=(jall - casc[kc]) / jall)

if __name__ == "__main__":
    cJ0, cR = 0.0174, 20.0
    rows = []
    print("Per 1,000 documents, US$; cR = $20 per reviewed paper (assumed). Depth q = share of ALL documents sent to the judge.\n")
    for L in (100, 500, 2000):
        for mult in (1, 100):
            print(f"--- L = ${L} per missed machine paper; judge price x{mult} (cJ = ${cJ0*mult:.2f}) ---")
            print(f"{'target':8s}{'pi':>6s}{'q*':>7s}{'none':>9s}{'screen':>9s}{'judge-all':>11s}{'cascade':>9s}{'saving vs judge-all':>21s}   best")
            for g in ("mixture", "gpt4o", "llama", "claude"):
                for pi in (0.01, 0.10, 0.30):
                    s = summarize(R[g], pi, cJ0 * mult, cR, L)
                    rows.append((g, L, mult, pi, *[round(s[k], 4) for k in ("f", "q", "none", "screen", "judge_all", "cascade", "saving_vs_judge_all")], s["best"]))
                    print(f"{g:8s}{pi:6.0%}{s['q']:7.0%}{s['none']:9.0f}{s['screen']:9.0f}{s['judge_all']:11.0f}{s['cascade']:9.0f}{s['saving_vs_judge_all']:20.1%}   {s['best']}")
            print()
    with open("results_formal_model.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["target", "L", "judge_price_mult", "pi", "f_star", "q_star", "none", "screen", "judge_all", "cascade", "saving_vs_judge_all", "best"]); w.writerows(rows)
