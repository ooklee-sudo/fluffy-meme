"""Figure 1 for the IEEE Intelligent Systems version."""
import json, sys, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
sim, ana, out = sys.argv[1:4]
KEY = sys.argv[4] if len(sys.argv) > 4 else 'ensemble_original'
MODELS = sys.argv[5].split(',') if len(sys.argv) > 5 else None
R_all = json.load(open(sim)); r = R_all[KEY]; a = json.load(open(ana))
rhos = [R_all[m]['implied_rho'] for m in (MODELS or [k for k in R_all if '/' in k])]
RHO_LO, RHO_HI = min(rhos), max(rhos)
Ns = sorted(int(n) for n in r['A_all'])
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.5))
sty = [('A_all', 'Test all (human A/B)', '#333333', '-'), ('E_twin_prior', 'Twin as prior, test all', '#1b9e77', '-'),
       ('B_twin_topm', 'Twin filter (keep top half)', '#d95f02', '-'), ('C_random_m', 'Random filter (placebo)', '#999999', '--'),
       ('D_twin_only', 'Twin only (no test)', '#7570b3', ':')]
for k, lab, c, ls in sty:
    ax1.plot(Ns, [100 * r[k][str(n)]['regret'] for n in Ns], ls=ls, color=c, lw=1.8,
             marker=None if k == 'D_twin_only' else 'o', ms=3, label=lab)
    if 'regret_ci' in r[k][str(Ns[0])]:
        ax1.fill_between(Ns, [100 * r[k][str(n)]['regret_ci'][0] for n in Ns], [100 * r[k][str(n)]['regret_ci'][1] for n in Ns],
                         color=c, alpha=.15, lw=0)
ax1.set_xscale('log'); ax1.set_xticks(Ns); ax1.set_xticklabels([f'{n//1000}k' for n in Ns]); ax1.minorticks_off()
ax1.set_xlabel('Impressions per test'); ax1.set_ylabel('Expected CTR loss (%)')
ax1.set_title('(a) 500 Upworthy headline tests', fontsize=9); ax1.grid(alpha=.3)
rho = [float(k) for k in a if a[k] is not None]; ns = [a[k] for k in a if a[k] is not None]
ax2.plot(rho, ns, 'o-', color='#d95f02', lw=1.8, ms=4)
ax2.set_yscale('log'); ax2.axvspan(RHO_LO, RHO_HI, color='#1b9e77', alpha=.15, lw=0)
ax2.text(RHO_LO - 0.025, 300, f'observed ρ\n({len(rhos)} models)', ha='right', fontsize=7, color='#1b9e77')
ax2.axhline(20000, color='#333333', ls='--', lw=1); ax2.text(0.72, 23000, 'typical Upworthy test', ha='right', fontsize=7)
ax2.text(0.05, 1500, 'never\npays', ha='center', fontsize=7, color='#d95f02')
ax2.set_xlim(0, 0.75); ax2.set_ylim(250, 60000)
ax2.set_xlabel('Twin–outcome correlation ρ'); ax2.set_ylabel('Break-even budget N* (impressions)')
ax2.set_title('(b) Filtering pays only below N*', fontsize=9); ax2.grid(alpha=.3)
h, l = ax1.get_legend_handles_labels()
fig.legend(h, l, loc='lower center', ncol=3, fontsize=7, frameon=False)
plt.tight_layout(rect=(0, 0.11, 1, 1)); plt.savefig(out, dpi=300)
