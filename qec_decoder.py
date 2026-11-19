"""Transformer decoder for the rotated surface code vs. MWPM (PyMatching).

Data are generated on the fly with Stim (circuit-level depolarizing noise), so
there is no dataset to download.  Each detector is one token: its Fourier-
encoded (x, y, t) coordinates plus a learned embedding of its 0/1 outcome.
Because the position encoding is coordinate based, a model trained at one code
distance can be evaluated at another (--eval-d).

Examples
  python qec_decoder.py --smoke                      # CPU, ~1 min
  python qec_decoder.py --d 5 --p 0.005 --steps 20000 --device cuda
  python qec_decoder.py --d 3 --eval-d 3 5 7 --steps 20000 --device cuda
"""
import argparse
import json
import math
import os
import time

import numpy as np
import pymatching
import stim
import torch
import torch.nn as nn
import torch.nn.functional as F


# ----------------------------------------------------------------- data
def make_circuit(d, rounds, p):
    return stim.Circuit.generated(
        "surface_code:rotated_memory_z",
        distance=d,
        rounds=rounds,
        after_clifford_depolarization=p,
        after_reset_flip_probability=p,
        before_measure_flip_probability=p,
        before_round_data_depolarization=p,
    )


def detector_coords(circ):
    c = circ.get_detector_coordinates()
    arr = np.array([c[i] for i in range(circ.num_detectors)], dtype=np.float32)
    return arr  # (n_det, 3): x, y, t


class Sampler:
    def __init__(self, d, rounds, p):
        self.d, self.rounds, self.p = d, rounds, p
        self.circ = make_circuit(d, rounds, p)
        self.sampler = self.circ.compile_detector_sampler()
        self.coords = detector_coords(self.circ)
        self._matching = None

    @property
    def matching(self):
        if self._matching is None:
            dem = self.circ.detector_error_model(decompose_errors=True)
            self._matching = pymatching.Matching.from_detector_error_model(dem)
        return self._matching

    def sample(self, n):
        det, obs = self.sampler.sample(n, separate_observables=True)
        return det, obs[:, 0]

    def mwpm_predict(self, det):
        return self.matching.decode_batch(det)[:, 0].astype(bool)


# ---------------------------------------------------------------- model
class FourierPos(nn.Module):
    def __init__(self, dim, n_freq=8):
        super().__init__()
        self.register_buffer("freqs", (2.0 ** torch.arange(n_freq)) * math.pi / 16.0)
        self.proj = nn.Linear(3 * n_freq * 2, dim)

    def forward(self, xyz):  # (N, 3)
        a = xyz[..., None] * self.freqs  # (N, 3, F)
        f = torch.cat([a.sin(), a.cos()], dim=-1).flatten(-2)
        return self.proj(f)


class Decoder(nn.Module):
    def __init__(self, dim=128, layers=4, heads=4):
        super().__init__()
        self.pos = FourierPos(dim)
        self.val = nn.Embedding(2, dim)
        self.cls = nn.Parameter(torch.zeros(1, 1, dim))
        layer = nn.TransformerEncoderLayer(
            dim, heads, dim * 4, dropout=0.0, batch_first=True, norm_first=True
        )
        self.enc = nn.TransformerEncoder(layer, layers)
        self.head = nn.Sequential(nn.LayerNorm(dim), nn.Linear(dim, 1))

    def forward(self, det, coords):
        # det: (B, N) bool/int, coords: (N, 3)
        x = self.val(det.long()) + self.pos(coords)[None]
        x = torch.cat([self.cls.expand(len(x), -1, -1), x], dim=1)
        return self.head(self.enc(x)[:, 0]).squeeze(-1)


# ------------------------------------------------------------ train/eval
@torch.no_grad()
def evaluate(model, smp, n, device, bs=1024):
    model.eval()
    coords = torch.tensor(smp.coords, device=device)
    n_err_nn = n_err_mw = done = 0
    while done < n:
        b = min(bs, n - done)
        det, obs = smp.sample(b)
        logits = model(torch.tensor(det, device=device), coords)
        pred = (logits > 0).cpu().numpy()
        n_err_nn += int((pred != obs).sum())
        n_err_mw += int((smp.mwpm_predict(det) != obs).sum())
        done += b
    return {"d": smp.d, "rounds": smp.rounds, "p": smp.p, "shots": n,
            "ler_nn": n_err_nn / n, "ler_mwpm": n_err_mw / n}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d", type=int, default=3, help="training code distance")
    ap.add_argument("--rounds", type=int, default=None, help="default: d")
    ap.add_argument("--p", type=float, default=0.005)
    ap.add_argument("--eval-d", type=int, nargs="*", default=None)
    ap.add_argument("--eval-p", type=float, nargs="*", default=None,
                    help="extra noise levels to evaluate at (distribution shift)")
    ap.add_argument("--steps", type=int, default=5000)
    ap.add_argument("--bs", type=int, default=256)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--dim", type=int, default=128)
    ap.add_argument("--layers", type=int, default=4)
    ap.add_argument("--heads", type=int, default=4)
    ap.add_argument("--eval-n", type=int, default=20000)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results/qec_decoder.json")
    ap.add_argument("--smoke", action="store_true", help="tiny CPU run")
    a = ap.parse_args()
    if a.smoke:
        a.steps, a.bs, a.dim, a.layers, a.eval_n, a.device = 300, 128, 64, 2, 4000, "cpu"
        a.p = 0.01
        a.out = "results/qec_decoder_smoke.json"
    rounds = a.rounds or a.d

    torch.manual_seed(a.seed)
    np.random.seed(a.seed)
    train = Sampler(a.d, rounds, a.p)
    model = Decoder(a.dim, a.layers, a.heads).to(a.device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"d={a.d} rounds={rounds} p={a.p} detectors={train.circ.num_detectors} "
          f"params={n_params/1e6:.2f}M device={a.device}")

    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, a.lr, total_steps=a.steps, pct_start=0.05)
    coords = torch.tensor(train.coords, device=a.device)
    t0 = time.time()
    for step in range(1, a.steps + 1):
        model.train()
        det, obs = train.sample(a.bs)
        logits = model(torch.tensor(det, device=a.device), coords)
        loss = F.binary_cross_entropy_with_logits(
            logits, torch.tensor(obs, device=a.device, dtype=torch.float32))
        opt.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        if step % max(1, a.steps // 10) == 0:
            print(f"step {step}/{a.steps} loss {loss.item():.4f} ({time.time()-t0:.0f}s)")

    results = []
    for d in (a.eval_d or [a.d]):
        for p in [a.p] + (a.eval_p or []):
            r = evaluate(model, Sampler(d, d if d != a.d else rounds, p), a.eval_n, a.device)
            results.append(r)
            print(f"eval d={d} p={p}: NN {r['ler_nn']:.4f}  MWPM {r['ler_mwpm']:.4f}")

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as f:
        json.dump({"args": vars(a), "params": n_params, "train_seconds": time.time() - t0,
                   "results": results}, f, indent=2)
    print("saved", a.out)


if __name__ == "__main__":
    main()
