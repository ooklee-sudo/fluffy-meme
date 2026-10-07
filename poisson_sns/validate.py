"""Experiment 1: do IPP-simulated timings match human-like reference distributions?

Real Twitter/Reddit timestamps are NOT bundled (no network/dataset in this env).
Pass --real-times file.csv (one UTC unix timestamp per line) and --real-delays
file.csv (reply delay in hours) to replace the parametric reference with data.
Default reference = published qualitative regularities, independent functional
forms from the simulator: bimodal diurnal profile + heavy-tailed lognormal reply delay.
"""
import argparse, json, numpy as np
from scipy import stats
from sim import Sim

ap = argparse.ArgumentParser()
ap.add_argument("--reps", type=int, default=5)
ap.add_argument("--n", type=int, default=800)
ap.add_argument("--days", type=int, default=3)
ap.add_argument("--real-times"); ap.add_argument("--real-delays")
ap.add_argument("--out", default="results/validate.json")
a = ap.parse_args()

def ref_profile():
    h = np.arange(24) + 0.5
    g = lambda m, s: np.exp(-0.5 * (((h - m + 12) % 24 - 12) / s) ** 2)
    p = 0.12 + 0.8 * g(12.5, 2.5) + 1.0 * g(21, 3.0)
    return p / p.sum()

def ref_delays(rng, k):
    return np.clip(rng.lognormal(np.log(0.5), 1.6, k), 0, 48)

rng = np.random.default_rng(123)
if a.real_times:
    ts = np.loadtxt(a.real_times); hrs = (ts / 3600) % 24
    prof = np.histogram(hrs, bins=24, range=(0, 24))[0].astype(float); prof /= prof.sum()
else:
    prof = ref_profile()
ref_d = np.loadtxt(a.real_delays) if a.real_delays else ref_delays(rng, 20000)

res = {}
for mode in ["ipp", "hpp", "periodic"]:
    chi, tv, rr, ks_d, ks_p, nposts = [], [], [], [], [], []
    ndel, med = [], []
    for r in range(a.reps):
        s = Sim(n=a.n, horizon=24 * a.days, mode=mode, seed=r, start_hour=0.0).run()
        pt = s.posting_times(); nposts.append(len(pt))
        obs = np.histogram(pt % 24, bins=24, range=(0, 24))[0]
        exp = prof * obs.sum()
        chi.append(stats.chisquare(obs, exp)[0])
        tv.append(0.5 * np.abs(obs / obs.sum() - prof).sum())
        rr.append(stats.pearsonr(obs / obs.sum(), prof)[0])
        d = s.reply_delays(); ndel.append(len(d)); med.append(float(np.median(d)))
        k = stats.ks_2samp(d, ref_d); ks_d.append(k.statistic); ks_p.append(k.pvalue)
    res[mode] = dict(posts=float(np.mean(nposts)), chi2=float(np.mean(chi)), chi2_crit=float(stats.chi2.ppf(.95, 23)),
                     tv=float(np.mean(tv)), pearson=float(np.mean(rr)), ks_D=float(np.mean(ks_d)),
                     ks_p=float(np.mean(ks_p)), n_replies=float(np.mean(ndel)), median_delay_h=float(np.mean(med)))
    print(mode, {k: round(v, 4) for k, v in res[mode].items()})
res["ref_median_delay_h"] = float(np.median(ref_d))
import os; os.makedirs("results", exist_ok=True)
json.dump(res, open(a.out, "w"), indent=1)
