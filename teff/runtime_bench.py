"""Cost of fitting T_eff: candidate-restricted cell vs full-vocabulary step."""
import json
import os
import time

import numpy as np
import torch

from teff_core import GRID, teff_cell

rng = np.random.default_rng(0)
V = rng.normal(0, 2, (240, 12))
y = rng.integers(0, 12, 240)
t = time.perf_counter()
for _ in range(50):
    teff_cell(V, y, 0.8)
restricted_ms = (time.perf_counter() - t) / 50 * 1000

g = torch.tensor(GRID[::3], dtype=torch.float32)
out = {}
for n, vocab in ((20, 151936), (20, 128256)):
    v = torch.randn(n, vocab)
    yy = torch.randint(0, vocab, (n,))
    ar = torch.arange(n)
    t = time.perf_counter()
    for _ in range(3):
        for tau in g:
            (v[ar, yy] / tau) - torch.logsumexp(v / tau, -1)
    out[f"fullvocab_{vocab}_s_per_step_20seq"] = (time.perf_counter() - t) / 3
out["restricted_ms_per_cell_240_steps"] = restricted_ms
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "runtime_bench.json"), "w"), indent=1)
print(out)
