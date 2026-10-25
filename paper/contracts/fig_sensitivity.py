import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sensitivity import stats
a, b = .12, .39
hv = np.logspace(0.7, 4.3, 40); kv = np.logspace(-3, 1, 40)               # H/v, k/v with v = 1
WA = np.full((len(kv), len(hv)), np.nan); WB = WA.copy(); RS = WA.copy()
for i, kk in enumerate(kv):
    for j, hh in enumerate(hv):
        r = stats(a, b, hh, 1.0, kk, J=1500)
        if r['NFB'] >= 1 and r.get('A') and r['A'][1] > 0 and r['B'][1] > 0:
            WA[i, j] = r['WA']/r['SFB']; WB[i, j] = r['WB']/r['SFB']; RS[i, j] = r['rent_share']
plt.rcParams.update({"font.size": 8.5, "font.family": "serif"})
fig, ax = plt.subplots(3, 1, figsize=(6.3, 8.2), constrained_layout=True, sharex=True)
for k_, (axx, Z, t) in enumerate(zip(ax, [WA, WB, RS], ["(a) Per-attempt monopoly: welfare / first best", "(b) Success-fee monopoly: welfare / first best", "(c) Incentive rent / surplus at first-best depth"])):
    im = axx.pcolormesh(np.log10(hv), np.log10(kv), Z, vmin=0, vmax=1, cmap="viridis", shading="auto")
    axx.set_ylabel("log10 (k / v)"); axx.set_title(t, fontsize=9, loc="left")
    if k_ == 2: axx.set_xlabel("log10 (H / v)   (human repair cost / firm cost per attempt)")
    fig.colorbar(im, ax=axx, shrink=.9, pad=.02)
fig.savefig("fig_sensitivity.png", dpi=200)
print("saved")
