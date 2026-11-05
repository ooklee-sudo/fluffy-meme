"""Markdown tables with 95% bootstrap intervals from sim.py outputs.

Usage: python tables.py sim_eb.json sim_raw.json sim_split.json out.md
"""
import sys, json
eb, raw, split = (json.load(open(f)) for f in sys.argv[1:4])
out = sys.argv[4]
NAMES = {'anthropic/claude-haiku-5.5': 'Claude Haiku 5.5', 'google/gemini-3.7-flash': 'Gemini 3.7 Flash',
         'meta-llama/llama-4-maverick': 'Llama 4 Maverick', 'openai/gpt-5.6-luna': 'GPT-5.6 luna',
         'x-ai/grok-4.3': 'Grok 4.3', 'ensemble_original': 'Ensemble (five models)',
         'openai/gpt-6-luna': 'GPT-6 luna', 'deepseek/deepseek-v4.1-flash': 'DeepSeek V4.1 Flash',
         'ensemble_current': 'Ensemble (four current models)'}
ORIGINAL = ['anthropic/claude-haiku-5.5', 'google/gemini-3.7-flash', 'meta-llama/llama-4-maverick',
            'openai/gpt-5.6-luna', 'x-ai/grok-4.3', 'ensemble_original']
NEWER = ['openai/gpt-6-luna', 'deepseek/deepseek-v4.1-flash', 'ensemble_current']
pct = lambda v: f'{100 * v:.1f}'
iv = lambda c, f=pct: f'[{f(c[0])}, {f(c[1])}]'

def row(r, m):
    A, B, E = (r[p]['16000'] for p in ('A_all', 'B_twin_topm', 'E_twin_prior'))
    return (f"| {NAMES[m]} | {r['implied_rho']:.2f} {iv(r['implied_rho_ci'], lambda v: f'{v:.2f}')} | "
            f"{pct(r['false_discard_rate'])}% | {pct(A['regret'])}% | {pct(B['regret'])}% | {pct(E['regret'])}% | "
            f"{pct(r['saving_E_regret@16000'])}% {iv(r['saving_E_regret@16000_ci'])} |")

H = ('| Model | Implied ρ [95% CI] | Best headline discarded by filter | Loss: test all | Loss: twin filter | '
     'Loss: twin prior | Traffic saved by prior [95% CI] |\n|---|---|---|---|---|---|---|')
lines = ['## Table 2 (main): five models of the pre-registered studies, truth = EB', '', H]
lines += [row(eb[m], m) for m in ORIGINAL if m in eb]
lines += ['', '## Supplement: newer models, truth = EB', '', H] + [row(eb[m], m) for m in NEWER if m in eb]
lines += ['', '## Robustness: definition of the true CTR (ensemble of the five original models)', '',
          '| Truth | Implied ρ [95% CI] | Discarded | Loss: test all | Loss: filter | Filter minus test all [95% CI] | Prior minus test all [95% CI] | Traffic saved by prior [95% CI] |',
          '|---|---|---|---|---|---|---|---|']
for lab, d in [('Empirical Bayes, all impressions (main)', eb), ('Raw CTR, all impressions', raw),
               ('Split sample: truth from half B, calibration on half A', split)]:
    r = d['ensemble_original']
    lines.append(f"| {lab} | {r['implied_rho']:.2f} {iv(r['implied_rho_ci'], lambda v: f'{v:.2f}')} | {pct(r['false_discard_rate'])}% | "
                 f"{pct(r['A_all']['16000']['regret'])}% | {pct(r['B_twin_topm']['16000']['regret'])}% | "
                 f"+{pct(r['diff_B_minus_A@16000'])} {iv(r['diff_B_minus_A@16000_ci'])} | "
                 f"{pct(r['diff_E_minus_A@16000'])} {iv(r['diff_E_minus_A@16000_ci'])} | "
                 f"{pct(r['saving_E_regret@16000'])}% {iv(r['saving_E_regret@16000_ci'])} |")
lines += ['', 'Losses are expected CTR shortfalls relative to the best headline at 16,000 impressions per test. '
          'Intervals: bootstrap over tests (1,000 resamples). Differences are in percentage points.']
open(out, 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
