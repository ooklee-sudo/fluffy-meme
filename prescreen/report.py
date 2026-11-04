"""Figures and tables from sim results."""
import sys, json, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
res = json.load(open(sys.argv[1])); outdir = sys.argv[2]
NAMES = {'A_all': 'A: test all (human A/B)', 'B_twin_topm': 'B: twin keeps top half', 'C_random_m': 'C: random half (placebo)',
         'D_twin_only': 'D: twin only, no traffic', 'E_twin_prior': 'E: twin as prior, test all'}
COL = {'A_all': '#444444', 'B_twin_topm': '#d95f02', 'C_random_m': '#999999', 'D_twin_only': '#7570b3', 'E_twin_prior': '#1b9e77'}
models = [m for m in res if m != 'ensemble'] + ['ensemble']
fig, axes = plt.subplots(1, len(models), figsize=(3.3 * len(models), 3.4), sharey=True)
lines = ['| Model | Tests | Pairwise agree | Implied ρ | Best headline discarded by twin (top half) | Regret A @16k | Regret B @16k | Regret E @16k | Crossover budget N* (B better than A below) | Traffic saved by E (regret, @16k) |',
         '|---|---|---|---|---|---|---|---|---|---|']
for ax, m in zip(axes, models):
    r = res[m]; Ns = sorted(int(n) for n in r['A_all'])
    for p in ['A_all', 'B_twin_topm', 'C_random_m', 'E_twin_prior', 'D_twin_only']:
        y = [100 * r[p][str(n)]['regret'] for n in Ns]
        ax.plot(Ns, y, marker='o' if p != 'D_twin_only' else None, ls='--' if p in ('C_random_m', 'D_twin_only') else '-',
                color=COL[p], label=NAMES[p], lw=1.6, ms=3)
    ax.set_xscale('log'); ax.set_title(f"{m.split('/')[-1]}\nρ≈{r['implied_rho']:.2f}", fontsize=9)
    ax.set_xticks(Ns); ax.set_xticklabels([f'{n//1000}k' for n in Ns]); ax.minorticks_off()
    ax.set_xlabel('Impressions per test'); ax.grid(alpha=.3)
    dA = np.array([r['A_all'][str(n)]['regret'] for n in Ns]); dB = np.array([r['B_twin_topm'][str(n)]['regret'] for n in Ns])
    better = dB < dA
    if better.all(): nstar = f'> {Ns[-1]:,}'
    elif not better[0]: nstar = f'< {Ns[0]:,}'
    else:
        k = np.argmin(better); x0, x1 = np.log(Ns[k - 1]), np.log(Ns[k]); d0, d1 = (dB - dA)[k - 1], (dB - dA)[k]
        nstar = f'≈ {np.exp(x0 - d0 * (x1 - x0) / (d1 - d0)):,.0f}'
    e = r['saving']['regret@16000']['E_twin_prior']
    lines.append(f"| {m} | {r['n_tests']} | {r['pairwise_agree']:.3f} | {r['implied_rho']:.2f} | {100*r['false_discard_rate']:.0f}% | "
                 f"{100*r['A_all']['16000']['regret']:.2f}% | {100*r['B_twin_topm']['16000']['regret']:.2f}% | "
                 f"{100*r['E_twin_prior']['16000']['regret']:.2f}% | {nstar} | {'n/a' if e is None else f'{100*e:.0f}%'} |")
axes[0].set_ylabel('Expected CTR loss vs best headline (%)')
axes[-1].legend(fontsize=7, loc='upper right')
plt.tight_layout(); plt.savefig(f'{outdir}/policy_regret.png', dpi=200)
open(f'{outdir}/policy_table.md', 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
