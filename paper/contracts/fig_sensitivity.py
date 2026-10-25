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
fig, ax = plt.subplots(1, 3, figsize=(15, 4.4), constrained_layout=True)
for axx, Z, t in zip(ax, [WA, WB, RS], ["Per-attempt monopoly: welfare / first best", "Success-fee monopoly: welfare / first best", "Incentive rent / surplus at first-best depth"]):
    im = axx.pcolormesh(np.log10(hv), np.log10(kv), Z, vmin=0, vmax=1, cmap="viridis", shading="auto")
    axx.set_xlabel("log10 (H / v)  [human repair cost / firm cost per attempt]"); axx.set_ylabel("log10 (k / v)  [vendor cost / firm cost per attempt]"); axx.set_title(t, fontsize=10)
    fig.colorbar(im, ax=axx, shrink=.85)
fig.suptitle("Sensitivity to cost ratios (a = 0.12, b = 0.39). Blank cells: AI repair not worth using", fontsize=11)
fig.savefig("fig_sensitivity.png", dpi=140)
print("saved")
