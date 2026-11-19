"""Transformer decoder for the rotated surface code vs. MWPM (PyMatching).

Data are generated on the fly with Stim (circuit-level depolarizing noise), so
there is no dataset to download.  Each detector is one token: its Fourier-
encoded (x, y, t) coordinates plus a learned embedding of its 0/1 outcome.
Because the position encoding is coordinate based, a model trained at one code
distance can be evaluated at another (--eval-d).

Modes
  plain   (default)  the network predicts the logical flip directly.
  --hybrid           MWPM's prediction m and matching weight w are fed to the
                     network (added to the CLS token) and the network predicts
                     whether MWPM is WRONG (target = obs XOR m).  The final
                     prediction is m XOR flip, so the decoder starts at MWPM
                     quality and only has to learn corrections.

Examples
  python qec_decoder.py --smoke                      # CPU, ~10 s
  python qec_decoder.py --smoke --hybrid
  python qec_decoder.py --d 5 --p 0.005 --hybrid --large --device cuda
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
    return np.array([c[i] for i in range(circ.num_detectors)], dtype=np.float32)  # x, y, t


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

    def mwpm(self, det):
        """MWPM prediction (bool) and matching weight (float32) per shot."""
        pred, w = self.matching.decode_batch(det, return_weights=True)
        return pred[:, 0].astype(bool), np.asarray(w, dtype=np.float32)


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
    def __init__(self, dim=128, layers=4, heads=4, hybrid=False):
        super().__init__()
        self.hybrid = hybrid
        self.pos = FourierPos(dim)
        self.val = nn.Embedding(2, dim)
        self.cls = nn.Parameter(torch.zeros(1, 1, dim))
        if hybrid:
            self.m_emb = nn.Embedding(2, dim)
            self.w_proj = nn.Linear(1, dim)
        layer = nn.TransformerEncoderLayer(
            dim, heads, dim * 4, dropout=0.0, batch_first=True, norm_first=True
        )
        self.enc = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.head = nn.Sequential(nn.LayerNorm(dim), nn.Linear(dim, 1))

    def forward(self, det, coords, m=None, w=None):
        # det: (B, N) bool, coords: (N, 3), m: (B,) bool, w: (B,) float
        x = self.val(det.long()) + self.pos(coords)[None]
        cls = self.cls.expand(len(x), -1, -1)
        if self.hybrid:
            cls = cls + self.m_emb(m.long())[:, None] + self.w_proj(torch.log1p(w)[:, None])[:, None]
        x = torch.cat([cls, x], dim=1)
        return self.head(self.enc(x)[:, 0]).squeeze(-1)


def run_batch(model, smp, n, coords, device):
    """Sample n shots; return (logits, obs, mwpm_pred) with obs/mwpm as numpy bool."""
    det, obs = smp.sample(n)
    m, w = (smp.mwpm(det) if model.hybrid else (None, None))
    t = lambda a: torch.tensor(a, device=device)
    logits = model(t(det), coords, t(m) if m is not None else None, t(w) if w is not None else None)
    return logits, obs, m, det


# ------------------------------------------------------------ train/eval
@torch.no_grad()
def evaluate(model, smp, n, device, bs=1024):
    model.eval()
    coords = torch.tensor(smp.coords, device=device)
    n_err_nn = n_err_mw = n_flip = done = 0
    while done < n:
        b = min(bs, n - done)
        logits, obs, m, det = run_batch(model, smp, b, coords, device)
        flip = (logits > 0).cpu().numpy()
        mw = m if m is not None else smp.mwpm(det)[0]
        pred = (flip ^ m) if model.hybrid else flip
        n_err_nn += int((pred != obs).sum())
        n_err_mw += int((mw != obs).sum())
        n_flip += int(flip.sum()) if model.hybrid else 0
        done += b
    out = {"d": smp.d, "rounds": smp.rounds, "p": smp.p, "shots": n,
           "ler_nn": n_err_nn / n, "ler_mwpm": n_err_mw / n}
    if model.hybrid:
        out["override_rate"] = n_flip / n  # how often the net overrides MWPM
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d", type=int, default=3, help="training code distance")
    ap.add_argument("--rounds", type=int, default=None, help="default: d")
    ap.add_argument("--p", type=float, default=0.005)
    ap.add_argument("--eval-d", type=int, nargs="*", default=None)
    ap.add_argument("--eval-p", type=float, nargs="*", default=None,
                    help="extra noise levels to evaluate at (distribution shift)")
    ap.add_argument("--hybrid", action="store_true", help="learn a correction on top of MWPM")
    ap.add_argument("--large", action="store_true",
                    help="preset: dim 256, 6 layers, 8 heads, bs 512, 60000 steps, lr 2e-4")
    ap.add_argument("--steps", type=int, default=5000)
    ap.add_argument("--bs", type=int, default=256)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--dim", type=int, default=128)
    ap.add_argument("--layers", type=int, default=4)
    ap.add_argument("--heads", type=int, default=4)
    ap.add_argument("--eval-n", type=int, default=20000)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--smoke", action="store_true", help="tiny CPU run")
    a = ap.parse_args()
    if a.large:
        a.dim, a.layers, a.heads, a.bs, a.steps, a.lr = 256, 6, 8, 512, 60000, 2e-4
    if a.smoke:
        a.steps, a.bs, a.dim, a.layers, a.eval_n, a.device = 300, 128, 64, 2, 4000, "cpu"
        a.p = 0.01
    if a.out is None:
        tag = ("_hybrid" if a.hybrid else "") + ("_smoke" if a.smoke else "")
        a.out = f"results/qec_decoder{tag}.json"
    rounds = a.rounds or a.d

    torch.manual_seed(a.seed)
    np.random.seed(a.seed)
    if a.device == "cuda":
        torch.set_float32_matmul_precision("high")
    train = Sampler(a.d, rounds, a.p)
    model = Decoder(a.dim, a.layers, a.heads, a.hybrid).to(a.device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"d={a.d} rounds={rounds} p={a.p} detectors={train.circ.num_detectors} "
          f"params={n_params/1e6:.2f}M hybrid={a.hybrid} device={a.device}")

    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, a.lr, total_steps=a.steps, pct_start=0.05)
    coords = torch.tensor(train.coords, device=a.device)
    history = []
    t0 = time.time()
    for step in range(1, a.steps + 1):
        model.train()
        logits, obs, m, _ = run_batch(model, train, a.bs, coords, a.device)
        target = (obs ^ m) if model.hybrid else obs  # hybrid: "is MWPM wrong?"
        loss = F.binary_cross_entropy_with_logits(
            logits, torch.tensor(target, device=a.device, dtype=torch.float32))
        opt.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        if step % max(1, a.steps // 10) == 0:
            msg = f"step {step}/{a.steps} loss {loss.item():.4f} ({time.time()-t0:.0f}s)"
            if step % max(1, a.steps // 5) == 0 and step < a.steps:  # quick progress check
                r = evaluate(model, train, 4000, a.device)
                history.append({"step": step, **r})
                msg += f" | quick eval NN {r['ler_nn']:.4f} MWPM {r['ler_mwpm']:.4f}"
            print(msg, flush=True)

    results = []
    for d in (a.eval_d or [a.d]):
        for p in [a.p] + (a.eval_p or []):
            r = evaluate(model, Sampler(d, d if d != a.d else rounds, p), a.eval_n, a.device)
            results.append(r)
            extra = f"  override {r['override_rate']:.4f}" if "override_rate" in r else ""
            print(f"eval d={d} p={p}: NN {r['ler_nn']:.4f}  MWPM {r['ler_mwpm']:.4f}{extra}")

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as f:
        json.dump({"args": vars(a), "params": n_params, "train_seconds": time.time() - t0,
                   "history": history, "results": results}, f, indent=2)
    print("saved", a.out)


if __name__ == "__main__":
    main()
