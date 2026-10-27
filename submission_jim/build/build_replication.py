"""Builds the replication package zip. Usage: python3 build_replication.py <scratch_dir_with_raw_outputs> <out.zip>"""
import sys, os, gzip, shutil, zipfile, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); SCR, OUTZIP = sys.argv[1], sys.argv[2]
README = r'''# Replication package
**When Can Marketers Trust Synthetic Consumers? Validity Regions and a Validation Protocol for LLM Digital Twins in Digital Experimentation**

This package contains everything needed to (A) reproduce every table, figure, and verdict in the manuscript and Web Appendix from the model outputs
without calling any model, and (B) re-run the simulations (costs money; needs an API key). Human data are public and are downloaded by a script
(they are not redistributed here).

## Contents
| Folder | What it holds |
|---|---|
| `code/` | simulation runners (`run_*.py`), analysis scripts (`analyze_*.py`), factual battery (`h6_battery.py`) |
| `benchmarks/` | `compute_human_benchmarks.py`: human effects from the public data |
| `scripts/` | `download_public_data.py`, `reproduce_analyses.sh`, `compare_results.py` |
| `raw_outputs/` | every model response used in the paper, one gzip JSON-lines file per study, plus `*_tests.json` for the field tests |
| `results/` | the summary tables produced for the paper (what the scripts regenerate) |
| `figures/` | `make_forest.py` and Figure 1 (PNG, PDF) |
| `prereg/` | AsPredicted #320110 and #320124 texts, amendment note, working document |
| `paper_src/` | manuscript source (`content_ama.json`, `make_ama.js`) |

## Study names
E1 = exploratory twin simulations (`run_full.py`), E2 = exploratory reasoning pilot (`run_h6.py`), C1 = confirmatory twin study (`run_c1.py`),
H6c = confirmatory reasoning grid (`run_h6c.py`), C2 = confirmatory field test (`run_c2.py`), S = stability study (`run_gen.py`).
C1, H6c, and C2 were run under AsPredicted #320110 and #320124. Analysis code for these studies was committed before their outputs were analyzed.

## Requirements
Python 3.10+ with `pip install -r requirements.txt`. Node.js and the `docx` npm package are needed only to rebuild the manuscript. `soffice` (LibreOffice) is needed only for PDFs.

## A. Reproduce the analyses from the shipped outputs (no API key, a few minutes)
1. Download the public human data (about 300 MB): `python3 scripts/download_public_data.py data/`
2. Re-run all analyses: `bash scripts/reproduce_analyses.sh data/ work/`
3. Compare with the shipped results: `python3 scripts/compare_results.py work/ results/`
   Bootstrap seeds are fixed, so the regenerated tables should match the shipped ones up to floating-point noise.
4. Rebuild Figure 1: `python3 figures/make_forest.py results/c1/final_effects.csv figures/Figure1_forest_C1`

## B. Re-run the simulations (optional; costs about US$306 in API calls at October 2026 prices)
Set `OPENROUTER_API_KEY` (an OpenRouter key) and run, for example:
```
python3 code/run_c1.py data/ out/c1 600 120
python3 code/run_h6c.py data/ out/h6c 100 60
python3 code/run_c2.py data/ data/upworthy/confirmatory.csv out/c2conf 1000 2026 5 100 persona,nopersona
python3 code/run_gen.py data/ out/gen 200 130
python3 code/run_full.py data/ out/full2 300
python3 code/run_h6.py data/ out/h6 100 100 80
```
The last two numbers of each command are respondent counts and a hard USD stop. Model identifiers are the aggregator names listed in Web Appendix Table W5;
models are updated or retired over time, so re-runs will not reproduce the outputs exactly. The reproducible object is the analysis of the shipped outputs.

## Known issues
- The raw condition tag (`EmbeddedData.target`) in the targeting-fairness mega-study file is inverted relative to the shown text; all analyses code conditions from the text.
- The run scripts did not send an API key header in the original runs (credentials were injected by a proxy); the `HDR` line that reads `OPENROUTER_API_KEY` was added afterwards. No other change was made to the run scripts after the studies.
- An indexing error in the Benjamini-Hochberg routine was corrected after the C2 evaluation; shipped results are from the corrected code.
- The provider that served each call was chosen by the aggregator and was not recorded.

## Data sources and licenses
Twin-2K-500 (CC BY 4.0) and its mega-study (Apache-2.0): huggingface.co/datasets/LLM-Digital-Twin. Upworthy Research Archive: OSF project jd64p.
Code license: [to be chosen by the authors before release].
'''
REQ = 'pandas>=2.2\nnumpy>=1.26\nscipy>=1.11\nrequests>=2.31\npyarrow>=15\npython-docx>=1.1\nmatplotlib>=3.8\n'
DL = r'''"""Download the public data used by the analyses. Usage: python3 download_public_data.py <data_dir> [--skip-persona] [--skip-upworthy]
Writes: {default_eric,context_effects,targeting_fairness}-00000-of-00001.parquet, wave1_3_response_label.csv, wave4_response_label.csv,
question_catalog.json, persona_summary.parquet (columns PID, persona_summary), upworthy/exploratory.csv, upworthy/confirmatory.csv."""
import sys, os, requests, glob
D = sys.argv[1]; os.makedirs(D, exist_ok=True)
HF = 'https://huggingface.co/datasets/LLM-Digital-Twin'
def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0: print('have', path); return
    with requests.get(url, stream=True, timeout=600, allow_redirects=True) as r:
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in r.iter_content(1 << 20): f.write(chunk)
    print('saved', path, os.path.getsize(path))
for st in ['default_eric', 'context_effects', 'targeting_fairness']:
    get(f'{HF}/Twin-2K-500-Mega-Study/resolve/main/data/{st}-00000-of-00001.parquet', f'{D}/{st}-00000-of-00001.parquet')
base = f'{HF}/Twin-2K-500/resolve/main/question_catalog_and_human_response_csv'
get(f'{base}/wave1_3_response_label.csv', f'{D}/wave1_3_response_label.csv'); get(f'{base}/wave4_response_label.csv', f'{D}/wave4_response_label.csv')
get(f'{base}/question_catalog.json', f'{D}/question_catalog.json')
if '--skip-persona' not in sys.argv:
    import pandas as pd
    parts = []
    for i in range(1, 8):
        p = f'{D}/persona_chunk_{i:03d}.parquet'; get(f'{HF}/Twin-2K-500/resolve/main/full_persona/chunks/persona_chunk_{i:03d}.parquet', p)
        parts.append(pd.read_parquet(p, columns=['pid', 'persona_summary']))
    df = pd.concat(parts); df['PID'] = 'pid_' + df['pid'].astype(str); df[['PID', 'persona_summary']].to_parquet(f'{D}/persona_summary.parquet')
    for p in glob.glob(f'{D}/persona_chunk_*.parquet'): os.remove(p)
if '--skip-upworthy' not in sys.argv:
    os.makedirs(f'{D}/upworthy', exist_ok=True)
    root = requests.get('https://api.osf.io/v2/nodes/jd64p/files/osfstorage/', timeout=60).json()['data']
    folder = [x for x in root if x['attributes']['name'] == 'upworthy-archive-datasets'][0]['id']
    files = requests.get(f'https://api.osf.io/v2/nodes/jd64p/files/osfstorage/{folder}/', timeout=60).json()['data']
    for x in files:
        n = x['attributes']['name']
        for key, out in [('exploratory-packages', 'exploratory.csv'), ('confirmatory-packages', 'confirmatory.csv')]:
            if key in n: get(f"https://files.osf.io/v1/resources/jd64p/providers/osfstorage/{x['id']}?action=download", f'{D}/upworthy/{out}')
print('done')
'''
REPRO = r'''#!/bin/bash
# Re-run every analysis from the shipped raw outputs. Usage: bash reproduce_analyses.sh <data_dir> <work_dir>
set -e
DATA="$(cd "$1" && pwd)"; WORK="$2"; HERE="$(cd "$(dirname "$0")/.." && pwd)"; mkdir -p "$WORK"; WORK="$(cd "$WORK" && pwd)"
for pair in E1_full_runs:e1 E2_reasoning_pilot:e2 C1_confirmatory_twin:c1 H6c_reasoning_grid:h6c C2_field_confirmatory:c2conf S_stability:s; do
  f="${pair%%:*}"; d="${pair##*:}"; mkdir -p "$WORK/$d"; gunzip -c "$HERE/raw_outputs/$f.jsonl.gz" > "$WORK/$d/raw.jsonl"
  [ -f "$HERE/raw_outputs/${f}_tests.json" ] && cp "$HERE/raw_outputs/${f}_tests.json" "$WORK/$d/tests.json" || true
done
cd "$HERE/code"
echo "== human benchmarks"; python3 -I ../benchmarks/compute_human_benchmarks.py "$DATA" "$DATA" > "$WORK/benchmarks.txt"
echo "== E1";  python3 -I analyze_twins.py "$DATA" "$WORK/e1/raw.jsonl" "$WORK/e1/res_final.csv" > "$WORK/e1/analysis.txt"
echo "== E2";  python3 -I analyze_h6.py "$DATA" "$WORK/e2/raw.jsonl" "$WORK/e2/final" > "$WORK/e2/analysis_final.txt"
echo "== C1";  python3 -I analyze_c1.py "$WORK/c1/raw.jsonl" "$WORK/c1/final" 1000 > "$WORK/c1/analysis.txt"
echo "== H6c"; python3 -I analyze_h6c.py "$WORK/h6c/raw.jsonl" "$WORK/h6c/final" > "$WORK/h6c/analysis.txt"
echo "== C2";  python3 -I analyze_c2.py "$WORK/c2conf" "$WORK/c2conf/final2" 500 > /dev/null; python3 -I analyze_c2_verdict.py "$WORK/c2conf" "$WORK/c2conf/final" 1000 > "$WORK/c2conf/verdict.txt"
echo "== S";   python3 -I analyze_gen.py "$WORK/s/raw.jsonl" "$WORK/s/res" 400 > "$WORK/s/analysis.txt"
echo "all analyses finished; now run: python3 scripts/compare_results.py $WORK results/"
'''
CMP = r'''"""Compare regenerated summary tables with the shipped ones. Usage: python3 compare_results.py <work_dir> <results_dir>"""
import sys, os, pandas as pd, numpy as np
W, R = sys.argv[1], sys.argv[2]
pairs = [('c1/final_effects.csv', 'c1/final_effects.csv'), ('c1/final_propositions.csv', 'c1/final_propositions.csv'), ('h6c/final_cells.csv', 'h6c/final_cells.csv'), ('h6c/final_propositions.csv', 'h6c/final_propositions.csv'),
         ('c2conf/final_verdicts.csv', 'c2/final_verdicts.csv'), ('c2conf/final2_summary.csv', 'c2/final2_summary.csv'), ('s/res_cells.csv', 's/res_cells.csv'), ('e1/res_final.csv', 'e1/res_final.csv'), ('e2/final_cells.csv', 'e2/final_cells.csv')]
ok = True
for a, b in pairs:
    pa, pb = os.path.join(W, a), os.path.join(R, b)
    if not (os.path.exists(pa) and os.path.exists(pb)): print('MISSING', a, b); ok = False; continue
    x, y = pd.read_csv(pa), pd.read_csv(pb)
    if x.shape != y.shape: print('SHAPE DIFF', a, x.shape, y.shape); ok = False; continue
    num = [c for c in x.columns if pd.api.types.is_numeric_dtype(x[c]) and not pd.api.types.is_bool_dtype(x[c]) and c in y.columns]; txt = [c for c in x.columns if c not in num and c in y.columns]
    d = max([float(np.nanmax(np.abs(x[c].values - y[c].values))) if len(x) else 0.0 for c in num] + [0.0]); same = all((x[c].fillna('') == y[c].fillna('')).all() for c in txt)
    flag = 'OK ' if d < 1e-6 and same else 'DIFF'; ok &= flag == 'OK '; print(flag, a, 'max abs diff', f'{d:.2e}', 'text identical' if same else 'TEXT DIFFERS')
print('ALL MATCH' if ok else 'SOME DIFFERENCES')
'''
stage = tempfile.mkdtemp(prefix='repl_'); P = os.path.join(stage, 'replication_package'); os.makedirs(P)
def put(rel, text, mode=None):
    p = os.path.join(P, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w', encoding='utf-8').write(text)
put('README.md', README); put('requirements.txt', REQ); put('scripts/download_public_data.py', DL); put('scripts/reproduce_analyses.sh', REPRO); put('scripts/compare_results.py', CMP)
def copytree(src, dst, skip=()):
    for dp, dn, fn in os.walk(os.path.join(ROOT, src)):
        dn[:] = [x for x in dn if x != '__pycache__']
        for f in fn:
            if f.endswith('.pyc') or f in skip: continue
            rel = os.path.relpath(os.path.join(dp, f), os.path.join(ROOT, src)); t = os.path.join(P, dst, rel); os.makedirs(os.path.dirname(t), exist_ok=True); shutil.copy(os.path.join(dp, f), t)
copytree('pilot', 'code', skip=('run_pilot.py',)); copytree('benchmarks', 'benchmarks'); copytree('prereg', 'prereg'); copytree('figures', 'figures'); copytree('paper_src', 'paper_src')
for sub in ['c1', 'c2', 'e1', 'e2', 'h6c', 's']: copytree(os.path.join('results', sub), os.path.join('results', sub))
for name, rel in [('E1_full_runs', 'full2'), ('E2_reasoning_pilot', 'h6'), ('C1_confirmatory_twin', 'c1'), ('H6c_reasoning_grid', 'h6c'), ('C2_field_confirmatory', 'c2conf'), ('S_stability', 'gen')]:
    os.makedirs(os.path.join(P, 'raw_outputs'), exist_ok=True)
    with open(os.path.join(SCR, rel, 'raw.jsonl'), 'rb') as fi, gzip.open(os.path.join(P, 'raw_outputs', name + '.jsonl.gz'), 'wb', 9) as fo: shutil.copyfileobj(fi, fo)
    tj = os.path.join(SCR, rel, 'tests.json')
    if os.path.exists(tj): shutil.copy(tj, os.path.join(P, 'raw_outputs', name + '_tests.json'))
os.chmod(os.path.join(P, 'scripts', 'reproduce_analyses.sh'), 0o755)
with zipfile.ZipFile(OUTZIP, 'w', zipfile.ZIP_DEFLATED) as z:
    for dp, dn, fn in os.walk(P):
        for f in sorted(fn): full = os.path.join(dp, f); z.write(full, os.path.relpath(full, stage))
shutil.rmtree(stage); print('built', OUTZIP, round(os.path.getsize(OUTZIP) / 1e6, 1), 'MB')
